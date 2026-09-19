---
name: Fix quiz feedback
overview: Flip the “closer to” lead so it describes the guess (not the target), and strip the numeric positions from the parenthetical so feedback only names the grade and which pole they overshot.
todos:
  - id: flip-lead
    content: In answerQuiz, change miss lead to “What you selected is closer to *word*.”
    status: completed
  - id: drop-numbers
    content: In describe(), keep grade + pole; remove put-at / sits-at / magnitude numbers.
    status: completed
isProject: false
---

# Fix backwards quiz lead and drop numbers

The copy is in [`answerQuiz()`](nuance-cube-v0.1.html) and [`describe()`](nuance-cube-v0.1.html). Scoring stays as-is: nearest sibling vs target, same `gradeWord` thresholds, same `err` / pole direction.

## Lead (backwards)

Today, when the click is nearer a sibling than the target:

> It’s closer to *thin* than what you selected.

“It” reads as the word being placed (`slim`). In the screenshot the guess *is* at *thin*; `slim` is not closer to *thin* than the click. The lesson is the opposite: **the click landed in another word’s neighborhood.**

Change the miss lead to:

> What you selected is closer to *thin*.

`thin` is still `wordLabel(near)`. Grade-only leads (`Close.` / `Spot on.` / `Off.`) are unchanged.

## Parenthetical (no numbers)

[`describe()`](nuance-cube-v0.1.html) currently emits:

> connotation: off. You put it at 0.07; it sits at 0.52. You had it 0.45 too far toward *harsh*.

Drop `got` / `truth` and the magnitude. Keep grade, axis name, and pole:

> connotation: off. You had it too far toward *harsh*.

Still omit spot-on axes; skip the whole paren if every scored axis is spot-on. `dir` from `err > 0 ? ax.hi : ax.lo` stays (in the screenshot, 0.07 vs 0.52 correctly points toward *harsh*).
