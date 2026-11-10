"""Oracle tests for T3. Every oracle is independent of the student code: the exact KF posterior of a
linear-Gaussian system, Table 4.1 on two states, closed-form Gaussian probabilities, dense quadrature,
numpy's weighted covariance, and Monte Carlo statistics over many independent runs.

Set STUDY_IMPL=solution to grade the reference solution instead of exercise.py.
"""

from __future__ import annotations

import importlib
import os
import warnings

import numpy as np
import pytest
from scipy.stats import norm

from .. import models

IMPL = os.environ.get("STUDY_IMPL", "exercise")
ex = importlib.import_module(f"..{'solutions.T3_solution' if IMPL == 'solution' else 'exercise'}", package=__package__)


def grid(lo, hi, K):
    edges = np.linspace(lo, hi, K + 1)
    return edges, 0.5 * (edges[1:] + edges[:-1])


# ---------------------------------------------------------------- C1 histogram filter


def test_transition_columns_are_distributions_and_match_probes():
    rw = models.RandomWalk1D()
    _, c = grid(-6, 6, 120)
    T = ex.transition_from_density(c, 0.7, rw.motion_pdf)
    assert T.shape == (120, 120)
    np.testing.assert_allclose(T.sum(axis=0), 1.0, atol=1e-12)
    probe = rw.motion_pdf(c[:, None], 0.7, c[None, :])
    np.testing.assert_allclose(T, probe / probe.sum(axis=0), rtol=1e-12)   # (4.5) with η per column


def test_hist_predict_is_table_4_1_line_3():
    rng = np.random.default_rng(1)
    T = rng.random((30, 30)); T /= T.sum(axis=0)
    p = rng.random(30); p /= p.sum()
    ref = np.array([sum(T[k, i] * p[i] for i in range(30)) for k in range(30)])
    np.testing.assert_allclose(ex.hist_predict(p, T), ref, rtol=1e-12)
    assert abs(ex.hist_predict(p, T).sum() - 1.0) < 1e-12


def test_hist_update_is_normalized_product_and_survives_underflow():
    rng = np.random.default_rng(2)
    p, lik = rng.random(40), rng.random(40)
    p /= p.sum()
    ref = lik * p / np.sum(lik * p)
    out = ex.hist_update(np.log(p), np.log(lik))
    np.testing.assert_allclose(np.exp(out), ref, rtol=1e-10)
    # a likelihood of e^-5000 for every bin underflows in linear space; log space must not care
    out2 = ex.hist_update(np.log(p), np.log(lik) - 5000.0)
    np.testing.assert_allclose(np.exp(out2), ref, rtol=1e-10)


def test_hist_density_is_piecewise_constant_4_2():
    edges = np.array([0.0, 0.5, 2.0, 2.25, 4.0])
    p = np.array([0.1, 0.3, 0.4, 0.2])
    xs = np.array([0.2, 1.0, 2.1, 3.9, -1.0, 4.0])
    np.testing.assert_allclose(ex.hist_density(xs, edges, p), [0.2, 0.2, 1.6, 0.2 / 1.75, 0.0, 0.0], rtol=1e-12)
    xx = np.linspace(0, 4, 400001)[:-1]
    assert abs(ex.hist_density(xx, edges, p).mean() * 4.0 - 1.0) < 1e-4


def test_histogram_filter_matches_kalman_filter():
    """Book exercises 1 and 4 in one dimension: Table 4.1 on a fine grid is the KF posterior."""
    rw = models.RandomWalk1D()
    rng = np.random.default_rng(3)
    U = np.full(12, 0.4)
    _, zs = rw.simulate(U, rng)
    edges, c = grid(-8, 14, 880)
    p = np.diff(norm.cdf(edges, rw.mu0, np.sqrt(rw.var0))); p /= p.sum()
    kf = rw.kf(U, zs)
    T = ex.transition_from_density(c, U[0], rw.motion_pdf)
    for t, z in enumerate(zs):
        p = ex.hist_predict(p, T)
        p = np.exp(ex.hist_update(np.log(np.maximum(p, 1e-300)), models.gauss_logpdf(z, c, np.sqrt(rw.Q_meas))))
        m = p @ c
        v = p @ (c - m) ** 2
        assert abs(m - kf[t, 0]) < 5e-3, (t, m, kf[t, 0])
        assert abs(v - kf[t, 1]) < 5e-3, (t, v, kf[t, 1])


