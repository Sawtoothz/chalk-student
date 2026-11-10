---
lesson: t2.2
title: Equation-to-code cards — Gaussian filters
oracle: filterpy is not used; the oracle is a Monte Carlo propagation and a dense linear-algebra reference in exercises/tests
status: draft
---

# Equation-to-code cards

Each card: the equation with every symbol's shape, a naive version you can read against the book, a robust version with the tricks named, the C++/Eigen version, and what breaks first.

Convention for the whole repo: `R_proc` is Thrun's R (process noise), `Q_meas` is Thrun's Q (measurement noise). Never name a variable plain `R` or `Q`.

---

## C1. Kalman filter, Table 3.1

**Shapes.** x ∈ ℝⁿ, u ∈ ℝᵐ, z ∈ ℝᵏ. A n×n, B n×m, C k×n, R_proc n×n, Q_meas k×k, K n×k, S k×k.

**Naive (reads like the book).**

```python
def kf_naive(mu, Sigma, u, z, A, B, C, R_proc, Q_meas):
    mu_bar = A @ mu + B @ u                                   # line 2
    Sigma_bar = A @ Sigma @ A.T + R_proc                      # line 3
    K = Sigma_bar @ C.T @ np.linalg.inv(C @ Sigma_bar @ C.T + Q_meas)   # line 4
    mu = mu_bar + K @ (z - C @ mu_bar)                        # line 5
    Sigma = (np.eye(len(mu)) - K @ C) @ Sigma_bar             # line 6
    return mu, Sigma
```

**Robust.**

```python
def kf_update(mu_bar, Sigma_bar, z, C, Q_meas):
    nu = z - C @ mu_bar                                  # innovation, keep it: you will plot it
    S = C @ Sigma_bar @ C.T + Q_meas                     # innovation covariance, k x k
    S = 0.5 * (S + S.T)
    # K = Sigma_bar C^T S^-1  ->  solve S^T K^T = C Sigma_bar^T, never form S^-1
    K = scipy.linalg.cho_solve(scipy.linalg.cho_factor(S), C @ Sigma_bar).T
    mu = mu_bar + K @ nu
    I_KC = np.eye(len(mu_bar)) - K @ C
    Sigma = I_KC @ Sigma_bar @ I_KC.T + K @ Q_meas @ K.T  # Joseph form: symmetric, PSD, works for any K
    return mu, Sigma, nu, S
```

Tricks, each one named:

1. **`cho_solve` instead of `inv`.** Same answer, half the flops, and it fails loudly (not PD) instead of returning garbage when S is singular.
2. **Joseph form** for line 6. The book's (I − KC)Σ̄ is only symmetric when K is the optimal gain in exact arithmetic. Joseph form is symmetric for any K and stays PSD under round-off. Cost: one extra n×n product; worth it below n ≈ 100.
3. **Symmetrize S.** Round-off in CΣ̄Cᵀ is enough to make `cho_factor` complain after a few thousand steps.
4. **Return ν and S.** Normalized innovation squared νᵀS⁻¹ν is the number you tune Q_meas and R_proc against (NIS, exercise T5).
5. **Sequential updates.** If Q_meas is diagonal, update one scalar measurement at a time: S is 1×1 and there is no inversion at all. This is how most embedded KFs run.

**Eigen.**

```cpp
template <int N, int K>
void kf_update(Eigen::Matrix<double,N,1>& mu, Eigen::Matrix<double,N,N>& Sigma,
               const Eigen::Matrix<double,K,1>& z, const Eigen::Matrix<double,K,N>& C,
               const Eigen::Matrix<double,K,K>& Q_meas) {
  const Eigen::Matrix<double,K,1> nu = z - C * mu;
  Eigen::Matrix<double,K,K> S = C * Sigma * C.transpose() + Q_meas;
  S = 0.5 * (S + S.transpose()).eval();
  const Eigen::LDLT<Eigen::Matrix<double,K,K>> ldlt(S);
  // K = Sigma C^T S^-1 : solve S K^T = C Sigma  (S symmetric)
  const Eigen::Matrix<double,N,K> Kg = ldlt.solve(C * Sigma).transpose();
  mu.noalias() += Kg * nu;
  const Eigen::Matrix<double,N,N> I_KC = Eigen::Matrix<double,N,N>::Identity() - Kg * C;
  Sigma = I_KC * Sigma * I_KC.transpose() + Kg * Q_meas * Kg.transpose();
}
```

