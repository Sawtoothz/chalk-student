---
lesson: t2.2
title: Equation-to-code cards — one-dimensional Kalman filters
source: Labbe, Kalman and Bayesian Filters in Python, ch. 4 (pp. 131–170)
oracle: the book's printed cell outputs (pp. 137, 138, 139, 168, 169), the Bayes form against the gain form, the fixed point of the variance recursion, Monte Carlo; FilterPy is not installed and not used
numbers: every number below is printed by figures/card_numbers.py (run with .venv/bin/python, 2026-11-10)
status: draft
---

# Equation-to-code cards

Four cards, in the order you implement them: predict (C1), update in the book's Bayes form (C2), update in the Kalman
gain form plus the loop (C3), steady state and the fixed-gain filter (C4). Each card gives the equation with every
symbol's units, a naive version you can read against the book's cell, a robust version with the tricks named, C++,
cost, and what breaks first.

The chapter has no numbered equations; cards cite the page and the notebook cell (`In [22]`).

**Names.** Labbe's `Q` is the process variance and his `R` the measurement variance (p. 151): the opposite of Thrun.
This package uses the repo convention everywhere: **`R_proc` = Labbe's `Q`** (variance added per predict),
**`Q_meas` = Labbe's `R`** (sensor variance). When a card quotes a book line that says `Q` or `R`, the comment says
which one it is. `P` is the belief variance, `P_bar` the prior's. No angles in this chapter, so no `wrap()`.

All four cards are scalar. They are also Thrun's Table 3.1 with n = k = 1, A = B = C = 1; the gold package's C1 is
the matrix version of C1 + C3 here, line for line.

---

## C1. Predict: sum of two Gaussians (pp. 135–137, table p. 153)

```latex
\bar x = x + f_x,\qquad \bar\mu = \mu + \mu_{f_x},\qquad \bar\sigma^2 = \sigma^2 + \sigma^2_{f_x}
\qquad\text{Kalman form: } \bar x = x + u,\quad \bar P = P + R_{proc}
```

**Shapes.** All scalars. Dog example units: x, x̄ [m]; P, P̄ [m²]; u = μ_fx = v·Δt [m/step]; R_proc = σ²_fx
[m²/step]. Assumption the sum rule needs: x and f_x independent.

**Naive (p. 136, In [9]).**

```python
gaussian = namedtuple('Gaussian', ['mean', 'var'])

def predict(pos, movement):
    return gaussian(pos.mean + movement.mean,      # mu_bar = mu + mu_fx
                    pos.var + movement.var)        # sigma_bar^2 = sigma^2 + sigma_fx^2
```

Kalman-form version, p. 151, In [22]:

```python
def predict(posterior, movement):
    x, P = posterior
    dx, Q = movement        # Labbe's Q = our R_proc
    x = x + dx
    P = P + Q
    return gaussian(x, P)
```

**Robust.**

```python
def predict(x, P, u, R_proc, dt=1.0):
    """x_bar = x + u*dt, P_bar = P + R_proc*dt. u in [units/s], R_proc in [units^2/s] when dt is given."""
    assert P >= 0.0 and R_proc >= 0.0, "variances are non-negative"
    return x + u * dt, P + R_proc * dt
```

Tricks:

1. **Separate floats, named for what they are.** `predict(x, P, u, R_proc)` is FilterPy's signature
   `kf.predict(x, P, u, Q)` (p. 168) with its `Q` renamed. A tuple called `movement` with a field called `var` hides
   which variance is which, and that is the bug that swaps R_proc and Q_meas.
2. **Assert the variances are non-negative.** A sign typo in R_proc gives a P̄ that shrinks on predict; nothing
   crashes, and C3 then computes K outside [0, 1].
3. **Scale R_proc with Δt when the step is irregular.** For a random walk the per-step increments are independent,
   so by the sum rule above two half-steps add two half-variances: variance grows linearly in elapsed time. The
   book's steps are all one epoch; a robot's sensor callbacks are not. Deriving R_proc from a continuous model is
   Labbe ch. 7 (and Barfoot ch. 3).
