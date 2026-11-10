"""Generate the lecture figures for Solà, Deray & Atchuthan, "A micro Lie theory" in the Chalk style.

Run from anywhere:
    python3 packages/sola-microlie/paper/figures/make_figures.py

Writes L<n>-<slug>.svg/.png and numbers.json (every number quoted in lecture.md).

On purpose this script does NOT contain the closed forms Aun implements in the exercises (Rodrigues,
V(θ), J_r, J_l, the Ad closed forms). Exp and Log are scipy's expm/logm on the hat matrix, the adjoint is
the generic definition (31) applied column by column, and every Jacobian is a central finite
difference of the definition (41a). These are the oracles, not the solutions.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.linalg import expm, logm
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch  # noqa: E402

from viz.py import style  # noqa: E402

OUT = Path(__file__).resolve().parent
P = style.use("light")
R = style.ROLE
rng = np.random.default_rng(7)
NUM: dict = {}


def save(fig, name):
    fig.savefig(OUT / f"{name}.svg")
    fig.savefig(OUT / f"{name}.png", format="png", dpi=110)
    plt.close(fig)


# ------------------------------------------------------------------ generic matrix-Lie-group plumbing
# SE(2): tau = (rho_x, rho_y, theta), tau^ = [[ [theta]x, rho ], [0, 0]]  (153)
def hat(t):
    return np.array([[0.0, -t[2], t[0]], [t[2], 0.0, t[1]], [0.0, 0.0, 0.0]])


def vee(M):
    return np.array([M[0, 2], M[1, 2], M[1, 0]])


def Exp(t):  # (23) via the matrix exponential (16)
    return expm(hat(t))


def Log(M):  # (24) via the matrix logarithm, principal branch
    return vee(np.real(logm(M)))


def inv(X):
    return np.linalg.inv(X)


def pose(x, y, th):
    c, s = np.cos(th), np.sin(th)
    return np.array([[c, -s, x], [s, c, y], [0, 0, 1.0]])


def act(X, p):  # X . p = R p + t
    return X[:2, :2] @ p + X[:2, 2]


def Ad_generic(X, hatf=hat, veef=vee, m=3):  # (31): Ad_X tau = (X tau^ X^-1)^v, column by column
    return np.column_stack([veef(X @ hatf(e) @ inv(X)) for e in np.eye(m)])


def jac(f, X, plus, minus, m, h=1e-6):
    """Right Jacobian (41a) by central differences: columns (f(X (+) h e_i) (-) f(X)) / h."""
    fX = f(X)
    cols = []
    for e in np.eye(m):
        a = minus(f(plus(X, h * e)), fX)
        b = minus(f(plus(X, -h * e)), fX)
        cols.append((a - b) / (2 * h))
    return np.column_stack(cols)


rplus = lambda X, t: X @ Exp(t)          # (25)
rminus = lambda Y, X: Log(inv(X) @ Y)     # (26)
vplus = lambda x, t: x + t                # (186)
vminus = lambda y, x: y - x               # (187)


def frame(ax, X, L=0.45, label=None, alpha=1.0, lw=1.6):
    o = X[:2, 2]
    for i, col in enumerate([R["coral"], R["teal"]]):
        d = X[:2, i] * L
        ax.plot([o[0], o[0] + d[0]], [o[1], o[1] + d[1]], color=col, lw=lw, alpha=alpha, solid_capstyle="round")
    ax.plot(*o, "o", color=P["ink"], ms=2.5, alpha=alpha)
    if label:
        ax.text(o[0] - 0.08, o[1] - 0.22, label, color=P["ink"], fontsize=9, ha="right", va="top")


def heat(ax, M, title, vmax=None, fmt="{:+.2f}"):
    vmax = 1.8 * (vmax or max(1e-9, np.abs(M).max()))
    ax.imshow(M, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    for (i, j), v in np.ndenumerate(M):
        v = 0.0 if abs(v) < 5e-3 else v
        ax.text(j, i, fmt.format(v).replace("-", "−"), ha="center", va="center", fontsize=7.5,
                color=P["ink"], family="monospace")
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    ax.set_title(title, fontsize=11, color=P["ink"], loc="left")
    for s in ax.spines.values():
        s.set_visible(False)


# ===================================================================================== L1  II-A
fig, ax = plt.subplots(figsize=(5.4, 4.4))
th = np.linspace(0, 2 * np.pi, 400)
ax.plot(np.cos(th), np.sin(th), color=R["blue"], lw=1.8)
a1, a2 = 0.7, 1.1
ax.text(0.93, -0.1, "ℰ = 1", color=P["ink"], fontsize=10, ha="right", va="top")
for ang, lab, col in [(0, "", P["ink"]), (a1, "z₁", R["gray"]), (a2, "z₂", R["gray"]), (a1 + a2, "z₁z₂", R["coral"])]:
    ax.plot(np.cos(ang), np.sin(ang), "o", color=col, ms=5)
    ax.text(1.1 * np.cos(ang), 1.1 * np.sin(ang), lab, color=col, fontsize=10, ha="center", va="center")
s = np.linspace(-1.1, 1.1, 2)
ax.plot([1, 1], s, color=R["teal"], lw=1.6)
ax.text(1.04, -1.05, "T_ℰS¹ = iℝ\n(Lie algebra)", color=R["teal"], fontsize=9)
for ang in [a1 + a2]:
    c, sn = np.cos(ang), np.sin(ang)
    ax.plot(c - sn * s, sn + c * s, color=R["teal"], lw=1.0, ls="--")
    ax.text(c - sn * 1.15 - 0.1, sn + c * 1.15, "T_zS¹", color=R["teal"], fontsize=9, ha="right")
ang = np.linspace(0, a1, 50); ax.plot(0.32 * np.cos(ang), 0.32 * np.sin(ang), color=R["gray"], lw=1)
ang = np.linspace(a1, a1 + a2, 50); ax.plot(0.45 * np.cos(ang), 0.45 * np.sin(ang), color=R["gray"], lw=1)
ax.text(0.36, 0.12, "θ₁", fontsize=9, color=P["muted"]); ax.text(0.05, 0.5, "θ₂", fontsize=9, color=P["muted"])
ax.set_aspect("equal"); ax.set_xlim(-1.5, 2.0); ax.set_ylim(-1.35, 1.45)
ax.set_xlabel("Re z"); ax.set_ylabel("Im z")
style.fig_label(ax, "Fig L1 · Ex. 1, Fig. 3", "S¹: composing moves along the circle; every tangent line is alike")
save(fig, "L1-group-s1")

# ===================================================================================== L2  II-B
outline = np.array([[0.35, 0], [-0.2, 0.18], [-0.2, -0.18], [0.35, 0]])  # a robot-shaped triangle (points v)
X = pose(2.2, 1.0, np.deg2rad(50)); Y = pose(1.0, -0.4, np.deg2rad(-35))
Yv = np.array([act(Y, p) for p in outline])
XYv = np.array([act(X, p) for p in Yv])
XY_v = np.array([act(X @ Y, p) for p in outline])
NUM["L2_compat_residual"] = float(np.abs(XYv - XY_v).max())
fig, ax = plt.subplots(figsize=(5.6, 4.0))
ax.fill(outline[:, 0], outline[:, 1], color=R["gray"], alpha=0.35, lw=0); ax.text(-0.25, -0.45, "v", color=P["muted"])
ax.fill(Yv[:, 0], Yv[:, 1], color=R["blue"], alpha=0.35, lw=0); ax.text(*(Yv[1] + [-0.35, 0.0]), "Y·v", color=R["blue"])
ax.plot(XYv[:, 0], XYv[:, 1], color=R["teal"], lw=1.8, label="X·(Y·v)")
ax.plot(XY_v[:, 0], XY_v[:, 1], color=R["coral"], lw=1.2, ls="--", label="(X∘Y)·v")
frame(ax, np.eye(3), label="ℰ"); frame(ax, X, label="X"); frame(ax, X @ Y, label="X∘Y")
ax.text(0.0, 2.6, f"max |X·(Y·v) − (X∘Y)·v| = {NUM['L2_compat_residual']:.1e} m", fontsize=8.5, color=P["muted"], family="monospace")
ax.legend(loc="lower right"); ax.set_aspect("equal"); ax.set_xlim(-0.8, 4.4); ax.set_ylim(-0.8, 2.9)
ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
style.fig_label(ax, "Fig L2 · (5)–(7)", "Acting twice equals acting once with the composition (7)")
save(fig, "L2-group-action")

# ===================================================================================== L3  II-C
w = 1.0
tt = np.linspace(0, 2 * np.pi / w, 300)
z = np.exp(1j * w * tt)
zdot = 1j * w * z
vloc = np.conj(z) * zdot
fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8), gridspec_kw=dict(width_ratios=[1, 1.35]))
ax = axes[0]
ax.plot(z.real, z.imag, color=R["blue"], lw=1.6)
for k in np.linspace(0, 2 * np.pi, 8, endpoint=False):
    zk = np.exp(1j * k); dz = 1j * w * zk * 0.45
    ax.add_patch(FancyArrowPatch((zk.real, zk.imag), (zk.real + dz.real, zk.imag + dz.imag), arrowstyle="-|>", mutation_scale=9, color=R["coral"], lw=1.3))
ax.add_patch(FancyArrowPatch((1, 0), (1, 0.45), arrowstyle="-|>", mutation_scale=9, color=R["teal"], lw=2.0))
ax.text(1.08, 0.5, "ᴱv^ = iω", color=R["teal"], fontsize=9)
ax.set_aspect("equal"); ax.set_xlim(-1.7, 1.9); ax.set_ylim(-1.6, 1.6)
ax.set_title("ż = z·iω at eight points of the circle", loc="left", fontsize=10, color=P["ink"])
ax = axes[1]
ax.plot(tt, zdot.real, color=R["coral"], lw=1.4, label="global ż: Re")
ax.plot(tt, zdot.imag, color=R["coral"], lw=1.4, ls="--", label="global ż: Im")
ax.plot(tt, vloc.imag, color=R["teal"], lw=2.0, label="local ᶻv^ = z*ż  (imag. part)")
ax.plot(tt, vloc.real, color=R["teal"], lw=1.0, ls=":", label="local: real part")
ax.set_xlabel("t [s]  (ω = 1 rad/s)"); ax.set_ylabel("velocity component [1/s]"); ax.legend(fontsize=7.5, loc="lower left", ncol=2)
ax.set_ylim(-1.6, 1.4)
NUM["L3_local_velocity_spread"] = float(np.ptp(vloc.imag) + np.ptp(vloc.real))
fig.suptitle("Fig L3 · Fig. 5, (9)  Spinning at constant ω: the local velocity z⁻¹ż is constant, the global ż rotates",
             x=0.01, ha="left", fontsize=11, color=P["ink"])
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "L3-tangent-velocity")

# ===================================================================================== L4  II-D
def hat3(w):
    return np.array([[0, -w[2], w[1]], [w[2], 0, -w[0]], [-w[1], w[0], 0.0]])


u = np.array([1.0, 2.0, 2.0]) / 3.0
fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.6))
ax = axes[0]
NUM["L4_terms_for_1e-12"] = {}
for thv, col in [(0.5, R["blue"]), (1.5, R["teal"]), (3.0, R["coral"])]:
    A = hat3(thv * u); ref = expm(A)
    S = np.eye(3); term = np.eye(3); errs = []
    for k in range(1, 31):
        term = term @ A / k; S = S + term
        errs.append(np.linalg.norm(S - ref))
    errs = np.maximum(np.array(errs), 1e-17)
    ax.semilogy(range(1, 31), errs, "o-", ms=3, color=col, label=f"θ = {thv} rad")
    NUM["L4_terms_for_1e-12"][str(thv)] = int(np.argmax(errs < 1e-12) + 1)
ax.axhline(1e-12, color=P["grid"], ls=":", lw=1)
ax.set_xlabel("highest power k kept in (16)"); ax.set_ylabel("‖series − expm‖_F"); ax.legend()
ax.set_title("SO(3): series (16) vs expm", loc="left", fontsize=10, color=P["ink"])
ax = axes[1]
ths = np.linspace(-2 * np.pi + 0.02, 2 * np.pi - 0.02, 801)
logs = []
for a in ths:
    M = expm(np.array([[0, -a], [a, 0.0]]))
    logs.append(np.real(logm(M))[1, 0])
logs = np.array(logs)
ax.plot(ths, ths, color=R["gray"], lw=1, ls="--", label="θ (the input)")
ax.plot(ths, logs, ".", ms=1.6, color=R["teal"], label="Log(Exp(θ))")
ax.axvspan(-np.pi, np.pi, color=R["teal"], alpha=0.06)
ax.set_xlabel("θ [rad]"); ax.set_ylabel("[rad]"); ax.legend(loc="upper left")
ax.set_title("SO(2): Log(Exp(θ)) = θ only on (−π, π]", loc="left", fontsize=10, color=P["ink"])
NUM["L4_log_jump_at"] = float(ths[np.argmax(np.abs(np.diff(logs)) > 1) + 1])
fig.suptitle("Fig L4 · (14)–(24), Ex. 4  Exp is a convergent series; Log returns the principal angle",
             x=0.01, ha="left", fontsize=11, color=P["ink"])
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "L4-exp-log")

# ===================================================================================== L5  II-E
X = pose(1.5, 1.0, np.deg2rad(60))
tau = np.array([1.2, 0.0, 0.9])
ss = np.linspace(0, 1, 60)
right = np.array([(X @ Exp(s * tau))[:2, 2] for s in ss])
left = np.array([(Exp(s * tau) @ X)[:2, 2] for s in ss])
fig, ax = plt.subplots(figsize=(5.6, 5.0))
ax.plot(right[:, 0], right[:, 1], color=R["teal"], lw=1.8, label="right-⊕: X∘Exp(sτ)  (local)")
ax.plot(left[:, 0], left[:, 1], color=R["coral"], lw=1.8, ls="--", label="left-⊕: Exp(sτ)∘X  (global)")
frame(ax, np.eye(3), label="ℰ"); frame(ax, X, label="X")
frame(ax, X @ Exp(tau), label="X⊕τ"); frame(ax, Exp(tau) @ X, label="τ⊕X")
ax.text(-0.6, 3.3, "τ = (ρx, ρy, θ) = (1.2 m, 0 m, 0.9 rad)", fontsize=8.5, color=P["muted"], family="monospace")
ax.legend(loc="lower right", fontsize=8); ax.set_aspect("equal"); ax.set_xlim(-0.6, 3.0); ax.set_ylim(-0.6, 3.5)
ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
NUM["L5_gap_m"] = float(np.linalg.norm(right[-1] - left[-1]))
style.fig_label(ax, "Fig L5 · (25)–(28), Fig. 7", "Same τ, two poses: right-⊕ is local, left-⊕ is global")
save(fig, "L5-plus-right-left")

# ===================================================================================== L6  II-F
AdX = Ad_generic(X)
tauE = AdX @ tau
loc = np.array([(X @ Exp(s * tau))[:2, 2] for s in ss])
glo = np.array([(Exp(s * tauE) @ X)[:2, 2] for s in ss])
res = max(np.linalg.norm(Log(inv(X @ Exp(s * tau)) @ Exp(s * tauE) @ X)) for s in ss)
NUM["L6_tauE"] = [round(float(v), 3) for v in tauE]
NUM["L6_residual"] = float(res)
fig, ax = plt.subplots(figsize=(5.6, 5.0))
ax.plot(loc[:, 0], loc[:, 1], color=R["teal"], lw=4, alpha=0.45, label="X ⊕ sˣτ")
ax.plot(glo[:, 0], glo[:, 1], color=R["blue"], lw=1.4, ls="--", label="s(Ad_X ˣτ) ⊕ X")
ax.plot(left[:, 0], left[:, 1], color=R["gray"], lw=1.0, ls=":", label="sˣτ ⊕ X  (no Ad: wrong)")
frame(ax, np.eye(3), label="ℰ"); frame(ax, X, label="X"); frame(ax, X @ Exp(tau), label="")
ax.text(-0.6, 3.3, "ˣτ = (1.20, 0.00, 0.90)\nᴱτ = Ad_X ˣτ = ({:.2f}, {:.2f}, {:.2f})".format(*tauE).replace("-", "−")
        + f"\nmax ‖gap‖ over s = {res:.1e}", fontsize=8.5, color=P["muted"], family="monospace", va="top")
ax.legend(loc="lower right", fontsize=8); ax.set_aspect("equal"); ax.set_xlim(-0.6, 3.0); ax.set_ylim(-0.6, 3.5)
ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
style.fig_label(ax, "Fig L6 · (30)–(32)", "Ad_X maps the local ˣτ to the global ᴱτ that reaches the same pose")
save(fig, "L6-adjoint")

# ===================================================================================== L7  II-G
b = np.array([3.0, 2.0])
f_meas = lambda X: act(inv(X), b)  # y = X^-1 . b  (95)
X0 = pose(1.0, 0.5, np.deg2rad(30))
J = jac(f_meas, X0, rplus, vminus, 3)
fig, ax = plt.subplots(figsize=(5.6, 4.0))
hs = np.logspace(-4, 0, 30)
slopes = []
for k in range(6):
    d = rng.normal(size=3); d /= np.linalg.norm(d)
    e = [np.linalg.norm(f_meas(rplus(X0, h * d)) - (f_meas(X0) + J @ (h * d))) for h in hs]
    ax.loglog(hs, e, color=R["teal"], lw=1.2, alpha=0.8)
    slopes.append(np.polyfit(np.log(hs[5:20]), np.log(e[5:20]), 1)[0])
ax.loglog(hs, 0.5 * hs**2, color=R["gray"], ls="--", lw=1, label="slope 2 reference")
ax.loglog(hs, 0.5 * hs, color=R["gray"], ls=":", lw=1, label="slope 1 (what a wrong J gives)")
ax.set_xlabel("‖τ‖  (six random directions)"); ax.set_ylabel("‖f(X⊕τ) − f(X) − Jτ‖ [m]"); ax.legend(loc="upper left")
NUM["L7_slopes"] = [round(float(s), 3) for s in slopes]
style.fig_label(ax, "Fig L7 · (41a), (43)", "With the right J, what is left over falls as ‖τ‖²")
save(fig, "L7-right-jacobian")

# ===================================================================================== L8  II-H
Xbar = pose(0.0, 0.0, 0.0)
Sig = np.diag([0.10**2, 0.10**2, 0.25**2])
pfwd = np.array([3.0, 0.0])
f_ahead = lambda X: act(X, pfwd)
N = 4000
taus = rng.multivariate_normal(np.zeros(3), Sig, N)
pts = np.array([f_ahead(rplus(Xbar, t)) for t in taus])
Jf = jac(f_ahead, Xbar, rplus, vminus, 3)
Slin = Jf @ Sig @ Jf.T
mlin = f_ahead(Xbar)
d = pts - mlin
m2 = np.einsum("ij,jk,ik->i", d, np.linalg.inv(Slin), d)
NUM["L8_inside_2sigma"] = float(np.mean(m2 < 4.0))
NUM["L8_expected_2sigma"] = float(chi2.cdf(4.0, 2))
NUM["L8_mc_mean_x"] = float(pts[:, 0].mean())
fig, ax = plt.subplots(figsize=(6.0, 5.0))
ax.scatter(pts[:, 0], pts[:, 1], s=3, color=R["gray"], alpha=0.25, lw=0, label="Monte Carlo: (X̄⊕τ)·p")
style.cov_ellipse(ax, mlin, Slin, n_std=2, role="blue", fill_alpha=0.08)
style.cov_ellipse(ax, pts.mean(0), np.cov(pts.T), n_std=2, role="teal", fill_alpha=0.0, ls="--")
ax.plot(*mlin, "o", color=R["blue"], ms=4); ax.plot(*pts.mean(0), "x", color=R["teal"], ms=6, mew=1.6)
frame(ax, Xbar, label="X̄")
ax.plot([], [], color=R["blue"], label="(55): J Σ Jᵀ, 2σ"); ax.plot([], [], color=R["teal"], ls="--", label="sample covariance, 2σ")
ax.text(-0.6, -1.95, f"inside the (55) 2σ ellipse: {100 * NUM['L8_inside_2sigma']:.1f} %  (Gaussian: {100 * NUM['L8_expected_2sigma']:.1f} %)",
        fontsize=8.5, color=P["muted"], family="monospace")
ax.legend(loc="upper left", fontsize=8); ax.set_aspect("equal"); ax.set_xlim(-0.7, 4.0); ax.set_ylim(-2.1, 2.2)
ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
style.fig_label(ax, "Fig L8 · (51)–(55), Fig. 10", "Tangent Gaussian seen 3 m ahead: a banana (55) only approximates")
save(fig, "L8-tangent-covariance")

# ===================================================================================== L9  II-I
v, om, T = 1.0, 0.5, 9.0
fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.9), gridspec_kw=dict(width_ratios=[1.1, 1]))
ax = axes[0]
c = np.linspace(0, 2 * np.pi, 300)
ax.plot(2 * np.sin(c), 2 - 2 * np.cos(c), color=R["gray"], lw=1, ls="--", label="truth: circle r = v/ω = 2 m")
errsE, errsL = [], []
dts = [1.5, 1.0, 0.5, 0.25, 0.1, 0.05]
for dt in dts:
    n = int(round(T / dt))
    Xk = np.eye(3); e = np.zeros(3); trL = [Xk[:2, 2]]; trE = [e[:2].copy()]
    for _ in range(n):
        Xk = Xk @ Exp(np.array([v * dt, 0, om * dt]))              # (56)
        e = e + dt * np.array([v * np.cos(e[2]), v * np.sin(e[2]), om])  # Euler on (x, y, θ)
        trL.append(Xk[:2, 2]); trE.append(e[:2].copy())
    truth = np.array([2 * np.sin(om * n * dt), 2 - 2 * np.cos(om * n * dt)])
    errsL.append(np.linalg.norm(trL[-1] - truth)); errsE.append(np.linalg.norm(trE[-1] - truth))
    if dt == 1.5:
        trL, trE = np.array(trL), np.array(trE)
        ax.plot(trL[:, 0], trL[:, 1], "o-", ms=4, color=R["teal"], lw=1.4, label="Xₖ = Xₖ₋₁ Exp(u δt)  (56)")
        ax.plot(trE[:, 0], trE[:, 1], "s-", ms=3.5, color=R["coral"], lw=1.2, label="Euler on (x, y, θ)")
ax.set_aspect("equal"); ax.legend(loc="lower left", fontsize=7.5, bbox_to_anchor=(0, -0.02)); ax.set_xlim(-3.2, 3.4); ax.set_ylim(-1.9, 4.6)
ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_title("δt = 1.5 s, v = 1 m/s, ω = 0.5 rad/s", loc="left", fontsize=10, color=P["ink"])
ax = axes[1]
ax.loglog(dts, np.maximum(errsL, 1e-16), "o-", color=R["teal"], label="Exp (56)")
ax.loglog(dts, errsE, "s-", color=R["coral"], label="Euler")
ax.set_xlabel("δt [s]"); ax.set_ylabel("end-point error after 9 s [m]"); ax.legend()
ax.set_title("constant twist: Exp is exact at any δt", loc="left", fontsize=10, color=P["ink"])
NUM["L9_err_exp_dt1.5"] = float(errsL[0]); NUM["L9_err_euler_dt1.5"] = float(errsE[0]); NUM["L9_err_euler_dt0.1"] = float(errsE[4])
fig.suptitle("Fig L9 · (56), Fig. 11  Integrating a constant twist with Exp stays on the circle; Euler on (x, y, θ) does not",
             x=0.01, ha="left", fontsize=11, color=P["ink"])
fig.tight_layout()
save(fig, "L9-integration")

# ===================================================================================== L10 III-A
Xm = pose(1.0, 0.5, np.deg2rad(30))
bm = np.array([3.0, 2.0])
J_inv = jac(inv, Xm, rplus, rminus, 3)                                      # J^{X^-1}_X
J_act = jac(lambda Z: act(Z, bm), inv(Xm), rplus, vminus, 3)              # J^{Z.b}_Z at Z = X^-1
J_all = jac(lambda Z: act(inv(Z), bm), Xm, rplus, vminus, 3)              # whole H by FD
Rm, tm = Xm[:2, :2], Xm[:2, 2]
one_x = np.array([[0, -1.0], [1.0, 0]])
H_printed = -np.hstack([np.eye(2), (Rm.T @ one_x @ (bm - tm))[:, None]])  # §V-A, p. 12
NUM["L10_chain_residual"] = float(np.abs(J_act @ J_inv - J_all).max())
NUM["L10_printed_H_residual"] = float(np.abs(H_printed - J_all).max())
fig, axes = plt.subplots(1, 3, figsize=(9.2, 2.9), gridspec_kw=dict(width_ratios=[3, 3, 3]))
heat(axes[0], J_all, r"$H = J^{X^{-1}\cdot b}_{X}$  (2×3, FD of the whole)", vmax=2.5)
heat(axes[1], J_act, r"$J^{X^{-1}\cdot b}_{X^{-1}}$  (2×3, FD)", vmax=2.5)
heat(axes[2], J_inv, r"$J^{X^{-1}}_{X}$  (3×3, FD)", vmax=2.5)
fig.text(0.345, 0.45, "=", fontsize=18, color=P["ink"], ha="center"); fig.text(0.67, 0.45, "·", fontsize=22, color=P["ink"], ha="center")
fig.suptitle("Fig L10 · (58), §V-A  Chain rule: the measurement Jacobian is the product of two blocks  "
             + f"(max |product − whole| = {NUM['L10_chain_residual']:.0e})".replace("-", "−"),
             x=0.01, ha="left", fontsize=10.5, color=P["ink"])
fig.tight_layout(rect=(0, 0, 1, 0.92))
save(fig, "L10-chain-rule")

# ===================================================================================== L11 III-B
Xa = pose(1.0, 0.5, np.deg2rad(30)); Yb = pose(-0.7, 1.2, np.deg2rad(-75))
Jfd = [jac(inv, Xa, rplus, rminus, 3),
       jac(lambda Z: Z @ Yb, Xa, rplus, rminus, 3),
       jac(lambda Z: Xa @ Z, Yb, rplus, rminus, 3)]
Jad = [-Ad_generic(Xa), np.linalg.inv(Ad_generic(Yb)), np.eye(3)]
names = [(r"$J^{X^{-1}}_{X}$  FD", r"$-\mathrm{Ad}_X$  (62)"), (r"$J^{XY}_{X}$  FD", r"$\mathrm{Ad}_Y^{-1}$  (65)"), (r"$J^{XY}_{Y}$  FD", r"$I$  (66)")]
NUM["L11_block_residuals"] = [float(np.abs(a - b_).max()) for a, b_ in zip(Jfd, Jad)]
tq = np.array([0.8, -0.4, 1.1])
Jr = jac(Exp, tq, vplus, rminus, 3)
Jl = jac(Exp, tq, vplus, lambda Y, X: Log(Y @ inv(X)), 3)  # left Jacobian (71): left-minus on the codomain
NUM["L11_Ad_eq_JlJrinv_residual"] = float(np.abs(Ad_generic(Exp(tq)) - Jl @ np.linalg.inv(Jr)).max())
NUM["L11_Jr_minus_eq_Jl_residual"] = float(np.abs(jac(Exp, -tq, vplus, rminus, 3) - Jl).max())
fig, axes = plt.subplots(2, 3, figsize=(7.6, 5.4))
for j in range(3):
    heat(axes[0, j], Jfd[j], names[j][0], vmax=2.5)
    heat(axes[1, j], Jad[j], names[j][1], vmax=2.5)
fig.suptitle("Fig L11 · (61)–(66)  The inverse and composition blocks are adjoints: FD (top) = formula (bottom)\n"
             f"max differences {', '.join(f'{r:.0e}' for r in NUM['L11_block_residuals'])}".replace("-", "−"),
             x=0.01, ha="left", fontsize=10.5, color=P["ink"])
fig.tight_layout(rect=(0, 0, 1, 0.9))
save(fig, "L11-elementary-blocks")

# ===================================================================================== L12 III-C
def Exp3(w):
    return expm(hat3(w))


def Log3(Rm_):
    A = np.real(logm(Rm_))
    return np.array([A[2, 1], A[0, 2], A[1, 0]])


u3 = np.array([0.3, -0.5, 0.8]); u3 /= np.linalg.norm(u3)
thg = np.linspace(0.05, 2 * np.pi - 0.05, 120)
smin, smax = [], []
for a in thg:
    Jr3 = jac(Exp3, a * u3, vplus, lambda Y, X: Log3(X.T @ Y), 3, h=1e-6)
    sv = np.linalg.svd(Jr3, compute_uv=False); smin.append(sv.min()); smax.append(sv.max())
smin = np.array(smin)
NUM["L12_sigma_min_at_pi"] = float(np.interp(np.pi, thg, smin))
NUM["L12_cond_Jrinv_at_pi"] = float(1 / NUM["L12_sigma_min_at_pi"])
fig, ax = plt.subplots(figsize=(5.8, 3.8))
ax.plot(thg, smax, color=R["gray"], lw=1.2, label="largest singular value of J_r")
ax.plot(thg, smin, color=R["teal"], lw=1.8, label="smallest singular value of J_r")
ax.plot(thg, np.minimum(1 / smin, 8), color=R["coral"], lw=1.4, ls="--", label="‖J_r⁻¹‖₂ = ‖J^{Log}‖  (79), clipped at 8")
ax.axvspan(np.pi, 2 * np.pi, color=R["amber"], alpha=0.08); ax.text(np.pi + 0.1, 6.8, "outside Log's range", color=R["amber"], fontsize=8.5)
ax.axvline(np.pi, color=P["grid"], lw=0.8, ls=":")
ax.set_xlabel("θ = ‖θ‖ [rad]  (SO(3), J_r by FD of Exp)"); ax.set_ylabel("gain"); ax.set_ylim(0, 8.5); ax.legend(loc="center left", fontsize=8)
style.fig_label(ax, "Fig L12 · (67), (79)", "J_r is singular only at 2π; on Log's range ‖J_r⁻¹‖ ≤ π/2")
save(fig, "L12-jr-conditioning")

# ===================================================================================== L13 IV
M0 = pose(0.3, 0.2, np.deg2rad(30))
tau7 = np.array([2.0, 0.0, np.pi / 2])  # (rho, theta) in the paper's SE(2) order; p = rho for the others
R0, t0 = M0[:2, :2], M0[:2, 2]
pse = np.array([(M0 @ Exp(s * tau7))[:2, 2] for s in ss])
ptso = np.array([t0 + R0 @ (s * tau7[:2]) for s in ss])
pcomp = np.array([t0 + s * tau7[:2] for s in ss])
fig, ax = plt.subplots(figsize=(5.8, 4.4))
ax.plot(pse[:, 0], pse[:, 1], color=R["teal"], lw=1.8, label="SE(2): t + R V(θ)ρ  (arc)")
ax.plot(ptso[:, 0], ptso[:, 1], color=R["blue"], lw=1.6, ls="--", label="T(2)×SO(2): t + R p  (body-frame line)")
ax.plot(pcomp[:, 0], pcomp[:, 1], color=R["coral"], lw=1.6, ls="-.", label="⟨ℝ², SO(2)⟩: t + p  (world-frame line)")
frame(ax, M0, label="M")
Rend = M0[:2, :2] @ expm(np.array([[0, -tau7[2]], [tau7[2], 0]]))
for pend in [pse[-1], ptso[-1], pcomp[-1]]:
    Te = np.eye(3); Te[:2, :2] = Rend; Te[:2, 2] = pend; frame(ax, Te)
ax.text(-0.5, 2.75, "τ: ρ = p = (2, 0) m, θ = π/2 rad", fontsize=8.5, color=P["muted"], family="monospace")
ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8); ax.set_aspect("equal"); ax.set_xlim(-0.6, 3.0); ax.set_ylim(-0.4, 2.9)
ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
style.fig_label(ax, "Fig L13 · Ex. 7, (84)–(88)", "One τ, three manifolds: one heading, three positions")
save(fig, "L13-composite")

# ===================================================================================== L14 V setup
poses = [pose(0.0, 0.0, 0.0), pose(1.6, 0.5, np.deg2rad(25)), pose(3.0, 1.4, np.deg2rad(40))]
beacons = {4: np.array([1.0, -1.0]), 5: np.array([2.2, 2.4]), 6: np.array([4.2, 0.2])}
links = [(1, 4), (1, 5), (2, 5), (2, 6), (3, 6)]
fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.9), gridspec_kw=dict(width_ratios=[1.35, 1]))
ax = axes[0]
for i, k in links:
    p_ = poses[i - 1][:2, 2]; ax.plot([p_[0], beacons[k][0]], [p_[1], beacons[k][1]], color=R["coral"], lw=0.9, alpha=0.7)
for i in range(2):
    a_, b_ = poses[i][:2, 2], poses[i + 1][:2, 2]; ax.plot([a_[0], b_[0]], [a_[1], b_[1]], color=P["ink"], lw=1.4)
for i, Xi in enumerate(poses):
    frame(ax, Xi, L=0.5, label=f"X{i + 1}")
for k, bk in beacons.items():
    ax.plot(*bk, "o", color=R["blue"], ms=7, mfc="white", mew=1.6); ax.text(bk[0] + 0.12, bk[1] + 0.1, f"b{k}", fontsize=9, color=R["blue"])
ax.set_aspect("equal"); ax.set_xlim(-0.6, 4.8); ax.set_ylim(-1.5, 2.9); ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
ax.set_title("world: poses Xᵢ ∈ SE(2), beacons bₖ ∈ ℝ²", loc="left", fontsize=10, color=P["ink"])
ax = axes[1]
for k in (5, 6):
    yk = act(inv(poses[1]), beacons[k])
    ax.add_patch(FancyArrowPatch((0, 0), tuple(yk), arrowstyle="-|>", mutation_scale=10, color=R["coral"], lw=1.4))
    ax.text(yk[0] + 0.08, yk[1] + 0.08, f"y₂,{k} = X₂⁻¹·b{k}\n= ({yk[0]:.2f}, {yk[1]:.2f}) m".replace("-", "−"), fontsize=8.5, color=R["coral"])
frame(ax, np.eye(3), L=0.6); ax.text(-0.15, -0.35, "X₂ (robot frame)", fontsize=9, color=P["ink"], ha="right")
ax.set_aspect("equal"); ax.set_xlim(-2.2, 4.6); ax.set_ylim(-1.8, 2.6); ax.set_xlabel("x_body [m]"); ax.set_ylabel("y_body [m]")
ax.set_title("what the sensor reports at X₂", loc="left", fontsize=10, color=P["ink"])
fig.suptitle("Fig L14 · (92)–(96), Fig. 12  Beacons are measured in the robot's frame: y = X⁻¹·b + n",
             x=0.01, ha="left", fontsize=11, color=P["ink"])
fig.tight_layout()
save(fig, "L14-setup")

# ===================================================================================== L15 V-A
dt = 0.1
u_nom = np.array([1.0 * dt, 0.0, 0.6 * dt])
W = np.diag([0.10**2 * dt, 0.05**2 * dt, 0.10**2 * dt])   # (93) with sigma_v, sigma_s, sigma_omega
Nn = np.diag([0.10**2, 0.10**2])                            # (96)
X0e = pose(0.0, 0.0, 0.0); P0 = np.diag([0.02**2, 0.02**2, 0.03**2])
steps = 25
Mc = 2000
Xs = [rplus(X0e, t) for t in rng.multivariate_normal(np.zeros(3), P0, Mc)]
Xh, Pk = X0e.copy(), P0.copy()
snap = {}
for k in range(1, steps + 1):
    F = jac(lambda Z: rplus(Z, u_nom), Xh, rplus, rminus, 3)            # = Ad_{Exp(u)}^{-1}  (100)
    G = jac(lambda uu: rplus(Xh, uu), u_nom, vplus, rminus, 3)          # = J_r(u)            (100)
    Xh = rplus(Xh, u_nom)                                              # (99)
    Pk = F @ Pk @ F.T + G @ W @ G.T                                    # (100)
    ws = rng.multivariate_normal(np.zeros(3), W, Mc)
    Xs = [rplus(Xi, u_nom + wi) for Xi, wi in zip(Xs, ws)]
    if k in (8, 16, 25):
        snap[k] = (Xh.copy(), Pk.copy(), np.array([Xi[:2, 2] for Xi in Xs]))
taus_mc = np.array([rminus(Xi, Xh) for Xi in Xs])
d2 = np.einsum("ij,jk,ik->i", taus_mc, np.linalg.inv(Pk), taus_mc)
NUM["L15_mc_inside_95"] = float(np.mean(d2 < chi2.ppf(0.95, 3)))
NUM["L15_F_vs_Adinv"] = float(np.abs(F - np.linalg.inv(Ad_generic(Exp(u_nom)))).max())
# one beacon correction (101)-(102); the measurement taken from one Monte Carlo sample as the truth
bk = np.array([3.5, 3.5])
Xtrue = Xs[0]
yk = act(inv(Xtrue), bk) + rng.multivariate_normal(np.zeros(2), Nn)
H = jac(lambda Z: act(inv(Z), bk), Xh, rplus, vminus, 3)
zk = yk - act(inv(Xh), bk)
Z = H @ Pk @ H.T + Nn
K = Pk @ H.T @ np.linalg.inv(Z)
Xpost = rplus(Xh, K @ zk)
Ppost = Pk - K @ Z @ K.T
NUM["L15_trace_P_prior"] = float(np.trace(Pk)); NUM["L15_trace_P_post"] = float(np.trace(Ppost))
NUM["L15_err_prior_m"] = float(np.linalg.norm(Xh[:2, 2] - Xtrue[:2, 2])); NUM["L15_err_post_m"] = float(np.linalg.norm(Xpost[:2, 2] - Xtrue[:2, 2]))
fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.0))
ax = axes[0]
pos_of = lambda Z: Z[:2, 2]
for k, (Xk_, Pk_, cloud) in snap.items():
    ax.scatter(cloud[:, 0], cloud[:, 1], s=2, color=R["gray"], alpha=0.18, lw=0)
    Jp = jac(pos_of, Xk_, rplus, vminus, 3)
    style.cov_ellipse(ax, Xk_[:2, 2], Jp @ Pk_ @ Jp.T, n_std=2, role="blue", fill_alpha=0.05)
    frame(ax, Xk_, L=0.25); ax.text(Xk_[0, 2] + 0.05, Xk_[1, 2] - 0.35, f"k = {k}", fontsize=8.5, color=P["muted"])
ax.set_aspect("equal"); ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
ax.set_title(f"predict (99)–(100): {100 * NUM['L15_mc_inside_95']:.1f} % of MC inside the χ²₃ 95 % set",
             loc="left", fontsize=9.5, color=P["ink"])
ax = axes[1]
ax.scatter(snap[25][2][:, 0], snap[25][2][:, 1], s=2, color=R["gray"], alpha=0.18, lw=0)
Jp = jac(pos_of, Xh, rplus, vminus, 3)
style.cov_ellipse(ax, Xh[:2, 2], Jp @ Pk @ Jp.T, n_std=2, role="blue", fill_alpha=0.06)
Jp2 = jac(pos_of, Xpost, rplus, vminus, 3)
style.cov_ellipse(ax, Xpost[:2, 2], Jp2 @ Ppost @ Jp2.T, n_std=2, role="teal", fill_alpha=0.12)
ax.plot(*Xtrue[:2, 2], "*", color=P["ink"], ms=9, label="truth")
ax.plot(*Xh[:2, 2], "o", color=R["blue"], ms=4, label="prior X̂")
ax.plot(*Xpost[:2, 2], "o", color=R["teal"], ms=4, label="posterior X̂ ⊕ δx")
ax.plot([Xtrue[0, 2], bk[0]], [Xtrue[1, 2], bk[1]], color=R["coral"], lw=1, ls="--", label="beacon measurement")
ax.plot(*bk, "o", color=R["coral"], ms=7, mfc="white", mew=1.6)
ax.set_aspect("equal"); ax.set_xlabel("x [m]"); ax.legend(fontsize=7.5, loc="upper left")
ax.set_title(f"correct (101)–(102): tr P {NUM['L15_trace_P_prior']:.3f} → {NUM['L15_trace_P_post']:.3f}",
             loc="left", fontsize=9.5, color=P["ink"])
fig.suptitle("Fig L15 · §V-A  The ESKF carries P in the tangent at X̂: it follows the curved cloud, and one beacon shrinks it",
             x=0.01, ha="left", fontsize=10.5, color=P["ink"])
fig.tight_layout()
save(fig, "L15-eskf")

# ===================================================================================== L16 V-B
blocks = [("X1", 3), ("X2", 3), ("X3", 3), ("b4", 2), ("b5", 2), ("b6", 2)]
col0 = np.cumsum([0] + [s for _, s in blocks])
idx = {n: i for i, (n, _) in enumerate(blocks)}
factors = [("r1", ["X1"], 3), ("r12", ["X1", "X2"], 3), ("r23", ["X2", "X3"], 3), ("r14", ["X1", "b4"], 2),
           ("r15", ["X1", "b5"], 2), ("r25", ["X2", "b5"], 2), ("r26", ["X2", "b6"], 2), ("r36", ["X3", "b6"], 2)]
nr = sum(f[2] for f in factors); nc = col0[-1]
Jmask = np.zeros((nr, nc)); r0 = 0; row_edges = [0]
for name, vars_, dim in factors:
    for v_ in vars_:
        c0 = col0[idx[v_]]; Jmask[r0:r0 + dim, c0:c0 + blocks[idx[v_]][1]] = 1
    r0 += dim; row_edges.append(r0)
Hmask = (Jmask.T @ Jmask) > 0
NUM["L16_J_shape"] = [int(nr), int(nc)]; NUM["L16_J_fill"] = float(Jmask.mean()); NUM["L16_JtJ_fill"] = float(Hmask.mean())
fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.4), gridspec_kw=dict(width_ratios=[1, 1.05]))
for ax, Mk, rows, ttl in [(axes[0], Jmask, row_edges, f"J  ({nr}×{nc}),  {100 * NUM['L16_J_fill']:.0f} % non-zero"),
                          (axes[1], Hmask, col0, f"JᵀJ  ({nc}×{nc}),  {100 * NUM['L16_JtJ_fill']:.0f} % non-zero")]:
    ax.imshow(Mk, cmap=matplotlib.colors.ListedColormap([P["surface"], R["teal"]]), aspect="equal", interpolation="nearest")
    for c_ in col0[1:-1]:
        ax.axvline(c_ - 0.5, color=P["grid"], lw=0.6)
    for r_ in rows[1:-1]:
        ax.axhline(r_ - 0.5, color=P["grid"], lw=0.6)
    ax.set_xticks([(col0[i] + col0[i + 1]) / 2 - 0.5 for i in range(len(blocks))], [n for n, _ in blocks], fontsize=8)
    ax.grid(False); ax.set_title(ttl, loc="left", fontsize=10, color=P["ink"])
axes[0].set_yticks([(row_edges[i] + row_edges[i + 1]) / 2 - 0.5 for i in range(len(factors))], [f[0] for f in factors], fontsize=8)
axes[1].set_yticks([(col0[i] + col0[i + 1]) / 2 - 0.5 for i in range(len(blocks))], [n for n, _ in blocks], fontsize=8)
fig.suptitle("Fig L16 · (103)–(109), Fig. 12  Each factor touches one or two blocks, so J and JᵀJ are block-sparse",
             x=0.01, ha="left", fontsize=11, color=P["ink"])
fig.tight_layout()
save(fig, "L16-sam-sparsity")

# ===================================================================================== L17 App. B
thv = np.logspace(-10, 0, 400)
ref_a = 2 * np.sin(thv / 2) ** 2 / thv**2                                  # exact identity, no cancellation
naive_a = (1 - np.cos(thv)) / thv**2
# (θ − sin θ)/θ³ : reference from the series, which converges fast for θ ≤ 1
ref_b = sum((-1) ** k * thv ** (2 * k) / np.prod(np.arange(1, 2 * k + 4, dtype=float)) for k in range(12))
naive_b = (thv - np.sin(thv)) / thv**3
rel_a = np.maximum(np.abs(naive_a - ref_a) / ref_a, 1e-17)
rel_b = np.maximum(np.abs(naive_b - ref_b) / ref_b, 1e-17)
NUM["L17_a_relerr_at_1e-4"] = float(np.interp(-4, np.log10(thv), rel_a))
NUM["L17_b_relerr_at_1e-3"] = float(np.interp(-3, np.log10(thv), rel_b))
NUM["L17_a_dead_below"] = float(thv[np.where(rel_a >= 0.99)[0].max()])
NUM["L17_b_dead_below"] = float(thv[np.where(rel_b >= 0.99)[0].max()])
fig, ax = plt.subplots(figsize=(5.8, 3.9))
ax.loglog(thv, rel_a, color=R["coral"], lw=1.4, label="(1 − cos θ)/θ²  as printed in (143)")
ax.loglog(thv, rel_b, color=R["amber"], lw=1.4, label="(θ − sin θ)/θ³  as printed in (143)")
ax.axhline(1e-8, color=P["grid"], lw=0.8, ls=":")
ax.set_xlabel("θ [rad]"); ax.set_ylabel("relative error in float64"); ax.set_ylim(1e-17, 1e3); ax.legend(loc="upper right", fontsize=8)
style.fig_label(ax, "Fig L17 · (143)–(146)", "Printed J_r coefficients lose every digit as θ → 0")
save(fig, "L17-small-angle")

# ===================================================================================== L18 App. C
thc = np.linspace(-2 * np.pi, 2 * np.pi, 401)
ratio = np.array([np.linalg.norm(Exp(np.array([2.0, 0.0, a]))[:2, 2]) / 2.0 for a in thc])
fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.9), gridspec_kw=dict(width_ratios=[1, 1.15]))
ax = axes[0]
for a, col in [(0.0, R["gray"]), (np.pi / 2, R["blue"]), (np.pi, R["teal"]), (3 * np.pi / 2, R["coral"])]:
    pth = np.array([Exp(s * np.array([2.0, 0.0, a]))[:2, 2] for s in np.linspace(0, 1, 80)])
    ax.plot(pth[:, 0], pth[:, 1], color=col, lw=1.6, label=f"θ = {a:.2f} rad")
    ax.plot(*pth[-1], "o", color=col, ms=4)
frame(ax, np.eye(3), L=0.35)
ax.set_aspect("equal"); ax.legend(fontsize=7.8, loc="upper left"); ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
ax.set_xlim(-1.4, 2.4); ax.set_ylim(-0.4, 2.6)
ax.set_title("Exp((ρ, θ)) with ρ = (2, 0) m", loc="left", fontsize=10, color=P["ink"])
ax = axes[1]
ax.plot(thc, ratio, color=R["teal"], lw=1.8, label="‖translation of Exp(τ)‖ / ‖ρ‖  (expm)")
ax.plot(thc, np.ones_like(thc), color=R["gray"], lw=1, ls="--", label="‖ρ‖ if you read ρ as (x, y)")
ax.set_xlabel("θ [rad]"); ax.set_ylabel("ratio"); ax.legend(fontsize=8, loc="lower center")
NUM["L18_ratio_at_pi"] = float(np.interp(np.pi, thc, ratio))
fig.suptitle("Fig L18 · (153), (156)–(158)  ρ is not the translation: Exp drives ‖ρ‖ along an arc, so the chord is shorter",
             x=0.01, ha="left", fontsize=11, color=P["ink"])
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "L18-se2-exp")

(OUT / "numbers.json").write_text(json.dumps(NUM, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(NUM, indent=2, ensure_ascii=False))
print("wrote", sorted(p.name for p in OUT.glob("*.svg")))
