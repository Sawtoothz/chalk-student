---
lesson: t2.4
title: Equation-to-code cards — Robot motion
oracle: the velocity forward model in long double, a forward–inverse round trip, finite differences for the two Jacobian determinants, and sampler-against-density comparisons; every Python block below runs in figures/card_checks.py and every number quoted comes from figures/card_numbers.json
status: draft
---

# Equation-to-code cards

Five cards, in the order you implement them: shapes, a naive version that reads like the book table, a robust version with each trick named, Eigen, cost, what breaks first. C3 and C4 call C1's densities, C2 and C4 its samplers; C5 wraps any of them.

Conventions for this chapter. A pose is (x, y, θ), with θ in rad, zero along x and positive counterclockwise (5.1). M particles are stored as an (M, 3) array; Eigen stores them as `Matrix3Xd`, one particle per column. The noise parameters are `alpha = (a1, …, a6)` for the velocity model and `(a1, …, a4)` for the odometry model, in the book's order. `wrap()` maps an angle to [−π, π) (from `models.py`; the first block repeats it so the cards run on their own). No `R_proc` or `Q_meas` here: the noise lives in the controls, and chapter 7 maps it into state space through a Jacobian. `figures/card_checks.py` runs every Python block, compiles every C++ block against it, and checks the robust code against the gated reference solution.

---

## C1. Error densities and their samplers, Tables 5.2 and 5.4, eq. 5.11–5.12

**Shapes.** a: the error, a scalar or an (M,) array, in the unit of the quantity it perturbs (m/s, rad/s, rad or m). b²: the variance, same shape or broadcastable, in that unit squared. Every density returns the same shape as a.

**Naive (reads like the book).**

```python
import numpy as np


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def prob_normal_naive(a, b2):                       # Table 5.2, eq. 5.11
    return 1.0 / np.sqrt(2 * np.pi * b2) * np.exp(-0.5 * a**2 / b2)          # line 2


def prob_triangular_naive(a, b2):                   # Table 5.2, eq. 5.12
    b = np.sqrt(b2)
    return max(0.0, 1.0 / (np.sqrt(6) * b) - abs(a) / (6 * b2))               # line 4


def sample_normal_naive(b2, rng):                   # Table 5.4
    b = np.sqrt(b2)
    return 0.5 * sum(rng.uniform(-b, b) for _ in range(12))                   # line 2


def sample_triangular_naive(b2, rng):               # Table 5.4
    b = np.sqrt(b2)
    return np.sqrt(6) / 2 * (rng.uniform(-b, b) + rng.uniform(-b, b))         # line 4
```

**Robust.**

```python
B2_FLOOR = 1e-12          # variance floor, in the unit of each error squared; see trick 2


def log_prob_normal(a, b2):
    b2 = np.maximum(b2, B2_FLOOR)
    return -0.5 * (np.log(2 * np.pi * b2) + a * a / b2)


def log_prob_triangular(a, b2):
    b2 = np.maximum(b2, B2_FLOOR)
    p = 1.0 / np.sqrt(6 * b2) - np.abs(a) / (6 * b2)
    return np.where(p > 0, np.log(np.where(p > 0, p, 1.0)), -np.inf)


def sample_normal(b2, rng, size=None):
    return rng.normal(0.0, 1.0, size) * np.sqrt(b2)       # b2 may be 0 or an array


def sample_triangular(b2, rng, size=None):
    b = np.sqrt(b2)
    return np.sqrt(6) / 2 * b * (rng.uniform(-1, 1, size) + rng.uniform(-1, 1, size))
```

Tricks:

1. **Log density, summed.** In this repo `prob_normal_naive` returns exactly 0.0 once |a| reaches 38.6 b. One such term zeroes a product of three, and then a whole set of particle weights. Return log densities, add the three terms, and exponentiate only after subtracting the maximum (the ch. 4 cards do the same for weights).
2. **Floor on b².** At rest (v = ω = 0) every variance in Tables 5.1 and 5.3 is zero: the naive density is 0/0 (`nan` on arrays, `ZeroDivisionError` on floats, both run here) and every particle gets the same pose. Floor it per term in that term's units if it should mean something, e.g. (0.005 m/s)² for v; a constant α₀ added to each variance is the same fix, common in practice and not in the book.
3. **Unit normals times √b², not `normal(0, b)`.** It works when b² = 0 and when b² is an array with one value per particle. C++ `std::normal_distribution` requires σ > 0, so the Eigen version draws N(0, 1) and scales.
4. **`rng.normal`, not twelve uniforms.** Exact Gaussian tails, and about 7× faster than the twelve-uniform sum for 10⁶ draws here (timings vary). Table 5.4's variance and its real support are in lecture L4; keep it for a microcontroller without a fast `log`.
5. **The triangular density is zero beyond ±√6 b** (p. 128). One odometry step outside that range gives a particle weight of exactly zero, and in the log version −∞. Use it only where errors really are bounded, or mix it with a small uniform term, the same mixture chapter 6 uses for range beams.

**Eigen.**

