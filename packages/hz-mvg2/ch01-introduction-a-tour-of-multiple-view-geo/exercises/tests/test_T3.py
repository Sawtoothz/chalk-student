"""Oracle tests for T3. Every oracle is independent of the student code: the chapter's own forms
written out longhand (p. 5's circle, p. 7's x = PX), cameras built from a known centre and rotation,
the closed-form F of §9.2, true 3D points and their camera-frame directions, and np.linalg.inv.

Set STUDY_IMPL=solution to grade the reference solution instead of exercise.py.
"""

from __future__ import annotations

import importlib
import os

import numpy as np
import pytest

from .. import models
from ..models import hom, make_camera, pixels, project, rot

IMPL = os.environ.get("STUDY_IMPL", "exercise")
ex = importlib.import_module(f"..{'solutions.T3_solution' if IMPL == 'solution' else 'exercise'}", package=__package__)

K = models.K_LECTURE
S = models.two_view_scene()


def same_point(a, b, tol=1e-9):
    """Equality in ℙⁿ: unit vectors equal up to sign."""
    a, b = np.ravel(a) / np.linalg.norm(a), np.ravel(b) / np.linalg.norm(b)
    return min(np.linalg.norm(a - b), np.linalg.norm(a + b)) < tol


def H_with_cond(rng, c, n=4):
    U, _, Vt = np.linalg.svd(rng.standard_normal((n, n)))
    return U @ np.diag(np.geomspace(1, 1 / c, n)) @ Vt


# ---------------------------------------------------------------- C1 dehom


def test_dehom_divides_by_last_coordinate_any_scale():
    rng = np.random.default_rng(0)
    xy = rng.uniform(-50, 50, (20, 2))
    k = rng.choice([-1, 1], 20) * rng.uniform(1e-3, 1e3, 20)      # (kx, ky, k), p. 2, k of either sign
    out = ex.dehom(hom(xy) * k[:, None])
    assert out.shape == (20, 2)
    np.testing.assert_allclose(out, xy, rtol=1e-12, atol=1e-12)
    out3 = ex.dehom(np.array([2.0, 4.0, 6.0, 2.0]))                # a single ℙ³ point, 1-D input
    np.testing.assert_allclose(out3, [[1.0, 2.0, 3.0]])


def test_dehom_refuses_points_at_infinity_scale_free():
    with pytest.raises(ValueError):
        ex.dehom(np.array([1.0, 2.0, 0.0]))
    with pytest.raises(ValueError):                                # after a rotation, w is round-off (1e-17), not 0
        ex.dehom(np.array([3.0, -1.0, 1e-17]))
    with pytest.raises(ValueError):                                # one bad row in a batch is enough
        ex.dehom(np.array([[1.0, 1.0, 1.0], [1.0, 0.0, 0.0]]))
    # a tiny but finite representative of (1, 1) is a finite point: an absolute threshold calls it infinite
    np.testing.assert_allclose(ex.dehom(np.array([1e-13, 1e-13, 1e-13])), [[1.0, 1.0]])


# ---------------------------------------------------------------- C2 circular points


def circle_form(x, a, b, r):
    """p. 5 longhand: (x − aw)² + (y − bw)² − r²w²."""
    X, Y, W = x
    return (X - a * W) ** 2 + (Y - b * W) ** 2 - r ** 2 * W ** 2


def test_circle_conic_is_the_books_quadratic_form():
    rng = np.random.default_rng(1)
    for _ in range(10):
        a, b, r = rng.uniform(-5, 5), rng.uniform(-5, 5), rng.uniform(0.1, 5)
        C = ex.circle_conic(a, b, r)
        assert C.shape == (3, 3)
        np.testing.assert_allclose(C, C.T, atol=0)
        for _ in range(5):
            x = rng.standard_normal(3)
            assert abs(x @ C @ x - circle_form(x, a, b, r)) < 1e-9 * (1 + abs(circle_form(x, a, b, r)))
        for t in np.linspace(0, 2 * np.pi, 9):                     # points on the circle, any scale
            x = rng.uniform(0.1, 10) * np.array([a + r * np.cos(t), b + r * np.sin(t), 1.0])
            assert abs(x @ C @ x) < 1e-9 * (x @ x)


