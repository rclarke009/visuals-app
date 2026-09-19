"""Grounded review factory for the nuance-cube word dataset.

The HTML prototype stays the published lesson. This package extracts
FAMILIES to JSON, audits it against Wiktionary / Etymonline / Ngrams,
and writes proposals for a human to accept. Cube coordinates are never
auto-merged.
"""

SCHEMA_VERSION = "1.0.0"
USAGE_YEARS = (1800, 1850, 1900, 1950, 2000, 2019)
PROTECTED_COORD_FIELDS = frozenset({"x", "y", "z", "band"})
