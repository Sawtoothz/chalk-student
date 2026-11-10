---
source: sola-microlie
unit: 1
stage: cards
code_refs: code_refs.json
---

# Equation → code cards: a micro Lie theory

Nine cards, in the order you would build a small Lie library and then use it: SO(3) Exp/Log (C1), ⊕/⊖ and the
adjoint (C2), the Jacobians of SO(3) and the elementary blocks (C3), SE(2) (C4), SE(3) (C5), covariance and
integration (C6), composite states (C7), the ESKF of §V-A (C8), and the Gauss-Newton smoother of §V-B/C (C9).
Equation and page numbers are the paper's (arXiv:1812.01537v9; PDF page = printed page).

**Conventions used in every snippet.** Right perturbations, 𝒳 ⊕ τ = 𝒳 Exp(τ), as in the paper. SE(n) tangents are
τ = (ρ, θ), translation first (153), (169). The paper's process noise **W** (93) is `R_proc` and its measurement
noise **N** (96) is `Q_meas`; a bare `R` is always a rotation matrix. Planar angles come out of `arctan2`, so they are
already wrapped to (−π, π]; an angle difference that does not go through Log is wrapped with `wrap()` from the
package's `models.py`.

**How these cards are checked.** `figures/check_cards.py` extracts every `python` block of this file in order, runs
them as one module, and checks every Jacobian against central finite differences of definition (41a), through
`scripts/fd_check.py` (its own SO(3)/SE(3) Exp/Log for the 3D groups; `scipy.linalg.expm`/`logm` for SE(2)). It also
compiles every `cpp` block with `g++ -fsyntax-only` against Eigen 3, and writes the numbers quoted below to
`figures/card_numbers.json`. Reference values for the precision measurements come from `mpmath` at 50 digits.

**Reference code.** The paper's own library is manif (ref. [7]), https://github.com/artivis/manif, pinned at commit
`65166b3bfd15`, **MIT licence**. The examples of §V are in its `examples/` folder. For the small-angle thresholds
the lecture (L17) promised, GTSAM is anchored too: https://github.com/borglab/gtsam at `8806b336af5a`, **BSD
licence**. Both licences allow copying with the notice kept. The snippets here are still written from the
equations (clean-room) so that each line maps to an equation number, not to a library's internal layout. Every
`path:line` below is recorded in `code_refs.json`, and line numbers are for those commits only.

---

## C1. SO(3) and S³: hat, vee, Exp and Log, Ex. 3–5, (132)–(135), (138)

**Shapes.** θ ∈ ℝ³ (angle-axis, θ = uθ, θ = ‖θ‖). [θ]ₓ = θ^ ∈ 𝔰𝔬(3) is 3×3 skew. R ∈ SO(3) is 3×3. q = (w, v) ∈ S³ is a
4-vector, w scalar, v ∈ ℝ³, ‖q‖ = 1. Exp: ℝ³ → SO(3) or S³; Log: back to ℝ³.

**Naive (reads like the paper).**

```python
import math
import numpy as np
from types import SimpleNamespace
from scipy.linalg import cho_factor, cho_solve

def so3_hat(w):                                   # Ex. 3: [w]x
    return np.array([[0.0, -w[2], w[1]], [w[2], 0.0, -w[0]], [-w[1], w[0], 0.0]])

def so3_vee(W):                                   # Ex. 3: ([w]x)^v = w
    return np.array([W[2, 1], W[0, 2], W[1, 0]])

def so3_exp_naive(theta):                         # (134), Ex. 4
    th = np.linalg.norm(theta)
    U = so3_hat(theta / th)                       # 0/0 at th = 0
    return np.eye(3) + np.sin(th) * U + (1 - np.cos(th)) * U @ U

def so3_log_naive(R):                             # (135)
    th = np.arccos((np.trace(R) - 1) / 2)         # loses all digits near 0 and near pi
    return th * so3_vee(R - R.T) / (2 * np.sin(th))
```

**Robust.**

```python
def coef_a(th):              # (1 - cos th)/th^2, the [θ]x coefficient of (143)
    return 0.5 * np.sinc(th / (2 * np.pi)) ** 2   # = 2 sin^2(th/2)/th^2, no subtraction

def coef_b(th):              # (th - sin th)/th^3, the [θ]x^2 coefficient of (143); even in th
    th = abs(th)
    if th < 0.3:             # sum_k (-1)^k th^2k / (2k+3)!
        return sum((-1) ** k * th ** (2 * k) / math.factorial(2 * k + 3) for k in range(5))
    return (th - np.sin(th)) / th ** 3

def so3_exp(theta):                               # (134) as R = I + A W + B W^2
    th = np.linalg.norm(theta)
    W = so3_hat(theta)
    return np.eye(3) + np.sinc(th / np.pi) * W + coef_a(th) * W @ W

def quat_exp(theta):                              # (132): (cos th/2, u sin th/2)
    th = np.linalg.norm(theta)
    return np.r_[np.cos(th / 2), 0.5 * np.sinc(th / (2 * np.pi)) * theta]

def quat_log(q):                                  # (133) with the w > 0 rule
    w, v = (q[0], q[1:]) if q[0] >= 0 else (-q[0], -q[1:])
    n = np.linalg.norm(v)
    if n == 0.0:
        return np.zeros(3)
    return 2 * np.arctan2(n, w) / n * v

def quat_mul(p, q):                               # Hamilton product, q_a q_b
    pw, pv, qw, qv = p[0], p[1:], q[0], q[1:]
    return np.r_[pw * qw - pv @ qv, pw * qv + qw * pv + np.cross(pv, qv)]

def quat_to_R(q):                                 # (138)
    w, x, y, z = q
    return np.array([[w*w + x*x - y*y - z*z, 2*(x*y - w*z), 2*(x*z + w*y)],
                     [2*(x*y + w*z), w*w - x*x + y*y - z*z, 2*(y*z - w*x)],
                     [2*(x*z - w*y), 2*(y*z + w*x), w*w - x*x - y*y + z*z]])

def R_to_quat(R):                                 # Shepperd: pivot on the largest of tr, R00, R11, R22
    tr = np.trace(R)
    i = int(np.argmax([tr, R[0, 0], R[1, 1], R[2, 2]]))
    if i == 0:
        w = 0.5 * np.sqrt(1 + tr)
        v = 0.25 / w * np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    else:
        j = i - 1; k = (j + 1) % 3; l = (j + 2) % 3
        r = np.sqrt(1 + 2 * R[j, j] - tr)         # = 2 |v_j|, never near zero here
        v = np.empty(3); v[j] = 0.5 * r; s = 0.5 / r
        v[k] = s * (R[k, j] + R[j, k]); v[l] = s * (R[l, j] + R[j, l])
        w = s * (R[l, k] - R[k, l])
    return np.r_[w, v] if w >= 0 else -np.r_[w, v]

def so3_log(R):                                   # (135), computed through the quaternion
    return quat_log(R_to_quat(R))
```

Tricks, each one named:

1. **Half-angle form of 1 − cos θ.** (1 − cos θ)/θ² = ½ (sin(θ/2)/(θ/2))². No subtraction, so it keeps full relative
   precision at every θ, and `np.sinc` handles θ = 0 without a branch. Written as printed, the coefficient is
   0 in float64 below θ = 1.0 × 10⁻⁸ rad (lecture L17).
2. **Series for (θ − sin θ)/θ³ below 0.3.** This one has no subtraction-free closed form. Five Taylor terms below the
   switch, the formula above it, where the cancellation costs only a couple of digits. The run measures the worst
   relative error of `coef_a` and `coef_b` over θ ∈ [10⁻¹², π] at 3.3 × 10⁻¹⁶ and 4.0 × 10⁻¹⁵ (`card_numbers.json`,
   `C1_coef_relerr`).
3. **Log through the quaternion, never through arccos.** arccos((tr R − 1)/2) has an infinite slope at both ends:
   near θ = 0 it returns 0 and (135) divides 0 by 0; near θ = π, R − Rᵀ → 0 and sin θ → 0 together. Shepperd's
   pivot picks the largest of four square roots, so no square root is taken of a small number; atan2(‖v‖, w) is
   accurate at both ends. Measured on `Log(Exp(θ))` over 20 random axes (`C1_log_error`): at θ = 10⁻⁹ the naive Log returns
   NaN and the robust one returns θ exactly; at θ = π − 10⁻³ the naive one is off by 2.1 × 10⁻⁹ rad, and at
   θ = π − 10⁻⁷ by 0.16 rad, while the robust one stays below 6.4 × 10⁻¹⁶ rad at both.
4. **The w ≥ 0 rule.** S³ double-covers SO(3) (p. 15); flipping q → −q before Log makes Log return the short rotation,
   θ ∈ [0, π].
5. **Renormalize quaternions after products.** ‖q‖ drifts by rounding in long integrations; manif rescales when
   |‖q‖² − 1| exceeds its eps (see below), which costs one multiply.

**Eigen.**

