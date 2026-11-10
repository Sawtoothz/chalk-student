# Exercises — ch. 4 Nonparametric filters

Five tiers. Each has a three-step clue ladder and a solution. Implementation solutions live in
`solutions/` and are revealed by `just reveal thrun-pr 4 T3` only after `just test thrun-pr 4` has run
at least once or all three clues of the tier have been opened. Read `clues.md` one clue at a time.

| Tier | File | What you do | Graded by |
| --- | --- | --- | --- |
| T1 concept | `T1_concept.md` | 10 short questions | self-check against `solutions/T1.md` |
| T2 derivation | `T2_derivation.md` | 4 derivations by hand | self-check against `solutions/T2.md` |
| T3 implementation | `exercise.py` | 12 stubs: histogram filter, log odds, importance sampling, resamplers, particle filter step, density extraction | `pytest tests/test_T3.py` (oracles: KF, Table 4.1 on two states, closed-form Φ, Table 4.4 line by line, `np.cov`, quadrature) |
| T4 debug | `T4_debug/broken_pf.py` | find and fix four planted bugs | `pytest tests/test_T4.py` |
| T5 robot | `T5_robot.md` | Monte Carlo localization on a symmetric RoboCup field with hidden noise and a surprise; half-page report | self-check against `solutions/T5.md` |

Book exercises (pp. 115–116), adapted rather than reproduced:
- 1 and 4 ask for a histogram and a particle filter on the ch. 3 car, state (x, ẋ), predicting t = 1..5 and
  updating with z = 5 at σ² = 10. The package checks the same idea, filter equals KF, on a 1-D random walk so a
  dense grid stays affordable: `test_histogram_filter_matches_kalman_filter`, `test_pf_matches_kalman_filter`.
  Doing the book's 2-D car version yourself with your `exercise.py` is a good extension.
- 2 and 5 ask for the θ-unknown banana with a small position prior (variance 0.01), a comparison with the EKF,
  the effect of grid resolution (2b), and varying numbers of particles (5). The package's
  `test_banana_histogram_and_particles_agree_with_quadrature` fixes x, y exactly and uses one M; the EKF
  comparison, resolution and M sweeps are left to you (T5 task 4 is the M sweep on a harder system).
- 3 (sampling bias with M = 2) is T2.4, worked exactly on a two-state example.

Systems in `models.py`: `RandomWalk1D` (KF oracle), `RingCorridor` (lecture Fig L2, L11), `Banana`,
`SymmetricField` (T5).

Run everything from the package folder: `python -m pytest exercises/tests -q`.
Regenerate T5 data: `python -m exercises.T5_sim`.
