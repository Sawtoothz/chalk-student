"""Oracle tests for T3. The oracle is independent of the student code: dense reference formulas,
finite-difference Jacobians, Monte Carlo propagation, and statistical consistency bounds.

Set STUDY_IMPL=solution to grade the reference solution instead of exercise.py.
"""

from __future__ import annotations

import importlib
import os

import numpy as np
import pytest
from scipy.stats import chi2

from .. import models

IMPL = os.environ.get("STUDY_IMPL", "exercise")
ex = importlib.import_module(f"..{'solutions.T3_solution' if IMPL == 'solution' else 'exercise'}", package=__package__)

rng = np.random.default_rng(42)


def spd(n, scale=1.0):
    A = rng.normal(size=(n, n))
    return scale * (A @ A.T + n * np.eye(n))


def numeric_jacobian(f, x, eps=1e-6, wrap_rows=()):
    y0 = np.atleast_1d(f(x))
    J = np.zeros((y0.size, x.size))
    for j in range(x.size):
        d = np.zeros_like(x); d[j] = eps
        diff = np.atleast_1d(f(x + d)) - np.atleast_1d(f(x - d))
        for r in wrap_rows:
            diff[r] = models.wrap(diff[r])
        J[:, j] = diff / (2 * eps)
    return J


# ---------------------------------------------------------------- C1


def test_kf_predict_matches_book():
    n, m = 4, 2
    A, B = rng.normal(size=(n, n)), rng.normal(size=(n, m))
    R = spd(n, 0.1)
    mu, Sigma, u = rng.normal(size=n), spd(n), rng.normal(size=m)
    mb, Sb = ex.kf_predict(mu, Sigma, u, A, B, R)
    np.testing.assert_allclose(mb, A @ mu + B @ u, rtol=1e-12)
    np.testing.assert_allclose(Sb, A @ Sigma @ A.T + R, rtol=1e-10)
    assert np.allclose(Sb, Sb.T)


def test_kf_update_matches_book_and_information_form():
    n, k = 5, 2
    C, Q = rng.normal(size=(k, n)), spd(k, 0.5)
    mb, Sb, z = rng.normal(size=n), spd(n), rng.normal(size=k)
    mu, Sigma, nu, S = ex.kf_update(mb, Sb, z, C, Q)
    S_ref = C @ Sb @ C.T + Q
    K_ref = Sb @ C.T @ np.linalg.inv(S_ref)
    np.testing.assert_allclose(nu, z - C @ mb, rtol=1e-12)
    np.testing.assert_allclose(S, S_ref, rtol=1e-10)
    np.testing.assert_allclose(mu, mb + K_ref @ (z - C @ mb), rtol=1e-9)
    # line 6 and eq. 3.38 must agree
    np.testing.assert_allclose(Sigma, (np.eye(n) - K_ref @ C) @ Sb, rtol=1e-8, atol=1e-10)
    np.testing.assert_allclose(Sigma, np.linalg.inv(C.T @ np.linalg.inv(Q) @ C + np.linalg.inv(Sb)), rtol=1e-7, atol=1e-9)


def test_kf_update_stays_symmetric_psd_over_many_steps():
    """Stress: tiny Q relative to Sigma, 5000 steps. Joseph form survives; (I-KC)Σ̄ usually does not."""
    car = models.CarCV
    mu, Sigma = np.zeros(2), np.eye(2) * 1e4
    for _ in range(5000):
        mu, Sigma = ex.kf_predict(mu, Sigma, np.zeros(1), car.A, car.B, car.R_proc)
        mu, Sigma, _, _ = ex.kf_update(mu, Sigma, np.array([0.0]), car.C, np.array([[1e-6]]))
    assert np.allclose(Sigma, Sigma.T, atol=1e-12)
    assert np.linalg.eigvalsh(Sigma).min() >= -1e-12


def test_uncertainty_grows_on_predict_and_shrinks_on_update():
    car = models.CarCV
    mu, Sigma = np.zeros(2), np.eye(2)
    _, Sb = ex.kf_predict(mu, Sigma, np.zeros(1), car.A, car.B, car.R_proc)
    assert np.trace(Sb) > np.trace(Sigma)
    _, S2, _, _ = ex.kf_update(mu, Sb, np.array([0.3]), car.C, car.Q_meas)
    assert np.trace(S2) < np.trace(Sb)


def test_book_exercise_1c_five_steps_from_rest():
    """Exercise 1(c): x0 = 0, Σ0 = 0, Δt = 1, σ_acc² = 1. Σ after t steps has a closed form."""
    car = models.CarCV
    mu, Sigma = np.zeros(2), np.zeros((2, 2))
    for t in range(1, 6):
        mu, Sigma = ex.kf_predict(mu, Sigma, np.zeros(1), car.A, car.B, car.R_proc)
    # Σ_t = Σ_{j=0}^{t-1} A^j Γ Γᵀ (A^j)ᵀ
    G = car._G
    ref = sum(np.linalg.matrix_power(car.A, j) @ G @ G.T @ np.linalg.matrix_power(car.A, j).T for j in range(5))
    np.testing.assert_allclose(Sigma, ref, rtol=1e-12)
    assert abs(mu).max() == 0.0


