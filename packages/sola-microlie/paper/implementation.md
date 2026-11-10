---
source: sola-microlie
unit: 1
stage: cards
---

# Practical implementation: a small Lie library, then the two §V estimators on it

This paper's method is a toolkit, not one algorithm. The goal is to own every block in C1–C7 by writing a small
library that passes finite differences everywhere, and then to run the two estimators of §V (C8, C9) on it,
first on synthetic data with known truth and then on one real planar dataset. Two deliverables, in this order:

1. **`microlie/`, a NumPy prototype** (target: under 500 lines). SO(3)/S³, SE(2), SE(3), ℝⁿ, and composites, each with Exp,
   Log, inverse, compose, act, Ad, J_r, J_l and their inverses, then `eskf_se2.py` and `sam_se2.py`. Offline, no rate
   target. Correctness first.
2. **On the robot, use manif itself** (MIT, header-only C++17, the paper's own library), not a port of the prototype.
   The prototype exists so that you can read manif with every line already derived, and so that you know which of its
   formulas lose precision (below). Target: the SE(3) ESKF of §V-D at the IMU rate of the drone or quadruped, to be
   measured on its computer.

## Step order (each step has a check that must pass before the next)

| # | build | check (oracle) | card |
| --- | --- | --- | --- |
| 1 | `so3.py`: hat/vee, `coef_a/b/d`, Exp/Log (matrix and quaternion), J_r, J_l, inverses, act | `Exp` vs `scipy.linalg.expm`; `Log(Exp(θ)) = θ` at θ ∈ {10⁻⁹, 1, π − 10⁻⁷} (target 10⁻¹⁵ rad); J_r, J_r⁻¹, (150) by `just fd`; (75), (76), (147) as identities; coefficient errors against `mpmath` over [10⁻¹², π] | C1, C3 |
| 2 | `ops.py`: `rplus`, `rminus`, `lplus`, `lminus`, generic Ad (31), blocks (62)–(83) | (32) as an identity; closed-form Ad vs (31); every block by `just fd` at 10 random points per group | C2, C3 |
| 3 | `se2.py`, `se3.py` with the a/b rewrites of (163)–(164) and the series Q of (180) | `expm`/`logm` oracle for Exp/Log; FD of J_r, J_l, J_r⁻¹, action; the SE(2) third column and Q against `mpmath` at θ ∈ {2 × 10⁻⁷, 10⁻⁴} (target 10⁻¹⁵) | C4, C5 |
| 4 | `composite.py`: diamond ⊕/⊖ over a (group, dim, offset) table; block J_r | round trip ⊖◇(⊕◇(𝒳, τ), 𝒳) = τ; FD of a two-block function through ⊕◇ | C6, C7 |
| 5 | `eskf_se2.py`: (99)–(102) with Joseph form, gating and the J_r(δx) reset | F, G, H by FD; on manif's example setup with Gaussian noise: ANEES within the 95 % band of χ²(3)/(steps·runs) around 3 over 200 runs of 100 steps (target), with the reset on and off | C8 |
| 6 | `sam_se2.py`: (103)–(110), whitened residuals, `lstsq`; then (111) | full J (19×15) against FD of r through ⊕◇; GN on Fig. 12 with known truth converges in under 10 iterations (target); with a known bias c, (111) recovers it within its 3σ | C9 |
| 7 | one real sequence (below): the ESKF and the smoother on the same data | trajectory error against the dataset's ground truth, NEES of the ESKF, GN iterations and cost; all to be measured, none quoted until run | C8, C9 |
| 8 | the SE(3) ESKF on the robot, with manif | identical increments to the prototype on a logged 60 s sequence (target 10⁻⁹ on δx per step); rate on the robot's computer | C5, C8 |

The targets in the check column are to be measured. This package records a number only after a run. Results
already measured by `figures/check_cards.py` (keys in `figures/card_numbers.json`) are marked as such below.

## Data

- **Synthetic first, from manif's own examples.** `examples/se2_localization.cpp` and `examples/se2_sam.cpp` define
  the setup of §V exactly (three beacons at (2, 0), (2, 1), (2, −1), control (0.1, 0, 0.05) per step). Reproduce
  them in Python with Gaussian noise. A prototype that disagrees with C8/C9 there has a bug.
- **One real planar dataset with landmarks and ground truth.** The UTIAS Multi-Robot Cooperative Localization and Mapping
  dataset (Leung et al., *IJRR* 2011): planar robots, wheel odometry as the control, range-bearing measurements of
  barcoded landmarks at surveyed positions, and motion-capture ground truth. It matches §V-A (known beacons) and §V-B
  (beacons as unknowns) without modification. Convert range-bearing to the Cartesian y of (95) once, at load, and
  propagate its covariance through that conversion with (55).
- **Then the tracked robot.** AprilTags at surveyed positions as beacons, track odometry as u with σ_s ≠ 0 in (93)
  for slip, a total station or the start-equals-end loop error as ground truth.

## What to copy from the paper, what to borrow from the code, what to leave out

| keep from the paper | reason |
| --- | --- |
| right ⊕/⊖ everywhere, left only for global priors (53) | one convention removes half the Jacobian bugs |
| Jacobians built from the blocks with the chain rule (58) | every H and factor Jacobian is a product of FD-tested blocks |
| covariance on the tangent (52), propagation (55) | the only definition that has the right size |
| composite ⊖◇ for errors and covariances (Ex. 7) | position errors are p₂ − p₁, as a covariance expects |

| borrow from the code (manif, GTSAM) | reason |
| --- | --- |
| store SO(3) as a quaternion, Log via atan2 and the w ≥ 0 flip (manif) | Log is then accurate at 0 and at π (C1) |
| renormalize after each product when ‖q‖² drifts from 1 (manif) | one multiply, no drift |
| Shepperd's method for matrix → quaternion (GTSAM) | the robust matrix Log (C1) |
| 2 sin²(θ/2) for 1 − cos θ (GTSAM) | full precision with no branch |
| `rminus` returning both ⊖ blocks with the value (manif) | the factor code gets (82)–(83) for free |

| not in this plan | reason |
| --- | --- |
| left Jacobians of functions (44) and crossed Jacobians (47)–(50) | not needed once everything is right; use (46) if a library hands you a left one |
| S¹ as complex numbers | SO(2) as an angle and a 2×2 matrix covers it (App. A) |
| SE₂(3), Sim(3), Bundle templates | later lessons (IMU preintegration, t2.11) |
| sparse solvers in the prototype | Fig. 12 has 15 unknowns; `lstsq` is exact and simple. Sparse QR only at step 7 |

## Pitfalls the code shows and the paper does not mention

- **Printed small-angle formulas above the switch.** manif's switch is `eps = 100 × machine epsilon` compared with θ²
  (`include/manif/constants.h:50`), so θ = 1.5 × 10⁻⁷. Above it, the printed SE(2) third column
  (`include/manif/impl/se2/SE2Tangent_base.h:163`) is off by 2.7 × 10⁻³ at θ = 2 × 10⁻⁷ for |ρ| = 1, and the SE(3)
  Q coefficient (`include/manif/impl/se3/SE3Tangent_base.h:272`) costs up to 4.2 × 10⁻¹⁰ in Q (measured:
  `C4_Jr_col3_abserr`, `C5_Q_abserr`). The SE(2) one is the one that matters: when a robot drives straight, θ = ω δt is near zero
  and lands in that range. GTSAM switches at θ = 10⁻³ (`gtsam/geometry/SO3.cpp:57`). Use the rewritten forms of C4
  and C5 in the prototype; on the robot, either live with manif's error or patch those two lines.
- **The example's simulated noise is uniform.** `u_noise = u_sigmas * Array3d::Random();`
  (`examples/se2_localization.cpp:207`) draws from [−σ, σ], variance σ²/3, while the filter is told σ²
  (`u_sigmas << 0.1, 0.1, 0.1;`, `:144`). Measured with C8 on that setup at a tenth of the control noise: ANEES 1.00
  with uniform noise and 3.03 with Gaussian (`IMPL_anees`, 200 runs of 100 steps, 3 is consistent). Use Gaussian noise
  in every consistency test.
- **The example's noise level is beyond first order.** At the example's own σ = 0.1 per step against 1 cm beacons,
  the ESKF with Gaussian noise gives ANEES 6.8 with the J_r(δx) reset and 8.3 without it (`IMPL_anees`). Use smaller
  steps or an iterated update before blaming the Jacobians, which FD has already cleared.
- **Gain by explicit inverse, covariance without Joseph form.** `K = P * H.transpose() * Z.inverse();` (`:261`) and
  `P = P - K * Z * K.transpose();` (`:268`). Fine for 2×2 at these noise levels; use LLT and Joseph form (C8) before
  the noise ratios get extreme.
- **The SAM solve inverts JᵀJ,** `dX = - (J.transpose() * J).inverse() * J.transpose() * r;`
  (`examples/se2_sam.cpp:541`), and the authors flag it themselves on the line above (`:540`). Stop rule
  `if (dX.norm() < 1e-6) break;` (`:568`) and `MAX_ITER = 20` (`:228`) are worth copying.
- **Prior residual with a left minus.** `poses[0].lminus(SE2d::Identity(), …)` (`:471`): for an identity prior it equals
  the paper's right ⊖; for any other prior, decide whether the prior is global (left) or local (right) and take the
  matching Jacobian. The comment above that line explains this.
- **Opposite sign of the calibration bias.** manif adds the offset, `u + J_u_c * c`
  (`examples/se3_sam_selfcalib.cpp:509`), where (111) subtracts it; its Jacobian is `- W * J_u_c` (`:514`). An estimated
  c compared across the two conventions has the opposite sign.
- **Noise names.** manif calls the measurement covariance `R` and the control covariance `U`; the paper calls them
  N and W; this repo calls them `Q_meas` and `R_proc`. Rename at the boundary, once.

## Licence note

manif is MIT and GTSAM is BSD: both allow copying and linking in the robot code, provided the copyright notice is kept.
The prototype is still written from the equations (clean-room) because the exercise is to derive each line; the
links in `translate.md` are for reading alongside. Using manif directly on the robot (deliverable 2) needs only its
licence file shipped with the binary.
