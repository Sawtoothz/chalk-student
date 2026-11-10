"""T3 — Implementation. Fill every function marked TODO. Do not change signatures.

Oracle tests: `just test hz-mvg2 1` (or `pytest exercises/tests/test_T3.py -q` from the package dir).
Cards: translate.md C1–C9, same order as below. Clues: `just clue hz-mvg2 1 T3.<n> <1|2|3>`.

Conventions: points are rows (N×3 in ℙ², N×4 in ℙ³), so a map acts as `X @ H.T`. Stay homogeneous;
divide by the last coordinate only when a pixel or a metre is needed. P = K[R | t] maps world to camera.
Given in models.py (not exercises): hom, project, pixels, make_camera, rot, skew, the scenes.
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import solve_triangular  # noqa: F401  (you will want it for K)

from .models import hom, project  # noqa: F401


# ---------------------------------------------------------------- C1 homogeneous coordinates, p. 2


def dehom(Xh, tol=1e-12):
    """(kx, ky, k) → (x, y), p. 2, for a batch of ℙ² or ℙ³ points (rows; a 1-D input is one point).

    Return an (N, n) array. Raise ValueError if any point is at infinity, tested scale-free:
    |last coordinate| < tol · ‖X‖. Not `== 0`, not `abs(w) < tol`.
    """
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------- C2 circular points, p. 5


def circle_conic(a, b, r):
    """The symmetric 3×3 C with xᵀ C x = (x − aw)² + (y − bw)² − r²w² (p. 5).

    Centre (a, b), radius r. The tests then check that (1, ±i, 0)ᵀ lie on every such C.
    """
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------- C3 central projection, p. 7


def camera_centre(P, rank_tol=1e-12):
    """The centre C with P C = 0 (p. 7), as a unit-norm 4-vector (sign arbitrary).

    Must work for a camera whose centre is at infinity. Raise ValueError if rank P < 3,
    tested as σ₃ < rank_tol · σ₁.
    """
    raise NotImplementedError("TODO")


def depth(P, Xh):
    """Depth of each point in front of camera P (eq. 6.15, p. 162). Shape (N,). Negative = behind.

    Must not change when P or X is multiplied by any non-zero scalar, negative ones included.
    """
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------- C4 homographies, pp. 7–9


def plane_homography(P, cond_max=1e12):
    """H₃ₓ₃ with (x, y, w)ᵀ = H (X, Y, T)ᵀ for points on the plane Z = 0 (p. 7). Unit Frobenius norm.

    Raise ValueError when cond(H) > cond_max: the plane passes through the camera centre.
    """
    raise NotImplementedError("TODO")


def rotation_homography(K, R_rel):
    """H′ with x′ = H′ x between two views from one centre (Fig. 1.1c): H′ = K R K⁻¹ (p. 204).

    R_rel is the rotation of the second view relative to the first. No np.linalg.inv. Unit norm.
    """
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------- C5 projective ambiguity, eq. (1.1), p. 11


def apply_ambiguity(Ps, Xh, H, cond_max=1e10):
    """(1.1): cameras P_j → P_j H⁻¹, points X_i → H X_i. Return (list of 3×4, N×4), each unit norm.

    No np.linalg.inv. Raise ValueError if cond(H) > cond_max.
    """
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------- C6 epipolar constraint, p. 11


def epipolar_distance_px(F, x, xp):
    """Distance in pixels from each x′ to its epipolar line l′ = F x. x, xp: (N, 3) with w = 1.

    Shape (N,). Must not depend on the scale of F.
    """
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------- C7 triangulation, step (iv) p. 12; transfer p. 16


def triangulate(Ps, xs):
    """Homogeneous linear triangulation (§12.2, p. 312) from any number of views.

    Ps: list of 3×4; xs: list of homogeneous 3-vectors, any scale. Return a unit-norm 4-vector
    (sign arbitrary). It must return points at infinity (T = 0) when that is the answer.
    """
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------- C8 calibrated camera, p. 9


def ray_angle(K, x1, x2):
    """Angle (rad) between the back-projected rays of pixels x1 and x2 (eq. 8.9, p. 210). Shape (N,).

    Accurate to 1e-12 rad at sub-pixel separations: not arccos.
    """
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------- C9 affine and metric upgrade, pp. 16–17


def affine_upgrade(pi):
    """A 4×4 H with H⁻ᵀ π ∝ (0, 0, 0, 1)ᵀ (§10.4, p. 268): sends the plane π to infinity.

    Must stay well conditioned (cond < 1e3) when π₄ ≈ 0 or π₄ = 0.
    """
    raise NotImplementedError("TODO")


def metric_upgrade(M, omega):
    """4×4 H = [A 0; 0 1] such that, in an affine frame with first camera [M | m] and IAC ω,
    the cameras P H⁻¹ have M_M M_Mᵀ ∝ K Kᵀ (Result 10.5, p. 272).

    ω is known only up to scale, sign included. Raise np.linalg.LinAlgError (or ValueError) if
    Mᵀ ω M is not definite.
    """
    raise NotImplementedError("TODO")