```cpp
#include <Eigen/Dense>
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <random>

constexpr double kB2Floor = 1e-12;

inline double wrap(double a) {  // [-pi, pi)
  a = std::fmod(a + M_PI, 2.0 * M_PI);
  return a < 0.0 ? a + M_PI : a - M_PI;
}

inline double log_prob_normal(double a, double b2) {
  b2 = std::max(b2, kB2Floor);
  return -0.5 * (std::log(2.0 * M_PI * b2) + a * a / b2);
}

inline double log_prob_triangular(double a, double b2) {
  b2 = std::max(b2, kB2Floor);
  const double p = 1.0 / std::sqrt(6.0 * b2) - std::abs(a) / (6.0 * b2);
  return p > 0.0 ? std::log(p) : -std::numeric_limits<double>::infinity();
}

inline double sample_normal(double b2, std::mt19937_64& rng) {
  static thread_local std::normal_distribution<double> n01(0.0, 1.0);  // sigma = 0 is not allowed
  return n01(rng) * std::sqrt(b2);
}
```

**Cost.** O(1) per call: one `log` for the density, one Gaussian draw for the sampler. With M particles, three draws per particle per step. Drawing the random numbers costs more than the arithmetic around them, so draw them in one vectorized call.

**What breaks first.** On a real robot, in this order: the first stop (trick 2), the first kidnap or wheel slip that pushes an error past about 38 σ (trick 1), the first outlier under a triangular density (trick 5).

---

## C2. Velocity model: forward kinematics and sampler, Table 5.3, eq. 5.9, 5.13–5.16

**Shapes.** xₜ₋₁ = (x, y, θ): one pose (3,) or M particles (M, 3). uₜ = (v, ω): v in m/s, ω in rad/s, one control shared by all particles. Δt in s. v̂, ω̂, γ̂: scalars or (M,), in m/s, rad/s, rad/s. alpha = (α₁ … α₆): α₁ dimensionless, α₂ in m², α₃ in m⁻², α₄ dimensionless (lecture L3); α₅ in m⁻² and α₆ dimensionless, by the same logic, since γ̂ is a rate in rad/s like ω̂. Output xₜ: same shape as xₜ₋₁.

**Naive.**

```python
def sample_motion_model_velocity_naive(u, x_prev, alpha, dt, rng, sample=sample_normal_naive):
    v, w = u
    x, y, th = x_prev
    a1, a2, a3, a4, a5, a6 = alpha
    v_h = v + sample(a1 * v**2 + a2 * w**2, rng)                              # line 2, eq. 5.10
    w_h = w + sample(a3 * v**2 + a4 * w**2, rng)                              # line 3, eq. 5.10
    g_h = sample(a5 * v**2 + a6 * w**2, rng)                                  # line 4, eq. 5.15
    xp = x - v_h / w_h * np.sin(th) + v_h / w_h * np.sin(th + w_h * dt)       # line 5, eq. 5.16
    yp = y + v_h / w_h * np.cos(th) - v_h / w_h * np.cos(th + w_h * dt)       # line 6
    tp = th + w_h * dt + g_h * dt                                             # line 7, eq. 5.14
    return np.array([xp, yp, tp])                                             # line 8
```

**Robust.**

```python
def velocity_forward(X, v_h, w_h, g_h, dt):
    """Eq. 5.16 in chord form. X is (3,) or (M, 3); v_h, w_h, g_h broadcast. Exact at w_h = 0."""
    X = np.asarray(X, dtype=float)
    half = 0.5 * w_h * dt
    s = v_h * dt * np.sinc(half / np.pi)        # signed chord length 2 (v/w) sin(w dt / 2); np.sinc(x) = sin(pi x)/(pi x)
    th = X[..., 2]
    return np.stack([X[..., 0] + s * np.cos(th + half),
                     X[..., 1] + s * np.sin(th + half),
                     wrap(th + (w_h + g_h) * dt)], axis=-1)


def sample_motion_model_velocity(u, X, alpha, dt, rng, sample=sample_normal):
    """Table 5.3 for M particles in one call. X is (M, 3)."""
    v, w = u
    a1, a2, a3, a4, a5, a6 = alpha
    M = X.shape[0]
    v_h = v + sample(a1 * v * v + a2 * w * w, rng, M)       # lines 2-4: noise scaled by the COMMANDED v, w
    w_h = w + sample(a3 * v * v + a4 * w * w, rng, M)
    g_h = sample(a5 * v * v + a6 * w * w, rng, M)
    return velocity_forward(X, v_h, w_h, g_h, dt)           # lines 5-7
```

Tricks:

1. **Chord form instead of v̂/ω̂.** Use sin(θ + φ) − sin θ = 2 cos(θ + φ/2) sin(φ/2) with φ = ω̂Δt, and the same for cos. Then lines 5–6 become x′ = x + v̂Δt · sinc(φ/2) · cos(θ + φ/2), with sinc(z) = sin z / z, and the same with sin for y′. Read it as a chord of length v̂Δt · sinc(φ/2), pointing along the mean heading θ + φ/2. Nothing divides by ω̂, so there is no straight-line branch, and the function is smooth through ω̂ = 0, which matters when chapter 7 differentiates it. Against a long-double reference at v = 1 m/s, Δt = 1 s and ω = 10⁻⁹ rad/s, the book's form is off by 4.2 × 10⁻⁸ m (cancellation in the difference of sines), and at ω = 0 it is 0/0. The chord form stays below 2 × 10⁻¹⁶ m from ω = 10⁻⁶ rad/s down to 0.
2. **One call for all M particles** (line 4 of Table 4.3): draw 3M normals at once.
3. **Wrap θ′** before C3, C4 or a sensor model compares it.
4. **Keep γ̂ even when you think α₅ = α₆ = 0.** Without it every sample lies on a 2-D surface in (x, y, θ) (p. 129), and any density evaluated at a pose not produced by this sampler is zero (lecture L3).
5. **Noise scales with the commanded (v, ω)** (eq. 5.10), so a robot commanded to stand still gets no noise at all (C1 trick 2).

**Eigen.**

```cpp
using Pose = Eigen::Vector3d;

inline double sinc(double h) {  // sin(h)/h, Taylor near 0 (error below h^4/120)
  return std::abs(h) < 1e-4 ? 1.0 - h * h / 6.0 : std::sin(h) / h;
}

inline Pose velocity_forward(const Pose& x, double v_h, double w_h, double g_h, double dt) {
  const double half = 0.5 * w_h * dt;
  const double s = v_h * dt * sinc(half);
  return Pose(x(0) + s * std::cos(x(2) + half),
              x(1) + s * std::sin(x(2) + half),
              wrap(x(2) + (w_h + g_h) * dt));
}

// X: one particle per column, updated in place.
inline void sample_motion_model_velocity(double v, double w, Eigen::Matrix3Xd& X,
                                         const std::array<double, 6>& a, double dt,
                                         std::mt19937_64& rng) {
  const double bv = a[0] * v * v + a[1] * w * w;
  const double bw = a[2] * v * v + a[3] * w * w;
  const double bg = a[4] * v * v + a[5] * w * w;
  for (Eigen::Index i = 0; i < X.cols(); ++i) {
    const Pose xi = X.col(i);  // copy: the right-hand side reads the column being written
    X.col(i) = velocity_forward(xi, v + sample_normal(bv, rng), w + sample_normal(bw, rng),
                                sample_normal(bg, rng), dt);
  }
}
```

The copy `xi` keeps `X.col(i)` from being written while the expression still reads it. With fixed-size `Pose` the copy is three doubles on the stack, and there is no heap allocation in the loop.

**Cost.** O(M) per step: three normal draws, one `sinc`, two `sin`/`cos` per particle. The draws cost more than the trigonometry. Nothing in it is quadratic.

**What breaks first.** The naive form's straight-line `nan` (trick 1): straight commands are the most common ones, and `nan` particles drop out of the weight normalization without an error. Next, a Δt that is not the time actually elapsed between the two controls: eq. 5.9 scales the arc by Δt, so a dropped control message stretches every particle.

---

## C3. Velocity model: closed-form density, Table 5.1, eq. 5.17–5.32

**Shapes.** xₜ₋₁ = (x, y, θ) (3,); xₜ = (x′, y′, θ′): one hypothesis (3,) or N hypotheses (N, 3), e.g. the cells of a grid. uₜ = (v, ω) and Δt as in C2. μ, x*, y*, r*, Δθ, v̂, ω̂, γ̂: scalars, or (N,) arrays for N hypotheses. Output: one density per hypothesis. It is a density over the noise variables (v̂, ω̂, γ̂), not over the pose (lecture L9 and trick 5).

**Naive.**

```python
def motion_model_velocity_naive(xt, u, x_prev, alpha, dt, prob=prob_normal_naive):
    xp, yp, tp = xt
    x, y, th = x_prev
    v, w = u
    a1, a2, a3, a4, a5, a6 = alpha
    mu = 0.5 * ((x - xp) * np.cos(th) + (y - yp) * np.sin(th)) / \
               ((y - yp) * np.cos(th) - (x - xp) * np.sin(th))                # line 2, eq. 5.18
    x_s = (x + xp) / 2 + mu * (y - yp)                                        # line 3, eq. 5.19
    y_s = (y + yp) / 2 + mu * (xp - x)                                        # line 4
    r_s = np.sqrt((x - x_s)**2 + (y - y_s)**2)                                # line 5, eq. 5.20
    dtheta = np.arctan2(yp - y_s, xp - x_s) - np.arctan2(y - y_s, x - x_s)   # line 6, eq. 5.21
    v_h = dtheta / dt * r_s                                                   # line 7, eq. 5.24
    w_h = dtheta / dt                                                         # line 8
    g_h = (tp - th) / dt - w_h                                                # line 9, eq. 5.25
    return (prob(v - v_h, a1 * v**2 + a2 * w**2)                              # line 10, eq. 5.32
            * prob(w - w_h, a3 * v**2 + a4 * w**2)
            * prob(g_h, a5 * v**2 + a6 * w**2))
```

**Robust.**

