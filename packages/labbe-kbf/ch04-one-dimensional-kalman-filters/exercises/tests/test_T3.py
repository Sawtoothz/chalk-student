"""Oracle tests for T3. Every oracle is independent of the student code: the book's printed cell outputs,
numerical integration of the Gaussian product, Monte Carlo propagation, the iterated variance recursion,
a dense re-implementation of the p. 147 loop, and Monte Carlo consistency over many runs.

Set STUDY_IMPL=solution to grade the reference solution instead of exercise.py.
Names: R_proc = Labbe's Q (process variance), Q_meas = Labbe's R (sensor variance).
"""

from __future__ import annotations

import importlib
import os

import numpy as np
import pytest

from .. import models

IMPL = os.environ.get("STUDY_IMPL", "exercise")
ex = importlib.import_module(f"..{'solutions.T3_solution' if IMPL == 'solution' else 'exercise'}", package=__package__)

BOOK = 5e-4   # the book prints three decimals
trapezoid = getattr(np, "trapezoid", None) or np.trapz   # numpy 2 renamed trapz


def book_close(a, b):
    assert abs(float(a) - b) <= BOOK, f"{float(a)} vs book {b}"


# ---------------------------------------------------------------- C1 predict


def test_predict_matches_book():
    # p. 137: predict(N(10, 0.2²), N(15, 0.7²)) = N(25, 0.53)
    x, P = ex.predict(10.0, 0.2 ** 2, 15.0, 0.7 ** 2)
    book_close(x, 25.0); book_close(P, 0.53)
    # p. 168: kf.predict(x=10, P=3, u=1, Q=4) = (11, 7); Labbe's Q is our R_proc
    x, P = ex.predict(10.0, 3.0, 1.0, 4.0)
    assert (float(x), float(P)) == pytest.approx((11.0, 7.0), abs=1e-12)


def test_predict_is_the_sum_of_two_gaussians_monte_carlo():
    """x ~ N(3, 0.8), f_x ~ N(1.5, 0.3), independent: x + f_x has mean 4.5 and variance 1.1."""
    r = np.random.default_rng(11)
    s = r.normal(3.0, np.sqrt(0.8), 1_000_000) + r.normal(1.5, np.sqrt(0.3), 1_000_000)
    x, P = ex.predict(3.0, 0.8, 1.5, 0.3)
    assert abs(x - s.mean()) < 5e-3
    assert abs(P - s.var()) / s.var() < 1e-2


def test_predict_dt_scaling_two_half_steps_equal_one_step():
    x1, P1 = ex.predict(*ex.predict(2.0, 0.5, 3.0, 0.4, dt=0.5), 3.0, 0.4, dt=0.5)
    x2, P2 = ex.predict(2.0, 0.5, 3.0, 0.4, dt=1.0)
    assert x1 == pytest.approx(x2, rel=1e-12) and P1 == pytest.approx(P2, rel=1e-12)
    assert P2 == pytest.approx(0.9, rel=1e-12)


def test_predict_rejects_negative_variances():
    with pytest.raises(ValueError):
        ex.predict(0.0, 1.0, 0.0, -0.1)
    with pytest.raises(ValueError):
        ex.predict(0.0, -1.0, 0.0, 0.1)


# ---------------------------------------------------------------- C2 update, Bayes form


def test_update_bayes_matches_book():
    # p. 138: update(N(10, 0.2²), N(11, 0.1²)) = N(10.8, 0.008)
    x, P, _ = ex.update_bayes(10.0, 0.2 ** 2, 11.0, 0.1 ** 2)
    book_close(x, 10.8); book_close(P, 0.008)
    # p. 139: N(10, 1) × N(10, 1) = N(10, 0.5)
    x, P, _ = ex.update_bayes(10.0, 1.0, 10.0, 1.0)
    assert (x, P) == pytest.approx((10.0, 0.5), rel=1e-12)


@pytest.mark.parametrize("x_bar,P_bar,z,Q", [(10.0, 0.04, 11.0, 0.01), (-3.0, 7.0, 4.0, 2.5), (0.0, 1e-2, 50.0, 30.0)])
def test_update_bayes_equals_numerical_product_of_pdfs(x_bar, P_bar, z, Q):
    """Multiply the two pdfs on a dense grid, integrate: the constant, the mean and the variance."""
    sd = np.sqrt(min(P_bar, Q))
    g = np.linspace(min(x_bar, z) - 12 * sd - 12 * np.sqrt(max(P_bar, Q)), max(x_bar, z) + 12 * np.sqrt(max(P_bar, Q)), 400_001)
    pdf = lambda t, m, v: np.exp(-0.5 * (t - m) ** 2 / v) / np.sqrt(2 * np.pi * v)
    prod = pdf(g, x_bar, P_bar) * pdf(g, z, Q)
    c = trapezoid(prod, g)
    mean = trapezoid(g * prod, g) / c
    var = trapezoid((g - mean) ** 2 * prod, g) / c
    x, P, log_c = ex.update_bayes(x_bar, P_bar, z, Q)
    assert x == pytest.approx(mean, rel=1e-6, abs=1e-9)
    assert P == pytest.approx(var, rel=1e-5)
    assert log_c == pytest.approx(np.log(c), rel=1e-6, abs=1e-6)