4. **Never set R_proc = 0 because u is "exact".** With R_proc = 0 the fixed point of C4 is P = 0, K = 0: the filter
   stops listening (the smug thermometer, pp. 156–157; lecture L7).
5. **Predict without update is legal.** A dropped measurement means calling `predict` again; P̄ grows by R_proc per
   missed step, and the next update weights the measurement more because of it.

**Oracles (book outputs).** `predict(N(10, 0.2²), N(15, 0.7²))` = N(25.000, 0.530) (p. 137);
`kf.predict(x=10, P=3, u=1, Q=4)` = (11.0, 7.0) (p. 168). Both reproduced by `figures/card_numbers.py`
(0.53 prints as 0.5299999999999999: compare with a tolerance, not `==`).

**C++.**

```cpp
struct Belief1 { double x, P; };   // mean [m], variance [m^2]

inline Belief1 predict(Belief1 b, double u, double R_proc, double dt = 1.0) {
  return {b.x + u * dt, b.P + R_proc * dt};
}
```

No Eigen for a scalar; the gold card's `template <int N, int K>` with N = 1 compiles to the same two adds.

**Cost.** Two additions. In n-D the same line is AΣAᵀ + R_proc, O(n³), and it becomes the expensive half of the
filter (gold package, C1).

**What breaks first.** R_proc too small for the real motion (p. 160: the filter ignores the data), then a biased u
(pp. 165–167: a constant offset in the estimate, see C4), then irregular Δt with a per-step R_proc.

---

## C2. Update, Bayes form: product of two Gaussians (pp. 137–138)

```latex
\mathcal N(\mu,\sigma^2) = \|\mathcal N(\bar\mu,\bar\sigma^2)\cdot\mathcal N(\mu_z,\sigma_z^2)\|
= \mathcal N\!\left(\frac{\bar\sigma^2\mu_z+\sigma_z^2\bar\mu}{\bar\sigma^2+\sigma_z^2},\;
\frac{\bar\sigma^2\sigma_z^2}{\bar\sigma^2+\sigma_z^2}\right)
```

**Shapes.** Scalars. x̄ [m], P̄ = σ̄² [m²], z = μ_z [m], Q_meas = σ_z² [m²], posterior x [m], P [m²].

**Naive (p. 138, In [11]).**

```python
def gaussian_multiply(g1, g2):
    mean = (g1.var * g2.mean + g2.var * g1.mean) / (g1.var + g2.var)
    variance = (g1.var * g2.var) / (g1.var + g2.var)
    return gaussian(mean, variance)

def update(prior, likelihood):
    posterior = gaussian_multiply(likelihood, prior)   # argument order swapped; harmless, the product commutes
    return posterior
```

**Robust: precision (information) form.**

```python
def update_bayes(x_bar, P_bar, z, Q_meas):
    """Product of N(x_bar, P_bar) and N(z, Q_meas), normalized. P_bar may be inf (no prior)."""
    assert Q_meas > 0.0 and P_bar >= 0.0
    if P_bar == 0.0:                          # a certain prior: the measurement changes nothing
        S = Q_meas
        return x_bar, 0.0, -0.5 * (np.log(2 * np.pi * S) + (z - x_bar) ** 2 / S)
    lam = 1.0 / P_bar + 1.0 / Q_meas          # precisions add (1/inf == 0.0 in IEEE)
    P = 1.0 / lam
    x = P * (x_bar / P_bar + z / Q_meas) if np.isfinite(P_bar) else z
    S = P_bar + Q_meas
    log_c = -0.5 * (np.log(2 * np.pi * S) + (z - x_bar) ** 2 / S) if np.isfinite(S) else -np.inf
    return x, P, log_c
```

Tricks:

1. **Precisions add.** 1/P = 1/P̄ + 1/Q_meas is the p. 138 variance written so the "narrower than both inputs"
   claim of pp. 139–142 is visible: P < min(P̄, Q_meas) whenever both are finite and positive.