def test_circular_points_lie_on_every_circle():
    rng = np.random.default_rng(2)
    I, J = np.array([1, 1j, 0]), np.array([1, -1j, 0])             # p. 5
    for _ in range(20):
        C = ex.circle_conic(rng.uniform(-9, 9), rng.uniform(-9, 9), rng.uniform(0.1, 9))
        assert abs(I @ C @ I) < 1e-12 and abs(J @ C @ J) < 1e-12   # bilinear form, no conjugate
    # a general conic (an ellipse) does not contain them
    E = np.diag([1.0, 4.0, -1.0])
    assert abs(I @ E @ I) > 1


# ---------------------------------------------------------------- C3 camera centre and depth


def test_camera_centre_is_the_null_vector():
    rng = np.random.default_rng(3)
    for _ in range(10):
        R = rot("z", rng.uniform(-180, 180)) @ rot("y", rng.uniform(-90, 90)) @ rot("x", rng.uniform(-180, 180))
        C = rng.uniform(-10, 10, 3)
        P = rng.uniform(0.1, 100) * make_camera(K, R, C)
        c = ex.camera_centre(P)
        assert c.shape == (4,)
        assert abs(np.linalg.norm(c) - 1) < 1e-12
        assert np.linalg.norm(P @ c) < 1e-10 * np.linalg.norm(P)
        np.testing.assert_allclose(c[:3] / c[3], C, atol=1e-8)


def test_camera_centre_at_infinity_and_rank_check():
    A = np.array([[500.0, 0, 0, 10], [0, 500.0, 0, 20], [0, 0, 0, 1]])   # affine camera, p. 13: centre at infinity
    c = ex.camera_centre(A)
    assert abs(c[3]) < 1e-12 and same_point(c, [0, 0, 1, 0])
    P_bad = np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0], [1.0, 1.0, 0, 0]])  # rank 2: not a camera
    with pytest.raises(ValueError):
        ex.camera_centre(P_bad)


def test_depth_is_distance_along_the_optical_axis():
    d1 = ex.depth(S.P1, S.Xh)
    assert d1.shape == (len(S.Xh),)
    np.testing.assert_allclose(d1, S.Xw[:, 2], rtol=1e-12)
    np.testing.assert_allclose(ex.depth(S.P2, S.Xh), (S.Xw - S.C2) @ S.R2[2], rtol=1e-12)
    # projective freedom: P up to scale (sign included) and X up to scale do not change the answer
    np.testing.assert_allclose(ex.depth(-3.0 * S.P2, -0.2 * S.Xh), (S.Xw - S.C2) @ S.R2[2], rtol=1e-12)
    assert np.all(ex.depth(S.P1, hom(-S.Xw)) < 0)                 # behind the camera


# ---------------------------------------------------------------- C4 homographies


def test_plane_homography_images_the_floor():
    rng = np.random.default_rng(4)
    for yaw in (0.0, 25.0, -60.0):
        P, _, _ = models.robot_camera(x=rng.uniform(-1, 1), y=rng.uniform(-1, 1), yaw_deg=yaw)
        H = ex.plane_homography(P)
        assert H.shape == (3, 3)
        XY = np.column_stack([rng.uniform(-3, 3, 30), rng.uniform(2, 9, 30)])
        if yaw:
            XY = XY @ rot("z", yaw)[:2, :2].T
        a = pixels(project(P, np.column_stack([XY, np.zeros(30), np.ones(30)])))   # x = P X with Z = 0, p. 7
        b = pixels(hom(XY) @ H.T)
        np.testing.assert_allclose(b, a, atol=1e-8)


