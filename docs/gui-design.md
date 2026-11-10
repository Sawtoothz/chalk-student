# Chalk GUI — design plan

The GUI is the desk side of Chalk: a place to put a book or a paper down, ask the professor to prepare one chapter, watch it being prepared, and open the result. It is not a dashboard and not a SaaS console. Everything on screen is either a source, a chapter, a stage, or the thing a stage produced.

## Tokens

Colour (shared with the Reader; `viz/web/figure.css` roles stay the same)

| name     | hex       | use |
|----------|-----------|-----|
| paper    | `#f7f5ef` | page background |
| sheet    | `#fffdf8` | ledger rows, panels, log |
| ink      | `#1f1e1d` | text, finished stages |
| ink-soft | `#5b5952` | secondary text |
| rule     | `#dedbd1` | hairlines, pending stages |
| chalk    | `#1d9e75` | the one accent: running stage, primary action, focus |
| fault    | `#a32d2d` | a stage that failed |

Stage track colours carry the same meaning as the highlight legend: a finished stage is ink, the running stage is chalk, a failed stage is fault, a pending stage is rule. No other colour appears in the chrome. Blue/coral/teal are reserved for figures inside packages. (A louder, hand-lettered variant was tried and rejected as too playful; this restrained version stands.)

The Run page shows the stage list and the live log only; an earlier animated page reader ("crawlers") was removed on 2026-11-06 as off-theme.

Type

- Source Serif 4 — book and paper titles, chapter titles, HANDOFF summaries. The things that came from a book look like a book.
- IBM Plex Sans — everything the interface says: buttons, statuses, counts, page numbers (tabular figures).
- IBM Plex Mono — only the live `claude -p` log and file paths. Never for labels.

Scale: 13 / 14.5 / 17 / 22 / 30 px. Weights 400 and 600 only. No all-caps, no letter-spaced eyebrows, no middle-dot meta strings.

## Layout

Three pages, same frame: a thin top bar (wordmark, page name, who is running), then a single column of at most 1040 px, left-aligned, 24 px gutter.

Library

```
Chalk     Library   Run   Reader                           claude · opus 5.5 ready
──────────────────────────────────────────────────────────────────────────────
Probabilistic Robotics                     Thrun, Burgard, Fox · 2005 · book
offset 21 · 17 chapters mapped from the table of contents

 2  Recursive State Estimation      pp. 13–38   ▮▮▮▮▮▮▮▮  Reader  Session
 3  Gaussian Filters                pp. 39–81   ▮▮▮▮▮▮▮▮  Reader  Session
 4  Nonparametric Filters           pp. 85–116  ▮▮▮▮▯▯▯▯  running: exercises
 5  Robot Motion                    pp. 117–148 ▯▯▯▯▯▯▯▯  Teach
 …

Estimation with Applications to Tracking…  Bar-Shalom · 2001 · book
chapters not mapped yet — set the page offset                 Set offset

A tutorial on graph-based SLAM             Grisetti et al. · 2010 · paper
 1  whole paper                     16 pages    ▯▯▯▯▯▯▯▯  Teach

┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
  Drop a PDF here, or choose a file.  Books get a chapter list; papers one unit.
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

The ledger row is the unit of the page: chapter number, title in serif, page range, the eight-segment stage track, and the one action that makes sense for that row's state. Rows are ruled, not boxed. Sources are separated by their title block, not by cards.

Run

```
Chalk     Library   Run   Reader
──────────────────────────────────────────────────────────────────────────────
Gaussian Filters                                     Probabilistic Robotics, ch. 3

 map        done 4 min        ┌─────────────────────────────────────────────┐
 highlight  done 11 min       │ › Read examples/…/highlight-spec.md          │
 lecture    done 9 min        │ › Read pages 39–52 (annotated.pdf)           │
 cards      done 6 min        │ Writing exercises/T3_implement/exercise.py   │
 exercises  running 3:12      │ › Bash pytest exercises/tests -q             │
 session                      │   12 passed, 3 failed (stubs, expected)      │
 build                        │                                              │
 review                       └─────────────────────────────────────────────┘
                                                                    Stop this stage
 Last handoff
 Cards C1–C5 written. C4 (UKF sigma points) uses √(n+λ); T3 should test
 the small-α weights. Exercises stage: write T1–T5, tests, clues.         Continue to session
