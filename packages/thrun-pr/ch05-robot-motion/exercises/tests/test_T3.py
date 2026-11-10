"""Oracle tests for T3. Every oracle is independent of the student code: the book's eq. 5.16 in long double,
RK4 integration of the kinematic ODEs, central finite differences, scipy.stats densities, Monte Carlo
moments over 10⁵–10⁶ samples, and grid quadrature (a density over poses must integrate to 1).

Set STUDY_IMPL=solution to grade the reference solution instead of exercise.py.
"""

from __future__ import annotations

import importlib
import os

import numpy as np
import pytest
from scipy.stats import norm, triang

from .. import models
from ..models import wrap

IMPL = os.environ.get("STUDY_IMPL", "exercise")
ex = importlib.import_module(f"..{'solutions.T3_solution' if IMPL == 'solution' else 'exercise'}", package=__package__)

A_VEL = models.ALPHA_VEL_L5
A_ODO = models.ALPHA_ODO_L7


# ---------------------------------------------------------------- oracles (no student code)


def book_forward_ld(x, v, w, g, dt):
    """Eq. 5.16 in long double, with the exact straight line at ω = 0."""
    L = np.longdouble
    x0, y0, th = (L(c) for c in x)
    v, w, g, dt = L(v), L(w), L(g), L(dt)
    if w == 0:
        return np.array([x0 + v * dt * np.cos(th), y0 + v * dt * np.sin(th), th + g * dt], dtype=np.longdouble)
    r = v / w
    return np.array([x0 - r * np.sin(th) + r * np.sin(th + w * dt),
                     y0 + r * np.cos(th) - r * np.cos(th + w * dt),
                     th + w * dt + g * dt], dtype=np.longdouble)


def rk4(f, s, dt, n=2000):
    h = dt / n
    for _ in range(n):
        k1 = f(s); k2 = f(s + h / 2 * k1); k3 = f(s + h / 2 * k2); k4 = f(s + h * k3)
        s = s + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    return s


def unicycle_ode(v, w):
    return lambda s: np.array([v * np.cos(s[2]), v * np.sin(s[2]), w])


def numeric_jacobian(f, p, eps=1e-6, wrap_rows=()):
    y0 = np.atleast_1d(f(p))
    J = np.zeros((y0.size, p.size))
    for j in range(p.size):
        d = np.zeros_like(p); d[j] = eps
        diff = np.atleast_1d(f(p + d)) - np.atleast_1d(f(p - d))
        for r in wrap_rows:
            diff[r] = wrap(diff[r])
        J[:, j] = diff / (2 * eps)
    return J


def pose_err(a, b):
    e = np.asarray(a, float) - np.asarray(b, float)
    e[..., 2] = wrap(e[..., 2])
    return e


def ref_odometry_compose(X, rot1, trans, rot2):
    th = X[..., 2]
    return np.stack([X[..., 0] + trans * np.cos(th + rot1), X[..., 1] + trans * np.sin(th + rot1),
                     wrap(th + rot1 + rot2)], axis=-1)


def ref_rot_for_noise(r):
    r = abs(wrap(r))
    return min(r, np.pi - r)


# ---------------------------------------------------------------- C1


def test_log_prob_normal_matches_scipy_and_has_a_floor():
    a = np.linspace(-5, 5, 41); b2 = 0.7
    np.testing.assert_allclose(ex.log_prob(a, b2), norm.logpdf(a, scale=np.sqrt(b2)), rtol=1e-12, atol=1e-12)
    # far tail: the naive density underflows to 0, the log stays finite (C1 trick 1)
    assert np.isfinite(ex.log_prob(50.0, 1.0))
    np.testing.assert_allclose(ex.log_prob(50.0, 1.0), norm.logpdf(50.0), rtol=1e-12)
    # robot at rest: b² = 0 must not give nan (C1 trick 2)
    with np.errstate(all="raise"):
        v = ex.log_prob(np.array([0.0, 0.1]), np.array([0.0, 0.0]))
    assert np.isfinite(v[0]) and not np.isnan(v[1])