Fixed sizes `N`, `K` when known at compile time: no heap allocation, and Eigen vectorizes the small products. `.eval()` on the symmetrize line avoids aliasing. `LDLT` over `LLT` because it tolerates a semidefinite S.

**Cost per step.** Predict O(n³) for AΣAᵀ (O(n²) when A is sparse, which it usually is). Update O(k³ + n²k). The book's O(k^2.4) is the inversion; in practice the n²k products dominate for n ≫ k.

**What breaks first.** Σ losing symmetry (fixed by Joseph), then Σ going indefinite when Q_meas is tiny relative to Σ̄ (fixed by Joseph or by a square-root filter), then the filter diverging because R_proc is too small for the real motion (fixed only by tuning; see T5).

---

## C2. EKF, Table 3.3

**Shapes.** g: ℝᵐ×ℝⁿ→ℝⁿ, h: ℝⁿ→ℝᵏ, G n×n, H k×n. Everything else as C1.

**Naive.**

```python
def ekf_naive(mu, Sigma, u, z, g, G_of, h, H_of, R_proc, Q_meas):
    mu_bar = g(u, mu)                        # line 2: the FULL nonlinear g, not G @ mu
    G = G_of(u, mu)                          # Jacobian at (u, mu_{t-1})
    Sigma_bar = G @ Sigma @ G.T + R_proc     # line 3
    H = H_of(mu_bar)                         # Jacobian at the PREDICTED mean
    K = Sigma_bar @ H.T @ np.linalg.inv(H @ Sigma_bar @ H.T + Q_meas)
    mu = mu_bar + K @ (z - h(mu_bar))        # line 5: the FULL nonlinear h
    Sigma = (np.eye(len(mu)) - K @ H) @ Sigma_bar
    return mu, Sigma
```

**Robust.** Reuse `kf_update` from C1 with `C = H` and `nu = z - h(mu_bar)` (pass ν in explicitly rather than letting the linear update compute z − Hμ̄). Add:

```python
def wrap_angle(a):
    return (a + np.pi) % (2 * np.pi) - np.pi

nu = z - h(mu_bar)
nu[bearing_idx] = wrap_angle(nu[bearing_idx])     # before it multiplies K
mu[theta_idx] = wrap_angle(mu[theta_idx])         # after the update
```

Tricks:

1. **g for the mean, G for the covariance.** The two most common EKF bugs are Gμ in line 2 and a stale G from the previous step.
2. **Linearize h at μ̄ₜ, not μₜ₋₁.** The book is explicit (3.53). Using the old mean is a subtle, slow-divergence bug.
3. **Wrap every angular innovation** before it is multiplied by K. A bearing innovation of 359° instead of −1° throws the state across the map.
4. **Check every Jacobian by finite differences** before trusting it: `python scripts/fd_check.py exercises.exercise:G_jac --arg u --wrap 2` (card C4 has the same code inline). The chapter gives no Jacobians for a real robot; chapters 5–6 do, and they are long.
5. **Mahalanobis gate** before the update: `d2 = nu @ solve(S, nu)`; reject if `d2 > chi2.ppf(0.99, k)`. This is how an EKF survives a wrong landmark association.

**Eigen.** Same as C1 with `H` for `C` and `nu` passed in. Jacobians as `Eigen::Matrix<double,N,N>` returned from a function; for SE(2)/SE(3) states the Jacobian is with respect to a local perturbation, which is lesson t2.6.

**What breaks first.** Wrong Jacobian sign (finite-difference check catches it), then angle wrap, then linearization error when Σ is wide (symptom: NEES above bound; cure: smaller Δt between predictions, or UKF).

---

## C3. Unscented transform and UKF, eq. 3.66–3.69, Table 3.4

**Shapes.** n = len(μ). Sigma points 𝒳: n×(2n+1). Weights w_m, w_c: (2n+1,). γ = √(n+λ).

