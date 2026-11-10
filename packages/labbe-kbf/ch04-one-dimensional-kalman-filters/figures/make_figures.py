"""Generate the lecture figures for Labbe ch. 4 (one-dimensional Kalman filters) in the Chalk style.

Run from the repo root or the package folder:
    .venv/bin/python packages/labbe-kbf/ch04-one-dimensional-kalman-filters/figures/make_figures.py

Every number quoted in lecture.md is printed by this script (the NUMBERS block at the end).
Naming follows the repo: R_proc = process variance (Labbe's Q, process_var),
Q_meas = measurement variance (Labbe's R, sensor_var), u = known displacement per step.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

from viz.py import style  # noqa: E402

OUT = Path(__file__).resolve().parent
P = style.use("light")
R = style.ROLE
NUM: dict[str, str] = {}


def save(fig, name):
    fig.savefig(OUT / f"{name}.svg")
    fig.savefig(OUT / f"{name}.png", format="png", dpi=110)
    plt.close(fig)


def pdf(x, m, var):
    return np.exp(-0.5 * (x - m) ** 2 / var) / np.sqrt(2 * np.pi * var)


# ------------------------------------------------------------------ the scalar filter used for the figures
def predict(x, P_, u, R_proc):
    return x + u, P_ + R_proc


def update(x, P_, z, Q_meas):
    y = z - x
    S = P_ + Q_meas
    K = P_ / S
    return x + K * y, (1 - K) * P_, K, y, S


def run_kf(zs, x0, P0, u, R_proc, Q_meas):
    """Return arrays of prior mean/var, posterior mean/var, gain, residual, innovation variance."""
    x, P_ = x0, P0
    out = {k: [] for k in ("xp", "Pp", "x", "P", "K", "y", "S")}
    for z in zs:
        xp, Pp = predict(x, P_, u, R_proc)
        x, P_, K, y, S = update(xp, Pp, z, Q_meas)
        for k, v in zip(out, (xp, Pp, x, P_, K, y, S)):
            out[k].append(v)
    return {k: np.array(v) for k, v in out.items()}


def dog(rng, n, x0, vel, Q_meas, R_proc_true, accel=0.0):
    """Labbe's DogSimulation: x += vel + N(0, R_proc_true); z = x + N(0, Q_meas). Optional velocity ramp."""
    xs, zs = [], []
    x, v = x0, vel
    for _ in range(n):
        v += accel
        x = x + v + rng.normal() * np.sqrt(R_proc_true)
        xs.append(x)
        zs.append(x + rng.normal() * np.sqrt(Q_meas))
    return np.array(xs), np.array(zs)


def p_inf(R_proc, Q_meas):
    """Steady-state posterior variance: positive root of P^2 + R_proc P - R_proc Q_meas = 0."""
    return 0.5 * (-R_proc + np.sqrt(R_proc**2 + 4 * R_proc * Q_meas))


# ================================================================== L1: histogram vs Gaussian
rng = np.random.default_rng(4)
bins = np.arange(0, 20)
uni = pdf(bins, 10.0, 2.0**2)
uni = uni * (1 + 0.15 * rng.uniform(-1, 1, bins.size))
uni /= uni.sum()
bi = 0.55 * pdf(bins, 5.0, 1.2**2) + 0.45 * pdf(bins, 14.0, 1.2**2)
bi /= bi.sum()
xx = np.linspace(-1, 20, 600)
fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.0), sharey=True)
for ax, h, lab in [(axes[0], uni, "one peak: two numbers carry it"),
                   (axes[1], bi, "two peaks: the Gaussian puts the dog where it is not")]:
    m = (bins * h).sum()
    v = ((bins - m) ** 2 * h).sum()
    ax.bar(bins, h, width=0.8, color=R["gray"], alpha=0.45, lw=0, label="histogram (20 numbers)")
    ax.plot(xx, pdf(xx, m, v), color=R["blue"], label=f"N(μ={m:.1f}, σ²={v:.1f}) (2 numbers)")
    ax.axvline(m, color=R["teal"], lw=1.0, ls="--")
    ax.set_title(lab, loc="left", fontsize=10, color=P["ink"])
    ax.set_xlabel("hallway position [m]")
    ax.legend(fontsize=7.5, loc="upper left")
    ax.set_ylim(0, 0.3)
