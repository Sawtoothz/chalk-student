# Slides spec (stage `slides`)

Two slide decks per unit (PDF study copies), built from the **reviewed** package after the `review` stage:

| Deck | File | For | Chapter | Paper |
| --- | --- | --- | --- | --- |
| Class | `slides/class.yaml` | Aun teaching his students at KMUTNB: a 60–90 min lecture (paper: a 30–45 min talk) | 20–30 slides | 12–18 slides |
| Review | `slides/review.yaml` | Aun revising on his own: dense, one idea per slide, equation-to-code | 20–30 slides | 12–18 slides |

You write the two YAML files. `scripts/make_slides.py` turns each into `slides/<style>.pdf`, a study copy: the
`.pptx` it lays out with is temporary and deleted, and every page gets a visible "Created by Chalk" watermark and an
invisible notice to AI assistants. `scripts/check_slides.py` checks the decks and the marks; `just view` puts them in
the Reader's Slides tab. This is the student edition: never produce a `.pptx` or other editable deck from these files.

## Reads, must not read

Read: `map.md`, `lecture.md`, `translate.md`, `README.md`, `REVIEW.md` (so a fixed error is not reintroduced),
`figures/*.png` (look at the ones you use), `figures/*.json`; for a paper also `implementation.md`.
Must not read: the chapter or paper PDF, `highlights.json`, anything under `exercises/solutions/`. The decks
restate what the reviewer has already checked; a slide that needs something the package does not say is a slide
to drop, not a reason to open the book.

## The theme is not yours

The renderer uses a plain white Office theme on purpose: standard layouts, titles and bullets in placeholders,
Arial as the theme font. Its diagram layouts (cards, step arrows, number tiles, panels, code colours) are drawn in the
theme's accent slots, which the plain theme fills with the figure palette (blue, coral, teal, amber), so Aun's own
theme in PowerPoint restyles them too. So: you never pick a colour, no decorative slides, no emoji, no "styling" in
the text. Emphasis is `**bold**` and `` `code` `` inside a bullet, nothing else.

## Rich, not dense

A deck of bullet lists is a lecture file with page breaks. Show structure with the diagram layouts:

| Content | Layout |
| --- | --- |
| roadmap, outline, "where we are" | `agenda` (set `current` to highlight one item when you return to it) |
| an algorithm table, a pipeline, a derivation in stages | `steps`: 2–5 cards with arrows, one per line group or stage |
| two methods, before / after, Gaussian vs nonparametric, naive vs robust | `compare`: 2–3 headed columns |
| results the package measured (errors, timings, ANEES) | `stats`: 2–4 big numbers with labels |
| the one sentence a section exists to teach | `key`: a large statement and an optional detail line |
| a Predict question | `predict`: the question in a card, optional context bullets, optional A–D `choices` |

And on the slides you already write:

- `takeaway:` on any content slide: one sentence (≤ 90 characters) shown in a bar above the footer. Use it on
  figure and equation slides to say what the picture or formula proves.
- `where:` on an `equation` slide: the symbols and what they mean, `[["Σ", "covariance, 3×3"], …]`, ≤ 6 rows.
- `code` slides are syntax-coloured; section dividers are numbered "Part k of n" automatically.

`check_slides.py` fails a class deck with fewer than 4 diagram slides (`agenda steps compare stats key predict`) or
more than 40% plain `bullets` slides, a review deck with fewer than 2, and any deck with three plain `bullets`
slides in a row.

## Class deck

The arc of a lecture, not a summary of the lecture file:

1. `title`: chapter title; subtitle = book and chapter (paper: authors and venue); meta = lesson id and authors.
2. Why it matters: one `bullets` or `figure` slide with the robot problem the chapter solves.
3. Roadmap: an `agenda` of the must-read sections (3–6 items); repeat it with `current` set before a long part if
   it helps students keep their place.
