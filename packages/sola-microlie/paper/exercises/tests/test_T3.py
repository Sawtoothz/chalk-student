"""Oracle tests for T3. Every oracle is independent of the code under test:

- `scipy.linalg.expm` / `logm` of the hat matrix and `scipy.spatial.transform.Rotation` for Exp and Log;
- central finite differences of definition (41a), computed with expm/logm, for every Jacobian;
- the generic adjoint (31) and the identities (32), (75), (76);
- Taylor series written out in the test for the small-angle limits;
- dense Kalman formulas with FD Jacobians; Monte Carlo propagation (10⁵ samples) for (100);
- Monte Carlo consistency (ANEES over M independent runs) for the ESKF;
- a noise-free Fig. 12 problem whose solution is known exactly, for the smoother.

Set STUDY_IMPL=solution to grade the reference solution instead of exercise.py.
"""

from __future__ import annotations

import importlib
import os

import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from scipy.stats import chi2

from .. import models as M

IMPL = os.environ.get("STUDY_IMPL", "exercise")
ex = importlib.import_module(f"..{'solutions.T3_solution' if IMPL == 'solution' else 'exercise'}", package=__package__)


def unit(v):
    return v / np.linalg.norm(v)


def fd_right(f, x, retract, minus, dim, eps=1e-6):
    """Central FD of (41a): column j = (f(x ⊕ ε e_j) ⊖ f(x)) − (f(x ⊕ −ε e_j) ⊖ f(x)), divided by 2ε."""
    y0 = f(x)
    cols = []
    for j in range(dim):
        d = np.zeros(dim); d[j] = eps
        cols.append((minus(f(retract(x, d)), y0) - minus(f(retract(x, -d)), y0)) / (2 * eps))
    return np.column_stack(cols)


euclid_plus = lambda x, d: x + d
euclid_minus = lambda a, b: a - b
so3_minus_ref = lambda R1, R0: Rotation.from_matrix(R0.T @ R1).as_rotvec()
se2_plus_ref = M.se2_rplus_ref
se2_minus_ref = M.se2_rminus_ref


def random_theta(rng, lo=0.1, hi=np.pi - 0.1):
    return unit(rng.normal(size=3)) * rng.uniform(lo, hi)


def random_tau(rng, th_max=np.pi - 0.2):
    return np.r_[rng.uniform(-2, 2, 2), rng.uniform(-th_max, th_max)]


# ---------------------------------------------------------------- T3.1 SO(3) Exp / Log (C1)


@pytest.mark.parametrize("seed", range(10))
def test_so3_exp_matches_expm(seed):
    rng = np.random.default_rng(seed)
    th = random_theta(rng, 0.0, 3.5)
    np.testing.assert_allclose(ex.so3_exp(th), M.so3_Exp_ref(th), atol=1e-13)


def test_so3_exp_at_and_near_zero():
    np.testing.assert_array_equal(ex.so3_exp(np.zeros(3)), np.eye(3))
    for s in [1e-12, 1e-9, 1e-6]:
        th = unit(np.array([0.3, -0.5, 0.8])) * s
        W = M.so3_hat(th)
        ref = np.eye(3) + W + 0.5 * W @ W                        # series, exact to O(s^3)
        R = ex.so3_exp(th)
        assert np.all(np.isfinite(R)), f"NaN/inf at |θ| = {s}"
        np.testing.assert_allclose(R, ref, atol=1e-15 + s ** 3)


@pytest.mark.parametrize("seed", range(10))
def test_so3_log_inverts_exp(seed):
    rng = np.random.default_rng(100 + seed)
    th = random_theta(rng, 0.0, np.pi - 1e-3)
    np.testing.assert_allclose(ex.so3_log(Rotation.from_rotvec(th).as_matrix()), th, atol=1e-12)