def test_log_prob_triangular_matches_scipy():
    b2 = 0.5; b = np.sqrt(b2); half = np.sqrt(6) * b
    a = np.linspace(-0.99 * half, 0.99 * half, 31)
    ref = triang.logpdf(a, c=0.5, loc=-half, scale=2 * half)
    np.testing.assert_allclose(ex.log_prob(a, b2, kind="triangular"), ref, rtol=1e-10, atol=1e-12)
    with np.errstate(all="raise"):
        out = ex.log_prob(np.array([1.01 * half, -3 * half]), b2, kind="triangular")
    assert np.all(np.isneginf(out))


# ---------------------------------------------------------------- C2


@pytest.mark.parametrize("w", [0.8, -1.3, 1e-6, 1e-9, 0.0])
def test_velocity_forward_matches_eq_5_16_in_long_double(w):
    x = np.array([0.4, -1.2, 2.9]); v, g, dt = -0.7, 0.05, 1.0
    ref = book_forward_ld(x, v, w, g, dt).astype(float)
    got = ex.velocity_forward(x, v, w, g, dt)
    assert got.shape == (3,)
    np.testing.assert_allclose(pose_err(got, ref), 0.0, atol=1e-9 if w and abs(w) < 1e-5 else 1e-12)


def test_velocity_forward_matches_ode_and_broadcasts():
    r = np.random.default_rng(0)
    M = 6
    X = np.column_stack([r.uniform(-2, 2, M), r.uniform(-2, 2, M), r.uniform(-np.pi, np.pi, M)])
    v = r.uniform(-1.5, 1.5, M); w = r.uniform(-2, 2, M); w[0] = 0.0; dt = 0.7
    got = ex.velocity_forward(X, v, w, np.zeros(M), dt)
    assert got.shape == (M, 3)
    for i in range(M):
        ref = rk4(unicycle_ode(v[i], w[i]), X[i].copy(), dt)
        np.testing.assert_allclose(pose_err(got[i], ref), 0.0, atol=1e-10)
    assert np.all((got[:, 2] >= -np.pi) & (got[:, 2] < np.pi))


def test_velocity_sampler_moments_match_eq_5_10_and_5_15():
    """Monte Carlo, 2·10⁵ samples. Invert each sample with the long-double-free oracle chain:
    the samples' mean must sit at the noise-free pose and their covariance must equal V·diag(b²)·Vᵀ
    to first order (small noise), with V by finite differences of the oracle forward model."""
    rng = np.random.default_rng(1)
    u, dt, M = (0.9, -0.6), 0.5, 200_000
    alpha = (0.004, 0.002, 0.003, 0.004, 0.001, 0.001)
    x0 = np.array([1.0, 2.0, 3.0])
    X = ex.sample_motion_model_velocity(u, np.tile(x0, (M, 1)), alpha, dt, rng)
    assert X.shape == (M, 3)
    v, w = u
    b2 = np.array([alpha[0] * v * v + alpha[1] * w * w, alpha[2] * v * v + alpha[3] * w * w,
                   alpha[4] * v * v + alpha[5] * w * w])
    f = lambda p: book_forward_ld(x0, p[0], p[1], p[2], dt).astype(float)
    mean_ref = f(np.array([v, w, 0.0]))
    V = numeric_jacobian(f, np.array([v, w, 0.0]))
    cov_ref = V @ np.diag(b2) @ V.T
    E = pose_err(X, mean_ref)
    sd = np.sqrt(np.diag(cov_ref))
    for i in range(3):
        assert abs(E[:, i].mean()) < 5 * sd[i] / np.sqrt(M) + 2e-4 * sd[i], f"mean of component {i}"
    np.testing.assert_allclose(np.cov(E.T), cov_ref, rtol=0.03, atol=0.02 * np.abs(cov_ref).max())


