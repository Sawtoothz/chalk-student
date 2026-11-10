# T5 — Robot application: Monte Carlo localization on a symmetric RoboCup field

You have a working `pf_step` (T3). Now make it localize a tracked robot on a field where every pose
has a mirror twin, with noise you do not know. This is book exercises 2 and 5 grown into the RoboCup case:
a belief no Gaussian can hold.

## Setup

`exercises/models.py::SymmetricField`: 9 m × 6 m, four identical goalposts at (±4.5, ±0.8) and a centre
spot at (0, 0). The detector reports range and bearing to every landmark within 9 m and ±75°, **without
labels** (`zs[t]` is 5 × 2, NaN-padded). `log_lik(z, X, sigma_r, sigma_b, eps)` is the likelihood, with
a floor `eps` for outliers. Controls are `field_controls()`: a loop in the own half (t < 150), a stop
(150 ≤ t < 200), then a slow drive across the field.

Run `python -m exercises.T5_sim` to (re)generate `data/t5_run_{0..9}.npz` with `xs` (401 × 3 truth),
`zs` (400 × 5 × 2), `U` (400 × 2). Noise levels, outlier rate and one surprise are hidden in `T5_sim.py`;
do not open it until you have written the report.

Your motion sampler: noise on (v, ω), then `SymmetricField.move`; return X unchanged when u = (0, 0).
Your estimate: C6 trick 4, the weighted mean and covariance of the heaviest cluster, not of all particles.
Error = position error of that estimate; NEES with its 3 × 3 covariance and the θ error wrapped.

## Tasks

1. **Initial guess.** M = 3000 particles uniform in the own half (x < 0; robots start there by the rules).
   σ_v = 0.1 m/s, σ_ω = 0.1 rad/s, σ_r = 0.3 m, σ_b = 6°, eps = 1e-3, resample on N_eff < M/2.
   Over the ten runs report: runs converged (error < 0.5 m for 20 steps within t < 150), median position
   error and median NEES over t ∈ [60, 150) ∪ [210, 300), and the fraction of NEES above χ²(3) at 0.99 (11.34).
2. **Tune the noise.** Bring σ_v, σ_ω, σ_r, σ_b toward what the data say. Watch what happens to NEES
   as you approach the true values. Is a particle filter at the true noise consistent? Why not?
3. **Symmetry.** Initialize uniform over the whole field instead of the own half. At t = 150, count the
   runs that are correct, the runs that are mirrored (error > 2 m but < 0.5 m to the mirrored pose
   (−x, −y, θ + π)), and the rest. Explain why no amount of sensing fixes this, and what a real team does.
4. **How many particles.** M ∈ {300, 1000, 3000, 10000}: runs converged, median error, median NEES,
   and the spread of the t = 60 estimate over 8 seeds on run 0 (lecture L8).
5. **The stop.** Three policies for 150 ≤ t < 200: resample with `rng.choice` every step; your `pf_step`
   (N_eff trigger, low-variance); skip the whole step when u = 0. Distinct particles at t = 150 and t = 200,
   median error during the stop.
6. **The surprise.** Something happens around t = 300. Find it from the error plot, then from a signal you
   would have on the robot without ground truth. Try random injection of 2% and 5% (p. 113): runs
   recovered, median steps to recover, and the cost in tracking error.
7. **Outliers.** Set eps = 1e-300 (no floor). What happens to error and NEES?
8. **Write-up (half a page).** What M and noise would you ship on the robot's CPU, how would you detect
   a kidnap in a match, and what would you log to tune this without a motion-capture system?

## Deliverables

- `T5_report.md` with plots (use `viz.py.style`) and the numbers.
- `T5_tuned.yaml` with your M, noise, eps, resampling threshold and injection rule.

## Self-check

`solutions/T5.md` gives the hidden parameters and reference numbers from the reference solution
(`solutions/T5_reference.py`). Compare only after you have written your report.
