# Dataset review factory

The cube in `nuance-cube-v0.1.html` stays the published lesson. This package turns `FAMILIES` into versioned JSON, audits it against Wiktionary, Etymonline, and Google Books Ngrams, and writes **proposals** for you to accept.

Coordinates (`x`, `y`, `z`, `band`) are never auto-merged. Rank suggestions are advisory.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional: add ANTHROPIC_API_KEY for gloss / swap-test / sense notes
```

Needs Node on PATH (used only to eval the existing JS array).

## Commands

```bash
python -m dataset extract              # HTML → data/families.json + schema
python -m dataset audit --no-llm       # LangGraph retrieve → extract → ngrams → proposals
python -m dataset audit --family thin  # one family; uses Claude if the key is set
python -m dataset roots                # shared root.id candidates → proposals/_root_links.json
python -m dataset queue list
python -m dataset queue accept livid
python -m dataset queue reject bright
python -m dataset queue accept-roots --sync
python -m dataset sync                 # families.json → HTML FAMILIES array
```

`audit` stops before merge (`interrupt_before apply_merge`). Accepting a proposal updates `data/families.json` only. `--sync` copies that JSON into the HTML.

## What you review

- **Swap test / gloss:** do two definitions still work if swapped?
- **Lesson fit:** does this sibling belong; is walk intensity body effort?
- **Receipts:** each `proposals/<hub>__<word>.json` quotes the dictionary and the six ngram samples. If a year is not in a quote, it is dropped.

Do not accept a `from` trail you cannot see in the quotes. A shorter Wiktionary trail is not automatically better than the hand-curated one.

This 37-word set currently shares **no** grounded ancestor form, so `proposals/_root_links.json` will say so until you assign a `root.id` or add a real cognate.