```cpp
inline Eigen::Matrix3d hat(const Eigen::Vector3d& w) {
  Eigen::Matrix3d W;
  W << 0, -w.z(), w.y(),  w.z(), 0, -w.x(),  -w.y(), w.x(), 0;
  return W;
}
inline double coefA(double th) {            // (1 - cos th)/th^2, half-angle form
  if (th == 0.0) return 0.5;
  const double s = std::sin(0.5 * th) / (0.5 * th);
  return 0.5 * s * s;
}
inline double coefB(double th) {            // (th - sin th)/th^3, even in th
  th = std::abs(th);
  if (th < 0.3) {                           // sum_k (-1)^k th^2k / (2k+3)!
    double sum = 0, term = 1.0 / 6, t2 = th * th;
    for (int k = 0; k < 5; ++k) { sum += term; term *= -t2 / ((2*k + 4) * (2*k + 5)); }
    return sum;
  }
  return (th - std::sin(th)) / (th * th * th);
}
inline Eigen::Matrix3d so3Exp(const Eigen::Vector3d& theta) {   // (134)
  const double th = theta.norm();
  const Eigen::Matrix3d W = hat(theta);
  const double A = th == 0.0 ? 1.0 : std::sin(th) / th;
  return Eigen::Matrix3d::Identity() + A * W + coefA(th) * (W * W);
}
inline Eigen::Vector3d so3Log(const Eigen::Matrix3d& R) {        // (135) via Shepperd + (133)
  Eigen::Quaterniond q(R);                  // Eigen's constructor pivots like Shepperd
  if (q.w() < 0) q.coeffs() *= -1.0;        // the w > 0 rule
  const double n = q.vec().norm();
  if (n == 0.0) return Eigen::Vector3d::Zero();
  return 2.0 * std::atan2(n, q.w()) / n * q.vec();
}
```

**Cost per step.** Exp: one sin, one sin of θ/2, one 3×3 product (W·W, 27 multiply-adds). Log: one square root, one
atan2, a handful of additions. Storing a rotation as a quaternion makes Log cheaper (no conversion) and Exp cheaper (no 3×3 product).

**What breaks first.** (1) Exp or Log called at exactly θ = 0 with the printed formula: NaN, usually at the first
prediction of a robot standing still. (2) Log near π via (135): 0.16 rad wrong at θ = π − 10⁻⁷ (trick 3); it appears as soon as a heading error of 180° is possible (a relocalization, a loop closure). (3) A
non-unit quaternion after thousands of products, which slowly scales every rotated vector.

**In the original code.** manif stores SO(3) as a unit quaternion, so `SO3TangentBase::exp` at
`include/manif/impl/so3/SO3Tangent_base.h:119` builds an `AngleAxis`, with the small-angle branch at
`if (theta_sq > Constants<Scalar>::eps)`, line 128, returning (θ/2, 1) unnormalized below it. `SO3Base::log` at
`include/manif/impl/so3/SO3_base.h:185` is (133): the branch at `:194` compares sin²(θ/2) with eps, and the
authors' comment above `:210` explains the w < 0 case, solved by `atan2(-sin_angle, -cos_angle)`, which is the
w > 0 rule of p. 15 without flipping q. The eps is `std::numeric_limits<_Scalar>::epsilon()*_Scalar(100)`
(`include/manif/constants.h:50`), 2.2 × 10⁻¹⁴, compared with θ², so manif switches to the series at
θ = 1.5 × 10⁻⁷ rad. Renormalization after a product is `approxSqrtInv(ret_sqnorm)` at `SO3_base.h:291`. GTSAM's
`SO3::Logmap` at `gtsam/geometry/SO3.cpp:337` starts with the comment at `:344`, "Convert R to a quaternion (w, v)
with Shepperd's method, pivoting on whichever of {tr, R00, R11, R22} is largest so the square root is never taken
of a near-zero quantity", and canonicalizes w at `:384`. That is the robust Log above.
https://github.com/artivis/manif/blob/65166b3bfd15b1020c29f3eaf6888e1009c79aea/include/manif/impl/so3/SO3_base.h#L185-L240

---

## C2. Plus, minus and the adjoint, (25)–(34), (139), (159), (175)

**Shapes.** 𝒳, 𝒴 ∈ ℳ as matrices (3×3 for SO(3) and SE(2), 4×4 for SE(3)); τ ∈ ℝᵐ with m = dim ℳ (3, 3, 6). Ad_𝒳 is m×m.
A group is passed as a namespace `G` with `exp`, `log`, `inv`, `hat`, `vee`, `Ad`, `m` (filled in by C3–C5).

**Naive (reads like the paper).**

```python
def rplus(X, tau, G):        # (25)  Y = X ∘ Exp(τ), τ in the local frame at X
    return X @ G.exp(tau)

def rminus(Y, X, G):         # (26)  τ = Log(X⁻¹ ∘ Y)
    return G.log(G.inv(X) @ Y)

def lplus(tau, X, G):        # (27)  Y = Exp(τ) ∘ X, τ in the global frame
    return G.exp(tau) @ X

def lminus(Y, X, G):         # (28)  τ = Log(Y ∘ X⁻¹)
    return G.log(Y @ G.inv(X))

def adjoint_generic(X, G):   # (31): column i is (X E_i X⁻¹)^v
    Xi = G.inv(X)
    return np.column_stack([G.vee(X @ G.hat(e) @ Xi) for e in np.eye(G.m)])
```

**Robust.** The operators above are already what you use; the robust part is the adjoint in closed form and its
inverse without a matrix inversion.

```python
def so3_Ad(R):               # (139)
    return R

def ad_inv(X, G):            # (33): Ad_{X^-1} = Ad_X^-1, built from X^-1 directly
    return G.Ad(G.inv(X))
```

Tricks, each one named:

1. **Closed-form Ad per group, generic (31) only as the test oracle.** (31) costs m conjugations of a full matrix;
   (139), (159), (175) cost one product at most. The checker compares each closed form with `adjoint_generic` at
   random points (`C2_Ad_closed_vs_generic`, worst 1.3 × 10⁻¹⁵ over SO(3), SE(2), SE(3)).
2. **Never invert Ad.** (33)–(34): Ad_{𝒳⁻¹} from 𝒳⁻¹, which is a transpose and a product. The paper says so under (34).
3. **Say which ⊖ you mean.** (26) and (28) are both written ⊖ (p. 6). Name them `rminus` and `lminus` in code. The
   paper defaults to the right one, and so does manif's `minus`.
4. **(32) as a unit test.** 𝒳 ⊕ τ = (Ad_𝒳 τ) ⊕ 𝒳 holds exactly, so it catches a wrong Ad sign or a transposed block
   in one line (`C2_eq32_residual`, worst 7.8 × 10⁻¹⁶).

**Eigen.**

```cpp
template <class Group>   // Group provides Exp, Log, inverse, and a fixed-size Tangent
typename Group::Mat rplus(const typename Group::Mat& X, const typename Group::Tangent& tau) {
  return X * Group::Exp(tau);                                   // (25)
}
template <class Group>
typename Group::Tangent rminus(const typename Group::Mat& Y, const typename Group::Mat& X) {
  return Group::Log(Group::inverse(X) * Y);                     // (26)
}
```

**Cost per step.** ⊕: one Exp plus one group product. ⊖: one inverse (a transpose for rotations), one product, one
Log. Ad: free for SO(3), one 3×3 product for SE(3).

**What breaks first.** (1) Mixing right and left ⊖ between the residual and its Jacobian: the Jacobian is then off by
an Ad, and FD catches it at once. (2) Using a Ad from another library's tangent order (GTSAM's Pose3 is (ω, v), so
its Ad has the blocks swapped). (3) Using T_body_world where the paper means T_world_body (footnote 3), which makes
every ⊕ silently a left ⊕.

**In the original code.** `LieGroupBase::rplus` at `include/manif/impl/lie_group_base.h:468` is (25) and also
returns J_r(τ) as the Jacobian with respect to τ; `lplus` at `:484` is (27), with the Jacobian
`inverse().adj() * t.rjac()`; `plus` at `:505` forwards to `rplus`, so manif's default is right, as in the paper.
`rminus` at `:516` is (26) and returns both blocks (82)–(83); `lminus` at `:538` is (28). The closed-form adjoints
are `SO3Base::adj` (`include/manif/impl/so3/SO3_base.h:322`, returns `rotation()`), `SE2Base::adj`
(`include/manif/impl/se2/SE2_base.h:342`) and `SE3Base::adj` (`include/manif/impl/se3/SE3_base.h:373`), where the
authors' comment contrasts Chirikjian's (ω; v) order with manif's (v; ω).
https://github.com/artivis/manif/blob/65166b3bfd15b1020c29f3eaf6888e1009c79aea/include/manif/impl/lie_group_base.h#L466-L560

---

## C3. Right and left Jacobians of SO(3), and the elementary blocks, (58)–(83), (143)–(151)

**Shapes.** J_r(θ), J_l(θ), their inverses: 3×3. Every block of III-B/C is m×m. The action blocks are 3×3 (150)–(151).
Notation: J^𝒴_𝒳 is the right Jacobian (41a) of 𝒴(𝒳), mapping T_𝒳ℳ → T_𝒴𝒩.