# ---------------------------------------------------------------- C4 Jacobians


@pytest.mark.parametrize("seed", range(10))
def test_G_jacobian_matches_finite_differences(seed):
    r = np.random.default_rng(seed)
    model = models.RangeBearing()
    u = np.array([r.uniform(0.2, 1.5), r.uniform(-1.5, 1.5) if seed % 3 else 0.0])
    x = np.array([r.uniform(-3, 3), r.uniform(-3, 3), r.uniform(-np.pi, np.pi)])
    Jn = numeric_jacobian(lambda s: model.g(u, s), x, wrap_rows=(2,))
    np.testing.assert_allclose(ex.G_jac(model, u, x), Jn, rtol=1e-5, atol=1e-7)


@pytest.mark.parametrize("seed", range(10))
def test_H_jacobian_matches_finite_differences(seed):
    r = np.random.default_rng(100 + seed)
    model = models.RangeBearing()
    x = np.array([r.uniform(-3, 3), r.uniform(-3, 3), r.uniform(-np.pi, np.pi)])
    Jn = numeric_jacobian(model.h, x, wrap_rows=(1,))
    np.testing.assert_allclose(ex.H_jac(model, x), Jn, rtol=1e-5, atol=1e-7)


# ---------------------------------------------------------------- C3 unscented transform


def test_sigma_points_reproduce_mean_and_covariance():
    n = 3
    mu, Sigma = rng.normal(size=n), spd(n)
    X, wm, wc = ex.sigma_points(mu, Sigma, alpha=1.0, beta=2.0, kappa=0.0)
    assert X.shape == (n, 2 * n + 1)
    assert abs(wm.sum() - 1.0) < 1e-12
    m, S, _ = ex.unscented_transform(X, wm, wc, np.zeros((n, n)))
    np.testing.assert_allclose(m, mu, atol=1e-10)
    np.testing.assert_allclose(S, Sigma, rtol=1e-8, atol=1e-10)


def test_unscented_transform_is_exact_for_linear_maps():
    n = 3
    mu, Sigma = rng.normal(size=n), spd(n)
    A = rng.normal(size=(n, n))
    X, wm, wc = ex.sigma_points(mu, Sigma, alpha=1e-3, beta=2.0, kappa=0.0)
    m, S, _ = ex.unscented_transform(A @ X, wm, wc, np.zeros((n, n)))
    np.testing.assert_allclose(m, A @ mu, rtol=1e-8, atol=1e-9)
    np.testing.assert_allclose(S, A @ Sigma @ A.T, rtol=1e-6, atol=1e-8)


def test_unscented_transform_beats_linearization_on_polar_to_cartesian():
    """Classic test: (r, θ) → (r cos θ, r sin θ) with wide θ. Compare to 1e6 Monte Carlo samples."""
    mu = np.array([5.0, 0.0]); Sigma = np.diag([0.1 ** 2, 0.6 ** 2])
    f = lambda p: np.array([p[0] * np.cos(p[1]), p[0] * np.sin(p[1])])
    s = rng.multivariate_normal(mu, Sigma, 1_000_000)
    ys = np.column_stack([s[:, 0] * np.cos(s[:, 1]), s[:, 0] * np.sin(s[:, 1])])
    mc_mean, mc_cov = ys.mean(0), np.cov(ys.T)
    X, wm, wc = ex.sigma_points(mu, Sigma, alpha=1.0, beta=2.0, kappa=1.0)
    ut_mean, ut_cov, _ = ex.unscented_transform(np.column_stack([f(X[:, i]) for i in range(5)]), wm, wc, np.zeros((2, 2)))
    J = numeric_jacobian(f, mu)
    ekf_mean, ekf_cov = f(mu), J @ Sigma @ J.T
    assert np.linalg.norm(ut_mean - mc_mean) < np.linalg.norm(ekf_mean - mc_mean)
    assert np.linalg.norm(ut_cov - mc_cov) < np.linalg.norm(ekf_cov - mc_cov)


# ---------------------------------------------------------------- C2/C3 filters on the robot


