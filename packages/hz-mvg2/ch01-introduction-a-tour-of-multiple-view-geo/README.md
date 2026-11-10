# H&Z ch. 1 — Introduction: a Tour of Multiple View Geometry · teaching package

Lesson t3.1 (proposed). Built from printed pages 1–22 of Multiple View Geometry in Computer Vision, 2nd ed.

```
ch01-introduction-a-tour-of-multiple-view-geo/
  README.md            this file
  map.md               chapter map: sections, verdicts, time, prerequisites, what feeds what
  annotated.pdf        the chapter with 79 highlights and margin notes (open the popups)
  highlights.json      the source of the annotations; colour = category
  lecture.md           L1–L6, four layers each, and L7: how to tell which model you need
  figures/             L1–L6 SVG + PNG from figures/make_figures.py; numbers.json and card_numbers.json hold every quoted number
  translate.md         equation-to-code cards C1–C9: shapes, naive, robust (tricks named), Eigen
  session.py           marimo session: Fig 3.1a–d, predict-then-see, live readouts (session_model.py holds the numbers)
  interactive.html     the same four figures in plain JS + Plotly (rebuilt by build_interactive.py, checked by compare_session.py)
  REVIEW.md            the reviewer's findings and what was fixed
  exercises/
    README.md          tiers, clue rules, how grading works
    T1_concept.md      10 questions
    T2_derivation.md   6 derivations
    exercise.py        T3 stubs: 12 functions, cards C1–C9 in order
    models.py          the cards' two-camera scene and the tracked robot's camera over a warehouse floor
    T4_debug/          a two-view pipeline with five planted bugs
    T5_robot.md        VO initializer on the tracked robot: H or F, pose, metric scale; T5_sim.py generates data/
    clues.md           three-step ladders
    tests/             oracle tests (test_T3) and the T4 grader
    solutions/         gated: T1, T2, T3_solution.py, T4, T5
```

## Highlight colours in annotated.pdf

| Colour | Meaning |
| --- | --- |
| green | definition or assumption |
| yellow | key idea or result |
| red box | equation you will derive and implement |
| orange | where it fails |
| blue | link to your robots or another lesson |
| gray note icon | section-level reading verdict |

## Suggested order (about 8 hours)

1. `map.md`, then read the chapter with `annotated.pdf` open (2.5 h for the must-read sections, 50 min of skims).
2. `lecture.md` L1–L4, then `session.py` Fig 3.1a (45 min).
3. `lecture.md` L5–L7, session Fig 3.1b–d (45 min).
4. T1 and T2 on paper, with `translate.md` open for T2 (1 h).
5. T3 card by card; `just test hz-mvg2 1` after each card (2 h).
6. T4 once T3 is green (45 min).
7. T5 when you next have a free evening (2 h); it is the VO initializer question your tracked robot and drone actually face.

## How this package was checked

- `scripts/check_package.py`: structure, figures, highlight placement, reference solution passes all 23
  oracle tests, shipped stubs fail them, T4 broken file fails its grader on all five bugs, session executes.
- `compare_session.py`: session.py and interactive.html readouts identical on 15 settings.
- `teach-reviewer`, a separate agent, compared every cited equation and page against the book (`REVIEW.md`).
- All T5 reference numbers were produced by running the reference solution on the shipped data.