2. **Total ignorance is P̄ = ∞, not P̄ = 10⁶.** The precision form gives x = z, P = Q_meas exactly. A large finite
   P̄ gives almost the same answer in float64 and a wrong one in float32 (C3, trick 2).
3. **Keep the constant the book normalizes away.** The product is N(z; x̄, P̄ + Q_meas) times the posterior
   (lecture L3). Its log, `log_c`, is the measurement log-likelihood: sum it over a run to compare two values of
   R_proc, or threshold it to gate (C3, trick 4).
4. **The variance never sees the data.** P depends on P̄ and Q_meas only ("the variances are completely unaffected
   by the values of the mean", p. 138). The whole P sequence can be computed before the robot moves; C4 is that
   observation taken to the limit.

**Oracles (book outputs).** `update(N(10, 0.2²), N(11, 0.1²))` = N(10.800, 0.008) (p. 138); N(10, 1) × N(10, 1)
= N(10, 0.5) (p. 139). Both reproduced by `figures/card_numbers.py`.

**C++.**

```cpp
inline Belief1 update_bayes(Belief1 prior, double z, double Q_meas) {
  const double P = 1.0 / (1.0 / prior.P + 1.0 / Q_meas);   // prior.P == INFINITY is fine
  const double x = std::isfinite(prior.P) ? P * (prior.x / prior.P + z / Q_meas) : z;
  return {x, P};
}
```

**Cost.** Two divisions in the naive form, three in the precision form. Irrelevant in 1-D; in n-D the precision
form is the information filter (gold package, C5), where update is an addition and predict needs two inversions.

**What breaks first.** P̄ = 0 and Q_meas = 0 together (0/0 in the naive form), then a P̄ "large" enough to lose the
measurement's digits in float32, then a mismatch between σ_z (what the sensor's datasheet quotes) and σ_z² (what
the formula wants): the book's Interactive Plots solution names a variance `sensor_noise` (p. 165, `map.md` errata), which invites the slip.

---

## C3. Update, Kalman gain form, and the filter loop (pp. 147, 149–153, 168–169)

```latex
y = z - \bar x,\qquad K = \frac{\bar P}{\bar P + Q_{meas}},\qquad x = \bar x + K y,\qquad P = (1-K)\bar P
```
```latex
\sigma^2 = \frac{\bar\sigma^2\sigma_z^2}{\bar\sigma^2+\sigma_z^2} = K\sigma_z^2 = (1-K)\bar\sigma^2 \qquad\text{(p. 150)}
```

**Shapes.** Scalars. y [m] residual; S = P̄ + Q_meas [m²], the residual's variance (not named in the chapter);
K dimensionless, in [0, 1] when both variances are non-negative.

**Naive (p. 151, In [22]).**

```python
def update(prior, measurement):
    x, P = prior            # mean and variance of prior
    z, R = measurement      # Labbe's R = our Q_meas
    y = z - x               # residual
    K = P / (P + R)         # Kalman gain
    x = x + K*y             # posterior
    P = (1 - K) * P         # posterior variance
    return gaussian(x, P)
```

The loop, p. 147, with Labbe's `process_var` = R_proc and `sensor_var` = Q_meas:

```python
for z in zs:
    # predict
    dx = velocity*dt
    pos = pos + dx
    var = var + process_var
    # update
    pos = (var*z + sensor_var*pos) / (var + sensor_var)
    var = (var * sensor_var) / (var + sensor_var)
```

The loop's update lines are the Bayes form (C2); `update` above is the gain form. Over 100 000 random cases
(P̄, Q_meas from 10⁻³ to 10³) they agree to 3.2 × 10⁻¹⁴ in the mean (relative) and 7.7 × 10⁻¹¹ in the variance
(relative): the same filter. The variance gap is the cancellation of trick 2.

**Robust.**