**Naive.**

```python
def sigma_points(mu, Sigma, alpha=1e-3, beta=2.0, kappa=0.0):
    n = len(mu)
    lam = alpha**2 * (n + kappa) - n
    gamma = np.sqrt(n + lam)
    L = np.linalg.cholesky((n + lam) * Sigma)           # sqrt((n+lam) Sigma), lower triangular
    X = np.column_stack([mu] + [mu + L[:, i] for i in range(n)] + [mu - L[:, i] for i in range(n)])  # 3.66
    wm = np.full(2 * n + 1, 1.0 / (2 * (n + lam)))
    wc = wm.copy()
    wm[0] = lam / (n + lam)                               # 3.67
    wc[0] = lam / (n + lam) + (1 - alpha**2 + beta)
    return X, wm, wc

def unscented_transform(Y, wm, wc, noise_cov):
    mu = Y @ wm                                           # 3.69
    D = Y - mu[:, None]
    Sigma = (D * wc) @ D.T + noise_cov
    return mu, Sigma, D
```

**Robust.**

```python
def ukf_step(mu, Sigma, u, z, g, h, R_proc, Q_meas, **sp):
    X, wm, wc = sigma_points(mu, Sigma, **sp)                       # line 2
    Xs = np.column_stack([g(u, X[:, i]) for i in range(X.shape[1])])  # line 3
    mu_bar, Sigma_bar, _ = unscented_transform(Xs, wm, wc, R_proc)    # lines 4-5
    Sigma_bar = 0.5 * (Sigma_bar + Sigma_bar.T)
    Xb, wm, wc = sigma_points(mu_bar, Sigma_bar, **sp)              # line 6: redraw, do not reuse Xs
    Zb = np.column_stack([h(Xb[:, i]) for i in range(Xb.shape[1])])   # line 7
    z_hat, S, Dz = unscented_transform(Zb, wm, wc, Q_meas)            # lines 8-9
    Dx = Xb - mu_bar[:, None]
    Sigma_xz = (Dx * wc) @ Dz.T                                       # line 10
    K = scipy.linalg.cho_solve(scipy.linalg.cho_factor(S), Sigma_xz.T).T   # line 11
    nu = z - z_hat
    mu = mu_bar + K @ nu                                              # line 12
    Sigma = Sigma_bar - K @ S @ K.T                                   # line 13, symmetric by construction
    return mu, 0.5 * (Sigma + Sigma.T), nu, S
```

Tricks:

1. **Cholesky as the matrix square root.** Any L with LLᵀ = (n+λ)Σ is valid in 3.66; Cholesky is the cheapest. Its columns are *not* the principal axes of the ellipse the book draws (p. 65): only the symmetric square root (from an eigendecomposition) gives those, and the two choices give different, equally valid sigma-point sets. Cholesky fails if Σ is not PD, which is your early warning that something upstream went wrong.
2. **Redraw sigma points at line 6.** Reusing the propagated points Xs loses the process-noise spread. The shortcut is common in tutorials and measurably worse.
3. **Angles in sigma points.** The weighted mean of angles is wrong near ±π. Either wrap each sigma point relative to 𝒳⁽⁰⁾ before averaging, or use the SO(2)/SO(3) mean (t2.6).
4. **Huge negative centre weights for small α.** With α = 10⁻³, κ = 0, n = 3: λ ≈ −3, w_m⁽⁰⁾ ≈ −10⁶ and w_c⁽⁰⁾ ≈ −10⁶, while the 2n outer points sit only γ ≈ 0.002 standard deviations from the mean. The weighted sums in 3.69 then subtract two numbers of size 10⁶ to get a result of size 1 (catastrophic cancellation), and Σ' can come out indefinite with a nonlinear g. If you see it, raise α toward 1 (the session uses α = 1, κ = 1) or add a small diagonal jitter before Cholesky.
5. **Cost.** 2n+1 calls to g and to h. For n = 15 that is 31 calls, each cheaper than one Jacobian evaluation in most robot models.

**Eigen.**

