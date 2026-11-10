# Solà, Deray, Atchuthan — A micro Lie theory for state estimation in robotics · teaching package

Lesson t2.6. Built from pages 1–17 (the whole paper; printed page = PDF page) of J. Solà, J. Deray, D. Atchuthan,
*A micro Lie theory for state estimation in robotics* (CC BY-NC-SA 4.0). Reference code: manif, the authors' library,
and GTSAM, both anchored at a fixed commit in `code_refs.json`.

```
paper/
├── map.md                 sections with verdicts and minutes, inventory, dependencies, what the paper leaves out
├── annotated.pdf          the paper with highlights and WHY / ROBOT / CODE / TEST margin notes
├── highlights.json        the source of annotated.pdf
├── lecture.md             L1–L18: Picture, Intuition, Formal, Your robots; symptom-to-fix table at the end
├── translate.md           cards C1–C9: shapes, naive code, robust code with each trick named, Eigen, cost, what breaks
├── implementation.md      what to build on the robot, in what order, against what checks; pitfalls the code shows
├── code_refs.json         every manif / GTSAM file:line the cards cite (checked by check_paper.py)
├── session.py             marimo session, cards 2.6a–d (⊕ and Ad, tangent covariance, ESKF NEES/NIS, small angles)
├── session_lib.py         the numbers behind the session (shared with the JS through the same RNG)
├── interactive.html       the same four figures in the browser (Reader, Session tab)
├── reader.html            the Reader page (just view sola-microlie 1)
├── REVIEW.md              the reviewer's findings and what was fixed
├── figures/               make_figures.py (lecture figures), check_cards.py (card numbers, 236 FD checks),
│                          make_session_data.py, compare_session.py (Python vs JS tiles)
└── exercises/
    ├── README.md          tiers, files, how each is graded
    ├── T1_concept.md      10 questions
    ├── T2_derivation.md   4 derivations: Ad of SE(2), the ⊖ blocks, H of §V-A, the covariance reset
    ├── exercise.py        T3: 13 stubs in 8 exercises (yours)
    ├── models.py          SectionV and TrackedRobot, built on expm/logm (do not edit)
    ├── clues.md           three clues per exercise, one at a time
    ├── T4_debug/          an SE(2) ESKF with four planted bugs
    ├── T5_robot.md        tune a tag-based ESKF for the tracked robot; T5_sim.py, data/
    ├── tests/             test_T3.py (oracles), test_T4.py (grader)
    └── solutions/         gated: just reveal sola-microlie 1 <tier>
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

1. `map.md`, then read the paper with `annotated.pdf` open (about 3.5 hours at the "must" verdicts; II-G and III-B take
   longest).
2. `lecture.md` L1–L12 (Sections II–III), then T1 and T2.
3. `session.py` cards 2.6a and 2.6b (`just session sola-microlie 1`), predicting before you move a slider.
4. `translate.md` C1–C7, then T3.1–T3.6 in `exercise.py`; `just test sola-microlie 1` after each.
5. `lecture.md` L13–L18 (composite, §V, the appendices), C8–C9, then T3.7–T3.8 (the ESKF and the smoother).
6. Session cards 2.6c and 2.6d; T4; T5 on the tracked robot.
7. `implementation.md` before writing any of this on the robot.

## How this package was checked

- `just check sola-microlie 1`: 28 file:line citations checked against 2 repositories, VERDICT: ship.
  `check_package.py`: T3 oracle 131 passed on the reference solution, the stubs fail, the T4 grader fails on the broken
  file, the session executes.
- `figures/check_cards.py`: every number in the cards, 236 finite-difference checks (worst 5.4 × 10⁻⁹), C++ snippets compile.
- `teach-reviewer` compared every cited equation and page against the paper and re-ran the Jacobians, the T2 numbers,
  the session and T5 (`REVIEW.md`); its eight confirmed errors and five doubtful items are fixed.
- All reference numbers were produced by running the reference solution on the shipped data.
