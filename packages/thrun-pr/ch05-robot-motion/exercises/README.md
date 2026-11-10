# Exercises — ch. 5 Robot motion

Five tiers. Each has a three-step clue ladder and a solution. Implementation solutions live in
`solutions/` and are revealed by `just reveal thrun-pr 5 T3` only after `just test thrun-pr 5` has run
at least once or all three clues of the tier have been opened. Read `clues.md` one clue at a time.

| Tier | File | What you do | Graded by |
| --- | --- | --- | --- |
| T1 concept | `T1_concept.md` | 10 short questions | self-check against `solutions/T1.md` |
| T2 derivation | `T2_derivation.md` | 5 derivations by hand | self-check against `solutions/T2.md` |
| T3 implementation | `exercise.py` | 12 stubs: log densities, velocity forward model, sampler, inverse, noise Jacobian and density; odometry decomposition, sampler and density; the map-aware sampler; bicycle and holonomic samplers | `pytest tests/test_T3.py` (oracles: eq. 5.16 in long double, RK4 on the kinematic ODEs, finite differences, scipy densities, Monte Carlo moments, grid quadrature) |
| T4 debug | `T4_debug/broken_motion.py` | find and fix five planted bugs | `pytest tests/test_T4.py` (one test per bug) |
| T5 robot | `T5_robot.md` | calibrate the tracked robot's odometry model from a log with ground truth; half-page report | self-check against `solutions/T5.md` |

Book exercises (pp. 145–147), adapted rather than reproduced:
- 1–3 (a robot with dynamics) are T2.4, worked on a 1-D double integrator with the ch. 3 car's numbers.
- 4 (the kinematic bicycle) is T2.5; 5 (its sampler) is T3.11, `sample_motion_model_bicycle`. The
  book's control table and variances are not copied here: plug them into `models.Bicycle` and plot the
  five settings yourself with your sampler. Check the conventions in T2.5 (c) first.
- 6 (the bicycle's inverse model) is optional and not graded.
- 7 (holonomic) is T3.12, `sample_motion_model_holonomic`; that is the quadruped's body-velocity command.
- 8 (triangular mean and variance) is T2.1, together with the range of Table 5.4's samplers.

Systems in `models.py`: `wrap`, the noise presets of lecture figures L5 and L7, `WallMap` (Fig L8),
`Bicycle`, `Holonomic`, and `tracked_route` (the T5 commands).

Run everything from the package folder: `python -m pytest exercises/tests -q`.
Regenerate T5 data: `python -m exercises.T5_sim`. Reference numbers (gated): `python -m exercises.solutions.T5_reference`.