axes[0].set_ylabel("probability")
fig.suptitle("Fig L1 · p. 134  A Gaussian replaces the histogram only when the belief has one peak",
             x=0.01, ha="left", fontsize=11, color=P["ink"])
fig.tight_layout()
save(fig, "L1-histogram-vs-gaussian")

# ================================================================== L2: predict = sum of Gaussians (p. 136)
x0m, x0v = 10.0, 0.2**2
fm, fv = 15.0, 0.7**2
pm, pv = x0m + fm, x0v + fv
NUM["L2 prior"] = f"N({pm:.3f}, {pv:.3f})"
xx = np.linspace(5, 31, 800)
fig, ax = plt.subplots(figsize=(7.2, 3.2))
ax.plot(xx, pdf(xx, x0m, x0v), color=R["blue"], label=f"posterior x = N({x0m:g}, {x0v:.2f})")
ax.plot(xx, pdf(xx, fm, fv), color=R["gray"], ls="--", lw=1.1, label=f"movement f_x = N({fm:g}, {fv:.2f})")
ax.plot(xx, pdf(xx, pm, pv), color=R["teal"], lw=2.0, label=f"prior x̄ = N({pm:g}, {pv:.2f})")
ax.annotate("", xy=(pm, pdf(pm, pm, pv) * 1.05), xytext=(x0m, pdf(pm, pm, pv) * 1.05),
            arrowprops=dict(arrowstyle="->", color=P["muted"], lw=0.9))
ax.text((x0m + pm) / 2, pdf(pm, pm, pv) * 1.10, "means add: 10 + 15", ha="center", fontsize=8.5, color=P["muted"])
ax.text(pm + 1.2, pdf(pm, pm, pv) * 0.55, "variances add:\n0.04 + 0.49 = 0.53 m²", fontsize=8.5, color=R["teal_deep"])
ax.set_xlabel("position [m]")
ax.set_ylabel("density")
ax.legend(fontsize=8, loc="upper center")
ax.set_ylim(0, pdf(x0m, x0m, x0v) * 1.15)
style.fig_label(ax, "Fig L2 · p. 136", "Predict adds: the prior is always wider than the posterior it came from")
save(fig, "L2-predict-sum")

# ================================================================== L3: update = product of Gaussians (p. 141)
xx = np.linspace(4, 15, 800)
fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.2), sharey=True)
for ax, (a, b) in zip(axes, [((8.5, 1.5), (10.2, 0.5)), ((8.5, 0.5), (10.2, 1.5))]):
    (m1, v1), (m2, v2) = a, b
    m = (v1 * m2 + v2 * m1) / (v1 + v2)
    v = v1 * v2 / (v1 + v2)
    ax.plot(xx, pdf(xx, m1, v1), color=R["blue"], label=f"prior N({m1}, {v1})")
    ax.plot(xx, pdf(xx, m2, v2), color=R["coral"], label=f"measurement N({m2}, {v2})")
    ax.plot(xx, pdf(xx, m, v), color=R["teal"], lw=2.0, label=f"posterior N({m:.3f}, {v:.3f})")
    ax.axvline(m, color=R["teal"], lw=0.8, ls=":")
    ax.set_xlabel("position [m]")
    ax.legend(fontsize=7.5, loc="upper right")
    NUM[f"L3 N({m1},{v1})xN({m2},{v2})"] = f"N({m:.4f}, {v:.4f})"
axes[0].set_title("uncertain prior, sharp sensor", loc="left", fontsize=10, color=P["ink"])
axes[1].set_title("sharp prior, uncertain sensor", loc="left", fontsize=10, color=P["ink"])
axes[0].set_ylabel("density")
axes[0].set_ylim(0, 0.95)
fig.suptitle("Fig L3 · pp. 138–142  The product is narrower than both inputs and sits nearer the sharper one",
             x=0.01, ha="left", fontsize=11, color=P["ink"])
fig.tight_layout()
save(fig, "L3-update-product")
NUM["L3 book p.138 update(N(10,.04),N(11,.01))"] = "N({:.3f}, {:.4f})".format(
    (0.04 * 11 + 0.01 * 10) / 0.05, 0.04 * 0.01 / 0.05)