```

The stage list is a real sequence, so it is numbered by position and reads top to bottom; the running stage is the only chalk-coloured thing on the page. The log is the one monospace region. The last HANDOFF is set in serif because it is prose from the professor, not system output.

Reader — unchanged (already built by `build_viewer.py`), embedded in the same frame.

Slides tab (added 2026-11-10): after `review`, the ledger row offers **Make slides** (stage `slides`, Sonnet). It writes `slides/class.yaml` (for Aun's students, with speaker notes) and `slides/review.yaml` (for Aun); `scripts/make_slides.py` renders each to `.pptx` (plain white Office theme, placeholders only, so a PowerPoint theme restyles it) and `.pdf` (LibreOffice). The Reader's Slides tab shows the PDF pages as images with a Class / Review toggle, arrow keys, full screen, the speaker notes and a `.pptx` download (`GET /reader/{source}/{unit}/slides/{class|review}.{pptx|pdf}`).

## Principles

1. The stage track is the memorable element. It appears in the ledger, in the Run page header, and in the browser tab title while a stage runs. Everything else stays quiet.
2. Structure encodes state: ruled rows, a dashed slot for the one thing that accepts a drop, a solid border only around the live log.
3. One action per row. The button says what happens: Teach, Continue to session, Open reader, Set offset, Stop this stage. The same verb is used in the CLI (`just teach`).
4. Empty and failed states give the next move, not a mood: "No sources yet — drop a PDF below." "Stage exercises stopped at pytest. Open the log, fix, then Continue."
5. Motion only answers an action: a segment turning chalk when a stage starts, the log autoscrolling. No entrance animations.

## Review against defaults

- Paper neutrals + serif + warm accent is a current cliché. The paper neutrals and serif are inherited from the Reader (the brief's own style), so they stay; the accent is the Reader's teal, not terracotta, and the chrome uses no gradient, no card shadow, no rounded-card grid.
- Status chips (green/amber/red pills) were replaced by the stage track, which carries more information in less chrome.
- All-caps section labels in the Reader notes sidebar (`.notes h2`, `.note .k`) are a tell — change them to sentence case in `build_viewer.py` in the next revision.
- Mono is restricted to the log; page numbers use tabular sans.
- Numbered stages are justified: the pipeline is a sequence.

## Implementation (app/)

Built as designed: `app/main.py` (FastAPI), `app/templates/{base,library,run}.html`, `app/static/chalk.css` + `shelf.js`; `scripts/ingest.py`, `scripts/run_stage.py`, `scripts/pages.py --list`. `docs/gui-mockup.html` remains the static mockup with simulated data.

## Backend touchpoints the pages need

- `GET /sources` → ledger data (`sources.yaml` + package status per unit, derived from which stage files exist and `HANDOFF.md`).
- `POST /sources` (multipart PDF) → `scripts/ingest.py` → chapter table or single unit; returns the new source for the ledger.
- `PUT /sources/{id}` → page offset / kind / unit edits.
- `POST /teach/{id}/{unit}?stage=next|<name>` → enqueue; `GET /jobs/{job}/stream` SSE for the log.
- `GET /packages/{id}/{unit}/reader` → the Reader HTML; `/session` → marimo.

## Library front: the shelf (2026-11-06, Aun's request)

The Library opens on a pixel-art shelf (`app/static/shelf.js`, a 480×200 canvas scaled with crisp pixels, drawn
from `pages.listing()`): a bookshelf and a filing box of papers on a side table. Each book on disk is a labelled spine
on the middle shelf (first author, 3×5 pixel font), with one green pixel per reviewed chapter; each paper is a tabbed
sheet in the box, with a green mark once its package is reviewed. Everything else on the shelves is decoration.
Hover lifts an item and shows title, authors and status.

Revised 2026-11-10 (Aun): the Library is one full-screen room with no page scroll. The canvas is as tall as the
window's aspect needs (extra wall above the room, with a CHALK chalkboard when there is room for it). Clicking a book
flies its closed cover from the spine to the middle of the screen, swings the cover open and inks the table of
contents across the two pages: each chapter with its pages, stage track, status and its one action (Teach, Continue
to <stage>, Make slides, Reader, Watch, Retry); longer books turn spreads (‹ › or arrow keys). A paper opens as a
manila folder: title and sections on the flap, its unit on a white sheet. Esc or the × closes it back onto the shelf.
`#<id>` in the URL opens that source directly. Adding a PDF is the ADD letter tray on the side table: click it, or
drop a PDF anywhere on the room, and an index card asks for the short name, kind and metadata; ingest errors show on
the card. While a stage runs, the open book refreshes its statuses from `GET /sources` every 4 s. One visually hidden button per item gives keyboard and screen-reader access. Earlier tries — an SVG
lecture room with Gauss and Euler, then a three.js room with a lecturer — were dropped.

