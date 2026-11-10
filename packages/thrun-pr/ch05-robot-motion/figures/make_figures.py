"""Generate the lecture figures for ch. 5 in the Chalk style. Run from anywhere:
    python figures/make_figures.py
Writes L*.svg / L*.png and numbers.json (every number quoted in lecture.md comes from that file).

Every motion model is imported from exercises/solutions/T3_solution.py (gated). The only model code kept
here is the book AS PRINTED (Table 5.4 samplers, Table 5.5 with delta-hat variances, Table 5.1 line 7),
which the figures contrast with the reference. Still: this file calls the solution, so read it after T3.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle  # noqa: E402

from viz.py import style  # noqa: E402

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG))
from exercises.models import wrap  # noqa: E402
from exercises.solutions import T3_solution as ref  # noqa: E402

OUT = Path(__file__).resolve().parent
P = style.use("light")
R = style.ROLE
NUM: dict = {}


def save(fig, name):
    fig.savefig(OUT / f"{name}.svg", pad_inches=0.15)
    fig.savefig(OUT / f"{name}.png", format="png", dpi=110, pad_inches=0.15)
    plt.close(fig)


def suptitle(fig, num, title):
    from matplotlib.transforms import offset_copy
    fig.text(0.01, 1.0, title, fontsize=12, color=P["ink"], weight="medium", va="bottom")
    fig.text(0.01, 1.0, num, fontsize=8.5, color=P["faint"], family="monospace", va="bottom",
             transform=offset_copy(fig.transFigure, fig=fig, y=20, units="points"))


def robot(ax, x, y, th, color, r=0.12, lw=1.4, z=4):
    ax.add_patch(Circle((x, y), r, fill=False, ec=color, lw=lw, zorder=z))
    ax.plot([x, x + r * np.cos(th)], [y, y + r * np.sin(th)], color=color, lw=lw, zorder=z)


def prob_normal(a, b2):  # Table 5.2, from the reference log density
    return np.exp(ref.log_prob(a, b2))


def sample_normal12(b2, rng, shape):  # Table 5.4 line 2, as printed (not an exercise)
    b = np.sqrt(b2)
    return 0.5 * rng.uniform(-b, b, shape + (12,)).sum(axis=-1)


def sample_triangular(b2, rng, shape):  # Table 5.4 line 4, as printed (not an exercise)
    b = np.sqrt(b2)
    return np.sqrt(6) / 2 * (rng.uniform(-b, b, shape) + rng.uniform(-b, b, shape))


# ------------------------------------------------------------------ thin adapters over the reference solution
# The figures pass poses as (x, y, theta) tuples of arrays; the reference works on (..., 3) arrays.
def _split(X):
    return tuple(np.moveaxis(np.asarray(X), -1, 0))


def vel_forward(x0, vh, wh, gh, dt):  # (5.16)
    return _split(ref.velocity_forward(np.asarray(x0, float), vh, wh, gh, dt))


def sample_vel(x0, u, a, dt, n, rng):  # Table 5.3
    return _split(ref.sample_motion_model_velocity(u, np.tile(np.asarray(x0, float), (n, 1)), a, dt, rng))


def vel_inverse(x0, xp, yp, tp, dt):  # Table 5.1 lines 2-9, with the sign fix of card C3
    return ref.velocity_inverse(np.asarray(x0, float), np.stack(np.broadcast_arrays(xp, yp, tp), -1), dt)


def vel_density(x0, u, a, dt, xp, yp, tp, pose_density=False):  # Table 5.1 line 10
    Xp = np.stack(np.broadcast_arrays(xp, yp, tp), -1)
    return np.exp(ref.log_motion_model_velocity(Xp, u, np.asarray(x0, float), a, dt, pose_density=pose_density))


odo_params = ref.odometry_params  # (5.34)-(5.36)


def sample_odo(x0, ob0, ob1, a, n, rng):  # Table 5.6
    X = np.column_stack(np.broadcast_arrays(*x0, np.zeros(n))[:3]).astype(float)
    return _split(ref.sample_motion_model_odometry((ob0, ob1), X, a, rng))


def odo_density_ref(x0, ob0, ob1, a, xp, yp, tp, pose_density=False):  # Table 5.5 with measured-delta variances
    Xp = np.stack(np.broadcast_arrays(xp, yp, tp), -1)
    return np.exp(ref.log_motion_model_odometry(Xp, (ob0, ob1), np.asarray(x0, float), a, pose_density=pose_density))


def book_table55(x0, ob0, ob1, a, xp, yp, tp, wrap_rot2=True):
    """Table 5.5 line by line AS PRINTED: variances from the hypothesized delta-hats, optional unwrapped rot2.
    Kept separate on purpose: Figs L6b and L9 contrast the printed table with the reference."""
    r1, tr, r2 = odo_params(ob0, ob1)
    x, y, th = x0
    r1h = wrap(np.arctan2(yp - y, xp - x) - th)
    trh = np.hypot(xp - x, yp - y)
    r2h_raw = tp - th - r1h
    r2h = wrap(r2h_raw) if wrap_rot2 else r2h_raw
    e2 = wrap(r2 - r2h) if wrap_rot2 else r2 - r2h
    p1 = prob_normal(wrap(r1 - r1h), a[0] * r1h ** 2 + a[1] * trh ** 2)
    p2 = prob_normal(tr - trh, a[2] * trh ** 2 + a[3] * (r1h ** 2 + r2h ** 2))
    p3 = prob_normal(e2, a[0] * r2h ** 2 + a[1] * trh ** 2)
    return p1 * p2 * p3


def xy_marginal(dens_fn, xe, ye, nth=120):
    """Evaluate a pose 'density' on an x-y grid and sum over theta' (what Figs 5.3 and 5.8 show)."""
    xc = 0.5 * (xe[1:] + xe[:-1])
    yc = 0.5 * (ye[1:] + ye[:-1])
    tc = -np.pi + (np.arange(nth) + 0.5) * 2 * np.pi / nth
    X, Y, T = np.meshgrid(xc, yc, tc, indexing="xy")
    d = dens_fn(X, Y, T).sum(axis=2)
    return d / d.sum()