# ================================================================== L4: the loop, P independent of z (pp. 143–148)
R_proc, Q_meas, N = 2.0, 4.5, 25
rng = np.random.default_rng(13)
truth, zs = dog(rng, N, 0.0, 1.0, Q_meas, R_proc)
kf = run_kf(zs, 0.0, 400.0, 1.0, R_proc, Q_meas)
rng2 = np.random.default_rng(99)
truth2, zs2 = dog(rng2, N, 0.0, 1.0, Q_meas, R_proc)
kf2 = run_kf(zs2, 0.0, 400.0, 1.0, R_proc, Q_meas)
NUM["L4 max |P(run1) - P(run2)|"] = f"{np.max(np.abs(kf['P'] - kf2['P'])):.1e}"
NUM["L4 P after 9 steps (R_proc=2, Q_meas=4.5)"] = f"{kf['P'][8]:.4f}"
NUM["L4 P inf (2, 4.5)"] = f"{p_inf(2, 4.5):.5f}"
kf10 = run_kf(np.zeros(10), 0.0, 400.0, 1.0, 1.0, 2.0)
NUM["L4 p.143 first prior var, first posterior var (R_proc=1, Q_meas=2)"] = f"{kf10['Pp'][0]:.3f}, {kf10['P'][0]:.4f}"
NUM["L4 p.143 P after 10 steps"] = f"{kf10['P'][-1]:.4f}"
k = np.arange(N)
fig, (ax, bx) = plt.subplots(2, 1, figsize=(7.4, 5.4), sharex=True, gridspec_kw=dict(height_ratios=[1.5, 1]))
ax.plot(k, truth, color=R["gray"], lw=1.0, label="truth")
ax.plot(k, zs, "o", color=R["coral"], ms=4, label=f"z, Q_meas = {Q_meas} m²")
ax.plot(k, kf["xp"], "v", color=R["blue"], mfc="none", ms=5, label="prior x̄")
ax.plot(k, kf["x"], color=R["blue"], label="posterior x")
s = np.sqrt(kf["P"])
ax.fill_between(k, kf["x"] - 2 * s, kf["x"] + 2 * s, color=R["blue"], alpha=0.12, lw=0, label="±2√P")
ax.set_ylabel("position [m]")
ax.set_ylim(min(kf["x"].min(), zs.min()) - 6, max(truth.max(), zs.max()) + 14)
ax.legend(fontsize=7.5, loc="upper left", ncol=2)
bx.semilogy(k, kf["Pp"], "v-", color=R["gray"], ms=4, lw=1.0, label="P̄ (prior)")
bx.semilogy(k, kf["P"], "o-", color=R["teal"], ms=3.5, label="P, run with seed 13")
bx.semilogy(k, kf2["P"], "x", color=R["coral"], ms=6, label="P, different measurements")
bx.axhline(p_inf(R_proc, Q_meas), color=R["teal"], lw=0.8, ls="--")
bx.text(12, p_inf(R_proc, Q_meas) * 0.86, f"P∞ = {p_inf(R_proc, Q_meas):.4f} m²", ha="center", va="top",
        fontsize=8.5, color=R["teal_deep"])
bx.set_ylabel("variance [m²]")
bx.set_xlabel("step")
bx.legend(fontsize=7.5, loc="upper right")
bx.set_ylim(1.0, 900)
style.fig_label(ax, "Fig L4 · pp. 147–148", "The mean follows the data; the variance follows only R_proc and Q_meas")
fig.tight_layout()
save(fig, "L4-kf-loop")