def test_velocity_sampler_at_rest_and_without_noise():
    rng = np.random.default_rng(2)
    X = np.array([[0.0, 0.0, 0.5], [1.0, -1.0, -3.0]])
    Y = ex.sample_motion_model_velocity((0.0, 0.0), X, A_VEL, 0.1, rng)
    np.testing.assert_allclose(Y, X, atol=1e-15)            # no command, no noise (C2 trick 5)
    Y = ex.sample_motion_model_velocity((1.0, 0.3), X, (0,) * 6, 0.1, rng)
    for i in range(2):
        np.testing.assert_allclose(pose_err(Y[i], book_forward_ld(X[i], 1.0, 0.3, 0.0, 0.1).astype(float)), 0, atol=1e-12)


# ---------------------------------------------------------------- C3


@pytest.mark.parametrize("v,w", [(1.0, 0.5), (1.0, -0.5), (-1.0, 0.5), (-1.0, -0.5), (0.8, 0.0), (-0.8, 0.0), (0.6, 1e-10)])
def test_velocity_inverse_recovers_sign_and_rate(v, w):
    """Table 5.1 line 7 gives v̂ the sign of the turn; the contract is the sign of the motion (C3 trick 1)."""
    x0 = np.array([0.3, -0.2, 2.2]); dt = 1.0; g = 0.07
    xp = book_forward_ld(x0, v, w, g, dt).astype(float)
    xp[2] = wrap(xp[2])
    v_h, w_h, g_h = ex.velocity_inverse(x0, xp, dt)
    np.testing.assert_allclose([v_h, w_h, g_h], [v, w, g], atol=1e-9)


def test_velocity_inverse_round_trip_many_and_vectorized():
    r = np.random.default_rng(3)
    N, dt = 2000, 0.4
    x0 = np.array([-1.0, 0.5, 3.1])
    v = r.uniform(-2, 2, N); w = r.uniform(-7, 7, N); g = r.uniform(-1, 1, N)   # |ω dt| < 2.8 < π
    w[:50] = 0.0
    Xp = np.array([book_forward_ld(x0, v[i], w[i], g[i], dt).astype(float) for i in range(N)])
    Xp[:, 2] = wrap(Xp[:, 2])
    v_h, w_h, g_h = ex.velocity_inverse(x0, Xp, dt)
    assert np.shape(v_h) == (N,)
    np.testing.assert_allclose(v_h, v, atol=1e-8)
    np.testing.assert_allclose(w_h, w, atol=1e-8)
    np.testing.assert_allclose(wrap(g_h * dt - g * dt), 0.0, atol=1e-8)


@pytest.mark.parametrize("seed", range(10))
def test_velocity_noise_jacobian_matches_finite_differences(seed):
    r = np.random.default_rng(10 + seed)
    x0 = np.array([r.uniform(-2, 2), r.uniform(-2, 2), r.uniform(-np.pi, np.pi)])
    dt = r.uniform(0.1, 1.0)
    v = r.uniform(-1.5, 1.5); w = 0.0 if seed in (0, 1) else (1e-7 if seed == 2 else r.uniform(-2, 2))
    g = r.uniform(-0.2, 0.2)
    f = lambda p: book_forward_ld(x0, p[0], p[1], p[2], dt).astype(float)
    if w == 0.0 or abs(w) < 1e-5:   # the book form is singular at 0: differentiate the ODE instead
        f = lambda p: rk4(unicycle_ode(p[0], p[1]), x0.copy(), dt, n=400) + np.array([0, 0, p[2] * dt])
    Jn = numeric_jacobian(f, np.array([v, w, g]), eps=1e-5, wrap_rows=(2,))
    J = ex.velocity_noise_jacobian(x0, v, w, dt)
    assert J.shape == (3, 3)
    np.testing.assert_allclose(J, Jn, rtol=1e-6, atol=1e-8)


