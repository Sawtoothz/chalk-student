---
lesson: t2.3
title: Equation-to-code cards — nonparametric filters
oracle: Table 4.1 on two states (for Table 4.2), the KF of t2.2 on linear-Gaussian systems (for Table 4.3), closed-form Gaussian probabilities (for (4.28)), the expected copy count M·w and the equal-weights identity (for Table 4.4); all in exercises/tests
status: draft
---

# Equation-to-code cards

Each card has six parts: shapes, naive code that reads like the book, robust code with each trick named, Eigen, cost, and what breaks first. Cards are in the order you implement them; C4 calls C5 and C6.

Repo conventions: motion noise is `R_proc` and measurement noise is `Q_meas` (Thrun's R and Q). Never write a bare `R` or `Q`. Angles go through `wrap()` from the package's `models.py`. Weights live in log space unless a line of code says otherwise.

```python
import numpy as np
from scipy.special import logsumexp, expit, logit
from models import wrap
```

---

## C1. Histogram filter, Table 4.1 with (4.2)–(4.5)

**Shapes.** K bins. Belief p ∈ ℝᴷ, Σp = 1. Transition T ∈ ℝᴷˣᴷ, Tₖᵢ = p(xₖ ∣ u, xᵢ), columns sum to 1. Likelihood ℓ ∈ ℝᴷ, ℓₖ = p(z ∣ x̂ₖ) (4.4). Bin edges (K+1,) in 1-D; bin volumes |xₖ| (K,). In n dimensions K = ∏ bins per axis, and p is stored as an n-D array and flattened only for T.

**Naive (reads like the book).**

```python
def hist_predict_naive(p, T):
    K = len(p)
    p_bar = np.zeros(K)
    for k in range(K):                       # line 2
        for i in range(K):
            p_bar[k] += T[k, i] * p[i]       # line 3
    return p_bar

def hist_update_naive(p_bar, lik):
    p = lik * p_bar                          # line 4, before eta
    return p / p.sum()                       # eta
```

**Robust.**

```python
def transition_from_density(centers, u, motion_pdf):
    T = motion_pdf(centers[:, None], u, centers[None, :])   # T[k, i] = p(x̂_k | u, x̂_i)   (4.5)
    # (4.5) multiplies by |x_k|; on a uniform grid that factor is a constant and the column
    # normalization absorbs it. On unequal bins multiply T by the volumes[:, None] first.
    return T / T.sum(axis=0, keepdims=True)                  # eta, one per source column

def hist_predict(p, T):
    return T @ p                                             # line 3 as one product

def hist_predict_conv(p, kernel):
    # shift-invariant motion on a ring: line 3 is a circular convolution
    return np.real(np.fft.ifft(np.fft.fft(p) * np.fft.fft(kernel)))

def hist_update(log_p_bar, log_lik):
    a = log_lik + log_p_bar                                  # line 4 in log space
    return a - logsumexp(a)                                  # eta

def hist_density(x, edges, p):
    k = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, len(p) - 1)
    inside = (x >= edges[0]) & (x < edges[-1])
    return np.where(inside, p[k] / np.diff(edges)[k], 0.0)   # (4.2)
```

Tricks:

1. **Normalize T by column.** The η of (4.5) is per source bin i: the probed densities times |xₖ| do not sum to 1 over k, and an unnormalized T slowly creates or destroys probability mass. Keep the |xₖ| factor when bins have unequal volumes (density trees, log-spaced range bins); on a uniform grid it cancels. Table 4.1 as printed leaves p̄ unnormalized and lets line 4's η fix it (p. 92); normalizing T keeps p̄ a distribution as well.
2. **Convolution when the motion is shift-invariant.** When p(xₖ ∣ u, xᵢ) depends only on xₖ − xᵢ − u, line 3 is a convolution: FFT on a ring, `scipy.signal.fftconvolve` with zero padding on a bounded domain. O(K log K) instead of O(K²), and no K×K matrix.
3. **Truncate the kernel and use a sparse T.** Motion noise that is negligible beyond 3–4σ gives a banded T; `scipy.sparse.csr_matrix` stores and multiplies only the band.
4. **Update in log space.** A product of many small likelihoods underflows to an all-zero belief and the division by the sum gives NaN. `logsumexp` cannot underflow.
5. **Probe at the bin centre, consistently.** (4.3) defines x̂ as the bin mean; use the same x̂ in T and in ℓ, or a half-bin bias appears in every step.
6. **Floor tiny bins only on purpose.** A bin that reaches exactly 0 can never come back (line 4 multiplies). A small floor plus renormalization is the histogram version of random injection; like injection, it makes the posterior incorrect, so leave it off by default and name it when you use it.

**Eigen.**

```cpp
Eigen::VectorXd hist_step(const Eigen::SparseMatrix<double>& T, const Eigen::VectorXd& p,
                          const Eigen::VectorXd& log_lik) {
  Eigen::VectorXd p_bar = T * p;                                   // line 3, banded sparse T
  Eigen::ArrayXd a = log_lik.array() + p_bar.array().max(1e-300).log();
  const double amax = a.maxCoeff();
  Eigen::ArrayXd q = (a - amax).exp();                             // line 4 in log space
  return (q / q.sum()).matrix();                                   // eta
}
```

Build T once per distinct u, as `Eigen::SparseMatrix<double>` from triplets with `setFromTriplets`. For a 2-D or 3-D grid with shift-invariant motion, use separable 1-D convolutions along each axis instead of any matrix.

**Cost.** Dense line 3 is O(K²), line 4 is O(K). With the convolution, O(K log K); with a kernel of half-width b bins, O(K b). Memory O(K), and K grows exponentially with the state dimension.

**What breaks first.** 1. An all-zero belief after a run of unlikely measurements (log space fixes it). 2. Mass leaking at the domain edge because the columns of T near the edge were not renormalized. 3. A bin width too coarse for the sensor: when the likelihood is narrower than a bin, (4.4) samples it at the centre and misses the peak (lecture L3). 4. Memory, once you add θ.

---

## C2. Binary Bayes filter in log odds, Table 4.2 with (4.13), (4.14), (4.21)

**Shapes.** Scalars per cell: lₜ, l₀ = logit p(x), p(x ∣ zₜ) ∈ (0, 1). For a map, l is an array the shape of the grid and everything below is element-wise.

**Naive.**

```python
def binary_bayes_naive(l_prev, p_x_given_z, p_x):
    return (l_prev + np.log(p_x_given_z / (1 - p_x_given_z))
                   - np.log(p_x / (1 - p_x)))           # line 2

def belief_naive(l):
    return 1 - 1 / (1 + np.exp(l))                      # (4.14)
```

**Robust.**

```python
def prob_to_logodds(p, eps=1e-12):
    return logit(np.clip(p, eps, 1 - eps))              # (4.13), (4.21)

def logodds_update(l, p_inv, l0, l_min=None, l_max=None):
    l = l + logit(p_inv) - l0                           # line 2: add evidence, subtract the prior
    if l_min is not None:
        l = np.clip(l, l_min, l_max)                    # common practice (e.g. OctoMap), not in the book
    return l

def logodds_to_prob(l):
    return expit(l)                                     # (4.14) without overflow or cancellation
```

Tricks:

1. **Subtract l₀ every update.** The inverse model p(x ∣ zₜ) already contains the prior; adding it once per reading counts it t times. (p. 96 says "addition"; (4.20) subtracts.) With l₀ = 0 (prior 0.5) the bug is invisible, which is why it survives in occupancy-grid code until somebody changes the prior.
2. **`expit` for (4.14).** As written, (4.14) overflows `exp` for l > 709 and returns exactly 0 by cancellation for very negative l. `expit` evaluates the same function stably for any l.
3. **Clip p before `logit`.** An inverse model that returns exactly 0 or 1 makes l infinite, and the cell can then never change.
4. **Clamp l (optional, named).** Bounding l to a band, as practical mappers such as OctoMap do (the book does not; Table 9.1 has no clamp), lets a cell that was occupied become free after the object moves. It is a modelling choice that breaks the static-state assumption on purpose; keep it a parameter.
5. **Store l, never p.** The update is one add per cell, which vectorizes over the whole map and fits in `float32`.

**Eigen.**

```cpp
inline double logodds_update(double l, double p_inv, double l0,
                             double l_min = -4.0, double l_max = 4.0) {
  const double l_new = l + std::log(p_inv / (1.0 - p_inv)) - l0;  // Table 4.2 line 2
  return std::clamp(l_new, l_min, l_max);                         // clamp: common practice, not the book
}
inline double logodds_to_prob(double l) {                         // (4.14), stable both ways
  return l >= 0 ? 1.0 / (1.0 + std::exp(-l)) : std::exp(l) / (1.0 + std::exp(l));
}
```

For a grid, `Eigen::ArrayXXf L` and `L += log_odds_inv - l0;` over the cells a scan touched. Precompute `log(p/(1-p))` for the two or three values your inverse model returns (hit, free, unknown).

**Cost.** O(1) per cell per reading; a map update is O(cells touched by the scan).

**What breaks first.** 1. The prior added instead of subtracted (the map drifts toward full or empty with no evidence; lecture Fig L4). 2. An inverse model returning 0 or 1 (infinite l). 3. Without a clamp, cells that saw a moving object stay occupied indefinitely. 4. `exp` overflow in (4.14) when you plot probabilities.

---

## C3. Self-normalized importance sampling, (4.25)–(4.28)

**Shapes.** M samples xᵐ ∈ ℝⁿ: an (M, n) array. log f, log g: (M,) → (M,). Test function h: (M, n) → (M,), e.g. the indicator I(x ∈ A). Normalized weights w̃ ∈ ℝᴹ, Σw̃ = 1.

**Naive.**

```python
def is_naive(xs, f, g, in_A):
    w = f(xs) / g(xs)                                  # (4.27)
    return np.sum(in_A(xs) * w) / np.sum(w)            # (4.28)
```

**Robust.**

```python
def is_estimate(xs, log_f, log_g, h):
    logw = log_f(xs) - log_g(xs)                       # (4.27) in log space
    if np.any(np.isposinf(logw)):
        raise ValueError("g(x) = 0 where f(x) > 0: support condition of (4.25) violated")
    wn = np.exp(logw - logsumexp(logw))                # (4.28): normalize once
    n_eff = 1.0 / np.sum(wn ** 2)
    return float(np.sum(wn * h(xs))), n_eff
```

Tricks:

1. **Log densities, not densities.** f and g are often products of many terms (a scan likelihood is a product over beams), and f/g then underflows to 0/0.
2. **Normalize with `logsumexp`.** Subtracting the maximum log weight before `exp` is what `logsumexp` does internally; f only needs to be known up to a constant, which is exactly the PF's situation (η in (4.34)).
3. **Return N_eff = 1/Σw̃².** It ranges from 1 (one sample carries everything) to M (equal weights). It is from outside the book: for normalized weights it equals M / (1 + M² Var(w̃)), so it is the book's "variance of the importance weights" (p. 109) on a readable scale.
4. **Check the support condition.** f(x) > 0 ⟹ g(x) > 0 (p. 100). An infinite log weight is a proof of violation; the silent failure is worse: g nearly zero where f has mass, so no sample ever lands there (lecture Fig L6, amber curve).
5. **Expect a bias at small M.** Dividing by Σw makes (4.28) biased by O(1/M) (standard result, e.g. Owen, *Monte Carlo theory, methods and examples*, ch. 9). The oracle tests use M large enough that the bias is below the test tolerance.

**Eigen.**

```cpp
inline double normalize_log_weights(Eigen::Ref<Eigen::VectorXd> logw) {   // returns N_eff
  const double m = logw.maxCoeff();
  const double lse = m + std::log((logw.array() - m).exp().sum());
  logw.array() -= lse;
  return 1.0 / (2.0 * logw.array()).exp().sum();
}
```

C4 reuses this function.

**Cost.** O(M) evaluations of log f and log g, which dominate; the normalization is O(M). The error falls as O(1/√M), with a constant set by how well g covers f (p. 102).

**What breaks first.** 1. Underflow to 0/0 with raw densities. 2. A proposal that misses a mode of f: the estimate is confidently wrong, and N_eff gives no warning because it only sees the samples that exist. 3. Small-M bias, when M is forced down.

---

## C4. Particle filter step, Table 4.3 with (4.24), (4.36)

**Shapes.** Particles X ∈ ℝᴹˣⁿ (rows are particles). Log weights logw ∈ ℝᴹ. Control u, measurement z: whatever the models take. `sample_motion(u, X, rng) -> (M, n)` draws line 4 for all particles at once, using `R_proc`. `log_lik(z, X) -> (M,)` evaluates line 5, using `Q_meas`.

**Naive (one resample per step, as in the table).**

```python
def pf_step_naive(X, u, z, sample_motion, likelihood, rng):
    M = len(X)
    X_bar = np.array([sample_motion(u, X[m], rng) for m in range(M)])   # line 4
    w = np.array([likelihood(z, X_bar[m]) for m in range(M)])           # line 5
    idx = rng.choice(M, size=M, p=w / w.sum())                          # lines 8-11
    return X_bar[idx]                                                   # line 12
```

**Robust.**

```python
def pf_step(X, logw, u, z, sample_motion, log_lik, rng,
            neff_frac=0.5, inject=0.0, sample_uniform=None, angle_idx=()):
    M = len(X)
    X = sample_motion(u, X, rng)                    # line 4, vectorized over particles
    for j in angle_idx:
        X[:, j] = wrap(X[:, j])
    logw = logw + log_lik(z, X)                     # line 5 and (4.36): multiply, in log space
    logw = logw - logsumexp(logw)
    n_eff = 1.0 / np.exp(logsumexp(2 * logw))
    if n_eff < neff_frac * M:                       # resample only when the weights say so
        idx = low_variance_resample(np.exp(logw), rng)   # C5
        X = X[idx]
        logw = np.full(M, -np.log(M))               # (4.36): weights reset after resampling
        if inject > 0:                              # p. 113, last resort, off by default
            n = int(round(inject * M))
            X[rng.choice(M, n, replace=False)] = sample_uniform(n, rng)
    return X, logw, n_eff
```

Tricks:

1. **Vectorize line 4 and line 5.** The loop over m in the table is a loop over rows; numpy draws all M motion samples in one call and evaluates all M likelihoods in one call.
2. **Log weights and `logsumexp`** (C3). A LiDAR likelihood is a product over hundreds of beams; in linear space it underflows for every particle.
3. **Carry weights across steps (4.36).** Table 4.3 throws the weights away after resampling every step. Keeping them and resampling only when needed is the book's first variance-reduction strategy (p. 109).
4. **Resample on N_eff < M/2.** The threshold is folklore, not the book's; M/2 is a common default in particle-filter code; treat it as a tuning parameter. Lower it if you see diversity loss, raise it if weights degenerate.
5. **Low-variance resampling** (C5) instead of `rng.choice`: O(M), and returns the set unchanged when the weights are equal.
6. **Do not update or resample when the robot is stationary** (p. 109). Gate the whole step on odometry: no motion, no step.
7. **Wrap angles after line 4** with `wrap()` from `models.py`, so later arithmetic (C6, likelihoods with bearing differences) never sees θ outside [−π, π).
8. **Random injection is a named option, off by default** (p. 113). It makes the posterior incorrect; switch it on only when the best log-likelihood stays low for several steps (lecture L11).
9. **Seed the generator per run** (`np.random.default_rng(seed)`, passed in). Two runs with different seeds are your sampling-variance measurement (lecture L8).

**Eigen.**

```cpp
template <int N, class Rng, class Motion, class LogLik>
double pf_step(Eigen::Matrix<double, Eigen::Dynamic, N>& X, Eigen::VectorXd& logw,
               const Eigen::VectorXd& u, const Eigen::VectorXd& z,
               Motion&& sample_motion, LogLik&& log_lik, Rng& rng, double neff_frac = 0.5) {
  const int M = static_cast<int>(X.rows());
  for (int m = 0; m < M; ++m) {
    X.row(m) = sample_motion(u, X.row(m).transpose().eval(), rng).transpose();  // line 4
    logw[m] += log_lik(z, X.row(m).transpose().eval());                         // line 5, (4.36)
  }
  const double neff = normalize_log_weights(logw);                              // C3
  if (neff < neff_frac * M) {
    const std::vector<int> idx = low_variance_resample(logw.array().exp().matrix().eval(), rng);
    Eigen::Matrix<double, Eigen::Dynamic, N> Xn(M, X.cols());
    for (int m = 0; m < M; ++m) Xn.row(m) = X.row(idx[m]);
    X.swap(Xn);                                   // gather into a new buffer: X[idx] in place aliases
    logw.setConstant(-std::log(static_cast<double>(M)));
  }
  return neff;
}
```

Fixed column count `N` (3 for planar pose) keeps each row on the stack. `.eval()` on the row arguments breaks the aliasing between the row being read and the row being written. The particle loop is embarrassingly parallel; give each thread its own `Rng`.

**Cost.** O(M) motion samples plus O(M) likelihood evaluations per step; the likelihood dominates (a beam model is O(beams) per particle, so O(M · beams)). Resampling is O(M). M needed grows quickly with state dimension (p. 113).

**What breaks first.** 1. All weights zero or NaN from linear-space likelihoods. 2. Particle collapse from resampling every step, worst when the robot is stationary (lecture L9). 3. A likelihood much narrower than the motion spread, so N_eff stays near 1 after every update (lecture L6); widen Q_meas in the likelihood or improve the proposal. 4. Deprivation after a kidnap or slip (lecture L11). 5. An unwrapped θ making the weighted mean (C6) meaningless.

---

## C5. Resampling, Table 4.4 and (4.37)

**Shapes.** Weights w ∈ ℝᴹ, normalized. Output: indices idx ∈ {0, …, M−1}ᴹ; the new set is `X[idx]`.

**Naive (Table 4.4, zero-based).**

```python
def low_variance_naive(X, w, rng):
    M = len(w)
    out = []
    r = rng.uniform(0, 1 / M)            # line 3
    c = w[0]                             # line 4
    i = 0                                # line 5
    for m in range(M):                   # line 6
        U = r + m / M                    # line 7  (book's m - 1 with m from 1)
        while U > c:                     # line 8
            i += 1                       # line 9
            c += w[i]                    # line 10
        out.append(X[i])                 # line 12
    return np.array(out)
```

**Robust.**

```python
def low_variance_resample(w, rng):          # systematic resampling
    M = len(w)
    cw = np.cumsum(w); cw /= cw[-1]          # normalize here, so the last edge is exactly 1
    U = rng.uniform(0, 1 / M) + np.arange(M) / M         # lines 3 and 7
    return np.minimum(np.searchsorted(cw, U, side="left"), M - 1)   # (4.37)

def multinomial_resample(w, rng):           # Table 4.3 lines 8-11
    cw = np.cumsum(w); cw /= cw[-1]
    return np.minimum(np.searchsorted(cw, rng.random(len(w))), len(w) - 1)

def stratified_resample(w, rng):            # the literature's stratified: one draw per stratum
    M = len(w); cw = np.cumsum(w); cw /= cw[-1]
    U = (np.arange(M) + rng.random(M)) / M
    return np.minimum(np.searchsorted(cw, U), M - 1)
```

Tricks:

1. **`searchsorted` is (4.37).** It returns, for each U, the first index j whose cumulative sum is ≥ U, which is the argmin in (4.37) and what the while loop of lines 8–10 computes. Because the U are sorted, the loop version is O(M); `searchsorted` is O(M log M) but runs as one vectorized call, which is what you want in numpy.
2. **Normalize inside the resampler.** Table 4.4 assumes Σw = 1 and Table 4.3 never normalizes. With Σw < 1 the naive while loop runs past index M−1; with Σw > 1 the tail particles are never drawn. Dividing the cumulative sum by its last entry makes the function safe for any positive weights.
3. **Clip to M − 1.** Round-off can leave cw[−1] a hair below the largest U; the clip turns an index error into the correct last particle.
4. **Return indices, not particles.** You need them for ancestry (lecture L7), for copying per-particle maps in FastSLAM, and for tests.
5. **Name the variants apart.** The book's "stratified sampling" (p. 111) is a two-stage scheme over groups of particles; `stratified_resample` above is the literature's one-draw-per-stratum sampler. Neither is Table 4.4.
6. **Equal weights in, same set out.** With w = 1/M, `low_variance_resample` returns 0, 1, …, M−1 (p. 111, second advantage). This is a one-line test.
7. **Copy counts are ⌊Mwᵢ⌋ or ⌈Mwᵢ⌉** for systematic resampling (outside the book; it follows from the comb's teeth being 1/M apart). Multinomial copies can be anything from 0 to M; both have expected copy count Mwᵢ.

**Eigen.**

```cpp
template <class Rng>
std::vector<int> low_variance_resample(const Eigen::VectorXd& w, Rng& rng) {
  const int M = static_cast<int>(w.size());
  std::uniform_real_distribution<double> uni(0.0, 1.0 / M);
  const double r = uni(rng), total = w.sum();                      // line 3, normalize on the fly
  std::vector<int> idx(M);
  double c = w[0] / total;                                         // line 4
  int i = 0;                                                       // line 5
  for (int m = 0; m < M; ++m) {
    const double U = r + static_cast<double>(m) / M;               // line 7
    while (U > c && i < M - 1) { ++i; c += w[i] / total; }         // lines 8-10, bounded
    idx[m] = i;                                                    // line 12
  }
  return idx;
}
```

In C++ the table's loop is the right implementation: O(M), one pass, no allocation beyond the output.

**Cost.** Table 4.4: O(M). Multinomial by M binary searches: O(M log M) (p. 111). Both are cheap next to M likelihood evaluations.

**What breaks first.** 1. Unnormalized weights (index past the end, or a tail never drawn). 2. Off-by-one from translating the book's 1-based `m − 1` and `i = 1`. 3. Diversity loss from resampling too often, which no resampler fixes (C4 trick 3).

---

## C6. Density extraction from particles (4.3.4, p. 104–105)

**Shapes.** X ∈ ℝᴹˣⁿ, normalized weights w̃ ∈ ℝᴹ. Outputs: μ ∈ ℝⁿ, Σ ∈ ℝⁿˣⁿ; or a density evaluated at query points (Q, n) → (Q,).

**Naive.**

```python
def mean_cov_naive(X, w):
    w = w / w.sum()
    mu = w @ X
    D = X - mu
    return mu, (D * w[:, None]).T @ D
```

**Robust.**

```python
def weighted_mean_cov(X, w, angle_idx=()):
    w = w / w.sum()
    mu = w @ X
    for j in angle_idx:                                     # circular mean for headings
        mu[j] = np.arctan2(w @ np.sin(X[:, j]), w @ np.cos(X[:, j]))
    D = X - mu
    for j in angle_idx:
        D[:, j] = wrap(D[:, j])                             # wrap before squaring
    cov = (D * w[:, None]).T @ D / (1.0 - np.sum(w ** 2))   # unbiased for normalized weights
    return mu, cov

def kde(X, w, Xq, bw=None):
    from scipy.stats import gaussian_kde
    return gaussian_kde(X.T, weights=w, bw_method=bw)(Xq.T)    # Fig 4.5(d)
```

Tricks:

1. **Circular mean for θ.** The arithmetic mean of headings at +179° and −179° is 0°, pointing backwards. Average the unit vectors and take `arctan2`.
2. **Wrap the deviations** before forming the covariance, for the same reason.
3. **Divide by 1 − Σw̃²** for an unbiased weighted covariance (reliability-weights correction; with equal weights it is the familiar M/(M−1)). It matters only when N_eff is small, which is when you read the covariance most carefully.
4. **One Gaussian only for one mode.** On a bimodal set the mean lands between modes (lecture L1). Cluster first (k-means, or the connected components of a coarse histogram) and report the heaviest cluster's mean and covariance.
5. **KDE for figures and for multiplying beliefs**, not for the control loop: O(M) per query point (p. 105).
6. **Always pass the weights.** When C4 skipped resampling, the particles alone are not the belief; `weighted_mean_cov(X, np.exp(logw))` is, whether or not the step resampled.

**Eigen.**

```cpp
template <int N>
void weighted_mean_cov(const Eigen::Matrix<double, Eigen::Dynamic, N>& X, const Eigen::VectorXd& w,
                       Eigen::Matrix<double, N, 1>& mu, Eigen::Matrix<double, N, N>& cov) {
  const Eigen::VectorXd wn = w / w.sum();
  mu.noalias() = X.transpose() * wn;
  const Eigen::Matrix<double, Eigen::Dynamic, N> D = X.rowwise() - mu.transpose();
  cov.noalias() = D.transpose() * wn.asDiagonal() * D;
  cov /= (1.0 - wn.squaredNorm());
}
```

For a heading column, replace `mu(j)` with `std::atan2(wn.dot(sin), wn.dot(cos))` and wrap `D.col(j)` before the product.

**Cost.** Mean and covariance O(M n²). Histogram extraction O(M) to build, O(1) per lookup, memory exponential in n. KDE O(M) per query.

**What breaks first.** 1. Heading averaged across ±π. 2. Mean of a multimodal set reported to the controller. 3. Covariance from a nearly degenerate set (N_eff ≈ 1) reported as confidence: Σ ≈ 0 means the filter has collapsed, not that the robot is certain.