# ================================================================== L5: gain and residual (pp. 149–151)
fig, (ax, bx) = plt.subplots(1, 2, figsize=(9.4, 3.5), gridspec_kw=dict(width_ratios=[1.1, 1]))
xprev, u_, z_ = 2.0, 3.0, 9.0
xbar = xprev + u_
Kd = 0.6
xpost = xbar + Kd * (z_ - xbar)
ax.plot([0, 1], [xprev, xbar], color=R["blue"], lw=1.4)
ax.plot(0, xprev, "o", color=R["blue"], ms=7)
ax.plot(1, xbar, "v", color=R["blue"], ms=8, mfc="white", mew=1.6)
ax.plot(1, z_, "o", color=R["coral"], ms=8)
ax.plot([1, 1], [xbar, z_], color=R["gray"], lw=1.0, ls="--")
ax.plot([1, 1], [xbar, xpost], color=R["teal"], lw=3.0)
ax.plot(1, xpost, "o", color=R["teal"], ms=8)
ax.text(-0.04, xprev - 0.6, "posterior x(t−1)", fontsize=8.5, color=P["muted"])
ax.text(0.45, (xprev + xbar) / 2 - 0.9, "predict: + u", fontsize=8.5, color=R["blue_deep"])
ax.text(1.04, xbar - 0.1, "prior x̄", fontsize=8.5, color=R["blue_deep"], va="center")
ax.text(1.04, z_, "measurement z", fontsize=8.5, color=R["coral_deep"], va="center")
ax.text(1.04, xpost, "x = x̄ + K·y", fontsize=8.5, color=R["teal_deep"], va="center", weight="bold")
ax.text(0.9, (xbar + z_) / 2 + 1.3, "residual\ny = z − x̄", fontsize=8.5, color=P["muted"], ha="right")
ax.set_xlim(-0.15, 1.55)
ax.set_ylim(0, 10.5)
ax.set_xticks([0, 1], ["t − 1", "t"])
ax.set_ylabel("state")
ax.set_title(f"K = {Kd}: move {Kd:.0%} of the way along y", loc="left", fontsize=10, color=P["ink"])
ratio = np.logspace(-2, 2, 400)
bx.semilogx(ratio, ratio / (ratio + 1), color=R["teal"], lw=2.0)
for rr, lab in [(9.0, "P̄ = 9 Q_meas → K = 0.9"), (1.0, "P̄ = Q_meas → K = 0.5")]:
    bx.plot(rr, rr / (rr + 1), "o", color=R["teal_deep"], ms=6)
    bx.text(rr * 1.25, rr / (rr + 1) - 0.07, lab, fontsize=8.5, color=P["muted"])
bx.axhline(1, color=R["coral"], lw=0.8, ls=":")
bx.axhline(0, color=R["blue"], lw=0.8, ls=":")
bx.text(0.012, 0.93, "K → 1: copy the measurement", fontsize=8.5, color=R["coral_deep"])
bx.text(1.5, 0.04, "K → 0: keep the prior", fontsize=8.5, color=R["blue_deep"])
bx.set_xlabel("P̄ / Q_meas")
bx.set_ylabel("K")
bx.set_ylim(-0.05, 1.05)
bx.set_title("K = P̄ / (P̄ + Q_meas) depends only on the ratio", loc="left", fontsize=10, color=P["ink"])
fig.suptitle("Fig L5 · pp. 149–151  The gain picks a point on the residual; the variance ratio picks the gain",
             x=0.01, ha="left", fontsize=11, color=P["ink"])
fig.tight_layout()
save(fig, "L5-gain-residual")

# ================================================================== L6: the generic recipe (pp. 152–153)
fig, ax = plt.subplots(figsize=(8.6, 3.4))
ax.set_axis_off()
ax.set_xlim(0, 10)
ax.set_ylim(0, 4)
boxes = [
    (0.2, "Initialize", ["x = z₀ (or a guess)", "P = P₀"], R["gray"]),
    (3.5, "Predict", ["x̄ = x + u", "P̄ = P + R_proc"], R["blue"]),
    (6.8, "Update", ["y = z − x̄", "K = P̄ / (P̄ + Q_meas)", "x = x̄ + K·y", "P = (1 − K)·P̄"], R["teal"]),
]
for x0b, title, lines, col in boxes:
    ax.add_patch(FancyBboxPatch((x0b, 0.6), 3.0, 2.6, boxstyle="round,pad=0.02,rounding_size=0.15",
                                facecolor=col, alpha=0.10, edgecolor=col, lw=1.3))
    ax.text(x0b + 0.15, 2.95, title, fontsize=11, weight="bold", color=col, va="top")
    for i, ln in enumerate(lines):
        ax.text(x0b + 0.2, 2.35 - 0.42 * i, ln, fontsize=10, family="monospace", color=P["ink"], va="top")
ax.add_patch(FancyArrowPatch((3.22, 1.9), (3.48, 1.9), arrowstyle="-|>", mutation_scale=12, color=P["muted"]))
ax.add_patch(FancyArrowPatch((6.52, 1.9), (6.78, 1.9), arrowstyle="-|>", mutation_scale=12, color=P["muted"]))
ax.add_patch(FancyArrowPatch((8.3, 0.58), (5.0, 0.58), connectionstyle="arc3,rad=-0.35", arrowstyle="-|>",
                             mutation_scale=12, color=P["muted"]))