**Naive (reads like the paper).**

```python
def so3_Jr_naive(theta):                          # (143)
    th = np.linalg.norm(theta); W = so3_hat(theta)
    return (np.eye(3) - (1 - np.cos(th)) / th**2 * W
            + (th - np.sin(th)) / th**3 * W @ W)

def so3_Jrinv_naive(theta):                       # (144)
    th = np.linalg.norm(theta); W = so3_hat(theta)
    return (np.eye(3) + 0.5 * W
            + (1 / th**2 - (1 + np.cos(th)) / (2 * th * np.sin(th))) * W @ W)
```

**Robust.**

```python
def coef_d(th):              # 1/th^2 - (1 + cos th)/(2 th sin th), the W^2 coefficient of (144)
    th = abs(th)
    if th < 0.3:
        t2 = th * th
        return 1 / 12 + t2 / 720 + t2 ** 2 / 30240 + t2 ** 3 / 1209600 + t2 ** 4 / 47900160
    return 1 / th ** 2 - 1 / (2 * th * np.tan(th / 2))   # (1 + cos)/sin = cot(th/2)

def so3_Jr(theta):                                # (143)
    th = np.linalg.norm(theta); W = so3_hat(theta)
    return np.eye(3) - coef_a(th) * W + coef_b(th) * W @ W

def so3_Jl(theta):                                # (145) = (147): J_l = J_r^T = J_r(-θ) (76)
    return so3_Jr(-theta)

def so3_Jrinv(theta):                             # (144)
    th = np.linalg.norm(theta); W = so3_hat(theta)
    return np.eye(3) + 0.5 * W + coef_d(th) * W @ W

def so3_Jlinv(theta):                             # (146)
    return so3_Jrinv(-theta)

SO3 = SimpleNamespace(m=3, exp=so3_exp, log=so3_log, inv=lambda R: R.T, hat=so3_hat, vee=so3_vee,
                      Ad=so3_Ad, Jr=so3_Jr, Jl=so3_Jl, Jrinv=so3_Jrinv, Jlinv=so3_Jlinv)

# Elementary blocks, any group G (III-B, III-C). Chain them with (58): J^Z_X = J^Z_Y J^Y_X.
def J_inv(X, G):          return -G.Ad(X)                          # (62)
def J_compose_X(X, Y, G): return ad_inv(Y, G)                      # (65)  Ad_Y^-1
def J_compose_Y(X, Y, G): return np.eye(G.m)                       # (66)
def J_log(X, G):          return G.Jrinv(G.log(X))                 # (79)
def J_rplus_X(X, tau, G): return G.Ad(G.exp(-tau))                 # (80)  Ad_{Exp(τ)}^-1 = Ad_{Exp(-τ)}
def J_rplus_tau(X, tau, G): return G.Jr(tau)                       # (81)
def J_rminus_X(Y, X, G):  return -G.Jlinv(rminus(Y, X, G))         # (82)
def J_rminus_Y(Y, X, G):  return G.Jrinv(rminus(Y, X, G))          # (83)

def so3_act(R, v):                                # R·v, with (150) and (151)
    return R @ v, -R @ so3_hat(v), R
```

Tricks, each one named:

1. **Shared coefficient functions.** a(θ) and b(θ) from C1 are the same scalars in Exp (134), J_r (143), the SE(2)
   Jacobians (163) and SE(3)'s V = J_l (174). Write them once with their small-angle handling and every formula that
   uses them is safe.
2. **J_l from J_r by (76), never a second formula.** J_l(θ) = J_r(−θ). Half the code, and the sign of the [θ]ₓ term
   cannot be typed wrong.
3. **Series for the (144) coefficient below 0.3, cot(θ/2) above it.** The printed coefficient subtracts two terms
   of size 1/θ² to get about 1/12, so it loses digits near 0: relative error 1.2 × 10⁻⁷ at θ = 10⁻⁴ and
   9.8 × 10⁻⁴ at θ = 10⁻⁶ (`C3_coef_d_printed_relerr`). Near π it is fine in float64 (7.0 × 10⁻¹¹ at π − 10⁻⁶),
   because sin(π) rounds to 1.2 × 10⁻¹⁶, not 0 (`sin_pi_float64`). Writing (1 + cos θ)/sin θ = cot(θ/2) removes the analytic 0/0 at π
   anyway, at no cost. The robust `coef_d` has a worst relative error of 3.5 × 10⁻¹⁴ over θ ∈ [10⁻⁸, π]
   (`C3_coef_d_relerr`).
4. **J_r⁻¹ by formula, not by `inv(J_r)`.** The closed form is as cheap as J_r. J_r⁻¹ stays bounded at π (its singular
   value across the axis is θ/(2 sin(θ/2)) = π/2 there; it diverges only as θ → 2π, lecture L12), so a 3×3 inversion is
   only wasteful, not wrong, inside |θ| ≤ π.
5. **(82) as −J_l⁻¹, not −J_r⁻¹ Ad.** The proof under (83) folds the adjoint away; use the folded form.
6. **Finite-difference every block once.** Each block is checked against (41a) through `scripts/fd_check.py`
   (`C3_fd_worst`). One wrong sign in (62) propagates into every H and every factor Jacobian.

**Eigen.**

```cpp
inline double coefD(double th) {            // W^2 coefficient of (144), even in th
  th = std::abs(th);
  if (th < 0.3) {
    const double t2 = th * th;
    return 1.0/12 + t2/720 + t2*t2/30240 + t2*t2*t2/1209600 + t2*t2*t2*t2/47900160;
  }
  return 1.0 / (th * th) - 1.0 / (2.0 * th * std::tan(0.5 * th));
}
inline Eigen::Matrix3d so3Jr(const Eigen::Vector3d& theta) {     // (143)
  const double th = theta.norm();
  const Eigen::Matrix3d W = hat(theta);
  return Eigen::Matrix3d::Identity() - coefA(th) * W + coefB(th) * (W * W);
}
inline Eigen::Matrix3d so3Jrinv(const Eigen::Vector3d& theta) {  // (144)
  const double th = theta.norm();
  const Eigen::Matrix3d W = hat(theta);
  return Eigen::Matrix3d::Identity() + 0.5 * W + coefD(th) * (W * W);
}
inline Eigen::Matrix3d so3Jl(const Eigen::Vector3d& theta) { return so3Jr(-theta); }       // (76)
inline Eigen::Matrix3d so3Jlinv(const Eigen::Vector3d& theta) { return so3Jrinv(-theta); }
```

**Cost per step.** Each Jacobian: one W·W product (27 multiply-adds) and three scalars. A chained H of three blocks
is three m×m products.

**What breaks first.** (1) The printed coefficients near θ = 0: in float64 (1 − cos θ)/θ² is 0 below 1.0 × 10⁻⁸ rad
and (θ − sin θ)/θ³ is 0 below 2.1 × 10⁻⁸ rad (lecture L17), and both are NaN at 0. A robot at rest hits this on its
first IMU sample. (2) The printed (144) at small θ: three digits left at θ = 10⁻⁶. It feeds every ⊖ Jacobian (82)–(83),
so a GN residual near convergence, where θ is small, gets the noisiest Jacobian. (3) J_l and J_r swapped, which still passes every test at θ ≈ 0.
Test at |θ| ≈ 1.

**In the original code.** `SO3TangentBase::rjac` at `include/manif/impl/so3/SO3Tangent_base.h:163` is
`ljac().transpose()`, that is (147); `ljac` at `:170` is (145) with the series switch at `:181`
(`if (theta_sq <= Constants<Scalar>::eps)`), where it returns the first-order `I + 0.5 W`. `rjacinv` at `:193` is
`ljacinv().transpose()`, and `ljacinv` at `:200` is (146), switching at `:210`. manif uses `1 - cos(theta)` and
`(1 + cos)/(2θ sin θ)` as printed. Just above its switch (θ > 1.5 × 10⁻⁷) the printed (1 − cos θ)/θ² has a relative
error of 2.5 × 10⁻³ at θ = 1.6 × 10⁻⁷ and 8.9 × 10⁻⁵ at θ = 10⁻⁶ (`C3_manif_coef_a_relerr`). It multiplies a W of norm
θ, so the printed J_r there is off by only 2.0 × 10⁻¹⁰ and 4.4 × 10⁻¹¹ (`C3_printed_Jr_abserr`), which is why this
never shows up in an FD test. GTSAM switches
much earlier: `kNearZeroThresholdSq = 1e-6` (`gtsam/geometry/SO3.cpp:57`), so the series is used below
θ = 10⁻³ rad, and it writes 1 − cos θ as `2.0 * s2 * s2` (`:86`, comment "numerically better than [1 - cos(theta)]"),
which is trick 1. It also has a near-π branch for the J_r⁻¹ coefficient at `:135`, with
`kNearPiThresholdSq = 1e-6` (`:59`): a first-order expansion around π instead of trick 3.
The ⊖ blocks are in `rminus` at `include/manif/impl/lie_group_base.h:516`, where `(*J_t_mb) = -(-t).rjacinv();`
(`:529`) is (82) written as −J_r⁻¹(−τ), equal to −J_l⁻¹(τ) by (76). The action blocks (150)–(151) are
`SO3Base::act` at `include/manif/impl/so3/SO3_base.h:300`; the inverse and composition blocks (140)–(141) are at
`:170` and `:264`.
https://github.com/artivis/manif/blob/65166b3bfd15b1020c29f3eaf6888e1009c79aea/include/manif/impl/so3/SO3Tangent_base.h#L160-L220

