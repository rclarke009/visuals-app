"""Pull FAMILIES out of the prototype HTML into versioned JSON."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from dataset import SCHEMA_VERSION, USAGE_YEARS
from dataset.models import Dataset
from dataset.paths import DATA_DIR, FAMILIES_JSON, HTML_PATH, SCHEMA_JSON

EXTRACT_JS = r"""
const fs = require('fs');
const htmlPath = process.env.HTML_PATH;
const html = fs.readFileSync(htmlPath, 'utf8');
const marker = 'const FAMILIES = ';
const start = html.indexOf(marker);
if (start < 0) {
  console.error('FAMILIES marker not found');
  process.exit(1);
}
const from = start + marker.length;
const end = html.indexOf('\n];', from);
if (end < 0) {
  console.error('FAMILIES terminator not found');
  process.exit(1);
}
const src = html.slice(from, end + 3).replace(/;\s*$/, '');
const FAMILIES = eval(src);
process.stdout.write(JSON.stringify(FAMILIES));
"""


def extract_families(html_path: Path = HTML_PATH) -> list:
    env = dict(os.environ)
    env["HTML_PATH"] = str(html_path)
    proc = subprocess.run(
        ["node", "-e", EXTRACT_JS],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or "node extract failed")
    return json.loads(proc.stdout)


def write_dataset(html_path: Path = HTML_PATH, out_path: Path = FAMILIES_JSON) -> Dataset:
    families = extract_families(html_path)
    ds = Dataset(
        schema_version=SCHEMA_VERSION,
        usage_years=USAGE_YEARS,
        families=families,
    )
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = ds.model_dump(mode="json", by_alias=True, exclude_none=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    SCHEMA_JSON.write_text(
        json.dumps(Dataset.model_json_schema(), indent=2) + "\n",
        encoding="utf-8",
    )
    n = sum(len(f.words) for f in ds.families)
    print(f"MYDEBUG → wrote {ds.schema_version} {len(ds.families)} families / {n} words → {out_path}")
    return ds


def load_dataset(path: Path = FAMILIES_JSON) -> Dataset:
    return Dataset.model_validate_json(path.read_text(encoding="utf-8"))


def main() -> None:
    ds = write_dataset()
    print("MYDEBUG → extract done", ds.schema_version)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