def run_filter(step, model, n=300, seed=7):
    r = np.random.default_rng(seed)
    U = models.figure_eight(n, model.dt)
    x0 = np.array([0.0, 0.0, 0.3])
    xs, zs = model.simulate(x0, U, r)
    mu, Sigma = x0 + r.normal(0, [0.05, 0.05, 0.02]), np.diag([0.05, 0.05, 0.02]) ** 2
    nees_, nis_ = [], []
    for t in range(n):
        mu, Sigma, nu, S = step(mu, Sigma, U[t], zs[t], model, model.R_proc, model.Q_meas)
        e = mu - xs[t + 1]; e[2] = models.wrap(e[2])
        nees_.append(ex.nees(e, Sigma)); nis_.append(ex.nis(nu, S))
    return np.array(nees_), np.array(nis_)


@pytest.mark.parametrize("name", ["ekf_step", "ukf_step"])
def test_filter_is_consistent_on_range_bearing(name):
    """Monte Carlo consistency (Bar-Shalom): over M independent runs the average NEES must be close to
    n = 3 and the average NIS close to k = 2. A single run is not a valid test: its errors are
    temporally correlated and one seed can land outside any band.

    Bands are deliberately wide (±20%) because the range-bearing model is mildly nonlinear and a
    correctly implemented EKF is a little conservative here. An overconfident filter (wrong Jacobian,
    missing noise, stale linearization) fails the upper bound by a wide margin.
    """
    model = models.RangeBearing()
    M, N = 12, 300
    ne = np.array([run_filter(getattr(ex, name), model, n=N, seed=s)[0] for s in range(M)])
    ni = np.array([run_filter(getattr(ex, name), model, n=N, seed=s)[1] for s in range(M)])
    anees, anis = ne.mean(), ni.mean()
    assert 0.8 * 3 <= anees <= 1.2 * 3, f"{name} ANEES {anees:.2f} outside [2.4, 3.6]"
    assert 0.8 * 2 <= anis <= 1.2 * 2, f"{name} ANIS {anis:.2f} outside [1.6, 2.4]"
    # overconfidence check: NEES above the 95% quantile should happen about 5% of the time, not 20%
    frac = (ne > chi2.ppf(0.95, 3)).mean()
    assert frac < 0.15, f"{name}: NEES exceeds its 95% bound {100 * frac:.1f}% of the time"


def test_ekf_and_ukf_agree_on_a_nearly_linear_problem():
    model = models.RangeBearing(landmark=(50.0, 30.0))   # far landmark: h is nearly linear
    r = np.random.default_rng(1)
    U = models.figure_eight(50, model.dt)
    xs, zs = model.simulate(np.array([0.0, 0.0, 0.0]), U, r)
    m1 = m2 = np.array([0.0, 0.0, 0.0]); S1 = S2 = np.diag([0.01, 0.01, 0.01])
    for t in range(50):
        m1, S1, _, _ = ex.ekf_step(m1, S1, U[t], zs[t], model, model.R_proc, model.Q_meas)
        m2, S2, _, _ = ex.ukf_step(m2, S2, U[t], zs[t], model, model.R_proc, model.Q_meas)
    assert np.linalg.norm(m1[:2] - m2[:2]) < 1e-2
    assert abs(models.wrap(m1[2] - m2[2])) < 1e-2


# ---------------------------------------------------------------- C5


def test_information_form_round_trip_and_update_equals_kf():
    n, k = 4, 2
    mu, Sigma = rng.normal(size=n), spd(n)
    xi, Omega = ex.to_information(mu, Sigma)
    np.testing.assert_allclose(Omega, np.linalg.inv(Sigma), rtol=1e-8)
    np.testing.assert_allclose(xi, np.linalg.solve(Sigma, mu), rtol=1e-8)
    mu2, Sigma2 = ex.from_information(xi, Omega)
    np.testing.assert_allclose(mu2, mu, rtol=1e-8); np.testing.assert_allclose(Sigma2, Sigma, rtol=1e-8)
    C, Q, z = rng.normal(size=(k, n)), spd(k, 0.3), rng.normal(size=k)
    xi_u, Om_u = ex.if_update(xi, Omega, z, C, Q)
    mu_if, Sig_if = ex.from_information(xi_u, Om_u)
    mu_kf, Sig_kf, _, _ = ex.kf_update(mu, Sigma, z, C, Q)
    np.testing.assert_allclose(mu_if, mu_kf, rtol=1e-7, atol=1e-9)
    np.testing.assert_allclose(Sig_if, Sig_kf, rtol=1e-7, atol=1e-9)


def test_information_form_accepts_total_ignorance():
    n, k = 3, 3
    xi, Omega = np.zeros(n), np.zeros((n, n))
    C, Q, z = np.eye(k), np.eye(k) * 0.5, np.array([1.0, 2.0, 3.0])
    xi, Omega = ex.if_update(xi, Omega, z, C, Q)
    mu, Sigma = ex.from_information(xi, Omega)
    np.testing.assert_allclose(mu, z, rtol=1e-12)
    np.testing.assert_allclose(Sigma, Q, rtol=1e-12)
