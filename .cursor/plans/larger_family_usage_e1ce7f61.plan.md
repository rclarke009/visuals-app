---
name: Larger family usage
overview: Enlarge the usage chart in the detail panel and label every family member’s curve so sibling histories are readable, not just faint traces behind the selected word.
todos:
  - id: enlarge-svg
    content: Widen usageSpark viewBox/CSS (~640x200, full-width, year ticks) and restyle selected vs sibling strokes
    status: completed
  - id: label-siblings
    content: End-label every family curve with vertical dodge; click label/path to select that word
    status: completed
isProject: false
---

# Larger family usage chart

Sibling curves are already drawn in [`usageSpark()`](nuance-cube-v0.1.html) (~line 1210) at 35% opacity with no labels, inside a 300×52 viewBox capped at 420×52px. That is why they disappear. Keep the same six hand-sampled points; only the drawing and CSS change.

## Bigger chart

In CSS, drop the 420px cap so `.usageSvg` is full width of the detail panel and about **180px** tall.

Rebuild the SVG around a wider viewBox, e.g. `0 0 640 200`: more plot height, room for year ticks (`1800 1850 1900 1950 2000 2019`) along the baseline, and a right gutter (~90px) for end labels.

## Other words, readable

Draw every word in the family, not only the selected one:

- Stroke with `connColor(w.x)` (same cool/warm as the cube) so lines stay distinct without a new palette.
- Selected word last, gold, thicker (~2.4), dots on the samples.
- Siblings at ~0.7 opacity, thinner (~1.3).
- **End label** at 2019: the word itself, same colour. If two labels would overlap, nudge them apart by the last sample’s y (simple vertical dodge).
- Labels are `data-jump` buttons in spirit: put `data-i` on `<text>` and bind clicks in `renderDetail()` the same way root chips already call `select()`. Clicking a sibling curve or label switches the detail panel to that word.

Caption stays honest: still own-peak scaled, Google Books English, now “gold is the word you picked; the others are the rest of this family.”

No new data, no change to the cube, trails, or roots. The selected word’s language trail stays above the chart as the one-word etymology; the chart is the family history.