def ref_log_density_velocity(xp, u, x0, alpha, dt):
    """Dense oracle: invert by root finding on the forward model, score with scipy."""
    from scipy.optimize import least_squares
    def res(p):
        e = book_forward_ld(x0, p[0], p[1], p[2], dt).astype(float) - xp
        e[2] = wrap(e[2]); return e
    p = least_squares(res, x0=np.array([u[0], u[1], 0.0]), xtol=1e-15, ftol=1e-15, gtol=1e-15).x
    v, w = u
    a = alpha
    return (norm.logpdf(v - p[0], scale=np.sqrt(a[0] * v * v + a[1] * w * w))
            + norm.logpdf(w - p[1], scale=np.sqrt(a[2] * v * v + a[3] * w * w))
            + norm.logpdf(p[2], scale=np.sqrt(a[4] * v * v + a[5] * w * w)))


def test_log_motion_model_velocity_matches_dense_oracle():
    u, dt, x0 = (1.0, -0.5), 1.0, np.array([0.0, 0.0, 0.0])
    # hypotheses from the oracle forward model, not from the student sampler; (1, -0.5) is a right turn
    pts = [book_forward_ld(x0, 1.0 + dv, -0.5 + dw, dg, dt).astype(float)
           for dv, dw, dg in [(0, 0, 0), (0.1, -0.05, 0.02), (-0.2, 0.1, -0.03), (0.05, 0.2, 0.0)]]
    pts = np.array(pts); pts[:, 2] = wrap(pts[:, 2])
    got = ex.log_motion_model_velocity(pts, u, x0, A_VEL, dt)
    ref = [ref_log_density_velocity(p, u, x0, A_VEL, dt) for p in pts]
    np.testing.assert_allclose(got, ref, rtol=1e-7, atol=1e-7)


def test_velocity_pose_density_integrates_to_one():
    """Quadrature over an (x′, y′, θ′) grid: a density over poses has mass 1 (C3 trick 5)."""
    u, dt, x0 = (1.0, 0.8), 2.0, np.array([0.0, 0.0, 0.0])
    xs = np.linspace(-0.5, 2.5, 121); ys = np.linspace(-0.5, 2.8, 133); ts = np.linspace(-0.6, 3.4, 161)
    Xg, Yg, Tg = np.meshgrid(xs, ys, ts, indexing="ij")
    P = np.column_stack([Xg.ravel(), Yg.ravel(), wrap(Tg.ravel())])
    lp = ex.log_motion_model_velocity(P, u, x0, A_VEL, dt, pose_density=True)
    cell = (xs[1] - xs[0]) * (ys[1] - ys[0]) * (ts[1] - ts[0])
    mass = np.exp(lp).sum() * cell
    assert abs(mass - 1.0) < 0.01, f"pose density integrates to {mass:.4f}"
    lp0 = ex.log_motion_model_velocity(P, u, x0, A_VEL, dt, pose_density=False)
    assert abs(np.exp(lp0).sum() * cell - 1.0) > 0.05, "without the Jacobian the mass should not be 1"


# ---------------------------------------------------------------- C4


def test_odometry_params_compose_back_and_wrap():
    r = np.random.default_rng(5)
    N = 500
    P0 = np.array([0.5, -1.0, 3.0])
    P1 = np.column_stack([r.uniform(-3, 3, N), r.uniform(-3, 3, N), r.uniform(-np.pi, np.pi, N)])
    rot1, trans, rot2 = ex.odometry_params(P0, P1)
    assert np.shape(rot1) == (N,)
    np.testing.assert_allclose(pose_err(ref_odometry_compose(P0, rot1, trans, rot2), P1), 0.0, atol=1e-12)
    for a in (rot1, rot2):
        assert np.all((a >= -np.pi) & (a < np.pi))
    np.testing.assert_allclose(trans, np.hypot(P1[:, 0] - P0[0], P1[:, 1] - P0[1]), rtol=1e-14)


