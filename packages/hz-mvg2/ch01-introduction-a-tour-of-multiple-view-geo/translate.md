---
lesson: t3.1   # proposed; see map.md
title: Equation-to-code cards — a tour of multiple view geometry
source: Hartley & Zisserman, Multiple View Geometry in Computer Vision, 2nd ed., ch. 1 (pp. 1–22)
oracle: dense reference formulas (F from (9.1), ω from Result 8.17), SVD null vectors, and direct projection; no vision library is used
numbers: figures/card_numbers.py → figures/card_numbers.json (it executes every Python block in this file)
status: draft
---

# Equation-to-code cards

Each card: every symbol with its shape, a naive version you can read against the page, a robust version with the tricks named, the C++/Eigen version, the cost, and what breaks first. Cards are in the order you implement them; `exercises/exercise.py` follows the same order.

Chapter 1 is a tour: two numbered equations, (1.1) and (1.2), and a dozen unnumbered ones. The cards cover every formula the chapter states for the must-read sections (1.1–1.3, 1.7). Where the chapter only names a computation (F from two cameras, triangulation, ray angles, the upgrade from projective to metric), the card takes the formula from the chapter the book points to and says so; those page numbers are printed pages of the same book. The trifocal relation (1.2) belongs to a skim section and has no card; it gets a full treatment in chapters 15–16.

Conventions for every card:

- Points are rows. A batch of N points in ℙ² is an N×3 array, in ℙ³ an N×4 array, so a map acts as `X @ H.T`. A single point is a 1-D array.
- Everything stays homogeneous until a pixel or a metre is needed. Division by the last coordinate happens once, at the end.
- `P` is a 3×4 camera, `H` a homography (3×3) or a projective transformation of space (4×4), `F` the fundamental matrix, `omega` the IAC ω, `Omega` the absolute conic Ω∞. None of them is a covariance or a Jacobian.
- The synthetic camera is the lecture's: K with f = 500 px, principal point (320, 240), image 640 × 480 px. H&Z's P = K[R | t] maps world to camera (eq. 6.8, p. 156); a GTSAM `Pose3` is the camera in the world, the inverse.

Two derivations are left out on purpose because they are T2 exercises: why two images from one centre differ by a homography (C4 gives only the special case p. 204 states), and why H in (1.1) must be non-singular (C5 gives the check, not the argument).

Every number below comes from `figures/card_numbers.py` (`figures/card_numbers.json`).

---

## C1. Homogeneous coordinates and X′ = HX, pp. 2–3

**Shapes.** A point of ℙ² is x = (x, y, w)ᵀ ∈ ℝ³ \ {0}; a point of ℙ³ is X = (X, Y, Z, T)ᵀ ∈ ℝ⁴ \ {0}. Batches: N×3, N×4. H is (n+1)×(n+1), non-singular, defined up to scale: 8 DoF for 3×3, 15 for 4×4.

**Naive (reads like the book).**

```python
import numpy as np

def hom_naive(x):               # (x, y) -> (x, y, 1): "add an extra coordinate", p. 2
    return np.append(x, 1.0)

def dehom_naive(xh):            # (kx, ky, k) -> (x, y): "dividing by k", p. 2
    return xh[:-1] / xh[-1]

def at_infinity_naive(xh):      # points at infinity: "the last coordinate is zero", p. 2
    return xh[-1] == 0

def transform_naive(H, X):      # X' = H_{(n+1)x(n+1)} X, p. 3
    return H @ X
```

**Robust.**

```python
import numpy as np

def hom(x):
    x = np.atleast_2d(np.asarray(x, float))
    return np.hstack([x, np.ones((len(x), 1))])

def normalize_h(Xh):
    """Unit-norm representative of each row; the scale k of p. 2 is fixed to 1/||X||."""
    Xh = np.atleast_2d(np.asarray(Xh, float))
    return Xh / np.linalg.norm(Xh, axis=1, keepdims=True)

def at_infinity(Xh, tol=1e-12):
    """Scale-free test: |last coordinate| relative to the whole vector."""
    return np.abs(normalize_h(Xh)[:, -1]) < tol

def dehom(Xh, tol=1e-12):
    Xh = np.atleast_2d(np.asarray(Xh, float))
    if np.any(at_infinity(Xh, tol)):
        raise ValueError("point at infinity: keep it homogeneous")
    return Xh[:, :-1] / Xh[:, -1:]

def same_point(a, b, tol=1e-9):
    """Equality in P^n: equal up to a non-zero scale, sign included."""
    a, b = normalize_h(a)[0], normalize_h(b)[0]
    return min(np.linalg.norm(a - b), np.linalg.norm(a + b)) < tol

def transform(H, Xh, cond_max=1e12):
    if np.linalg.cond(H) > cond_max:
        raise ValueError("H is numerically singular; p. 3 requires a non-singular matrix")
    return np.atleast_2d(Xh) @ H.T            # rows are points: (H X)^T = X^T H^T

def compose(*Hs):
    """H_k ... H_2 H_1, renormalized after every product."""
    out = np.eye(Hs[0].shape[0])
    for H in Hs:
        out = H @ out
        out /= np.linalg.norm(out)
    return out
```

Tricks, each one named:

1. **Rows are points, multiply by Hᵀ.** One matrix product maps N points; the column form `H @ X` invites a Python loop.
2. **Scale-free infinity test.** Compare |w| with ‖x‖, not with 0 and not with an absolute epsilon. After one rotation a point at infinity has w = 1e-17, which `== 0` calls finite; an absolute threshold of 1e-12 calls (1e-13, 1e-13, 1e-13) infinite although it is the finite point (1, 1).
3. **Dehomogenize last.** A point with T → 0 is a legal point (a far landmark, a vanishing point). Divide only to display or to measure pixels and metres, and raise if the point is at infinity instead of returning `inf`.
4. **Equality up to scale and sign.** (kx, ky, k) with k < 0 is the same point (p. 2). Compare unit vectors up to ±; `np.allclose(a, b)` on raw homogeneous vectors is wrong.
5. **Renormalize compositions.** Products of homographies grow or shrink geometrically. Composing 500 random 3×3 homographies (entries N(0, 1) plus the identity) without renormalizing reaches a largest entry of about 10¹⁰¹; with `compose` the result has unit norm and the same direction.
6. **Check non-singularity.** p. 3 requires a non-singular H. A singular H collapses ℙⁿ onto a lower-dimensional subspace and nothing downstream warns you.