def test_ring_corridor_two_doors_dense_reference():
    """Lecture Fig L2: uniform prior, door, drive 2.5 m, door. Reference: the same Bayes sums written densely."""
    ring = models.RingCorridor()
    _, c = grid(0, 10, 100)
    p = np.full(100, 0.01)
    T = ex.transition_from_density(c, 2.5, ring.motion_pdf)
    lp = ex.hist_update(np.log(p), np.log(ring.p_door(c)))
    p1 = ex.hist_predict(np.exp(lp), T)
    p2 = np.exp(ex.hist_update(np.log(p1), np.log(ring.p_door(c))))
    q = ring.p_door(c) * 0.01; q /= q.sum()
    Td = ring.motion_pdf(c[:, None], 2.5, c[None, :]); Td /= Td.sum(axis=0)
    q = ring.p_door(c) * (Td @ q); q /= q.sum()
    np.testing.assert_allclose(p2, q, rtol=1e-9)
    assert c[np.argmax(p2)] == pytest.approx(4.0, abs=0.1)


# ---------------------------------------------------------------- C2 log odds


def two_state_table_4_1(prior, p_inv_seq):
    """Oracle: Table 4.1 on {x, ¬x} with the forward model implied by the inverse one, p(z|x) ∝ p(x|z)/p(x)."""
    b = np.array([prior, 1 - prior])
    for pz in p_inv_seq:
        b = np.array([pz / prior, (1 - pz) / (1 - prior)]) * b
        b /= b.sum()
    return b[0]


@pytest.mark.parametrize("prior", [0.5, 0.3, 0.8])
def test_logodds_filter_equals_two_state_bayes(prior):
    rng = np.random.default_rng(int(prior * 100))
    seq = rng.choice([0.15, 0.4, 0.65, 0.9], size=25)
    l0 = ex.prob_to_logodds(prior)
    l = l0
    for pz in seq:
        l = ex.logodds_update(l, pz, l0)
    assert abs(float(ex.logodds_to_prob(l)) - two_state_table_4_1(prior, seq)) < 1e-10


def test_logodds_conversions_are_inverse_and_stable():
    p = np.linspace(0.01, 0.99, 50)
    np.testing.assert_allclose(ex.logodds_to_prob(ex.prob_to_logodds(p)), p, rtol=1e-12)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        big = ex.logodds_to_prob(np.array([-1000.0, -50.0, 0.0, 50.0, 1000.0]))
    assert np.all(np.isfinite(big)) and big[0] == 0.0 and big[-1] == 1.0 and big[2] == 0.5
    assert big[1] > 0.0, "(4.14) by cancellation returns exactly 0 at l = −50; expit does not"
    assert np.all(np.isfinite(ex.prob_to_logodds(np.array([0.0, 1.0]))))


def test_logodds_clamp():
    l = 0.0
    for _ in range(100):
        l = ex.logodds_update(l, 0.9, 0.0, l_min=-3.5, l_max=3.5)
    assert l == pytest.approx(3.5)
    for _ in range(3):
        l = ex.logodds_update(l, 0.1, 0.0, l_min=-3.5, l_max=3.5)
    assert l < 0.0, "a clamped cell must be able to change its mind"


# ---------------------------------------------------------------- C3 importance sampling


def test_is_estimate_closed_form_and_rate():
    """Target N(0,1), proposal N(1, 2²), A = (−∞, 0.5]. Oracle: Φ(0.5). Error over 200 runs must scale as 1/√M."""
    lf = lambda x: norm.logpdf(x, 0, 1)
    lg = lambda x: norm.logpdf(x, 1, 2)
    h = lambda x: (x <= 0.5).astype(float)
    rng = np.random.default_rng(5)
    est, _ = ex.is_estimate(rng.normal(1, 2, 400_000), lf, lg, h)
    assert abs(est - norm.cdf(0.5)) < 4e-3
    rmse = []
    for M in (100, 1600):
        e = [ex.is_estimate(rng.normal(1, 2, M), lf, lg, h)[0] - norm.cdf(0.5) for _ in range(200)]
        rmse.append(np.sqrt(np.mean(np.square(e))))
    assert 2.8 < rmse[0] / rmse[1] < 5.6, rmse    # √16 = 4


