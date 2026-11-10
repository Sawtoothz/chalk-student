# Exercises — ch. 4 One-dimensional Kalman filters

Five tiers. Each has a three-step clue ladder and a solution. The T3 solution lives in `solutions/` and is
revealed by `just reveal labbe-kbf 4 T3` only after `just test labbe-kbf 4` has run at least once or all
three clues of a T3 exercise have been opened. Open clues one at a time with `just clue labbe-kbf 4 <exercise> <n>`
(for example `just clue labbe-kbf 4 T3.3 1`); do not scroll `clues.md`.

| Tier | File | What you do | Graded by |
| --- | --- | --- | --- |
| T1 concept | `T1_concept.md` | 10 short questions | self-check against `solutions/T1.md` |
| T2 derivation | `T2_derivation.md` | 4 derivations by hand, each ending in numbers | self-check against `solutions/T2.md` |
| T3 implementation | `exercise.py` | 11 functions: predict, both update forms, Joseph variance, the loop, NIS, steady state, its inverse, the fixed-gain filter and its true variance | `pytest exercises/tests/test_T3.py` (oracles: the book's printed outputs, numerical integration, Monte Carlo, the iterated recursion) |
| T4 debug | `T4_debug/broken_filter.py` | find and fix five planted bugs in a drone's float32 altitude filter | `pytest exercises/tests/test_T4.py` |
| T5 robot | `T5_robot.md` | tune a barometric-altitude KF for a quadrotor from logged flights with hidden noise; half-page report | self-check against `solutions/T5.md` |

`models.py` holds the two systems (the book's dog; the drone). Read it, do not edit it.

## Where the book's own exercises went

| Book exercise | Page | Here |
| --- | --- | --- |
| Modify Variance Values | 148 | T1.3 and T2.2 (done with numbers for both choices) |
| Interactive Plots | 164–165 | the marimo session (`session.py`) replaces the ipywidgets cell |
| Nonlinear Systems | 165–167 | T1.9 and T2.4: the offset comes from a wrong u, and a sine in time is not a nonlinear system |
| (implicit) the fixed gain 0.13232 | 168 | T2.2 and `ratio_from_gain` in T3: which R_proc/Q_meas gives it |

Suggested order: T1, then T3 card by card (C1 → C4) with T2.1 after C3 and T2.2–T2.3 after C4, then T4, then
T5. Budget: T1 + T2 about 1.5 h, T3 about 2 h, T4 30 min, T5 2 h.

Run from the package directory: `pytest exercises/tests -q`. The T3 tests take under a second.