ax.text(6.65, 0.05, "next z", fontsize=9, color=P["muted"], ha="center")
ax.text(3.6, 3.45, "p. 153 Kalman form · g-h (ch. 1) is the same loop with a hand-picked K",
        fontsize=8.5, color=P["muted"])
style.fig_label(ax, "Fig L6 · p. 153", "Every filter in the book is this loop; only the math in the boxes changes")
save(fig, "L6-recipe")

# ================================================================== L7: the smug filter (pp. 155–158)
rng = np.random.default_rng(26)
N = 120
volt = np.where(np.arange(N) < 60, 16.3, 16.6)
Qm = 0.13**2
zs = volt + rng.normal(size=N) * 0.13
runs = {0.0: run_kf(zs, 25.0, 1000.0, 0.0, 0.0, Qm), 0.05**2: run_kf(zs, 25.0, 1000.0, 0.0, 0.05**2, Qm)}
k = np.arange(N)
fig, (ax, bx) = plt.subplots(2, 1, figsize=(7.4, 5.0), sharex=True, gridspec_kw=dict(height_ratios=[1.5, 1]))
ax.plot(k, volt, color=R["gray"], lw=1.0, label="true voltage")
ax.plot(k, zs, "o", color=R["coral"], ms=3, alpha=0.7, label="z, σ = 0.13 V")
ax.plot(k, runs[0.0]["x"], color=R["amber"], lw=1.6, label="R_proc = 0 (smug)")
ax.plot(k, runs[0.05**2]["x"], color=R["blue"], lw=1.6, label="R_proc = 0.05² V²")
ax.set_ylim(15.9, 17.0)
ax.set_ylabel("volts [V]")
ax.legend(fontsize=7.5, loc="upper left", ncol=2)
bx.semilogy(k, runs[0.0]["K"], color=R["amber"], label="K, R_proc = 0")
bx.semilogy(k, runs[0.05**2]["K"], color=R["teal"], label="K, R_proc = 0.05² V²")
bx.set_ylabel("gain K")
bx.set_xlabel("step")
bx.legend(fontsize=7.5, loc="upper right")
style.fig_label(ax, "Fig L7 · pp. 155–158", "With R_proc = 0 the gain dies as 1/n and the filter stops listening")
fig.tight_layout()
save(fig, "L7-smug-filter")
sm, ok = runs[0.0], runs[0.05**2]
NUM["L7 K at step 120, R_proc=0"] = f"{sm['K'][-1]:.4f}"
NUM["L7 K at step 120, R_proc=0.05^2"] = f"{ok['K'][-1]:.4f}"
NUM["L7 K inf thermometer"] = f"{p_inf(0.05**2, Qm) / Qm:.4f}"
NUM["L7 error at step 120 (true 16.6): smug, tuned"] = f"{sm['x'][-1] - 16.6:+.3f} V, {ok['x'][-1] - 16.6:+.3f} V"

# ================================================================== L8: R_proc is a claim about the model (pp. 159–161)
rng = np.random.default_rng(28)
N = 1000
t1, z1 = dog(rng, N, 0.0, 1.0, 300.0**2, 2.0)
e1 = run_kf(z1, 0.0, 500.0, 1.0, 2.0, 300.0**2)
rng = np.random.default_rng(29)
N2 = 100
t2, z2 = dog(rng, N2, 0.0, 1.0, 20.0, 0.001 * 10000, accel=0.04)
e2 = run_kf(z2, 0.0, 500.0, 1.0, 0.001, 20.0)
e2b = run_kf(z2, 0.0, 500.0, 1.0, 10.0, 20.0)
nis = e2["y"] ** 2 / e2["S"]
nisb = e2b["y"] ** 2 / e2b["S"]
NUM["L8 extreme noise: RMS error last 500 steps (filter), RMS z error"] = (
    f"{np.sqrt(np.mean((e1['x'][500:] - t1[500:]) ** 2)):.2f} m, {np.sqrt(np.mean((z1[500:] - t1[500:]) ** 2)):.1f} m")
NUM["L8 extreme noise: K inf"] = f"{p_inf(2, 300.0**2) / 300.0**2:.5f}"
NUM["L8 bad R_proc: final error filter (R_proc=0.001), (R_proc=10)"] = (
    f"{e2['x'][-1] - t2[-1]:+.1f} m, {e2b['x'][-1] - t2[-1]:+.1f} m")
