"""Replace the FAMILIES array in the HTML with data/families.json.

Coordinates come only from families.json (hand-placed). Proposal ranks are
never written here unless a human first copied numbers into the JSON by hand.
"""

from __future__ import annotations

import json
import re

from dataset.extract import load_dataset
from dataset.paths import HTML_PATH


def sync_html() -> None:
    ds = load_dataset()
    families = [f.model_dump(mode="json", by_alias=True, exclude_none=True) for f in ds.families]
    blob = json.dumps(families, ensure_ascii=False, indent=2)
    html = HTML_PATH.read_text(encoding="utf-8")
    pattern = r"const FAMILIES = \[[\s\S]*?\n\];"
    if not re.search(pattern, html):
        raise RuntimeError("could not find FAMILIES array in HTML")
    html = re.sub(pattern, "const FAMILIES = " + blob + ";", html, count=1)
    HTML_PATH.write_text(html, encoding="utf-8")
    n = sum(len(f.words) for f in ds.families)
    print("MYDEBUG → synced HTML", len(ds.families), "families /", n, "words")