**Eigen.**

```cpp
#include <Eigen/Dense>
#include <stdexcept>

// Rows are points: N x 3 for P^2, N x 4 for P^3.
template <int D>
Eigen::Matrix<double, Eigen::Dynamic, D> transform_rows(
    const Eigen::Matrix<double, D, D>& H,
    const Eigen::Matrix<double, Eigen::Dynamic, D>& X) {
  return X * H.transpose();
}

template <int D>
bool at_infinity(const Eigen::Matrix<double, D, 1>& x, double tol = 1e-12) {
  return std::abs(x(D - 1)) < tol * x.norm();
}

inline Eigen::Vector2d dehom(const Eigen::Vector3d& x) {
  if (at_infinity<3>(x)) throw std::domain_error("point at infinity");
  return x.hnormalized();                  // divides by the last coordinate
}
// x.homogeneous() appends a 1; Eigen::Transform<double, 3, Eigen::Projective> holds a 4x4 H.
```

Fixed sizes (`Vector3d`, `Matrix<double, 4, 4>`) live on the stack. `hnormalized()` and `homogeneous()` are Eigen's built-ins for exactly p. 2's two operations.

**Cost.** O(N(n+1)²): 9 multiplies per ℙ² point, 16 per ℙ³ point. Never the bottleneck; the division and the infinity test cost as much as the product.

**What breaks first.** Division by w ≈ 0, which produces `inf` pixels and NaN errors downstream; then `==` or `allclose` equality on homogeneous vectors; then a long chain of homographies overflowing; then applying H to a line vector, which needs H⁻ᵀ (eq. 2.6, p. 36), and gets the horizon wrong.

---

## C2. Circular points, the absolute conic and conjugacy, pp. 5–6

**Shapes.** A conic C is 3×3 symmetric (6 entries, 5 DoF), the point set xᵀCx = 0. The circular points I, J = (1, ±i, 0)ᵀ ∈ ℂ³. Ω∞ is 3×3 symmetric on the plane at infinity; a direction d ∈ ℝ³ is the point (d, 0)ᵀ where a line meets that plane. In a Euclidean frame Ω∞ = I₃.

**Naive (reads like the book).**

```python
import numpy as np

def circle_form_naive(x, a, b, r):        # (x - a w)^2 + (y - b w)^2 = r^2 w^2, p. 5
    X, Y, W = x
    return (X - a * W) ** 2 + (Y - b * W) ** 2 - r ** 2 * W ** 2

I_PT = np.array([1, 1j, 0])               # (1, +i, 0)^T, p. 5
J_PT = np.array([1, -1j, 0])              # (1, -i, 0)^T

def perpendicular_naive(d1, d2, Omega=np.eye(3)):   # d1^T Omega_inf d2 = 0, p. 6
    return d1 @ Omega @ d2 == 0
```

**Robust.**

```python
import numpy as np

def circle_conic(a, b, r):
    """Matrix of the circle with centre (a, b, 1)^T and radius r, so that x^T C x is p. 5's form."""
    return np.array([[1.0, 0.0, -a],
                     [0.0, 1.0, -b],
                     [-a, -b, a * a + b * b - r * r]])

def conic_eval(C, x):
    return x @ C @ x                       # bilinear x^T C x; NOT x.conj() @ C @ x

def conic_transform(C, H):
    """Result 2.13, p. 37: under x' = H x a point conic maps to C' = H^-T C H^-1."""
    Hinv_C = np.linalg.solve(H.T, C)       # H^-T C
    Cp = np.linalg.solve(H.T, Hinv_C.T).T  # (H^-T (H^-T C)^T)^T = H^-T C H^-1
    Cp = 0.5 * (Cp + Cp.T)
    return Cp / np.linalg.norm(Cp)

def conjugacy(d1, d2, Omega=np.eye(3)):
    """Scale-free version of d1^T Omega d2: the cosine of (3.23), p. 82. 0 means perpendicular."""
    return (d1 @ Omega @ d2) / np.sqrt((d1 @ Omega @ d1) * (d2 @ Omega @ d2))

def perpendicular(d1, d2, Omega=np.eye(3), tol=1e-9):
    return abs(conjugacy(d1, d2, Omega)) < tol
```

Tricks, each one named:

1. **Bilinear, not Hermitian.** The incidence test is xᵀCx with a plain transpose. `@` and `np.dot` do not conjugate; `np.vdot` and `x.conj().T` do. On the circle centre (2, −1), radius 3, `conic_eval` at I gives 0.0; the Hermitian form gives 2.0, and you would conclude the circular points are not on the circle.
2. **The conic as a matrix.** Expanding p. 5's form into the symmetric C turns "lies on the circle" into one quadratic form and makes the transform rule a matrix product. C is defined up to scale; normalize it before comparing two conics.
3. **Transform with H⁻ᵀCH⁻¹, by solves.** Result 2.13 (p. 37). Two `solve` calls instead of `inv`, then symmetrize: round-off breaks symmetry, and a non-symmetric C has an antisymmetric part that xᵀCx ignores but eigen-solvers do not.
4. **Scale-free conjugacy.** d₁ᵀΩ∞d₂ scales with ‖d₁‖‖d₂‖ and with Ω∞'s arbitrary scale. Threshold the normalized ratio, which is the cosine of (3.23) (p. 82), never the raw product.
5. **Ω∞ is I only in a Euclidean frame.** p. 6 says the equations X² + Y² + Z² = 0, T = 0 hold "only in the Euclidean coordinate system". In a projective or affine reconstruction Ω∞ is some other symmetric matrix (C9 computes it); hard-coding `np.eye(3)` there gives wrong angles with no error.

**Eigen.**

