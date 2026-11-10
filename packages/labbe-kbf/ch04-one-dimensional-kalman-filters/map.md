---
book: labbe-kbf
chapter: 4
title: One Dimensional Kalman Filters
printed_pages: [131, 170]
pdf_pages: [131, 170]
lesson: t2.2
prereqs:
  - g-h filter: predict, residual, scale the residual (Labbe ch. 1, no lesson id)
  - t2.1 discrete Bayes filter: predict = convolution, update = likelihood × prior, normalize (Labbe ch. 2; Thrun ch. 2)
  - Gaussian sum and product formulas, proved in Labbe ch. 3 and used here without proof (p. 135, p. 137)
feeds:
  - t2.2 Thrun ch. 3 Gaussian filters (gold package): Table 3.1 is this chapter with scalars replaced by matrices
  - Labbe ch. 6 multivariate KF: same predict/update, x and P become a vector and a matrix
  - Labbe ch. 8 designing filters: choosing the process noise, which this chapter only shows going wrong
  - drone altitude (baro + accelerometer), wheel-odometry drift, IMU gyro-bias random walk: all scalar KFs in practice
status: draft
---

# Chapter map

One idea: a Bayes filter whose belief is a single Gaussian. Predict adds two Gaussians (means add, variances add);
update multiplies prior by likelihood (a variance-weighted mean, a variance smaller than either input). Everything
else in the chapter hangs off that pair. The Kalman gain section rewrites the product as `x̄ + K·(z − x̄)`, which is
the g-h filter with a gain that the variances compute instead of you. The worked examples (pp. 155–167) show what
the variances control: a too-small process variance makes the filter ignore the data; a bad initial mean washes out
at a rate set by the sensor variance. Fixed-gain filters fall out because, with constant variances, P and K converge.
There are no numbered equations: the chapter is a Jupyter notebook, so cite by page and section.

| Section | Pages | Verdict | Time | What to take |
| --- | --- | --- | --- | --- |
| Intro, Problem Description | 131–132 | skim | 3 min | Dog in a hallway, RFID position sensor, both errors modeled as Gaussians |
| Beliefs as Gaussians | 132–133 | skip | — | N(10, 1) plot and 500 draws; covered in Labbe ch. 3 |
| Tracking with Gaussian Probabilities | 133–135 | must | 10 min | Histogram → (μ, σ²); the ⊕ / ⊗ table on p. 134; the scheme only works if sum and product stay Gaussian |
| Predictions with Gaussians | 135–137 | must | 10 min | x̄ = x + f_x; μ̄ = μ + μ_fx, σ̄² = σ² + σ²_fx; predict always loses information |
| Updates with Gaussians | 137–138 | must | 15 min | Product ∝ Gaussian; posterior mean and variance (p. 138); `gaussian_multiply`, `update` |
| Understanding Gaussian Multiplication, Interactive Example | 139–142 | skim | 10 min | Product is narrower than both inputs and sits closer to the lower-variance one |
| First Kalman Filter, Code Walkthrough | 142–148 | must | 25 min | The predict/update loop; first step P̄ = 401 → P = 1.99 (pp. 144, 146); P converges to a constant independent of z |
| Exercise: Modify Variance Values | 148 | do | in package | Which of Labbe's Q = 40 (R_proc) or R = 40 (Q_meas) gives the smaller steady variance |
| KF Animation | 148–149 | skip | — | Animation does not render in the PDF |
| Kalman Gain | 149–151 | must | 20 min | μ = μ̄ + K(z − μ̄), K = σ̄²/(σ̄² + σ_z²), σ² = (1 − K)σ̄²; residual chart p. 150; the P, Q, R, z names |
| Full Description of the Algorithm | 152–153 | must | 10 min | The generic init / predict / update recipe; the two tables on p. 153 (Bayes form vs Kalman form) |
| Comparison with g-h and discrete Bayes | 153–155 | skim | 5 min | Uniform vs Gaussian vs discrete error models; tractability vs expressiveness |
| Introduction to Designing a Filter, Animation | 155–159 | must | 15 min | Thermometer: zero motion plus nonzero process variance, the "smug" filter; spec-sheet noise is not your sensor's noise |
| Example: Extreme Amounts of Noise | 159–160 | must | 5 min | σ_z = 300 m still gives a straight line, because the process model is right and R_proc is small |
| Example: Incorrect Process Variance | 160–161 | must | 10 min | R_proc too small + a maneuvering target = the filter ignores the data and diverges; it does not "notice" (p. 161) |
| Example: Bad Initial Estimate; Large Noise and Bad Initial Estimate | 161–164 | must | 10 min | Initial error washes out at a rate set by Q_meas; initialize from the first measurement |
| Exercise: Interactive Plots | 164–165 | do (in the session) | in package | Sliders for x0, Q_meas, velocity, R_proc; the session replaces the ipywidgets cell |
| Exercise: Nonlinear Systems | 165–167 | do, with care | in package | See lecture L9: the offset in the plot comes from the motion input u = 1, amplified by sensor_var = 30 against noise variance 1.44, plus lag; not from nonlinearity |
| Fixed Gain Filters | 167–168 | must | 5 min | Constant R_proc and Q_meas → P and K converge; hard-code K on a small MCU |
| FilterPy's Implementation | 168–169 | skim | 5 min | `kf.predict(x, P, u, Q)`, `kf.update(x, P, z, R)`; Labbe's Q, R ↔ our `R_proc`, `Q_meas` |
| Summary | 170 | skim | 2 min | One trick: pick a value between prediction and measurement |

