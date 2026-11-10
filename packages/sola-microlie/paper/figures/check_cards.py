#!/usr/bin/env python3
"""Check the code in translate.md: run every python block, finite-difference every Jacobian, measure the
precision numbers the cards quote, and compile every cpp block against Eigen.

    python3 packages/sola-microlie/paper/figures/check_cards.py

Writes figures/card_numbers.json. Exits 1 if any check fails. The card code is executed from translate.md
itself, so the cards and the checked code cannot drift apart.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import mpmath as mp
import numpy as np
from scipy.linalg import expm, logm

PKG = Path(__file__).resolve().parents[1]
ROOT = PKG.parents[2]
sys.path.insert(0, str(ROOT))
from scripts.fd_check import (EUCLID, SE3_RIGHT, SO3_LEFT, SO3_RIGHT, Space,  # noqa: E402
                              check_jacobian_manifold)

mp.mp.dps = 50
text = (PKG / "translate.md").read_text(encoding="utf-8")
py_blocks = re.findall(r"```python\n(.*?)```", text, re.S)
cpp_blocks = re.findall(r"```cpp\n(.*?)```", text, re.S)
ns: dict = {}
exec(compile("\n".join(py_blocks), "translate.md", "exec"), ns)
S = __import__("types").SimpleNamespace(**ns)

rng = np.random.default_rng(0)
out: dict = {}
fails: list[str] = []
fd_worst: dict[str, float] = {}


def fd(name, f, J, x, retract, minus=None, dim=None):
    try:
        fd_worst[name] = float(check_jacobian_manifold(f, J, x, retract, minus, dim, rtol=1e-5, atol=1e-7))
    except Exception as e:  # noqa: BLE001
        fails.append(f"FD {name}: {e}")


def rand_rot(scale=1.0):
    return rng.normal(size=3) * scale


# independent SE(2) oracle space: scipy expm/logm on the 3x3 algebra
def se2_hat_ref(d):
    return np.array([[0, -d[2], d[0]], [d[2], 0, d[1]], [0, 0, 0.0]])


def se2_minus_ref(M1, M0):
    L = np.real(logm(np.linalg.solve(M0, M1)))
    return np.array([L[0, 2], L[1, 2], L[1, 0]])


SE2_RIGHT = Space(lambda M, d: M @ expm(se2_hat_ref(d)), se2_minus_ref, 3)
SE2_LEFT = Space(None, lambda M1, M0: se2_minus_ref(M1 @ np.linalg.inv(M0), np.eye(3)), 3)   # Log(M1 M0^-1)


def rel(a, b):
    return abs(float(a) - float(b)) / abs(float(b))


# ---------------------------------------------------------------- C1
ths = np.logspace(-12, np.log10(np.pi), 400)
a_ref = lambda t: (1 - mp.cos(t)) / t**2                     # noqa: E731
b_ref = lambda t: (t - mp.sin(t)) / t**3                     # noqa: E731
d_ref = lambda t: 1 / t**2 - (1 + mp.cos(t)) / (2 * t * mp.sin(t))   # noqa: E731
c_ref = lambda t: (1 - t**2 / 2 - mp.cos(t)) / t**4          # noqa: E731
e_ref = lambda t: (t - mp.sin(t) - t**3 / 6) / t**5          # noqa: E731
out["C1_coef_relerr"] = {
    "a": max(rel(S.coef_a(t), a_ref(mp.mpf(t))) for t in ths),
    "b": max(rel(S.coef_b(t), b_ref(mp.mpf(t))) for t in ths),
}

log_err = {}
for th in [1e-9, 1e-6, 1e-3, 1.0, np.pi - 1e-3, np.pi - 1e-7]:
    errs_n, errs_r = [], []
    for _ in range(20):
        u = rng.normal(size=3); u /= np.linalg.norm(u)
        theta = th * u
        R = S.so3_exp(theta)
        with np.errstate(all="ignore"):
            errs_n.append(float(np.linalg.norm(S.so3_log_naive(R) - theta)))
        errs_r.append(float(np.linalg.norm(S.so3_log(R) - theta)))
    log_err[f"{th:.17g}"] = {"naive": max(errs_n), "robust": max(errs_r)}
out["C1_log_error"] = log_err
# Exp agrees with expm and with the quaternion route
w_exp = max(float(np.abs(S.so3_exp(t) - expm(S.so3_hat(t))).max()) for t in [rand_rot() for _ in range(50)])
w_q = max(float(np.abs(S.quat_to_R(S.quat_exp(t)) - S.so3_exp(t)).max()) for t in [rand_rot() for _ in range(50)])
out["C1_exp_vs_expm"], out["C1_quat_vs_matrix"] = w_exp, w_q
if max(w_exp, w_q) > 1e-12:
    fails.append("C1 Exp disagrees with expm or the quaternion route")
if max(v["robust"] for v in log_err.values()) > 1e-9:
    fails.append("C1 robust Log error too large")

# ---------------------------------------------------------------- C2
groups = {"SO3": (S.SO3, lambda: S.so3_exp(rand_rot())),
          "SE2": (S.SE2, lambda: S.se2_exp(rng.normal(size=3))),
          "SE3": (S.SE3, lambda: S.se3_exp(rng.normal(size=6)))}
ad_err, eq32 = 0.0, 0.0
for name, (G, draw) in groups.items():
    for _ in range(20):
        X = draw(); tau = rng.normal(size=G.m) * 0.7
        ad_err = max(ad_err, float(np.abs(G.Ad(X) - S.adjoint_generic(X, G)).max()))
        eq32 = max(eq32, float(np.abs(S.rplus(X, tau, G) - S.lplus(G.Ad(X) @ tau, X, G)).max()))
        rt = S.rminus(S.rplus(X, tau, G), X, G)
        if np.abs(rt - tau).max() > 1e-9:
            fails.append(f"C2 {name} rminus(rplus) round trip")
out["C2_Ad_closed_vs_generic"], out["C2_eq32_residual"] = ad_err, eq32
if max(ad_err, eq32) > 1e-12:
    fails.append("C2 adjoint / (32)")

# ---------------------------------------------------------------- C3: SO(3) Jacobians and blocks (fd_check's own SO(3))
for k in range(8):
    th = rand_rot(1.0 if k < 6 else 3.0 / np.sqrt(3))
    fd(f"so3_Jr#{k}", S.so3_exp, S.so3_Jr, th, EUCLID, SO3_RIGHT)
    fd(f"so3_Jl#{k}", S.so3_exp, S.so3_Jl, th, EUCLID, SO3_LEFT)
    fd(f"so3_Jrinv#{k}", S.so3_log, lambda R: S.so3_Jrinv(S.so3_log(R)), S.so3_exp(th), SO3_RIGHT)
    X, Y = S.so3_exp(rand_rot()), S.so3_exp(rand_rot())
    v = rng.normal(size=3)
    fd(f"inv#{k}", lambda X: X.T, lambda X: S.J_inv(X, S.SO3), X, SO3_RIGHT, SO3_RIGHT)
    fd(f"compX#{k}", lambda X: X @ Y, lambda X: S.J_compose_X(X, Y, S.SO3), X, SO3_RIGHT, SO3_RIGHT)
    fd(f"compY#{k}", lambda Y: X @ Y, lambda Y: S.J_compose_Y(X, Y, S.SO3), Y, SO3_RIGHT, SO3_RIGHT)
    fd(f"rplusX#{k}", lambda X: S.rplus(X, v, S.SO3), lambda X: S.J_rplus_X(X, v, S.SO3), X, SO3_RIGHT, SO3_RIGHT)
    fd(f"rplusTau#{k}", lambda t: S.rplus(X, t, S.SO3), lambda t: S.J_rplus_tau(X, t, S.SO3), v, EUCLID, SO3_RIGHT)
    fd(f"rminusX#{k}", lambda X: S.rminus(Y, X, S.SO3), lambda X: S.J_rminus_X(Y, X, S.SO3), X, SO3_RIGHT)
    fd(f"rminusY#{k}", lambda Y: S.rminus(Y, X, S.SO3), lambda Y: S.J_rminus_Y(Y, X, S.SO3), Y, SO3_RIGHT)
    fd(f"log#{k}", S.so3_log, lambda X: S.J_log(X, S.SO3), X, SO3_RIGHT)
    fd(f"actR#{k}", lambda R: S.so3_act(R, v)[0], lambda R: S.so3_act(R, v)[1], X, SO3_RIGHT)
    fd(f"actV#{k}", lambda p: S.so3_act(X, p)[0], lambda p: S.so3_act(X, p)[2], v, EUCLID)
# identities (75) and (76) on SO(3)
for _ in range(10):
    t = rand_rot()
    if np.abs(S.SO3.Ad(S.so3_exp(t)) - S.so3_Jl(t) @ S.so3_Jrinv(t)).max() > 1e-12:
        fails.append("C3 (75)")
    if np.abs(S.so3_Jr(t) @ S.so3_Jrinv(t) - np.eye(3)).max() > 1e-12:
        fails.append("C3 Jr Jr^-1 = I")

ths_d = np.logspace(-8, np.log10(np.pi), 400)
out["C3_coef_d_relerr"] = max(rel(S.coef_d(t), d_ref(mp.mpf(t))) for t in ths_d)


def d_printed(t):
    return 1 / t**2 - (1 + np.cos(t)) / (2 * t * np.sin(t))


out["C3_coef_d_printed_relerr"] = {f"{t:.17g}": rel(d_printed(t), d_ref(mp.mpf(t)))
                                  for t in [1e-6, 1e-4, 1.0, np.pi - 1e-6]}
out["C3_coef_d_printed_at_pi"] = float(d_printed(np.pi))
out["C3_manif_coef_a_relerr"] = {f"{t:.17g}": rel((1 - np.cos(t)) / t**2, a_ref(mp.mpf(t)))
                                for t in [1.6e-7, 1e-6, 1e-4]}
out["C3_printed_Jr_abserr"] = {f"{t:.17g}": max(float(np.abs(S.so3_Jr_naive(t * u) - S.so3_Jr(t * u)).max())
                                                  for u in [v / np.linalg.norm(v) for v in rng.normal(size=(20, 3))])
                               for t in [1.6e-7, 1e-6]}
out["manif_eps"] = float(np.finfo(float).eps * 100)
out["manif_switch_theta"] = float(np.sqrt(np.finfo(float).eps * 100))

# ---------------------------------------------------------------- C4: SE(2) (scipy expm/logm oracle)
for k in range(8):
    tau = rng.normal(size=3)
    X, Y = S.se2_exp(rng.normal(size=3)), S.se2_exp(rng.normal(size=3))
    p = rng.normal(size=2)
    fd(f"se2_Jr#{k}", S.se2_exp, S.se2_Jr, tau, EUCLID, SE2_RIGHT)
    fd(f"se2_Jl#{k}", S.se2_exp, S.se2_Jl, tau, EUCLID, SE2_LEFT)
    fd(f"se2_Jrinv#{k}", S.se2_log, lambda M: S.se2_Jrinv(S.se2_log(M)), X, SE2_RIGHT)
    fd(f"se2_inv#{k}", S.se2_inv, lambda M: S.J_inv(M, S.SE2), X, SE2_RIGHT, SE2_RIGHT)
    fd(f"se2_compX#{k}", lambda M: M @ Y, lambda M: S.J_compose_X(M, Y, S.SE2), X, SE2_RIGHT, SE2_RIGHT)
    fd(f"se2_rminusX#{k}", lambda M: S.rminus(Y, M, S.SE2), lambda M: S.J_rminus_X(Y, M, S.SE2), X, SE2_RIGHT)
    fd(f"se2_rminusY#{k}", lambda M: S.rminus(M, X, S.SE2), lambda M: S.J_rminus_Y(M, X, S.SE2), Y, SE2_RIGHT)
    fd(f"se2_actM#{k}", lambda M: S.se2_act(M, p)[0], lambda M: S.se2_act(M, p)[1], X, SE2_RIGHT)
    fd(f"se2_actP#{k}", lambda q: S.se2_act(X, q)[0], lambda q: S.se2_act(X, q)[2], p, EUCLID)
    # beacon H of p. 12 against the chain (166) at X^-1 times (62)
    b = rng.normal(size=2) * 3
    _, JM, _ = S.se2_act(S.se2_inv(X), b)
    H_chain = JM @ S.J_inv(X, S.SE2)
    R, t = X[:2, :2], X[:2, 2]
    H_p12 = -np.hstack([np.eye(2), (R.T @ S.J1 @ (b - t))[:, None]])
    if np.abs(H_chain - H_p12).max() > 1e-12:
        fails.append("C4 H chain vs p.12")
    fd(f"C8_H#{k}", lambda M: S.se2_inv(M)[:2, :2] @ b + S.se2_inv(M)[:2, 2], lambda M: H_p12, X, SE2_RIGHT)
    # Exp/Log against expm/logm
    if np.abs(S.se2_exp(tau) - expm(se2_hat_ref(tau))).max() > 1e-12:
        fails.append("C4 se2_exp vs expm")
    if np.abs(S.se2_log(S.se2_exp(tau)) - tau).max() > 1e-9 and abs(tau[2]) < np.pi:
        fails.append("C4 se2_log round trip")
    if np.abs(S.se2_Jr(tau) - S.se2_Jr_naive(tau)).max() > 1e-12:
        fails.append("C4 robust Jr differs from printed (163) at ordinary theta")


def se2_col3_ref(rho, th):  # third column of (163) in mpmath
    r1, r2, t = mp.mpf(rho[0]), mp.mpf(rho[1]), mp.mpf(th)
    return np.array([float((t * r1 - r2 + r2 * mp.cos(t) - r1 * mp.sin(t)) / t**2),
                     float((r1 + t * r2 - r1 * mp.cos(t) - r2 * mp.sin(t)) / t**2)])


col3 = {}
for th in [2e-7, 1e-6, 1e-4]:
    en, er = 0.0, 0.0
    for _ in range(50):
        rho = rng.normal(size=2); rho /= np.linalg.norm(rho)
        ref = se2_col3_ref(rho, th)
        en = max(en, float(np.abs(S.se2_Jr_naive(np.r_[rho, th])[:2, 2] - ref).max()))
        er = max(er, float(np.abs(S.se2_Jr(np.r_[rho, th])[:2, 2] - ref).max()))
    col3[f"{th:.17g}"] = {"printed": en, "robust": er}
out["C4_Jr_col3_abserr"] = col3

# ---------------------------------------------------------------- C5: SE(3) (fd_check's own SE(3))
for k in range(8):
    tau = rng.normal(size=6)
    X, Y = S.se3_exp(rng.normal(size=6)), S.se3_exp(rng.normal(size=6))
    p = rng.normal(size=3)
    fd(f"se3_Jr#{k}", S.se3_exp, S.se3_Jr, tau, EUCLID, SE3_RIGHT)
    fd(f"se3_Jrinv#{k}", S.se3_log, lambda M: S.se3_Jrinv(S.se3_log(M)), X, SE3_RIGHT)
    fd(f"se3_inv#{k}", S.se3_inv, lambda M: S.J_inv(M, S.SE3), X, SE3_RIGHT, SE3_RIGHT)
    fd(f"se3_compX#{k}", lambda M: M @ Y, lambda M: S.J_compose_X(M, Y, S.SE3), X, SE3_RIGHT, SE3_RIGHT)
    fd(f"se3_actM#{k}", lambda M: S.se3_act(M, p)[0], lambda M: S.se3_act(M, p)[1], X, SE3_RIGHT)
    if np.abs(S.se3_exp(tau) - expm(S.se3_hat(tau))).max() > 1e-12:
        fails.append("C5 se3_exp vs expm")
    if np.abs(S.se3_Q(tau[:3], tau[3:]) - S.se3_Q_naive(tau[:3], tau[3:])).max() > 1e-12:
        fails.append("C5 robust Q differs from printed (180) at ordinary theta")
    if np.abs(S.se3_Jl(tau) @ S.se3_Jlinv(tau) - np.eye(6)).max() > 1e-12:
        fails.append("C5 (179b) is not the inverse of (179a)")
out["C5_coef_relerr"] = {
    "c": max(rel(S.coef_c(t), c_ref(mp.mpf(t))) for t in np.logspace(-8, np.log10(np.pi), 300)),
    "e": max(rel(S.coef_e(t), e_ref(mp.mpf(t))) for t in np.logspace(-8, np.log10(np.pi), 300)),
}


def Q_with(rho, theta, b, c, e):
    P, T = S.so3_hat(rho), S.so3_hat(theta)
    TP, PT, TPT = T @ P, P @ T, T @ P @ T
    return 0.5 * P + b * (TP + PT + TPT) - c * (T @ TP + PT @ T - 3 * TPT) - 0.5 * (c - 3 * e) * (TPT @ T + T @ TPT)


qerr = {}
for th in [1e-6, 1e-4, 1e-2, 1e-1]:
    en, er = 0.0, 0.0
    for _ in range(30):
        u = rng.normal(size=3); u /= np.linalg.norm(u)
        rho = rng.normal(size=3); rho /= np.linalg.norm(rho)
        tm = mp.mpf(th)
        ref = Q_with(rho, th * u, float(b_ref(tm)), float(c_ref(tm)), float(e_ref(tm)))
        with np.errstate(all="ignore"):
            en = max(en, float(np.abs(S.se3_Q_naive(rho, th * u) - ref).max()))
        er = max(er, float(np.abs(S.se3_Q(rho, th * u) - ref).max()))
    qerr[f"{th:.17g}"] = {"printed": en, "robust": er}
out["C5_Q_abserr"] = qerr

# ---------------------------------------------------------------- C6: Monte Carlo for (55)
X, Y = S.se2_exp(np.array([1.0, 0.5, 0.4])), S.se2_exp(np.array([0.8, -0.3, -0.7]))
Sx = np.diag([0.1, 0.1, 0.1]) ** 2
Sy = np.diag([0.1, 0.1, 0.1]) ** 2
Z, Sz = S.compose_with_cov(X, Sx, Y, Sy, S.SE2)
N = 200_000
ex = rng.multivariate_normal(np.zeros(3), Sx, N)
ey = rng.multivariate_normal(np.zeros(3), Sy, N)
dz = np.array([S.rminus((X @ S.se2_exp(a)) @ (Y @ S.se2_exp(b)), Z, S.SE2) for a, b in zip(ex, ey)])
Smc = np.cov(dz.T)
out["C6_mc_relerr"] = float(np.linalg.norm(Smc - Sz) / np.linalg.norm(Smc))
out["C6_mc_samples"] = N
q = S.quat_integrate(np.array([1.0, 0, 0, 0]), [rng.normal(size=3) for _ in range(1000)], 0.01)
out["C6_quat_norm_err"] = float(abs(np.linalg.norm(q) - 1))

# ---------------------------------------------------------------- C7
groups7 = [S.SE2, S.SE2, S.RN]
dims7 = [3, 3, 2]
rt = 0.0
for _ in range(50):
    Xs = [S.se2_exp(rng.normal(size=3)), S.se2_exp(rng.normal(size=3)), rng.normal(size=2)]
    tau = rng.normal(size=8) * 0.5
    rt = max(rt, float(np.abs(S.diamond_minus(S.diamond_plus(Xs, tau, groups7, dims7), Xs, groups7, dims7) - tau).max()))
out["C7_roundtrip"] = rt
if rt > 1e-12:
    fails.append("C7 round trip")

# ---------------------------------------------------------------- C8: reset Jacobian and filter sanity
for k in range(6):
    dx = rng.normal(size=3) * 0.3
    fd(f"C8_reset#{k}", lambda e: S.se2_log(S.se2_inv(S.se2_exp(dx)) @ S.se2_exp(e)), S.se2_Jr, dx, EUCLID)
for k in range(4):
    u = rng.normal(size=3) * 0.2
    fd(f"C8_F#{k}", lambda M: M @ S.se2_exp(u), lambda M: S.se2_Ad(S.se2_exp(-u)), S.se2_exp(rng.normal(size=3)),
       SE2_RIGHT, SE2_RIGHT)
    Xn, Pn = S.eskf_predict_naive(np.eye(3), np.eye(3) * 0.01, u, np.eye(3) * 1e-3)
    Xr, Pr = S.eskf_predict(np.eye(3), np.eye(3) * 0.01, u, np.eye(3) * 1e-3)
    if np.abs(Pn - Pr).max() > 1e-12:
        fails.append("C8 robust predict differs from naive")
    Xn2, Pn2 = S.eskf_update_naive(Xr, Pr, np.array([2.0, 0.1]), np.array([2.0, 0.5]), np.eye(2) * 1e-2)
    Xr2, Pr2 = S.eskf_update(Xr, Pr, np.array([2.0, 0.1]), np.array([2.0, 0.5]), np.eye(2) * 1e-2, reset=False)
    if np.abs(Pn2 - Pr2).max() > 1e-12 or np.abs(Xn2 - Xr2).max() > 1e-12:
        fails.append("C8 robust update (no reset) differs from naive")

# ---------------------------------------------------------------- C9: GN SAM on the paper's graph
true_poses = [S.se2_exp(np.array([0.0, 0.0, 0.0]))]
u_true = [np.array([1.0, 0.0, 0.3]), np.array([1.0, 0.0, 0.3])]
for u in u_true:
    true_poses.append(true_poses[-1] @ S.se2_exp(u))
true_lmks = [np.array([1.0, -1.0]), np.array([1.5, 1.5]), np.array([2.8, 1.0])]
pairs = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)]          # 14, 15, 25, 26, 36 (beacons 4, 5, 6 -> 0, 1, 2)
R_proc = np.diag([0.05, 0.05, 0.02]) ** 2
Q_meas = np.diag([0.05, 0.05]) ** 2
P0 = np.eye(3) * 1e-4
motions = [(0, 1, u_true[0] + rng.multivariate_normal(np.zeros(3), R_proc)),
           (1, 2, u_true[1] + rng.multivariate_normal(np.zeros(3), R_proc))]
beacons = [(i, k, S.se2_inv(true_poses[i])[:2, :2] @ true_lmks[k] + S.se2_inv(true_poses[i])[:2, 2]
            + rng.multivariate_normal(np.zeros(2), Q_meas)) for i, k in pairs]
init_p = [X @ S.se2_exp(np.r_[rng.normal(size=2) * 0.1, rng.normal() * 0.1]) for X in true_poses]
init_l = [b + rng.normal(size=2) * 0.1 for b in true_lmks]
args = (np.eye(3), motions, beacons, R_proc, Q_meas, P0)
r0, J0 = S.sam_linearize(init_p, init_l, *args)
out["C9_J_shape"] = list(J0.shape)


def r_of(state):
    ps = [state[0], state[1], state[2]]
    ls = [state[3], state[4], state[5]]
    return S.sam_linearize(ps, ls, *args)[0]


def retract_state(state, d):
    return S.diamond_plus(state, d, [S.SE2] * 3 + [S.RN] * 3, [3] * 3 + [2] * 3)


fd("C9_J", r_of, lambda st: S.sam_linearize(st[:3], st[3:], *args)[1], init_p + init_l, retract_state, dim=15)
ps, ls, iters = S.sam_solve(init_p, init_l, *args)
r1, _ = S.sam_linearize(ps, ls, *args)
out["C9_iterations"] = iters
out["C9_cost_init_final"] = [float(r0 @ r0), float(r1 @ r1)]
out["C9_pose_err_m"] = float(max(np.linalg.norm(a[:2, 2] - b[:2, 2]) for a, b in zip(ps, true_poses)))
if iters >= 20 or r1 @ r1 > r0 @ r0:
    fails.append("C9 GN did not converge")
# self-calibration column (111): r = Ω^{T/2}(c(ũ, c) - d), c(ũ, c) = ũ - [c_v, 0, c_ω]
Su = S.sqrt_info(R_proc)
d = rng.normal(size=3); ut = rng.normal(size=3)
fd("C9_calib", lambda c: Su @ (ut - np.array([c[0], 0.0, c[1]]) - d), lambda c: S.calib_jacobian(Su),
   rng.normal(size=2), EUCLID)

out["sin_pi_float64"] = float(np.sin(np.pi))
from scipy.stats import chi2  # noqa: E402
out["chi2_99_2dof"] = float(chi2.ppf(0.99, 2))


# ---------------------------------------------------------------- manif's se2_localization setup, ANEES
def eskf_anees(noise, reset, runs=200, steps=100, su_scale=1.0):
    u_nom = np.array([0.1, 0.0, 0.05]); su = np.array([0.1, 0.1, 0.1]) * su_scale; sy = np.array([0.01, 0.01])
    U, Rm = np.diag(su ** 2), np.diag(sy ** 2)
    lm = [np.array([2.0, 0.0]), np.array([2.0, 1.0]), np.array([2.0, -1.0])]
    nees = []
    for _ in range(runs):
        Xs, X, P = np.eye(3), np.eye(3), np.zeros((3, 3))
        for _ in range(steps):
            n_u = su * (rng.uniform(-1, 1, 3) if noise == "uniform" else rng.normal(size=3))
            Xs = Xs @ S.se2_exp(u_nom)                       # simulation moves with u_nom, as in the example
            X, P = S.eskf_predict(X, P, u_nom + n_u, U)      # the filter gets the noisy control
            for b in lm:
                n_y = sy * (rng.uniform(-1, 1, 2) if noise == "uniform" else rng.normal(size=2))
                y = S.se2_inv(Xs)[:2, :2] @ b + S.se2_inv(Xs)[:2, 2] + n_y
                X, P = S.eskf_update(X, P, y, b, Rm, reset=reset)
            e = S.rminus(Xs, X, S.SE2)
            nees.append(float(e @ np.linalg.solve(P, e)))
    return float(np.mean(nees))


out["IMPL_anees"] = {"gaussian": eskf_anees("gaussian", True), "uniform": eskf_anees("uniform", True),
                     "gaussian_no_reset": eskf_anees("gaussian", False),
                     "gaussian_su_0.01": eskf_anees("gaussian", True, su_scale=0.1),
                     "uniform_su_0.01": eskf_anees("uniform", True, su_scale=0.1), "runs": 200, "steps": 100, "dof": 3}
out["fd_worst_abs"] = max(fd_worst.values())
out["fd_checks"] = len(fd_worst)

# ---------------------------------------------------------------- C++ blocks
src = "#include <Eigen/Dense>\n#include <cmath>\n" + "\n".join(cpp_blocks) + "\nint main() { return 0; }\n"
with tempfile.TemporaryDirectory() as tmp:
    f = Path(tmp) / "cards.cpp"
    f.write_text(src)
    res = subprocess.run(["g++", "-std=c++17", "-fsyntax-only", "-I/usr/include/eigen3", str(f)],
                         capture_output=True, text=True)
    out["cpp_compiles"] = res.returncode == 0
    if res.returncode != 0:
        fails.append("C++ blocks do not compile:\n" + res.stderr[:3000])

(PKG / "figures" / "card_numbers.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
print(f"{len(fd_worst)} FD checks, worst {out['fd_worst_abs']:.2e}")
for f_ in fails:
    print("FAIL:", f_)
print("VERDICT:", "ok" if not fails else "fix")
sys.exit(1 if fails else 0)
