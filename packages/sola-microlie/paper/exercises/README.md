# Exercises — a micro Lie theory for state estimation in robotics (Solà, Deray, Atchuthan)

Five tiers. Each has a three-step clue ladder and a solution. The implementation solution lives in `solutions/` and is
revealed by `just reveal sola-microlie 1 T3` only after `just test` has run at least once or all three clues of every
T3 exercise have been opened. Read `clues.md` one clue at a time; do not scroll.

| Tier | File | What you do | Graded by |
| --- | --- | --- | --- |
| T1 concept | `T1_concept.md` | 10 short questions | self-check against `solutions/T1.md` |
| T2 derivation | `T2_derivation.md` | 4 derivations by hand: Ad of SE(2), the ⊖ blocks (82)–(83), H of §V-A, the covariance reset | self-check against `solutions/T2.md` |
| T3 implementation | `exercise.py` | 13 stubs in 8 exercises: SO(3) Exp/Log and J_r/J_r⁻¹, SE(2) Exp/Log/Ad/J_r, ⊖ with its blocks, the beacon model, the ESKF of §V-A, the Gauss-Newton smoother of §V-B | `pytest exercises/tests/test_T3.py` (oracles: expm/logm, scipy `Rotation`, FD of (41a), series limits, Monte Carlo, ANEES over 40 runs) |
| T4 debug | `T4_debug/broken_eskf.py` | find and fix four planted bugs in an SE(2) ESKF | `pytest exercises/tests/test_T4.py` |
| T5 robot | `T5_robot.md` | tune a tag-based ESKF for the tracked robot with hidden slip noise; NIS/NEES, a large-heading stress case, gating; report | self-check against `solutions/T5.md`; numbers from `solutions/T5_reference.py` |

T3 has 13 functions, one more than the usual 12, because the paper is a toolkit: four pairs (Exp/Log twice, J_r/J_r⁻¹,
Ad/J_r) are short and belong together. Budget about 4 hours; T3.7 and T3.8 reuse everything before them, so do the
exercises in order.

The paper has no numbered exercises. Its worked material is folded in: Ex. 4 (Rodrigues) into T3.1, the SE(2)
appendix into T3.3–T3.4 and T2.1, the proof under (83) into T2.2, the H of §V-A into T2.3 and T3.6, §V-A into T3.7, T4
and T5, and Fig. 12 (§V-B) into T3.8.

Two systems in `models.py` (read it, do not edit it): `SectionV`, the setup of §V with manif's beacons and control and
Gaussian noise, and `TrackedRobot`, a tracked base in a yard of AprilTags with lateral slip. Everything in `models.py`
is built on `scipy.linalg.expm`/`logm`, so the tests' oracles do not depend on your code.

Run everything: `just test sola-microlie 1`, or `python3 -m pytest exercises/tests -q` from the package directory.
Regenerate the T5 data with `python3 -m exercises.T5_sim`.