def test_is_neff():
    rng = np.random.default_rng(6)
    xs = rng.normal(0, 1, 1000)
    _, n = ex.is_estimate(xs, lambda x: norm.logpdf(x), lambda x: norm.logpdf(x), lambda x: x)
    assert n == pytest.approx(1000.0, rel=1e-9)
    _, n2 = ex.is_estimate(xs, lambda x: norm.logpdf(x, 0, 0.2), lambda x: norm.logpdf(x), lambda x: x)
    w = norm.pdf(xs, 0, 0.2) / norm.pdf(xs); w /= w.sum()
    assert n2 == pytest.approx(1.0 / np.sum(w**2), rel=1e-9)


def test_is_support_violation_raises():
    xs = np.array([-1.0, 0.0, 2.0])
    lg = lambda x: np.where(x < 1.0, 0.0, -np.inf)
    with pytest.raises(ValueError):
        ex.is_estimate(xs, lambda x: norm.logpdf(x), lg, lambda x: x)


# ---------------------------------------------------------------- C5 resampling


def table_4_4(w, r):
    """Oracle: Table 4.4 line by line (zero-based), with a given r."""
    M = len(w); out = []
    c = w[0]; i = 0
    for m in range(M):
        U = r + m / M
        while U > c:
            i += 1; c += w[i]
        out.append(i)
    return np.array(out)


def test_low_variance_matches_table_4_4():
    rng = np.random.default_rng(7)
    for _ in range(50):
        w = rng.gamma(0.5, 1.0, 37); w /= w.sum()
        seed = int(rng.integers(1 << 30))
        idx = ex.low_variance_resample(w, np.random.default_rng(seed))
        r = np.random.default_rng(seed).uniform(0.0, 1.0 / 37)
        np.testing.assert_array_equal(idx, table_4_4(w, r))


def test_low_variance_properties():
    rng = np.random.default_rng(8)
    M = 50
    np.testing.assert_array_equal(ex.low_variance_resample(np.full(M, 1.0 / M), rng), np.arange(M))
    for _ in range(200):
        w = rng.gamma(0.3, 1.0, M); w /= w.sum()
        cnt = np.bincount(ex.low_variance_resample(w, rng), minlength=M)
        assert cnt.sum() == M
        assert np.all(cnt >= np.floor(M * w) - 1e-9) and np.all(cnt <= np.ceil(M * w) + 1e-9)
    w = rng.gamma(0.3, 1.0, M)
    s = int(rng.integers(1 << 30))
    np.testing.assert_array_equal(ex.low_variance_resample(7.3 * w, np.random.default_rng(s)),
                                  ex.low_variance_resample(w / w.sum(), np.random.default_rng(s)))


@pytest.mark.parametrize("name", ["low_variance_resample", "stratified_resample"])
def test_resampler_mean_copy_count_is_M_w(name):
    f = getattr(ex, name)
    rng = np.random.default_rng(9)
    M = 20
    w = rng.gamma(1.0, 1.0, M); w /= w.sum()
    runs = 20000
    cnt = np.zeros(M)
    for _ in range(runs):
        idx = f(w, rng)
        assert idx.min() >= 0 and idx.max() < M and np.all(np.diff(idx) >= 0)
        cnt += np.bincount(idx, minlength=M)
    np.testing.assert_allclose(cnt / runs, M * w, atol=0.03)


# ---------------------------------------------------------------- C4 particle filter


def test_pf_matches_kalman_filter():
    rw = models.RandomWalk1D()
    rng = np.random.default_rng(10)
    U = np.full(10, 0.5)
    _, zs = rw.simulate(U, rng)
    kf = rw.kf(U, zs)
    M = 40_000
    X = rng.normal(rw.mu0, np.sqrt(rw.var0), (M, 1))
    logw = np.full(M, -np.log(M))
    for t in range(10):
        X, logw, _ = ex.pf_step(X, logw, U[t], zs[t], rw.sample_motion, rw.log_lik, rng)
        w = np.exp(logw)
        m = w @ X[:, 0]; v = w @ (X[:, 0] - m) ** 2
        assert abs(m - kf[t, 0]) < 0.02 and abs(v - kf[t, 1]) < 0.02, (t, m, kf[t, 0], v, kf[t, 1])