```python
def velocity_inverse(X, Xp, dt):
    """Table 5.1 lines 2-9 in chord form: the (v_h, w_h, g_h) that carry X to Xp in dt.
    X is (3,); Xp is (3,) or (N, 3). Valid for |w_h dt| < pi (less than a half turn per step)."""
    X, Xp = np.asarray(X, dtype=float), np.asarray(Xp, dtype=float)
    dx, dy, th = Xp[..., 0] - X[0], Xp[..., 1] - X[1], X[2]
    c = dx * np.cos(th) + dy * np.sin(th)           # displacement along the initial heading
    l = -dx * np.sin(th) + dy * np.cos(th)          # displacement to the left of it
    half = np.arctan2(l, c)                          # chord direction relative to the heading ...
    half = np.where(half > np.pi / 2, half - np.pi, np.where(half < -np.pi / 2, half + np.pi, half))
    #                                                ... folded to (-pi/2, pi/2]: reversing is not a half turn
    sgn = np.where(c < 0, -1.0, 1.0)                 # forward or reverse: the sign line 7 loses
    v_h = sgn * np.hypot(dx, dy) / (dt * np.sinc(half / np.pi))
    w_h = 2 * half / dt
    g_h = wrap(Xp[..., 2] - th - 2 * half) / dt     # line 9, wrapped
    return v_h, w_h, g_h


STEP_EPS = 0.01           # m; floor on |v_h| dt before dividing by the Jacobian (trick 5)


def velocity_jacobian_det(v_h, w_h, dt):
    """|det d(x', y', theta') / d(v_h, w_h, g_h)| of eq. 5.16 (from outside the book)."""
    return np.abs(v_h) * dt**4 * np.sinc(w_h * dt / (2 * np.pi))**2 / 2


def log_motion_model_velocity(Xp, u, X, alpha, dt, log_prob=log_prob_normal, pose_density=False):
    v, w = u
    a1, a2, a3, a4, a5, a6 = alpha
    v_h, w_h, g_h = velocity_inverse(X, Xp, dt)
    lp = (log_prob(v - v_h, a1 * v * v + a2 * w * w)          # line 10, as a sum of logs
          + log_prob(w - w_h, a3 * v * v + a4 * w * w)
          + log_prob(g_h, a5 * v * v + a6 * w * w))
    if pose_density:                                           # trick 5
        lp = lp - np.log(velocity_jacobian_det(np.maximum(np.abs(v_h), STEP_EPS / dt), w_h, dt))
    return lp
```

Tricks:

1. **The sign of v̂ (line 7).** r* is a distance, so it is positive, and Δθ carries the sign of the turn. Line 7 therefore gives v̂ the sign of ω̂, not the sign of the motion. In this repo, the end poses of (v, ω) = (1, −0.5), (−1, 0.5) and (1, 0.5) at Δt = 1 s give v̂ = −1.0, 1.0 and 1.0 m/s from line 7, against 1.0, −1.0 and 1.0 m/s from `velocity_inverse`. For (1, −0.5) with the moderate α of Fig L5a, (0.02, 0.02, 0.02, 0.02, 0.005, 0.005), the book's density at the noise-free end pose is e⁻⁸⁰ times the corrected one. The chord form takes the sign from c, the displacement along the initial heading. If you would rather keep the book's lines 2–6, the one-line patch is v̂ = λ Δθ / Δt with λ = (y* − y) cos θ − (x* − x) sin θ. λ is the signed radius from the first equality of eq. 5.17, and it gives the same v̂ as the chord form on the three cases above.
2. **No straight-line branch.** Line 2 divides by (y − y′) cos θ − (x − x′) sin θ, which is zero for a straight move: the centre is at infinity (p. 130). Run here: at ω = 0 the naive density is `nan`, and at ω = 10⁻⁹ rad/s its v̂ is off by 1.4 × 10⁻⁷ relative. In the chord form c and l stay finite. Its round trip `velocity_inverse(velocity_forward(…))` returns (v̂, ω̂, γ̂) to within 5.4 × 10⁻¹² over 20 000 random cases, including ω̂ = 0 and reversing.
3. **Wrap the angles.** Line 6 is a difference of two `atan2` values and line 9 a difference of headings; both jump by 2π at the seam. The chord form has only one angle difference, θ′ − θ − ω̂Δt in line 9, and wraps it.
4. **Log domain, summed** (C1 trick 1). A grid over (x′, y′, θ′) has most of its cells far out in the tails.
5. **The Jacobian, when you need a density over poses.** Eq. 5.32 scores the noise, not the pose. To make it a density over (x′, y′, θ′), divide by |det ∂(x′, y′, θ′)/∂(v̂, ω̂, γ̂)| = |v̂| Δt⁴ sinc²(ω̂Δt/2) / 2. Derivation: γ̂ enters only the θ′ row, as γ̂Δt, so the determinant is Δt times that of the x–y block, and the x–y block's determinant is v̂Δt(1 − cos ω̂Δt)/ω̂². The formula agrees with a central-difference Jacobian (`scripts/fd_check.py`'s `numeric_jacobian`) to 3.1 × 10⁻⁹ relative over ten random cases. With it, the density integrates to 0.9999 over an (x′, y′, θ′) grid for the Fig L5a setting (u = (1.0 m/s, 0.8 rad/s), Δt = 2.0 s). The pose density goes as 1/|v̂| near the start position. That singularity is integrable, but a grid cell sitting on it gets an absurd value, so floor |v̂|Δt at 1 cm before dividing (`STEP_EPS`). You need the Jacobian only where Table 5.1 is used as a transition table (grid localization, ch. 8); a particle filter only samples. This is from outside the book.
6. **Domain.** The chord form, like the book's wrapped line 6, assumes less than a half turn per step, |ω̂Δt| < π. At 10 Hz that means |ω| < 31 rad/s.