NUM["L8 mean NIS steps 50-99: R_proc=0.001, R_proc=10"] = f"{nis[50:].mean():.1f}, {nisb[50:].mean():.2f}"
fig, (ax, bx) = plt.subplots(1, 2, figsize=(9.6, 3.6))
k1 = np.arange(N)
ax.plot(k1, z1, "o", color=R["coral"], ms=1.6, alpha=0.35, label="z, σ = 300 m")
ax.plot(k1, t1, color=R["gray"], lw=1.0, label="truth")
ax.plot(k1, e1["x"], color=R["blue"], lw=1.6, label="filter, R_proc = 2 m²")
ax.set_xlabel("step")
ax.set_ylabel("position [m]")
ax.set_title("model right, sensor awful: still a line", loc="left", fontsize=10, color=P["ink"])
ax.legend(fontsize=7.5, loc="upper left")
k2 = np.arange(N2)
bx.plot(k2, z2, "o", color=R["coral"], ms=3, label="z, accelerating dog")
bx.plot(k2, e2["x"], color=R["amber"], lw=1.6, label="R_proc = 0.001 m² (p. 160)")
bx.plot(k2, e2b["x"], color=R["blue"], lw=1.6, label="R_proc = 10 m²")
bx.set_xlabel("step")
bx.set_title("model wrong, R_proc tiny: diverges, no alarm", loc="left", fontsize=10, color=P["ink"])
bx.legend(fontsize=7.5, loc="upper left")
fig.suptitle("Fig L8 · pp. 159–161  R_proc says how much to trust the model; lie about it and the filter believes you",
             x=0.01, ha="left", fontsize=11, color=P["ink"])
fig.tight_layout()
save(fig, "L8-process-variance")

# ================================================================== L9: bad initial estimate (pp. 161–164)
M = 300
cases = [("x₀ = 1000, Q_meas = 25 m²", 25.0, "bad", R["blue"]),
         ("x₀ = 1000, Q_meas = 30000 m²", 30000.0, "bad", R["amber"]),
         ("x₀ = z₀, Q_meas = 30000 m²", 30000.0, "z0", R["teal"])]
N = 1000
fig, ax = plt.subplots(figsize=(7.4, 3.6))
for lab, Qm_, init, col in cases:
    err = np.zeros((M, N))
    for s in range(M):
        rng = np.random.default_rng(1000 + s)
        tr, zz = dog(rng, N, 0.0, 1.0, Qm_, 2.0)
        x0 = 1000.0 if init == "bad" else zz[0]
        err[s] = run_kf(zz, x0, 500.0, 1.0, 2.0, Qm_)["x"] - tr
    rms = np.sqrt((err**2).mean(0))
    ax.semilogy(np.arange(N), rms, color=col, label=lab)
    ss = np.sqrt(p_inf(2.0, Qm_))
    below = np.where(rms < 2 * ss)[0]
    NUM[f"L9 {lab}: first step RMS < 2 sqrt(P inf) ({2 * ss:.1f} m)"] = f"{below[0]}" if below.size else "never"
ax.set_xscale("symlog", linthresh=10)
ax.set_xlabel("step (log after 10)")
ax.set_ylabel("RMS error over 300 runs [m]")
ax.legend(fontsize=8, loc="upper right")
style.fig_label(ax, "Fig L9 · pp. 161–164", "A bad x₀ washes out at a rate Q_meas sets; starting at z₀ skips most of it")
save(fig, "L9-bad-init")
NUM["L9 p.161 first-step K (P0=500, R_proc=2, Q_meas=25)"] = f"{502 / 527:.5f}"

# ================================================================== L10: fixed gain (pp. 167–168)
R_proc, Q_meas, N, M = 2.0, 4.5, 40, 2000
Pinf = p_inf(R_proc, Q_meas)
Kinf = Pinf / Q_meas
fig, (ax, bx) = plt.subplots(1, 2, figsize=(9.4, 3.5))
for P0, col in [(400.0, R["blue"]), (1.0, R["coral"]), (0.01, R["gray"])]:
    r = run_kf(np.zeros(N), 0.0, P0, 1.0, R_proc, Q_meas)
    ax.plot(np.arange(N), r["K"], "o-", ms=3, color=col, lw=1.1, label=f"P₀ = {P0:g} m²")
