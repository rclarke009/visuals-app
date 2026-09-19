from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "nuance-cube-v0.1.html"
DATA_DIR = ROOT / "data"
FAMILIES_JSON = DATA_DIR / "families.json"
SCHEMA_JSON = DATA_DIR / "families.schema.json"
PROPOSALS_DIR = ROOT / "proposals"
CACHE_DIR = ROOT / "dataset" / ".cache"
ENV_EXAMPLE = ROOT / ".env.example"