```cpp
#include <Eigen/Dense>
#include <complex>

using C3 = Eigen::Vector3cd;

// x^T C x without conjugation. Eigen's a.dot(b) conjugates a for complex scalars, so do not use it here.
inline std::complex<double> conic_eval(const Eigen::Matrix3d& C, const C3& x) {
  return (x.transpose() * C.cast<std::complex<double>>() * x)(0, 0);
}

// Result 2.13: C' = H^-T C H^-1, via an LU of H^T.
inline Eigen::Matrix3d conic_transform(const Eigen::Matrix3d& C, const Eigen::Matrix3d& H) {
  const Eigen::PartialPivLU<Eigen::Matrix3d> luHt(H.transpose());
  const Eigen::Matrix3d HtinvC = luHt.solve(C);                          // H^-T C
  Eigen::Matrix3d Cp = luHt.solve(HtinvC.transpose()).transpose();       // H^-T C H^-1
  Cp = (0.5 * (Cp + Cp.transpose())).eval();
  return Cp / Cp.norm();
}

inline double conjugacy(const Eigen::Vector3d& d1, const Eigen::Vector3d& d2,
                        const Eigen::Matrix3d& Omega) {
  return d1.dot(Omega * d2) / std::sqrt(d1.dot(Omega * d1) * d2.dot(Omega * d2));
}
```

`.eval()` on the symmetrize line avoids aliasing between `Cp` and `Cp.transpose()`. For complex vectors Eigen's `dot` is conjugate-linear in its first argument, the same trap as `np.vdot`.

**Cost.** O(1): 3×3 products and one 3×3 LU. Trivial.

**What breaks first.** Conjugating the complex circular points; then hard-coding Ω∞ = I in a frame that is not Euclidean; then thresholding the raw d₁ᵀΩ∞d₂, which fails as soon as the directions are not unit vectors; then taking a line's direction from two homogeneous points without dehomogenizing them first (the direction is X̃₂/T₂ − X̃₁/T₁, not X̃₂ − X̃₁).

---

## C3. Central projection x = PX and the camera centre, p. 7

**Shapes.** P is 3×4 of rank 3 (11 DoF). X ∈ ℝ⁴ (N×4), x ∈ ℝ³ (N×3). The centre C ∈ ℝ⁴ is the null vector, PC = 0. For a finite camera P = K[R | t] with K 3×3 upper triangular, R ∈ SO(3), t = −RC̃ ∈ ℝ³ (eq. 6.8, p. 156); M = KR is the left 3×3 block.

**Naive (reads like the book).**

```python
import numpy as np

P0_naive = np.hstack([np.eye(3), np.zeros((3, 1))])   # P = [I_3x3 | 0_3], p. 7

def project_naive(P, X):          # (x, y, w)^T = P_3x4 (X, Y, Z, T)^T, p. 7
    x = P @ X
    return x[:2] / x[2]
```

**Robust.**

```python
import numpy as np

def make_camera(K, R, C_tilde):
    """P = K [R | t], t = -R C~ (eq. 6.8, p. 156). R maps world to camera."""
    return K @ np.hstack([R, (-R @ C_tilde)[:, None]])

def project(P, Xh):
    """Homogeneous image points, rows. Dehomogenize with C1's dehom only when pixels are needed."""
    return np.atleast_2d(Xh) @ P.T

def camera_centre(P, rank_tol=1e-12):
    """Null vector of P, unit norm (PC = 0)."""
    _, s, Vt = np.linalg.svd(P)
    if s[2] < rank_tol * s[0]:
        raise ValueError("rank P < 3: not a camera (p. 7)")
    return Vt[-1]

def depth(P, Xh):
    """Result 6.1, eq. 6.15, p. 162: depth = sign(det M) w / (T ||m3||). Negative: behind the camera."""
    Xh = np.atleast_2d(Xh)
    M = P[:, :3]
    w = Xh @ P[2]
    return np.sign(np.linalg.det(M)) * w / (Xh[:, 3] * np.linalg.norm(M[2]))
```

Tricks, each one named:

1. **Return homogeneous points.** `project` stops at x = PX. A point on the camera's principal plane has w = 0 and images to a point at infinity; C1's `dehom` raises there instead of returning `inf`.
2. **Centre by SVD, with a rank check.** The null vector of P is C: PC = 0, and rank 3 (p. 7) makes it unique up to scale. Page 7 only gives the rank and the centre (0, 0, 0, 1)ᵀ of [I | 0]; PC = 0 in general is §6.2.1, p. 158. The SVD gives it for any P, finite or not, and the ratio s₃/s₁ tells you when an estimated P has lost rank. `-inv(M) @ p4` fails for a camera whose centre is at infinity.
3. **Cheirality by eq. 6.15.** A projective camera images every point of a ray through C to the same pixel, including the points behind C; and (X, Y, Z, T) and its negative are one point of ℙ³, so the sign of the homogeneous vector carries nothing either. The sign of depth(X; P) is the only thing that says "in front". Triangulated points with negative depth are the first sign of a wrong (R, t) choice.
4. **Pose convention at the boundary.** H&Z's R, t map world to camera. A robot pose (GTSAM `Pose3`, ROS TF) is the camera in the world: R_HZ = R_wcᵀ and C̃ = t_wc. Convert once, in one function, and test it with a point straight ahead of the camera.
5. **Batch rows.** `Xh @ P.T` projects N points with one product.

**Eigen.**

```cpp
#include <Eigen/Dense>
#include <stdexcept>

using Mat34 = Eigen::Matrix<double, 3, 4>;

inline Mat34 make_camera(const Eigen::Matrix3d& K, const Eigen::Matrix3d& R, const Eigen::Vector3d& C) {
  Mat34 Rt;
  Rt << R, -R * C;
  return K * Rt;
}

inline Eigen::Vector4d camera_centre(const Mat34& P) {
  const Eigen::JacobiSVD<Mat34> svd(P, Eigen::ComputeFullV);
  const auto& s = svd.singularValues();
  if (s(2) < 1e-12 * s(0)) throw std::domain_error("rank P < 3");
  return svd.matrixV().col(3);
}

inline double depth(const Mat34& P, const Eigen::Vector4d& X) {
  const Eigen::Matrix3d M = P.leftCols<3>();
  const double w = P.row(2).dot(X);
  const double s = M.determinant() > 0 ? 1.0 : -1.0;
  return s * w / (X(3) * M.row(2).norm());
}
```

`ComputeFullV` is required: the null vector of a 3×4 matrix is the fourth column of the full V, which the thin SVD drops.

**Cost.** 12 multiplies per point for x = PX. The 3×4 SVD is a constant, done once per camera.

**What breaks first.** Points behind the camera landing on plausible pixels (no cheirality check); then the pose-convention inversion between H&Z and your robot stack; then points on or near the principal plane producing `inf`; then an estimated P that is close to rank 2 giving a centre that jumps between frames.

---

## C4. Homographies from cameras: a scene plane and a shared centre, pp. 7–9