def test_odometry_params_rotation_in_place():
    for th in (0.0, 2.6, -2.9):
        P0 = np.array([1.0, 1.0, th]); P1 = np.array([1.0 + 1e-4, 1.0, wrap(th + 0.5)])
        rot1, trans, rot2 = ex.odometry_params(P0, P1)
        assert rot1 == 0.0
        np.testing.assert_allclose(rot2, 0.5, atol=1e-12)


def ref_odometry_variances(P0, P1, alpha):
    dx, dy = P1[0] - P0[0], P1[1] - P0[1]
    t = np.hypot(dx, dy)
    r1 = 0.0 if t < 0.01 else wrap(np.arctan2(dy, dx) - P0[2])
    r2 = wrap(P1[2] - P0[2] - r1)
    n1, n2 = ref_rot_for_noise(r1), ref_rot_for_noise(r2)
    a1, a2, a3, a4 = alpha
    return (r1, t, r2), (a1 * n1**2 + a2 * t**2, a3 * t**2 + a4 * (n1**2 + n2**2), a1 * n2**2 + a2 * t**2)


@pytest.mark.parametrize("case", ["forward_turn", "reverse", "spin"])
def test_odometry_sampler_moments(case):
    """Monte Carlo, 3·10⁵ samples: decompose every sample by the oracle and check the three δ̂ have
    the means and variances of eq. 5.37–5.39 (measured δ, reverse-symmetric)."""
    rng = np.random.default_rng(6)
    o0 = np.array([2.0, 1.0, 2.5])
    o1 = {"forward_turn": o0 + np.array([0.4 * np.cos(2.7), 0.4 * np.sin(2.7), 0.6]),
          "reverse": o0 + np.array([-0.5 * np.cos(2.5), -0.5 * np.sin(2.5), 0.0]),
          "spin": o0 + np.array([0.0, 0.0, -0.7])}[case]
    o1[2] = wrap(o1[2])
    alpha = (0.05, 0.01, 0.05, 0.01)
    (r1, t, r2), b2 = ref_odometry_variances(o0, o1, alpha)
    x0 = np.array([-1.0, 4.0, -2.0]); M = 300_000
    X0 = np.tile(x0, (M, 1))
    Y = ex.sample_motion_model_odometry((o0, o1), X0, alpha, rng)
    np.testing.assert_array_equal(X0, np.tile(x0, (M, 1)))          # input not modified
    if case == "spin":   # δrot1 = 0 exactly; δ̂trans is pure noise along the heading (variance α₄δrot2²)
        d = Y[:, :2] - x0[:2]
        along = d[:, 0] * np.cos(x0[2]) + d[:, 1] * np.sin(x0[2])
        np.testing.assert_allclose(along * np.cos(x0[2]), d[:, 0], atol=1e-12)
        np.testing.assert_allclose(along.var(), b2[1], rtol=0.02)
        dth = wrap(Y[:, 2] - x0[2])
        np.testing.assert_allclose(dth.mean(), r2, atol=5 * np.sqrt(b2[2] / M))
        np.testing.assert_allclose(dth.var(), b2[2], rtol=0.02)
        return
    d = Y[:, :2] - x0[:2]
    h_t = np.hypot(d[:, 0], d[:, 1])
    sgn = np.where(np.cos(np.arctan2(d[:, 1], d[:, 0]) - x0[2] - r1) < 0, -1.0, 1.0)   # δ̂trans may cross 0
    h_r1 = wrap(np.arctan2(sgn * d[:, 1], sgn * d[:, 0]) - x0[2])
    h_t = sgn * h_t
    h_r2 = wrap(Y[:, 2] - x0[2] - h_r1)
    for got, mean, var in [(wrap(h_r1 - r1), 0.0, b2[0]), (h_t - t, 0.0, b2[1]), (wrap(h_r2 - r2), 0.0, b2[2])]:
        np.testing.assert_allclose(got.mean(), mean, atol=5 * np.sqrt(var / M))
        np.testing.assert_allclose(got.var(), var, rtol=0.03)
    if case == "reverse":   # reversing is as noisy as going forward the same distance (C4 trick 3)
        assert b2[0] == pytest.approx(alpha[1] * t * t)