def hist2(xs, ys, xe, ye):
    h, _, _ = np.histogram2d(ys, xs, bins=[ye, xe])
    return h / h.sum()


def tv(p, q):
    return 0.5 * float(np.abs(p - q).sum())


# ---------------------------------------------------------------------- L1  Fig 5.2 redrawn
rng = np.random.default_rng(5)
A_ODO = (0.02, 0.002, 0.02, 0.005)
M = 3000


def run_path(way):
    """Sample Table 5.6 step by step along a polyline (MCL line 4 with no measurement)."""
    poses = [(way[0, 0], way[0, 1], 0.0)]
    for i in range(1, len(way)):
        d = way[i] - way[i - 1]
        poses.append((way[i, 0], way[i, 1], np.arctan2(d[1], d[0])))
    cur = (np.zeros(M), np.zeros(M), np.zeros(M))
    for i in range(1, len(poses)):
        cur = sample_odo(cur, poses[i - 1], poses[i], A_ODO, M, rng)
    return cur


def major_std(c):
    return float(np.sqrt(np.linalg.eigvalsh(np.cov(np.vstack([c[0], c[1]]))).max()))


way_b = np.array([[0, 0], [1, 0], [1, -0.8], [2.2, -0.8], [2.2, 0.6], [3.2, 0.6]], float)
L_b = float(np.sum(np.linalg.norm(np.diff(way_b, axis=0), axis=1)))
way_a = np.column_stack([np.linspace(0, L_b, 6), np.zeros(6)])
ca, cb_ = run_path(way_a), run_path(way_b)
NUM["L1"] = {"alpha": A_ODO, "path_m": round(L_b, 2), "steps": 5,
             "a_major_std_m": round(major_std(ca), 3), "b_major_std_m": round(major_std(cb_), 3)}
fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.9), sharey=True)
for ax, way, c, ttl in [(axes[0], way_a, ca, f"(a) {L_b:.1f} m straight, 5 odometry steps"),
                        (axes[1], way_b, cb_, f"(b) {L_b:.1f} m with four 90° turns, 5 steps")]:
    ax.scatter(c[0], c[1], s=3, color=R["blue"], alpha=0.2, lw=0)
    style.cov_ellipse(ax, (c[0].mean(), c[1].mean()), np.cov(np.vstack([c[0], c[1]])), n_std=2.0, role="blue", fill_alpha=0.0)
    ax.plot(way[:, 0], way[:, 1], color=P["ink"], lw=1.0)
    robot(ax, 0, 0, 0, P["ink"], r=0.15)
    ax.set_title(ttl, fontsize=10, loc="left")
    ax.annotate(f"major-axis std {major_std(c):.2f} m", (0.03, 0.05), xycoords="axes fraction",
                color=R["teal_deep"], fontsize=8.5, family="monospace")
    ax.set_aspect("equal"); ax.set_xlim(-0.5, 8.0); ax.set_ylim(-3.2, 3.2); ax.set_xlabel("x [m]")
axes[0].set_ylabel("y [m]")
suptitle(fig, "Fig L1 · eq. 5.3", "p(xₜ | uₜ, xₜ₋₁) is a cloud; the same distance with turns gives a wider one")
fig.tight_layout(rect=(0, 0, 1, 0.9))
save(fig, "L1-motion-posterior")

# ---------------------------------------------------------------------- L2  exact motion on a circle
x0 = np.array([0.0, 0.0, np.deg2rad(20)])
v, w, dt = 1.0, 0.8, 2.0
xc_, yc_ = x0[0] - v / w * np.sin(x0[2]), x0[1] + v / w * np.cos(x0[2])  # (5.7), (5.8)
xe_, ye_, te_ = vel_forward(x0, np.array(v), np.array(w), np.array(0.0), dt)  # (5.9)
# ODE check: integrate the unicycle with RK4 at a fine step
s = x0.copy(); hstep = 1e-4
f = lambda st: np.array([v * np.cos(st[2]), v * np.sin(st[2]), w])
for _ in range(int(round(dt / hstep))):
    k1 = f(s); k2 = f(s + hstep / 2 * k1); k3 = f(s + hstep / 2 * k2); k4 = f(s + hstep * k3)
    s = s + hstep / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