**Eigen.**

```cpp
struct VelocityNoise { double v_h, w_h, g_h; };

inline VelocityNoise velocity_inverse(const Pose& x, const Pose& xp, double dt) {
  const double dx = xp(0) - x(0), dy = xp(1) - x(1), c0 = std::cos(x(2)), s0 = std::sin(x(2));
  const double c = dx * c0 + dy * s0, l = -dx * s0 + dy * c0;
  double half = std::atan2(l, c);
  if (half > M_PI / 2) half -= M_PI; else if (half < -M_PI / 2) half += M_PI;
  const double sgn = c < 0.0 ? -1.0 : 1.0;
  const double w_h = 2.0 * half / dt;
  return {sgn * std::hypot(dx, dy) / (dt * sinc(half)), w_h, wrap(xp(2) - x(2) - 2.0 * half) / dt};
}

inline double log_motion_model_velocity(const Pose& xp, double v, double w, const Pose& x,
                                        const std::array<double, 6>& a, double dt) {
  const VelocityNoise n = velocity_inverse(x, xp, dt);
  return log_prob_normal(v - n.v_h, a[0] * v * v + a[1] * w * w) +
         log_prob_normal(w - n.w_h, a[2] * v * v + a[3] * w * w) +
         log_prob_normal(n.g_h, a[4] * v * v + a[5] * w * w);
}
```

**Cost.** O(1) per hypothesis: one `atan2`, one `hypot`, one `sinc`, three logs. Grid localization (ch. 8) is where it gets expensive. The full transition sums over every pair of cells, O(N²) per step for N cells; the usual fix is to evaluate it only within a few standard deviations of each source cell.

