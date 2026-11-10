"""Grader for T4. Passes only when all four planted bugs in broken_ekf.py are fixed."""

from __future__ import annotations

import numpy as np
import pytest

from .. import models
from ..T4_debug.broken_ekf import BrokenEKF
from .test_T3 import numeric_jacobian


def test_G_jacobian_is_correct():
    model = models.RangeBearing()
    f = BrokenEKF(model, np.zeros(3), np.eye(3))
    for seed in range(6):
        r = np.random.default_rng(seed)
        u = np.array([r.uniform(0.2, 1.5), r.uniform(-1.5, 1.5)])
        x = np.array([r.uniform(-3, 3), r.uniform(-3, 3), r.uniform(-np.pi, np.pi)])
        Jn = numeric_jacobian(lambda s: model.g(u, s), x, wrap_rows=(2,))
        np.testing.assert_allclose(f.G(u, x), Jn, rtol=1e-5, atol=1e-7)


def test_jacobian_is_recomputed_every_step():
    model = models.RangeBearing()
    f = BrokenEKF(model, np.array([0.0, 0.0, 0.0]), np.eye(3) * 0.01)
    f.predict(np.array([1.0, 0.5]))
    S1 = f.Sigma.copy()
    f.mu = np.array([0.0, 0.0, 2.0])
    f.Sigma = np.eye(3) * 0.01
    f.predict(np.array([1.0, 0.5]))
    assert not np.allclose(S1, f.Sigma), "the Jacobian did not change with the state"


def test_bearing_innovation_is_wrapped():
    model = models.RangeBearing(landmark=(1.0, 0.0))   # bearing = −θ, so it crosses the ±π seam with θ
    f = BrokenEKF(model, np.array([0.0, 0.0, np.pi - 0.05]), np.eye(3) * 1e-4)
    z = model.h(np.array([0.0, 0.0, -np.pi + 0.05]))   # true heading just across the ±π seam
    nu, _ = f.update(z)
    assert abs(nu[1]) < 0.2, f"bearing innovation {nu[1]:.2f} rad was not wrapped"
    assert abs(f.mu[2]) > 3.0, "heading estimate not kept near ±π"


def test_filter_is_consistent_and_stable():
    model = models.RangeBearing()
    M, N = 8, 400
    nees = []
    for s in range(M):
        r = np.random.default_rng(s)
        U = models.figure_eight(N, model.dt)
        x0 = np.array([0.0, 0.0, 0.3])
        xs, zs = model.simulate(x0, U, r)
        f = BrokenEKF(model, x0 + r.normal(0, [0.05, 0.05, 0.02]), np.diag([0.05, 0.05, 0.02]) ** 2)
        for t in range(N):
            f.predict(U[t]); f.update(zs[t])
            e = f.mu - xs[t + 1]; e[2] = models.wrap(e[2])
            assert np.allclose(f.Sigma, f.Sigma.T, atol=1e-9), "Sigma lost symmetry"
            nees.append(e @ np.linalg.solve(f.Sigma, e))
    anees = float(np.mean(nees))
    assert 2.4 <= anees <= 3.6, f"ANEES {anees:.2f}"