NUM["L2"] = {"v_mps": v, "w_radps": w, "dt_s": dt, "r_m": round(v / w, 3),
             "closed_form_vs_rk4_max_err": float(f"{np.max(np.abs(np.array([xe_, ye_, te_]) - s)):.1e}")}
fig, ax = plt.subplots(figsize=(6.2, 4.6))
ang = np.linspace(0, 2 * np.pi, 300)
ax.plot(xc_ + v / w * np.cos(ang), yc_ + v / w * np.sin(ang), color=P["grid"], lw=0.8, ls="--")
tt = np.linspace(0, dt, 200)
px, py, _ = vel_forward(x0, np.full_like(tt, v), np.full_like(tt, w), np.zeros_like(tt), tt)
ax.plot(px, py, color=R["teal"], lw=2.2, label="path, length v·Δt")
ax.plot([xc_, x0[0]], [yc_, x0[1]], color=R["gray"], lw=1.0)
ax.plot([xc_, xe_], [yc_, ye_], color=R["gray"], lw=1.0)
ax.plot(xc_, yc_, "o", color=R["gray"], ms=5)
ax.annotate("centre (5.7), (5.8)", (xc_, yc_), (xc_ - 1.15, yc_ + 0.12), color=P["muted"], fontsize=9)
ax.annotate("r = |v/ω|", ((xc_ + x0[0]) / 2, (yc_ + x0[1]) / 2), ((xc_ + x0[0]) / 2 + 0.06, (yc_ + x0[1]) / 2 - 0.12),
            color=P["muted"], fontsize=9)
a0 = np.arctan2(x0[1] - yc_, x0[0] - xc_)
arc = np.linspace(a0, a0 + w * dt, 60)
ax.plot(xc_ + 0.3 * np.cos(arc), yc_ + 0.3 * np.sin(arc), color=R["teal"], lw=1.0)
ax.annotate("ωΔt", (xc_ + 0.42 * np.cos(a0 + w * dt / 2) - 0.05, yc_ + 0.42 * np.sin(a0 + w * dt / 2) - 0.05), color=R["teal_deep"], fontsize=10)
robot(ax, *x0, R["blue"])
robot(ax, xe_, ye_, te_, R["blue"])
ax.annotate("xₜ₋₁ = (x, y, θ)", (x0[0], x0[1]), (x0[0] + 0.12, x0[1] - 0.22), color=P["ink"], fontsize=9)
ax.annotate("xₜ = (x′, y′, θ′)  (5.9)", (xe_, ye_), (xe_ - 1.25, ye_ + 0.22), color=P["ink"], fontsize=9)
ax.plot([x0[0], x0[0] + 2.2 * np.cos(x0[2])], [x0[1], x0[1] + 2.2 * np.sin(x0[2])], color=R["amber"], lw=1.0, ls=":")
ax.annotate("ω → 0: straight line,\nr → ∞", (x0[0] + 1.6 * np.cos(x0[2]), x0[1] + 1.6 * np.sin(x0[2])),
            (x0[0] + 1.15, x0[1] + 0.68), color=R["amber"], fontsize=9)
ax.set_aspect("equal"); ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
ax.set_xlim(-1.9, 2.3)
ax.legend(loc="upper right")
suptitle(fig, "Fig L2 · eqs. 5.5–5.9", "Constant (v, ω) puts the robot on a circle; the heading turns by ωΔt")
fig.tight_layout(rect=(0, 0, 1, 0.92))
save(fig, "L2-circle")

# ---------------------------------------------------------------------- L3  two noise terms -> 2-D manifold
rng = np.random.default_rng(7)
x0 = (0.0, 0.0, 0.0); u = (1.0, 0.8); dt = 1.5
A2 = (0.02, 0.02, 0.02, 0.02, 0.0, 0.0)
A3 = (0.02, 0.02, 0.02, 0.02, 0.01, 0.01)
n = 4000
s2x, s2y, s2t = sample_vel(x0, u, A2, dt, n, rng)
s3x, s3y, s3t = sample_vel(x0, u, A3, dt, n, rng)
g2 = vel_inverse(x0, s2x, s2y, s2t, dt)[2]
g3 = vel_inverse(x0, s3x, s3y, s3t, dt)[2]
NUM["L3"] = {"max_abs_gamma_recovered_alpha56_zero": float(f"{np.max(np.abs(g2)):.1e}"),
             "std_gamma_recovered_alpha56_nonzero_radps": round(float(g3.std()), 3),
             "std_gamma_expected_radps": round(float(np.sqrt(A3[4] * u[0] ** 2 + A3[5] * u[1] ** 2)), 3)}
fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.6), gridspec_kw={"width_ratios": [1.15, 1]})
ax = axes[0]
sc = ax.scatter(s2x, s2y, c=np.rad2deg(s2t), s=3, cmap="cividis", lw=0)
cb = fig.colorbar(sc, ax=ax, fraction=0.05, pad=0.02); cb.set_label("θ′ [deg]", color=P["muted"])
robot(ax, *x0, P["edge"])
ax.set_aspect("equal"); ax.set_xlabel("x′ [m]"); ax.set_ylabel("y′ [m]")
ax.set_title("(a) α₅ = α₆ = 0: θ′ is a function of (x′, y′)", fontsize=10, loc="left")
ax = axes[1]
bins = np.linspace(-0.6, 0.6, 61)
ax.hist(g3, bins=bins, color=R["teal"], alpha=0.45, edgecolor=R["teal"], lw=0.6, label="α₅, α₆ > 0 (5.15)")
ax.axvline(0, color=R["amber"], lw=2.2, label="α₅ = α₆ = 0: all at 0")
ax.set_xlabel("γ̂ recovered by Table 5.1 line 9 [rad/s]"); ax.set_ylabel("samples")
ax.set_title("(b) the final rotation γ̂ fills the third dimension", fontsize=10, loc="left")
ax.legend(loc="upper right", fontsize=8)
suptitle(fig, "Fig L3 · eqs. 5.13–5.16", "With two noise terms every sample lies on one surface; γ̂ thickens it")
fig.tight_layout(rect=(0, 0, 1, 0.91))
save(fig, "L3-final-rotation")

# ---------------------------------------------------------------------- L4  error densities and samplers
rng = np.random.default_rng(11)
N = 1_000_000
sn = sample_normal12(1.0, rng, (N,))
st = sample_triangular(1.0, rng, (N,))
NUM["L4"] = {"N": N, "var_normal12": round(float(sn.var()), 4), "var_triangular": round(float(st.var()), 4),
             "frac_normal12_beyond_2b": round(float(np.mean(np.abs(sn) > 2)), 4),
             "max_abs_normal12_seen_b": round(float(np.abs(sn).max()), 2),
             "support_normal12_b": 6.0, "support_triangular_b": round(float(np.sqrt(6)), 3)}
fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.2), sharey=True)
aa = np.linspace(-4, 4, 800)
tri = np.maximum(0, 1 / np.sqrt(6) - np.abs(aa) / 6)
for ax, samp, dens, name, sup in [
    (axes[0], sn, prob_normal(aa, 1.0), "(a) normal (5.11); Table 5.4 line 2", 6.0),
    (axes[1], st, tri, "(b) triangular (5.12); Table 5.4 line 4", np.sqrt(6)),
]:
    ax.hist(samp, bins=np.linspace(-4, 4, 81), density=True, color=R["teal"], alpha=0.35, edgecolor=R["teal"], lw=0.4,
            label="sampler, 10⁶ draws")
    ax.plot(aa, dens, color=R["blue"], lw=1.6, label="Table 5.2 density, b² = 1")
    ax.set_title(name, fontsize=10, loc="left"); ax.set_xlabel("a / b")
    ax.set_xlim(-4, 4)
axes[0].axvspan(-4, -2, color=R["amber"], alpha=0.08, lw=0)
axes[0].axvspan(2, 4, color=R["amber"], alpha=0.08, lw=0)
axes[0].annotate(f"{100 * NUM['L4']['frac_normal12_beyond_2b']:.2f} % of draws\noutside [−2b, 2b] (p. 132)",
                 (2.1, 0.30), color=R["amber"], fontsize=8.5)
axes[1].axvline(-np.sqrt(6), color=R["gray"], lw=0.8, ls=":"); axes[1].axvline(np.sqrt(6), color=R["gray"], lw=0.8, ls=":")
axes[1].annotate("±√6 b", (np.sqrt(6) + 0.08, 0.30), color=P["muted"], fontsize=8.5)
axes[0].set_ylabel("density")
for ax in axes:
    ax.legend(loc="upper left", fontsize=7.5)
suptitle(fig, "Fig L4 · Tables 5.2, 5.4", "Both samplers have variance b²; the 12-uniform one is not bounded by 2b")
fig.tight_layout(rect=(0, 0, 1, 0.9))
save(fig, "L4-error-densities")

# ---------------------------------------------------------------------- L5  Figs 5.3 / 5.4: density and samples
rng = np.random.default_rng(13)
x0 = (0.0, 0.0, 0.0); u = (1.0, 0.8); dt = 2.0
SETS = [("(a) moderate", (0.02, 0.02, 0.02, 0.02, 0.005, 0.005)),
        ("(b) small angular, large translational", (0.12, 0.12, 0.002, 0.002, 0.005, 0.005)),
        ("(c) large angular, small translational", (0.002, 0.002, 0.08, 0.08, 0.005, 0.005))]