@pytest.mark.parametrize("angle", [0.0, 1e-12, 1e-9, 1e-6, np.pi - 1e-3, np.pi - 1e-7])
def test_so3_log_at_both_ends(angle):
    """θ = 0 (robot at rest) and θ → π (a 180° error after relocalization). The printed (135) returns NaN at 0
    and is 0.16 rad wrong at π − 1e-7 (translate.md C1, trick 3)."""
    rng = np.random.default_rng(7)
    for _ in range(20):
        th = unit(rng.normal(size=3)) * angle
        R = Rotation.from_rotvec(th).as_matrix()
        out = ex.so3_log(R)
        assert np.all(np.isfinite(out)), f"NaN at |θ| = {angle}"
        np.testing.assert_allclose(out, th, atol=1e-12)


# ---------------------------------------------------------------- T3.2 SO(3) Jacobians (C3)


@pytest.mark.parametrize("seed", range(10))
def test_so3_Jr_matches_finite_differences(seed):
    rng = np.random.default_rng(200 + seed)
    th = random_theta(rng)
    Jn = fd_right(lambda t: Rotation.from_rotvec(t).as_matrix(), th, euclid_plus, so3_minus_ref, 3)
    np.testing.assert_allclose(ex.so3_Jr(th), Jn, atol=1e-7)


@pytest.mark.parametrize("seed", range(10))
def test_so3_Jrinv_is_the_inverse_and_Log_jacobian(seed):
    """J_r⁻¹ is the right Jacobian of Log (79): FD of R ↦ Log(R) at R = Exp(θ), perturbing R on the right."""
    rng = np.random.default_rng(300 + seed)
    th = random_theta(rng, 0.1, np.pi - 1e-2)
    R = Rotation.from_rotvec(th).as_matrix()
    Jn = fd_right(lambda X: Rotation.from_matrix(X).as_rotvec(), R,
                  lambda X, d: X @ M.so3_Exp_ref(d), euclid_minus, 3)
    np.testing.assert_allclose(ex.so3_Jrinv(th), Jn, atol=1e-6)
    np.testing.assert_allclose(ex.so3_Jrinv(th) @ ex.so3_Jr(th), np.eye(3), atol=1e-12)


@pytest.mark.parametrize("seed", range(5))
def test_so3_jacobian_identities_75_76(seed):
    """(76) J_l(θ) = J_r(−θ) and (75) Ad_{Exp(θ)} = R = J_l(θ) J_r⁻¹(θ). The oracle R comes from expm."""
    rng = np.random.default_rng(400 + seed)
    th = random_theta(rng)
    np.testing.assert_allclose(ex.so3_Jr(-th) @ ex.so3_Jrinv(th), M.so3_Exp_ref(th), atol=1e-12)


@pytest.mark.parametrize("s", [0.0, 1e-12, 1e-9, 1e-6, 1e-4])
def test_so3_jacobians_at_small_angles(s):
    """Series: J_r = I − ½W + ⅙W² + O(θ³), J_r⁻¹ = I + ½W + (1/12)W² + O(θ⁴). The printed (1 − cos θ)/θ² is 0 in
    float64 below 1e-8 rad (lecture L17), which drops the ½W term entirely; at θ = 0 the printed forms are NaN."""
    th = unit(np.array([-0.2, 0.9, 0.4])) * s
    W = M.so3_hat(th)
    Jr, Jri = ex.so3_Jr(th), ex.so3_Jrinv(th)
    assert np.all(np.isfinite(Jr)) and np.all(np.isfinite(Jri)), f"NaN/inf at |θ| = {s}"
    np.testing.assert_allclose(Jr, np.eye(3) - 0.5 * W + W @ W / 6, atol=1e-15 + s ** 3)
    np.testing.assert_allclose(Jri, np.eye(3) + 0.5 * W + W @ W / 12, atol=1e-15 + s ** 4)


# ---------------------------------------------------------------- T3.3 SE(2) Exp / Log (C4)


