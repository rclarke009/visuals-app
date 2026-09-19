"""LangGraph family audit: retrieve → extract → ngrams → sense → gloss → ranks → proposals.

Merge is interrupted: use `python -m dataset queue accept` instead of writing coordinates.
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from dataset.extract import load_dataset
from dataset.llm import extract_etymology_llm, gloss_review_llm, llm_enabled, rank_llm, sense_flag_llm
from dataset.models import (
    Evidence,
    Family,
    GlossReview,
    RankSuggestion,
    SenseFlag,
    Word,
    WordProposal,
)
from dataset.paths import PROPOSALS_DIR
from dataset.sources import evidence_pack, etymology_sections, grounded_extract


class FamilyState(TypedDict, total=False):
    hub: str
    family: dict[str, Any]
    sources: dict[str, Any]
    extracts: dict[str, Any]
    senses: dict[str, Any]
    gloss_review: dict[str, Any]
    ranks: list[dict[str, Any]]
    proposals: list[dict[str, Any]]
    use_llm: bool
    errors: list[str]


def retrieve(state: FamilyState) -> FamilyState:
    family = Family.model_validate(state["family"])
    sources: dict[str, Any] = {}
    errors = list(state.get("errors") or [])
    for word in family.words:
        ev, pack = evidence_pack(word.w)
        pack["evidence"] = [e.model_dump() for e in ev]
        sources[word.w] = pack
        if not pack["wiktionary"].get("ok"):
            errors.append(f"{word.w}: wiktionary {pack['wiktionary'].get('error')}")
        if not pack["ngrams"].get("ok"):
            errors.append(f"{word.w}: ngrams {pack['ngrams'].get('error')}")
    print("MYDEBUG → retrieve", family.hub, list(sources))
    return {"sources": sources, "errors": errors}


def extract_node(state: FamilyState) -> FamilyState:
    family = Family.model_validate(state["family"])
    sources = state["sources"]
    extracts: dict[str, Any] = {}
    for word in family.words:
        pack = sources[word.w]
        steps, root, quotes, year_ok, wiki_roots = grounded_extract(pack["wiktionary"], pack["etymonline"])
        wiki_q = next((e["quote"] for e in pack["evidence"] if e["source"] == "wiktionary"), "")
        ety_q = next((e["quote"] for e in pack["evidence"] if e["source"] == "etymonline"), "")
        llm = extract_etymology_llm(word.w, wiki_q, ety_q) if state.get("use_llm") else None
        if llm and llm.from_steps:
            blob = wiki_q + " " + ety_q
            kept = []
            for step in llm.from_steps:
                if step.year is not None and str(step.year) not in blob:
                    step.year = None
                if step.form and step.form.lower() not in blob.lower() and step.form not in blob:
                    continue
                kept.append(step)
            if kept:
                steps = kept
                root = llm.root or root
                year_ok = all(s.year is None or str(s.year) in blob for s in steps)
        extracts[word.w] = {
            "from": [s.model_dump(exclude_none=True) for s in steps],
            "root": root.model_dump() if root else None,
            "quotes": quotes,
            "year_grounded": year_ok,
            "wiki_roots": wiki_roots,
        }
    print("MYDEBUG → extract", list(extracts))
    return {"extracts": extracts}


def _homograph_heuristic(word: Word, pack: dict) -> SenseFlag:
    secs = etymology_sections(pack["wiktionary"].get("wikitext") or "")
    ety = pack["etymonline"].get("text") or ""
    other = []
    if len(secs) > 1:
        other.append(f"{len(secs)} English etymology sections")
    hints = [
        ("month", "calendar month"),
        ("military", "military / rank"),
        ("goat", "young goat"),
        ("colour", "colour"),
        ("color", "colour"),
        ("shining", "light / shine"),
        ("lesser", "lesser / music"),
    ]
    blob = " ".join(secs) + " " + ety
    for needle, label in hints:
        if needle in blob.lower():
            other.append(label)
    pollutes = len(secs) > 1 or any(
        x in other for x in ("young goat", "colour", "light / shine", "calendar month", "military / rank")
    )
    note = None
    if pollutes:
        note = (
            f"This surface form has other senses ({', '.join(dict.fromkeys(other)) or 'see sources'}). "
            "The usage curve may mix them."
        )
    return SenseFlag(pollutes_curve=pollutes, other_senses=list(dict.fromkeys(other)), usageNote=note, reason="heuristic")


def sense_node(state: FamilyState) -> FamilyState:
    family = Family.model_validate(state["family"])
    senses: dict[str, Any] = {}
    for word in family.words:
        pack = state["sources"][word.w]
        quotes = "\n".join(e["quote"] for e in pack["evidence"])
        flag = sense_flag_llm(word.w, family.hub, word.gloss, quotes) if state.get("use_llm") else None
        if flag is None:
            flag = _homograph_heuristic(word, pack)
        senses[word.w] = flag.model_dump()
    return {"senses": senses}


def gloss_node(state: FamilyState) -> FamilyState:
    family = Family.model_validate(state["family"])
    payload = json.dumps(
        [{"w": w.w, "gloss": w.gloss, "ex": w.ex} for w in family.words],
        indent=2,
    )
    review = gloss_review_llm(payload) if state.get("use_llm") else GlossReview()
    if review is None:
        review = GlossReview()
    return {"gloss_review": review.model_dump()}


def rank_node(state: FamilyState) -> FamilyState:
    family = Family.model_validate(state["family"])
    payload = json.dumps(
        {
            "hub": family.hub,
            "answer": family.answer,
            "insight": family.insight,
            "words": [
                {"w": w.w, "gloss": w.gloss, "x": w.x, "y": w.y, "z": w.z}
                for w in family.words
            ],
        },
        indent=2,
    )
    ranks = rank_llm(payload, ", ".join(family.answer)) if state.get("use_llm") else None
    return {"ranks": [r.model_dump() for r in ranks] if ranks else []}


def write_proposals(state: FamilyState) -> FamilyState:
    family = Family.model_validate(state["family"])
    review = GlossReview.model_validate(state.get("gloss_review") or {})
    ranks = [RankSuggestion.model_validate(r) for r in (state.get("ranks") or [])]
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    proposals: list[dict[str, Any]] = []
    for word in family.words:
        pack = state["sources"][word.w]
        ext = state["extracts"][word.w]
        sense = SenseFlag.model_validate(state["senses"][word.w])
        ev = [Evidence.model_validate(e) for e in pack["evidence"]]
        diffs: list[str] = []
        errors = [e for e in (state.get("errors") or []) if e.startswith(word.w + ":")]
        proposed_from = ext["from"] or None
        current_from = [s.model_dump(exclude_none=True) for s in word.from_]
        if proposed_from and proposed_from != current_from:
            diffs.append("from")
        proposed_root = ext["root"]
        if proposed_root and (not word.root or word.root.model_dump() != proposed_root):
            diffs.append("root")
        usage = pack["ngrams"].get("usage")
        if usage and usage != word.usage:
            diffs.append("usage")
        note = sense.usageNote if sense.pollutes_curve else None
        if note and note != word.usageNote:
            diffs.append("usageNote")
        cands = review.candidates.get(word.w) or []
        proposed_gloss = cands[0].gloss if cands else None
        if proposed_gloss:
            diffs.append("gloss")
        prop = WordProposal(
            word=word.w,
            hub=family.hub,
            evidence=ev,
            proposed_from=proposed_from,
            proposed_root=proposed_root,
            proposed_usage=usage,
            proposed_usageNote=note,
            proposed_gloss=proposed_gloss,
            rank_suggestions=ranks,
            gloss_candidates=cands,
            diffs=diffs,
            errors=errors,
            wiki_roots=ext.get("wiki_roots") or [],
        )
        path = PROPOSALS_DIR / f"{family.hub}__{word.w}.json"
        path.write_text(prop.model_dump_json(indent=2) + "\n", encoding="utf-8")
        proposals.append({"path": str(path), **prop.model_dump()})
    fam_path = PROPOSALS_DIR / f"{family.hub}__family.json"
    fam_path.write_text(
        json.dumps(
            {
                "hub": family.hub,
                "swap_failures": review.swap_failures,
                "rank_suggestions": [r.model_dump() for r in ranks],
                "note": "Rank suggested_xyz is advisory. Queue accept never writes x/y/z/band.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("MYDEBUG → wrote proposals", family.hub, len(proposals))
    return {"proposals": proposals}


def apply_merge(_state: FamilyState) -> FamilyState:
    # interrupt_before this node — human queue owns merge.
    return {}


def build_graph():
    g = StateGraph(FamilyState)
    g.add_node("retrieve", retrieve)
    g.add_node("extract", extract_node)
    g.add_node("sense", sense_node)
    g.add_node("gloss", gloss_node)
    g.add_node("rank", rank_node)
    g.add_node("write_proposals", write_proposals)
    g.add_node("apply_merge", apply_merge)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "extract")
    g.add_edge("extract", "sense")
    g.add_edge("sense", "gloss")
    g.add_edge("gloss", "rank")
    g.add_edge("rank", "write_proposals")
    g.add_edge("write_proposals", "apply_merge")
    g.add_edge("apply_merge", END)
    return g.compile(interrupt_before=["apply_merge"], checkpointer=MemorySaver())


GRAPH = build_graph()


def audit_family(hub: str, use_llm: Optional[bool] = None) -> FamilyState:
    ds = load_dataset()
    family = next((f for f in ds.families if f.hub == hub), None)
    if family is None:
        raise KeyError(hub)
    enabled = llm_enabled() if use_llm is None else use_llm
    state: FamilyState = {
        "hub": hub,
        "family": family.model_dump(by_alias=True),
        "use_llm": enabled,
        "errors": [],
    }
    # Run through write_proposals; apply_merge stays interrupted.
    out = GRAPH.invoke(state, {"configurable": {"thread_id": f"audit-{hub}"}})
    return out


def audit_all(use_llm: Optional[bool] = None) -> list[str]:
    ds = load_dataset()
    hubs = []
    for family in ds.families:
        audit_family(family.hub, use_llm=use_llm)
        hubs.append(family.hub)
    return hubs