def test_plane_through_the_centre_is_refused():
    P, _, _ = models.robot_camera(h=0.0)                           # camera on the floor: Z = 0 contains the centre
    with pytest.raises(ValueError):
        ex.plane_homography(P)


def test_rotation_homography_explains_any_scene_from_one_centre():
    rng = np.random.default_rng(5)
    C = np.array([0.4, -1.2, 0.55])
    Xw = C + np.column_stack([rng.uniform(-3, 3, 50), rng.uniform(-2, 2, 50), rng.uniform(2, 40, 50)])   # not planar
    for R_rel in (rot("y", 15), rot("x", -7) @ rot("z", 30), rot("y", -3) @ rot("x", 1)):
        P1 = make_camera(K, np.eye(3), C)
        P2 = make_camera(K, R_rel, C)
        H = ex.rotation_homography(K, R_rel)
        a = pixels(project(P1, hom(Xw)) @ H.T)
        b = pixels(project(P2, hom(Xw)))
        np.testing.assert_allclose(a, b, atol=1e-8)
        np.testing.assert_allclose(H / np.linalg.norm(H) * np.sign(H[2, 2]),
                                   (K @ R_rel @ np.linalg.inv(K)) / np.linalg.norm(K @ R_rel @ np.linalg.inv(K))
                                   * np.sign((K @ R_rel @ np.linalg.inv(K))[2, 2]), atol=1e-12)


# ---------------------------------------------------------------- C5 projective ambiguity (1.1)


def test_ambiguity_leaves_every_image_unchanged():
    rng = np.random.default_rng(6)
    for c in (2.0, 10.0, 1e3):
        H = H_with_cond(rng, c)
        Ps, Xn = ex.apply_ambiguity([S.P1, S.P2], S.Xh, H)
        assert len(Ps) == 2 and Xn.shape == S.Xh.shape
        for P_old, P_new in zip((S.P1, S.P2), Ps):
            same_cam = P_new / np.linalg.norm(P_new)
            ref = P_old @ np.linalg.inv(H)
            ref = ref / np.linalg.norm(ref)
            assert min(np.linalg.norm(same_cam - ref), np.linalg.norm(same_cam + ref)) < 1e-9 * c
            np.testing.assert_allclose(pixels(project(P_new, Xn)), pixels(project(P_old, S.Xh)), atol=1e-6)
        for X_new, X_old in zip(Xn, S.Xh):
            assert same_point(X_new, H @ X_old, 1e-9)


def test_ambiguity_refuses_a_singular_H():
    H = np.eye(4)
    H[3] = H[2]                                                    # rank 3
    with pytest.raises(ValueError):
        ex.apply_ambiguity([S.P1], S.Xh, H)


# ---------------------------------------------------------------- C6 epipolar constraint


def point_line_distance(l, u):
    """Geometric distance from pixel u to the line l·(x, y, 1) = 0, via the foot of the perpendicular."""
    n = l[:2]
    p0 = -l[2] * n / (n @ n)                                       # the point of the line closest to the origin
    foot = u - ((u - p0) @ n) / (n @ n) * n                        # foot of the perpendicular from u
    return np.linalg.norm(u - foot)


def test_epipolar_distance_is_zero_on_true_matches_and_scale_free():
    d = ex.epipolar_distance_px(S.F, S.x1, S.x2)
    assert d.shape == (len(S.x1),)
    assert np.max(d) < 1e-6
    np.testing.assert_allclose(ex.epipolar_distance_px(1e5 * S.F, S.x1, S.x2), d, atol=1e-6)


def test_epipolar_distance_is_pixels_from_the_epipolar_line():
    rng = np.random.default_rng(7)
    x2n = S.x2.copy()
    x2n[:, :2] += rng.normal(0, 2.0, (len(x2n), 2))
    d = ex.epipolar_distance_px(S.F * 37.0, S.x1, x2n)
    ref = np.array([point_line_distance(S.F @ a, b[:2]) for a, b in zip(S.x1, x2n)])
    np.testing.assert_allclose(d, ref, rtol=1e-9)
    assert 0.5 < np.median(d) < 3.0                                # 2 px noise → about a pixel or two off the line