@pytest.mark.parametrize("seed", range(10))
def test_se2_exp_log_match_expm_logm(seed):
    rng = np.random.default_rng(500 + seed)
    tau = random_tau(rng)
    np.testing.assert_allclose(ex.se2_exp(tau), M.se2_Exp_ref(tau), atol=1e-13)
    np.testing.assert_allclose(ex.se2_log(M.se2_Exp_ref(tau)), tau, atol=1e-10)


@pytest.mark.parametrize("th", [0.0, 1e-12, 2e-7, 1e-4])
def test_se2_exp_log_straight_line(th):
    """Driving straight: θ = ω δt is 0 or tiny. ρ must come back exactly (no 0/0 in V(θ) or V⁻¹)."""
    tau = np.array([0.7, -0.3, th])
    T = ex.se2_exp(tau)
    assert np.all(np.isfinite(T)), f"NaN at θ = {th}"
    np.testing.assert_allclose(T, M.se2_Exp_ref(tau), atol=1e-15)
    np.testing.assert_allclose(ex.se2_log(T), tau, atol=1e-15)


def test_se2_log_angle_in_every_quadrant():
    for th in [0.5, 2.0, 3.1, -0.5, -2.0, -3.1]:
        X = M.pose(1.0, 2.0, th)
        assert abs(ex.se2_log(X)[2] - th) < 1e-14, f"θ = {th}: got {ex.se2_log(X)[2]}"


# ---------------------------------------------------------------- T3.4 SE(2) adjoint and right Jacobian (C2, C4)


@pytest.mark.parametrize("seed", range(10))
def test_se2_Ad_matches_generic_and_eq32(seed):
    rng = np.random.default_rng(600 + seed)
    X, tau = M.random_pose(rng), random_tau(rng)
    A = ex.se2_Ad(X)
    np.testing.assert_allclose(A, M.se2_Ad_ref(X), atol=1e-13)
    # (32): X ⊕ τ = (Ad_X τ) ⊕ X, exactly
    np.testing.assert_allclose(X @ M.se2_Exp_ref(tau), M.se2_Exp_ref(A @ tau) @ X, atol=1e-12)


@pytest.mark.parametrize("seed", range(10))
def test_se2_Jr_matches_finite_differences(seed):
    rng = np.random.default_rng(700 + seed)
    tau = random_tau(rng)
    np.testing.assert_allclose(ex.se2_Jr(tau), M.se2_Jr_ref(tau), atol=1e-7)


@pytest.mark.parametrize("th", [0.0, 1e-12, 2e-7, 1e-6, 1e-4])
def test_se2_Jr_third_column_at_small_angle(th):
    """Series of (163) about θ = 0: column 3 = (−ρ₂/2 + θρ₁/6, ρ₁/2 + θρ₂/6, 1) + O(θ²). As printed, column 3 is off
    by 2.7e-3 at θ = 2e-7 (translate.md C4, trick 1); at θ = 0 it is NaN."""
    r1, r2 = 0.6, -0.8
    J = ex.se2_Jr(np.array([r1, r2, th]))
    assert np.all(np.isfinite(J)), f"NaN at θ = {th}"
    ref = np.array([-r2 / 2 + th * r1 / 6, r1 / 2 + th * r2 / 6, 1.0])
    np.testing.assert_allclose(J[:, 2], ref, atol=1e-14 + th ** 2)


# ---------------------------------------------------------------- T3.5 minus and its two blocks (C3: (26), (82), (83))


@pytest.mark.parametrize("seed", range(10))
def test_se2_rminus_value_and_blocks(seed):
    rng = np.random.default_rng(800 + seed)
    X = M.random_pose(rng, 2.0)
    Y = X @ M.se2_Exp_ref(random_tau(rng, 2.5))
    tau, J_Y, J_X = ex.se2_rminus(Y, X)
    np.testing.assert_allclose(tau, M.se2_rminus_ref(Y, X), atol=1e-10)
    Jn_Y = fd_right(lambda A: M.se2_rminus_ref(A, X), Y, se2_plus_ref, euclid_minus, 3)
    Jn_X = fd_right(lambda B: M.se2_rminus_ref(Y, B), X, se2_plus_ref, euclid_minus, 3)
    np.testing.assert_allclose(J_Y, Jn_Y, atol=1e-6)
    np.testing.assert_allclose(J_X, Jn_X, atol=1e-6)