## Auto-run (2026-11-10, Aun's request)

A switch in the top bar on every page (`POST /settings {auto}`, saved in `.cache/gui-settings.json`). When on, the
worker checks after each successful job whether the stage it ran now has its file; if so and the unit has a next
stage, it queues `next` for the same unit before the job is marked done, so the Run page's reload lands on the new
job. It stops when the switch is off, a stage fails or is stopped, a stage leaves no file (no loops), or every stage
including `slides` is done; each decision is a green line in the log. With it on, the open book's buttons read
"Teach all stages" and "Run <stage> → end". Overlays start below the top bar so the switch stays reachable.

## Chalky, the mascot (2026-11-10, Aun's request)

An original character: a stick of chalk in a green Chalk wrapper (`app/static/chalky.js`, drawn into the shelf canvas
at the room's 1-px scale, about 12 px tall). It plans one activity at a time at random — stroll the floor, look
around, nap (rising z's), read a tiny book, hop onto the window sill to watch the moon, a short dance, or hop up to the
chalkboard ledge, wipe the last formula and write a new one (`X=FX+BU`, `K=PH/S`, `WRAP IT!`…) letter by letter with
chalk dust. While a stage is running it writes more often, and a click may make it name the running stage; otherwise a
click makes it hop and say a Chalk tip in a speech bubble. The room animates continuously while Chalky is there
(the browser pauses it in hidden tabs); with reduced motion Chalky stands still and only answers clicks.

## Student edition (branch `student`)

Slides ship as PDF only. `make_slides.py` builds the `.pptx` in a temporary directory, converts it and deletes it;
`stamp()` then adds a faint diagonal "CREATED BY CHALK" and a corner line "Created by Chalk · study copy, not for
presenting" to every page, a boxed notice to AI assistants on the title slide (visible, so tools that read
pages as images see it), an invisible text layer (render mode 3, first in reading order) addressed to AI
assistants asking them not to convert the deck into an editable presentation, and the same notice in the PDF
metadata and XMP rights. `check_slides.py` fails a deck without the marks or with a `.pptx` beside it. The Reader
offers only the PDF. These are speed bumps, not protection: the YAML decks and the code are in the repository.

## Way back from the Reader

`reader.html` is a standalone file (it also opens from `file://`), so it carries no Chalk navigation. When the GUI
serves it (`/reader/<source>/<unit>`), `app/main.py` adds two links at the left of the Reader's header: **← Library**
(`/#<source>`, which reopens that book at its contents) and **Run** (the unit's stages and log). Esc does the same as
← Library, except inside a text field or full-screen slides. The Run page already has Library in the top bar.

## AI engine page

The top bar's **AI: <engine>** link opens `/ai`: one card per engine (Claude Code, OpenAI Codex CLI, Gemini CLI,
Custom command) with an installed / not-installed badge, install and login hints, a strong and a fast model field
(empty = the engine's default), the command template (folded; `{prompt}`, `{model}`, `{max_turns}`), and **Test**,
which saves and runs a one-line prompt through the engine. Saving picks the engine for every later job, Auto-run
included; a running job keeps the engine it started with. The Run page names the engine. `scripts/engines.py` holds
the engine table, the settings, the per-engine log readers (Claude stream-json, Codex JSONL, plain text) and the
prompt that tells a non-Claude agent to follow `.claude/skills/teach/SKILL.md`.

Because the page stores commands the GUI will run, every non-GET request must come from the GUI's own origin: a
cross-site form or fetch (foreign `Origin` or `Referer`) gets 403. Validation happens before anything is kept.