xe = np.linspace(-0.6, 2.8, 171); ye = np.linspace(-0.3, 3.0, 166)
ex, ey, et = vel_forward(x0, np.array(u[0]), np.array(u[1]), np.array(0.0), dt)
fig, axes = plt.subplots(1, 3, figsize=(11, 3.9), sharey=True)
NUM["L5"] = {}
for ax, (name, a) in zip(axes, SETS):
    D = xy_marginal(lambda X, Y, T: vel_density(x0, u, a, dt, X, Y, T), xe, ye)
    sx, sy, _ = sample_vel(x0, u, a, dt, 500, rng)
    ax.pcolormesh(xe, ye, D, cmap="Greys", shading="flat", vmax=D.max(), alpha=0.85, rasterized=True)
    ax.scatter(sx, sy, s=3, color=R["blue"], alpha=0.7, lw=0)
    tt = np.linspace(0, dt, 100)
    px, py, _ = vel_forward(x0, np.full_like(tt, u[0]), np.full_like(tt, u[1]), np.zeros_like(tt), tt)
    ax.plot(px, py, color=R["teal"], lw=1.2)
    robot(ax, *x0, P["edge"], r=0.15)
    robot(ax, float(ex), float(ey), float(et), R["teal"], r=0.15)
    ax.set_aspect("equal"); ax.set_xlim(xe[0], xe[-1]); ax.set_ylim(ye[0], ye[-1])
    ax.set_title(name, fontsize=9.5, loc="left"); ax.set_xlabel("x′ [m]")
axes[0].set_ylabel("y′ [m]")
suptitle(fig, "Fig L5 · Tables 5.1, 5.3",
         "Density (gray) and 500 samples (blue) agree; v-noise stretches the cloud along a ray, ω-noise bends it")
fig.tight_layout(rect=(0, 0, 1, 0.9))
save(fig, "L5-velocity-model")

# sign trap of Table 5.1 line 7 (right turn), measured
vh_b = []
for uu in [(1.0, -0.5), (-1.0, 0.5), (1.0, 0.5)]:
    px, py, pt = vel_forward((0.0, 0.0, 0.0), np.array(uu[0]), np.array(uu[1]), np.array(0.0), 1.0)
    # book line 7: v-hat = dtheta * r* / dt (no sign)
    xx, yy, th = 0.0, 0.0, 0.0
    num = (xx - px) * np.cos(th) + (yy - py) * np.sin(th)
    den = (yy - py) * np.cos(th) - (xx - px) * np.sin(th)
    mu = 0.5 * num / den
    xs = (xx + px) / 2 + mu * (yy - py); ys = (yy + py) / 2 + mu * (px - xx)
    rs = np.hypot(xx - xs, yy - ys)
    dth = np.arctan2(py - ys, px - xs) - np.arctan2(yy - ys, xx - xs)
    vh_b.append(round(float(dth * rs), 3))
NUM["L5"]["book_line7_vhat_for_(1,-0.5)_(-1,0.5)_(1,0.5)"] = vh_b

# ---------------------------------------------------------------------- L6  odometry: rot-trans-rot and the seam
fig, axes = plt.subplots(1, 2, figsize=(10, 3.9), gridspec_kw={"width_ratios": [1.25, 1]})
ax = axes[0]
ob0 = np.array([0.6, 0.4, np.deg2rad(60)]); ob1 = np.array([2.4, 1.3, np.deg2rad(110)])
r1, tr, r2 = odo_params(ob0, ob1)
xw0 = np.array([3.4, -1.0, np.deg2rad(75)])
xw1 = np.array([xw0[0] + tr * np.cos(xw0[2] + r1), xw0[1] + tr * np.sin(xw0[2] + r1), xw0[2] + r1 + r2])
for (p0, p1, col, lab) in [(ob0, ob1, R["coral"], "odometry frame: x̄ₜ₋₁ → x̄ₜ"), (xw0, xw1, R["blue"], "world frame: xₜ₋₁ → xₜ")]:
    robot(ax, *p0, col, r=0.2); robot(ax, *p1, col, r=0.2)
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=col, lw=1.2, label=lab)
    hd = np.arctan2(p1[1] - p0[1], p1[0] - p0[0])
    a1 = np.linspace(p0[2], hd, 30)
    ax.plot(p0[0] + 0.45 * np.cos(a1), p0[1] + 0.45 * np.sin(a1), color=R["teal"], lw=1.4)
    a2 = np.linspace(hd, p1[2], 30)
    ax.plot(p1[0] + 0.45 * np.cos(a2), p1[1] + 0.45 * np.sin(a2), color=R["teal"], lw=1.4)
    ax.plot([p0[0], p0[0] + 0.6 * np.cos(p0[2])], [p0[1], p0[1] + 0.6 * np.sin(p0[2])], color=col, lw=0.7, ls=":")
    ax.plot([p1[0], p1[0] + 0.5 * np.cos(hd)], [p1[1], p1[1] + 0.5 * np.sin(hd)], color=col, lw=0.7, ls=":")
ax.annotate("δrot1", (ob0[0] + 0.5, ob0[1] + 0.35), color=R["teal_deep"], fontsize=9)
ax.annotate("δtrans", ((ob0[0] + ob1[0]) / 2 - 0.1, (ob0[1] + ob1[1]) / 2 + 0.15), color=R["teal_deep"], fontsize=9)
ax.annotate("δrot2", (ob1[0] + 0.25, ob1[1] + 0.48), color=R["teal_deep"], fontsize=9)
ax.set_aspect("equal"); ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
ax.set_xlim(-0.2, 6.0); ax.set_ylim(-1.5, 2.2)
ax.legend(loc="lower left", fontsize=8)
ax.set_title(f"(a) same (δrot1, δtrans, δrot2) = ({np.rad2deg(r1):.0f}°, {tr:.2f} m, {np.rad2deg(r2):.0f}°), two frames".replace("-", "−"),
             fontsize=9.5, loc="left")