```python
CHI2_1DOF_99 = 6.635   # scipy.stats.chi2.ppf(0.99, 1)

def update(x_bar, P_bar, z, Q_meas, gate=None):
    """Returns x, P, y, S, accepted. gate: reject if y^2/S exceeds it (e.g. CHI2_1DOF_99)."""
    y = z - x_bar
    S = P_bar + Q_meas
    if not S > 0.0:
        raise ValueError(f"innovation variance S = {S} must be positive")
    if gate is not None and y * y > gate * S:
        return x_bar, P_bar, y, S, False          # outlier: keep the prior
    K = P_bar / S
    x = x_bar + K * y
    P = P_bar * Q_meas / S                        # = (1 - K) P_bar without computing 1 - K
    return x, P, y, S, True

def run_filter(zs, x0, P0, u, R_proc, Q_meas, gate=None):
    out = np.empty((len(zs), 6))                  # x, P, x_bar, P_bar, y, S per step
    x, P = x0, P0
    for k, z in enumerate(zs):
        x_bar, P_bar = predict(x, P, u, R_proc)
        x, P, y, S, _ = update(x_bar, P_bar, z, Q_meas, gate)
        out[k] = x, P, x_bar, P_bar, y, S
    return out
```

Tricks:

1. **Return y and S.** NIS = y²/S has mean 1 for a consistent scalar filter. It is the only thing that shows the
   p. 160 failure from inside the filter: over steps 50–99 of lecture L8, mean NIS is 342.1 with R_proc = 0.001 and
   1.82 with R_proc = 10, while P looks equally confident in both. Store y and S per step; plot them first when a
   filter misbehaves.
2. **P = P̄·Q_meas/S, not (1 − K)P̄.** When P̄ ≫ Q_meas, K rounds toward 1 and 1 − K loses its digits. In float32 the
   relative error of (1 − K)P̄ is 2.7 × 10⁻⁴ at P̄/Q_meas = 10⁴, 1.3 × 10⁻² at 10⁶ and 100% at 10⁸ (P = 0 exactly),
   while P̄·Q_meas/S stays below 3 × 10⁻⁸ throughout. 10⁸ is a 1 km-wide initial guess (P₀ = 10⁶ m²) meeting an
   RTK fix with Q_meas = 0.01 m²: the float32 filter's P becomes 0 and it never moves again. Float64 does the same
   at P̄/Q_meas = 10¹⁸.
3. **Joseph form when K is not the optimal gain.** The scalar Joseph form P = (1 − K)²P̄ + K²Q_meas is the true
   variance after an update with *any* gain; (1 − K)P̄ and P̄·Q_meas/S are only right for K = P̄/S. Use it for the
   fixed-gain filter (C4) and whenever someone hand-tunes K. Matrix version: gold package C1, trick 2.
4. **Gate on y²/S.** Under the filter's own model y ~ N(0, S), so y²/S ~ χ²(1). Reject when it exceeds 6.635 (99%)
   or 3.841 (95%), skip the update, keep predicting. A UWB anchor's multipath jump of 3 m against S = 0.1 m² gives
   y²/S = 90: rejected. Gating with a too-small R_proc rejects good data, so tune R_proc (trick 1) before gating.
5. **Initialize from the first measurement.** x₀ = z₀, P₀ = Q_meas is the P̄ → ∞ limit of this update (K → 1,
   P → Q_meas). It removes the transient that pp. 161–164 spend two plots on, and the guesswork in P₀ = 400 m²
   (p. 145).
6. **Two sensors on one state: update twice.** Products commute, so the order does not matter in exact arithmetic.
   This is the scalar case of sequential updates (gold package C1, trick 5): baro then GPS altitude on a drone,
   each with its own Q_meas.
7. **Store prior and posterior separately.** The p. 147 plot bands the line of posteriors with the prior's variance
   (lecture L4, plot trap). `run_filter` keeps both; band x with P, x̄ with P̄.

