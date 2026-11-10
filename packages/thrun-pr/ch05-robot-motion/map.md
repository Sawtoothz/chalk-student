---
book: thrun-pr
chapter: 5
title: Robot Motion
printed_pages: [117, 148]
pdf_pages: [138, 169]
lesson: t2.4
prereqs:
  - t2.1 Bayes filter (Thrun ch. 2; p(xₜ ∣ uₜ, xₜ₋₁) is the prediction step of Table 2.1)
  - t2.2 Gaussian filters (Thrun ch. 3; the velocity model g(u, x) of (5.9) is already the EKF example of the ch. 3 package, with additive noise instead of noise on the controls)
  - t2.3 nonparametric filters (Thrun ch. 4; Table 4.3 line 4 is exactly the sampling algorithms of this chapter; the ch. 4 T5 already sampled noise on (v, ω))
  - probability: densities vs sampling, change of variables only by name, variance of a sum of uniforms
  - geometry: circle through two points with a given tangent, atan2 and angle wrapping
feeds:
  - t2.4 robot perception (Thrun ch. 6; same lesson: the motion model is the predict half, ch. 6 the update half)
  - t2.7 EKF/UKF localization (Thrun ch. 7; the velocity model is linearized there, with control noise mapped through its Jacobian)
  - t2.3 grid and Monte Carlo localization (Thrun ch. 8; sample_motion_model_odometry is MCL's line 4, motion_model_odometry fills the grid filter's transition)
  - t2.9 FastSLAM (Thrun ch. 13; same samplers, per particle)
  - tracked robot: skid-steer is commanded in (v, ω), so the velocity model fits the interface; whether track slip makes odometry worse than the commands is untested on the real hull; the book says odometry is usually more accurate (pp. 121, 132), and T5's simulated slip agrees once spins are modelled
  - quadruped: the book's models exclude legged robots (p. 121); body-velocity commands with a sideways component need book exercise 7 (holonomic)
  - drone: kinematic models do not apply; exercises 1–3 (a robot with dynamics) are the first step, inertial sensing is mentioned on p. 144 only
  - RoboCup and FORGE: walking odometry as (δrot1, δtrans, δrot2) is the relative-pose factor between consecutive poses in a factor graph
status: draft
---

# Chapter map

One idea: the state transition p(xₜ ∣ uₜ, xₜ₋₁) for a planar robot is a deterministic kinematic model with noise injected into the motion parameters, and every algorithm comes in two forms. The *density* form inverts the kinematics to recover the motion parameters that would explain a given pose change, then scores their deviation from the commanded or measured ones; the *sampling* form perturbs the parameters and runs the kinematics forward. The chapter does this twice: for velocity commands (v, ω) over Δt, which move the robot on a circle (5.3), and for odometry decomposed as rotate–translate–rotate (5.4). The velocity model needs a third noise term, a final rotation γ̂, because two noise variables leave the posterior on a 2-D manifold inside 3-D pose space (p. 129). Section 5.5 conditions either model on a map by multiplying by p(xₜ ∣ m), which checks only the final pose, not the path.