@pytest.mark.parametrize("case", ["forward", "reverse"])
def test_log_motion_model_odometry_matches_dense_oracle(case):
    """Reversing puts δrot1 and δrot2 at ±π, so a small error on either side of the seam must be wrapped."""
    o0 = np.array([0.0, 0.0, 0.3])
    o1 = np.array([0.5, 0.3, 0.9]) if case == "forward" else np.array([-0.5 * np.cos(0.3), -0.5 * np.sin(0.3), 0.3])
    x0 = np.array([3.0, -2.0, -2.8])
    (r1, t, r2), b2 = ref_odometry_variances(o0, o1, A_ODO)
    errs = [(0, 0, 0), (0.02, -0.01, 0.03), (-0.05, 0.03, -0.01), (0.1, 0.0, 0.1), (-0.03, 0.01, 0.02)]
    hyps = np.array([ref_odometry_compose(x0, r1 + e1, t + e2, r2 + e3) for e1, e2, e3 in errs])
    ref = [norm.logpdf(e1, scale=np.sqrt(b2[0])) + norm.logpdf(-e2, scale=np.sqrt(b2[1]))
           + norm.logpdf(e3, scale=np.sqrt(b2[2])) for e1, e2, e3 in errs]
    np.testing.assert_allclose(ex.log_motion_model_odometry(hyps, (o0, o1), x0, A_ODO), ref, rtol=1e-9, atol=1e-9)


def test_log_motion_model_odometry_is_invariant_to_rotating_the_world():
    """Rotating x_{t-1} and x_t together about the origin changes nothing; it moves headings across ±π
    (p. 135: the δrot2 error 'has to be truncated')."""
    o0 = np.array([0.0, 0.0, 0.0]); o1 = np.array([0.4, 0.05, 0.3])
    x0 = np.array([1.0, 0.5, 2.9])
    hyps = np.array([ref_odometry_compose(x0, 0.12, 0.41, 0.2 + d) for d in np.linspace(-0.3, 0.3, 13)])
    base = ex.log_motion_model_odometry(hyps, (o0, o1), x0, A_ODO)
    for phi in (0.15, 0.4, -2.0):
        c, s = np.cos(phi), np.sin(phi)
        rot = lambda P: np.stack([c * P[..., 0] - s * P[..., 1], s * P[..., 0] + c * P[..., 1], wrap(P[..., 2] + phi)], -1)
        np.testing.assert_allclose(ex.log_motion_model_odometry(rot(hyps), (o0, o1), rot(x0), A_ODO), base, atol=1e-8)


def test_odometry_pose_density_integrates_to_one_and_is_finite_at_rest():
    o0 = np.array([0.0, 0.0, 0.0]); o1 = np.array([0.5, 0.2, 0.6]); x0 = np.array([0.0, 0.0, 0.0])
    alpha = (0.05, 0.005, 0.05, 0.005)
    xs = np.linspace(0.1, 0.9, 121); ys = np.linspace(-0.25, 0.65, 121); ts = np.linspace(0.05, 1.15, 141)
    Xg, Yg, Tg = np.meshgrid(xs, ys, ts, indexing="ij")
    P = np.column_stack([Xg.ravel(), Yg.ravel(), Tg.ravel()])
    lp = ex.log_motion_model_odometry(P, (o0, o1), x0, alpha, pose_density=True)
    mass = np.exp(lp).sum() * (xs[1] - xs[0]) * (ys[1] - ys[0]) * (ts[1] - ts[0])
    assert abs(mass - 1.0) < 0.01, f"pose density integrates to {mass:.4f}"
    with np.errstate(invalid="raise"):
        v = ex.log_motion_model_odometry(x0, (o0, o0), x0, alpha)
    assert np.isfinite(v)


