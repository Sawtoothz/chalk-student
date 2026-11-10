---
book: sola-microlie
chapter: 1
title: A micro Lie theory for state estimation in robotics
kind: paper
printed_pages: [1, 17]
pdf_pages: [1, 17]
lesson: t2.6
prereqs:
  - t2.2 Gaussian filters (Thrun ch. 3; the ESKF of §V-A is Table 3.3 with + replaced by ⊕ in (99) and (101) and the Jacobians taken from App. C)
  - t2.6 matrix Lie groups (Barfoot ch. 8, same lesson, package at map stage only; same objects, other conventions — left perturbation, ξ = (ρ, φ); this paper perturbs on the right with τ = (ρ, θ))
  - Gauss-Newton on a sum of squared residuals (normal equations (109); Barfoot ch. 4 §4.3.1, or Grisetti t2.8)
  - linear algebra: skew-symmetric matrices and the cross-product matrix [a]ₓ, matrix exponential as a power series, block matrices; quaternion product (Ex. 2, App. B)
feeds:
  - t2.7 EKF localization (Thrun ch. 7); §V-A is landmark localization on SE(2) with the Jacobians written once in Lie form
  - t2.8 graph SLAM (Grisetti tutorial, "Least Squares on a Manifold"; FAST-LIO2's ⊞/⊟ on SO(3) × ℝⁿ × S² is the composite manifold of §IV)
  - t2.11 IMU preintegration (Forster et al., ref. [6]); built on (56), (68)–(70) and the J_r of (143)–(144)
  - Barfoot ch. 8 package; (75) Ad = J_l J_r⁻¹ and (147) J_l = J_rᵀ are the bridge between the two conventions
  - drone: attitude integration R_k = R_{k−1} Exp(ω δt) (56); covariance of attitude in the local tangent (52), (55)
  - quadruped: the state ⟨p, v, R, biases, feet⟩ is a composite manifold (§IV); the ESKF steps (99)–(102) carry over unchanged
  - tracked robot: §V-A is a planar tracked/skid robot almost verbatim (u_s, the lateral slip term in (92)–(93))
  - FORGE and GTSAM: GTSAM's Pose3 also perturbs on the right but orders the tangent (ω, v); manif (ref. [7]) is this paper's code and the reference implementation for the cards
status: draft
---

# Chapter map

One idea: a state that lives on a curved group (a rotation, a pose, a unit quaternion) is handled by doing every
calculus operation in the flat tangent space ℝᵐ and moving between the two only through Exp and Log. The plus and
minus operators (25)–(28) package that move, so that "state + increment" and "state − state" read as in a vector
space and give a vector of exactly m = dof numbers. From those two operators everything else follows by analogy with
vector calculus: the adjoint Ad_X (30) converts a tangent vector between the local frame at X and the global frame at
the identity; the right Jacobian (41a) is the ordinary limit definition with + and − replaced by ⊕ and ⊖; four
elementary blocks (inverse (62), composition (65)–(66), the Jacobians of Exp (67), (71), and the group action (77)–(78))
plus the chain rule (58) give every Jacobian a robot needs; covariance (52) is defined on the tangent perturbation,
and propagates as in a vector space (55). Section IV stacks several groups into one composite state, and Section V uses
the toolkit for an ESKF on SE(2) and a Gauss-Newton smoother, where the only lines that change from the textbook
versions are the ⊕ in the state update and the Jacobian blocks. The appendices are the formula sheet for S¹, SO(2),
S³, SO(3), SE(2), SE(3), ℝⁿ and T(n).

| Section | Pages | Verdict | Time | What to take |
| --- | --- | --- | --- | --- |
| I Introduction | 1–2 | skim | 5 min | What is left out on purpose (the Lie bracket, abstract 𝔪); everything is done in ℝᵐ |
| II-A The Lie group (Ex. 1–2, Fig. 2–4) | 2–3 | must | 10 min | Group axioms (1)–(4); smooth manifold; all tangent spaces alike; S¹ and S³ as the pictures to keep |
| II-B The group actions | 3 | must | 5 min | Action axioms (6)–(7); the four actions R·x, H·x, z x, q x q* |
| II-C Tangent spaces and the Lie algebra (Ex. 3, Table I, Fig. 5–6) | 3–5 | must | 15 min | 𝔪 = T_ℰM (8); v^ = X⁻¹Ẋ (9); hat and vee (10)–(11); Table I sizes vs dof |
| II-D The exponential map (Ex. 4–5) | 5–6 | must | 20 min | exp/log (14)–(15); Rodrigues from the series (Ex. 4); properties (17)–(20); Exp/Log (21)–(24) |
| II-E Plus and minus operators (Fig. 7) | 6 | must | 10 min | Right ⊕/⊖ (25)–(26) local, left (27)–(28) global; the paper defaults to right; footnote 3 frame convention |
| II-F The adjoint and the adjoint matrix (Ex. 6) | 6–7 | must | 15 min | Ad_X (29)–(31); X ⊕ τ = (Ad_X τ) ⊕ X (32); (33)–(34); Ad of SE(3) derived in Ex. 6 |
| II-G Derivatives on Lie groups (Fig. 8–9) | 7–9 | must | 25 min | Right Jacobian (41a–c) as a limit; linearization (43); left Jacobian (44); (46) relates them; crossed Jacobians (47)–(50) only as a pointer |
| II-H Uncertainty, covariance propagation (Fig. 10) | 9 | must | 10 min | Σ on the tangent perturbation (51)–(52), footnote 5; global vs local (53)–(54); Σ_Y ≈ J Σ_X Jᵀ (55) |
| II-I Discrete integration on manifolds (Fig. 11) | 9 | must | 5 min | X_k = X_{k−1} Exp(v_k δt_k) (56) |
| III intro, III-A The chain rule | 9–10 | must | 10 min | (57) left from right; (58) chain rule, proved via (43) three times; (59)–(60) when frames mix |
| III-B Elementary Jacobian blocks | 10 | must | 20 min | Inverse −Ad_X (62); composition Ad_Y⁻¹ and I (65)–(66); J_r, J_l and (68)–(74); Ad = J_l J_r⁻¹ (75); J_r(−τ) = J_l(τ) (76); action (77)–(78) |
| III-C Useful, but deduced, Jacobian blocks | 11 | must | 10 min | Log J_r⁻¹ (79); ⊕ (80)–(81); ⊖ −J_l⁻¹ and J_r⁻¹ (82)–(83) and the proof below them |
| IV Composite manifolds (Ex. 7) | 11–12 | must | 15 min | ⟨M₁,…,M_M⟩ with block Exp/Log (84)–(87); diamond ⊕/⊖ (86)–(88); block Jacobian (89); SE(n) vs T(n)×SO(n) vs ⟨ℝⁿ, SO(n)⟩ |
| V intro: the common setup | 12 | must | 5 min | SE(2) pose, ℝ² beacons; control u ∈ 𝔰𝔢(2) with slip u_s (92)–(93); motion (94); measurement X⁻¹·b (95)–(96) |
| V-A Localization with ESKF on manifold | 12 | must | 15 min | δx and P in the tangent at X̂ (97)–(98); prediction (99)–(100) with F = Ad_{Exp(u)}⁻¹, G = J_r(u); correction (101)–(102); H derived from the blocks |
| V-B Smoothing and mapping, graph-based | 12–13 | must | 15 min | Composite state (103); residuals with Ω^{T/2} (104)–(105); block-sparse J (107); GN step (106)–(110) |
| V-C SAM with self-calibration | 13 | skim | 5 min | Bias c in the state; one extra column in J (111) |
| V-D 3D implementations | 13 | skim | 2 min | Same algebra from (97) on with SE(3), 𝔰𝔢(3), ℝ³ |
| VI Conclusion | 13–14 | skip | — | Restates the seven choices; nothing new |
| App. A S¹ and SO(2) | 14 | skim | 10 min | Exp/Log (114)–(117); everything commutes, so every Jacobian is 1 or −1 (123)–(128); action (129)–(130) |
| App. B S³ and SO(3) | 14–15 | must | 15 min | Quaternion Exp/Log (132)–(133) and the w > 0 rule; Rodrigues and Log(R) (134)–(135); R(q) (138); Ad_R = R (139); J_r, J_r⁻¹, J_l, J_l⁻¹ (143)–(147); ⊕/⊖ (148)–(149); action (150)–(151) |
| App. C SE(2) | 16 | must | 15 min | Exp/Log with V(θ) (156)–(158); Ad (159); inverse, composition (160)–(162); J_r, J_l closed forms (163)–(164); action (166)–(167) |
| App. D SE(3) | 16–17 | skim (reference) | 10 min | Exp/Log with V(θ) = J_l(θ) (172)–(174); Ad (175); (176)–(178); J_l with Q(ρ, θ) (179)–(180); action (182)–(183) |
| App. E (ℝⁿ, +) and T(n) | 17 | skim | 3 min | The trivial group: ⊕ is +, every block is I or −I (185)–(193) |

Total reading at "must": about 3.5 hours (14 dense two-column pages; II-G and III-B take longer than the 10 min/page
rule). Coding (exercises T3) about 4 hours.

## Inventory

Definitions: Lie group (1)–(4); smooth manifold; group action (5)–(7); tangent space T_X M; Lie algebra 𝔪 = T_ℰM (8);
generators E_i; hat and vee (10)–(11); exp and log (14)–(15); capitalized Exp and Log (21)–(24); right and left ⊕, ⊖
(25)–(28); local and global frames (footnote 3); adjoint Ad_X (29) and adjoint matrix (30)–(31); right Jacobian of a
function (41a); left Jacobian of a function (44); crossed Jacobians (47)–(48); right and left Jacobians of M, J_r (67)
and J_l (71); covariance on a manifold (52), global covariance (53); composite manifold ⟨M₁,…,M_M⟩ (84) and diamond
⊕/⊖ (86)–(87); notation J_X^{f(X)} (below (57)).

Boxed examples: Ex. 1 S¹; Ex. 2 S³; Ex. 3 SO(3), 𝔰𝔬(3), ℝ³; Ex. 4 Exp of SO(3) (Rodrigues); Ex. 5 Exp of S³;
Ex. 6 Ad of SE(3); Ex. 7 SE(n) vs T(n)×SO(n) vs ⟨ℝⁿ, SO(n)⟩.

Figures and tables: Fig. 1 (manifold and 𝔪), Fig. 2 (T_X M), Fig. 3 (S¹), Fig. 4 (S³), Fig. 5 (velocities in local and
global tangents), Fig. 6 (the hat/vee/exp/log/Exp/Log diagram), Fig. 7 (local vs global deltas, Ad), Fig. 8 (right
Jacobian), Fig. 9 (all the linear maps between tangent spaces), Fig. 10 (covariance in the tangent), Fig. 11 (motion
integration), Fig. 12 (SAM factor graph); Table I (the groups: size, dim, constraint, τ^, Exp, composition, action).

Algorithms (no numbered tables; written as equation blocks): discrete integration (56); ESKF on SE(2) prediction
(99)–(100) and correction (101)–(102); Gauss-Newton SAM on a composite manifold (106)–(110); SAM with bias
self-calibration (111).

Equations you will implement:
- hat/vee and Exp/Log for SO(2) (113), (116)–(117); SO(3) (134)–(135) with small-angle branches; S³ (132)–(133) with
  the w > 0 rule; SE(2) (156)–(158); SE(3) (172)–(174); ℝⁿ (185)
- right and left ⊕/⊖ (25)–(28); composite ⊕/⊖ (86)–(87)
- adjoint: generic (31) as a numerical oracle, closed forms (139), (159), (175)
- elementary blocks: inverse (62), composition (65)–(66), J_r and J_r⁻¹ for SO(3) (143)–(144), J_l and J_l⁻¹
  (145)–(146), SE(2) J_r and J_l (163)–(164), SE(3) J_l with Q(ρ, θ) (179)–(180) and J_r via (76); ⊕ and ⊖ blocks
  (80)–(83), (148)–(149); action blocks (129)–(130), (150)–(151), (166)–(167), (182)–(183)
- covariance: global/local conversion (54), propagation (55)
- integration (56); the SE(2) motion model (92)–(94) and beacon model (95)–(96)
- ESKF (97)–(102) with F, G, H from App. C; Gauss-Newton SAM (103)–(110) with the block Jacobian (107); bias column (111)

Equations you will derive by hand:
- Rodrigues (Ex. 4) and the S³ exponential (Ex. 5) from the power series
- (20) X exp(τ^) X⁻¹ = exp(X τ^ X⁻¹), and from it (29)–(32)
- Ad of SE(3) (Ex. 6) and of SE(2) (159)
- the elementary blocks (62) and (65) from (41b)
- (75) Ad_{Exp(τ)} = J_l(τ) J_r⁻¹(τ) and (76) J_r(−τ) = J_l(τ)
- (82) J_X^{Y⊖X} = −J_l⁻¹(τ), following the proof under (83)
- the SO(3) action Jacobian (150) and the SE(2) action Jacobian (166)
- the measurement Jacobian H in §V-A, chained from (62) and (166) applied at X⁻¹
- F = Ad_{Exp(u)}⁻¹ and G = J_r(u) in (100) from (80)–(81)

## Dependencies inside the paper

```
II-A group axioms (1)-(4) ── II-B actions (5)-(7)
 └── II-C tangent space, 𝔪, hat/vee (8)-(11)
      └── II-D exp/log, Exp/Log (14)-(24)
           └── II-E ⊕/⊖ right (25)-(26), left (27)-(28)
                ├── II-F adjoint Ad_X (29)-(34)
                │    └── (46),(57) left Jacobian = Ad · right Jacobian · Ad⁻¹
                ├── II-G right Jacobian (41a), linearization (43), left (44)
                │    └── III-A chain rule (58)
                │         └── III-B blocks: inverse (62), composition (65)-(66),
                │              J_r, J_l of Exp (67)-(76), action (77)-(78)
                │              └── III-C Log, ⊕, ⊖ blocks (79)-(83)
                ├── II-H covariance on the tangent (51)-(55)
                └── II-I integration (56)
 IV composite ⟨…⟩, diamond ⊕/⊖ (84)-(91)  ← II-E, II-G per block
 Appendices A-E: closed forms of every block above, per group
 V setup (92)-(96) ── V-A ESKF (97)-(102)   ← III-B/C, II-H, App. C
                  └── V-B GN SAM (103)-(110) ← IV, III-C, App. C, App. E
                       └── V-C self-calibration (111)
```

## What this paper does not cover (and where it is)

- The Lie bracket, BCH formula and the structure of 𝔪 beyond a vector space: Barfoot ch. 8 §8.1.2 (bracket) and §8.1.5 (BCH), t2.6.
- Uncertainty beyond first order (fourth-order compounding, sigmapoint on the group): Barfoot ch. 8 §8.3.2–8.3.3, t2.6.
- The ESKF reset of P after the ⊕ update and the error-state kinematics with IMU biases: Solà's quaternion kinematics
  report (paper ref. [8]); not in `books.yaml` yet.
- Continuous-time error dynamics and interpolation on the group: Barfoot ch. 8 §8.2 and ch. 11.
- IMU preintegration on SO(3): Forster et al. (paper ref. [6]), t2.11; not in `books.yaml` yet.
- Robust costs, marginalization and sparse solvers (QR, Cholesky, iSAM2) for (109): Grisetti tutorial t2.8, refs. [12]–[15].
- Invariant EKF (errors defined so that F does not depend on the estimate): Barfoot ch. 8 §8.4 and §9.2.4.
- S² (unit vectors, gravity direction) and other non-group manifolds used in FAST-LIO2: xu-fastlio2, t2.8.
