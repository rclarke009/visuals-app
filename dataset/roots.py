"""Propose shared root.id when grounded etymology shows the same ancestor form."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict

from dataset.extract import load_dataset
from dataset.models import Evidence, RootLink, RootLinkProposal
from dataset.paths import PROPOSALS_DIR


def _norm(form: str) -> str:
    form = unicodedata.normalize("NFKD", form)
    form = "".join(ch for ch in form if not unicodedata.combining(ch))
    form = form.lower().strip().strip("*")
    form = re.sub(r"[^a-z0-9]+", "", form)
    return form


def _ancestors(word_from: list[dict], root: dict | None) -> list[tuple[str, str]]:
    out = []
    for step in word_from:
        form = step.get("form") or ""
        lang = step.get("lang") or ""
        n = _norm(form)
        if n:
            out.append((n, f"{lang} {form}".strip()))
    if root and root.get("form"):
        n = _norm(root["form"])
        if n:
            out.append((n, root["form"]))
    return out


def propose_root_links() -> RootLinkProposal:
    ds = load_dataset()
    surfaces = {_norm(w.w) for family in ds.families for w in family.words}
    buckets: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    labels: dict[str, str] = {}
    for family in ds.families:
        for word in family.words:
            steps = [s.model_dump() for s in word.from_]
            root = word.root.model_dump() if word.root else None
            payload: dict = {}
            prop_path = PROPOSALS_DIR / f"{family.hub}__{word.w}.json"
            if prop_path.exists():
                payload = json.loads(prop_path.read_text(encoding="utf-8"))
                if payload.get("proposed_from"):
                    steps = payload["proposed_from"]
                if payload.get("proposed_root"):
                    root = payload["proposed_root"]
            for n, label in _ancestors(steps, root):
                if len(n) < 4:
                    continue
                if n in surfaces:
                    continue
                key = (family.hub, word.w)
                if key not in [(h, w) for h, w, _ in buckets[n]]:
                    buckets[n].append((family.hub, word.w, label))
                    labels.setdefault(n, label)
            for wr in payload.get("wiki_roots") or []:
                n = "wiki-" + _norm(wr)
                if len(n) < 8:
                    continue
                buckets[n].append((family.hub, word.w, wr))
                labels.setdefault(n, wr)

    links: list[RootLink] = []
    for n, members in sorted(buckets.items()):
        uniq = []
        seen = set()
        for hub, w, label in members:
            if w in seen:
                continue
            seen.add(w)
            uniq.append((hub, w, label))
        if len(uniq) < 2:
            continue
        words = [w for _, w, _ in uniq]
        hubs = [h for h, _, _ in uniq]
        rid = re.sub(r"[^a-z0-9]+", "-", n)
        links.append(
            RootLink(
                proposed_id=rid,
                form=labels[n],
                gloss="shared ancestor (from dictionary extract)",
                words=words,
                hubs=hubs,
                evidence=[
                    Evidence(
                        source="grounded-extract",
                        quote=f"normalized form {n} shared by {', '.join(words)}",
                    )
                ],
                reason=f"Same ancestor form {labels[n]!r} appears in more than one trail.",
            )
        )

    proposal = RootLinkProposal(links=links)
    if not links:
        proposal.note = (
            "No two words in the current 37 share a grounded ancestor form or Wiktionary "
            "{{root}} id. Root chips will keep falling through to Wiktionary until you assign "
            "a shared root.id by hand. Re-run after accepting etymology proposals."
        )
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    path = PROPOSALS_DIR / "_root_links.json"
    path.write_text(proposal.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print("MYDEBUG → root link proposals", len(links), "→", path)
    return proposal