# ---------------------------------------------------------------- C5


def test_map_sampler_returns_free_poses_and_matches_rejection():
    m = models.WallMap()
    rng = np.random.default_rng(7)
    u, dt = (1.0, -0.35), 3.0
    alpha = (0.03, 0.03, 0.03, 0.03, 0.005, 0.005)
    x0 = np.array([0.0, 0.0, np.pi / 2]); M = 60_000
    # oracle sampler: the book's closed form (5.16) in NumPy, independent of the student code
    def oracle_sampler(u_, X, r):
        K = len(X); v, w = u_
        vh = v + r.normal(size=K) * np.sqrt(alpha[0] * v * v + alpha[1] * w * w)
        wh = w + r.normal(size=K) * np.sqrt(alpha[2] * v * v + alpha[3] * w * w)
        gh = r.normal(size=K) * np.sqrt(alpha[4] * v * v + alpha[5] * w * w)
        rr = vh / wh; th = X[:, 2]
        return np.stack([X[:, 0] - rr * np.sin(th) + rr * np.sin(th + wh * dt),
                         X[:, 1] + rr * np.cos(th) - rr * np.cos(th + wh * dt), wrap(th + (wh + gh) * dt)], -1)
    Xn, pi = ex.sample_motion_model_with_map(u, np.tile(x0, (M, 1)), oracle_sampler, m.in_free, rng)
    assert Xn.shape == (M, 3) and pi.shape == (M,)
    assert np.all(m.in_free(Xn[pi == 1.0]))
    assert pi.mean() > 0.999
    # rejection sampling by hand: the accepted cloud has the same mean
    ref = []
    r2 = np.random.default_rng(8)
    while sum(len(a) for a in ref) < M:
        Y = oracle_sampler(u, np.tile(x0, (M, 1)), r2); ref.append(Y[m.in_free(Y)])
    ref = np.concatenate(ref)[:M]
    np.testing.assert_allclose(Xn[:, :2].mean(0), ref[:, :2].mean(0), atol=0.01)
    np.testing.assert_allclose(Xn[:, :2].std(0), ref[:, :2].std(0), rtol=0.03)


def test_map_sampler_terminates_and_redraws_only_failures():
    calls = []

    def sampler(u, X, rng):           # deterministic: moves 1 m along x; counts how many it was asked to move
        calls.append(len(X))
        return X + np.array([1.0, 0.0, 0.0])

    in_free = lambda X: X[:, 0] < 5.0  # everything at x ≥ 5 is a wall
    X = np.array([[0.0, 0.0, 0.0], [4.5, 0.0, 0.0], [1.0, 0.0, 0.0]])
    Xn, pi = ex.sample_motion_model_with_map(None, X, sampler, in_free, np.random.default_rng(0), max_tries=4)
    np.testing.assert_array_equal(pi, [1.0, 0.0, 1.0])
    assert calls == [3, 1, 1, 1], f"sampler calls {calls}: redraw only the failing particle, max_tries in total"
    np.testing.assert_allclose(Xn[1], [5.5, 0.0, 0.0])    # redrawn from its own x_{t-1}, not from the last draw


# ---------------------------------------------------------------- book exercises 4-5 and 7


def bicycle_ode(v, phi, l):
    return lambda s: np.array([v * np.cos(s[2]), v * np.sin(s[2]), v * np.tan(phi) / l])   # rear axle