Total reading at "must": about 2.5 hours. Half of each page is code and plots, so this chapter reads faster than the
10 min/page rule; the time goes into running the loop by hand. Coding (exercises T3) about 3 hours: the filter is five
lines, the work is in the oracle tests and the variance experiments.

## Notation (read this before the lecture)

Labbe uses the standard names: **Q = process noise variance, R = measurement noise variance** (p. 151, p. 168).
That is the opposite of Thrun. The package uses the project convention throughout:

| Labbe | Package | Meaning |
| --- | --- | --- |
| `Q`, `process_var`, σ²_fx | `R_proc` | variance added by predict per step |
| `R`, `sensor_var`, σ²_z | `Q_meas` | measurement variance |
| `P`, σ², `x.var` | `P` | belief variance (P̄ for the prior) |
| `dx`, `u`, `velocity*dt`, μ_fx | `u` | known displacement per step |

Every card and highlight that quotes Labbe's `Q` or `R` says which one it is.

## Inventory

Definitions: Gaussian belief N(μ, σ²) as a replacement for the histogram (p. 134), prior and posterior, process model
f_x as a Gaussian (p. 135), likelihood as a Gaussian centered on z (p. 137), residual y (p. 150–151), Kalman gain K
(p. 150), process variance and sensor variance (p. 145), smug filter (p. 156), fixed-gain filter (p. 167).

Algorithms: no numbered tables. The algorithm is the predict/update loop (p. 143, In [18]), its 5-line inline form
(p. 147), the gain form of `update`/`predict` (p. 151, In [22]), the generic recipe (p. 152) and the two
"Equation / Implementation / Kalman Form" tables (p. 153). Fixed-gain filter (p. 168).

Equations you will implement:
- Predict, p. 136 / p. 153: μ̄ = μ + μ_fx, P̄ = P + R_proc.
- Update, Bayes form, p. 138: μ = (σ̄²μ_z + σ_z²μ̄)/(σ̄² + σ_z²), σ² = σ̄²σ_z²/(σ̄² + σ_z²).
- Update, Kalman form, p. 153: y = z − x̄, K = P̄/(P̄ + Q_meas), x = x̄ + Ky, P = (1 − K)P̄.
- Fixed-gain update, p. 168: x = x̄ + K_∞(z − x̄).
- Steady-state P and K (not in the chapter; needed to check p. 148 and p. 168): fixed point of the two updates.

Equations you will derive by hand:
- Bayes-form update = Kalman-form update (p. 149–150: weights W1, W2 → K).
- The three variance forms σ̄²σ_z²/(σ̄² + σ_z²) = Kσ_z² = (1 − K)σ̄² (p. 150).
- The product of two Gaussian pdfs is proportional to a Gaussian (asserted p. 137, proved in ch. 3); the dropped
  constant is N(z; μ̄, P̄ + Q_meas), which the chapter never names.
- Steady state: P² + R_proc·P − R_proc·Q_meas = 0 for the posterior variance (gives the 1.0 of p. 146 and the 2.1623
  of p. 148).

Book outputs to reproduce as test oracles (from the printed cells): `predict(N(10, 0.2²), N(15, 0.7²)) = N(25, 0.53)`
(p. 137); `update(N(10, 0.2²), N(11, 0.1²)) = N(10.8, 0.008)` (p. 138); `N(10,1) × N(10,1) = N(10, 0.5)` (p. 139);
`kf.predict(10, 3, 1, 4) = (11, 7)` (p. 168); predict(10, 3, u=1, Q=4) then update(z=12, R=3.5²) = (11.364, 4.455)
(p. 169).

## Checked against a run

Steady-state posterior variance and gain for each filter in the chapter, from the fixed point above (run in this repo,
`.venv/bin/python`, 2026-11-10):

