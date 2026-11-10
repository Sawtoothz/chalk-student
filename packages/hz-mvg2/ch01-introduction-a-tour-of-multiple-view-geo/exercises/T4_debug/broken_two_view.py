"""T4 — Debug. A colleague's two-view toolkit for the tracked robot's visual-odometry initializer.
It contains FIVE planted bugs, each one a real bug from the field (normalisation, sign, transpose,
wrong column). Find and fix them. `pytest exercises/tests/test_T4.py` passes when all five are fixed.

Do T3 first. Do not rewrite the file from your T3 solution; the point is to recognise each symptom.

Symptoms reported by the people who used it:
- the floor overlay drawn with the plane homography lands about 170 px away from the floor;
- after a rescaled camera matrix came out of an SVD, every triangulated point was "behind the camera";
- the 1 px epipolar inlier threshold accepted every match, gross mismatches included;
- triangulation was fine on raw detections and garbage on matches that had gone through a homography;
- the metric upgrade gave a cube with corners anywhere between 12° and 166°, even with the right ω.
"""

from __future__ import annotations

import numpy as np


def plane_homography(P):
    """H with (x, y, w)ᵀ = H (X, Y, T)ᵀ for points on the floor Z = 0 (p. 7)."""
    H = P[:, [0, 1, 2]]
    return H / np.linalg.norm(H)


def depth(P, Xh):
    """Depth of each point in front of P (eq. 6.15). Negative means behind the camera."""
    Xh = np.atleast_2d(Xh)
    M = P[:, :3]
    w = Xh @ P[2]
    return w / (Xh[:, 3] * np.linalg.norm(M[2]))


def epipolar_distance_px(F, x, xp):
    """Pixel distance from x′ to the epipolar line F x. x, xp: (N, 3) with w = 1."""
    x, xp = np.atleast_2d(x), np.atleast_2d(xp)
    l = x @ F.T
    return np.abs(np.sum(xp * l, axis=1)) / np.linalg.norm(l, axis=1)


def triangulate(Ps, xs):
    """Homogeneous linear triangulation from any number of views. Unit-norm 4-vector."""
    rows = []
    for P, x in zip(Ps, xs):
        rows += [x[0] * P[2] - P[0], x[1] * P[2] - P[1]]
    A = np.array(rows)
    A /= np.linalg.norm(A, axis=1, keepdims=True)
    X = np.linalg.svd(A)[2][-1]
    return X / np.linalg.norm(X)


def metric_upgrade(M, omega):
    """H_M from an affine frame with first camera [M | m] and IAC ω (Result 10.5)."""
    Omega = M.T @ omega @ M
    Omega = 0.5 * (Omega + Omega.T)
    if np.trace(Omega) < 0:
        Omega = -Omega
    L = np.linalg.cholesky(Omega)
    H = np.eye(4)
    H[:3, :3] = L
    return H