ax.axhline(Kinf, color=R["teal"], lw=1.4, ls="--")
ax.text(N - 1, Kinf + 0.04, f"K∞ = {Kinf:.4f}", ha="right", fontsize=8.5, color=R["teal_deep"])
ax.set_xlabel("step")
ax.set_ylabel("K")
ax.set_title("K(t) forgets P₀ within a few steps", loc="left", fontsize=10, color=P["ink"])
ax.legend(fontsize=7.5, loc="upper right")
ekf, efix = np.zeros((M, N)), np.zeros((M, N))
for s in range(M):
    rng = np.random.default_rng(5000 + s)
    tr, zz = dog(rng, N, 0.0, 1.0, Q_meas, R_proc)
    ekf[s] = np.r_[zz[0], run_kf(zz[1:], zz[0], Q_meas, 1.0, R_proc, Q_meas)["x"]] - tr
    xf = zz[0]
    est = [xf]
    for z in zz[1:]:
        xf = xf + 1.0
        xf = xf + Kinf * (z - xf)
        est.append(xf)
    efix[s] = np.array(est) - tr
rk, rf = np.sqrt((ekf**2).mean(0)), np.sqrt((efix**2).mean(0))
bx.plot(np.arange(N), rk, color=R["blue"], label="Kalman filter, x₀ = z₀, P₀ = Q_meas")
bx.plot(np.arange(N), rf, color=R["teal"], ls="--", label=f"fixed K∞, x₀ = z₀")
bx.axhline(np.sqrt(Pinf), color=R["gray"], lw=0.8, ls=":")
bx.text(N - 1, np.sqrt(Pinf) * 0.9, "√P∞", ha="right", va="top", fontsize=8.5, color=P["muted"])
bx.set_xlabel("step")
bx.set_ylabel("RMS error, 2000 runs [m]")
bx.set_ylim(0, None)
bx.set_title("after the transient they are the same filter", loc="left", fontsize=10, color=P["ink"])
bx.legend(fontsize=7.5, loc="upper right")
fig.suptitle("Fig L10 · pp. 167–168  Constant R_proc and Q_meas make P and K constant; hard-code K∞",
             x=0.01, ha="left", fontsize=11, color=P["ink"])
fig.tight_layout()
save(fig, "L10-fixed-gain")
NUM["L10 K inf (2, 4.5)"] = f"{Kinf:.5f}"
NUM["L10 RMS step 1, KF vs fixed"] = f"{rk[1]:.3f} m, {rf[1]:.3f} m"
NUM["L10 RMS mean steps 20-39, KF vs fixed, sqrt(P inf)"] = f"{rk[20:].mean():.3f} m, {rf[20:].mean():.3f} m, {np.sqrt(Pinf):.3f} m"
for lab, rp, qm in [("dog p.143", 1, 2), ("thermometer p.156", 0.05**2, 0.13**2), ("extreme p.159", 2, 300.0**2),
                    ("bad Q p.160", 0.001, 20), ("bad init p.161", 2, 25), ("large noise p.162", 2, 30000)]:
    NUM[f"L10 K inf {lab}"] = f"{p_inf(rp, qm) / qm:.5f}"

# ================================================================== nonlinear exercise numbers (pp. 165–167), no figure
offs = {}
for u in (1.0, 0.0):
    o = []
    for s in range(200):
        rng = np.random.default_rng(7000 + s)
        i = np.arange(100)
        truth_s = np.sin(i / 3.0) * 2
        zz = truth_s + rng.normal(size=100) * 1.2
        r = run_kf(zz, 100.0, 500.0, u, 2.0, 30.0)
        o.append((r["x"][50:] - truth_s[50:]).mean())
    offs[u] = np.mean(o)
NUM["nonlinear mean offset steps 50-99, 200 seeds: u=1, u=0"] = f"{offs[1.0]:+.2f}, {offs[0.0]:+.2f}"
_k = p_inf(2, 30) / 30
NUM["nonlinear steady offset u(1-K inf)/K inf (u=1, R_proc=2, Q_meas=30)"] = f"{(1 - _k) / _k:+.2f}"

print("NUMBERS")
for key, val in NUM.items():
    print(f"  {key}: {val}")