**Oracles.** Book: predict (10, 3) with u = 1, R_proc = 2² then update with z = 12, Q_meas = 3.5² gives
(11.364, 4.455) (p. 169); here y = 1.000 m, S = 19.250 m², K = 0.36364. Dog, x₀ = N(0, 400), R_proc = 1, Q_meas = 2
(pp. 143–145): first prior P̄ = 401.000 m², first posterior P = 1.9901 m² (book prints 1.990). Gain form = Bayes form
on random inputs (above). FilterPy's `kf.update(x, P, z, R)` takes our Q_meas as `R` (p. 168).

**C++.**

```cpp
struct Innov { double y, S; bool accepted; };

inline Innov update(Belief1& b, double z, double Q_meas, double gate = INFINITY) {
  const double y = z - b.x;
  const double S = b.P + Q_meas;
  if (!(S > 0.0)) throw std::domain_error("S <= 0");
  if (y * y > gate * S) return {y, S, false};
  const double K = b.P / S;
  b.x += K * y;
  b.P = b.P * Q_meas / S;          // not (1 - K) * b.P
  return {y, S, true};
}
```

On a microcontroller keep `double` for P if the FPU has it; if not, trick 2 is what makes `float` safe.

**Cost.** One division, three multiplies, three adds per update; the gate adds two multiplies and a compare. In n-D
the division becomes the solve with S (k×k) and the products O(n²k) dominate (gold C1).

**What breaks first.** R_proc too small (P converges to a value the data contradicts; NIS ≫ 1, trick 1), then
Q_meas from a datasheet instead of measured on the robot (p. 158), then outliers without a gate, then float32
cancellation with a huge P₀.

---

## C4. Steady state and the fixed-gain filter (pp. 146, 148, 157, 167–168)

The chapter states that P converges (pp. 146, 148, 157) and hard-codes a gain (p. 168); it does not give the limit.
Require one predict + update to return the same P:

```latex
P_\infty = \frac{(P_\infty+R_{proc})\,Q_{meas}}{P_\infty+R_{proc}+Q_{meas}}
\;\Longrightarrow\; P_\infty^2 + R_{proc}P_\infty - R_{proc}Q_{meas} = 0,
\qquad P_\infty = \tfrac12\left(-R_{proc} + \sqrt{R_{proc}^2 + 4R_{proc}Q_{meas}}\right),
\qquad K_\infty = \frac{P_\infty}{Q_{meas}} = \frac{\bar P_\infty}{\bar P_\infty + Q_{meas}}
```

K∞ = P∞/Q_meas is p. 150's σ² = Kσ_z² read backwards. The fixed-gain update (p. 168):
`x = x̄ + K∞(z − x̄)`.

**Shapes.** Scalars. P∞ [m²] posterior, P̄∞ = P∞ + R_proc [m²] prior, K∞ dimensionless. R_proc > 0, Q_meas > 0
(with R_proc = 0 the positive root is 0: C1, trick 4).

**Naive (p. 168).**

```python
def update(x, z):
    K = .13232  # experimentally derived Kalman gain
    y = z - x   # residual
    x = x + K*y # posterior
    return x

def predict(x):
    return x + vel*dt
```

**Robust.**

```python
def steady_state(R_proc, Q_meas):
    """Posterior P_inf and gain K_inf of the scalar random-walk KF. Positive root, stable form."""
    assert R_proc > 0.0 and Q_meas > 0.0
    # 2 R Q / (R + sqrt(R^2 + 4 R Q)) is the positive root without subtracting nearly equal numbers
    P_inf = 2.0 * R_proc * Q_meas / (R_proc + np.sqrt(R_proc**2 + 4.0 * R_proc * Q_meas))
    return P_inf, P_inf / Q_meas

def fixed_gain_step(x, z, u, K):
    x_bar = x + u
    return x_bar + K * (z - x_bar)

def fixed_gain_variance(K, R_proc, Q_meas):
    """True steady error variance of a fixed-gain filter on the random-walk model, any 0 < K < 1 (Joseph)."""
    a = (1.0 - K) ** 2
    return (a * R_proc + K**2 * Q_meas) / (1.0 - a)
```