# ---------------------------------------------------------------- T3.6 beacon expectation (95), H by the chain rule


@pytest.mark.parametrize("seed", range(10))
def test_beacon_expect_and_jacobians(seed):
    rng = np.random.default_rng(900 + seed)
    X, b = M.random_pose(rng), rng.uniform(-4, 4, 2)
    e, H_X, H_b = ex.beacon_expect(X, b)
    np.testing.assert_allclose(e, (np.linalg.inv(X) @ np.r_[b, 1.0])[:2], atol=1e-13)
    f_X = lambda A: (np.linalg.inv(A) @ np.r_[b, 1.0])[:2]
    f_b = lambda c: (np.linalg.inv(X) @ np.r_[c, 1.0])[:2]
    np.testing.assert_allclose(H_X, fd_right(f_X, X, se2_plus_ref, euclid_minus, 3), atol=1e-7)
    np.testing.assert_allclose(H_b, fd_right(f_b, b, euclid_plus, euclid_minus, 2), atol=1e-7)


# ---------------------------------------------------------------- T3.7 ESKF on SE(2) (C8)


@pytest.mark.parametrize("seed", range(5))
def test_eskf_predict_matches_dense_reference(seed):
    """(99)-(100) with F = Ad_{Exp(u)}⁻¹ (dense inverse of the generic Ad) and G = J_r(u) by FD."""
    rng = np.random.default_rng(1000 + seed)
    X, P, u = M.random_pose(rng), M.random_spd(rng, 3, 0.01), random_tau(rng, 1.0)
    Rp = M.random_spd(rng, 3, 1e-3)
    Xn, Pn = ex.eskf_predict(X, P, u, Rp)
    F = np.linalg.inv(M.se2_Ad_ref(M.se2_Exp_ref(u)))
    G = M.se2_Jr_ref(u)
    np.testing.assert_allclose(Xn, X @ M.se2_Exp_ref(u), atol=1e-13)
    np.testing.assert_allclose(Pn, F @ P @ F.T + G @ Rp @ G.T, atol=1e-8)
    np.testing.assert_allclose(Pn, Pn.T, atol=1e-15)


def test_eskf_predict_matches_monte_carlo():
    """Sample X_true = X̂ ⊕ ε, ε ~ N(0, P); the true control is ũ − w, w ~ N(0, R_proc) (93); step with
    (94); take ⊖ to the predicted mean. 10⁵ samples; the sample covariance must match (100) to first order."""
    rng = np.random.default_rng(11)
    X = M.pose(1.0, -0.5, 0.4)
    P = np.diag([0.02, 0.02, 0.02]) ** 2
    Rp = np.diag([0.01, 0.005, 0.01]) ** 2
    u = np.array([0.3, 0.0, 0.2])
    Xn, Pn = ex.eskf_predict(X, P, u, Rp)
    N = 100_000
    eps = rng.multivariate_normal(np.zeros(3), P, N)
    w = rng.multivariate_normal(np.zeros(3), Rp, N)
    Xn_inv = np.linalg.inv(Xn)
    devs = np.array([M.se2_Log_ref(Xn_inv @ X @ M.se2_Exp_ref(eps[i]) @ M.se2_Exp_ref(u - w[i])) for i in range(0, N, 10)])
    # logm is slow; every tenth sample (10⁴) is enough for a 5 % check on a 3×3 covariance
    C = np.cov(devs.T)
    assert np.linalg.norm(C - Pn) / np.linalg.norm(Pn) < 0.05, f"MC {C} vs (100) {Pn}"


