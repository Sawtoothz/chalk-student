# Package spec

One folder per chapter: `packages/<book>/chNN-<slug>/`. Every file below is required unless marked
optional. `scripts/check_package.py` enforces the structure.

```
chNN-<slug>/
  README.md                contents, highlight colour key, suggested order, how it was checked
  map.md                   chapter map (front matter + tables)
  highlights.json          source of the annotations
  annotated.pdf            built by highlight_pdf.py (gitignored)
  lecture.md               four-layer lecture
  figures/make_figures.py  generates figures/*.svg and *.png with viz.py.style
  translate.md             equation-to-code cards (papers: each card ends with "In the original code")
  implementation.md        papers only: the practical implementation proposal (see paper-code.md)
  code_refs.json           papers only: verified repo/commit/path:line anchors from scripts/code_refs.py
  session.py               marimo session
  interactive.html         browser version of the session (Plotly, plain JS), included in the Reader
  exercises/
    README.md              tiers, clue rules, grading
    T1_concept.md          6–10 short questions
    T2_derivation.md       2–4 derivations
    exercise.py            stubs with docstrings naming the book line/equation each implements
    models.py              the systems the exercises run on (never edited by Aun)
    T4_debug/<name>.py     a working implementation with 3–5 planted bugs
    T5_robot.md            the robot application exercise
    T5_sim.py              generates exercises/data/ (optional if T5 needs no data)
    clues.md               three-step ladders, one section per exercise
    tests/test_T3.py       oracle tests for the stubs; STUDY_IMPL=solution grades the reference
    tests/test_T4.py       grader for the planted bugs
    solutions/T1.md T2.md T3_solution.py T4.md T5.md
  REVIEW.md                reviewer record
  reader.html              built by build_viewer.py (gitignored)
```

## map.md

Front matter keys: `book`, `chapter`, `title`, `printed_pages`, `pdf_pages`, `lesson`, `prereqs`
(list, with where each is covered), `feeds` (list: later lessons and Aun's projects that use this),
`status`.

Body, in order:
1. One paragraph: the chapter's one idea and how its parts hang off it.
2. Section table: section, pages, verdict (must / skim / skip / do N,M), time, what to take.
   Total reading time at "must" and coding time, stated.
3. Inventory: definitions; algorithms; equations to implement; equations to derive by hand.
4. Dependencies inside the chapter, as an ASCII tree.
5. What the chapter does not cover and where that is (book, chapter, lesson id).

## highlights.json

See `highlight-spec.md`.

## lecture.md, translate.md, session.py

See `teaching-style.md`.

## exercises/

See `exercise-spec.md`.

## REVIEW.md

Sections: Verified correct; Confirmed errors (table: where, error, fix); Doubtful items addressed;
Automated checks after fixes; Verdict.

## Naming

- Lesson figures: `L<n>-<slug>.svg` and `.png`, numbered by lecture section.
- Session figures: `Fig <lesson>a`, `b`, `c`, `d` (e.g. `Fig 2.2c`).
- Cards: `C1`, `C2`, … in the order a student implements them.
- Exercises: `T1`–`T5`; sub-exercises `T3.2`.

## Sizes that worked

Thrun ch. 3 (46 pages): 177 highlights, lecture 2,400 words plus 5 figures, 5 cards, 33 oracle tests,
4 planted bugs, session with 4 figure cards. Scale with the chapter; do not pad a short chapter.