**Shapes.** P = [p₁ p₂ p₃ p₄] with columns pᵢ ∈ ℝ³. H₃ₓ₃ maps (X, Y, T)ᵀ on the plane Z = 0 to (x, y, w)ᵀ in the image. Fig. 1.1c's H′₃ₓ₃ maps image points x to x′ between two cameras with one centre. Both are non-singular 3×3, 8 DoF.

**Naive (reads like the book).**

```python
import numpy as np

def plane_homography_naive(P):       # Z = 0: (x, y, w)^T = H_3x3 (X, Y, T)^T, p. 7
    return P[:, [0, 1, 3]]           # drop the column that multiplies Z

def rotation_homography_naive(K, R_rel):   # Fig. 1.1c, same centre: x' = H' x; H' = K R K^-1, p. 204
    return K @ R_rel @ np.linalg.inv(K)
```

**Robust.**

```python
import numpy as np
from scipy.linalg import solve_triangular

def plane_homography(P, cond_max=1e12):
    H = P[:, [0, 1, 3]]
    if np.linalg.cond(H) > cond_max:
        raise ValueError("the plane Z = 0 passes through the camera centre: its image is a line")
    return H / np.linalg.norm(H)

def rotation_homography(K, R_rel):
    """H' = K R K^-1 (p. 204) for one calibration K and a pure rotation R_rel between the views."""
    KR = K @ R_rel
    H = solve_triangular(K.T, KR.T, lower=True).T   # (K^-T (K R)^T)^T = K R K^-1, K upper triangular
    return H / np.linalg.norm(H)

def apply_homography(H, x):
    return np.atleast_2d(x) @ H.T          # points; lines map by H^-T (eq. 2.6, p. 36)

def transfer_rms_px(H, x1, x2):
    """RMS pixel distance between H x1 and x2. The test of whether one H explains two views."""
    y = apply_homography(H, x1)
    d = y[:, :2] / y[:, 2:] - x2[:, :2] / x2[:, 2:]
    return np.sqrt(np.mean(np.sum(d ** 2, axis=1)))
```

Tricks, each one named:

1. **Pick columns, do not fit.** H = [p₁ p₂ p₄] is exact for Z = 0. Fitting H from correspondences is chapter 4 (DLT with normalization, Algorithm 4.2, p. 109); use it only when the cameras are unknown.
2. **Plane through the centre.** If the centre lies on Z = 0, [p₁ p₂ p₄] has rank 2 and the plane images to a line. The condition number catches it; a ground plane seen by a camera at zero height is the robot case.
3. **Triangular solve for K⁻¹.** K is upper triangular, so K⁻¹ is a back-substitution, not a general inverse.
4. **Frobenius normalization.** Scale H by ‖H‖_F, not by H₃₃: H₃₃ is zero whenever the plane's origin images to a point at infinity, and dividing by it destroys the matrix.
5. **Measure the fit in pixels.** Whether one H explains two views is a pixel question (`transfer_rms_px`). In the lecture's scene (L3), a depth range of 4–12 m and f = 500 px keep a single H within 1 px up to 0.048 m of baseline.

The general shared-centre H′ for two different calibrations is T2's derivation; do it before you generalize `rotation_homography`.

**Eigen.**

```cpp
#include <Eigen/Dense>

inline Eigen::Matrix3d plane_homography(const Eigen::Matrix<double, 3, 4>& P) {
  Eigen::Matrix3d H;
  H << P.col(0), P.col(1), P.col(3);
  return H / H.norm();
}

inline Eigen::Matrix3d rotation_homography(const Eigen::Matrix3d& K, const Eigen::Matrix3d& R) {
  // K R K^-1 = ((K^T)^-1 (K R)^T)^T ; K^T is lower triangular
  const Eigen::Matrix3d KR = K * R;
  Eigen::Matrix3d H = K.transpose().triangularView<Eigen::Lower>().solve(KR.transpose()).transpose();
  return H / H.norm();
}
```

**Cost.** O(1) to form; 9 multiplies per point to apply.

**What breaks first.** Using an H between two views whose centres differ and whose scene is not planar (residual grows with baseline, L3); then normalizing by H₃₃ on a plane whose origin is near the horizon; then mapping lines with H instead of H⁻ᵀ; then a ground plane seen from nearly zero height, where H is close to singular.

---

## C5. Projective ambiguity, eq. (1.1), p. 11

**Shapes.** Cameras P_j 3×4, points X_i ∈ ℝ⁴ (N×4), H 4×4 non-singular (15 DoF). The transformed reconstruction is {P_j H⁻¹}, {H X_i}.

**Naive (reads like the book).**

```python
import numpy as np

def apply_ambiguity_naive(Ps, X, H):     # P_j X_i = (P_j H^-1)(H X_i), (1.1)
    Hinv = np.linalg.inv(H)
    return [P @ Hinv for P in Ps], [H @ Xi for Xi in X]
```

**Robust.**

```python
import numpy as np

def apply_ambiguity(Ps, Xh, H, cond_max=1e10):
    if np.linalg.cond(H) > cond_max:
        raise ValueError("H is numerically singular")
    # P H^-1 = (H^-T P^T)^T: one LU of H^T, no explicit inverse
    Ps_new = [np.linalg.solve(H.T, P.T).T for P in Ps]
    Ps_new = [P / np.linalg.norm(P) for P in Ps_new]
    Xh_new = np.atleast_2d(Xh) @ H.T
    Xh_new /= np.linalg.norm(Xh_new, axis=1, keepdims=True)
    return Ps_new, Xh_new

def max_reprojection_change_px(Ps, Xh, Ps_new, Xh_new):
    """Largest pixel difference between the two reconstructions' images: the oracle for (1.1)."""
    worst = 0.0
    for P, Pn in zip(Ps, Ps_new):
        a = np.atleast_2d(Xh) @ P.T
        b = np.atleast_2d(Xh_new) @ Pn.T
        worst = max(worst, np.max(np.abs(a[:, :2] / a[:, 2:] - b[:, :2] / b[:, 2:])))
    return worst

def crosses_infinity(Xh, H):
    """True for points on the minority side of the plane H sends to infinity (its 4th row, h4)."""
    Xh = np.atleast_2d(Xh)
    Xh = Xh * np.sign(Xh[:, 3:])          # representative with T > 0 (finite points)
    side = Xh @ H[3]                      # T' = h4^T X, up to a positive scale
    return np.sign(side) != np.sign(np.median(side))
```