def test_pf_is_consistent_over_independent_runs():
    """100 runs, M = 300: the normalized squared error (x − μ)²/σ² of the PF estimate averages ≈ 1."""
    rw = models.RandomWalk1D()
    nes = []
    for s in range(100):
        rng = np.random.default_rng(1000 + s)
        U = np.full(20, 0.3)
        xs, zs = rw.simulate(U, rng)
        X = rng.normal(rw.mu0, np.sqrt(rw.var0), (300, 1)); logw = np.full(300, -np.log(300))
        for t in range(20):
            X, logw, _ = ex.pf_step(X, logw, U[t], zs[t], rw.sample_motion, rw.log_lik, rng)
        w = np.exp(logw); m = w @ X[:, 0]; v = w @ (X[:, 0] - m) ** 2
        nes.append((xs[-1] - m) ** 2 / v)
    assert 0.7 < np.mean(nes) < 1.4, np.mean(nes)


def test_pf_carries_weights_and_resamples_only_on_low_neff():
    rng = np.random.default_rng(11)
    M = 1000
    X = rng.normal(0, 1, (M, 1)); logw = np.full(M, -np.log(M))
    still = lambda u, X, r: X.copy()
    flat = lambda z, X: np.zeros(len(X))
    X2, lw2, n = ex.pf_step(X, logw, 0.0, 0.0, still, flat, rng)
    assert n == pytest.approx(M) and np.array_equal(X2, X), "equal weights must not trigger resampling"
    mild = lambda z, X: -0.5 * ((z - X[:, 0]) / 3.0) ** 2
    X3, lw3, n3 = ex.pf_step(X, logw, 0.0, 1.0, still, mild, rng, neff_frac=0.5)
    assert n3 > 0.5 * M and np.array_equal(X3, X)
    X4, lw4, _ = ex.pf_step(X3, lw3, 0.0, 1.0, still, mild, rng, neff_frac=0.5)
    ref = 2 * mild(1.0, X); ref -= ref.max(); ref = np.exp(ref); ref /= ref.sum()
    np.testing.assert_allclose(np.exp(lw4), ref, rtol=1e-9)        # (4.36): weights multiply across steps
    sharp = lambda z, X: -0.5 * ((z - X[:, 0]) / 0.05) ** 2
    X5, lw5, n5 = ex.pf_step(X, logw, 0.0, 0.0, still, sharp, rng)
    assert n5 < 0.5 * M
    np.testing.assert_allclose(np.exp(lw5), 1.0 / M, rtol=1e-12)   # reset after resampling
    assert np.abs(X5[:, 0]).max() < 0.5


def test_pf_survives_likelihood_underflow():
    rw = models.RandomWalk1D()
    rng = np.random.default_rng(12)
    M = 20_000
    X = rng.normal(0, 1, (M, 1)); logw = np.full(M, -np.log(M))
    deep = lambda z, X: rw.log_lik(z, X) - 3000.0        # a LiDAR-sized log likelihood
    X, logw, n = ex.pf_step(X, logw, 0.0, 0.8, rw.sample_motion, deep, rng)
    assert np.all(np.isfinite(logw)) and np.isfinite(n)
    w = np.exp(logw)
    v0 = rw.var0 + rw.R_proc; k = v0 / (v0 + rw.Q_meas)
    assert abs(w @ X[:, 0] - k * 0.8) < 0.02


def test_pf_stationary_equal_weights_keeps_diversity():
    rng = np.random.default_rng(13)
    M = 200
    X = rng.normal(0, 1, (M, 1)); logw = np.full(M, -np.log(M))
    still = lambda u, X, r: X.copy()
    flat = lambda z, X: np.zeros(len(X))
    for _ in range(100):
        X, logw, _ = ex.pf_step(X, logw, 0.0, 0.0, still, flat, rng)
    assert len(np.unique(X)) == M


