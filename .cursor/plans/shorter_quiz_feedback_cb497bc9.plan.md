---
name: Shorter quiz feedback
overview: Replace the long per-axis quiz result with a one-line lead (grade, or “closer to this other word”) and a compact parenthetical of the numbers you already compute.
todos:
  - id: lead-neighbor
    content: In answerQuiz, nearest-sibling vs target; lead with grade or “closer to *word* than what you selected.”
    status: completed
  - id: compact-paren
    content: Rewrite describe() to the compact parenthetical; omit spot-on axes and the confidence-band sentence.
    status: completed
isProject: false
---

The copy lives in [`describe()`](nuance-cube-v0.1.html) (~1783) and is concatenated in [`answerQuiz()`](nuance-cube-v0.1.html). A field miss currently dumps two of these:

> **connotation: close.** You put it at 0.25; it sits at 0.52. You had it 0.27 too far toward *harsh*. **intensity: …**

Drop the confidence-band sentence and stop repeating the axis name as a headline. Keep the same `gradeWord` thresholds and the same `got` / `truth` / pole math.

## Lead line

After scoring, find the family word whose plotted position is nearest the click (same axes the quiz is already scoring: line = `lineAxis`; field = `orderedAnswer(f)`). Exclude the target.

- If the click is nearer the **target** than any sibling, or `gradeWord` is `spot on` / `close`: lead with that grade only (`Close.` / `Spot on.` / `Off.`).
- Otherwise: **It's closer to *skinny* than what you selected.** — `skinny` is the nearest sibling; “what you selected” is the click, not another chip.

That is the useful lesson: you landed in someone else’s neighborhood.

## Parenthetical

One short clause per scored axis, only when that axis is not spot-on (if every scored axis is spot-on, skip the paren).

`(connotation: close. You put it at 0.25; it sits at 0.52. You had it 0.27 too far toward harsh.)`

Reuse today’s numbers; drop “inside its own confidence band.” Field layout can still mention both axes if both missed, but each is this one-liner, not a second bold headline.

`q.msg` stays HTML for `.qres`; italicize the sibling word the same way poles are italicized now. No cube, chart, or scoring-threshold changes.
