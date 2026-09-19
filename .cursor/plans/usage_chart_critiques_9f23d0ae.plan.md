---
name: Usage chart critiques
overview: Keep the chart as a family of own-peak career shapes. Incorporate the scaling and sampling warnings as copy, and flag words whose early Google Books counts mix a different sense. Do not add a raw-frequency toggle or an emotion-normalized chart.
todos:
  - id: sharpen-caption
    content: "Rewrite sparkCap: own-peak ≠ commonness, six coarse samples, shared 1950 corpus trough"
    status: completed
  - id: usage-notes
    content: Add usageNote on words whose Google Books curve mixes a different sense (livid first; pass the other families)
    status: completed
isProject: false
---

# Which usage-chart comments to keep

The chart in [`nuance-cube-v0.1.html`](nuance-cube-v0.1.html) is already the design from [word origin history](.cursor/plans/word_origin_history_efc7c1f8.plan.md): six hand-sampled years, **each curve scaled to that word’s own peak**, captioned as such. Heights are for *shape*, not prevalence. The four comments mix one real data bug, two reading problems the caption only half-solves, and one new product (a relative-frequency chart) that fights the prototype.

## Verdict

**Incorporate (copy + a curated flag)**
- Heights are not comparable across words — the caption already says own-peak; make that impossible to miss, including that 1950 is a shared corpus trough, not a special fact about anger.
- Six points are coarse — say so; do not recurate denser series.
- Livid (and similar words) mix senses — flag that on the selected word.

**Do not incorporate**
- A **raw-frequency toggle**. That needs unscaled Ngram rates for all 35 words. Rare members (`svelte`, `stinky`, `livid`) would flatten to the baseline, which is why own-peak scaling exists.
- **Dividing by “emotion words overall.”** That is a second chart with a new denominator series the file does not have. The 1950 dip is a Google Books composition artifact (copyright, corpus mix), not a family-specific story. Normalizing it would make the panel about the corpus, not about how these synonyms’ careers differ. One sentence in the caption is enough.

## What changes in the file

**1. Sharpen `.sparkCap` in `renderDetail()`** (today: “Each curve is scaled to that word’s own peak…”).

Replace with the same facts, tighter: own-peak so height is not commonness; six samples, so a single bump (e.g. annoyed at 1850) may be noise; a mid-century dip that every line shares is the corpus, not the family.

**2. Optional `usageNote` on a word**, shown only when that word is selected, under the caption.

Filter: flag when the **curve’s shape is polluted by another dominant sense**, not every etymology (roots already cover origin).

Likely flags after a short pass (confirm against Etymonline / OED while editing):

- `livid` — until ~early 1900s, mostly bruise-colour; the 1800 peak is not anger.
- `rank` — military/status/order dwarfs the smell sense in early counts.
- `bright` / `brilliant` — literal shine vs mind.
- `kid` — young goat vs child (early counts are the animal).
- `minor` — lesser / music vs legal age.
- `march` — month and military noun vs the gait.

Leave alone words whose early counts are already near zero in the lesson sense (`stinky`, `svelte`, `skinny`) or whose shift is already the root gloss without wrecking the shape.

Implementation: `if (w.usageNote)` append a second muted line in `.sparkWrap`. No extra chart chrome, no dashed segments.

**3. Schema comment** at the `usage` field (~line 349): notes are for sense-mix, not a second data series.

No change to `usageSpark()` geometry, sample count, cube, trails, or roots.