def test_pf_wraps_angles_and_injects_only_on_resample():
    rng = np.random.default_rng(14)
    M = 400
    X = np.column_stack([np.zeros(M), np.full(M, 3.0)])
    spin = lambda u, X, r: X + np.array([0.0, u]) + r.normal(0, [0.1, 0.01], X.shape)
    flat = lambda z, X: np.zeros(len(X))
    sentinel = lambda n, r: np.column_stack([np.full(n, 99.0), np.zeros(n)])
    X1, lw1, _ = ex.pf_step(X, np.full(M, -np.log(M)), 0.5, 0.0, spin, flat, rng, inject=0.05,
                            sample_uniform=sentinel, angle_idx=(1,))
    assert np.all(X1[:, 1] >= -np.pi) and np.all(X1[:, 1] < np.pi)
    assert not np.any(X1[:, 0] == 99.0), "injection without resampling"
    sharp = lambda z, X: -0.5 * (X[:, 0] / 0.02) ** 2
    X2, _, _ = ex.pf_step(X1, lw1, 0.0, 0.0, spin, sharp, rng, inject=0.05, sample_uniform=sentinel, angle_idx=(1,))
    assert np.sum(X2[:, 0] == 99.0) == 20


# ---------------------------------------------------------------- C6 density extraction


def test_weighted_mean_cov_matches_numpy():
    rng = np.random.default_rng(15)
    X = rng.normal(size=(500, 3)) @ rng.normal(size=(3, 3))
    w = rng.gamma(1.0, 1.0, 500)
    mu, cov = ex.weighted_mean_cov(X, w)
    np.testing.assert_allclose(mu, np.average(X, axis=0, weights=w), rtol=1e-12)
    np.testing.assert_allclose(cov, np.cov(X.T, aweights=w), rtol=1e-10)
    mu2, cov2 = ex.weighted_mean_cov(X, 5.0 * w)
    np.testing.assert_allclose(cov2, cov, rtol=1e-12)


def test_weighted_mean_cov_heading_across_pi():
    rng = np.random.default_rng(16)
    th = models.wrap(np.pi + rng.normal(0, 0.1, 2000))
    X = np.column_stack([rng.normal(0, 1, 2000), th])
    mu, cov = ex.weighted_mean_cov(X, np.ones(2000), angle_idx=(1,))
    assert abs(models.wrap(mu[1] - np.pi)) < 0.01
    assert cov[1, 1] == pytest.approx(0.01, rel=0.15)


# ---------------------------------------------------------------- book exercises 2 and 5: the banana


def test_banana_histogram_and_particles_agree_with_quadrature():
    """θ ~ U(−π, π), drive 1 m, measure z = x + N(0, 0.1²). Dense quadrature over θ is the oracle."""
    b = models.Banana()
    z = 0.4
    th = np.linspace(-np.pi, np.pi, 200_001)
    post = np.exp(models.gauss_logpdf(z, np.cos(th), np.sqrt(b.Q_meas)))
    post /= post.sum()
    E_y = post @ np.sin(th); P_pos = post[th > 0].sum(); E_absth = post @ np.abs(th)
    # histogram over θ (the state after the drive is a function of θ)
    edges, c = grid(-np.pi, np.pi, 720)
    lp = ex.hist_update(np.full(720, -np.log(720)), models.gauss_logpdf(z, np.cos(c), np.sqrt(b.Q_meas)))
    p = np.exp(lp)
    assert abs(p @ np.abs(c) - E_absth) < 2e-3 and abs(p[c > 0].sum() - P_pos) < 2e-3
    # particles
    rng = np.random.default_rng(17)
    M = 50_000
    X = b.sample_prior(M, rng); logw = np.full(M, -np.log(M))
    X, logw, _ = ex.pf_step(X, logw, b.d, z, b.sample_motion, b.log_lik, rng, angle_idx=(2,))
    w = np.exp(logw)
    assert abs(w @ X[:, 1] - E_y) < 0.03
    assert abs(w @ np.abs(X[:, 2]) - E_absth) < 0.02
    assert abs(w[X[:, 2] > 0].sum() - P_pos) < 0.03