---

## C4. SE(2), App. C, (152)–(167)

**Shapes.** M = [[R, t], [0, 1]] 3×3, R 2×2, t ∈ ℝ². τ = (ρ, θ) ∈ ℝ³, ρ ∈ ℝ², θ scalar. [1]ₓ = [[0, −1], [1, 0]]. V(θ) 2×2.
Ad, J_r, J_l: 3×3. Action M·p: J_M 2×3, J_p 2×2.

**Naive (reads like the paper).**

```python
J1 = np.array([[0.0, -1.0], [1.0, 0.0]])          # [1]x

def so2(th):
    c, s = np.cos(th), np.sin(th)
    return np.array([[c, -s], [s, c]])

def se2_Jr_naive(tau):                            # (163)
    r1, r2, th = tau; s, c = np.sin(th), np.cos(th)
    return np.array([[s / th, (1 - c) / th, (th * r1 - r2 + r2 * c - r1 * s) / th**2],
                     [(c - 1) / th, s / th, (r1 + th * r2 - r1 * c - r2 * s) / th**2],
                     [0.0, 0.0, 1.0]])
```

**Robust.**

```python
def se2_V(th):                                    # (158), (1 - cos)/th = th * a(th)
    return np.sinc(th / np.pi) * np.eye(2) + th * coef_a(th) * J1

def se2_exp(tau):                                 # (156)
    M = np.eye(3); M[:2, :2] = so2(tau[2]); M[:2, 2] = se2_V(tau[2]) @ tau[:2]
    return M

def se2_log(M):                                   # (157), (117)
    th = np.arctan2(M[1, 0], M[0, 0])
    A, B = np.sinc(th / np.pi), th * coef_a(th)   # V = A I + B [1]x, V^-1 = (A I - B [1]x)/(A^2 + B^2)
    rho = (A * np.eye(2) - B * J1) @ M[:2, 2] / (A * A + B * B)
    return np.r_[rho, th]

def se2_inv(M):                                   # (154)
    R, t = M[:2, :2], M[:2, 2]
    Mi = np.eye(3); Mi[:2, :2] = R.T; Mi[:2, 2] = -R.T @ t
    return Mi

def se2_hat(tau):                                 # (153)
    return np.array([[0.0, -tau[2], tau[0]], [tau[2], 0.0, tau[1]], [0.0, 0.0, 0.0]])

def se2_vee(T):
    return np.array([T[0, 2], T[1, 2], T[1, 0]])

def se2_Ad(M):                                    # (159)
    A = np.eye(3); A[:2, :2] = M[:2, :2]; A[:2, 2] = -J1 @ M[:2, 2]
    return A

def se2_Jl(tau):                                  # (164), third column as a(th), b(th) combinations
    r1, r2, th = tau
    A, B, a, tb = np.sinc(th / np.pi), th * coef_a(th), coef_a(th), th * coef_b(th)
    return np.array([[A, -B, r1 * tb + r2 * a],
                     [B, A, -r1 * a + r2 * tb],
                     [0.0, 0.0, 1.0]])

def se2_Jr(tau):                                  # (163) = J_l(-τ) by (76)
    return se2_Jl(-tau)

def se2_Jlinv(tau):                               # block inverse of [[V', c], [0, 1]]
    J = se2_Jl(tau); Vi = np.linalg.inv(J[:2, :2])   # 2x2 rotation-times-scale, closed-form inverse
    Ji = np.eye(3); Ji[:2, :2] = Vi; Ji[:2, 2] = -Vi @ J[:2, 2]
    return Ji

def se2_Jrinv(tau):
    return se2_Jlinv(-tau)

def se2_act(M, p):                                # (165)-(167): M·p, J_M = [R  R[1]x p], J_p = R
    R = M[:2, :2]
    return M[:2, 2] + R @ p, np.hstack([R, (R @ J1 @ p)[:, None]]), R

SE2 = SimpleNamespace(m=3, exp=se2_exp, log=se2_log, inv=se2_inv, hat=se2_hat, vee=se2_vee,
                      Ad=se2_Ad, Jr=se2_Jr, Jl=se2_Jl, Jrinv=se2_Jrinv, Jlinv=se2_Jlinv)
```

Tricks, each one named:

1. **Rewrite the third column of (163)–(164) with a(θ) and b(θ).** (θρ₁ − ρ₂ + ρ₂ cos θ − ρ₁ sin θ)/θ² = ρ₁ θ b(θ) − ρ₂ a(θ),
   and the other three entries alike. The printed form adds O(1) terms that cancel to O(θ²) and then divides by θ²;
   the rewritten one has no cancellation. Measured with |ρ| = 1 (`C4_Jr_col3_abserr`): the printed column is off by
   2.7 × 10⁻³ at θ = 2 × 10⁻⁷, 1.4 × 10⁻⁴ at θ = 10⁻⁶ and 1.3 × 10⁻⁸ at θ = 10⁻⁴; the rewritten one by at most
   1.1 × 10⁻¹⁶.
2. **Angle from atan2, never arccos.** (117): θ = atan2(r₂₁, r₁₁) is right in all four quadrants and is already
   wrapped to (−π, π].
3. **V⁻¹ in closed form.** V = A I + B[1]ₓ is a scaled rotation, so V⁻¹ = (A I − B[1]ₓ)/(A² + B²). A² + B² =
   (sin(θ/2)/(θ/2))², which is never 0 for |θ| ≤ π.
4. **J_r from J_l by (76).** Same reason as C3.
5. **One H for the beacon, by the chain rule, checked once.** H = J^{𝒳⁻¹·b}_{𝒳⁻¹} J^{𝒳⁻¹}_𝒳 = −[I  Rᵀ[1]ₓ(b − t)] (p. 12);
   C8 uses the closed form and the checker compares it with the chain of `se2_act` and `J_inv`.

**Eigen.**

```cpp
struct SE2Jac { Eigen::Matrix3d Jl, Jr; };
inline Eigen::Matrix3d se2Jl(const Eigen::Vector3d& tau) {      // (164)
  const double r1 = tau(0), r2 = tau(1), th = tau(2);
  const double A = th == 0.0 ? 1.0 : std::sin(th) / th;
  const double a = coefA(th), B = th * a, tb = th * coefB(th);
  Eigen::Matrix3d J;
  J << A, -B, r1 * tb + r2 * a,
       B,  A, -r1 * a + r2 * tb,
       0,  0, 1;
  return J;
}
inline Eigen::Matrix3d se2Jr(const Eigen::Vector3d& tau) { return se2Jl(-tau); }   // (76)
inline Eigen::Matrix<double, 2, 3> se2ActJacM(const Eigen::Matrix2d& R, const Eigen::Vector2d& p) {
  Eigen::Matrix<double, 2, 3> J;                                 // (166)
  J.leftCols<2>() = R;
  J.col(2) = R * Eigen::Vector2d(-p.y(), p.x());                 // R [1]x p
  return J;
}
```

**Cost per step.** Everything is a handful of scalars: one sin, one cos, one atan2 for Log. Use fixed-size 3×3
types; dynamic matrices cost more in allocation than in arithmetic here.

**What breaks first.** (1) The printed third column of J_r and J_l at small θ: an error of 2.7 × 10⁻³ in the ρ–θ coupling
at θ = 2 × 10⁻⁷ (trick 1). When a robot drives straight, θ = ω δt is near zero and lands in that range. (2) θ from arccos or
from `R[1,0]` alone: wrong sign in two quadrants. (3) Using (ρ, θ) in one place and (x, y, θ) of the pose in another: ρ is
not t unless θ = 0 (Ex. 7, lecture L18).

**In the original code.** `SE2TangentBase::exp` at `include/manif/impl/se2/SE2Tangent_base.h:120` returns J_r
(163) as a by-product; its third column is `(-y() + theta*x() + y()*cos_theta - x()*sin_theta)/theta_sq` at `:163`,
the printed form, used whenever θ² ≥ 2.2 × 10⁻¹⁴. That is the cancellation trick 1 removes. `rjac` at `:182` calls
`exp(Jr)`, and the commented-out block from `:186` is an older copy of the same formula. `rjacinv` at `:224` has its
own closed form, and `ljac` at `:273` is (164). `SE2Base::log` at `include/manif/impl/se2/SE2_base.h:216` computes
V⁻¹ through `den = 1/(A*A + B*B)`, trick 3. `inverse` at `:199` returns `-adj()` as the Jacobian (160),
`compose` at `:271` returns `m.inverse().adj()` and identity (161)–(162), `act` at `:319` is (166)–(167), and
`adj` at `:342` is (159) as `Adj(0,2) = y(); Adj(1,2) = -x();`.
https://github.com/artivis/manif/blob/65166b3bfd15b1020c29f3eaf6888e1009c79aea/include/manif/impl/se2/SE2Tangent_base.h#L118-L180