Tricks, each one named:

1. **Solve, do not invert.** P H⁻¹ is (H⁻ᵀPᵀ)ᵀ, one LU of Hᵀ shared by every camera.
2. **Compare pixels, not matrices.** P H⁻¹ and P differ entry by entry; only their images agree. The oracle for (1.1) is the pixel difference after dehomogenizing, which the lecture's L5 cubes put at 8.5 × 10⁻¹⁴ px.
3. **Conditioning sets the floor.** With cond(H) = 10, the largest pixel change on the C6 scene is 5.7 × 10⁻¹³ px; with cond(H) = 10⁸ it is 1.1 × 10⁻⁶ px. (1.1) is exact in algebra, not in floating point; an ill-conditioned H loses digits in both the forward map and the solve.
4. **Watch the plane at infinity.** A general H sends some plane to infinity. That plane is h₄ᵀX = 0, with h₄ᵀ the fourth row of H. Points on opposite sides of it end up with opposite signs of T, and a wireframe drawn after dehomogenizing joins them "through infinity": the turned-inside-out shapes at the extremes of Fig. 1.4. `crosses_infinity` flags them; the fix is to keep the reconstruction homogeneous or choose H with the plane it sends to infinity away from the scene.
5. **Renormalize both sides.** Unit-norm cameras and points keep later SVDs (C6, C7) well scaled.

**Eigen.**

```cpp
#include <Eigen/Dense>
#include <vector>

using Mat34 = Eigen::Matrix<double, 3, 4>;

inline void apply_ambiguity(std::vector<Mat34>& Ps, Eigen::Matrix<double, Eigen::Dynamic, 4>& X,
                            const Eigen::Matrix4d& H) {
  const Eigen::PartialPivLU<Eigen::Matrix4d> luHt(H.transpose());
  for (auto& P : Ps) {
    Mat34 Pn = luHt.solve(P.transpose()).transpose();   // P H^-1
    P = Pn / Pn.norm();
  }
  X = (X * H.transpose()).eval();                        // rows: (H X)^T
  X.rowwise().normalize();
}
```

`.eval()` because `X` appears on both sides.

**Cost.** One 4×4 LU, then 48 multiplies per camera and 16 per point.

**What breaks first.** Comparing camera matrices instead of reprojections; then an ill-conditioned H losing digits; then plotting a projective reconstruction whose points straddle the plane H sends to infinity; then forgetting that any metric number (length, angle) computed from a projective reconstruction is meaningless until C9.

---

## C6. The epipolar constraint x′ᵀFx = 0 and det F = 0, pp. 11–13

**Shapes.** F is 3×3 of rank 2, defined up to scale: 9 − 1 − 1 = 7 DoF. x, x′ ∈ ℝ³ (N×3). The epipole e′ = P′C ∈ ℝ³ with e′ᵀF = 0. Step (i)'s design row a ∈ ℝ⁹; stacked, A is N×9. P⁺ is the 4×3 pseudo-inverse of P.

**Naive (reads like the book).**

```python
import numpy as np

def epipolar_residual_naive(F, x, xp):   # x'_i^T F x_i = 0, p. 11
    return xp @ F @ x

def det_F_naive(F):                      # det F = 0, p. 13
    return np.linalg.det(F)

def F_row_naive(x, xp):                  # step (i), p. 12: one linear equation in the 9 entries of F
    return np.kron(xp, x)                # a . F.ravel() == x'^T F x  (row-major)
```

The chapter does not say how to get F from two cameras; that is eq. (9.1), p. 244: F = [e′]× P′P⁺ with e′ = P′C. `exercises/models.py` uses it as the reference F.

**Robust.**

```python
import numpy as np

def skew(v):
    return np.array([[0.0, -v[2], v[1]], [v[2], 0.0, -v[0]], [-v[1], v[0], 0.0]])

def F_from_cameras(P1, P2):
    """Eq. (9.1), p. 244: F = [e']_x P' P^+, e' = P' C. Unit Frobenius norm, sign fixed."""
    C1 = camera_centre(P1)                       # C3
    e2 = P2 @ C1
    if np.linalg.norm(e2) < 1e-12 * np.linalg.norm(P2):
        raise ValueError("same camera centre: F is the zero matrix (p. 244); use C4's homography")
    F = skew(e2) @ P2 @ np.linalg.pinv(P1)
    F /= np.linalg.norm(F)
    return F * np.sign(F.flat[np.argmax(np.abs(F))])

def epipolar_distance_px(F, x, xp):
    """Distance in pixels from x' to the epipolar line l' = F x (both points with w = 1)."""
    x, xp = np.atleast_2d(x), np.atleast_2d(xp)
    l = x @ F.T
    return np.abs(np.sum(xp * l, axis=1)) / np.hypot(l[:, 0], l[:, 1])

def rank2_gap(F):
    """sigma_3 / sigma_1: a scale-free det F = 0 test."""
    s = np.linalg.svd(F, compute_uv=False)
    return s[2] / s[0]

def normalize_pts(x):
    """Algorithm 11.1 (p. 282) / 4.2 (p. 109): centroid to 0, RMS distance sqrt(2). Returns (T x, T)."""
    xy = x[:, :2] / x[:, 2:]
    c = xy.mean(axis=0)
    s = np.sqrt(2) / np.sqrt(np.mean(np.sum((xy - c) ** 2, axis=1)))
    T = np.array([[s, 0, -s * c[0]], [0, s, -s * c[1]], [0, 0, 1]])
    return hom(xy) @ T.T, T

def F_design(x, xp):
    """Step (i): rows kron(x', x). Call it on normalized points."""
    return np.einsum("ni,nj->nij", xp, x).reshape(len(x), 9)
```

Tricks, each one named:

