---
name: Chart label matching
overview: Make each usage-curve name sit next to a unique stretch of its line, instead of stacking all names on the 2019 pile. Isolated endpoints stay where they are; crowded ones move, with a short same-color leader if the label still has to dodge.
todos:
  - id: anchor-year
    content: In usageSpark, pick 2019 when clear, else the rightmost quiet sample; keep true x/y
    status: completed
  - id: place-leaders
    content: Position labels at that point, dodge collisions, draw same-color elbow leaders when shifted
    status: completed
  - id: verify-families
    content: Check walk (crowded) and a small family (uncrowded) plus click-to-select
    status: completed
isProject: false
---

# Make usage labels match their lines

The pile on the right is not a spacing bug. In the walk family, **stroll, walk, stride, trudge, and stomp all end at 1.0** in 2019, so they share one pixel. [`usageSpark()`](nuance-cube-v0.1.html) then dodges names 13px apart in the gutter with **no leaders**, so the stack no longer lines up with the endpoints. Color does not save it: those words sit close on the connotation axis, so their strokes look alike.

```mermaid
flowchart LR
  lastY[2019 y of each word] --> crowded{pixel gap vs others}
  crowded -->|clear| gutter[Keep name in right gutter]
  crowded -->|tied at peak] --> quiet[Label at rightmost quiet year]
  quiet --> dodge[Vertical dodge if names overlap]
  dodge --> leader[Hairline to the true point if shifted]
```

## Change (one function)

Only [`usageSpark()`](nuance-cube-v0.1.html) (~L1232–1322). Keep click-to-select, gold selected stroke/dots, mix hollow-dots, and caption.

For each series with `usage`:

1. **Prefer 2019** when its pixel-y is at least `minGap` (~14px) from every other series at that year (amble and march already qualify).
2. **Otherwise** pick the **rightmost year** with the largest min-gap to other series (ties: later year). That puts `stomp` on its low early line, `stride` near the 1950 bump, `trudge`/`walk` where they actually separate, instead of five names on one peak.
3. Place the `<text>` a few pixels to the right of that point (gutter if the year is 2019; inside the plot otherwise). `text-anchor="start"`. Selected word stays gold/bold; siblings keep `connColor`.
4. Remember **true y**. Run the existing sort + minGap dodge, clamped to `[top, bot]`.
5. If the dodged y is more than ~3px from true y, draw a **1px same-color polyline** from the point to the text (short elbow: out from the point, then to the label). No leader if the name already sits on the point.
6. Keep `data-jump` on labels, leaders, and paths.

Skip a mid-plot label that would sit on the selected word’s `usageMixTag` (nudge to the other side of the point, or fall back one year). Do not add a second palette, dots on siblings, or a legend.

## What should not change

- Own-peak scaling, six years, mix marks, cube, trails, roots.
- Families whose 2019 ends are already spread: they keep right-gutter names.

## Check

Open the walk family on **stride** (the crowded case in the screenshot) and on **march** (already isolated). Then one smaller family (e.g. thin) to confirm uncrowded charts still look like end-labeled sparklines. Confirm clicking a relocated name still selects that word.