---

## C5. SE(3), App. D, (168)–(183)

**Shapes.** M = [[R, t], [0, 1]] 4×4. τ = (ρ, θ) ∈ ℝ⁶. V(θ) = J_l(θ) of SO(3), 3×3 (174). Q(ρ, θ) 3×3 (180).
Ad, J_l, J_r, inverses: 6×6. Action M·p: J_M 3×6, J_p 3×3.

**Naive (reads like the paper).**

```python
def se3_Q_naive(rho, theta):                      # (180), as printed
    th = np.linalg.norm(theta); P = so3_hat(rho); T = so3_hat(theta)
    return (0.5 * P
            + (th - np.sin(th)) / th**3 * (T @ P + P @ T + T @ P @ T)
            - (1 - th**2 / 2 - np.cos(th)) / th**4 * (T @ T @ P + P @ T @ T - 3 * T @ P @ T)
            - 0.5 * ((1 - th**2 / 2 - np.cos(th)) / th**4 - 3 * (th - np.sin(th) - th**3 / 6) / th**5)
                  * (T @ P @ T @ T + T @ T @ P @ T))
```

**Robust.**

```python
def coef_c(th):              # (1 - th^2/2 - cos th)/th^4
    th = abs(th)
    if th < 0.6:             # sum_k (-1)^(k+1) th^2k / (2k+4)!
        return sum((-1) ** (k + 1) * th ** (2 * k) / math.factorial(2 * k + 4) for k in range(6))
    return (1 - th * th / 2 - np.cos(th)) / th ** 4

def coef_e(th):              # (th - sin th - th^3/6)/th^5
    th = abs(th)
    if th < 0.6:             # sum_k (-1)^(k+1) th^2k / (2k+5)!
        return sum((-1) ** (k + 1) * th ** (2 * k) / math.factorial(2 * k + 5) for k in range(6))
    return (th - np.sin(th) - th ** 3 / 6) / th ** 5

def se3_Q(rho, theta):                            # (180)
    th = np.linalg.norm(theta); P = so3_hat(rho); T = so3_hat(theta)
    TP, PT, TPT = T @ P, P @ T, T @ P @ T
    c = coef_c(th)
    return (0.5 * P + coef_b(th) * (TP + PT + TPT) - c * (T @ TP + PT @ T - 3 * TPT)
            - 0.5 * (c - 3 * coef_e(th)) * (TPT @ T + T @ TPT))

def se3_exp(tau):                                 # (172), V = J_l (174)
    M = np.eye(4); M[:3, :3] = so3_exp(tau[3:]); M[:3, 3] = so3_Jl(tau[3:]) @ tau[:3]
    return M

def se3_log(M):                                   # (173)
    theta = so3_log(M[:3, :3])
    return np.r_[so3_Jlinv(theta) @ M[:3, 3], theta]

def se3_inv(M):                                   # (170)
    R, t = M[:3, :3], M[:3, 3]
    Mi = np.eye(4); Mi[:3, :3] = R.T; Mi[:3, 3] = -R.T @ t
    return Mi

def se3_hat(tau):                                 # (169)
    T = np.zeros((4, 4)); T[:3, :3] = so3_hat(tau[3:]); T[:3, 3] = tau[:3]
    return T

def se3_vee(T):
    return np.r_[T[:3, 3], so3_vee(T[:3, :3])]

def se3_Ad(M):                                    # (175)
    R, t = M[:3, :3], M[:3, 3]
    A = np.zeros((6, 6)); A[:3, :3] = R; A[3:, 3:] = R; A[:3, 3:] = so3_hat(t) @ R
    return A

def se3_Jl(tau):                                  # (179a)
    J = np.zeros((6, 6)); Jl = so3_Jl(tau[3:])
    J[:3, :3] = Jl; J[3:, 3:] = Jl; J[:3, 3:] = se3_Q(tau[:3], tau[3:])
    return J

def se3_Jlinv(tau):                               # (179b)
    J = np.zeros((6, 6)); Ji = so3_Jlinv(tau[3:])
    J[:3, :3] = Ji; J[3:, 3:] = Ji; J[:3, 3:] = -Ji @ se3_Q(tau[:3], tau[3:]) @ Ji
    return J

def se3_Jr(tau):    return se3_Jl(-tau)           # (76), as the paper says under (180)
def se3_Jrinv(tau): return se3_Jlinv(-tau)

def se3_act(M, p):                                # (181)-(183): J_M = [R  -R[p]x], J_p = R
    R = M[:3, :3]
    return M[:3, 3] + R @ p, np.hstack([R, -R @ so3_hat(p)]), R

SE3 = SimpleNamespace(m=6, exp=se3_exp, log=se3_log, inv=se3_inv, hat=se3_hat, vee=se3_vee,
                      Ad=se3_Ad, Jr=se3_Jr, Jl=se3_Jl, Jrinv=se3_Jrinv, Jlinv=se3_Jlinv)
```

Tricks, each one named:

1. **V = J_l of SO(3).** (174) is (145), as the paper notes. Exp and Log of SE(3) are then SO(3) Exp/Log plus one
   3×3 product with J_l or J_l⁻¹, and Log reuses the near-π-safe SO(3) Log of C1.
2. **Series for the two fourth- and fifth-order coefficients of Q below θ = 0.6.** (1 − θ²/2 − cos θ)/θ⁴ cancels
   three O(1) terms to O(θ⁴), so the printed coefficient is noise at small θ. The terms it multiplies are O(θ²) and
   O(θ³), which hides most of the damage: on Q with |ρ| = 1 (`C5_Q_abserr`) the printed form is off by at most
   4.2 × 10⁻¹⁰ (at θ = 10⁻⁴), 1.4 × 10⁻¹¹ at θ = 10⁻⁶ and 2.0 × 10⁻¹³ at θ = 10⁻². That is harmless for a filter and enough to fail a
   10⁻¹² unit test. With six series terms below 0.6 the coefficients have worst relative errors 9.1 × 10⁻¹⁵ and
   5.2 × 10⁻¹⁴ (`C5_coef_relerr`), and Q's error is below what the reference can resolve. manif uses the printed
   form; see below.
3. **J_r and J_r⁻¹ by (76).** The paper gives only J_l (179). Flip the sign of τ.
4. **(179b) instead of inverting a 6×6.** The upper-right block is −J_l⁻¹ Q J_l⁻¹: two 3×3 products.
5. **The upper-right block of Ad is [t]ₓR, not R[t]ₓ.** (175). The two differ unless R = I, so a test at R = I misses
   the swap. Test at random R.

**Eigen.**

```cpp
inline Eigen::Matrix3d se3Q(const Eigen::Vector3d& rho, const Eigen::Vector3d& theta) {   // (180)
  const double th = theta.norm(), t2 = th * th;
  const Eigen::Matrix3d P = hat(rho), T = hat(theta);
  const Eigen::Matrix3d TP = T * P, PT = P * T, TPT = TP * T;
  double c = 0, e = 0;
  if (th < 0.6) {                           // factorial series, six terms each
    double tc = -1.0 / 24, te = -1.0 / 120;
    for (int k = 0; k < 6; ++k) {
      c += tc; e += te;
      tc *= -t2 / ((2*k + 5) * (2*k + 6));
      te *= -t2 / ((2*k + 6) * (2*k + 7));
    }
  } else {
    c = (1 - t2/2 - std::cos(th)) / (t2 * t2);
    e = (th - std::sin(th) - t2*th/6) / (t2 * t2 * th);
  }
  return 0.5 * P + coefB(th) * (TP + PT + TPT) - c * (T * TP + PT * T - 3.0 * TPT)
         - 0.5 * (c - 3.0 * e) * (TPT * T + T * TPT);
}
inline Eigen::Matrix<double, 6, 6> se3Jl(const Eigen::Matrix<double, 6, 1>& tau) {       // (179a)
  Eigen::Matrix<double, 6, 6> J = Eigen::Matrix<double, 6, 6>::Zero();
  const Eigen::Matrix3d Jl = so3Jl(tau.tail<3>());
  J.topLeftCorner<3, 3>() = Jl;
  J.bottomRightCorner<3, 3>() = Jl;
  J.topRightCorner<3, 3>() = se3Q(tau.head<3>(), tau.tail<3>());
  return J;
}
```

**Cost per step.** Q: seven 3×3 products (7 × 27 = 189 multiply-adds), the most expensive block in this paper. An IMU-rate
filter that needs J_r(τ) on SE(3) every sample pays this; most use the ⟨ℝ³, SO(3)⟩ composite (C7) for exactly
this reason.

