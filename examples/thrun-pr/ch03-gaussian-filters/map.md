---
book: thrun-pr
chapter: 3
title: Gaussian Filters
printed_pages: [39, 84]
pdf_pages: [60, 105]
lesson: t2.2
prereqs:
  - t2.1 Bayes filter (Thrun ch. 2, eq. 2.38 and 2.41 are reused verbatim)
  - t4.1 Gaussian conditioning and marginalization (Murphy PML1 ch. 3)
  - linear algebra: Cholesky, Schur complement, matrix inversion lemma
feeds:
  - t2.4 motion and sensor models (ch. 5-6 give the g and h you linearize here)
  - t2.7 EKF-SLAM (ch. 10 is Table 3.3 with a growing state)
  - t2.11 IMU preintegration (prediction with the constant term of exercise 5)
  - t7.4 moving-horizon estimation (same quadratic cost, batch instead of recursive)
  - FORGE and GTSAM: information form of 3.5 is what a factor graph stores
status: pilot
---

# Chapter map

One idea, four filters. The idea: if the belief is a Gaussian and every map is linear, the belief stays a Gaussian and you only ever need to move a mean and a covariance. The four filters are what you do when a map is not linear (EKF, UKF) or when you want the other parameterization (IF, EIF).

| Section | Pages | Verdict | Time | What to take |
| --- | --- | --- | --- | --- |
| 3.1 Introduction | 39–40 | must | 10 min | Gaussian belief; moments vs canonical parameterization; unimodal only |
| 3.2.1 Linear Gaussian systems | 40–42 | must | 15 min | Three assumptions (3.2, 3.5, 3.7); shapes of A, B, C, R, Q |
| 3.2.2 KF algorithm | 43 | must | 20 min | Table 3.1, innovation, cost O(k^2.4 + n^2) |
| 3.2.3 Illustration | 44–45 | must | 5 min | Predict widens, update narrows |
| 3.2.4 KF derivation | 45–54 | skim, return later | 45 min | Completing the square; inversion lemma (Table 3.2); why line 4 inverts k×k not n×n |
| 3.3.1–3.3.2 Why linearize, Taylor | 54–58 | must | 20 min | Closure breaks under nonlinear g; tangent at the mean; Jacobians G, H |
| 3.3.3 EKF algorithm | 59 | must | 15 min | Table 3.3: g and h in the mean lines, G and H in the covariance lines |
| 3.3.4 EKF derivation | 59–61 | skip | — | Same as 3.2.4 with G, H substituted |
| 3.3.5 Practical considerations | 61–64 | must | 15 min | Two error sources: uncertainty and local nonlinearity; MHEKF |
| 3.4.1 Unscented transform | 65–67 | must | 20 min | Sigma points (3.66), weights (3.67), transform (3.69) |
| 3.4.2 UKF algorithm | 67–71 | must | 20 min | Table 3.4: 14 lines, cross-covariance replaces Σ̄Hᵀ |
| 3.5.1–3.5.2 Canonical form, IF | 71–74 | must | 20 min | Ω = Σ⁻¹, ξ = Σ⁻¹μ; Table 3.5; duality of cost |
| 3.5.3–3.5.5 IF and EIF derivation | 74–77 | skim | 10 min | Substitution only; Table 3.6 |
| 3.5.6 Practical considerations | 77–79 | must | 10 min | Ω = 0 for total ignorance; information adds; sparse Ω ≠ sparse Σ |
| 3.6 Summary | 79–81 | must | 5 min | Compare with your own |
| 3.8 Exercises | 81–84 | do 1, 2, 4 | in package | 3 needs transforms; 5 and 6 are short |

Total reading at "must": about 3.5 hours. Coding (exercises T3) about 4 hours.

## Inventory

Definitions: Gaussian (3.1), moments and canonical parameterization, linear Gaussian system, Kalman gain, innovation, Jacobian, sigma point, unscented transform, information matrix and vector, Mahalanobis distance.

Algorithms: Table 3.1 KF, Table 3.3 EKF, Table 3.4 UKF, Table 3.5 IF, Table 3.6 EIF.

Equations you will implement: 3.2, 3.5 (models); Table 3.1 lines 2–6; 3.51, 3.53 (Jacobians); 3.66, 3.67, 3.69 (sigma points and transform); Table 3.4 lines 2–13; 3.70–3.73 (conversions); Table 3.5 lines 2–5.

Equations you will derive by hand: 3.31 (prediction mean), 3.38 and 3.47 (two forms of the covariance update), 3.45 (gain), Table 3.2 (inversion lemma).

## Dependencies inside the chapter

```
3.1 Gaussian, parameterizations
 ├── 3.2 KF  ──────────────┬── 3.3 EKF (replace A,B,C by g,G,h,H)
 │     └── 3.2.4 derivation │     └── 3.3.5 when EKF fails ──┐
 │           └── Table 3.2 inversion lemma                   ├── 3.4 UKF (no Jacobians)
 └── 3.5 IF  (Ω = Σ⁻¹, dual of 3.2)                          │
       └── 3.5.4 EIF (dual of 3.3)  ←────────────────────────┘
```

## What this chapter does not cover (and where it is)

- Nonlinear noise inside g (velocity motion model): augmented UKF, ch. 7.
- Angles and rotations: no wrapping in this chapter. Lie-group treatment is Barfoot ch. 7–8, lesson t2.6.
- Consistency testing (NEES, NIS): Bar-Shalom; built into the package exercises because you cannot tune a filter without it.
- Smoothing and batch: Barfoot ch. 3–4, lesson t2.11.
- Square-root and UD filters: Maybeck; mentioned in card C1 for when n is large.