1. **Pixels, not algebra.** x′ᵀFx scales with F's arbitrary scale and with the pixel coordinates (≈ 320² for a 640-px image). On the C6 scene with 1 px Gaussian noise, the algebraic residual of unit-norm F has median 0.038 while the epipolar distance has median 1.1 px. Threshold the distance; it has units.
2. **Scale-free rank test.** det F scales as the cube of F's scale. Test σ₃/σ₁ instead: 1.3 × 10⁻¹⁸ for F from (9.1) on the C6 cameras.
3. **Same centre means F = 0.** p. 244 says (9.1) breaks down when the centres coincide: P′C = 0 and F is the zero matrix. Check ‖e′‖ before trusting F; pure rotation is C4's case.
4. **Normalize before step (i).** The chapter warns its outline "should not be implemented directly" (p. 12). On the C6 matches in raw pixels the 9-column design matrix A has condition number 1.8 × 10⁵; after Algorithm 11.1's normalization, 21 (both ratios σ₁/σ₈, since σ₉ = 0 on exact data). Solving A f = 0 by SVD and enforcing rank 2 is Algorithm 11.1, chapter 11; this chapter only asks you to verify x′ᵀFx = 0 for a given F.
5. **Compare F up to scale and sign.** Normalize to unit Frobenius norm and fix the sign by the largest entry, as `F_from_cameras` does. The lecture's L5 F-change numbers use exactly this.

**Eigen.**

```cpp
#include <Eigen/Dense>
#include <stdexcept>

inline Eigen::Matrix3d skew(const Eigen::Vector3d& v) {
  Eigen::Matrix3d S;
  S << 0, -v(2), v(1), v(2), 0, -v(0), -v(1), v(0), 0;
  return S;
}

inline Eigen::Matrix3d F_from_cameras(const Eigen::Matrix<double, 3, 4>& P1,
                                      const Eigen::Matrix<double, 3, 4>& P2) {
  const Eigen::JacobiSVD<Eigen::Matrix<double, 3, 4>> svd(P1, Eigen::ComputeFullU | Eigen::ComputeFullV);
  const Eigen::Vector4d C1 = svd.matrixV().col(3);
  const Eigen::Vector3d e2 = P2 * C1;
  if (e2.norm() < 1e-12 * P2.norm()) throw std::domain_error("same centre: F = 0");
  // P1^+ from the SVD: V_3 S_3^-1 U^T
  const Eigen::Matrix<double, 4, 3> P1pinv =
      svd.matrixV().leftCols<3>() * svd.singularValues().cwiseInverse().asDiagonal() *
      svd.matrixU().transpose();
  Eigen::Matrix3d F = skew(e2) * P2 * P1pinv;
  return F / F.norm();
}

inline double epipolar_distance_px(const Eigen::Matrix3d& F, const Eigen::Vector3d& x,
                                   const Eigen::Vector3d& xp) {
  const Eigen::Vector3d l = F * x;
  return std::abs(xp.dot(l)) / l.head<2>().norm();
}
```

The pseudo-inverse reuses the SVD that gave the centre. A rank-3 P has three non-zero singular values, so `cwiseInverse` is safe once the C3 rank check has passed.

**Cost.** Forming F: one 3×4 SVD. Residuals: 9 multiplies per match for Fx plus a dot product. Building A: 9 per match; its SVD is O(N·81), linear in N.

**What breaks first.** Thresholding the algebraic residual; then a near-pure-rotation pair (tiny baseline) where F is poorly defined and the epipole wanders; then an unnormalized step (i) on raw pixels; then a planar scene, a critical configuration for F (p. 11), where an H explains the matches better (L3, L7).

---

## C7. Triangulation, step (iv) p. 12, and transfer x″ = P″X, p. 16

**Shapes.** P, P′ 3×4; a match x ↔ x′ with w = 1; A is 4×4 (two rows per view, §12.2, p. 312), more rows for more views; X ∈ ℝ⁴ the right singular vector of A for its smallest singular value. Transfer: P″ 3×4, x″ ∈ ℝ³.

**Naive (reads like the book).**

```python
import numpy as np

def triangulate_naive(P1, P2, x1, x2):        # x x (P X) = 0, two rows per view, Sec. 12.2, p. 312
    A = np.vstack([x1[0] * P1[2] - P1[0],
                   x1[1] * P1[2] - P1[1],
                   x2[0] * P2[2] - P2[0],
                   x2[1] * P2[2] - P2[1]])
    return np.linalg.svd(A)[2][-1]            # homogeneous method (DLT)

def transfer_naive(P3, X):                    # x'' = P'' X, p. 16, step (iii)
    return P3 @ X
```

**Robust.**

```python
import numpy as np

def triangulate(Ps, xs):
    """Homogeneous DLT for any number of views. Ps: list of 3x4, xs: list of homogeneous 3-vectors."""
    rows = []
    for P, x in zip(Ps, xs):
        x = x / x[2]
        rows += [x[0] * P[2] - P[0], x[1] * P[2] - P[1]]
    A = np.array(rows)
    A /= np.linalg.norm(A, axis=1, keepdims=True)      # row scaling: each equation weighs the same
    X = np.linalg.svd(A)[2][-1]
    return X / np.linalg.norm(X)                       # homogeneous; may lie on the plane at infinity

def triangulate_checked(Ps, xs, max_px=2.0):
    X = triangulate(Ps, xs)
    X = X * np.sign(X[3]) if abs(X[3]) > 0 else X      # T > 0 so that depth() signs are meaningful
    for P, x in zip(Ps, xs):
        if depth(P, X)[0] <= 0:                         # C3, eq. 6.15
            raise ValueError("triangulated point is behind a camera")
        y = P @ X
        if np.hypot(*(y[:2] / y[2] - x[:2] / x[2])) > max_px:
            raise ValueError("reprojection error too large: bad match or bad cameras")
    return X

def transfer(P3, X):
    return P3 @ X                                      # homogeneous; dehom at the end (C1)
```

Tricks, each one named:

1. **Homogeneous method, not inhomogeneous.** Setting X = (X, Y, Z, 1)ᵀ fails for points at or near the plane at infinity (p. 313), which a projective reconstruction can contain. For the point at infinity on camera 1's optical axis (T = 0: a star, a vanishing point), seen by the C6 pair, the homogeneous method returns it exactly (T and direction error both 0 to machine precision); the inhomogeneous least-squares solve returns a finite point 0.51 m from the origin that leaves a relative residual of 0.32, i.e. it satisfies none of the four equations.
2. **Row scaling.** Each row of A carries the pixel magnitude of x and the scale of P. Normalizing rows makes the four equations count equally; image-coordinate normalization (§4.4, p. 107) does the same job more thoroughly. On noise-free C6 matches, the recovered points match the true ones to 5 × 10⁻¹⁶ (largest ‖X − X_true‖ on unit-norm vectors, sign fixed).
3. **Check cheirality and reprojection.** The DLT returns a point for any pair of rays, including rays that diverge. Negative depth (eq. 6.15) or a large reprojection error means a bad match, not a bad algorithm.
4. **n views for free.** Two rows per view; the same code takes three or more views (p. 313: it "generalizes easily").
5. **It is not the optimal method.** The linear method is not projective-invariant (p. 313) and does not minimize image error; chapter 12's optimal method does. With 1 px noise on the C6 scene the linear method's median reprojection error is 0.56 px. Good enough to initialize BA, which is how p. 14 uses it.