NUM["L6"] = {"example_rot1_deg": round(float(np.rad2deg(r1)), 1), "example_trans_m": round(float(tr), 3),
             "example_rot2_deg": round(float(np.rad2deg(r2)), 1)}
# (b) Table 5.5 as a function of theta' near the +-pi seam
ax = axes[1]
A_SEAM = (0.05, 0.01, 0.05, 0.01)
ob0 = np.array([0.0, 0.0, np.deg2rad(150)]); ob1 = np.array([1.0 * np.cos(np.deg2rad(150)), 1.0 * np.sin(np.deg2rad(150)), np.deg2rad(178)])
xw0 = ob0.copy()
_r1, _tr, _r2 = odo_params(ob0, ob1)
xp_ = xw0[0] + _tr * np.cos(xw0[2] + _r1); yp_ = xw0[1] + _tr * np.sin(xw0[2] + _r1)
tp = np.linspace(-np.pi, np.pi, 2001)
dw = book_table55(xw0, ob0, ob1, A_SEAM, np.full_like(tp, xp_), np.full_like(tp, yp_), tp, wrap_rot2=True)
du = book_table55(xw0, ob0, ob1, A_SEAM, np.full_like(tp, xp_), np.full_like(tp, yp_), tp, wrap_rot2=False)
ax.plot(np.rad2deg(tp), dw, color=R["teal"], lw=1.8, label="δrot2 − δ̂rot2 wrapped")
ax.plot(np.rad2deg(tp), du, color=R["amber"], lw=1.4, ls="--", label="not wrapped")
ax.axvline(178, color=R["gray"], lw=0.8, ls=":")
ax.set_xlabel("hypothesized θ′ [deg]"); ax.set_ylabel("Table 5.5 output")
ax.set_xlim(-180, 180)
ax.legend(loc="upper center", fontsize=8)
ax.set_title("(b) odometry says θ̄′ = 178°; the density wraps to −180°", fontsize=9.5, loc="left")
lost = 1 - float(np.trapezoid(du, tp) / np.trapezoid(dw, tp))
NUM["L6"]["seam_theta_bar_deg"] = 178
NUM["L6"]["mass_lost_unwrapped_frac"] = round(lost, 3)
suptitle(fig, "Fig L6 · Table 5.5, eqs. 5.34–5.36", "Odometry is used only as a relative motion; its angles live on a circle")
fig.tight_layout(rect=(0, 0, 1, 0.9))
save(fig, "L6-odometry")

# ---------------------------------------------------------------------- L7  Fig 5.10: dead reckoning
rng = np.random.default_rng(17)
A_DR = (0.01, 0.0005, 0.01, 0.0005)
corners = np.array([[0, 0], [5, 0], [5, 4], [-3, 4]], float)
pts = [corners[0]]
for i in range(1, len(corners)):
    seg = corners[i] - corners[i - 1]
    k = int(round(np.linalg.norm(seg) / 0.5))
    for j in range(1, k + 1):
        pts.append(corners[i - 1] + seg * j / k)
pts = np.array(pts)
hd = np.zeros(len(pts))
for i in range(1, len(pts)):
    d = pts[i] - pts[i - 1]; hd[i] = np.arctan2(d[1], d[0])
odo = np.column_stack([pts, hd])
M = 2000
cur = (np.zeros(M), np.zeros(M), np.zeros(M))
snaps = {}
dist = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
for i in range(1, len(odo)):
    cur = sample_odo(cur, odo[i - 1], odo[i], A_DR, M, rng)
    if i % 6 == 0 or i == len(odo) - 1:
        snaps[i] = cur
fig, ax = plt.subplots(figsize=(8.4, 4.8))
ax.plot(pts[:, 0], pts[:, 1], color=P["ink"], lw=1.0)
spread = {}
for i, c in snaps.items():
    ax.scatter(c[0][:400], c[1][:400], s=2, color=R["blue"], alpha=0.25, lw=0)
    ax.plot(*pts[i], "o", color=P["ink"], ms=3)
    cov = np.cov(np.vstack([c[0], c[1]]))
    style.cov_ellipse(ax, (c[0].mean(), c[1].mean()), cov, n_std=2.0, role="blue", fill_alpha=0.0)
    spread[round(float(dist[i]), 1)] = round(float(np.sqrt(np.linalg.eigvalsh(cov).max())), 3)
robot(ax, 0, 0, 0, P["edge"], r=0.2)
ax.annotate("start", (0, 0), (0.3, -0.6), color=P["muted"], fontsize=9)
ax.set_aspect("equal"); ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
suptitle(fig, "Fig L7 · Table 5.6, Fig 5.10", "Dead reckoning: the cloud only grows, and each turn's heading error swings it sideways")
fig.tight_layout(rect=(0, 0, 1, 0.92))
save(fig, "L7-dead-reckoning")
NUM["L7"] = {"alpha": A_DR, "step_m": 0.5, "path_m": round(float(dist[-1]), 1),
             "major_std_m_by_distance": spread}