**What breaks first.** (1) (ω, v) tangent order copied from GTSAM into (ρ, θ) code: every block is swapped, and the
FD test passes if it uses the same wrong order on both sides. (2) Ad with R[t]ₓ instead of [t]ₓR, invisible at R = I.
(3) The printed Q at small θ (trick 2): 4.2 × 10⁻¹⁰ off at θ = 10⁻⁴, the per-sample rotation at 100 Hz of a body
turning at 0.01 rad/s. That is
not a filter problem in float64, but an FD test at random τ (θ ≈ 1) never reaches that range, so it goes unnoticed.

**In the original code.** `SE3TangentBase::exp` at `include/manif/impl/se3/SE3Tangent_base.h:144` builds the
translation as `asSO3().ljac()*lin()`, trick 1. `rjac` at `:182` and `ljac` at `:196` assemble (179a), calling
`fillQ` with `-coeffs()` for J_r, which is (76). `rjacinv` at `:211` assembles (179b) with
`-Jl⁻¹ Q Jl⁻¹`, trick 4. `fillQ` at `:246` is (180): the series switch at `:259` is `theta_sq <= eps`, that is
θ ≤ 1.5 × 10⁻⁷, and above it the coefficient is `C = (Scalar(1) - theta_sq/Scalar(2) - cos_theta) / (theta_sq*theta_sq)`
(`:272`), the printed form. The authors' comments in `fillQ` record three identities they used to save products
(V·W = (W·V)ᵀ and two more). `SE3Base::log` at `include/manif/impl/se3/SE3_base.h:291` uses `ljacinv`, `inverse` at
`:276` returns `-adj()` (176), `act` at `:349` is (182)–(183), `adj` at `:373` is (175).
https://github.com/artivis/manif/blob/65166b3bfd15b1020c29f3eaf6888e1009c79aea/include/manif/impl/se3/SE3Tangent_base.h#L244-L295

---

## C6. Covariance on the tangent and discrete integration, (51)–(56)

**Shapes.** Σ_𝒳 m×m on the tangent at 𝒳̄ (52); ᴱΣ m×m on the tangent at ℰ (53). Df/D𝒳 n×m. Velocities v_k ∈ ℝᵐ, δt_k
scalars.

**Naive (reads like the paper).**

```python
def cov_local_to_global(X, Sigma, G):             # (54)
    A = G.Ad(X)
    return A @ Sigma @ A.T

def propagate_cov(J, Sigma):                      # (55)
    return J @ Sigma @ J.T

def integrate(X0, vs, dts, G):                    # (56): X_k = X_{k-1} Exp(v_k dt_k)
    X = X0
    for v, dt in zip(vs, dts):
        X = X @ G.exp(v * dt)
    return X
```

**Robust.**

```python
def compose_with_cov(X, Sx, Y, Sy, G):            # Z = X ∘ Y, X and Y independent; (55) with (65), (66)
    Jx = J_compose_X(X, Y, G)                     # Ad_Y^-1
    S = Jx @ Sx @ Jx.T + Sy                       # J_Y = I
    return X @ Y, 0.5 * (S + S.T)

def quat_integrate(q, omegas, dt):                # q_k = q_{k-1} Exp(ω_k dt), renormalized
    for w in omegas:
        q = quat_mul(q, quat_exp(w * dt))
        q = q / np.linalg.norm(q)
    return q
```

Tricks, each one named:

1. **Symmetrize after every propagation.** J Σ Jᵀ is symmetric in exact arithmetic only; ½(Σ + Σᵀ) costs nothing and
   keeps Cholesky from failing later.
2. **Know which tangent Σ lives in.** A covariance from a library or a datasheet is often global (53): a GNSS
   attitude, an "attitude known up to yaw" prior (p. 9). Convert with (54), Ad⁻¹ Σ Ad⁻ᵀ the other way, before
   adding it to a local P.
3. **Exp for the step, not Euler.** X_{k−1}(I + v^ δt) leaves the group; X_{k−1}Exp(v δt) is exact for piecewise-
   constant v. The lecture's L9 run puts numbers on it.
4. **Monte Carlo as the oracle for (55).** First order only: the checker samples X ⊕ ε, composes, takes ⊖ to the
   mean, and compares the sample covariance with `compose_with_cov`. For an SE(2) composition with 0.1 rad and
   0.1 m standard deviations it measures a relative Frobenius error of 3.4 × 10⁻³ with 200 000 samples
   (`C6_mc_relerr`). The error grows with the angular spread, which is where (55) stops being enough (lecture L8).

**Eigen.**

```cpp
template <int M>
inline Eigen::Matrix<double, M, M> propagate(const Eigen::Matrix<double, M, M>& J,
                                             const Eigen::Matrix<double, M, M>& S) {
  Eigen::Matrix<double, M, M> out;
  out.noalias() = J * S * J.transpose();                          // (55)
  return 0.5 * (out + out.transpose());
}
```

**Cost per step.** (55): two m×m products, O(m³), 2·216 multiply-adds for SE(3). Integration: one Exp and one group
product per step.

**What breaks first.** (1) A global covariance added to a local one without (54): consistent near ℰ, wrong after
the robot has turned. (2) (55) on a wide covariance (a heading σ of tens of degrees): first-order propagation
underestimates the banana; NEES rises before anything diverges. (3) An unnormalized quaternion after a long
integration.

**In the original code.** Covariance propagation is not a library function in manif. It is the line
`P = J_x * P * J_x.transpose() + J_u * U * J_u.transpose();` in `examples/se2_localization.cpp:239`, with `J_x` and
`J_u` returned by `X.plus(u_est, J_x, J_u)` at `:237`, which is `rplus` at
`include/manif/impl/lie_group_base.h:468`. Integration (56) is the same `plus`. Quaternion renormalization after a
product is in `SO3Base::compose` (`include/manif/impl/so3/SO3_base.h:264`, rescale at `:291`).
https://github.com/artivis/manif/blob/65166b3bfd15b1020c29f3eaf6888e1009c79aea/examples/se2_localization.cpp#L235-L240

---

## C7. Composite manifolds, (84)–(91), Ex. 7

**Shapes.** 𝒳 = ⟨𝒳₁, …, 𝒳_M⟩, stored as a Python list; τ ∈ ℝⁿ with n = Σ mᵢ, split into slices. The Jacobian (89) is a
block matrix; Σ (91) is n×n.

**Naive (reads like the paper).**

```python
RN = SimpleNamespace(plus=lambda x, d: x + d, minus=lambda y, x: y - x, m=None)      # App. E, (186)-(187)
SE2.plus = lambda X, d: rplus(X, d, SE2); SE2.minus = lambda Y, X: rminus(Y, X, SE2)

def slices(dims):
    edges = np.cumsum([0] + list(dims))
    return [slice(a, b) for a, b in zip(edges[:-1], edges[1:])]

def diamond_plus(Xs, tau, groups, dims):          # (86): X ◇ Exp<τ>, block by block
    return [G.plus(X, tau[s]) for X, G, s in zip(Xs, groups, slices(dims))]

def diamond_minus(Ys, Xs, groups, dims):          # (87): Log<X^◇ ◇ Y>, block by block
    return np.concatenate([G.minus(Y, X) for Y, X, G in zip(Ys, Xs, groups)])
```

**Robust.** The same functions; what changes is the bookkeeping around them.

```python
def block_jacobian(rows, cols, blocks):           # (89): blocks {(i, j): D f_i / D X_j}, the rest zero
    J = np.zeros((sum(rows), sum(cols)))
    rs, cs = slices(rows), slices(cols)
    for (i, j), B in blocks.items():
        J[rs[i], cs[j]] = B
    return J
```

Tricks, each one named:

1. **One table of (group, dim, offset) for the whole state.** Every ⊕, ⊖, Jacobian column and covariance block reads
   its slice from it. Off-by-three errors between a state layout and a Jacobian layout are the most common bug in
   composite filters.
2. **Use ⟨ℝⁿ, SO(n)⟩ for errors, SE(n) or T(n)×SO(n) for the dynamics (p. 11).** The composite ⊖ gives p₂ − p₁ for the
   position error, which is what a position covariance means. SE(n) ⊖ gives V⁻¹R₁ᵀ(p₂ − p₁) instead (Ex. 7).
3. **Block-diagonal J_r.** J_r of a composite is blockdiag(J_r(τᵢ)), and it is identity on the ℝⁿ blocks. Never form the
   full n×n product with dense zeros.
4. **Test the round trip.** diamond_minus(diamond_plus(𝒳, τ), 𝒳) = τ to rounding, for random τ with |θ| < π on each
   rotation block (`C7_roundtrip`, worst 6.8 × 10⁻¹⁶).

**Eigen.**

```cpp
struct PoseLmk2D {                       // <SE(2), R^2>: a pose and one beacon, n = 5
  Eigen::Matrix3d X;
  Eigen::Vector2d b;
};
inline PoseLmk2D diamondPlus(const PoseLmk2D& s, const Eigen::Matrix<double, 5, 1>& d,
                             Eigen::Matrix3d (*se2Exp)(const Eigen::Vector3d&)) {   // (86)
  return {s.X * se2Exp(d.head<3>()), s.b + d.tail<2>()};
}
```

