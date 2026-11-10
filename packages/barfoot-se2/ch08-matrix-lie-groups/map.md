---
book: barfoot-se2
chapter: 8
title: Matrix Lie Groups
printed_pages: [279, 374]
pdf_pages: [299, 394]
lesson: t2.6
prereqs:
  - t2.6 three-dimensional geometry (Barfoot ch. 7, same lesson, not yet packaged; the C_vi frame-rotation convention of §7.3.2, the cross-product operator, Poisson's equation (7.45), Euler-angle perturbations §7.2.5 and homogeneous points §7.3.1 are used here without re-deriving them)
  - t2.11 batch estimation (Barfoot ch. 4 §4.3.1; Gauss-Newton, line search and Levenberg-Marquardt; 8.1.9 is exactly that method with a new perturbation; robust costs are §5.4.2)
  - t2.2 Gaussian filters (Thrun ch. 3; the sigmapoint transform of 8.3.3 and 8.3.7 is the unscented transform of Thrun Table 3.4)
  - probability: Isserlis' theorem for fourth moments of a Gaussian (Barfoot ch. 2), change of variables in a density
  - linear algebra: matrix exponential and logarithm, eigenvectors, skew-symmetric matrices, Cholesky, Jacobi's formula det(exp A) = exp(tr A)
feeds:
  - Barfoot ch. 9–10 pose and pose-and-point estimation (no lesson id in books.yaml yet); point-cloud alignment, the SVD projection onto SO(3) promised on p. 329 (§9.1.3), the invariant EKF (§9.2.4) and inertial navigation on SE₂(3) (§9.4, book exercise 8.21)
  - Barfoot ch. 11 continuous-time estimation; the perturbed interpolation of 8.1.7 (8.143, 8.160) is what it needs
  - t2.8 graph SLAM and FAST-LIO2; the paper's A(·)⁻ᵀ in Eq. 11 is J_r⁻¹ of (8.81a); the relative-pose covariance (8.368) is what a pose-graph edge stores; GN on SE(3) (8.195–8.201) is the inner loop
  - t2.11 IMU preintegration; the rotation update (8.238–8.241), the Magnus correction (8.245) and the perturbation solution (8.296) are its rotation half
  - t2.7 EKF localization; book exercise 8.22 is an EKF on SO(3)
  - drone: attitude integration by exp(ω^Δt) (8.238) instead of re-normalising; on-manifold MPC needs J and Ad in its linearisation (8.299–8.304)
  - quadruped: the moving-frame invariant error (8.415) is the error of the invariant EKF (Barrau and Bonnabel 2017, p. 368), which is the common choice for legged state estimation with contact kinematics
  - tracked robot: SE(2) is book exercise 8.20; the "banana" of 8.355–8.357 is the book's own unicycle example (p. 349), constant forward speed with uncertain yaw rate
  - FORGE and GTSAM: GTSAM perturbs Pose3 on the right with the tangent ordered (ω, v); Barfoot perturbs on the left with ξ = (ρ, φ). Converting between them is Ad (8.47) and J_ℓ = 𝒯 J_r (8.92); the package must test this, not assume it
status: draft
---

# Chapter map

One idea: keep the large part of a rotation or pose in the group, as a matrix with no singularities but with constraints, and put every small thing (an optimiser step, a velocity, a noise sample) in the Lie algebra, as an unconstrained vector, joined by the exponential map. The chapter uses this idea three times. Geometry (8.1) builds the dictionary: hat and vee, exp and log in closed form, the adjoint Ad, BCH and the Jacobians J that account for non-commuting products; then it does Gauss-Newton with the left perturbation T = exp(ε^)T_op (8.1.9), which turns a constrained problem into an unconstrained one at every iteration. Kinematics (8.2) integrates Ṫ = ϖ^T in the group and linearises it to δξ̇ = ϖ^⋏δξ + δϖ, whose transition matrix is the adjoint of the nominal solution, 𝒯(t)𝒯(s)⁻¹ (8.302). Probability (8.3) defines a Gaussian on the group as T = exp(ε^)T̄ with ε ~ N(0, Σ), then compounds, inverts, differences, fuses and projects such Gaussians through a camera. Section 8.4 explains why errors defined as relative poses do not depend on the world frame (invariance, equivariance); the rest of the book relies on that. Two conventions run through every page and differ from GTSAM and Solà: ξ = [ρ; φ] with translation first (8.14), and the left Jacobian with left perturbations (p. 302, footnote 14).

| Section | Pages | Verdict | Time | What to take |
| --- | --- | --- | --- | --- |
| Intro, 8.1.1 SO(3) and SE(3) | 279–281 | skim | 15 min | Not vector spaces (8.4); group axioms (Table 8.1); T⁻¹ in closed form (8.9) |
| 8.1.2 Lie algebras | 281–283 | must | 20 min | φ^ (8.10), ξ^ 4×4 (8.14), ξ^⋏ 6×6 (8.17); the bracket is the matrix commutator |
| 8.1.3 Exponential map: rotations | 283–287 | must | 35 min | Series to Rodrigues (8.23); log by trace (8.28) with the sign check; surjective-only, unique for \|φ\| < π |
| 8.1.3 Exponential map: poses, Jacobian | 287–290 | must | 35 min | T = [C, Jρ; 0ᵀ, 1] (8.33–8.34); ρ = J⁻¹r (8.35); J and J⁻¹ closed form (8.37); J = ∫C^α dα (8.40); C = 1 + φ^J (8.42); 4×4 series (8.44) |
| 8.1.4 Adjoints: Ad and ad | 291–293 | must | 25 min | 𝒯 = Ad(T) = [C, r^C; 0, C] (8.47); (Cv)^ = Cv^Cᵀ (8.50); Ad(T)⁻¹ = Ad(T⁻¹) (8.51); ad = ξ^⋏ (8.55–8.56) |
| 8.1.4 Adjoints: exp map, direct series | 293–295 | skim | 10 min | Commuting diagram (8.61); Ad(exp ξ^) = exp(ξ^⋏) (8.62); 6×6 series (8.68). The proof (8.63–8.66) is optional |
| 8.1.5 BCH: general formula | 296–297 | skim | 10 min | Why exp(A)exp(B) ≠ exp(A+B); linear-in-one-argument forms (8.75–8.76); Bernoulli numbers (8.77) |
| 8.1.5 BCH for SO(3) and SE(3), left and right Jacobians | 297–302 | must | 55 min | (8.80); J_r, J_ℓ and inverses (8.81–8.82); J_ℓ = CJ_r (8.83); J_ℓ(−φ) = J_r(φ) (8.85); 𝒥 = [J, Q; 0, J] (8.90–8.91); direct series (8.99); inverses (8.100); "choosing the left" (8.104–8.105) |
| 8.1.6 Distance, volume, integration | 302–305 | skim | 20 min | Left and right differences (8.106, 8.115); ln(δC)^∨ ≈ Jδφ (8.109, 8.120); \|det J\| (8.113, 8.124) |
| 8.1.7 Interpolation: rotations | 305–307 | must | 15 min | C = (C₂C₁ᵀ)^α C₁ (8.128) is constant angular velocity (8.134–8.137) |
| 8.1.7 Perturbed interpolation, Faulhaber, poses | 307–311 | skip, return for ch. 11 | — | Result only: δφ = (1 − A)δφ₁ + Aδφ₂ (8.143), and 8.160 for poses |
| 8.1.8 Homogeneous points | 311–312 | must | 10 min | p^⊙ 4×6 and p^⊚ 6×4 (8.163); ξ^p = p^⊙ξ (8.164); (Tp)^⊙ = Tp^⊙𝒯⁻¹ (8.165) |
| 8.1.9 Calculus and optimization | 312–318 | must | 60 min | ∂(Cv)/∂φ = −(Cv)^J (8.170) vs ∂(Cv)/∂ψ = −(Cv)^ (8.179); C ← exp(ψ^)C_op; GN on SO(3) (8.185–8.191) and SE(3) (8.195–8.201); three properties (p. 318) |
| 8.1.10 Optimization on Riemannian manifolds | 318–322 | skim | 20 min | Retraction = exp (8.205); Riemannian gradient (8.209, 8.224); the perturbation step equals Riemannian GD (8.216, 8.230) |
| 8.1.11 Identities | 322–324 | skim, keep open | 10 min | The two identity pages (pp. 323–324, printed rotated) are the reference sheet for every card |
| 8.2.1 Rotations: kinematics, numerical integration | 325–327 | must | 30 min | Ċ = ω^C (8.232); ω = Jφ̇ (8.236); exp(ω^Δt) update (8.238–8.241); Magnus terms (8.244–8.245) |
| 8.2.1 Projection onto SO(3), transport theorem | 327–329 | skim | 10 min | R = (CCᵀ)^(−1/2)C (p. 328) and its det = −1 failure (footnote 23); v̇_i = C_iv(v̇_v − ω^v_v) (8.254) |
| 8.2.2 Poses: kinematics, hybrid, integration | 329–331 | must | 25 min | Ṫ = ϖ^T (8.257); ϖ = 𝒥ξ̇ (8.260); hybrid (8.262); exp(ϖ^Δt) update (8.263–8.267); Magnus (8.269) |
| 8.2.2 With dynamics, transport theorem | 332–333 | skim | 10 min | Rigid-body dynamics in ϖ (8.270) with mass matrix (8.271); ṗ_v = p_v^⊙ϖ (8.276) |
| 8.2.3 Linearized rotations: Lie group | 333 | must | 10 min | Nominal Ċ = ω^C, perturbation δφ̇ = ω^δφ + δω (8.279) |
| 8.2.3 Linearized rotations: Lie algebra | 333–335 | skim | 15 min | Same answer the hard way (8.288); uses (8.285), proved in App. B.2.1 |
| 8.2.3 Solutions commute, integrating | 335–337 | must | 20 min | Φ(t, s) = C(t)C(s)ᵀ (8.295); closed-form δφ(t) (8.296) |
| 8.2.4 Linearized poses | 337–338 | must (dynamics part skim) | 15 min | δξ̇ = ϖ^⋏δξ + δϖ (8.301); Φ = 𝒯(t)𝒯(s)⁻¹ (8.302–8.303); with dynamics (8.308–8.309) |
| 8.3 intro, 8.3.1 Gaussian random variables and PDFs | 338–344 | must | 45 min | Left, middle, right table (p. 339); C = exp(ε^)C̄ (8.312); induced p(C) (8.319); mean and covariance (8.320–8.323); exact under a fixed rotation (8.324–8.325); poses (8.326–8.331) |
| 8.3.2 Uncertainty on a rotated vector | 344–345 | must | 15 min | E[y] to fourth order (8.338) versus samples and sigmapoints (Fig. 8.5) |
| 8.3.3 Compounding poses: theory, sigmapoint | 345–349 | must (8.347–8.351 skim) | 40 min | Mean T̄₁T̄₂ (8.343); Σ₂nd = Σ₁ + 𝒯₁Σ₂𝒯₁ᵀ (8.350b, 8.352); Σ₄th (8.352); sigmapoints (8.353–8.354) equal second order here |
| 8.3.3 Simple compound example, compound experiment | 349–352 | must | 20 min | Closed-form Σ_K (8.357b) with no x-growth at second order; Fig. 8.7 banana; Fig. 8.8 (the book reports fourth order better by about a factor of seven) |
| 8.3.4 Inverse pose | 352–353 | must | 10 min | ξ′ ~ N(0, 𝒯̄⁻¹Σ𝒯̄⁻ᵀ) (8.362), exact |
| 8.3.5 Compounding and differencing correlated poses | 353–354 | must | 10 min | (8.366) and (8.368); derivations are book exercises 8.14–8.15 |
| 8.3.6 Fusing poses | 354–358 | must | 35 min | e_k = ln(T̄_kT⁻¹)^∨ (8.371); G_k = 𝒥(−e_k)⁻¹ (8.373); normal equations (8.375); Σ (8.377); the fusion experiment (8.378–8.380, Figs. 8.10–8.11) |
| 8.3.7 Camera model: points, first order | 358–361 | must | 25 min | p = p̄ + Dζ (8.382–8.383); z ≈ z̄ + Zθ with Z = [(T̄p̄)^⊙, T̄D] (8.389b); G = SZ (8.391b); first order (8.392) |
| 8.3.7 Second order, sigmapoint, stereo, experiment | 361–366 | skim | 20 min | ȳ₂nd (8.397), R₄th (8.398), sigmapoints (8.399–8.401), stereo s, ∂s/∂z, Hessians (8.402–8.405); Figs. 8.12–8.13 |
| 8.4 Symmetry, invariance, equivariance | 366–369 | must | 25 min | J*(T₁₂p) = J*(p) (8.410); T*(T₁₂p) = T*(p)T₁₂ (8.412); moving-frame vs stationary-frame invariant errors (8.415–8.416); InEKF, EqF |
| 8.5 Summary | 369 | must | 5 min | Compare with your own |
| 8.6 Exercises | 369–373 | do 3, 14, 15, 17, 20, 21, 22 | in package | 20 (SE(2)) is the tracked robot; 21 (SE₂(3)) the drone IMU state; 22 is a full EKF on SO(3) |

Total reading at "must": about 10 hours (8.1 about 4.3 h, 8.2 about 1.7 h, 8.3–8.5 about 3.8 h); the skim rows add about 2.3 hours. That is three sittings, one per part; do not try it in one. Coding (exercises T3) about 4 hours, more if you take book exercise 8.22 as the T5 filter.

## Inventory

Definitions: SO(3) (8.1) and SE(3) (8.5); group, Lie group, matrix Lie group (p. 280); group properties (Table 8.1); Lie algebra and Lie bracket (pp. 281–282); so(3) and the hat φ^ (8.10) with vee (8.11); se(3) and ξ^ (8.14) with vee (8.15); ξ^⋏ (8.17); matrix exponential and logarithm (8.19–8.20); surjective-only map (p. 284, footnote 29); left Jacobian J of SO(3) (8.36, 8.40); adjoint map and adjoint representation Ad(T) (8.45–8.47); Ad(SE(3)) as a matrix Lie group (8.48–8.51); adjoint of se(3), ad(ξ^) = ξ^⋏ (8.52–8.56); BCH formula (8.70–8.71); Bernoulli numbers (8.77); Lie product formula (8.78); right and left Jacobians of SO(3) (8.81–8.82) and SE(3) (8.89–8.91), with Q_ℓ (8.91a) and Q_r (8.91b); inner products on so(3) and se(3) (8.107, 8.116); right and left distances (8.108, 8.117); infinitesimal volume element and unimodular group (8.110–8.112, 8.121–8.123); interpolation on SO(3) and SE(3) (8.128, 8.155); Faulhaber coefficients (8.147); homogeneous coordinates (p. 311) and the operators ⊙, ⊚ (8.163); directional derivative (8.167); left Lie derivative (p. 314, footnote 20); retraction (p. 315 margin, 8.205); Riemannian manifold and Riemannian gradient (8.206–8.209, 8.219–8.224); generalized velocity ϖ (8.257); generalized mass matrix 𝓜 (8.271); transport theorem (8.254, 8.274); state transition matrix (8.294); fundamental matrix (footnote 27); left, middle and right random variables (p. 339); Gaussian on SO(3) (8.312–8.314) and SE(3) (8.326); mean rotation and mean transformation (8.320, 8.327); dilation matrix D (8.383); invariance (8.406); right- and left-equivariance (8.413–8.414); moving-frame and stationary-frame invariant errors (8.415–8.416).

Algorithms: the chapter has no numbered algorithm tables; Table 8.1 is a property table. The procedures are: gradient descent on SO(3) with the exponential retraction (8.172–8.184, 8.210–8.216) and on SE(3) (8.226–8.230); Gauss-Newton on SO(3) (8.185–8.191) and on SE(3) (8.195–8.201); piecewise-constant integration on SO(3) (8.238–8.241) and SE(3) (8.263–8.267); Magnus integration (8.245, 8.269); projection onto SO(3) (8.246–8.251); compounding two uncertain poses at second and fourth order (8.341–8.352); sigmapoint compounding (pp. 348–349, 8.353–8.354); inverse and correlated compounding and differencing (8.360–8.368); pose fusion by Gauss-Newton (8.371–8.377); uncertainty through a camera at first order (8.394–8.395), second/fourth order (8.396–8.398) and by sigmapoints (8.399–8.401).

Equations you will implement: 8.10, 8.11, 8.14, 8.15, 8.17 (hat, vee, curly hat); 8.23, 8.28 with the axis from (8.26) (exp and log on SO(3)); 8.33–8.35 (exp and log on SE(3)); 8.37a, 8.37b, 8.81a–b, 8.82a–b (J_ℓ, J_r and inverses); 8.44 and 8.68 (direct series, checked against `scipy.linalg.expm`); 8.47 (Ad); 8.90–8.91a, 8.99, 8.100 (𝒥 and its inverse); 8.80 and 8.88 (approximate BCH, checked against exact log of the product); 8.113 (det J, checked numerically); 8.128 and 8.155 (interpolation); 8.163–8.165 (⊙ and ⊚); 8.170, 8.179, 8.192, 8.194 (Jacobians of a transformed point, checked by `scripts/fd_check.py`); 8.185–8.191 and 8.195–8.201 (Gauss-Newton); 8.238–8.241, 8.245, 8.263–8.267 (integration) and the projection of p. 328; 8.296 and 8.303 (perturbation solutions, checked by Monte Carlo); 8.312, 8.326 (sampling); 8.338 (rotated vector, checked by Monte Carlo); 8.343 and 8.352 at second order, 8.353–8.354 (sigmapoints); 8.357b (closed-form oracle for the K-step chain); 8.362, 8.366, 8.368 (inverse, correlated compounding, differencing); 8.371–8.377 (fusion); 8.389b, 8.391b, 8.392, 8.395, 8.402–8.404 (first-order stereo camera); 8.415–8.416 (invariant errors).

Equations you will derive by hand: 8.23 (series to Rodrigues, with 8.24); 8.27–8.28; 8.33–8.34; 8.42; 8.47 from 8.45 and 8.50; 8.83 and 8.85; 8.92; 8.109; 8.169–8.170 and 8.179 (the J that the left perturbation removes); 8.189–8.190; 8.235–8.236 (ω = Jφ̇); 8.279 (perturbation kinematics); 8.295–8.297; 8.324–8.325; 8.342–8.346 and Σ₂nd from 8.347; 8.360–8.362; 8.366 and 8.368 (book exercises 8.14, 8.15); 8.373–8.375; 8.412. Book exercises 8.3 and 8.17 are one-line consequences of 8.47 and 8.62.

## Dependencies inside the chapter

```
8.1.1 SO(3), SE(3) are groups, not vector spaces
 └── 8.1.2 Lie algebra: φ^, ξ^, ξ^⋏
      └── 8.1.3 exp / log  ──── J (8.36)  ──────────────────────────────┐
           ├── 8.1.4 Ad(T), ad(ξ^)                                     │
           │     └── 8.1.5 BCH → J_ℓ, J_r, 𝒥, Q  ("choose the left")  ←┘
           │           ├── 8.1.6 distance, volume (det J)
           │           ├── 8.1.7 interpolation ── perturbed (A, Faulhaber) ─→ ch. 11
           │           └── 8.1.9 perturbation exp(ε^)T_op, GN ←── 8.1.8 ⊙, ⊚
           │                 └── 8.1.10 = Riemannian gradient descent
           ├── 8.2.1–8.2.2 kinematics Ṫ = ϖ^T, integration by exp
           │     └── 8.2.3–8.2.4 perturbation kinematics, Φ = 𝒯(t)𝒯(s)⁻¹
           └── 8.3.1 Gaussian T = exp(ε^)T̄  (uses Ad, 8.1.6 volume)
                 ├── 8.3.2 rotated vector (4th order, Isserlis)
                 ├── 8.3.3 compounding ── 8.3.4 inverse ── 8.3.5 correlated
                 ├── 8.3.6 fusion (GN of 8.1.9 with G_k = 𝒥⁻¹)
                 └── 8.3.7 camera (⊙ from 8.1.8, sigmapoints)
                       └── 8.4 invariant errors ─→ ch. 9 (InEKF §9.2.4, SE₂(3) §9.4)
```

## What this chapter does not cover (and where it is)

- SE(2) and SE₂(3) worked out: only book exercises 8.20 and 8.21; SE₂(3) is used in Barfoot §9.4. Solà et al. (2018), cited on p. 284, is not in the library; the package's exercises do SE(2) for the tracked robot.
- Right perturbation and rotation-first ordering (GTSAM, Solà): the book names the right option (p. 340, footnotes 17, 19) but works only on the left. The package's cards give both and the Ad conversion between them.
- Robust projection onto SO(3) by SVD: Barfoot §9.1.3 (footnote 23, p. 329).
- Invariant EKF and the equivariant filter: Barfoot §9.2.4 and App. C.4; Barrau and Bonnabel (2017), Mahony and Trumpf (2021), not in the library.
- Large uncertainty and global densities on groups: Chirikjian and Kyatkin (2016), not in the library; this chapter is valid for small uncertainty only (p. 339, summary point 3).
- Quaternions, Euler angles and the C_vi convention: Barfoot ch. 7, lesson t2.6.
- IMU preintegration: lesson t2.11.
- Minimal polynomials and the proof of (8.285): Barfoot App. B.2.1 and B.3; the appendix pages are not in `books.yaml`.
- Riemannian Hessian and Newton's method: Absil et al. (2009), Boumal (2022), not in the library (p. 322).
- Rigid-body dynamics on SE(3) (8.270–8.271, 8.305–8.309): stated only; D'Eleuterio (1985).