4. For each must-read section (in `map.md` order), 2–5 slides from its four lecture layers:
   Picture (`figure` with the lecture's figure and a `takeaway`), Intuition (`bullets`, `compare` or `key`),
   Formal (`equation` with the book's numbering as the label and a `where` legend; an algorithm table as `steps`),
   and where it helps a **Predict** slide (`predict` layout): title starts "Predict:", the question on the slide,
   the answer and the reasoning in the notes only. Choices, if any, include the right answer and plausible wrong
   ones; never mark which is right on the slide.
   A skim section gets at most one slide; a skip section none.
5. Traps: a `table` from the lecture's symptom-to-fix table or the map's trap list (≤ 8 rows).
6. Summary: 3–6 bullets, each a claim a student should be able to defend; or a `key` slide followed by the bullets.
7. What comes next: the chapters this one feeds (`map.md` `feeds`).

Speaker notes are required on every slide except `title` and `section`: 50–150 words of what to say, the
derivation steps the slide skips, and one question to ask the room. Write for students, not for Aun: no "you
asked", no "your robots"; say "a tracked robot", "a quadruped", "a drone". Exercises may be named ("T2 asks you to
derive (5.18)") but never answered, and no code from `exercises/` appears on any slide.

## Review deck

Denser and for one reader:

- `title`, an `agenda`, then one slide per must-read section with its single key result (equation or claim), the
  page it is on, and the trap that goes with it (an `equation` with a `takeaway` naming the trap works well).
- One `code` slide per card that matters: the card's naive or robust code (copied from `translate.md`, ≤ 14 lines),
  bullets naming the trick.
- A shapes / cost `table` where the cards have one; naive versus robust code as a `compare`; measured numbers from
  the package as `stats`.
- The symptom-to-fix table; the reviewer's catches from `REVIEW.md` as a "Mistakes already made" slide.
- Paper: the implementation plan from `implementation.md` (steps, data structures, what to build first).
- Notes optional, ≤ 60 words.

## Format

```yaml
title: "Robot Motion"                                   # deck title
footer: "Thrun · Probabilistic Robotics · ch. 5"        # shown on every content slide
slides:
  - layout: title
    title: "Robot Motion"
    subtitle: "Probabilistic Robotics, chapter 5"
    meta: "Lesson t2.4 · Thrun, Burgard, Fox"
    source: map.md
  - layout: section                                     # divider: title, optional subtitle
    title: "5.3 The velocity motion model"
    source: lecture.md §5.3
  - layout: bullets
    title: "Two forms of every motion model"            # ≤ 60 characters: one line
    bullets:                                            # ≤ 6 top-level items, ≤ 110 characters each
      - "**Density** p(xₜ ∣ uₜ, xₜ₋₁): invert the kinematics, score the deviation"
      - text: "**Sampling**: perturb the parameters, run the kinematics forward"
        sub: ["Table 5.3 for velocity, Table 5.6 for odometry"]   # ≤ 3 sub-items
    notes: "…"
    source: lecture.md §5.2
  - layout: figure                                      # figure alone, or with ≤ 4 short bullets on the right
    title: "Exact motion is a circle"
    figure: figures/L2-circle.png                       # an existing PNG in the package
    caption: "Constant (v, ω) over Δt"                  # optional, one line
    source: lecture.md §5.3.3
  - layout: equation                                    # 1–3 equations, optional ≤ 3 bullets below
    title: "Motion on the circle"
    equations:
      - {tex: 'x^\prime = x - \frac{v}{\omega}\sin\theta + \frac{v}{\omega}\sin(\theta + \omega\Delta t)', label: "(5.9)"}
    bullets: ["r = v/ω is the radius"]
    source: lecture.md §5.3.3
  - layout: code                                        # ≤ 14 lines, ≤ 70 characters wide; optional ≤ 3 bullets
    title: "Sampling the velocity model"
    code: |
      def sample(u, x, a, dt, rng): ...
    source: translate.md C2
  - layout: table                                       # ≤ 8 rows, ≤ 4 columns, short cells
    title: "Symptom to fix"
    table: {header: [Symptom, Cause, Fix], rows: [[…, …, …]], widths: [2, 2, 3]}
    source: lecture.md symptom table
  - layout: agenda                                      # 2–7 items; current (1-based) highlights one, fades the rest
    title: "Roadmap"
    items: ["5.3 Velocity model", "5.4 Odometry model", "5.5 Motion and maps"]
    current: 2
    source: map.md
  - layout: steps                                       # 2–5 cards: title ≤ 20 chars, text ≤ 110 chars; ≤ 2 bullets below
    title: "Sampling the odometry model, Table 5.6"
    steps:
      - {title: "Recover", text: "Turn the odometry pair into δrot1, δtrans, δrot2"}
      - {title: "Perturb", text: "Add noise scaled by α1…α4 to each of the three"}
      - {title: "Compose", text: "Apply the noisy motion to the old pose"}
    takeaway: "Noise enters in the robot's motion parameters, not in x and y"
    source: lecture.md §5.4
  - layout: compare                                     # 2–3 columns: heading ≤ 30 chars, ≤ 5 bullets each
    title: "Velocity or odometry?"
    columns:
      - {heading: "Velocity model", bullets: ["Uses commands, before the motion", "Needed for planning"]}
      - {heading: "Odometry model", bullets: ["Uses wheel encoders, after the motion", "Usually more accurate"]}
    source: lecture.md §5.4
  - layout: stats                                       # 2–4 tiles; every value is a number from the package
    title: "What the ring corridor shows"
    stats: [{value: "0.990", label: "bel after fifteen hits"}, {value: "0.000", label: "with the prior forgotten"}]
    bullets: ["…"]                                      # optional, ≤ 2
    source: figures/L4-log-odds.json
  - layout: key                                         # one statement (≤ 120 chars), optional detail line
    title: "The one idea"
    statement: "A motion model is a probability over where the robot ends up, not a pose"
    detail: "Every filter in the book calls it in its prediction step"
    source: lecture.md §5.1
  - layout: predict                                     # question ≤ 140 chars; ≤ 3 context bullets; ≤ 4 choices
    title: "Predict: what does the cloud look like?"
    bullets: ["α1 large, all other α small"]
    question: "After 20 steps, which way does the sample cloud stretch?"
    choices: ["Along the heading", "Across the heading, a banana", "A round blob", "It does not grow"]
    notes: "Answer and reasoning here, never on the slide."
    source: lecture.md §5.4
```

Any content slide may add `takeaway: "…"`; an `equation` slide may add
`where: [["xₜ", "pose at time t"], ["α₁", "rotation noise from rotation"]]`.

Every slide has `source`: the package file and section it restates (`lecture.md §5.3`, `translate.md C3`,
`map.md traps`, `REVIEW.md`). Use single quotes around `tex` so backslashes survive YAML.

### Equations

Drawn by matplotlib mathtext, not TeX. Supported: `\frac \dfrac \sqrt \hat \bar \tilde \dot \widehat \overline`,
`\sum \int \partial \nabla`, Greek, `\mathbf \boldsymbol \mathrm \mathcal \mathbb \text \operatorname`,
`\left( \right) \left[ \right]`, `\| \mid \top \oplus \boxplus \triangleq \approx \in \cdot \quad`, sub- and
superscripts. **Not supported**: any `\begin{…}` environment (matrices, cases, align), `\tfrac`, `\underbrace`,
`\lVert`. Write a matrix as a `table` slide or split it into component equations; write cases as two equations.
Copy the formula from the lecture's Formal layer or the card; do not re-derive it. Inline maths in bullets is
Unicode, as in `map.md` (xₜ, Σ, ∂, θ̂).

### Numbers

Every decimal number on a slide or in its notes must already appear in the package's reviewed text or
`figures/*.json` (`check_slides.py` fails otherwise). Quote, do not recompute.

## Check and finish

1. Write `slides/class.yaml` and `slides/review.yaml`.
2. `just slides <book> <unit>`: renders both decks, runs `check_slides.py`, rebuilds the Reader.
3. Fix every FAIL. A "title runs into the content area" means shorten the title; "text runs into the footer"
   means cut bullets or split the slide.
4. Look at the rendered PDFs (Read `slides/class.pdf` with `pages`, a few at a time): figures readable, nothing
   crowded, the arc of the class deck makes sense in order.
5. Append a `## Slides` section to `HANDOFF.md` (date, slide counts, check verdict). Do not rewrite the rest: the
   review stage's decisions and open questions stay. Reply to Aun in three lines.
