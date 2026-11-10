"""Generate the lecture figures for ch. 3 in the Chalk style. Run from the package folder:
    python figures/make_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from viz.py import style  # noqa: E402

OUT = Path(__file__).resolve().parent
P = style.use("light")
R = style.ROLE
rng = np.random.default_rng(3)


def gauss(x, m, s):
    return np.exp(-0.5 * ((x - m) / s) ** 2) / (s * np.sqrt(2 * np.pi))


# L1: one blob, two parameterizations
fig, ax = plt.subplots(figsize=(5.2, 3.6))
mu = np.array([1.0, 0.6])
Sig = np.array([[0.9, 0.5], [0.5, 0.5]])
pts = rng.multivariate_normal(mu, Sig, 400)
ax.scatter(pts[:, 0], pts[:, 1], s=6, color=R["gray"], alpha=0.35, lw=0)
style.cov_ellipse(ax, mu, Sig, n_std=1, role="blue")
style.cov_ellipse(ax, mu, Sig, n_std=2, role="blue", fill_alpha=0.06)
ax.plot(*mu, "o", color=R["blue"], ms=5)
ax.annotate("μ", mu + [0.08, 0.1], color=P["ink"])
ax.annotate("1σ, 2σ of Σ", (mu[0] + 1.6, mu[1] + 1.0), color=P["muted"], fontsize=9)
ax.text(-1.9, 2.4, "moments: (μ, Σ)\ncanonical: Ω = Σ⁻¹,  ξ = Σ⁻¹μ", fontsize=9, color=P["muted"], family="monospace")
ax.set_xlim(-2, 4.2); ax.set_ylim(-1.6, 2.9); ax.set_aspect("equal")
ax.set_xlabel("x₁"); ax.set_ylabel("x₂")
style.fig_label(ax, "Fig L1 · 3.1", "A Gaussian belief is one ellipse: a centre and a shape")
fig.savefig(OUT / "L1-gaussian-belief.svg"); fig.savefig(OUT / "L1-gaussian-belief.png", format="png", dpi=110)

# L2: predict widens, update narrows (1-D, after Fig 3.2)
x = np.linspace(-2, 14, 600)
fig, axes = plt.subplots(1, 3, figsize=(9, 2.6), sharey=True)
m0, s0 = 2.0, 1.0
m1, s1 = m0 + 5.0, np.sqrt(s0**2 + 1.5**2)
z, sz = 8.0, 1.0
k = s1**2 / (s1**2 + sz**2)
m2, s2 = m1 + k * (z - m1), np.sqrt((1 - k) * s1**2)
for ax, (title, curves) in zip(axes, [
    ("prior bel(x₀)", [(m0, s0, "blue", "prior")]),
    ("predict: motion u = 5", [(m0, s0, "gray", "prior"), (m1, s1, "blue", "predicted  Σ̄ = AΣAᵀ+R")]),
    ("update: measurement z = 8", [(m1, s1, "gray", "predicted"), (z, sz, "coral", "measurement"), (m2, s2, "teal", "posterior")]),
]):
    for m, s, role, lab in curves:
        ax.plot(x, gauss(x, m, s), color=R[role], lw=1.6 if role != "gray" else 1.0, label=lab, ls="-" if role != "gray" else "--")
    ax.set_title(title, loc="left", fontsize=10, color=P["ink"])
    ax.legend(fontsize=7.5, loc="upper left")
    ax.set_xlabel("x [m]")
    ax.set_yticks([])
axes[0].set_ylabel("density")
fig.suptitle("Fig L2 · 3.2  Predict widens the belief, update narrows it", x=0.01, ha="left", fontsize=11, color=P["ink"])
fig.tight_layout()
fig.savefig(OUT / "L2-predict-update.svg"); fig.savefig(OUT / "L2-predict-update.png", format="png", dpi=110)

# L3: linearization (after Fig 3.3b / 3.4)
g = lambda x: 4.0 + 1.6 * np.tanh(1.3 * (x - 3.0)) - 0.15 * (x - 3.0)
xs = np.linspace(0, 6, 500)
mx, sx = 3.3, 0.9
samples = rng.normal(mx, sx, 200000)
ys = g(samples)
eps = 1e-5
slope = (g(mx + eps) - g(mx - eps)) / (2 * eps)
tangent = g(mx) + slope * (xs - mx)
fig = plt.figure(figsize=(7.2, 5.2))
gs = fig.add_gridspec(2, 2, width_ratios=[1.4, 2.2], height_ratios=[2.2, 1], hspace=0.08, wspace=0.08)
axy = fig.add_subplot(gs[0, 0]); axg = fig.add_subplot(gs[0, 1]); axx = fig.add_subplot(gs[1, 1])
axg.plot(xs, g(xs), color=P["ink"], lw=1.6, label="g(x)")
axg.plot(xs, tangent, color=R["blue"], lw=1.4, ls="--", label="tangent at μ")
axg.axvline(mx, color=P["grid"], lw=0.8, ls=":")
axg.axhline(g(mx), color=P["grid"], lw=0.8, ls=":")
axg.plot(mx, g(mx), "o", color=R["blue"], ms=5)
axg.set_xlim(0, 6); axg.set_ylim(1.5, 6.5); axg.set_xticklabels([]); axg.legend(loc="lower right")
axx.plot(xs, gauss(xs, mx, sx), color=R["blue"], lw=1.6); axx.fill_between(xs, gauss(xs, mx, sx), color=R["blue"], alpha=0.12)
axx.set_xlim(0, 6); axx.set_yticks([]); axx.set_xlabel("x  (input)")
yy = np.linspace(1.5, 6.5, 500)
hist, edges = np.histogram(ys, bins=160, range=(1.5, 6.5), density=True)
axy.fill_betweenx(0.5 * (edges[1:] + edges[:-1]), hist, color=R["teal"], alpha=0.25, label="true p(y)")
axy.plot(gauss(yy, ys.mean(), ys.std()), yy, color=R["teal"], lw=1.4, label="Gaussian fit of p(y)")
axy.plot(gauss(yy, g(mx), abs(slope) * sx), yy, color=R["blue"], lw=1.4, ls="--", label="EKF Gaussian")
axy.set_ylim(1.5, 6.5); axy.set_xticks([]); axy.invert_xaxis(); axy.set_ylabel("y = g(x)  (output)"); axy.legend(fontsize=7.5, loc="upper left")
axy.set_title("Fig L3 · 3.3–3.4  The tangent's Gaussian (dashed) misses the true output (solid)", loc="left", fontsize=10.5, color=P["ink"], pad=10)
fig.savefig(OUT / "L3-linearization.svg"); fig.savefig(OUT / "L3-linearization.png", format="png", dpi=110)

# L4: sigma points through the same g
n = 1; alpha, beta, kappa = 1.0, 2.0, 2.0
lam = alpha**2 * (n + kappa) - n
gam = np.sqrt(n + lam)
sp = np.array([mx, mx + gam * sx, mx - gam * sx])
wm = np.array([lam / (n + lam), 1 / (2 * (n + lam)), 1 / (2 * (n + lam))])
wc = wm.copy(); wc[0] += 1 - alpha**2 + beta
Y = g(sp)
mu_u = wm @ Y
var_u = wc @ (Y - mu_u) ** 2
fig = plt.figure(figsize=(7.2, 5.2))
gs = fig.add_gridspec(2, 2, width_ratios=[1.4, 2.2], height_ratios=[2.2, 1], hspace=0.08, wspace=0.08)
axy = fig.add_subplot(gs[0, 0]); axg = fig.add_subplot(gs[0, 1]); axx = fig.add_subplot(gs[1, 1])
axg.plot(xs, g(xs), color=P["ink"], lw=1.6, label="g(x)")
for s_, y_ in zip(sp, Y):
    axg.plot([s_, s_], [1.5, y_], color=P["grid"], lw=0.8, ls=":")
    axg.plot([0, s_], [y_, y_], color=P["grid"], lw=0.8, ls=":")
axg.plot(sp, Y, "o", color=R["coral"], ms=6, label="g(sigma points)")
axg.set_xlim(0, 6); axg.set_ylim(1.5, 6.5); axg.set_xticklabels([]); axg.legend(loc="lower right")
axx.plot(xs, gauss(xs, mx, sx), color=R["blue"], lw=1.6); axx.fill_between(xs, gauss(xs, mx, sx), color=R["blue"], alpha=0.12)
axx.plot(sp, gauss(sp, mx, sx), "x", color=R["coral"], ms=8, mew=2, label="sigma points X")
axx.set_xlim(0, 6); axx.set_yticks([]); axx.set_xlabel("x  (input)"); axx.legend(loc="upper right", fontsize=8)
axy.fill_betweenx(0.5 * (edges[1:] + edges[:-1]), hist, color=R["teal"], alpha=0.25, label="true p(y)")
axy.plot(gauss(yy, ys.mean(), ys.std()), yy, color=R["teal"], lw=1.4, label="Gaussian fit of p(y)")
axy.plot(gauss(yy, mu_u, np.sqrt(var_u)), yy, color=R["coral"], lw=1.4, ls="--", label="UKF Gaussian")
axy.plot(gauss(yy, g(mx), abs(slope) * sx), yy, color=R["blue"], lw=1.0, ls=":", label="EKF Gaussian")
axy.set_ylim(1.5, 6.5); axy.set_xticks([]); axy.invert_xaxis(); axy.set_ylabel("y = g(x)  (output)"); axy.legend(fontsize=7.5, loc="upper left")
axy.set_title("Fig L4 · 3.4  Sigma points see the curvature; the tangent does not", loc="left", fontsize=10.5, color=P["ink"], pad=10)
fig.savefig(OUT / "L4-sigma-points.svg"); fig.savefig(OUT / "L4-sigma-points.png", format="png", dpi=110)

# L5: duality table as a figure
fig, ax = plt.subplots(figsize=(6.4, 2.6))
ax.axis("off")
rows = [("", "Kalman filter (μ, Σ)", "Information filter (ξ, Ω)"),
        ("predict", "μ̄ = Aμ + Bu\nΣ̄ = AΣAᵀ + R      cheap", "Ω̄ = (AΩ⁻¹Aᵀ + R)⁻¹   two inversions"),
        ("update", "K = Σ̄Cᵀ(CΣ̄Cᵀ+Q)⁻¹   invert k×k", "Ω += CᵀQ⁻¹C\nξ += CᵀQ⁻¹z          addition"),
        ("ignorance", "Σ = ∞   impossible", "Ω = 0   trivial"),
        ("sparsity", "Σ dense", "Ω sparse = factor graph")]
colors = [None, R["blue"], R["coral"], R["gray"], R["teal"]]
for i, (a, b, c) in enumerate(rows):
    y = 0.92 - i * 0.2
    w = "medium" if i == 0 else "normal"
    col = P["ink"] if i == 0 else (colors[i] if colors[i] else P["ink"])
    ax.text(0.0, y, a, fontsize=9.5, color=col, weight="medium", va="top")
    ax.text(0.17, y, b, fontsize=9, color=P["ink"], family="monospace", va="top", weight=w)
    ax.text(0.6, y, c, fontsize=9, color=P["ink"], family="monospace", va="top", weight=w)
    if i == 0:
        ax.plot([0, 1], [y - 0.05, y - 0.05], color=P["grid"], lw=0.8)
ax.set_title("Fig L5 · 3.5  What is cheap in one parameterization is expensive in the other", loc="left", fontsize=10.5, color=P["ink"])
fig.savefig(OUT / "L5-duality.svg"); fig.savefig(OUT / "L5-duality.png", format="png", dpi=110)
print("wrote", sorted(p.name for p in OUT.glob("*.svg")))
