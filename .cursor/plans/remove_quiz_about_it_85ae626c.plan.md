---
name: Remove quiz About it
overview: Remove the Origin / Usage / Root “About it” buttons from the quiz result bar. Those sections stay in the detail panel, where you can already scroll to them.
todos:
  - id: drop-about-row
    content: Remove About it buttons and data-panel listeners from renderQuizBar
    status: completed
isProject: false
---

# Remove About it from the quiz bar

In [`renderQuizBar()`](nuance-cube-v0.1.html), when a quiz is done, drop the second `.quizActs` row that currently builds **About it** → Origin / Usage / Root, plus the `[data-panel]` click handlers that `scrollIntoView` those blocks.

Keep **This word on** (axis / both-at-once) and **Another word** / **Stop quizzing**.

Leave the detail-panel ids (`detailOrigin`, `detailUsage`, `detailRoot`) in [`renderDetail()`](nuance-cube-v0.1.html). They do not show in the quiz bar; Origin, Usage, and Root remain in the stacked detail column for scrolling.

No scoring, layout, or CSS changes unless the unused `.quizActs` rules still apply to the remaining rows (they do — leave them).