| Filter | Page | Labbe Q (= R_proc) | Labbe R (= Q_meas) | P∞ | K∞ |
| --- | --- | --- | --- | --- | --- |
| Dog, 10 steps | 143 | 1 | 2 | 1.00000 | 0.50000 |
| Dog, 25 steps | 147 | 2 | 4.5 | 2.16228 | 0.48051 |
| Thermometer | 156 | 0.0025 | 0.0169 | 0.00537 | 0.31770 |
| Extreme noise | 159 | 2 | 90000 | 423.26525 | 0.00470 |
| Bad process variance | 160 | 0.001 | 20 | 0.14092 | 0.00705 |
| Bad initial estimate | 161 | 2 | 25 | 6.14143 | 0.24566 |
| Large noise, bad init | 162 | 2 | 30000 | 243.95102 | 0.00813 |

The book's P∞ of 1.0 (p. 146), 2.1623 (p. 148) and 0.005 (p. 157) agree. The fixed gain K = 0.13232 on p. 168 matches
none of them, although p. 167 introduces it as "the dog tracking filter" reduced to a fixed gain; the code on p. 168
calls it "experimentally derived".

## Errata and traps found while reading

- p. 158: "quite close to the 16.4 used by the `volt()` function", but the code on p. 156 sets `actual_voltage = 16.3`.
- p. 161: "I'll reduce the sensor variance to 30", but the code sets `sensor_var = 5.**2` (25), and the text on
  p. 162 says σ² = 5².
- p. 135: the motion example switches from a 2 s epoch (x̄ = 40) to a 1 s epoch (x̄ = 25) in consecutive paragraphs.
- p. 140–142: plot legends print the literal text "g2.mean, ge.var" (typo in the cell's label string).
- p. 150: residual chart label reads "y = z − −x̄_t".
- p. 165: the Interactive Plots solution uses `sensor_noise` consistently as a variance; only the name and slider say
  noise. A naming trap, not a bug.
- p. 166–167 (nonlinear exercise): the filter's offset above the sine comes mostly from `process_model = N(1, 2)`,
  a displacement of +1 per step that the signal does not have. The text blames nonlinearity and a constant-velocity
  model. A sine in time is a time-varying signal, not a nonlinear system; the lecture separates the two (model
  mismatch in u vs lag from a too-small R_proc).

## Dependencies inside the chapter

```
Gaussian as belief (p. 134: ⊕ predict, ⊗ update)
 ├── Predict: sum of Gaussians (p. 135–137) ─────────────┐
 └── Update: product of Gaussians (p. 137–142)           │
        └── First Kalman Filter loop (p. 142–148) ◄──────┘
              ├── Kalman Gain: K, residual, P/Q/R names (p. 149–151)
              │     ├── Full Description of the Algorithm (p. 152–153) ── same recipe as g-h (ch. 1) and discrete Bayes (ch. 2)
              │     └── Fixed Gain Filters (p. 167–168) ◄── P converges (p. 146, 148, 157)
              │           └── FilterPy predict/update (p. 168–169)
              └── Designing a filter (p. 155–158): choosing R_proc and Q_meas
                    ├── Extreme noise (p. 159)        Q_meas huge, model right → still fine
                    ├── Incorrect process variance (p. 160)   R_proc too small → divergence
                    ├── Bad initial estimate (p. 161–164)     P0 and x0 → transient only
                    └── Nonlinear exercise (p. 165–167)       model mismatch
```

## What this chapter does not cover (and where it is)

- State vectors, covariance matrices, hidden velocity: Labbe ch. 5–6; Thrun ch. 3 Table 3.1, lesson t2.2 (gold package).
- Deriving the process noise from a continuous model (white-noise acceleration, Δt scaling): Labbe ch. 7; Barfoot ch. 3.
- Consistency checks (NEES, NIS) and the innovation variance S = P̄ + Q_meas: not named here; Labbe ch. 8; Bar-Shalom
  ch. 5. The package exercises add NIS because the p. 160 divergence is exactly what NIS detects.
- The normalization constant of the Gaussian product (the measurement likelihood used for gating and model
  selection): Labbe ch. 3 proof; Thrun ch. 3, lesson t2.2.
- Nonlinear models: Labbe ch. 9 (nonlinear filtering), ch. 10 (UKF), ch. 11 (EKF); Thrun ch. 3.3–3.4, lesson t2.2.
- Optimality (minimum variance, orthogonal projection): named on p. 151 and deferred; Labbe ch. 7 (Kalman Filter Math) for the math the book gives.
- Angles: no wrapping in this chapter; the scalar state is a position or a voltage. `wrap()` is not needed until a
  heading appears.
