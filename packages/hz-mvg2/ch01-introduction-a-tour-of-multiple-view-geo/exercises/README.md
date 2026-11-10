# Exercises — H&Z ch. 1, a tour of multiple view geometry

Five tiers. Chapter 1 has no end-of-chapter exercises, so every exercise here is written for the package.
It is a tour chapter: the coding checks the chapter's claims numerically (T3), finds the bugs those claims
predict (T4), and then puts them to work on the tracked robot (T5). Implementation solutions live in
`solutions/` and are revealed by `just reveal hz-mvg2 1 T3` only after `just test hz-mvg2 1` has run once
or all three clues of T3 have been opened. Open clues one at a time with `just clue hz-mvg2 1 <exercise> <n>`.

| Tier | File | What you do | Graded by |
| --- | --- | --- | --- |
| T1 concept | `T1_concept.md` | 10 short questions | self-check against `solutions/T1.md` |
| T2 derivation | `T2_derivation.md` | 6 derivations: (1.1) and the 7-point count, circular points, the canonical camera and plane H, same-centre H, IAC angles with numbers, three-view counting | self-check against `solutions/T2.md` |
| T3 implementation | `exercise.py` | 12 functions, cards C1–C9 in order: `dehom`, `circle_conic`, `camera_centre`, `depth`, `plane_homography`, `rotation_homography`, `apply_ambiguity`, `epipolar_distance_px`, `triangulate`, `ray_angle`, `affine_upgrade`, `metric_upgrade` | `tests/test_T3.py`, 23 oracle tests |
| T4 debug | `T4_debug/broken_two_view.py` | find and fix five planted bugs (normalisation, sign, transpose, wrong column) | `tests/test_T4.py`, one test per bug |
| T5 robot | `T5_robot.md` | VO initializer on the tracked robot: H or F, pose, metric scale from the floor, stability, RANSAC; half-page report | self-check against `solutions/T5.md` |

Oracles in `test_T3.py`, none of which uses your code: the chapter's formulas written out longhand (p. 5's circle, p. 7's
x = PX), cameras built from a known centre and rotation, the closed-form F of §9.2 (`models.F_reference`), true 3D
points and their camera-frame directions, and `np.linalg.inv`. No vision library is needed.

`models.py` holds the two systems (the cards' two-camera scene and the tracked robot's camera over a warehouse floor)
and three tools for T5 from later chapters. Do not edit it.

Suggested order: T1 after the lecture; T2 alongside the cards; T3 card by card (`just test hz-mvg2 1` after each);
T4 only after T3 is green; T5 last. Time: about 3 hours for T3–T4 and 2 hours for T5.

Run everything from the package dir: `python3 -m pytest exercises/tests -q`.