**What breaks first.** Straight-line `nan`s (a whole grid row lost), right turns scored as nearly impossible (a belief that will not follow the robot through right-hand turns) and the ±π seam: tricks 2, 1 and 3. The one no trick fixes is a spin in place (v̂ = 0). The position does not move, so the inverse model gets ω̂ = 0 and books all of the rotation as γ̂; the map from noise to pose is singular there (trick 5's determinant is zero at v̂ = 0). A correctly executed spin therefore scores as a large γ̂ error, scaled by α₅v² + α₆ω².

---

## C4. Odometry model: decomposition, density and sampler, Tables 5.5 and 5.6, eq. 5.33–5.46

**Shapes.** uₜ = (x̄ₜ₋₁, x̄ₜ): two odometry poses (3,) each, in the odometer's own frame, whose relation to the world frame is unknown (p. 134). xₜ₋₁: one pose (3,) or M particles (M, 3). xₜ: one hypothesis (3,) or N of them (N, 3). δrot1, δrot2 in rad, δtrans in m. alpha = (α₁, α₂, α₃, α₄): α₁ and α₃ dimensionless, α₂ in rad²/m², α₄ in m²/rad² (lecture L6).

**Naive.**

```python
def motion_model_odometry_naive(xt, u, x_prev, alpha, prob=prob_normal_naive):
    (xb, yb, tb), (xbp, ybp, tbp) = u
    x, y, th = x_prev
    xp, yp, tp = xt
    a1, a2, a3, a4 = alpha
    d_rot1 = np.arctan2(ybp - yb, xbp - xb) - tb                              # line 2, eq. 5.34
    d_trans = np.sqrt((xb - xbp)**2 + (yb - ybp)**2)                          # line 3, eq. 5.35
    d_rot2 = tbp - tb - d_rot1                                                # line 4, eq. 5.36
    dh_rot1 = np.arctan2(yp - y, xp - x) - th                                 # line 5
    dh_trans = np.sqrt((x - xp)**2 + (y - yp)**2)                             # line 6
    dh_rot2 = tp - th - dh_rot1                                               # line 7
    p1 = prob(d_rot1 - dh_rot1, a1 * dh_rot1**2 + a2 * dh_trans**2)                     # line 8
    p2 = prob(d_trans - dh_trans, a3 * dh_trans**2 + a4 * dh_rot1**2 + a4 * dh_rot2**2)  # line 9
    p3 = prob(d_rot2 - dh_rot2, a1 * dh_rot2**2 + a2 * dh_trans**2)                     # line 10
    return p1 * p2 * p3                                                       # line 11


def sample_motion_model_odometry_naive(u, x_prev, alpha, rng, sample=sample_normal_naive):
    (xb, yb, tb), (xbp, ybp, tbp) = u
    x, y, th = x_prev
    a1, a2, a3, a4 = alpha
    d_rot1 = np.arctan2(ybp - yb, xbp - xb) - tb                              # line 2
    d_trans = np.sqrt((xb - xbp)**2 + (yb - ybp)**2)                          # line 3
    d_rot2 = tbp - tb - d_rot1                                                # line 4
    dh_rot1 = d_rot1 - sample(a1 * d_rot1**2 + a2 * d_trans**2, rng)                     # line 5, eq. 5.37
    dh_trans = d_trans - sample(a3 * d_trans**2 + a4 * d_rot1**2 + a4 * d_rot2**2, rng)  # line 6, eq. 5.38
    dh_rot2 = d_rot2 - sample(a1 * d_rot2**2 + a2 * d_trans**2, rng)                     # line 7, eq. 5.39
    xp = x + dh_trans * np.cos(th + dh_rot1)                                  # line 8, eq. 5.40
    yp = y + dh_trans * np.sin(th + dh_rot1)                                  # line 9
    tp = th + dh_rot1 + dh_rot2                                               # line 10
    return np.array([xp, yp, tp])                                             # line 11
```

**Robust.**

```python
TRANS_EPS = 0.01          # m; below this a step counts as a rotation in place (ROS amcl uses the same 1 cm)


def odometry_params(P0, P1):
    """Eq. 5.34-5.36, wrapped, with the rotate-in-place rule. P0 is (3,); P1 is (3,) or (N, 3)."""
    P0, P1 = np.asarray(P0, dtype=float), np.asarray(P1, dtype=float)
    dx, dy = P1[..., 0] - P0[..., 0], P1[..., 1] - P0[..., 1]
    trans = np.hypot(dx, dy)
    rot1 = np.where(trans < TRANS_EPS, 0.0, wrap(np.arctan2(dy, dx) - P0[..., 2]))
    rot2 = wrap(P1[..., 2] - P0[..., 2] - rot1)
    return rot1, trans, rot2


def rot_for_noise(rot):
    """Size of a rotation measured from straight ahead or straight back, whichever is closer (as amcl does)."""
    return np.minimum(np.abs(rot), np.abs(wrap(rot - np.pi)))


def odometry_variances(rot1, trans, rot2, alpha):
    """The three variances of eq. 5.37-5.39 (measured deltas), reverse-symmetric."""
    a1, a2, a3, a4 = alpha
    n1, n2 = rot_for_noise(rot1), rot_for_noise(rot2)
    return (a1 * n1**2 + a2 * trans**2,
            a3 * trans**2 + a4 * (n1**2 + n2**2),
            a1 * n2**2 + a2 * trans**2)


def sample_motion_model_odometry(u, X, alpha, rng, sample=sample_normal):
    """Table 5.6 for M particles. u = (odom_prev, odom_now); X is (M, 3)."""
    rot1, trans, rot2 = odometry_params(*u)                                   # lines 2-4
    b1, b2, b3 = odometry_variances(rot1, trans, rot2, alpha)
    M = X.shape[0]
    h_rot1 = rot1 - sample(b1, rng, M)                                        # lines 5-7
    h_trans = trans - sample(b2, rng, M)
    h_rot2 = rot2 - sample(b3, rng, M)
    th = X[:, 2]
    return np.stack([X[:, 0] + h_trans * np.cos(th + h_rot1),                 # lines 8-10
                     X[:, 1] + h_trans * np.sin(th + h_rot1),
                     wrap(th + h_rot1 + h_rot2)], axis=-1)


def log_motion_model_odometry(Xp, u, X, alpha, log_prob=log_prob_normal, pose_density=False):
    """Table 5.5 with eq. 5.44-5.46's variances. X is (3,); Xp is (3,) or (N, 3)."""
    rot1, trans, rot2 = odometry_params(*u)                                   # lines 2-4
    h_rot1, h_trans, h_rot2 = odometry_params(X, Xp)                          # lines 5-7
    b1, b2, b3 = odometry_variances(rot1, trans, rot2, alpha)                 # measured deltas: trick 4
    lp = (log_prob(wrap(rot1 - h_rot1), b1)                                   # lines 8-11, as a sum of logs
          + log_prob(trans - h_trans, b2)
          + log_prob(wrap(rot2 - h_rot2), b3))
    if pose_density:                                                          # trick 5
        lp = lp - np.log(np.maximum(h_trans, TRANS_EPS))
    return lp
```

Tricks:

1. **Wrap every angle and every angular difference:** lines 2, 4, 5 and 7, and the errors in lines 8 and 10. The book says it for δrot2 − δ̂rot2 (p. 135, printed there as δrot2 − δ̄rot2) and calls it "a common error that tends to be difficult to debug". Lecture L6 measures what it loses at θ̄′ near 180°.
2. **Rotation in place: δrot1 = 0 below `TRANS_EPS`.** With δtrans = 0, line 2 is atan2(0, 0). NumPy returns 0, so δrot1 = −θ̄, and the noise then depends on which way the odometry frame happens to point. In this repo, with the α of lecture L7, (0.01, 0.0005, 0.01, 0.0005), a 30° turn in place at θ̄ = 150° gives δrot1 = −150.0° from the book's lines, and 10⁵ samples have a heading standard deviation of 0.409 rad. With the threshold it is 0.052 rad, the same at any θ̄. Apply the same function to the hypothesis (lines 5–7) so that the density and the sampler agree.
3. **Reversing is not a half turn.** For a straight move backwards, δrot1 = δrot2 = ±π, and α₁δ²rot1 blows up the noise. In this repo, 0.5 m straight back with α = (0.01, 0.0005, 0.01, 0.0005) (lecture L7) gives a heading standard deviation of 0.445 rad with the book's variances and 0.0158 rad with `rot_for_noise`, the same as 0.5 m forward (0.0158 rad). The decomposition itself is unchanged; only the size used in the variances is measured from the nearer of straight ahead and straight back. ROS amcl's differential-drive odometry model does the same. A tracked robot reverses all the time, so this is not a corner case for you.
4. **Use the measured δ in the variances, as eq. 5.44–5.46 do.** Table 5.5 lines 8–10 use the hypothesized δ̂, but the derivation they come from (p. 139, eq. 5.44–5.46) and the sampler (Table 5.6 lines 5–7) both use the measured δ. With δ, the density and the sampler describe one distribution. Lecture L9 measures the difference against the sampler. The naive block keeps the table's δ̂ so you can read it against the book.
5. **Divide by δ̂trans for a density over poses.** For eq. 5.40, |det ∂(x′, y′, θ′)/∂(δ̂rot1, δ̂trans, δ̂rot2)| = δ̂trans: the θ′ row is (1, 0, 1), and the x–y block's two columns, δ̂trans(−sin, cos) and (cos, sin), are orthogonal with norms δ̂trans and 1. It agrees with central differences to 5.6 × 10⁻¹⁰ relative over ten random cases. With it, `log_motion_model_odometry` integrates to 0.9995 over a grid for the L9 odometry pair. Floor δ̂trans at `TRANS_EPS` before dividing, for the same reason as in C3. As in C3, you need it for a grid transition table, not for particles. This is from outside the book.
6. **Keep the last odometry pose you used, not a sum of δs.** If odometry arrives at 50 Hz and the filter predicts at 10 Hz, make the pair (x̄ at the last predict, x̄ now) and decompose that. Summing three δs from each 20 ms step and calling the result one step is wrong: δrot1 of a later step is measured from a different heading.
7. **Log domain, summed** (C1).

**Eigen.**

```cpp
constexpr double kTransEps = 0.01;  // m

struct OdomParams { double rot1, trans, rot2; };

inline OdomParams odometry_params(const Pose& p0, const Pose& p1) {
  const double dx = p1(0) - p0(0), dy = p1(1) - p0(1);
  const double trans = std::hypot(dx, dy);
  const double rot1 = trans < kTransEps ? 0.0 : wrap(std::atan2(dy, dx) - p0(2));
  return {rot1, trans, wrap(p1(2) - p0(2) - rot1)};
}

inline double rot_for_noise(double r) { return std::min(std::abs(r), std::abs(wrap(r - M_PI))); }

inline Eigen::Vector3d odometry_variances(const OdomParams& d, const std::array<double, 4>& a) {
  const double n1 = rot_for_noise(d.rot1), n2 = rot_for_noise(d.rot2), t2 = d.trans * d.trans;
  return {a[0] * n1 * n1 + a[1] * t2, a[2] * t2 + a[3] * (n1 * n1 + n2 * n2), a[0] * n2 * n2 + a[1] * t2};
}

inline void sample_motion_model_odometry(const Pose& odom0, const Pose& odom1, Eigen::Matrix3Xd& X,
                                         const std::array<double, 4>& a, std::mt19937_64& rng) {
  const OdomParams d = odometry_params(odom0, odom1);
  const Eigen::Vector3d b = odometry_variances(d, a);
  for (Eigen::Index i = 0; i < X.cols(); ++i) {
    const double r1 = d.rot1 - sample_normal(b(0), rng);
    const double tr = d.trans - sample_normal(b(1), rng);
    const double r2 = d.rot2 - sample_normal(b(2), rng);
    const double th = X(2, i);
    X(0, i) += tr * std::cos(th + r1);
    X(1, i) += tr * std::sin(th + r1);
    X(2, i) = wrap(th + r1 + r2);
  }
}

inline double log_motion_model_odometry(const Pose& xp, const Pose& odom0, const Pose& odom1,
                                        const Pose& x, const std::array<double, 4>& a) {
  const OdomParams d = odometry_params(odom0, odom1), h = odometry_params(x, xp);
  const Eigen::Vector3d b = odometry_variances(d, a);
  return log_prob_normal(wrap(d.rot1 - h.rot1), b(0)) + log_prob_normal(d.trans - h.trans, b(1)) +
         log_prob_normal(wrap(d.rot2 - h.rot2), b(2));
}
```

`th` is read before X(2, i) is overwritten. The order of the three updates matters, and the per-column loop makes it visible; a column-block expression would hide it.

**Cost.** O(M) per sampling step and O(1) per density evaluation, with the same constants as C2 and C3. Lines 2–4 (the measured δ) depend only on uₜ, so the robust versions compute them once per step, not once per particle.

**What breaks first.** The unwrapped δrot2 error (trick 1): density lost only for headings near ±π, which is why it is hard to find. Then rotation in place and reversing (tricks 2, 3), and δ̂ variances that make a grid filter and a particle filter disagree on the same data (trick 4). The one that is not a code problem: α₁–α₄ tuned on a smooth floor, so the robot on grass or carpet drifts outside the belief (T5).

---

## C5. Motion with a map, Table 5.7, eq. 5.47–5.51

**Shapes.** m: a map that answers p(xₜ ∣ m) for a pose. In practice this is a boolean free-space test in configuration space: the obstacles grown by the robot radius (p. 141). A distance transform of the occupancy grid makes it O(1) per pose: free if the distance is greater than the robot radius. xₜ₋₁: (M, 3). π: (M,), the importance factor. `sampler(u, X, rng)` is any sampler with α and Δt bound in (C2 or C4).

**Naive.**

```python
def motion_model_with_map_naive(xt, u, x_prev, m, motion_model, p_map):
    return motion_model(xt, u, x_prev) * p_map(xt, m)                         # line 2, eq. 5.48 without eta


def sample_motion_model_with_map_naive(u, x_prev, m, sampler, p_map, rng):
    while True:                                                               # line 2: do
        xt = sampler(u, x_prev[None, :], rng)[0]                              # line 3
        pi = p_map(xt, m)                                                     # line 3 (printed twice)
        if pi > 0:                                                            # line 4: until pi > 0
            return xt, pi                                                     # line 5
```

**Robust.**

```python
def log_motion_model_with_map(Xp, u, X, log_motion_model, in_free):
    """Eq. 5.48 up to eta: the motion density in free space, -inf in occupied space."""
    return np.where(in_free(Xp), log_motion_model(Xp, u, X), -np.inf)


def sample_motion_model_with_map(u, X, sampler, in_free, rng, max_tries=10):
    """Table 5.7 for M particles: redraw only those in occupied space, at most max_tries draws each.
    Returns the new particles and pi (1 in free space, 0 where every draw failed)."""
    Xn = sampler(u, X, rng)
    ok = np.asarray(in_free(Xn), dtype=bool)
    for _ in range(max_tries - 1):
        if ok.all():
            break
        bad = ~ok
        Xn[bad] = sampler(u, X[bad], rng)
        ok[bad] = in_free(Xn[bad])
    return Xn, ok.astype(float)
```

Tricks:

1. **Cap the retries** (p. 141: "care has to be taken … to ensure termination"). A particle whose whole motion cloud lies in an obstacle never leaves the loop. After `max_tries`, return the last draw with π = 0; resampling removes it. On open ground ten failures in a row are rare (lecture L8); in a narrow corridor, or with a particle that is already inside a wall after a kidnap, it is not small.
2. **Redraw only the failures, all at once.** Each round costs one vectorized sampler call on the failing subset, not one Python loop iteration per particle.
3. **Rejection keeps η; a single draw weighted by π does not.** Eq. 5.48 normalizes per xₜ₋₁. Redrawing until the sample is free samples exactly that normalized conditional. Drawing once and using π as the weight is cheaper, but it penalizes a particle next to a wall by the fraction of its motion cloud that is blocked, which is a different model. Pick one on purpose. The capped loop is between the two: it matches rejection unless all `max_tries` draws fail.
4. **The end-pose check lets the robot through walls** (eq. 5.51 drops the path, p. 143). Lecture L8 measures how often, and how fast it falls with more checks per step. The fix is the book's own: keep the step shorter than the thinnest wall, i.e. predict often. With the velocity model you can also call `velocity_forward` at fractions of Δt with the same (v̂, ω̂) and check each point, which costs one map lookup per point.
5. **Configuration space once, at map load.** Grow the obstacles by the robot radius (a distance transform) when the map is loaded, not per particle.

**Eigen.**

```cpp
// Sampler: void(Eigen::Matrix3Xd&), moves the columns it is given in place (C2 or C4 with u, alpha bound).
// InFree:  bool(const Pose&).
template <class Sampler, class InFree>
Eigen::VectorXd sample_motion_model_with_map(Eigen::Matrix3Xd& X, Sampler&& sampler, InFree&& in_free,
                                             int max_tries = 10) {
  const Eigen::Matrix3Xd X0 = X;  // x_{t-1}, kept for redraws
  sampler(X);
  Eigen::VectorXd pi(X.cols());
  for (Eigen::Index i = 0; i < X.cols(); ++i) {
    pi(i) = in_free(Pose(X.col(i))) ? 1.0 : 0.0;
    for (int k = 1; k < max_tries && pi(i) == 0.0; ++k) {
      Eigen::Matrix3Xd xi = X0.col(i);  // one column, redrawn from x_{t-1}
      sampler(xi);
      X.col(i) = xi;
      pi(i) = in_free(Pose(xi)) ? 1.0 : 0.0;
    }
  }
  return pi;
}
```

**Cost.** Expected draws per particle: 1/(acceptance rate), capped at `max_tries`; one map lookup per draw, two to ten more with the path check of trick 4. The density costs one lookup on top of C3 or C4.

**What breaks first.** The infinite loop the first time a particle sits in an obstacle (trick 1, after a kidnap or a bad initialization), then tunnelling on a long step (trick 4). Then a map without the robot radius (trick 5 skipped), so particles hug walls the robot cannot reach. And η handled by accident (trick 3): a belief that shies away from walls, or one that does not, with no one having chosen which.
