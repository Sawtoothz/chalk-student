# T5 — Robot application: calibrate the tracked robot's motion model from a log

You have working motion models (T3). Now fit one to a robot whose noise you do not know. That is
the job the book leaves out: α₁–α₄ do not come from a datasheet.

## Setup

`python -m exercises.T5_sim` writes `data/t5_run_{0..9}.npz`: a skid-steer tracked robot driving
`models.tracked_route` (60 s at 10 Hz: straights, left and right arcs, two spins in place, a stop, a
reverse leg). Each file has `xs` (601, 3), the ground-truth poses from motion capture; `odom` (601, 3),
the track-encoder odometry in its own frame; `U` (600, 2), the commands (v, ω); and `dt` = 0.1 s.
The simulator's slip model is hidden in `T5_sim.py`; do not open it until you have written your report.

Conventions for every task:
- Predict once per second, as a filter on this robot would: take every 10th sample of `xs` and `odom`,
  so one step is a pair (odom[k], odom[k+10]) (C4 trick 6). The command is constant within each second.
- Leave out the seconds where the command is (0, 0); the robot is parked and both logs agree exactly.
- Train on runs 0–7, report on runs 8–9 (held out).
- Score a model two ways on the held-out runs: the mean log density per step of the true pose,
  `log_motion_model_odometry(..., pose_density=True)` (higher is better; it is a density over poses, so
  different models compare fairly), and 5 s dead reckoning: from the true pose every 2 s, propagate
  M = 2000 particles for five steps with the sampler and count how often the true end pose lies inside
  the cloud's 95 % ellipsoid (NEES of the true pose against the cloud's mean and covariance, θ wrapped,
  below χ²(3) at 0.95 = 7.81). Target coverage 0.95; median NEES target 2.37.

## Tasks

1. **Initial guess.** Score α = (0.1, 0.01, 0.1, 0.01). Split the log density into driving steps and
   steps where the odometry translation is under 3 cm (spins in place). What do you see?
2. **Maximum likelihood, book model.** Fit α₁–α₄ by maximizing the training log density (optimize
   log α with Nelder–Mead). Look at the fitted values and the coverage. Plot the three per-step errors
   (wrap(δrot1 − δ̂rot1), δtrans − δ̂trans, wrap(δrot2 − δ̂rot2)) against the step's δtrans. Which
   steps drive the fit, and why does the rot–trans–rot decomposition fail on them? (Hint: C4 trick 2
   applies the 1 cm rule to the odometry and to the hypothesis separately.)
3. **Spins in place.** For odometry steps under 3 cm, replace Table 5.5 by a model that does not
   decompose: an isotropic 2-D Gaussian of standard deviation σ_spin on the position change and
   N(0, α₁Δθ²) on the heading error, with Δθ the odometry's heading change. Write the matching
   sampler. Refit (α₁–α₄, σ_spin) and score again.
4. **Systematic error.** The model assumes zero-mean noise. Plot the true heading change per step
   against the odometry heading change. Fit the slope through the origin; its inverse is a factor χ by
   which the encoders over- or under-report turning. Divide the odometry heading change, and the chord
   direction (half of it), by χ before decomposing; refit and score. What physical quantity is χ on a
   skid-steer robot?
5. **Robustness.** Look at the worst held-out steps. Replace each Gaussian term by a two-component
   mixture, (1 − ε) N(b²) + ε N(100 b²), fit ε with the rest, and compare the fitted α, the mean and
   the worst-step log density, and the coverage. Is coverage still the right metric for a heavy-tailed
   cloud?
6. **Odometry or commands?** Fit the velocity model α₁–α₆ to the commands (`log_motion_model_velocity`,
   `pose_density=True`, Δt = 1 s) on the driving steps only, and compare its held-out log density with
   the odometry model's on the same steps. Map L1's claim (p. 121) onto this robot.
7. **Write-up (half a page).** Which correction mattered most, what would you log on the real robot
   to repeat this without motion capture, and what would you put in the robot's configuration.

## Deliverables

- `T5_report.md` with the plots (use `viz.py.style`) and the numbers, one table row per task.
- `T5_tuned.yaml` with your final α₁–α₄, σ_spin, χ and ε.

## Self-check

`solutions/T5.md` gives the hidden simulator parameters and the reference numbers from
`python -m exercises.solutions.T5_reference`. Compare only after you have written your report.