**Eigen.**

```cpp
#include <Eigen/Dense>
#include <vector>

using Mat34 = Eigen::Matrix<double, 3, 4>;

inline Eigen::Vector4d triangulate(const std::vector<Mat34>& Ps, const std::vector<Eigen::Vector3d>& xs) {
  Eigen::Matrix<double, Eigen::Dynamic, 4> A(2 * Ps.size(), 4);
  for (size_t j = 0; j < Ps.size(); ++j) {
    const Eigen::Vector2d x = xs[j].hnormalized();
    A.row(2 * j)     = x(0) * Ps[j].row(2) - Ps[j].row(0);
    A.row(2 * j + 1) = x(1) * Ps[j].row(2) - Ps[j].row(1);
  }
  A.rowwise().normalize();
  const Eigen::JacobiSVD<Eigen::Matrix<double, Eigen::Dynamic, 4>> svd(A, Eigen::ComputeFullV);
  return svd.matrixV().col(3).normalized();
}
```

For two views use `Eigen::Matrix4d` for A; the dynamic version exists for n views.

**Cost.** One 2n×4 SVD per point, O(n). For N points over n views, O(Nn); in a real front end the matching costs far more than triangulation.

**What breaks first.** A small baseline: rays nearly parallel, depth poorly determined, A close to rank 2; then points behind a camera from a wrong (R, t) choice (the four-fold choice of §9.6); then the inhomogeneous method on far points; then noise, where the linear method's bias matters at long range and chapter 12's method or BA takes over.

---

## C8. Calibrated cameras: ω and the angle between rays, p. 9

**Shapes.** K 3×3 upper triangular. ω = (KKᵀ)⁻¹ 3×3 symmetric positive definite, defined up to scale (5 DoF). x₁, x₂ ∈ ℝ³ homogeneous pixels. θ ∈ [0, π] the angle between the back-projected rays. Ray directions d = K⁻¹x ∈ ℝ³ in the camera frame.

The chapter states the idea in words (p. 9: "knowing the IAC, one can measure the angle between rays by direct measurements in the image"). The formula is eq. (8.9), p. 210, with ω = (KKᵀ)⁻¹ from Result 8.17 on the same page.

**Naive (reads like the book).**

```python
import numpy as np

def omega_naive(K):                         # IAC: omega = (K K^T)^-1, Result 8.17, p. 210
    return np.linalg.inv(K @ K.T)

def ray_angle_naive(x1, x2, omega):         # eq. (8.9), p. 210
    c = (x1 @ omega @ x2) / np.sqrt((x1 @ omega @ x1) * (x2 @ omega @ x2))
    return np.arccos(c)
```

**Robust.**

```python
import numpy as np
from scipy.linalg import solve_triangular

def back_project(K, x):
    """Ray directions d = K^-1 x, rows. x^T omega x = ||K^-1 x||^2, so (8.9) is the cosine between rays d."""
    return solve_triangular(K, np.atleast_2d(x).T, lower=False).T

def ray_angle(K, x1, x2):
    d1, d2 = back_project(K, x1), back_project(K, x2)
    cross = np.linalg.norm(np.cross(d1, d2), axis=1)
    dot = np.sum(d1 * d2, axis=1)
    return np.arctan2(cross, dot)              # accurate at 0 and at pi; arccos is not

def ray_angle_omega(x1, x2, omega):
    """When only omega is known (no K): (8.9) with the cosine clipped into [-1, 1]."""
    c = (x1 @ omega @ x2) / np.sqrt((x1 @ omega @ x1) * (x2 @ omega @ x2))
    return np.arccos(np.clip(c, -1.0, 1.0))
```

Tricks, each one named:

1. **Back-project instead of forming ω.** xᵀωy = (K⁻¹x)ᵀ(K⁻¹y), so (8.9) is the cosine between the rays d = K⁻¹x. One triangular solve per point and no inverse of KKᵀ, whose condition number is the square of K's: cond(KKᵀ) = 6.7 × 10⁵ for the lecture's K, against cond(K) = 820.
2. **atan2, not arccos.** Near θ = 0 the cosine is 1 − θ²/2, so arccos loses about half the digits: the error is roughly ε/θ. In float32 (an embedded board), for two pixels 1 px apart near the image edge, the arccos form returns 1582.21 µrad and atan2 returns 1521.22 µrad; the true angle is 1521.24 µrad. In float64 the same pair is fine either way; the trap is single precision and sub-pixel angles.
3. **Clip the cosine** when ω is all you have: round-off pushes c to 1 + 1e-16 and arccos returns NaN.
4. **ω is defined up to scale.** (8.9) is a ratio, so the scale cancels; a test that checks ω entries directly must normalize first.
5. **Calibration error grows towards the edge.** The angle error from a wrong f is zero on the optical axis and largest at the edge: 6.04° at the image edge for an f 20% short (L4). Check K at the edge of the image, not the centre.

**Eigen.**

```cpp
#include <Eigen/Dense>
#include <cmath>

inline double ray_angle(const Eigen::Matrix3d& K, const Eigen::Vector3d& x1, const Eigen::Vector3d& x2) {
  const auto Ku = K.triangularView<Eigen::Upper>();
  const Eigen::Vector3d d1 = Ku.solve(x1);
  const Eigen::Vector3d d2 = Ku.solve(x2);
  return std::atan2(d1.cross(d2).norm(), d1.dot(d2));
}
```

**Cost.** Two 3×3 triangular solves (9 flops each) and a cross product per pair.

