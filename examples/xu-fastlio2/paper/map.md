---
source: xu-fastlio2
unit: 1
title: "FAST-LIO2: Fast Direct LiDAR-Inertial Odometry"
kind: paper
pages: [1, 13]
lesson: t2.8
stage: map
---

# Map

## What the paper claims

Two changes to FAST-LIO make LiDAR-inertial odometry both faster and more accurate: (1) register the **raw**
LiDAR points to the map directly, no edge/plane feature extraction, which keeps subtle features and makes the
front end LiDAR-agnostic; (2) keep the map in an **incremental k-d tree (ikd-Tree)** that supports insertion,
box-wise deletion, down-sampling and re-balancing in place, so the map can be updated and searched at scan rate
without rebuilding. The estimator is the tightly-coupled **iterated error-state Kalman filter on manifolds** from
FAST-LIO, with the Kalman gain written in a form whose cost grows with the state dimension (24) instead of the
number of points (thousands).

## Sections → what you must leave with

| § | section | leave with |
| --- | --- | --- |
| I–II | Introduction, related work | why feature extraction was the bottleneck; where this sits between LOAM-style and direct methods |
| III | System overview | the data flow: IMU forward propagation → backward propagation (undistortion) → iterated update against the ikd-Tree map → map insertion |
| IV | State estimation | the state on the manifold $\mathcal{M} = SO(3)\times\mathbb{R}^{15}\times\mathbb{S}^2\times SO(3)\times\mathbb{R}^3$, the ⊞/⊟ operators, forward propagation (Eq. 2–6), backward propagation (Eq. 7–8), the point-to-plane residual (Eq. 9–12), the iterated update and the gain (Eq. 18–20) |
| V | Mapping | ikd-Tree: structure, incremental insert with on-tree down-sampling, box delete, lazy labels, re-balance criteria (α_bal, α_del), parallel rebuild |
| VI | Experiments | 10–30 ms per scan on an ARM board; accuracy on 19 sequences; ablation of ikd-Tree vs. rebuilding a static k-d tree |

## The five things

1. **Direct registration**: every (down-sampled) raw point is matched to a plane fitted on its 5 nearest map points; the residual is the point-to-plane distance.
2. **Manifold state and error state**: estimate a 24-dim state, update a 23-dim tangent error; gravity lives on $\mathbb{S}^2$ (2 dof), not $\mathbb{R}^3$.
3. **Backward propagation**: each point is moved to the scan-end frame using the IMU poses integrated *backwards* inside the scan; no interpolation of a global trajectory.
4. **The gain in information form**: $K = (H^TR^{-1}H + P^{-1})^{-1}H^TR^{-1}$ — invert a 23×23 matrix, never an $m\times m$ one.
5. **ikd-Tree**: an incremental, lazily-deleted, self-balancing k-d tree that makes "update the map with every scan" affordable.

## Reading order for the cards

C1 state and ⊞ → C2 forward propagation → C3 backward propagation → C4 residual and $H$ → C5 the iterated update → C6 ikd-Tree operations.
Exercise tiers for a 13-page paper: T1 concept, T2 derivation (the gain identity), T3 implement (the update on synthetic planes), T5 robot (a 2-D LiDAR+IMU simulation); no T4.

## Open questions carried to HANDOFF

- The paper's Eq. 8 uses the *scan-end* IMU state for undistortion; the code comments "not accurate!" at that line — worth a lecture aside on what is approximated.
- Extrinsic estimation is in the state but off by default in the shipped config; decide whether C4 shows the 12-column $H$ or the 6-column one.