**Cost per step.** ⊕ and ⊖: the sum of the block costs. The Jacobian (89) of a sensor model touches only the blocks
that model reads, so it is sparse; store it sparse beyond a few hundred columns.

**What breaks first.** (1) Slice offsets that disagree between ⊕ and the Jacobian. (2) SE(n) ⊖ used for a position
error, so the covariance is in a rotated, scaled frame and gating on it is wrong. (3) A dense n×n J_r in a large state.

**In the original code.** manif's composite is `Bundle`. `BundleTangentBase::exp` at
`include/manif/impl/bundle/BundleTangent_base.h:171` calls each element's `exp` and writes each element's J_r into
the diagonal block. `rjac_impl` at `:246` fills `Jr.template block<Element<_Idx>::DoF, Element<_Idx>::DoF>(…)`
with `element<_Idx>().rjac()`, trick 3, and leaves the off-diagonal blocks at zero.
https://github.com/artivis/manif/blob/65166b3bfd15b1020c29f3eaf6888e1009c79aea/include/manif/impl/bundle/BundleTangent_base.h#L244-L256

---

## C8. ESKF on SE(2) with beacons, §V-A, (92)–(102)

**Shapes.** 𝒳̂ ∈ SE(2) 3×3; P 3×3 on the tangent at 𝒳̂ (98). u ∈ ℝ³ (92), `R_proc` 3×3 (93). One beacon b ∈ ℝ²,
measurement y ∈ ℝ² (95), `Q_meas` 2×2 (96). F, G 3×3; H 2×3; Z 2×2; K 3×2; δx ∈ ℝ³.

**Naive (reads like the paper).**

```python
def eskf_predict_naive(X, P, u, R_proc):          # (99)-(100)
    F = np.linalg.inv(se2_Ad(se2_exp(u)))         # Ad_{Exp(u)}^-1
    G = se2_Jr(u)
    return X @ se2_exp(u), F @ P @ F.T + G @ R_proc @ G.T

def eskf_update_naive(X, P, y, b, Q_meas):        # (101)-(102)
    R, t = X[:2, :2], X[:2, 2]
    z = y - R.T @ (b - t)                         # innovation, X^-1 · b (95)
    H = -np.hstack([np.eye(2), (R.T @ J1 @ (b - t))[:, None]])   # p. 12
    Z = H @ P @ H.T + Q_meas
    K = P @ H.T @ np.linalg.inv(Z)
    dx = K @ z
    return X @ se2_exp(dx), P - K @ Z @ K.T
```

**Robust.**

```python
def eskf_predict(X, P, u, R_proc):                # (99)-(100)
    F = se2_Ad(se2_exp(-u))                       # (80) with (33): no 3x3 inversion
    G = se2_Jr(u)                                 # (81)
    P = F @ P @ F.T + G @ R_proc @ G.T
    return X @ se2_exp(u), 0.5 * (P + P.T)

def eskf_update(X, P, y, b, Q_meas, reset=True):  # (101)-(102), one beacon
    R, t = X[:2, :2], X[:2, 2]
    z = y - R.T @ (b - t)
    H = -np.hstack([np.eye(2), (R.T @ J1 @ (b - t))[:, None]])
    Z = H @ P @ H.T + Q_meas
    K = cho_solve(cho_factor(Z), H @ P).T         # K = P H^T Z^-1 without forming Z^-1
    dx = K @ z
    IKH = np.eye(3) - K @ H
    P = IKH @ P @ IKH.T + K @ Q_meas @ K.T        # Joseph form, = P - K Z K^T in exact arithmetic
    if reset:                                     # not in (102): move P to the tangent at the new X
        Jr = se2_Jr(dx)
        P = Jr @ P @ Jr.T
    return X @ se2_exp(dx), 0.5 * (P + P.T)
```

Tricks, each one named:

1. **F = Ad_{Exp(−u)}.** (80) with (33) gives the inverse adjoint without a matrix inversion.
2. **`cho_solve` for the gain.** Z is 2×2 symmetric positive definite; solve Z Kᵀ = H P instead of forming Z⁻¹. It
   costs the same at this size, and it fails loudly (Cholesky error) when Z stops being positive definite, which
   `inv` hides.
3. **Joseph form.** (102) loses symmetry and positive definiteness by rounding when Q_meas is small relative to H P Hᵀ;
   the Joseph form stays positive semidefinite for any K (Bar-Shalom et al., *Estimation with Applications to
   Tracking and Navigation*, ch. 5).
4. **Covariance reset after ⊕ (not in the paper).** After 𝒳̂ ← 𝒳̂ ⊕ δx, P still describes the error at the old 𝒳̂.
   To first order the error at the new 𝒳̂ is J_r(δx)(ε − δx), so P ← J_r(δx) P J_r(δx)ᵀ (lecture L15; ref. [8] does the
   quaternion case). The checker verifies the Jacobian by finite differences of ε ↦ Log(Exp(δx)⁻¹ Exp(ε))
   (`C8_reset_fd`). The paper's (102) is the δx → 0 limit, J_r ≈ I.
5. **Sequential beacons, H re-evaluated at the updated 𝒳̂.** Two-dimensional updates one beacon at a time keep Z 2×2 and
   relinearize between beacons. With linear models this equals a batch update; with nonlinear ones it is slightly
   better.
6. **Gate on the innovation.** zᵀZ⁻¹z ~ χ²(2) when the model is right. Reject above the 99 % quantile, 9.21 (`chi2_99_2dof`; Bar-Shalom).
   One wrong data association otherwise moves the pose by the full beacon distance.

**Eigen.**

```cpp
struct Eskf2D { Eigen::Matrix3d X, P; };
inline void eskfUpdate(Eskf2D& f, const Eigen::Vector2d& y, const Eigen::Vector2d& b,
                       const Eigen::Matrix2d& Q_meas,
                       Eigen::Matrix3d (*se2Exp)(const Eigen::Vector3d&)) {
  const Eigen::Matrix2d R = f.X.topLeftCorner<2, 2>();
  const Eigen::Vector2d t = f.X.topRightCorner<2, 1>();
  const Eigen::Vector2d z = y - R.transpose() * (b - t);                         // innovation, p. 12 (above (101))
  Eigen::Matrix<double, 2, 3> H;
  H.leftCols<2>() = -Eigen::Matrix2d::Identity();
  H.col(2) = -R.transpose() * Eigen::Vector2d(-(b - t).y(), (b - t).x());      // -R^T [1]x (b - t)
  const Eigen::Matrix<double, 2, 3> HP = H * f.P;
  const Eigen::Matrix2d Z = HP * H.transpose() + Q_meas;
  const Eigen::LLT<Eigen::Matrix2d> llt(Z);
  const Eigen::Matrix<double, 3, 2> K = llt.solve(HP).transpose();               // P H^T Z^-1
  const Eigen::Matrix3d IKH = Eigen::Matrix3d::Identity() - K * H;
  f.P = (IKH * f.P * IKH.transpose() + K * Q_meas * K.transpose()).eval();       // Joseph
  f.X = (f.X * se2Exp(K * z)).eval();
}
```

**Cost per step.** Predict: four 3×3 products for F P Fᵀ and G R_proc Gᵀ, plus the Jacobians. Update per beacon: one 2×2
Cholesky and a few 3×3 products. The filter is never the bottleneck; data association is.

**What breaks first.** (1) A wrong sign in H, which makes the filter diverge after the first turn. The FD check of
`C8_H_fd` catches it. (2) Inconsistent noise: R_proc too small for wheel slip on a tracked base (σ_s in (93) is the
lever), so NEES rises in turns. (3) No gate: one bad association. (4) Large corrections against precise beacons. With manif's example noise (0.1 rad of heading noise per step,
1 cm beacons) the first-order filter is overconfident: ANEES 6.8 with the reset and 8.3 without it, against 3.03
when the control noise is ten times smaller (`IMPL_anees`, 200 runs of 100 steps). The reset helps; iterating the
update (IEKF) is the next step.

**In the original code.** `examples/se2_localization.cpp` is this section in C++. Prediction is
`X = X.plus(u_est, J_x, J_u);` at `:237` and `P = J_x * P * J_x.transpose() + J_u * U * J_u.transpose();` at `:239`,
so manif's F and G are the Jacobians `rplus` returns. The expectation and H come from the chain rule as the paper
writes it, `e = X.inverse(J_xi_x).act(b, J_e_xi);` at `:252` and `H = J_e_xi * J_xi_x` on the next line. The gain is
`K = P * H.transpose() * Z.inverse();` at `:261`, and the update is `P = P - K * Z * K.transpose();` at `:268`, which
is (102) without Joseph form and without the reset. Noise names differ: manif calls the control covariance `U` and the
measurement covariance `R`. One pitfall the paper does not have: the simulated control noise is
`u_noise = u_sigmas * Array3d::Random();` at `:207`, uniform on [−σ, σ], whose variance is σ²/3, while the filter is
told `U = σ²` with `u_sigmas << 0.1, 0.1, 0.1;` at `:144`. The example's filter is therefore conservative by a factor
of three in variance. The checker runs the example's setup through C8: ANEES 1.00 with uniform noise against
3.03 with Gaussian noise, at a tenth of the example's control noise (`IMPL_anees`; 3 is consistent).
https://github.com/artivis/manif/blob/65166b3bfd15b1020c29f3eaf6888e1009c79aea/examples/se2_localization.cpp#L235-L270