**What breaks first.** A stale K after a zoom or lens change (the camera is then uncalibrated in the book's sense, p. 9); then arccos at small angles, where bearings to distant landmarks live; then forming ω by inverting KKᵀ in single precision on an embedded board; then ignoring lens distortion (§7.4), which the pinhole ω cannot represent.

---

## C9. Climbing back: plane at infinity, then absolute conic, pp. 16–17

**Shapes.** A projective reconstruction: cameras P_j 3×4, points X_i ∈ ℝ⁴. π ∈ ℝ⁴ the plane at infinity in that frame. H_A 4×4 (affine upgrade). After it, a camera [M | m] with M 3×3. ω 3×3 the IAC of that camera; Ω∞ = MᵀωM 3×3 symmetric positive definite in the affine frame; L lower-triangular Cholesky factor; H_M 4×4 (metric upgrade). A similarity (7 DoF) remains.

The chapter has no equations here; p. 17 states the facts (Ω∞ lies on π∞, calibration is equivalent to Euclidean structure). The formulas are §10.4: eq. (10.2), p. 268, and Result 10.5, p. 272.

**Naive (reads like the book).**

```python
import numpy as np

def affine_upgrade_naive(pi):               # H = [ I | 0 ; pi^T ], eq. (10.2), p. 268
    return np.vstack([np.hstack([np.eye(3), np.zeros((3, 1))]), pi[None, :]])

def metric_upgrade_naive(M, omega):         # Result 10.5, p. 272: H = [A^-1 0; 0 1], A A^T = (M^T omega M)^-1
    A = np.linalg.cholesky(np.linalg.inv(M.T @ omega @ M))
    H = np.eye(4)
    H[:3, :3] = np.linalg.inv(A)
    return H
```

**Robust.**

```python
import numpy as np

def affine_upgrade(pi):
    """H with H^-T pi ~ (0,0,0,1)^T, by a Householder reflection (p. 268's fallback). Works when pi_4 = 0."""
    p = pi / np.linalg.norm(pi)
    e4 = np.array([0.0, 0.0, 0.0, 1.0])
    v = p + np.copysign(1.0, p[3]) * e4      # sign chosen so that p + s e4 never cancels
    Q = np.eye(4) - 2.0 * np.outer(v, v) / (v @ v)
    return Q                                 # Q symmetric orthogonal: H^-T = Q, and Q p = -s e4

def metric_upgrade(M, omega):
    """H_M = [L^T 0; 0 1] with Omega_inf = M^T omega M = L L^T. Equals Result 10.5's H up to a rotation: A = L^-T Q."""
    Omega = M.T @ omega @ M
    Omega = 0.5 * (Omega + Omega.T)
    if np.trace(Omega) < 0:
        Omega = -Omega                       # omega is defined up to scale, sign included
    L = np.linalg.cholesky(Omega)            # raises LinAlgError if not positive definite
    H = np.eye(4)
    H[:3, :3] = L.T
    return H

def upgrade(Ps, Xh, H):
    return apply_ambiguity(Ps, Xh, H)        # C5: cameras P H^-1, points H X
```

Tricks, each one named:

1. **Householder when π₄ is small.** (10.2) needs π₄ ≠ 0 (p. 268 says so and offers a Householder matrix instead). With π₄ = 10⁻¹⁴ (π normalized), cond(H) for (10.2) is 2 × 10¹⁴; the Householder H is orthogonal, cond 1.000. The Householder result differs from (10.2)'s by an affine transformation, so it is an equally valid affine reconstruction, and C9's next step removes the difference.
2. **One Cholesky, no inverses.** Result 10.5 inverts MᵀωM, factors it, then inverts the factor. Factoring Ω∞ = LLᵀ directly and using Lᵀ gives the same H up to a rotation: AAᵀ = (LLᵀ)⁻¹ = L⁻ᵀL⁻¹, so A = L⁻ᵀQ for some orthogonal Q (Result 10.5's lower-triangular A is one choice of Q). H_M = [Lᵀ 0; 0 1] differs from Result 10.5's H by that rotation, which is part of the similarity that remains anyway.
3. **Fix ω's sign.** An estimated ω has arbitrary scale, including sign. A negative-definite MᵀωM is the same conic; flip it before `cholesky`. If it is indefinite after the flip, the reconstruction was not affine or ω is wrong: stop.
4. **Upgrade cameras and points together.** Both steps are a 4×4 H applied as in (1.1): cameras P H⁻¹, points HX. Reuse C5.
5. **Oracle for the result.** After the metric upgrade the left 3×3 block M_M of the camera satisfies M_M M_Mᵀ ∝ KKᵀ = ω* (proof of Result 10.5, p. 272), and perpendicular scene edges pass C2's conjugacy test with Ω∞ = I. The lecture's L6 cube reaches 90.00° corners and an edge ratio of 1.000.

**Eigen.**

```cpp
#include <Eigen/Dense>
#include <stdexcept>

inline Eigen::Matrix4d affine_upgrade(const Eigen::Vector4d& pi) {
  const Eigen::Vector4d p = pi.normalized();
  const Eigen::Vector4d e4(0, 0, 0, 1);
  const Eigen::Vector4d v = p + std::copysign(1.0, p(3)) * e4;
  return Eigen::Matrix4d::Identity() - 2.0 * v * v.transpose() / v.squaredNorm();
}

inline Eigen::Matrix4d metric_upgrade(const Eigen::Matrix3d& M, const Eigen::Matrix3d& omega) {
  Eigen::Matrix3d Omega = M.transpose() * omega * M;
  Omega = (0.5 * (Omega + Omega.transpose())).eval();
  if (Omega.trace() < 0) Omega = -Omega;
  const Eigen::LLT<Eigen::Matrix3d> llt(Omega);
  if (llt.info() != Eigen::Success) throw std::domain_error("M^T omega M is not definite");
  Eigen::Matrix4d H = Eigen::Matrix4d::Identity();
  H.topLeftCorner<3, 3>() = llt.matrixL().transpose();
  return H;
}
```

`LLT`, not `LDLT`, on purpose: Ω∞ must be strictly definite, and `LLT` reports failure where `LDLT` would quietly accept a semidefinite matrix.

**Cost.** O(1) per upgrade (a 4×4 reflection, a 3×3 Cholesky), then C5's cost to apply it. Finding π and ω is the hard part (p. 18) and is chapters 10, 13 and 19.

**What breaks first.** A wrong π: parallel edges stay non-parallel and the metric step then fails its Cholesky or gives skewed corners; then π₄ near zero with (10.2); then ω with the wrong sign; then a correct upgrade judged wrong because the remaining similarity (scale, pose) was not removed before comparing with ground truth.