@pytest.mark.parametrize("reset", [False, True])
def test_eskf_update_matches_dense_reference(reset):
    rng = np.random.default_rng(12)
    for _ in range(5):
        X, P = M.random_pose(rng), M.random_spd(rng, 3, 0.01)
        b, Q = rng.uniform(-3, 3, 2), M.random_spd(rng, 2, 1e-3)
        y = (np.linalg.inv(X) @ np.r_[b, 1.0])[:2] + rng.normal(0, 0.05, 2)
        Xn, Pn, z, Z = ex.eskf_update(X, P, y, b, Q, reset=reset)
        f_X = lambda A: (np.linalg.inv(A) @ np.r_[b, 1.0])[:2]
        H = fd_right(f_X, X, se2_plus_ref, euclid_minus, 3)
        z_ref = y - f_X(X)
        Z_ref = H @ P @ H.T + Q
        K = P @ H.T @ np.linalg.inv(Z_ref)
        dx = K @ z_ref
        P_ref = P - K @ Z_ref @ K.T
        if reset:
            Jr = M.se2_Jr_ref(dx)
            P_ref = Jr @ P_ref @ Jr.T
        np.testing.assert_allclose(z, z_ref, atol=1e-12)
        np.testing.assert_allclose(Z, Z_ref, atol=1e-8)
        np.testing.assert_allclose(Xn, X @ M.se2_Exp_ref(dx), atol=1e-7)
        np.testing.assert_allclose(Pn, P_ref, atol=1e-8)
        np.testing.assert_allclose(Pn, Pn.T, atol=1e-15)


def test_eskf_stays_symmetric_psd_with_precise_beacons():
    """Stress: 5000 steps, beacon noise 1e-4 m against 1 m-scale P growth. Joseph form survives."""
    sec = M.SectionV(sigma_u=0.05, sigma_y=1e-4)
    rng = np.random.default_rng(13)
    Xs, us, ys = sec.simulate(5000, rng)
    X, P = np.eye(3), np.eye(3) * 1e-2
    for k in range(5000):
        X, P = ex.eskf_predict(X, P, us[k], sec.R_proc)
        for j, b in enumerate(sec.beacons):
            X, P, _, _ = ex.eskf_update(X, P, ys[k, j], b, sec.Q_meas)
    assert np.allclose(P, P.T, atol=1e-15)
    assert np.linalg.eigvalsh(P).min() > 0
    assert np.all(np.isfinite(X))


def run_eskf(sec, n, seed, reset=True):
    rng = np.random.default_rng(seed)
    Xs, us, ys = sec.simulate(n, rng)
    P = np.diag([0.01, 0.01, 0.01]) ** 2
    X = Xs[0] @ M.se2_Exp_ref(np.linalg.cholesky(P) @ rng.normal(size=3))
    nees, nis = [], []
    for k in range(n):
        X, P = ex.eskf_predict(X, P, us[k], sec.R_proc)
        for j, b in enumerate(sec.beacons):
            X, P, z, Z = ex.eskf_update(X, P, ys[k, j], b, sec.Q_meas, reset=reset)
            nis.append(z @ np.linalg.solve(Z, z))
        e = M.se2_rminus_ref(Xs[k + 1], X)                # true ⊖ estimate, in the tangent at X̂ (52)
        nees.append(e @ np.linalg.solve(P, e))
    return np.array(nees), np.array(nis)


