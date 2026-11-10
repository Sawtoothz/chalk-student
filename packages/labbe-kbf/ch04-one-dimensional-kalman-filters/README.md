# Labbe ch. 4 — One Dimensional Kalman Filters · teaching package

Lesson t2.2. Built from printed pages 131–170 of Kalman and Bayesian Filters in Python (R. Labbe, CC BY 4.0).
The gold package for Thrun ch. 3 is the same lesson in matrix form; do this one first.

Notation: Labbe's Q (process variance) is `R_proc` here, Labbe's R (measurement variance) is `Q_meas`. The table in
`map.md` §Notation is the key.

```
ch04-one-dimensional-kalman-filters/
  README.md            this file
  REVIEW.md            what the reviewer checked against the book, and what it caught
  map.md               chapter map: sections, verdicts, time, notation, steady-state table, book errata
  annotated.pdf        the chapter with 125 highlights and margin notes (open the popups)
  highlights.json      the source of the annotations; colour = category
  lecture.md           L1–L10, four layers each (Picture, Intuition, Formal, Your robots); L11 symptom → fix table
  figures/             L1–L10 SVG + PNG from make_figures.py; card_numbers.py prints every number the cards quote;
                       make_session_data.py writes the fixed noise both session versions share
  translate.md         equation-to-code cards C1–C4: predict, Bayes-form update, gain form and loop, steady state
  session.py           marimo session: Fig 2.2a–d, predict-then-see, live readouts
  interactive.html     the same four figures in plain JS + Plotly, no Python needed
  reader.html          everything above in one page (just view labbe-kbf 4)
  exercises/
    README.md          tiers, clue rules, how grading works
    T1_concept.md      10 questions
    T2_derivation.md   4 derivations: product → gain, steady state and the book's 0.13232, Joseph cost, u-offset
    exercise.py        T3 stubs: predict, update (both forms), Joseph variance, run_filter, NIS, steady state,
                       fixed-gain filter and its variance
    models.py          DogHallway (the book's dog) and DroneAltitude (baro + commanded climb rate, 20 Hz)
    T4_debug/          a float32 drone-altitude filter with five planted bugs
    T5_robot.md        tune the baro-altitude filter from flight logs with NIS, then check against truth;
                       data/ holds ten flights, T5_sim.py regenerates them
    clues.md           three-step ladders
    tests/             oracle tests (test_T3) and the T4 grader (test_T4)
    solutions/         gated: T1, T2, T3_solution.py, T4, T5, T5_reference.py
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

The chapter has no numbered equations (it is a Jupyter notebook), so red boxes mark the formulas by page.

## Suggested order (about 6 hours)

1. `map.md` including the notation table, then the must-read sections with `annotated.pdf` open (2.5 h; half of each
   page is code and plots).
2. `lecture.md` L1–L5, then `session.py` (or `interactive.html`) Fig 2.2a–b (45 min).
3. T1 and T2.1–T2.2 on paper (45 min).
4. T3 with `translate.md` C1–C3 beside you; `just test labbe-kbf 4` until green (1.5 h).
5. `lecture.md` L6–L10, session Fig 2.2c–d, T2.3–T2.4, T4 (1 h).
6. T5 when you have an evening: it is the altitude channel of a flight controller, and the NIS tuning carries over
   unchanged to the multivariate filters of Labbe ch. 6 and Thrun ch. 3.

## How this package was checked

- `scripts/check_package.py`: 125 highlights placed. The reference solution passes all 36 oracle tests, the shipped
  stubs fail them, the T4 broken file fails its grader (5 failures) and the session executes. Verdict: ship.
- `teach-reviewer` compared every equation, page citation and book-attributed claim against the book and redid the
  T2 algebra. It caught seven errors: wrong pages, a misquote, a σ/σ² slip wrongly blamed on the book, and bare Q/R.
  All are fixed (`REVIEW.md`).
- All reference numbers come from running the reference solution and the figure scripts in this repo. The session
  tiles agree between Python and JS on every readout.
