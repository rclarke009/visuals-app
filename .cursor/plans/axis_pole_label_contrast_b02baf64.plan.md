---
name: Axis pole label contrast
overview: Give the axis pole labels (harsh, complimentary, mild, extreme, casual, formal) the same small-uppercase letterspaced treatment that already makes CONNOTATION unmistakable as chrome, so case alone separates labels from vocabulary without drawing anything new.
todos:
  - id: css
    content: Add .axPole class and the pole()/poleWidth() helpers, keeping .axEnd for the quiz prompts
    status: completed
  - id: sites
    content: Switch the six pole render sites (axis3, rulerLine, rulerField, sparkline) to uppercase axPole labels
    status: completed
  - id: rulerline
    content: Move rulerLine poles inside the ruler bounds and down into the axis-name band, fixing the narrow-viewport overflow
    status: completed
  - id: collision
    content: Correct both axisObstacles width measurements for uppercase plus letter-spacing
    status: completed
  - id: verify
    content: Check cube rotation, flat line and field views at desktop and under 760px in both themes, especially the vertical EXTREME label
    status: completed
isProject: false
---

## Why the poles read as words today

`wordFace` renders any word below the formality threshold in sans-serif:

```541:542:/Users/rebeccaclarke/Claude/Projects/visuals_app/nuance-cube-v0.1.html
/* formality -> typeface */
const wordFace   = z => z > 0.30 ? SERIF : SANS;
```

So in the cube, `harsh` and `skinny` are both lowercase sans, differing only in size and colour saturation. The one element that never gets mistaken for a word is `.axName`, because it is uppercase and letterspaced. Extending that treatment to the poles costs zero new ink and works in every view at once.

## The edits, all in [nuance-cube-v0.1.html](/Users/rebeccaclarke/Claude/Projects/visuals_app/nuance-cube-v0.1.html)

### 1. New `.axPole` class, alongside the existing two

`.axEnd` is also used for the quiz prompts "click where it belongs" and "your guess" (lines 992, 996, 1005), which should stay sentence case. So add a class rather than restyling `.axEnd`, near line 206:

```css
.axPole{font-family:var(--sans);font-size:10px;letter-spacing:1px;fill:var(--s-axEnd)}
```

Uppercase the strings in JS rather than using `text-transform`, so that what gets measured is what gets drawn. Size drops 11px to 10px because caps read heavier; tracking stays modest at 1px so `.axName` (10.5px / 1.5px, and a dimmer token) still sits a clear step back from the poles it sits under.

### 2. A pole helper next to `textWidth` (line 517)

`measureText` ignores letter-spacing, so width has to be added back by hand:

```js
const POLE_TRACK = 1;                       // keep in sync with .axPole letter-spacing
const pole = s => s.toUpperCase();
const poleWidth = (s, px, track) =>
  textWidth(pole(s), '400 '+px+'px '+SANS) + Math.max(0, pole(s).length-1)*track;
```

### 3. Swap the six pole render sites to `axPole` + `pole()` + `fs(10)`

- `axis3` lines 818-819 (the cube). `axName` under the high end stays as it is.
- `rulerLine` lines 841-842.
- `rulerField` lines 858-859 (horizontal) and 861-862 (vertical).
- `sparkline` lines 1034-1035 — these use inline attributes, not a class, so add `letter-spacing="1"` and `.toUpperCase()` there.

Leave the axis-guess buttons (line 1095) and the coordinate readout (line 1245) lowercase. Those are prose, where no word/label confusion is possible.

### 4. Move the line-view poles into the label band

`rulerLine` currently hangs them outside the ruler at `b[0]-9` / `b[1]+9` on the ruler's own baseline. On a phone that already overflows: `LB()[1]+9` is 841 against a viewBox that ends at 882, with "complimentary" at 18px running to roughly 960. Wider caps make it worse.

Anchor them inside the ruler ends and drop them to the axis-name band, matching what `rulerField` already does — `text-anchor="start"` at `b[0]`, `text-anchor="end"` at `b[1]`, baseline around `LY + 20*t`. This fixes the clipping and gets the poles off the word baseline, so the flat view reads as one horizontal band of chrome under the line.

### 5. Fix the de-collision measurements

`axisObstacles` (lines 895-898) is what keeps rotating words from landing on the axis labels. Both of its measurements need correcting:

- The pole obstacle measures the lowercase string at 11px: switch to `poleWidth(txt, 10*t, POLE_TRACK*t)`.
- The axis-name obstacle measures `name` lowercase at 10px with no tracking, while the label actually renders uppercase and letterspaced. "connotation" measures near 55px but draws near 78px, so this obstacle is under-sized today and words can already drift onto it. Measure `name.toUpperCase()` with its 1.5px tracking.

## Verify after

Rotate the cube through all three axes and check the flat line and field views on both a desktop width and under 760px, in both themes. The vertical poles in `rulerField` sit at `b[0]-10` anchored `end`, which on narrow is already close to the viewBox left edge — confirm "EXTREME" is not clipped there, and pull the offset in or shrink it if it is.