---

## C9. Gauss-Newton smoothing and mapping on a composite, §V-B and §V-C, (103)–(111)

**Shapes.** State (103) ⟨𝒳₁, 𝒳₂, 𝒳₃, b₄, b₅, b₆⟩, n = 3·3 + 3·2 = 15. Factors 𝒫 = {1, 12, 23, 14, 15, 25, 26, 36} (106):
one prior (3 rows), two motion (3 rows each), five beacon (2 rows each), 19 rows in total. J is 19×15 (107), r ∈ ℝ¹⁹.
Ω^{T/2}: the transposed square root of the information matrix, 3×3 or 2×2. Self-calibration (111): c ∈ ℝ², J gains
two columns.

**Naive (reads like the paper).**

```python
def gn_step_naive(J, r):                          # (109)
    return -np.linalg.inv(J.T @ J) @ J.T @ r
```

**Robust.**

```python
def sqrt_info(cov):            # Ω^{T/2} with Ω = cov^-1: L^-1 where cov = L L^T, so (L^-1)^T L^-1 = Ω
    return np.linalg.solve(np.linalg.cholesky(cov), np.eye(len(cov)))

def sam_linearize(poses, lmks, prior, motions, beacons, R_proc, Q_meas, P0):
    """poses: list of 3x3; lmks: list of (2,); prior: 3x3 mean of X_1;
    motions: [(i, j, u_ij)]; beacons: [(i, k, y_ik)]. Returns r (whitened) and J."""
    Np, Nl = len(poses), len(lmks)
    col = lambda i: slice(3 * i, 3 * i + 3)                      # pose columns
    lcol = lambda k: slice(3 * Np + 2 * k, 3 * Np + 2 * k + 2)   # beacon columns
    Sp, Su, Sy = sqrt_info(P0), sqrt_info(R_proc), sqrt_info(Q_meas)
    r, rows = [], []
    d = rminus(poses[0], prior, SE2)                             # prior residual, p. 13
    r.append(Sp @ d)
    row = np.zeros((3, 3 * Np + 2 * Nl)); row[:, col(0)] = Sp @ se2_Jrinv(d); rows.append(row)
    for i, j, u in motions:                                      # r = Ω^{T/2}(u - (X_j ⊖ X_i))
        d = rminus(poses[j], poses[i], SE2)
        r.append(Su @ (u - d))
        row = np.zeros((3, 3 * Np + 2 * Nl))
        row[:, col(i)] = Su @ se2_Jlinv(d)                       # -Ω^{T/2} (82)
        row[:, col(j)] = -Su @ se2_Jrinv(d)                      # -Ω^{T/2} (83)
        rows.append(row)
    for i, k, y in beacons:                                      # r = Ω^{T/2}(y - X_i^-1 · b_k)
        Xi = poses[i]; R, t = Xi[:2, :2], Xi[:2, 2]
        e = R.T @ (lmks[k] - t)
        H = -np.hstack([np.eye(2), (R.T @ J1 @ (lmks[k] - t))[:, None]])   # as in C8
        r.append(Sy @ (y - e))
        row = np.zeros((2, 3 * Np + 2 * Nl))
        row[:, col(i)] = -Sy @ H
        row[:, lcol(k)] = -Sy @ R.T                              # (167) at X^-1: J_b = R^T
        rows.append(row)
    return np.concatenate(r), np.vstack(rows)

def sam_solve(poses, lmks, *args, max_iter=20, tol=1e-6):        # (106)-(110)
    for it in range(max_iter):
        r, J = sam_linearize(poses, lmks, *args)
        dx = np.linalg.lstsq(J, -r, rcond=None)[0]               # QR/SVD on J, not (J^T J)^-1
        Np = len(poses)
        poses = [X @ se2_exp(dx[3 * i:3 * i + 3]) for i, X in enumerate(poses)]          # (110)
        lmks = [b + dx[3 * Np + 2 * k:3 * Np + 2 * k + 2] for k, b in enumerate(lmks)]
        if np.linalg.norm(dx) < tol:
            break
    return poses, lmks, it + 1

def calib_jacobian(Su):                           # (111): J^r_c = Ω^{T/2} D c(ũ, c)/D c
    return Su @ np.array([[-1.0, 0.0], [0.0, 0.0], [0.0, -1.0]])
```

Tricks, each one named:

1. **Whiten with a Cholesky solve.** Ω^{T/2} = L⁻¹ for Σ = L Lᵀ. For the diagonal (93) and (96) this is 1/σ per row;
   never form Ω and then take its square root.
2. **Solve the least-squares problem on J, not on JᵀJ.** Forming JᵀJ squares the condition number. `lstsq` (QR/SVD)
   here; sparse QR or Cholesky with a fill-reducing ordering at scale (refs. [12]–[15]), never the inverse of (109).
3. **The prior fixes the gauge.** Without the factor on 𝒳₁ the problem has three free directions (a rigid motion of
   everything), JᵀJ is singular and GN wanders. Fig. 12's caption says this.
4. **Jacobian of the residual, with the residual's sign.** The paper writes residuals as measurement − expectation,
   so every block is minus the expectation's Jacobian. manif's example writes expectation − measurement and flips the
   blocks instead. Either is right if r and J agree; mixing them makes GN climb. The checker compares the whole J with
   finite differences of r through the composite ⊕ (`C9_J_fd`).
5. **Stop on the step norm and cap the iterations.** ‖δx‖ < 10⁻⁶ and at most 20 iterations, as in manif's example. On
   the checker's synthetic version of Fig. 12 (start perturbed by 0.1 m and 0.1 rad standard deviation), GN stops
   after 4 iterations and the cost falls from 481.4 to 1.07 (`C9_iterations`, `C9_cost_init_final`).
6. **The calibration column is constant.** With c additive in u (111), D c/D c = [[−1, 0], [0, 0], [0, −1]] does not
   depend on the state; only Ω^{T/2} multiplies it.

**Eigen.**

```cpp
#include <Eigen/SparseCore>
#include <Eigen/SparseQR>
#include <Eigen/OrderingMethods>
inline Eigen::VectorXd gnStep(const Eigen::SparseMatrix<double>& J, const Eigen::VectorXd& r) {
  Eigen::SparseQR<Eigen::SparseMatrix<double>, Eigen::COLAMDOrdering<int>> qr;
  qr.compute(J);                                   // J must be in compressed mode
  return qr.solve(-r);                             // (108): argmin ||r + J dx||
}
```

**Cost per step.** Linearization: O(number of factors) block evaluations. Solve: dense QR of a 19×15 matrix is
trivial; for N poses and L beacons the sparse solve costs about O((N + L)^1.5) for planar problems with a nested-dissection ordering (George, *SIAM J. Numer. Anal.* 10, 1973), against O(n³)
dense.

**What breaks first.** (1) No prior: singular JᵀJ. (2) A sign mismatch between residual and Jacobian: the cost goes up
in the first iteration. (3) Explicit (JᵀJ)⁻¹ on a larger problem: slow, then inaccurate as the condition number
squares. (4) A start too far away for GN: add Levenberg-Marquardt damping (not in the paper).

**In the original code.** `examples/se2_sam.cpp` is §V-B in C++. The prior residual is
`poses[0].lminus(SE2d::Identity(), …)` at `:471`, a left minus, with a long comment above it explaining when a prior
should use left or right ⊖ (they coincide for the identity prior used there). The motion factor is
`d  = Xj.rminus(Xi, J_d_xj, J_d_xi);` at `:490`, which returns the blocks (82)–(83); the beacon factor is
`e       = Xi.inverse(J_ix_x).act(b, J_e_ix, J_e_b);` at `:516` with the chain rule on the next line. The solve is
`dX = - (J.transpose() * J).inverse() * J.transpose() * r;` at `:541`, under the authors' own warning at `:540`:
"ATTENTION: Use QR factorization and column reordering for larger problems!!". It stops at
`if (dX.norm() < 1e-6) break;` (`:568`), with `MAX_ITER = 20` (`:228`). §V-C is `examples/se3_sam_selfcalib.cpp`, in
3D. There the offset is added, `u_corr = u + J_u_c * c` (`:509`), where the paper subtracts it in (111), so the
calibration block is `- W * J_u_c` (`:514`) with `J_u_c(0,0) = 1.0` (`:278`); the sign of c is the opposite of the paper's.
https://github.com/artivis/manif/blob/65166b3bfd15b1020c29f3eaf6888e1009c79aea/examples/se2_sam.cpp#L465-L570