```cpp
template <int N>
struct SigmaPoints {
  Eigen::Matrix<double, N, 2 * N + 1> X;
  Eigen::Matrix<double, 2 * N + 1, 1> wm, wc;
};

template <int N>
SigmaPoints<N> sigma_points(const Eigen::Matrix<double,N,1>& mu, const Eigen::Matrix<double,N,N>& Sigma,
                            double alpha = 1e-3, double beta = 2.0, double kappa = 0.0) {
  const double lam = alpha * alpha * (N + kappa) - N;
  const Eigen::LLT<Eigen::Matrix<double,N,N>> llt((N + lam) * Sigma);
  if (llt.info() != Eigen::Success) throw std::runtime_error("Sigma not PD");
  const Eigen::Matrix<double,N,N> L = llt.matrixL();
  SigmaPoints<N> s;
  s.X.col(0) = mu;
  for (int i = 0; i < N; ++i) { s.X.col(1 + i) = mu + L.col(i); s.X.col(1 + N + i) = mu - L.col(i); }
  s.wm.setConstant(1.0 / (2.0 * (N + lam)));
  s.wc = s.wm;
  s.wm(0) = lam / (N + lam);
  s.wc(0) = lam / (N + lam) + (1.0 - alpha * alpha + beta);
  return s;
}
```

**What breaks first.** Cholesky failing (Σ not PD: upstream bug or w_c⁽⁰⁾ trouble), then angle averaging, then the same linearization limits as the EKF but later.

---

## C4. Jacobians by finite differences (3.50, 3.53)

Not in the book's tables but required by them. The check every Jacobian must pass:

```python
def numeric_jacobian(f, x, eps=1e-6):
    y0 = np.atleast_1d(f(x))
    J = np.zeros((y0.size, x.size))
    for j in range(x.size):
        dx = np.zeros_like(x); dx[j] = eps
        J[:, j] = (np.atleast_1d(f(x + dx)) - np.atleast_1d(f(x - dx))) / (2 * eps)   # central difference
    return J

def check_jacobian(f, J_analytic, x, rtol=1e-5, atol=1e-7):
    Jn = numeric_jacobian(f, x)
    Ja = J_analytic(x)
    err = np.abs(Ja - Jn).max()
    assert err <= atol + rtol * np.abs(Jn).max(), f"Jacobian mismatch {err:.2e}\n{Ja}\n{Jn}"
```

Central differences give O(ε²) error; ε = 1e-6 is the sweet spot for double precision. For angular outputs, wrap the difference before dividing. Run it at ten random states, not one: a wrong sign in a sin term is invisible at θ = 0.

---

## C5. Information form, Table 3.5 and eq. 3.70–3.73

**Conversions.**

```python
Omega = np.linalg.inv(Sigma)           # 3.70   (or cho_solve(cho_factor(Sigma), I))
xi = Omega @ mu                        # 3.71
Sigma = np.linalg.inv(Omega)           # 3.72
mu = np.linalg.solve(Omega, xi)        # 3.73   solve, never inv @ xi
```

**Update (lines 4–5): addition.**

```python
Omega = Omega_bar + C.T @ solve(Q_meas, C)
xi = xi_bar + C.T @ solve(Q_meas, z)
```

**Predict (lines 2–3): two inversions.** Implement it once as written to feel the cost, then note that in practice you keep Σ for prediction and switch to Ω only for fusion.

**Total ignorance.** `Omega = zeros((n, n)); xi = zeros(n)` is a valid prior. There is no covariance-form equivalent; `Sigma = 1e12 * I` is the usual hack and it destroys conditioning in line 4 of the KF.

**Mahalanobis distance.** The book defines it on p. 72 as the Ω-weighted quadratic in x. The same idea applied to the innovation, d² = (z − ẑ)ᵀ S⁻¹ (z − ẑ), is the standard gating test (Bar-Shalom), not something the chapter states: under the hypothesis that the measurement belongs to this state, d² ~ χ²(k). Gate at the 99% quantile.

**Where this goes.** GTSAM's `GaussianFactorGraph` is Ω and ξ stored as a sum of factors that was never added up. `Marginals` is 3.72 for a block. iSAM2 is Table 3.5 lines 4–5 with a clever ordering for the solve in 3.73.