| Section | Pages | Verdict | Time | What to take |
| --- | --- | --- | --- | --- |
| 5.1 Introduction | 117–118 | must | 10 min | Kinematics made probabilistic by noise on the actuation; models that overestimate uncertainty are more robust (p. 118) |
| 5.2.1 Kinematic configuration | 118–119 | skim | 5 min | Pose (x, y, θ) (5.1), θ = 0 along x, counterclockwise positive; location (5.2) |
| 5.2.2 Probabilistic kinematics | 119–121 | must | 10 min | (5.3); Fig 5.2; velocity model for planning, odometry model for estimation (p. 121) |
| 5.3 + 5.3.1 Velocity model, closed form | 121–123 | must | 25 min | Table 5.1 (inverse model, α₁–α₆), Table 5.2 (normal and triangular densities with variance b²), Fig 5.3 |
| 5.3.2 Velocity model, sampling | 122–125 | must | 20 min | Table 5.3 lines 2–7; Table 5.4 samplers; Fig 5.4; sampling is easier than evaluating the density (p. 125) |
| 5.3.3 Exact motion, real motion, final orientation | 125–129 | must | 30 min | Circle (5.5)–(5.9); noisy controls (5.10)–(5.13); the degeneracy and γ̂ (5.14)–(5.16) |
| 5.3.3 Computation of p(xₜ ∣ uₜ, xₜ₋₁), sampling | 129–132 | skim, derive (5.17)–(5.25) | 25 min | Centre of the circle through two poses (5.17)–(5.19), r*, Δθ, (5.22) atan2, errors (5.26)–(5.32) |
| 5.4 + 5.4.1 Odometry model, closed form | 132–135 | must | 25 min | Odometry as a control (5.33); rot–trans–rot (Fig 5.7); Table 5.5; wrap δrot2 − δ̂rot2 (p. 135) |
| 5.4.2 Odometry model, sampling | 136–138 | must | 15 min | Table 5.6; Fig 5.9; Fig 5.10 dead reckoning: uncertainty grows without bound |
| 5.4.3 Odometry derivation | 137–139 | skim | 10 min | (5.34)–(5.46): the same three equations read forward (sampling) and backward (density) |
| 5.5 Motion and maps | 140–143 | must | 25 min | (5.47)–(5.51); Table 5.7; Fig 5.11 and the "through the wall" error; fine only for small motions |
| 5.6 Summary | 143–144 | must | 5 min | Compare with your own; dynamics and inertial sensing named as not covered |
| 5.7 Bibliographical remarks | 145 | skip | — | Siegwart and Nourbakhsh (2004) for kinematics of other drive types |
| 5.8 Exercises | 145–147 | do 1–3, 5, 7, 8; 4 as part of 5; 6 optional | in package | 1–3 dynamics (the drone's first step); 4–5 bicycle (Ackermann); 7 holonomic (quadruped, omni base); 8 triangular mean and variance |

Total reading at "must": about 2.8 hours (165 min over about 20 pages), plus 40 min of skim. Coding (exercises T3) about 4 hours.

## Inventory

Definitions: kinematics, configuration, pose, bearing (heading direction), location, motion model, velocity motion model, translational and rotational velocity, motion error parameters α₁–α₆, normal and triangular distribution with variance b², final rotation γ̂, inverse motion model, odometry motion model, relative motion information, δrot1 / δtrans / δrot2, map-based motion model, configuration (pose) space.

Algorithms: Table 5.1 motion_model_velocity, Table 5.2 prob_normal_distribution and prob_triangular_distribution, Table 5.3 sample_motion_model_velocity, Table 5.4 sample_normal_distribution and sample_triangular_distribution, Table 5.5 motion_model_odometry, Table 5.6 sample_motion_model_odometry, Table 5.7 motion_model_with_map and sample_motion_model_with_map.

Figures worth redrawing in the lecture: 5.3/5.4 (density vs samples for three α settings), 5.5 (the circle), 5.7 (rot–trans–rot), 5.8/5.9, 5.10 (dead-reckoning spread over a path), 5.11 (map-conditioned density and the through-the-wall region).

Equations you will implement: Table 5.1 with (5.17)–(5.25) and (5.32); Table 5.2 = (5.11), (5.12); Table 5.3 = (5.10), (5.15), (5.16); Table 5.4; Table 5.5 = (5.34)–(5.36), (5.44)–(5.46); Table 5.6 = (5.37)–(5.40); Table 5.7 = (5.48).

Equations you will derive by hand: (5.9) from the circle geometry (5.5)–(5.8); (5.18) by solving (5.17); (5.23)–(5.25); variance of Table 5.4's samplers (book exercise 8); (5.48) from (5.49)–(5.51).

Traps to carry into cards and T4 (decided now, so later stages do not rediscover them):
- **Table 5.1 line 7 loses the sign of v̂.** v̂ = Δθ r*/Δt carries the sign of Δθ, not of the motion (measured cases in card C3). The card fixes it and a test covers right turns and reversing.
- **Table 5.1 line 2 divides by zero for straight-line motion** (the circle's centre is at infinity, p. 130); Table 5.3 lines 5–6 divide by ω̂ = 0. Both need a straight-line branch.
- **p. 132 says sample_normal_distribution's values "lie always in [−2b, 2b]".** The support is [−6b, 6b]; the variance b² is right (lecture L4).
- **Table 5.5 line 2 is atan2(0, 0) for a rotation in place** (δtrans = 0): δrot1 is then arbitrary and the noise terms α₁δ²rot1 are meaningless. Robust code sets δrot1 = 0 below a translation threshold.
- **Angular differences must be wrapped** (p. 135 says δrot2 − δ̂rot2 "has to be truncated"; the same holds for δrot1 − δ̂rot1 in line 8 and for θ′ − θ in Table 5.1 line 9 and line 6's Δθ).
- **Table 5.7's sampler has two lines numbered 3** and an unbounded do–until loop (p. 141 warns about termination); robust code caps the retries.
- **Table 5.5 line 8 uses the hatted δ̂ in the variances, Table 5.6 line 5 the measured δ.** (Amended at the cards stage: p. 139 eq. 5.44–5.46 use the measured δ, so only Table 5.5 differs. Robust C4 uses δ; the naive card keeps the table.)
- **prob() with a zero variance** (robot at rest: v = ω = 0 makes every b² zero) returns 0/0. Add a floor to b².
- **Book exercise 5's control table numbers its last row 1**; it is problem 5.

## Dependencies inside the chapter

```
Bayes filter prediction step (ch. 2, Table 2.1): p(x_t | u_t, x_{t-1})   (5.3)
 ├── 5.2 pose (5.1), location (5.2), control vs odometry (p. 120-121)
 ├── 5.3 velocity model, u = (v, ω)   (5.4)
 │     ├── exact motion on a circle (5.5)-(5.9)
 │     ├── noisy controls (5.10)-(5.13), error densities Table 5.2 = (5.11), (5.12)
 │     ├── degeneracy -> final rotation γ̂ (5.14)-(5.16)
 │     ├── density: invert (5.17)-(5.25), errors (5.26)-(5.32)  -> Table 5.1
 │     └── sampling: forward (5.16)                             -> Table 5.3, Table 5.4
 ├── 5.4 odometry model, u = (x̄_{t-1}, x̄_t)   (5.33)
 │     ├── rot-trans-rot (5.34)-(5.36), noise (5.37)-(5.39), forward (5.40)
 │     ├── density (5.41)-(5.46)  -> Table 5.5
 │     └── sampling               -> Table 5.6
 └── 5.5 map-based model (5.47)-(5.51) -> Table 5.7, wraps either model above
```

## What this chapter does not cover (and where it is)

- Linearizing the motion model for the EKF, with control-space noise mapped into state space through the Jacobian: Thrun ch. 7, lesson t2.7.
- Using the samplers inside MCL and the motion model inside grid localization: Thrun ch. 8, lesson t2.3.
- Robot dynamics (state with velocities, forces): only book exercises 1–3 here; for the drone this is where IMU-driven process models come in (Barfoot; lesson t2.6 for the SE(3) part).
- 3-D motion, SE(3) poses and inertial sensing: named on p. 144 only; Barfoot, lesson t2.6.
- Holonomic and car-like kinematics: book exercises 7 and 4–6; Siegwart and Nourbakhsh (2004).
- Skid-steer specifics (instantaneous centre of rotation, track slip as a function of turn rate): not in the book; this package's T5 models it on the odometry side: a slip factor χ that divides the odometry's heading change, a separate noise term for spins in place, and an outlier mixture.
- Calibrating α₁–α₆ from data: not in this chapter; this package's T5 does it (maximum likelihood on simulated odometry with ground truth).
- Path-consistent map-based motion (checking the swept path, not only the final pose): the book argues it away for high update rates (p. 143); collision checking along the arc belongs to planning, not this book's filters.