# ---------------------------------------------------------------- C7 triangulation


def test_triangulate_recovers_the_points_exactly():
    for i in range(len(S.Xh)):
        X = ex.triangulate([S.P1, S.P2], [S.x1[i], S.x2[i]])
        assert X.shape == (4,) and abs(np.linalg.norm(X) - 1) < 1e-12
        assert same_point(X, S.Xh[i], 1e-9)


def test_triangulate_accepts_any_homogeneous_scale_and_more_views():
    P3 = make_camera(K, rot("y", 8), np.array([-1.0, 0.0, 0.5]))
    x3 = project(P3, S.Xh)
    for i in range(0, len(S.Xh), 7):
        xs = [3.7 * S.x1[i], -0.01 * S.x2[i], x3[i]]               # w ≠ 1, negative scale too
        X = ex.triangulate([S.P1, S.P2, P3], xs)
        assert same_point(X, S.Xh[i], 1e-9)
        # transfer, p. 16: x″ = P″ X from two views equals the direct projection
        X2 = ex.triangulate([S.P1, S.P2], xs[:2])
        np.testing.assert_allclose(pixels(project(P3, X2)), pixels(x3[i]), atol=1e-6)


def test_triangulate_keeps_a_point_at_infinity():
    X_inf = np.array([0.0, 0.0, 1.0, 0.0])                         # a star on camera 1's optical axis
    x1, x2 = project(S.P1, X_inf)[0], project(S.P2, X_inf)[0]
    X = ex.triangulate([S.P1, S.P2], [x1, x2])
    assert abs(X[3]) < 1e-12 and same_point(X, X_inf, 1e-9)


# ---------------------------------------------------------------- C8 ray angles


def test_ray_angle_matches_the_true_3d_angle():
    Xc = S.Xw                                                      # P1 = K[I | 0]: world = camera frame
    i, j = np.arange(0, 60, 2), np.arange(1, 60, 2)
    a, b = Xc[i], Xc[j]
    true = np.arctan2(np.linalg.norm(np.cross(a, b), axis=1), np.sum(a * b, axis=1))
    got = ex.ray_angle(K, 2.5 * S.x1[i], S.x1[j])                  # homogeneous scale does not matter
    assert got.shape == (len(i),)
    np.testing.assert_allclose(got, true, atol=1e-12)
    np.testing.assert_allclose(np.degrees(ex.ray_angle(K, np.array([320.0, 240, 1]), np.array([640.0, 240, 1]))),
                               [np.degrees(np.arctan(320 / 500))], atol=1e-10)   # the lecture's 32.62°


def test_ray_angle_is_accurate_at_small_angles():
    xa, xb = np.array([600.0, 240.0, 1.0]), np.array([600.001, 240.0, 1.0])   # a millipixel apart near the edge
    true = np.arctan2(600.001 - 320, 500) - np.arctan2(600 - 320, 500)
    got = ex.ray_angle(K, xa, xb)[0]
    assert abs(got - true) < 1e-12, f"{got:.3e} vs {true:.3e}: arccos loses digits near 0"
    assert ex.ray_angle(K, xa, xa)[0] == 0.0


# ---------------------------------------------------------------- C9 affine and metric upgrade


def test_affine_upgrade_sends_pi_to_infinity():
    rng = np.random.default_rng(8)
    pis = [rng.standard_normal(4) for _ in range(5)] + [np.array([0.3, -0.5, 0.8, 1e-14]), np.array([0.0, 0, 1, 0])]
    for pi in pis:
        H = ex.affine_upgrade(pi)
        assert H.shape == (4, 4)
        assert np.linalg.cond(H) < 1e3, "H must stay well conditioned even when π₄ ≈ 0"
        e = np.linalg.solve(H.T, pi)                               # planes map by H⁻ᵀ
        assert np.linalg.norm(e[:3]) < 1e-12 * np.linalg.norm(e)


