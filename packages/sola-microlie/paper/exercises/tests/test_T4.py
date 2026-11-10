"""Grader for T4. One test per planted bug in broken_eskf.py, each written so that only its bug fails it, plus one
end-to-end consistency run that passes only when all four are fixed. Oracles: expm/logm, the generic adjoint (31),
finite differences of (41a)."""

from __future__ import annotations

import numpy as np

from .. import models as M
from ..T4_debug.broken_eskf import BrokenESKF
from .test_T3 import euclid_minus, fd_right

P0 = np.diag([0.01, 0.01, 0.01]) ** 2


def make(X=None):
    sec = M.SectionV()
    return BrokenESKF(np.eye(3) if X is None else X, P0, sec.R_proc, sec.Q_meas), sec


def test_exp_survives_driving_straight():
    """θ = ω δt = 0 on every straight segment. Exp must be finite there and equal expm."""
    f, _ = make()
    for tau in [np.array([0.1, 0.0, 0.0]), np.array([0.2, -0.05, 0.0]), np.array([0.1, 0.0, 1e-12])]:
        T = f.exp(tau)
        assert np.all(np.isfinite(T)), f"Exp({tau}) is not finite"
        np.testing.assert_allclose(T, M.se2_Exp_ref(tau), atol=1e-14)


def test_F_is_the_jacobian_of_rplus_with_respect_to_X():
    """F = J^{X⊕u}_X = Ad_{Exp(u)}⁻¹ (80). Oracle: dense inverse of the generic adjoint (31) at u with θ ≠ 0."""
    f, _ = make()
    rng = np.random.default_rng(3)
    for _ in range(6):
        u = np.r_[rng.uniform(-0.5, 0.5, 2), rng.uniform(0.1, 1.0) * rng.choice([-1, 1])]
        np.testing.assert_allclose(f.F(u), np.linalg.inv(M.se2_Ad_ref(M.se2_Exp_ref(u))), atol=1e-12)


def test_H_matches_finite_differences_away_from_the_origin():
    """H = J^{X⁻¹·b}_X by FD of (41a). At X = I every frame mix-up is invisible, so test at turned, moved poses."""
    rng = np.random.default_rng(4)
    for _ in range(6):
        X = M.random_pose(rng)
        b = rng.uniform(-4, 4, 2)
        f, _ = make(X)
        _, H = f.expect(b)
        g = lambda A: (np.linalg.inv(A) @ np.r_[b, 1.0])[:2]
        np.testing.assert_allclose(H, fd_right(g, X, M.se2_rplus_ref, euclid_minus, 3), atol=1e-7)


def test_update_applies_the_correction_on_the_right():
    """(101): X ← X ⊕ δx = X Exp(δx), δx in the local tangent where P lives. Uses the filter's own H and gain, so
    this test does not depend on whether H is right; only on where δx is applied."""
    rng = np.random.default_rng(5)
    X0 = M.pose(1.5, -1.0, 2.0)
    f, sec = make(X0)
    f.P = np.diag([0.1, 0.1, 0.1]) ** 2
    b = sec.beacons[1]
    e, H = f.expect(b)
    y = e + np.array([0.08, -0.05])
    Z = H @ f.P @ H.T + f.Q_meas
    dx = f.P @ H.T @ np.linalg.solve(Z, y - e)
    assert abs(dx[2]) > 1e-3
    f.update(y, b)
    np.testing.assert_allclose(f.X, X0 @ M.se2_Exp_ref(dx), atol=1e-12)


def test_filter_is_consistent_once_fixed():
    """End to end on the §V setup, started away from the origin and turned: 20 runs of 100 steps, ANEES near 3."""
    nees = []
    X0 = M.pose(-1.0, 2.0, 2.5)
    for s in range(20):
        rng = np.random.default_rng(s)
        sec = M.SectionV()
        Xs, us, ys = sec.simulate(100, rng, X0=X0)
        f = BrokenESKF(X0 @ M.se2_Exp_ref(np.linalg.cholesky(P0) @ rng.normal(size=3)), P0, sec.R_proc, sec.Q_meas)
        for k in range(100):
            f.predict(us[k])
            for j, b in enumerate(sec.beacons):
                f.update(ys[k, j], b)
            e = M.se2_rminus_ref(Xs[k + 1], f.X)
            nees.append(e @ np.linalg.solve(f.P, e))
    anees = float(np.mean(nees))
    assert 2.4 <= anees <= 3.6, f"ANEES {anees:.2f}"