def test_update_bayes_handles_no_prior_and_perfect_prior():
    x, P, log_c = ex.update_bayes(123.0, np.inf, 4.0, 2.5)
    assert x == 4.0 and P == pytest.approx(2.5, rel=1e-14) and log_c == -np.inf
    x, P, _ = ex.update_bayes(7.0, 0.0, 4.0, 2.5)
    assert x == 7.0 and P == 0.0


def test_update_bayes_posterior_is_narrower_than_both_inputs():
    r = np.random.default_rng(3)
    for _ in range(200):
        Pb, Q = 10 ** r.uniform(-3, 3, 2)
        _, P, _ = ex.update_bayes(r.normal(), Pb, r.normal(), Q)
        assert P < min(Pb, Q)


def test_update_bayes_rejects_bad_variances():
    with pytest.raises(ValueError):
        ex.update_bayes(0.0, 1.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        ex.update_bayes(0.0, -1.0, 0.0, 1.0)


# ---------------------------------------------------------------- C3 update, gain form


def test_update_matches_book_p169():
    # p. 169: predict (10, 3) with u = 1, Labbe's Q = 2² (R_proc); update z = 12, Labbe's R = 3.5² (Q_meas)
    x_bar, P_bar = ex.predict(10.0, 3.0, 1.0, 2.0 ** 2)
    x, P, y, S, ok = ex.update(x_bar, P_bar, 12.0, 3.5 ** 2)
    book_close(x, 11.364); book_close(P, 4.455)
    assert ok and y == pytest.approx(1.0) and S == pytest.approx(19.25)


def test_update_gain_form_equals_bayes_form():
    """p. 150: the gain form is the product of Gaussians rewritten. Dense Bayes-form oracle (p. 138)."""
    r = np.random.default_rng(4)
    for _ in range(2000):
        xb, z = r.normal(0, 100, 2)
        Pb, Q = 10 ** r.uniform(-3, 3, 2)
        x, P, y, S, ok = ex.update(xb, Pb, z, Q)
        assert ok
        assert x == pytest.approx((Pb * z + Q * xb) / (Pb + Q), rel=1e-12, abs=1e-10)
        assert P == pytest.approx(Pb * Q / (Pb + Q), rel=1e-12)
        assert y == pytest.approx(z - xb, rel=1e-14) and S == pytest.approx(Pb + Q, rel=1e-14)


def test_update_keeps_variance_in_float32_with_huge_prior():
    """translate.md C3 trick 2: in float32, (1 − K)P̄ is exactly 0 at P̄/Q_meas = 1e8. The posterior must be ≈ Q_meas."""
    x, P, _, _, _ = ex.update(np.float32(0.0), np.float32(1e8), np.float32(3.0), np.float32(1.0))
    assert np.asarray(P).dtype == np.float32, "keep the input dtype"
    assert P > 0.0 and abs(float(P) - 1.0) < 1e-5, f"P = {P}"
    assert abs(float(x) - 3.0) < 1e-4


def test_update_gate_rejects_outliers_and_keeps_inliers():
    # S = 0.1 + 0.05: y = 3 → y²/S = 60 > 6.635, rejected; y = 0.5 → 1.67, accepted
    x, P, y, S, ok = ex.update(1.0, 0.1, 4.0, 0.05, gate=ex.CHI2_1DOF_99)
    assert not ok and (x, P) == (1.0, 0.1) and y == pytest.approx(3.0) and S == pytest.approx(0.15)
    x, P, y, S, ok = ex.update(1.0, 0.1, 1.5, 0.05, gate=ex.CHI2_1DOF_99)
    assert ok and x == pytest.approx(1.0 + 0.5 * 0.1 / 0.15)
    # the gate uses S, not Q_meas alone: a wide prior must accept a large residual
    *_, ok = ex.update(0.0, 100.0, 5.0, 1.0, gate=ex.CHI2_1DOF_99)
    assert ok


def test_update_rejects_nonpositive_S():
    with pytest.raises(ValueError):
        ex.update(0.0, 0.0, 1.0, 0.0)


def test_joseph_variance_monte_carlo_for_any_gain():
    """e⁺ = (1 − K)ē − K v with ē ~ N(0, P̄), v ~ N(0, Q_meas): sample it."""
    r = np.random.default_rng(5)
    Pb, Q = 3.0, 1.2
    e, v = r.normal(0, np.sqrt(Pb), 1_000_000), r.normal(0, np.sqrt(Q), 1_000_000)
    for K in (0.1, Pb / (Pb + Q), 0.9, 1.3):
        mc = np.var((1 - K) * e - K * v)
        assert ex.joseph_variance(Pb, K, Q) == pytest.approx(mc, rel=1e-2)
    assert ex.joseph_variance(Pb, Pb / (Pb + Q), Q) == pytest.approx(Pb * Q / (Pb + Q), rel=1e-12)
    np.testing.assert_allclose(ex.joseph_variance(Pb, np.array([0.0, 1.0]), Q), [Pb, Q])


# ---------------------------------------------------------------- C3 the loop


def dense_loop(zs, x, P, u, R_proc, Q_meas):
    """The p. 147 cell, verbatim except for names: Bayes-form update lines."""
    rows = []
    for z in zs:
        x = x + u
        P = P + R_proc
        xb, Pb = x, P
        x = (P * z + Q_meas * x) / (P + Q_meas)
        P = (P * Q_meas) / (P + Q_meas)
        rows.append((x, P, xb, Pb, z - xb, Pb + Q_meas))
    return np.array(rows)


def test_run_filter_matches_book_first_step_and_dense_loop():
    # pp. 143–145: x0 = N(0, 400), velocity 1, process_var = 1 (R_proc), sensor_var = 2 (Q_meas)
    zs = models.DogHallway(1.0, 1.0, 2.0).simulate(10, np.random.default_rng(0))[1]
    out = ex.run_filter(zs, 0.0, 400.0, 1.0, 1.0, 2.0)
    assert out.shape == (10, 6)
    assert out[0, 3] == pytest.approx(401.0) and out[0, 1] == pytest.approx(1.9901, abs=5e-5)
    np.testing.assert_allclose(out, dense_loop(zs, 0.0, 400.0, 1.0, 1.0, 2.0), rtol=1e-12, atol=1e-12)


def test_run_filter_variance_ignores_the_data_and_accepts_array_u():
    """p. 138/146: P depends on P̄ and Q_meas only. Two different measurement sequences, same P column."""
    r = np.random.default_rng(1)
    a = ex.run_filter(r.normal(0, 5, 30), 0.0, 50.0, 1.0, 2.0, 4.5)
    b = ex.run_filter(r.normal(100, 50, 30), 10.0, 50.0, -3.0, 2.0, 4.5)
    np.testing.assert_allclose(a[:, 1], b[:, 1], rtol=1e-14)
    np.testing.assert_allclose(a[:, 3], b[:, 3], rtol=1e-14)
    us = r.normal(0, 1, 30); zs = r.normal(0, 1, 30)
    np.testing.assert_allclose(ex.run_filter(zs, 0.0, 1.0, us, 2.0, 4.5)[:, 2][1:],
                               ex.run_filter(zs, 0.0, 1.0, us, 2.0, 4.5)[:, 0][:-1] + us[1:], rtol=1e-12)


def test_run_filter_gate_skips_rejected_rows():
    zs = np.zeros(20); zs[10] = 50.0
    out = ex.run_filter(zs, 0.0, 1.0, 0.0, 0.01, 0.1, gate=ex.CHI2_1DOF_99)
    assert out[10, 0] == out[10, 2] and out[10, 1] == out[10, 3]
    assert abs(out[11, 0]) < 1e-9


def test_filter_is_consistent_over_many_runs():
    """Monte Carlo consistency on the model the filter assumes (dog, p. 147 values). Over M runs the
    average NEES e²/P and the average NIS y²/S are 1. A filter with the variances swapped or with P
    computed as the prior's fails one of the two bands by a wide margin."""
    dog = models.DogHallway()
    r = np.random.default_rng(2024)
    M, N, P0 = 300, 60, 25.0
    xs, zs = dog.simulate(N, r, runs=M)
    nees_, nis_ = [], []
    for m in range(M):
        x0 = r.normal(0.0, np.sqrt(P0))          # the start belief N(x0, P0) contains the true x = 0
        out = ex.run_filter(zs[m], x0, P0, dog.u, dog.R_proc, dog.Q_meas)
        nees_.append((out[:, 0] - xs[m]) ** 2 / out[:, 1])
        nis_.append(ex.nis(out[:, 4], out[:, 5]))
    anees, anis = np.mean(nees_), np.mean(nis_)
    assert 0.92 <= anees <= 1.08, f"ANEES {anees:.3f}"
    assert 0.92 <= anis <= 1.08, f"ANIS {anis:.3f}"


def test_nis():
    np.testing.assert_allclose(ex.nis(np.array([2.0, -3.0]), np.array([4.0, 3.0])), [1.0, 3.0])


# ---------------------------------------------------------------- C4 steady state


def iterate_P(R_proc, Q_meas, P=1e3, steps=200_000):
    for _ in range(steps):
        Pn = (P + R_proc) * Q_meas / (P + R_proc + Q_meas)
        if Pn == P:
            break
        P = Pn
    return P


def test_steady_state_matches_book():
    book_close(ex.steady_state(1.0, 2.0)[0], 1.0)            # p. 146
    book_close(ex.steady_state(2.0, 4.5)[0], 2.1623)         # p. 148
    book_close(ex.steady_state(0.05 ** 2, 0.13 ** 2)[0], 0.005)   # p. 157, thermometer


@pytest.mark.parametrize("R_proc,Q_meas", [(1.0, 2.0), (2.0, 4.5), (0.0025, 0.0169), (2.0, 30000.0),
                                           (0.001, 20.0), (1.0, 1e-10), (1e3, 1e-4)])
def test_steady_state_equals_iterated_recursion(R_proc, Q_meas):
    P_inf, K_inf = ex.steady_state(R_proc, Q_meas)
    assert P_inf == pytest.approx(iterate_P(R_proc, Q_meas), rel=1e-12)
    Pb = P_inf + R_proc
    assert K_inf == pytest.approx(Pb / (Pb + Q_meas), rel=1e-12)


def test_steady_state_rejects_zero_process_noise():
    with pytest.raises(ValueError):
        ex.steady_state(0.0, 1.0)


def test_ratio_from_gain_inverts_steady_state():
    for K in (0.01, 0.13232, 0.31770, 0.5, 0.95):
        r = ex.ratio_from_gain(K)
        assert ex.steady_state(r, 1.0)[1] == pytest.approx(K, rel=1e-12)
        assert ex.steady_state(7.0 * r, 7.0)[1] == pytest.approx(K, rel=1e-12)   # only the ratio matters
    with pytest.raises(ValueError):
        ex.ratio_from_gain(1.0)


# ---------------------------------------------------------------- C4 fixed gain


def test_fixed_gain_filter_equals_kf_started_at_steady_state():
    """Started at P0 = P∞ the full filter's gain is K∞ every step: both filters give the same x."""
    R_proc, Q_meas = 2.0, 4.5
    P_inf, K_inf = ex.steady_state(R_proc, Q_meas)
    zs = models.DogHallway().simulate(100, np.random.default_rng(6))[1]
    ref = dense_loop(zs, 0.0, P_inf, 1.0, R_proc, Q_meas)[:, 0]
    np.testing.assert_allclose(ex.fixed_gain_filter(zs, 0.0, 1.0, K_inf), ref, rtol=1e-10, atol=1e-10)


def test_fixed_gain_filter_bias_offset():
    """translate.md C4 trick 5: a u that is wrong by e per step leaves a steady offset e(1 − K)/K."""
    for K in (0.1, 0.48, 0.9):
        xs = ex.fixed_gain_filter(np.zeros(3000), 0.0, 1.0, K)    # truth stays at 0, filter adds 1 m/step
        assert xs[-1] == pytest.approx((1 - K) / K, rel=1e-9)


def test_fixed_gain_variance_is_minimal_at_K_inf():
    R_proc, Q_meas = 2.0, 4.5
    P_inf, K_inf = ex.steady_state(R_proc, Q_meas)
    assert ex.fixed_gain_variance(K_inf, R_proc, Q_meas) == pytest.approx(P_inf, rel=1e-12)
    Ks = np.linspace(0.02, 1.98, 197)
    v = np.array([ex.fixed_gain_variance(K, R_proc, Q_meas) for K in Ks])
    assert abs(Ks[v.argmin()] - K_inf) <= 0.01 and v.min() >= P_inf
    with pytest.raises(ValueError):
        ex.fixed_gain_variance(2.0, R_proc, Q_meas)


def test_fixed_gain_variance_monte_carlo():
    r = np.random.default_rng(7)
    R_proc, Q_meas, runs = 2.0, 4.5, 4000
    for K in (0.2, 0.8):
        truth = np.zeros(runs); est = np.zeros(runs); errs = []
        for k in range(300):
            truth = truth + r.normal(0, np.sqrt(R_proc), runs)
            est = est + K * (truth + r.normal(0, np.sqrt(Q_meas), runs) - est)
            if k >= 100:
                errs.append(est - truth)
        assert ex.fixed_gain_variance(K, R_proc, Q_meas) == pytest.approx(np.var(errs), rel=3e-2)