def test_eskf_is_consistent_on_section_V():
    """Monte Carlo consistency on the §V setup (Bar-Shalom): M = 40 runs of 100 steps. ANEES must lie in the
    two-sided 99 % band of χ²(3·M)/M around 3 (per step, averaged over runs, then over steps) widened by 15 % for
    the first-order linearization, and ANIS near 2. A wrong F, G or H, a missing ⊕ on the update, or the
    covariance of the wrong tangent pushes ANEES far above the band."""
    sec = M.SectionV()
    Mruns, n = 40, 100
    runs = [run_eskf(sec, n, s) for s in range(Mruns)]
    nees = np.array([r[0] for r in runs])
    nis = np.concatenate([r[1] for r in runs])
    anees = nees.mean()
    lo, hi = chi2.ppf([0.005, 0.995], 3 * Mruns * n) / (Mruns * n)
    assert 0.85 * lo <= anees <= 1.15 * hi, f"ANEES {anees:.2f} outside [{0.85 * lo:.2f}, {1.15 * hi:.2f}]"
    assert 1.7 <= nis.mean() <= 2.3, f"ANIS {nis.mean():.2f}"
    frac = (nees > chi2.ppf(0.95, 3)).mean()
    assert frac < 0.10, f"NEES above its 95 % bound {100 * frac:.1f} % of the time"


# ---------------------------------------------------------------- T3.8 Gauss-Newton SAM on Fig. 12 (C9)


def _problem_args(p, poses=None, lmks=None):
    return (p["init_poses"] if poses is None else poses, p["init_lmks"] if lmks is None else lmks,
            p["prior"], p["P0"], p["motions"], p["beacons"], p["R_proc"], p["Q_meas"])


def test_sam_jacobian_matches_finite_differences():
    """The whole 19×15 J (107) against FD of r through the composite ⊕ (86): poses by X Exp(δ), beacons by b + δ."""
    p = M.fig12_problem(np.random.default_rng(20))
    poses, lmks = p["init_poses"], p["init_lmks"]
    r, J = ex.sam_linearize(*_problem_args(p))
    assert r.shape == (19,) and J.shape == (19, 15)
    def plus(x, d):
        P_, L_ = x
        return ([X @ M.se2_Exp_ref(d[3 * i:3 * i + 3]) for i, X in enumerate(P_)],
                [b + d[9 + 2 * k:11 + 2 * k] for k, b in enumerate(L_)])
    f = lambda x: ex.sam_linearize(*_problem_args(p, *x))[0]
    Jn = fd_right(f, (poses, lmks), plus, euclid_minus, 15)
    np.testing.assert_allclose(J, Jn, atol=1e-4 * np.abs(Jn).max())


def test_sam_residual_is_zero_at_truth_without_noise():
    p = M.fig12_problem(np.random.default_rng(21), noise=False)
    r, _ = ex.sam_linearize(*_problem_args(p, p["poses"], p["lmks"]))
    np.testing.assert_allclose(r, 0.0, atol=1e-9)


def test_sam_solve_recovers_truth_without_noise():
    p = M.fig12_problem(np.random.default_rng(22), noise=False)
    poses, lmks, iters, costs = ex.sam_solve(*_problem_args(p))
    assert iters <= 10, f"{iters} iterations"
    for X, Xt in zip(poses, p["poses"]):
        np.testing.assert_allclose(M.se2_rminus_ref(X, Xt), 0.0, atol=1e-8)
    for b, bt in zip(lmks, p["lmks"]):
        np.testing.assert_allclose(b, bt, atol=1e-8)
    assert costs[-1] < 1e-12


def test_sam_solve_with_noise_reaches_the_chi2_cost():
    """With noise, the final cost r·r is a χ² with 19 − 15 = 4 degrees of freedom. Over 30 problems its mean must be
    close to 4 (a wrong residual sign or a wrong whitening moves it by a factor)."""
    finals = []
    for s in range(30):
        p = M.fig12_problem(np.random.default_rng(100 + s))
        _, _, iters, costs = ex.sam_solve(*_problem_args(p))
        assert costs[-1] <= costs[0], "GN increased the cost"
        finals.append(costs[-1])
    m = np.mean(finals)
    assert 2.5 <= m <= 5.5, f"mean final cost {m:.2f}, expected about 4"
