# T5 — Robot application: tune the tracked robot's range-bearing EKF

You have a working EKF and UKF (T3). Now make one run well on a system where you do not know the
noise, which is the real job.

## Setup

`exercises/models.py::RangeBearing` with the figure-eight controls, but the simulator's true noise is
hidden from you: run `python -m exercises.T5_sim` to generate `data/t5_run_{0..9}.npz` with the true
trajectory, controls and measurements. The true R_proc and Q_meas are not in the file.

## Tasks

1. **Initial guess.** Start with R_proc = diag(0.05, 0.05, 0.02)² and Q_meas = diag(0.2, 3°)². Run the
   EKF on all ten files. Plot per-step NIS with the χ²(2) 95% band, and ANIS per run.
2. **Tune Q_meas from NIS.** NIS does not need ground truth, so this is what you can do on the real
   robot. Adjust Q_meas until ANIS ≈ 2 over the ten runs. Record what you changed and why.
3. **Tune R_proc from NEES.** Using the ground truth in the files, repeat with NEES and ANEES ≈ 3.
   Note that NEES and NIS can disagree: a filter can be consistent in innovation space and wrong in
   state space when a state is weakly observable. Which state is weakly observable here, and when?
4. **Stress.** Set the landmark to (1.0, 0.5) so the robot passes within 0.5 m of it. Watch H's 1/r
   terms. Does the EKF stay consistent? Does the UKF? Report ANEES for both.
5. **Gating.** Corrupt 5% of the measurements with outliers (uniform bearing). Add a Mahalanobis gate at
   χ²(2) 0.99 and show the effect on ANEES with and without it.
6. **Write-up (half a page).** What would you log on the real tracked robot to tune this filter
   without ground truth, and what plot would you look at first when it misbehaves?

## Deliverables

- `T5_report.md` with the plots (use `viz.py.style`) and the numbers.
- `T5_tuned.yaml` with your final R_proc, Q_meas, and gate threshold.

## Self-check

Solutions in `solutions/T5.md` give the true noise values used by `T5_sim.py` and reference ANEES/ANIS
numbers for the tuned filter, the stress case and the gated case. Compare only after you have written
your report.
