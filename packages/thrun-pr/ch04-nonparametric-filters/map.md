---
book: thrun-pr
chapter: 4
title: Nonparametric Filters
printed_pages: [85, 116]
pdf_pages: [106, 137]
lesson: t2.3
prereqs:
  - t2.1 Bayes filter (Thrun ch. 2; Table 2.1 is what Table 4.1 discretizes, 2.4.2 door example is the binary filter's first appearance)
  - t2.2 Gaussian filters (Thrun ch. 3; exercises 4.6.1–4.6.5 reuse the systems of ch. 3 exercises 1, 2, 4, and you compare against your KF/EKF)
  - probability: sampling from a CDF, Monte Carlo estimates and their 1/√M error, Borel sets only by name
  - numerics: cumulative sums, log-sum-exp, binary search (searchsorted)
feeds:
  - t2.3 grid and Monte Carlo localization (Thrun ch. 8: Table 4.1 becomes grid localization, Table 4.3 becomes MCL, deprivation gets its real fixes)
  - t2.4 motion and sensor models (Thrun ch. 5–6: sample_motion_model is line 4 of Table 4.3, the beam model is line 5)
  - t2.5 occupancy grid mapping (Thrun ch. 9: Table 4.2 run once per cell with an inverse sensor model)
  - t2.9 FastSLAM (Thrun ch. 13: particles carry a map; the path-space view of 4.3.3 is why it works)
  - RoboCup map: MCL on a point-symmetric field is the textbook bimodal posterior; resampling choices decide whether the wrong mode survives
  - tracked robot and quadruped: occupancy grids built with Table 4.2; skid-steer slip is a heavy-tailed motion model the EKF cannot carry and a PF can
  - drone: when the PF stops being affordable (state dimension, Fig. 4.6 sample variance) and you go back to ch. 3
status: draft
---

# Chapter map

One idea, two discretizations. The idea: drop the fixed functional form and represent the belief by a finite set of numbers, then run the Bayes filter of ch. 2 on those numbers. The histogram filter (4.1) fixes the numbers in space (bins) and stores a probability per bin; the binary Bayes filter (4.2) is its two-bin special case for a static state, written in log odds. The particle filter (4.3) lets the numbers move (samples) and stores a weight per sample; importance sampling (4.3.2) is why weighting by the measurement likelihood and resampling is correct, and 4.3.4 is the list of ways a finite particle set lies to you: sampling variance, loss of diversity through resampling, bias at small M, deprivation.

| Section | Pages | Verdict | Time | What to take |
| --- | --- | --- | --- | --- |
| 4 Introduction | 85–86 | must | 15 min | Nonparametric = finite number of values; multimodal beliefs; adaptive vs resource-adaptive |
| 4.1.1 Discrete Bayes filter | 86–87 | must | 10 min | Table 4.1: prediction is a matrix–vector product, update is element-wise product then normalize; HMM forward pass |
| 4.1.2 Continuous state | 87–89 | must | 20 min | Partition (4.1), piecewise constant density (4.2), representative state (4.3), approximations (4.4), (4.5); Fig. 4.1 |
| 4.1.3 Derivation of the histogram approximation | 89–92 | skim, derive (4.7) | 20 min | (4.6) is exact under (4.2); the only approximation is p(z∣x) ≈ p(z∣x̂) inside a bin; line 3's p̄ₖ are unnormalized, line 4's η normalizes (p. 92) |
| 4.1.4 Decomposition techniques | 92–93 | skim | 10 min | Static vs dynamic (density trees, Fig. 4.2); selective updating; topological vs metric |
| 4.2 Binary Bayes filter, static state | 94–96 | must | 25 min | Table 4.2; log odds (4.13), recovery (4.14), derivation (4.15)–(4.20); inverse measurement model; the prior is subtracted every update |
| 4.3.1 Particle filter, basic algorithm | 96–100 | must | 35 min | Table 4.3: sample from motion model, weight by likelihood, resample; (4.23) holds only as M → ∞; (4.24) the no-resampling variant |
| 4.3.2 Importance sampling | 100–102 | must | 25 min | (4.25) w = f/g, support condition f > 0 ⇒ g > 0; (4.27), (4.28) self-normalized estimate, O(1/√M); proposal (4.29); Fig. 4.4 |
| 4.3.3 Derivation of the PF | 103–104 | must | 15 min | Path-space posterior (4.31), (4.32); target/proposal (4.34) = η p(z∣x); the text says "Table 4.4" on p. 104, it means Table 4.3 |
| 4.3.4 Density extraction | 104–106 | skim | 10 min | Gaussian, k-means, histogram, kernel density (Fig. 4.5); pick by what the controller needs |
| 4.3.4 Sampling variance | 105–108 | must | 15 min | Fig. 4.6: 25 vs 250 samples; the estimate is itself a random variable |
| 4.3.4 Resampling | 108–111 | must | 30 min | Diversity loss for a static state; (4.36) resample less often, decide by weight variance; Table 4.4 low-variance sampler, (4.37), Fig. 4.7, O(M); stratified sampling |
| 4.3.4 Sampling bias | 112 | must | 10 min | M = 1 ignores every measurement (4.38); normalization removes one degree of freedom |
| 4.3.4 Particle deprivation | 112–113 | must | 10 min | No particle near the truth; random particle injection as last resort; real fixes in ch. 8 |
| 4.4 Summary | 113–114 | must | 5 min | Compare with your own |
| 4.5 Bibliographical remarks | 114–115 | skip | — | Doucet et al. (2001) is the follow-up text if you want one |
| 4.6 Exercises | 115–116 | do 2, 3, 5; 1 as warm-up | in package | 2 and 5 are the banana (θ unknown) system of ch. 3 ex. 4, histogram vs PF vs your EKF; 3 is the M = 2 bias question; 4 repeats 1 with particles |

Total reading at "must": about 3.6 hours (215 min over about 22 pages), plus 40 min of skim. Coding (exercises T3) about 4 hours.

## Inventory

Definitions: nonparametric filter, adaptive and resource-adaptive algorithm, discrete Bayes filter, histogram filter, hidden Markov model, partition of dom(X) into bins (4.1), bin volume |x_k,t|, representative state x̂_k,t (4.3), static and dynamic decomposition, density tree, selective updating, topological and metric representation, binary Bayes filter, odds (4.12), log odds (4.13), inverse measurement model, particle and particle set (4.22), importance factor, resampling, target distribution, proposal distribution, density extraction, kernel density estimation, sampling variance, variance reduction, low-variance sampling, stratified sampling, sampling bias, particle deprivation.

Algorithms: Table 4.1 Discrete_Bayes_filter, Table 4.2 binary_Bayes_filter (log odds), Table 4.3 Particle_filter, Table 4.4 Low_variance_sampler.

Figures worth redrawing in the lecture: 4.1 (histogram through a nonlinear g), 4.3 (particles through the same g), 4.4 (target, proposal, weighted samples), 4.6 (sample variance, 25 vs 250), 4.7 (low-variance comb).

Equations you will implement: Table 4.1 lines 3–4 with (4.2), (4.4), (4.5) for a continuous state; (4.13), (4.14), (4.21) and Table 4.2 line 2; Table 4.3 lines 4–10; (4.25)–(4.28) as a self-normalized importance-sampling estimator; (4.36) with a weight-variance trigger for when to resample; Table 4.4 and (4.37); random particle injection (p. 113) as an option, off by default.

Equations you will derive by hand: (4.7) from (4.6) (where the histogram approximation enters); (4.19)–(4.20) (log-odds update, why the prior is subtracted); (4.32)–(4.34) (importance weight = measurement likelihood); (4.38) and its M = 2 extension (book exercise 3).

Traps to carry into cards and T4 (decided now, so later stages do not rediscover them):
- Table 4.4 assumes normalized weights (r ∈ [0, M⁻¹], U up to 1); Table 4.3 never normalizes. Unnormalized weights into Table 4.4 is a planted-bug candidate.
- (4.14) as written overflows for large |l|; robust code uses a logistic (expit). Grid mappers clamp l in practice (common practice, e.g. OctoMap; not in the book: Table 9.1 has no clamp).
- Likelihood products underflow; weights in log space and log-sum-exp normalize.
- Table 4.1 line 3 is O(K²) dense; a shift-invariant motion model makes it a convolution.

## Dependencies inside the chapter

```
Bayes filter (ch. 2, Table 2.1)
 ├── 4.1 histogram: fixed bins
 │     ├── 4.1.1 Table 4.1 discrete Bayes filter (finite state, HMM forward pass)
 │     ├── 4.1.2 continuous state: (4.1)-(4.5)
 │     │     └── 4.1.3 derivation (4.6)-(4.10)
 │     ├── 4.1.4 decompositions: static / dynamic / selective ──┐
 │     └── 4.2 binary static state, log odds, Table 4.2         │ density tree reused
 │            (two-bin case of 4.1; feeds ch. 9)                │ for density extraction
 └── 4.3 particles: moving samples                              │
       ├── 4.3.1 Table 4.3 ──── 4.3.2 importance sampling (4.25)-(4.29)
       │                          └── 4.3.3 derivation (4.30)-(4.35)
       └── 4.3.4 practical
             ├── density extraction (Fig. 4.5) ←────────────────┘
             ├── sampling variance (Fig. 4.6)
             ├── resampling: (4.36), Table 4.4, (4.37)
             ├── sampling bias (4.38)
             └── particle deprivation → ch. 8 fixes
```

## What this chapter does not cover (and where it is)

- Motion and measurement models to sample from and weight with: Thrun ch. 5–6, lesson t2.4.
- Grid localization and Monte Carlo localization on real maps, including augmented MCL and KLD-sampling (adaptive M): Thrun ch. 8, lesson t2.3.
- Occupancy grid mapping with inverse sensor models: Thrun ch. 9, lesson t2.5. Log-odds clamping is common practice (OctoMap), not in the book.
- Rao-Blackwellized particle filters: Thrun ch. 13 (FastSLAM), lesson t2.9.
- Better proposals than the motion model (optimal proposal, auxiliary PF, using z_t in line 4): Doucet et al. (2001); FastSLAM 2.0 in Thrun ch. 13.
- Effective sample size N_eff = 1/Σw² as the resampling trigger: the book only says "variance of the weights" (p. 109); for normalized weights N_eff is a monotone function of that variance, so the package uses N_eff and shows the equivalence.
- Convergence proofs and the M → ∞ conditions: Doucet et al. (2001); not needed for this package.
- Particle smoothing (keeping the path in 4.30 on purpose): Barfoot ch. 4, lesson t2.11.
- Angles: θ in book exercise 2 is not wrapped in the chapter; the package wraps it with `wrap()` from `models.py`.
