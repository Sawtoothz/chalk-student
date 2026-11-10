# Exercises — ch. 3 Gaussian filters

Five tiers. Each has a three-step clue ladder and a solution. Implementation solutions live in
`solutions/` and are revealed by `just reveal t2.2 T3` only after `pytest` has run at least once or all
three clues have been opened. Read `clues.md` one clue at a time; do not scroll.

| Tier | File | What you do | Graded by |
| --- | --- | --- | --- |
| T1 concept | `T1_concept.md` | 8 short questions | self-check against `solutions/T1.md` |
| T2 derivation | `T2_derivation.md` | 3 derivations by hand | self-check against `solutions/T2.md` |
| T3 implementation | `exercise.py` | fill the stubs: KF, EKF, UKF, Jacobians, IF conversions | `pytest tests/` (oracle: Monte Carlo + dense reference) |
| T4 debug | `T4_debug/broken_ekf.py` | find and fix four planted bugs | `pytest tests/test_T4.py` |
| T5 robot | `T5_robot.md` | tune a range-bearing EKF for the tracked robot; NEES/NIS report | self-check; `session.py` shows the plots |

Book exercises 1, 2 and 4 (pp. 81–83) are folded into T3 and T5.

Run everything: `pytest exercises/tests -q`.
