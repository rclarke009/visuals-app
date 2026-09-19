---
name: Fix walk family
overview: "Correct the walk family’s example data in the nuance cube: keep march, but stop treating it as the forceful end. Add trudge and stomp there, and rewrite the insight so intensity means effort, not speed or cadence."
todos:
  - id: rewrite-walk-data
    content: "Update walk family in nuance-cube-v0.1.html: reposition march, add trudge and stomp, rewrite prompt/insight/glosses/examples"
    status: completed
  - id: verify-walk-lesson
    content: Open the walk family in the browser and confirm intensity reveal, placements, and glosses
    status: completed
isProject: false
---

# Fix the walk family placements

The croak / expire critique is right, and it is the risk the prototype already names: a wrong point costs more than a missing family. That family is **not in the live file**. It was swapped for `smelly` and will stay out.

The live error is [`nuance-cube-v0.1.html`](nuance-cube-v0.1.html): `march` sits at the high-intensity pole (`y: 0.85`) with the insight “amble and march are the same action at opposite ends of effort.” That treats cadence as force.

## What changes

Only the `walk` object in `FAMILIES` (prompt, insight, word list). Lesson, quiz, and home cards already scale with `words.length`; seven words matches `thin`, so no layout code change.

Keep `answer: ['intensity']`. The axis still separates the family. The glosses have to stop implying that intensity means speed.

## Placements

Keep amble, stroll, walk, stride. Keep march, move it off the force pole. Add trudge and stomp.

- **amble / stroll** — stay at the mild end (little effort, no hurry).
- **walk** — origin.
- **stride** — long, confident steps; purpose without heaviness. Mid-high `y`, warm `x`.
- **march** — measured rhythm and a destination, military or determined. Similar `y` to stride (not the extreme), higher `z` (more formal/cadenced), near-neutral `x`. Gloss must say cadence, not force.
- **trudge** — slow, reluctant, the ground resisting. High `y` (effort), cool `x` (weary, unwelcome). This is the word that proves intensity here is work, not speed.
- **stomp** — each foot put down hard, usually in anger. Highest `y`, harshest `x`. This is force.

Draft insight (final wording in the file): the body-work axis runs from amble to trudge/stomp. March would land at the wrong end if you read that axis as speed. Stride and march share purpose; only one of them is a beat.

Rewrite the prompt from “Five ways of going on foot” to seven.

## Out of scope

No `die` family. No axis-system change. No new families. After the edit, check the walk lesson in the browser: guess intensity, confirm march is no longer the far pole, and that trudge/stomp read as the heavy end.