def test_affine_upgrade_restores_parallelism():
    rng = np.random.default_rng(9)
    Hp = H_with_cond(rng, 20)
    pi = np.linalg.solve(Hp.T, np.array([0.0, 0, 0, 1]))           # the plane at infinity in the projective frame
    HA = ex.affine_upgrade(pi)
    G = HA @ Hp                                                    # truth → affine frame: must be affine
    assert np.linalg.norm(G[3, :3]) < 1e-10 * abs(G[3, 3])
    # the two pairs of opposite edges of a true parallelogram stay parallel
    Q = np.array([[0, 0, 5, 1], [2, 0, 5, 1], [3, 1, 6, 1], [1, 1, 6, 1.0]])
    q = Q @ G.T
    q = q[:, :3] / q[:, 3:]
    np.testing.assert_allclose(np.cross(q[1] - q[0], q[2] - q[3]), 0, atol=1e-9)
    np.testing.assert_allclose(np.cross(q[3] - q[0], q[2] - q[1]), 0, atol=1e-9)


def affine_reconstruction(rng):
    """Truth (S) seen through a random affine H_A: cameras P H_A⁻¹, points H_A X. Built here, not by you."""
    HA = np.eye(4)
    HA[:3, :3] = rng.standard_normal((3, 3)) + 2 * np.eye(3)
    HA[:3, 3] = rng.standard_normal(3)
    Ps = [P @ np.linalg.inv(HA) for P in (S.P1, S.P2)]
    return Ps, HA


def test_metric_upgrade_recovers_calibration_and_right_angles():
    rng = np.random.default_rng(10)
    omega = np.linalg.inv(K @ K.T)                                 # IAC, Result 8.17
    cube = np.array([[x, y, z, 1.0] for x in (0, 1) for y in (0, 1) for z in (6, 7)])
    for _ in range(5):
        Ps, HA = affine_reconstruction(rng)
        HM = ex.metric_upgrade(Ps[0][:, :3], omega)
        assert HM.shape == (4, 4)
        Mm = (Ps[0] @ np.linalg.inv(HM))[:, :3]
        W = Mm @ Mm.T
        np.testing.assert_allclose(W / W[2, 2], K @ K.T / (K @ K.T)[2, 2], atol=1e-8)   # proof of Result 10.5
        # the true cube in the metric frame: right angles and equal edges
        c = cube @ (HM @ HA).T
        c = c[:, :3] / c[:, 3:]
        e1, e2, e3 = c[4] - c[0], c[2] - c[0], c[1] - c[0]
        for u, v in ((e1, e2), (e1, e3), (e2, e3)):
            assert abs(u @ v) < 1e-8 * np.linalg.norm(u) * np.linalg.norm(v)
        np.testing.assert_allclose([np.linalg.norm(e2) / np.linalg.norm(e1), np.linalg.norm(e3) / np.linalg.norm(e1)],
                                   [1, 1], atol=1e-8)


def test_metric_upgrade_ignores_omegas_scale_and_sign():
    rng = np.random.default_rng(11)
    omega = np.linalg.inv(K @ K.T)
    Ps, _ = affine_reconstruction(rng)
    M = Ps[0][:, :3]
    ref = (Ps[0] @ np.linalg.inv(ex.metric_upgrade(M, omega)))[:, :3]
    for s in (1e-6, -3.0):
        Mm = (Ps[0] @ np.linalg.inv(ex.metric_upgrade(M, s * omega)))[:, :3]
        W, Wr = Mm @ Mm.T, ref @ ref.T
        np.testing.assert_allclose(W / W[2, 2], Wr / Wr[2, 2], atol=1e-8)
    with pytest.raises((np.linalg.LinAlgError, ValueError)):
        ex.metric_upgrade(M, np.diag([1.0, -1.0, 1.0]))            # indefinite: not an IAC, or not an affine frame