@pytest.mark.parametrize("phi", [0.0, 0.3, -0.5])
def test_bicycle_without_noise_matches_ode(phi):
    model = models.Bicycle(l=1.2, sigma_v=0.0, sigma_phi=0.0)
    F0 = np.array([[1.0, 2.0, 0.4], [-1.0, 0.0, -2.8]]); v, dt = 0.9, 1.5
    got = ex.sample_motion_model_bicycle((v, phi), F0, model, dt, np.random.default_rng(0))
    for i in range(2):
        th = F0[i, 2]
        rear = rk4(bicycle_ode(v, phi, model.l), np.array([F0[i, 0] - model.l * np.cos(th), F0[i, 1] - model.l * np.sin(th), th]), dt)
        front = np.array([rear[0] + model.l * np.cos(rear[2]), rear[1] + model.l * np.sin(rear[2]), rear[2]])
        np.testing.assert_allclose(pose_err(got[i], front), 0.0, atol=1e-10)


def test_bicycle_noise_matches_monte_carlo_oracle():
    model = models.Bicycle(l=1.0, sigma_v=0.1, sigma_phi=np.deg2rad(5))
    F0 = np.array([0.0, 0.0, 0.0]); u, dt, M = (1.0, 0.25), 1.0, 200_000
    got = ex.sample_motion_model_bicycle(u, np.tile(F0, (M, 1)), model, dt, np.random.default_rng(9))
    r = np.random.default_rng(10)
    v = u[0] + model.sigma_v * r.normal(size=M); ph = u[1] + model.sigma_phi * r.normal(size=M)
    w = v * np.tan(ph) / model.l
    th1 = w * dt
    rx = -model.l + v / w * np.sin(th1); ry = v / w * (1 - np.cos(th1))
    ref = np.column_stack([rx + model.l * np.cos(th1), ry + model.l * np.sin(th1), th1])
    np.testing.assert_allclose(got.mean(0), ref.mean(0), atol=2e-3)
    C, Cr = np.cov(got.T), np.cov(ref.T)
    tol = 6 * np.sqrt(np.outer(np.diag(Cr), np.diag(Cr)) / M) + 0.02 * np.abs(Cr)
    assert np.all(np.abs(C - Cr) < tol), f"covariance\n{C}\nvs oracle\n{Cr}"


@pytest.mark.parametrize("vx,vy,w", [(0.5, 0.3, 0.8), (0.0, -0.4, -1.1), (0.6, 0.2, 0.0), (0.0, 0.0, 0.7)])
def test_holonomic_without_noise_matches_ode(vx, vy, w):
    model = models.Holonomic(A=np.zeros((4, 3)))
    X0 = np.array([[1.0, -1.0, 2.0], [0.0, 0.0, -3.0]]); dt = 1.3
    got = ex.sample_motion_model_holonomic((vx, vy, w), X0, model, dt, np.random.default_rng(0))
    ode = lambda s: np.array([vx * np.cos(s[2]) - vy * np.sin(s[2]), vx * np.sin(s[2]) + vy * np.cos(s[2]), w])
    for i in range(2):
        np.testing.assert_allclose(pose_err(got[i], rk4(ode, X0[i].copy(), dt)), 0.0, atol=1e-10)


def test_holonomic_noise_variances():
    """With ω = 0 and a tiny Δt the pose change is linear in the noise: check each variance by Monte Carlo."""
    A = np.array([[0.02, 0.005, 0.01], [0.005, 0.04, 0.01], [0.0, 0.0, 0.03], [0.0, 0.0, 0.005]])
    model = models.Holonomic(A=A)
    u = (0.8, 0.5, 0.0); dt, M = 1e-3, 400_000
    got = ex.sample_motion_model_holonomic(u, np.zeros((M, 3)), model, dt, np.random.default_rng(11))
    b2 = A @ np.array([u[0]**2, u[1]**2, u[2]**2])
    np.testing.assert_allclose(got[:, 0].var() / dt**2, b2[0], rtol=0.02)
    np.testing.assert_allclose(got[:, 1].var() / dt**2, b2[1], rtol=0.02)
    np.testing.assert_allclose(got[:, 2].var() / dt**2, b2[2] + b2[3], rtol=0.02)
