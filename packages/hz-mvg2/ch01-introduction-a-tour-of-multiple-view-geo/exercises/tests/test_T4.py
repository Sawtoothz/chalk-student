"""Grader for T4. One test per planted bug in broken_two_view.py; each test exercises one function only,
so each fails for its own bug and no other. All pass when the five bugs are fixed."""

from __future__ import annotations

import numpy as np

from .. import models
from ..models import hom, pixels, project, rot
from ..T4_debug import broken_two_view as bt

K = models.K_LECTURE
S = models.two_view_scene()


def same_point(a, b, tol=1e-9):
    a, b = np.ravel(a) / np.linalg.norm(a), np.ravel(b) / np.linalg.norm(b)
    return min(np.linalg.norm(a - b), np.linalg.norm(a + b)) < tol


def test_floor_homography_matches_projection():
    rng = np.random.default_rng(0)
    P, _, _ = models.robot_camera(x=0.3, y=-0.2, yaw_deg=10.0)
    XY = np.column_stack([rng.uniform(-3, 3, 40), rng.uniform(2, 9, 40)])
    a = pixels(project(P, np.column_stack([XY, np.zeros(40), np.ones(40)])))
    b = pixels(hom(XY) @ bt.plane_homography(P).T)
    np.testing.assert_allclose(b, a, atol=1e-8, err_msg="the floor overlay does not land on the floor")


def test_depth_survives_a_negative_camera_scale():
    want = (S.Xw - S.C2) @ S.R2[2]
    for s in (1.0, -1.0, -250.0):                       # an SVD returns P up to scale, sign included
        np.testing.assert_allclose(bt.depth(s * S.P2, S.Xh), want, rtol=1e-12,
                                   err_msg=f"depth flips sign when P is scaled by {s}")


def test_epipolar_distance_is_in_pixels():
    rng = np.random.default_rng(1)
    x2n = S.x2.copy()
    x2n[:, :2] += rng.normal(0, 2.0, (len(x2n), 2))
    d = bt.epipolar_distance_px(S.F, S.x1, x2n)
    l = S.x1 @ S.F.T
    ref = np.abs(np.sum(x2n * l, axis=1)) / np.hypot(l[:, 0], l[:, 1])   # distance of a point to a line in the plane
    np.testing.assert_allclose(d, ref, rtol=1e-9, err_msg="the distance is not in pixels")


def test_triangulation_ignores_homogeneous_scale():
    for i in range(0, len(S.Xh), 5):
        X = bt.triangulate([S.P1, S.P2], [4.0 * S.x1[i], -0.5 * S.x2[i]])
        assert same_point(X, S.Xh[i], 1e-9), f"point {i}: matches with w ≠ 1 triangulate to the wrong point"


def test_metric_upgrade_gives_right_angles():
    rng = np.random.default_rng(2)
    omega = np.linalg.inv(K @ K.T)
    HA = np.eye(4)
    HA[:3, :3] = rng.standard_normal((3, 3)) + 2 * np.eye(3)
    HA[:3, 3] = rng.standard_normal(3)
    P_aff = S.P1 @ np.linalg.inv(HA)
    HM = bt.metric_upgrade(P_aff[:, :3], omega)
    Mm = (P_aff @ np.linalg.inv(HM))[:, :3]
    W = Mm @ Mm.T
    np.testing.assert_allclose(W / W[2, 2], K @ K.T / (K @ K.T)[2, 2], atol=1e-8,
                               err_msg="M_M M_Mᵀ is not proportional to K Kᵀ")
    cube = np.array([[x, y, z, 1.0] for x in (0, 1) for y in (0, 1) for z in (6, 7)]) @ (HM @ HA).T
    c = cube[:, :3] / cube[:, 3:]
    e1, e2 = c[4] - c[0], c[2] - c[0]
    ang = np.degrees(np.arccos(e1 @ e2 / np.linalg.norm(e1) / np.linalg.norm(e2)))
    assert abs(ang - 90.0) < 1e-6, f"cube corner {ang:.2f}°"