# ---------------------------------------------------------------------- L8  Fig 5.11: map and the wall
rng = np.random.default_rng(19)
x0 = (0.0, 0.0, np.deg2rad(90)); u = (1.0, -0.35); dt = 3.0
a = (0.03, 0.03, 0.03, 0.03, 0.005, 0.005)
WALL = (0.2, 1.75, 2.2, 0.15)  # x, y, width, height of the obstacle
RAD = 0.15  # robot radius; obstacle grown by it (configuration space)
CX = (WALL[0] - RAD, WALL[1] - RAD, WALL[0] + WALL[2] + RAD, WALL[1] + WALL[3] + RAD)


def in_cspace(x, y):
    return (x > CX[0]) & (x < CX[2]) & (y > CX[1]) & (y < CX[3])


n = 200_000
twin = copy.deepcopy(rng)  # replays Table 5.3's first two draws to get (v-hat, w-hat) for the arc checks
sx, sy, st_ = sample_vel(x0, u, a, dt, n, rng)
vh = u[0] + ref.sample_normal(a[0] * u[0] ** 2 + a[1] * u[1] ** 2, twin, n)
wh = u[1] + ref.sample_normal(a[2] * u[0] ** 2 + a[3] * u[1] ** 2, twin, n)
gh = np.zeros(n)
assert np.allclose(np.column_stack(vel_forward(x0, vh, wh, gh, dt)[:2]), np.column_stack([sx, sy]), atol=1e-9), "replay"
ok = ~in_cspace(sx, sy)
hit_path = {}
for Nst in [1, 2, 5, 10, 20]:
    alive = ok.copy()
    for k in range(1, Nst):
        ix, iy, _ = vel_forward(x0, vh, wh, np.zeros_like(gh), dt * k / Nst)
        alive &= ~in_cspace(ix, iy)
    hit_path[Nst] = alive
# continuous truth: check the arc densely
crossed = np.zeros(n, bool)
for k in range(1, 200):
    ix, iy, _ = vel_forward(x0, vh, wh, np.zeros_like(gh), dt * k / 200)
    crossed |= in_cspace(ix, iy)
through = {N_: round(float(np.mean(crossed[hit_path[N_]])), 4) for N_ in hit_path}
step_len = {N_: round(u[0] * dt / N_, 3) for N_ in hit_path}
# capped rejection sampler (Table 5.7, retries capped)
acc = float(ok.mean())
NUM["L8"] = {"accept_rate_final_pose": round(acc, 3), "through_wall_frac_of_accepted_by_checks": through,
             "step_len_m": step_len, "cspace_wall_thickness_m": round(WALL[3] + 2 * RAD, 2),
             "p_10_retries_all_fail": float(f"{(1 - acc) ** 10:.1e}")}
xe = np.linspace(-0.6, 3.0, 181); ye = np.linspace(-0.4, 3.0, 171)
D = xy_marginal(lambda X, Y, T: vel_density(x0, u, a, dt, X, Y, T), xe, ye)
xc = 0.5 * (xe[1:] + xe[:-1]); yc = 0.5 * (ye[1:] + ye[:-1])
XX, YY = np.meshgrid(xc, yc)
Dm = np.where(in_cspace(XX, YY), 0.0, D); Dm /= Dm.sum()
fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.9), gridspec_kw={"width_ratios": [1, 1, 0.9]})
for ax, dd, ttl in [(axes[0], D, "(a) p(xₜ | uₜ, xₜ₋₁)"), (axes[1], Dm, "(b) × p(xₜ | m), normalized (5.48)")]:
    ax.pcolormesh(xe, ye, dd, cmap="Greys", shading="flat", rasterized=True)
    robot(ax, *x0, P["edge"], r=0.15)
    ax.set_aspect("equal"); ax.set_xlim(xe[0], xe[-1]); ax.set_ylim(ye[0], ye[-1])
    ax.set_title(ttl, fontsize=9.5, loc="left"); ax.set_xlabel("x′ [m]")
axes[0].set_ylabel("y′ [m]")
for ax in axes[:2]:
    ax.add_patch(Rectangle((WALL[0], WALL[1]), WALL[2], WALL[3], fc=R["gray"], ec=P["edge"], lw=0.8, alpha=0.6, zorder=3))
axes[1].add_patch(Rectangle((CX[0], CX[1]), CX[2] - CX[0], CX[3] - CX[1], fill=False, ec=R["gray"], lw=0.8, ls="--", zorder=3))
bad = crossed & ok
axes[1].scatter(sx[bad][:400], sy[bad][:400], s=3, color=R["amber"], lw=0, alpha=0.8, zorder=4, label="went through the wall")
axes[1].legend(loc="lower right", fontsize=7.5)
ax = axes[2]
Ns = list(hit_path)
ax.bar(range(len(Ns)), [100 * through[k] for k in Ns], color=R["amber"], alpha=0.75)
ax.set_xticks(range(len(Ns)), [f"{k}\n{step_len[k]:.2f} m" for k in Ns])
ax.set_xlabel("map checks per motion · step length")
ax.set_ylabel("accepted samples that crossed [%]")
ax.set_title("(c) check more often, the error vanishes", fontsize=9.5, loc="left")
suptitle(fig, "Fig L8 · eq. 5.48, Table 5.7", "Checking only the final pose lets the robot through the wall")
fig.tight_layout(rect=(0, 0, 1, 0.9))
save(fig, "L8-motion-and-maps")

