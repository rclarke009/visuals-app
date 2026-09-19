from __future__ import annotations

import hashlib
import json
import re
import time
from html import unescape
from typing import Optional
from urllib.parse import quote

import httpx

from dataset import USAGE_YEARS
from dataset.models import Evidence, FromStep, Root
from dataset.paths import CACHE_DIR

UA = (
    "NuanceCubeDataset/1.0 (word-dataset audit; "
    "https://en.wiktionary.org/wiki/Wiktionary:Main_Page)"
)


def _cache_path(kind: str, key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    folder = CACHE_DIR / kind
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{digest}.json"


def cached_get(kind: str, url: str, params: Optional[dict] = None, timeout: float = 30.0) -> dict:
    key = url + "?" + json.dumps(params or {}, sort_keys=True)
    path = _cache_path(kind, key)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    headers = {"User-Agent": UA, "Accept": "application/json, text/html;q=0.8"}
    last_exc: Exception | None = None
    with httpx.Client(headers=headers, follow_redirects=True, timeout=timeout) as client:
        for attempt in range(6):
            try:
                r = client.get(url, params=params)
                if r.status_code == 429:
                    wait = float(r.headers.get("Retry-After") or 2 ** attempt)
                    time.sleep(min(wait, 20))
                    last_exc = httpx.HTTPStatusError("429", request=r.request, response=r)
                    continue
                r.raise_for_status()
                ctype = r.headers.get("content-type", "")
                if "json" in ctype or (r.text[:1] in "[{"):
                    try:
                        body = {"ok": True, "json": r.json(), "url": str(r.url)}
                    except Exception:
                        body = {"ok": True, "text": r.text, "url": str(r.url)}
                else:
                    body = {"ok": True, "text": r.text, "url": str(r.url)}
                path.write_text(json.dumps(body), encoding="utf-8")
                time.sleep(0.5)
                return body
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response is not None and exc.response.status_code == 429:
                    time.sleep(min(2 ** attempt, 20))
                    continue
                raise
    raise last_exc or RuntimeError("request failed")


def fetch_wiktionary(word: str) -> dict:
    url = "https://en.wiktionary.org/w/api.php"
    params = {
        "action": "parse",
        "page": word,
        "prop": "wikitext",
        "format": "json",
        "formatversion": "2",
        "redirects": "1",
    }
    try:
        raw = cached_get("wiktionary", url, params)
        wikitext = (raw.get("json") or {}).get("parse", {}).get("wikitext") or ""
        return {
            "ok": True,
            "url": f"https://en.wiktionary.org/wiki/{quote(word)}",
            "wikitext": wikitext,
        }
    except Exception as exc:
        return {
            "ok": False,
            "url": f"https://en.wiktionary.org/wiki/{quote(word)}",
            "error": str(exc),
            "wikitext": "",
        }


def _english_section(wikitext: str) -> str:
    parts = re.split(r"(?m)^==(?!=)\s*", wikitext)
    for part in parts:
        if re.match(r"English\s*==", part):
            return "==" + part
    return wikitext


def etymology_sections(wikitext: str) -> list[str]:
    english = _english_section(wikitext)
    out = []
    for m in re.finditer(
        r"(?ms)^===\s*Etymology(?:\s+\d+)?\s*===\s*(.*?)(?=^==|\Z)",
        english,
    ):
        body = m.group(1).strip()
        if body:
            out.append(body)
    return out


_LEMMA = re.compile(
    r"\{\{\s*(?:infl of|verb form of|noun form of|adj form of|past participle of|"
    r"participle of|lemma of)\|en\|([^}|]+)",
    re.I,
)


def lemma_of(wikitext: str) -> Optional[str]:
    m = _LEMMA.search(wikitext or "")
    if not m:
        return None
    return m.group(1).strip()


def wiki_root_ids(wikitext: str) -> list[str]:
    ids = []
    for m in re.finditer(r"\{\{\s*root\|en\|([^}]+)\}\}", wikitext or "", re.I):
        ids.append(re.sub(r"\|id=[^|}]+", "", m.group(1)).strip())
    return list(dict.fromkeys(ids))


_TMPL = re.compile(
    r"\{\{\s*(inh|der|bor|ud)\+?\s*\|([^}]*)\}\}",
    re.I,
)

_LANG = {
    "en": "English",
    "enm": "Middle English",
    "ang": "Old English",
    "la": "Latin",
    "fr": "French",
    "fro": "Old French",
    "xno": "Anglo-Norman",
    "it": "Italian",
    "nl": "Dutch",
    "de": "German",
    "gmh": "Middle High German",
    "gmw-pro": "Proto-West-Germanic",
    "non": "Old Norse",
    "grc": "Ancient Greek",
    "gem-pro": "Proto-Germanic",
    "ine-pro": "Proto-Indo-European",
    "itc-pro": "Proto-Italic",
}


def _clean_form(form: str) -> str:
    form = unescape(form).strip()
    form = re.sub(r"<[^>]+>", "", form)
    form = form.replace("'''", "").replace("''", "")
    return form.strip()


def parse_etymology_templates(sections: list[str]) -> tuple[list[FromStep], list[str]]:
    steps: list[FromStep] = []
    quotes: list[str] = []
    seen: set[tuple] = set()
    for sec in sections:
        quotes.append(re.sub(r"\s+", " ", sec)[:900])
        for m in _TMPL.finditer(sec):
            kind, inner = m.group(1).lower(), m.group(2)
            parts = [p.strip() for p in inner.split("|")]
            positional = [p for p in parts if p and "=" not in p]
            if len(positional) < 2:
                continue
            if kind in {"m", "l"}:
                lang_code, form = positional[0], positional[1]
            elif kind == "root":
                lang_code = positional[1] if len(positional) > 1 else positional[0]
                form = positional[2] if len(positional) > 2 else positional[1]
            else:
                # {{inh|en|ang|þynne}}
                lang_code = positional[1]
                form = positional[2] if len(positional) > 2 else ""
            form = _clean_form(form)
            if not form or form.endswith("-") or len(form) < 2:
                continue
            if lang_code in {"t", "lit", "pos", "id"}:
                continue
            lang = _LANG.get(lang_code, lang_code)
            key = (lang, form)
            if form and key not in seen:
                seen.add(key)
                steps.append(FromStep(lang=lang, form=form))
        years = [int(y) for y in re.findall(
            r"(?:attested|borrowed|first recorded)[^\d]{0,24}\b(1[0-9]{3})\b",
            sec,
            flags=re.I,
        )]
        if years and steps:
            if not any(s.year is not None for s in steps):
                eng = next((s for s in reversed(steps) if s.lang == "English"), None)
                if eng:
                    eng.year = years[0]
                else:
                    steps.append(FromStep(lang="English", year=years[0]))
    # Templates list the immediate source first; the cube schema is oldest → English.
    steps.reverse()
    return steps, quotes


def strip_html(text: str) -> str:
    text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_etymonline(word: str) -> dict:
    url = f"https://www.etymonline.com/word/{quote(word)}"
    try:
        raw = cached_get("etymonline", url)
        html = raw.get("text") or ""
        og = ""
        m = re.search(r'(?is)property="og:description"\s+content="([^"]+)"', html)
        if m:
            og = unescape(m.group(1))
        m = re.search(r'(?is)(from [A-Z][^.]{12,500}\.)', strip_html(html))
        sentence = m.group(1) if m else ""
        text = " ".join(p for p in (og, sentence) if p).strip()
        if not text:
            text = strip_html(html)[200:900]
        return {"ok": True, "url": url, "text": text[:1500]}
    except Exception as exc:
        return {"ok": False, "url": url, "error": str(exc), "text": ""}


def fetch_ngrams(word: str) -> dict:
    url = "https://books.google.com/ngrams/json"
    params = {
        "content": word,
        "year_start": str(USAGE_YEARS[0]),
        "year_end": str(USAGE_YEARS[-1]),
        "corpus": "en-2019",
        "smoothing": "3",
    }
    try:
        raw = cached_get("ngrams", url, params)
        series = raw.get("json")
        if not series:
            params = dict(params)
            params["corpus"] = "26"
            raw = cached_get("ngrams", url, params)
            series = raw.get("json")
        if not series:
            return {"ok": False, "url": url, "error": "empty ngram payload", "usage": None, "raw": None}
        row = series[0] if isinstance(series, list) else series
        timeseries = row.get("timeseries") or []
        start = int(row.get("year_start") or USAGE_YEARS[0])
        by_year = {start + i: float(v) for i, v in enumerate(timeseries)}
        samples = [by_year.get(y) for y in USAGE_YEARS]
        if any(v is None for v in samples):
            return {"ok": False, "url": str(raw.get("url") or url), "error": "missing year samples", "usage": None}
        peak = max(samples) or 1.0
        scaled = [round(v / peak, 4) for v in samples]
        return {
            "ok": True,
            "url": str(raw.get("url") or url),
            "usage": scaled,
            "raw": [round(v, 12) for v in samples],
        }
    except Exception as exc:
        return {"ok": False, "url": url, "error": str(exc), "usage": None}


def evidence_pack(word: str) -> tuple[list[Evidence], dict]:
    wiki = fetch_wiktionary(word)
    ety = fetch_etymonline(word)
    ngram = fetch_ngrams(word)
    ev: list[Evidence] = []
    secs = etymology_sections(wiki.get("wikitext") or "")
    if not secs:
        lemma = lemma_of(wiki.get("wikitext") or "")
        if lemma:
            followed = fetch_wiktionary(lemma)
            secs = etymology_sections(followed.get("wikitext") or "")
    if secs:
        ev.append(Evidence(source="wiktionary", url=wiki["url"], quote=re.sub(r"\s+", " ", secs[0])[:700]))
    elif wiki.get("wikitext"):
        ev.append(Evidence(source="wiktionary", url=wiki["url"], quote=re.sub(r"\s+", " ", wiki["wikitext"][:400])))
    elif wiki.get("error"):
        ev.append(Evidence(source="wiktionary", url=wiki["url"], quote=f"ERROR: {wiki['error']}"))
    if ety.get("text"):
        ev.append(Evidence(source="etymonline", url=ety["url"], quote=ety["text"][:700]))
    elif ety.get("error"):
        ev.append(Evidence(source="etymonline", url=ety["url"], quote=f"ERROR: {ety['error']}"))
    if ngram.get("ok"):
        ev.append(
            Evidence(
                source="ngrams",
                url=ngram["url"],
                quote=f"years {list(USAGE_YEARS)} scaled={ngram['usage']} raw={ngram['raw']}",
            )
        )
    elif ngram.get("error"):
        ev.append(Evidence(source="ngrams", url=ngram.get("url", ""), quote=f"ERROR: {ngram['error']}"))
    return ev, {"wiktionary": wiki, "etymonline": ety, "ngrams": ngram}


def grounded_extract(
    wiki: dict, ety: dict, depth: int = 0
) -> tuple[list[FromStep], Optional[Root], list[str], bool, list[str]]:
    wikitext = wiki.get("wikitext") or ""
    secs = etymology_sections(wikitext)
    roots = wiki_root_ids(wikitext)
    if not secs and depth < 2:
        lemma = lemma_of(wikitext)
        if lemma:
            followed = fetch_wiktionary(lemma)
            if followed.get("wikitext"):
                return grounded_extract(followed, ety, depth + 1)
    steps, quotes = parse_etymology_templates(secs)
    if ety.get("text"):
        quotes.append(ety["text"][:700])
    blob = " ".join(quotes)
    year_grounded = any(s.year is not None and str(s.year) in blob for s in steps)
    root = None
    if steps:
        first = next((s for s in steps if s.form), steps[0])
        rid = re.sub(r"[^a-z0-9]+", "-", (first.form or first.lang).lower()).strip("-")
        root = Root(id=rid or "unknown", form=first.form or first.lang, gloss="")
    elif roots:
        # Keep PIE template ids for linking; do not invent a cube root without a form trail.
        root = None
    return steps, root, quotes, year_grounded, roots