Tricks:

1. **Compute K∞ from the model; do not tune it by eye.** `steady_state` gives the gain the full filter converges
   to; "experimentally derived" (p. 168) gives a number nobody can re-derive when the sensor changes.
2. **Stable root.** −R_proc + √(R_proc² + 4R_procQ_meas) subtracts two nearly equal numbers when R_proc ≫ Q_meas;
   the rationalized form 2R_procQ_meas/(R_proc + √…) does not. Same root. At R_proc = 1, Q_meas = 10⁻¹⁰ the textbook
   form is off by 8 × 10⁻⁹ relative; the stable form agrees with the iterated recursion to all printed digits.
3. **Check by iteration.** Iterating C2's variance from the chapter's P₀ reaches P∞ to 10⁻⁶ relative in 11 steps
   for the dog (R_proc = 1, Q_meas = 2; P∞ = 1.00000 m², K∞ = 0.50000), 12 steps for (2, 4.5) (P∞ = 2.16228 m²,
   K∞ = 0.48051) and 20 steps for the thermometer (P∞ = 0.00537 V², K∞ = 0.31770). These match p. 146 (1.0),
   p. 148 (2.1623) and p. 157 (0.005). An oracle test should compare `steady_state` with the iterated recursion.
4. **Price a wrong gain with Joseph.** C3's Joseph form at steady state gives the variance any fixed K actually
   delivers. Dog (R_proc = 2, Q_meas = 4.5): K∞ = 0.48051 → 2.16228 m²; K = 0.2 → 4.05556 m²; K = 0.8 →
   3.08333 m². Monte Carlo (2000 runs, steps 100–399) gives 2.1628, 4.0734 and 3.0723 m². K∞ is the minimum; too
   small a gain costs more here than too large.
5. **A biased u becomes a constant offset.** With the fixed gain and an error e in u per step, the estimate settles
   at e(1 − K)/K from the truth: e = 1 m/step, K = 0.48051 gives 1.0811 m, by formula and by simulation. Small K
   (heavy smoothing) amplifies it; this is the offset in the pp. 165–167 plot (lecture L9).
6. **It is the g-h filter with h = 0.** `fixed_gain_step` is the ch. 1 g-h filter without the velocity update and
   with g = K∞; the Kalman filter is what chooses g.

**Oracles.** P∞ against the iterated variance recursion; K∞ = P∞/Q_meas = P̄∞/(P̄∞ + Q_meas) (both print 0.48051 for
the dog); `fixed_gain_variance(K∞)` = P∞; `fixed_gain_variance` against Monte Carlo (trick 4). The book's 0.13232 is
not checked here: which ratio R_proc/Q_meas produces it is an exercise.

**C++ (the microcontroller version).**

```cpp
// Gains computed offline by steady_state(); no variance, no division at run time.
constexpr float K_INF = 0.48051f;   // dog, R_proc = 2 m^2, Q_meas = 4.5 m^2

inline float fixed_gain_step(float x, float z, float u) {
  const float x_bar = x + u;
  return x_bar + K_INF * (z - x_bar);
}
```

**Cost.** Two adds and one multiply per step, no division and no variance state. Fits a fixed-point Q15 pipeline.
The price: no NIS (no S), no gate, no recovery from a bad x₀ faster than K∞ allows, and K∞ is wrong the moment
Q_meas or R_proc changes (a different sensor, a faster robot).

**What breaks first.** The noise changes and the hard-coded gain does not (re-run `steady_state`, trick 1); then
the transient: the full filter starts with K ≈ 1, the fixed-gain filter at K∞. A mean error of 100 m with P₀ = 10⁴ m²
falls below 1 m in 1 step (full) vs 8 (fixed) for the dog (2, 4.5), and 197 vs 565 steps for the large-noise filter
of p. 162 (R_proc = 2, Q_meas = 30 000, K∞ = 0.00813). Lecture L10 starts both at z₀, which hides this. Then a biased
u (trick 5).