# ---------------------------------------------------------------------- L9  two models, two forms, one distribution
rng = np.random.default_rng(23)
x0v = (0.0, 0.0, 0.0); uv = (1.0, 0.8); dtv = 2.0; av = SETS[0][1]
xev = np.linspace(-0.4, 1.8, 111); yev = np.linspace(0.3, 2.5, 111)
Dv = xy_marginal(lambda X, Y, T: vel_density(x0v, uv, av, dtv, X, Y, T), xev, yev, nth=180)
svx, svy, _ = sample_vel(x0v, uv, av, dtv, 400_000, rng)
svx2, svy2, _ = sample_vel(x0v, uv, av, dtv, 400_000, rng)
Hv = hist2(svx, svy, xev, yev); Hv2 = hist2(svx2, svy2, xev, yev)
x0o = (0.0, 0.0, 0.0); ob0 = np.array([0.0, 0.0, 0.0]); ob1 = np.array([1.5, 1.0, np.deg2rad(70)])
ao = (0.05, 0.01, 0.05, 0.01)
xeo = np.linspace(0.6, 2.4, 111); yeo = np.linspace(0.1, 1.9, 111)
Do = xy_marginal(lambda X, Y, T: book_table55(x0o, ob0, ob1, ao, X, Y, T), xeo, yeo, nth=180)
so = sample_odo(x0o, ob0, ob1, ao, 400_000, rng); so2 = sample_odo(x0o, ob0, ob1, ao, 400_000, rng)
Ho = hist2(so[0], so[1], xeo, yeo); Ho2 = hist2(so2[0], so2[1], xeo, yeo)


Dvj = xy_marginal(lambda X, Y, T: vel_density(x0v, uv, av, dtv, X, Y, T, pose_density=True), xev, yev, nth=180)
Doj = xy_marginal(lambda X, Y, T: book_table55(x0o, ob0, ob1, ao, X, Y, T) / np.hypot(X, Y), xeo, yeo, nth=180)
Dom = xy_marginal(lambda X, Y, T: odo_density_ref(x0o, ob0, ob1, ao, X, Y, T, pose_density=True), xeo, yeo, nth=180)
NUM["L9"] = {"samples": 400_000,
             "velocity_TV_with_jacobian": round(tv(Dvj, Hv), 3),
             "odometry_TV_with_jacobian": round(tv(Doj, Ho), 3),
             "odometry_TV_with_jacobian_and_measured_delta_variances": round(tv(Dom, Ho), 3),
             "velocity_TV_density_vs_samples": round(tv(Dv, Hv), 3), "velocity_TV_samples_vs_samples": round(tv(Hv, Hv2), 3),
             "odometry_TV_density_vs_samples": round(tv(Do, Ho), 3), "odometry_TV_samples_vs_samples": round(tv(Ho, Ho2), 3)}
fig, axes = plt.subplots(2, 2, figsize=(8.0, 7.6))
for row, (D_, H_, xe_, ye_, name, key) in enumerate([
    (Dv, Hv, xev, yev, "velocity", "velocity"), (Do, Ho, xeo, yeo, "odometry", "odometry")]):
    vmax = max(D_.max(), H_.max())
    axes[row, 0].pcolormesh(xe_, ye_, D_, cmap="Greys", vmax=vmax, rasterized=True)
    axes[row, 1].pcolormesh(xe_, ye_, H_, cmap="Greys", vmax=vmax, rasterized=True)
    axes[row, 0].set_title(f"{name}: density (Table {'5.1' if row == 0 else '5.5'}), Σθ′", fontsize=9.5, loc="left")
    axes[row, 1].set_title(f"{name}: histogram of Table {'5.3' if row == 0 else '5.6'}", fontsize=9.5, loc="left")
    axes[row, 1].annotate(f"TV = {NUM['L9'][key + '_TV_density_vs_samples']:.3f}\n(sampling floor {NUM['L9'][key + '_TV_samples_vs_samples']:.3f})",
                          (0.04, 0.84), xycoords="axes fraction", color=R["teal_deep"], fontsize=8.5, family="monospace")
    for ax in axes[row]:
        ax.set_aspect("equal"); ax.set_xlabel("x′ [m]")
    axes[row, 0].set_ylabel("y′ [m]")
suptitle(fig, "Fig L9 · ch. 5 summary", "Inverse model and forward model describe one distribution")
fig.tight_layout(rect=(0, 0, 1, 0.94))
save(fig, "L9-two-forms")

(OUT / "numbers.json").write_text(json.dumps(NUM, indent=2, default=lambda o: list(o) if isinstance(o, tuple) else str(o)))
print(json.dumps(NUM, indent=2, default=str))
