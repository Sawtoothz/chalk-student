# T5 — Robot application: tune the tracked robot's tag-based ESKF on SE(2)

You have an ESKF on SE(2) that passes its tests on the §V setup (T3.7). Now make it work on a system where you do not
know the noise, which is the real job. The system is §V-A almost verbatim: a tracked base, track odometry as the
control ũ = (v δt, 0, ω δt), AprilTags at surveyed positions as the beacons, each detection a 2-D position in the
body frame (95).

## Setup

`exercises/models.py::TrackedRobot`: a 9 m × 7 m yard with a 4 × 3 grid of tags, a 60 s figure-eight at 0.5 m/s
(600 steps of 0.1 s, with exactly straight segments where ω = 0), a camera that sees tags within 5 m and ±60°.
Run `python -m exercises.T5_sim` from the package directory to (re)generate `data/`:

- `t5_run_{0..9}.npz`: `truth` (601 × 3, x, y, θ), `U` (600 × 3, the odometry ũ), `Y` (600 × 12 × 2) and `mask`
  (600 × 12, which tags were seen at step k, after the k-th motion), `tags` (12 × 2), `dt`;
- `t5_outliers_run_{0..9}.npz`: the same runs with about 5 % of detections replaced by a misread tag ID (the position
  of another tag), plus a boolean `outlier` array for scoring.

The true `R_proc` and `Q_meas` are not in the files. Start every run at the true pose ⊕ ε with
ε ~ N(0, P₀), P₀ = diag(0.05, 0.05, 0.02)², and seed the draw with the run number, so your numbers are comparable
with the reference ones. Use the reset (`reset=True`) unless a task says otherwise. Compute NEES with the error
true ⊖ estimate in the tangent at the estimate (52), and NIS per detection.

## Tasks

1. **Initial guess.** R_proc = diag(0.02, 0.001, 0.01)² per step ("tracks do not slip sideways": the middle term
   is the lateral slip u_s of (92)–(93)), Q_meas = diag(0.10, 0.10)². Run all ten files. Plot NIS per detection with
   the χ²(2) 95 % band, and NEES per step with the χ²(3) band. Report ANIS, ANEES, position RMSE.
2. **Tune Q_meas from NIS.** NIS needs no ground truth, so this is what you can do on the real robot. Change only
   Q_meas until ANIS ≈ 2. Then look at ANEES. Better or worse than task 1? Why?
3. **Tune R_proc from NEES.** Using the ground truth, adjust R_proc until ANEES ≈ 3 with ANIS still ≈ 2. Which of
   the three components of R_proc did the work? Show it by putting the true-looking values back in all components
   except the slip one.
4. **Stress: a large heading error.** Start every run with ε = (0, 0, 0.8 rad) and tell the filter so,
   P₀ = diag(0.1, 0.1, 0.8)². Report ANEES and ANIS over the first 50 steps with the covariance reset on and off.
   Which assumption of the ESKF is broken here, and what would you add next (lecture L15; card C8, "what breaks
   first")?
5. **Gating.** On the `_outliers` files, run without a gate and with a Mahalanobis gate on the innovation at the
   χ²(2) 99 % quantile (card C8, trick 6). Report ANEES, position RMSE and the fraction of detections accepted. Then
   run the same gate on the clean files: how many good detections does it throw away?
6. **Write-up (half a page).** What would you log on the real tracked robot to tune this filter without ground truth,
   which plot would you open first when it misbehaves, and how would you get ground truth once (task 3 needs it)?

## Deliverables

- `T5_report.md` with the plots (use `viz.py.style`) and a table of the numbers.
- `T5_tuned.yaml` with your final R_proc, Q_meas and gate threshold.

## Extension (optional, no reference numbers)

The UTIAS Multi-Robot Cooperative Localization and Mapping dataset (Leung et al., *IJRR* 2011) is the real version of
this exercise: wheel odometry, range-bearing detections of barcoded landmarks, motion-capture ground truth.
Convert range-bearing to the body-frame position y of (95) at load, and propagate its covariance through that
conversion with (55) (`implementation.md`, Data). It is not in `library/`; download it yourself.

## Self-check

`solutions/T5.md` gives the true noise used by `T5_sim.py` and the reference numbers from the reference solution on
the shipped data (`solutions/T5_reference.py` → `solutions/t5_numbers.json`). Compare only after you have written
your report.
