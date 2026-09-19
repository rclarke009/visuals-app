"""Human review queue. Accept never writes x/y/z/band."""

from __future__ import annotations

import json
from pathlib import Path

from dataset import PROTECTED_COORD_FIELDS
from dataset.extract import load_dataset
from dataset.models import Dataset, Root, WordProposal
from dataset.paths import FAMILIES_JSON, PROPOSALS_DIR
from dataset.sync_html import sync_html


def _proposal_files() -> list[Path]:
    if not PROPOSALS_DIR.exists():
        return []
    return sorted(
        p for p in PROPOSALS_DIR.glob("*.json") if "__family" not in p.name and p.name != "_root_links.json"
    )


def load_proposal(word: str) -> tuple[Path, WordProposal]:
    matches = [p for p in _proposal_files() if p.stem.endswith("__" + word) or p.stem.endswith(word)]
    if not matches:
        raise FileNotFoundError(f"no proposal for {word}")
    path = matches[0]
    return path, WordProposal.model_validate_json(path.read_text(encoding="utf-8"))


def list_proposals() -> None:
    files = _proposal_files()
    if not files:
        print("MYDEBUG → no proposals (run: python -m dataset audit)")
        return
    for path in files:
        prop = WordProposal.model_validate_json(path.read_text(encoding="utf-8"))
        print(f"{prop.status:10} {prop.hub:8} {prop.word:12} diffs={prop.diffs} errors={len(prop.errors)}")
    roots = PROPOSALS_DIR / "_root_links.json"
    if roots.exists():
        print(f"root-links   {roots}")


def _save_dataset(ds: Dataset) -> None:
    payload = ds.model_dump(mode="json", by_alias=True, exclude_none=True)
    FAMILIES_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def accept(word: str, do_sync: bool = False) -> None:
    path, prop = load_proposal(word)
    if prop.status == "rejected":
        raise RuntimeError(f"{word} was rejected")
    ds = load_dataset()
    found = None
    for family in ds.families:
        for w in family.words:
            if w.w == word and family.hub == prop.hub:
                found = w
                break
        if found:
            break
    if found is None:
        raise KeyError(word)
    if prop.proposed_from:
        found.from_ = prop.proposed_from
    if prop.proposed_root:
        found.root = prop.proposed_root
    if prop.proposed_usage:
        found.usage = prop.proposed_usage
    if prop.proposed_usageNote:
        found.usageNote = prop.proposed_usageNote
    if prop.proposed_gloss:
        found.gloss = prop.proposed_gloss
    if prop.proposed_ex:
        found.ex = prop.proposed_ex
    for k in PROTECTED_COORD_FIELDS:
        assert hasattr(found, k)
    prop.status = "accepted"
    path.write_text(prop.model_dump_json(indent=2) + "\n", encoding="utf-8")
    _save_dataset(ds)
    print("MYDEBUG → accepted", word, "fields", prop.diffs, "(coords untouched)")
    if do_sync:
        sync_html()


def reject(word: str) -> None:
    path, prop = load_proposal(word)
    prop.status = "rejected"
    path.write_text(prop.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print("MYDEBUG → rejected", word)


def accept_roots(do_sync: bool = False) -> None:
    path = PROPOSALS_DIR / "_root_links.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    ds = load_dataset()
    by_word = {}
    for family in ds.families:
        for w in family.words:
            by_word[(family.hub, w.w)] = w
    for link in data.get("links") or []:
        root = Root(id=link["proposed_id"], form=link.get("form") or link["proposed_id"], gloss=link.get("gloss") or "")
        words = link["words"]
        hubs = link.get("hubs") or []
        for i, wname in enumerate(words):
            hub = hubs[i] if i < len(hubs) else None
            if hub:
                target = by_word.get((hub, wname))
            else:
                target = next((w for (h, n), w in by_word.items() if n == wname), None)
            if target is None:
                continue
            target.root = root
    data["status"] = "accepted"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    _save_dataset(ds)
    print("MYDEBUG → accepted root links", len(data.get("links") or []))
    if do_sync:
        sync_html()


def reject_roots() -> None:
    path = PROPOSALS_DIR / "_root_links.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["status"] = "rejected"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("MYDEBUG → rejected root links")
