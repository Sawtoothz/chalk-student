# T5 — Robot application: tune a quadrotor's barometric-altitude filter

You have a working scalar filter (T3). Now make it run well on a system whose noise you do not know, using only
what you can log on the vehicle, then check it against ground truth the way you would with a motion-capture
session. This is the altitude channel of a flight controller: a 1-D Kalman filter fed the commanded climb rate and
the barometer, which is what runs underneath altitude hold on most small drones.

## Setup

`models.py::DroneAltitude`, 20 Hz (dt = 0.05 s), a 70 s mission: 10 s armed on the ground, climb, hover, climb,
hover, descend, hover. Ten logged flights are in `data/t5_run_{0..9}.npz` (regenerate with
`python -m exercises.T5_sim` from the package directory; do not open `T5_sim.py` until you have written your report).
Each file holds:

| Key | Shape | What |
| --- | --- | --- |
| `t`, `dt` | (1400,), scalar | time [s], step [s] |
| `v_cmd`, `u` | (1400,) | commanded climb rate [m/s]; u = v_cmd·dt, the known move per step [m] |
| `ground` | (1400,) bool | True while the drone sits on the ground (t < 10 s) |
| `z` | (1400,) | barometric altitude [m above sea level] |
| `h` | (1400,) | true altitude (motion capture), for tasks 4–7 only |
| `z_out` | (1400,) | the same flight with baro spikes added (task 6) |
| `h_gust`, `z_gust` | (1400,) | the same flight with an unmodeled downdraft (task 5) |

Model: h_{k+1} = h_k + u_k + w_k, z_k = h_{k+1} + v_k. R_proc is the variance of w per step (in flight; on the ground
the drone does not move), Q_meas the variance of v. Use `run_filter(z, z[0], Q_meas, u, R_proc, Q_meas)`: initialize
from the first measurement (translate.md C3 trick 5). Compute the statistics over the flight steps (`~ground`) of all
ten runs pooled.

## Tasks

1. **Datasheet guess.** The baro datasheet quotes 0.1 m RMS noise, so Q_meas = 0.1² m²; take R_proc = 0.01² m²/step.
   Run the filter on all ten flights. Report ANIS over flight, and plot the per-step NIS of one run with the χ²(1)
   95% line (3.84). Look at the RMS error too (you are allowed `h` for that number only, here).
2. **Q_meas from the ground segment.** On the ground the true altitude is constant, so the baro's sample variance over
   `ground` is Q_meas. No ground truth needed: this is a 10 s log before every flight. Pool the ten runs.
3. **R_proc from NIS.** With Q_meas from task 2, adjust R_proc until ANIS = 1. Cross-check two ways that also need no
   ground truth: (a) the total measurement log-likelihood (sum of `log_c` from `update_bayes` over flight steps) for
   R_proc at ¼, ½, 1, 2, 4 times your value; (b) the lag-1 autocorrelation of y/√S, for your R_proc and for R_proc/10
   and ×10. Which sign does each mistuning give?
4. **Check with NEES.** Now use `h`: report ANEES for the filters of tasks 1, 2 and 3, with their RMS errors. Explain
   why the datasheet filter of task 1 has an RMS error about as good as the tuned one while being badly inconsistent
   (hint: T2.2 (b)).
5. **Stress: an unmodeled downdraft.** Run the tuned filter on `z_gust` against `h_gust`. Find when the gust happens
   from the filter's own outputs (a 1 s moving mean of NIS), report the peak error and ANEES in that window. What would
   you change on the vehicle: R_proc, the model, or neither?
6. **Gating.** Run the tuned filter on `z_out` with and without the 99% gate (`gate=CHI2_1DOF_99`). Report ANEES, RMS
   error and the accepted fraction. Also run the gate on the clean `z`: what does it cost?
7. **Fixed gain for the flight controller.** Compute K∞ from your tuned values with `steady_state`. Boot both filters at
   x0 = 0 (the flight controller starts before it knows the field elevation): the full filter with P0 = 10⁴ m², the
   fixed-gain one with K∞. How long until each stays within 1 m of the truth for a full second? Compare RMS error over
   the flight.
8. **Write-up (half a page).** What would you log on the real drone to keep this filter tuned without motion capture,
   and which plot would you open first when altitude hold misbehaves?

## Deliverables

- `T5_report.md` with the plots (use `viz.py.style`) and the numbers.
- `T5_tuned.yaml` with your final R_proc, Q_meas, gate threshold and K∞.

## Self-check

`solutions/T5.md` gives the hidden noise values used by `T5_sim.py` and the reference numbers from the reference
solution on the shipped data (`python -m exercises.solutions.T5_reference` reproduces them). Compare only after you
have written your report.
