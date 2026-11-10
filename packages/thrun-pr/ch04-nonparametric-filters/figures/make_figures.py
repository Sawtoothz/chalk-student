"""Generate the lecture figures for ch. 4 in the Chalk style. Run from anywhere:
    python figures/make_figures.py
Writes L*.svg / L*.png and numbers.json (every number quoted in lecture.md comes from that file).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from scipy.special import logsumexp  # noqa: E402
from scipy.stats import gaussian_kde  # noqa: E402

from viz.py import style  # noqa: E402

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG))
from exercises.models import RingCorridor  # noqa: E402
from exercises.solutions import T3_solution as ref  # noqa: E402

OUT = Path(__file__).resolve().parent
P = style.use("light")
R = style.ROLE
NUM: dict = {}


def gauss(x, m, s):
    return np.exp(-0.5 * ((x - m) / s) ** 2) / (s * np.sqrt(2 * np.pi))


def save(fig, name):
    fig.savefig(OUT / f"{name}.svg", pad_inches=0.15)
    fig.savefig(OUT / f"{name}.png", format="png", dpi=110, pad_inches=0.15)
    plt.close(fig)


def suptitle(fig, num, title):
    from matplotlib.transforms import offset_copy
    fig.text(0.01, 1.0, title, fontsize=12, color=P["ink"], weight="medium", va="bottom")
    fig.text(0.01, 1.0, num, fontsize=8.5, color=P["faint"], family="monospace", va="bottom",
             transform=offset_copy(fig.transFigure, fig=fig, y=20, units="points"))


# The one nonlinear function used by L1, L3, L8 (a stand-in for the book's g in Figs 4.1, 4.3, 4.6):
# two plateaus, so a Gaussian input comes out two-humped.
def g(x):
    return 2.0 + 0.9 * np.tanh(9.0 * (0.55 - x)) + 0.15 * np.sin(3.0 * x)


MX, SX = 0.55, 0.22  # input Gaussian

# ---------------------------------------------------------------------- L1
rng = np.random.default_rng(1)
ys_true = g(rng.normal(MX, SX, 400_000))
yy = np.linspace(0.6, 3.4, 600)
kde_true = gaussian_kde(ys_true[:40_000], bw_method=0.05)
py = kde_true(yy)
fig, axes = plt.subplots(1, 3, figsize=(10, 3.0), sharey=True)
mu_y, sd_y = ys_true.mean(), ys_true.std()
NUM["L1"] = {"mean_y": round(float(mu_y), 3), "density_at_mean_rel_peak": round(float(kde_true(mu_y)[0] / py.max()), 3)}
for ax in axes:
    ax.fill_between(yy, py, color=P["grid"], alpha=0.35, lw=0, label="true belief")
axes[0].plot(yy, gauss(yy, mu_y, sd_y), color=R["blue"], lw=1.6, label="Gaussian (μ, Σ)")
axes[0].axvline(mu_y, color=R["blue"], lw=0.8, ls=":")
axes[0].set_title("ch. 3: two numbers", fontsize=10, loc="left")
edges = np.linspace(0.6, 3.4, 15)
h, _ = np.histogram(ys_true, bins=edges, density=True)
axes[1].bar(edges[:-1], h, width=np.diff(edges), align="edge", color=R["teal"], alpha=0.35, edgecolor=R["teal"], lw=0.8, label="histogram, K = 14")
axes[1].set_title("4.1: probability per fixed bin", fontsize=10, loc="left")
sm = ys_true[:60]
axes[2].vlines(sm, 0, 0.25, color=R["teal"], lw=1.0, label="particles, M = 60")
axes[2].set_title("4.3: samples that move", fontsize=10, loc="left")
for ax in axes:
    ax.set_xlabel("y"); ax.legend(fontsize=7.5, loc="upper right"); ax.set_yticks([])
axes[0].set_ylabel("density")
suptitle(fig, "Fig L1 · ch. 4", "The Gaussian puts its mean where the belief has almost no mass")
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "L1-three-beliefs")

# ---------------------------------------------------------------------- L2  Table 4.1 on a ring corridor
RING = RingCorridor()  # system model from exercises/models.py
L, K = RING.L, 100
xc = (np.arange(K) + 0.5) * L / K
DOORS = RING.DOORS
ring_d, p_door, range_to_next_door = RING.ring_dist, RING.p_door, RING.range_to_next_door
T_L2 = ref.transition_from_density(xc, 2.5, lambda xn, u, xp: gauss(ring_d(xn, xp + u), 0, 0.3))  # (4.5), s = 0.3


b0 = np.full(K, 1 / K)
b1 = np.exp(ref.hist_update(np.log(b0), np.log(p_door(xc))))  # Table 4.1 line 4
b2 = ref.hist_predict(b1, T_L2)  # line 3
b3 = np.exp(ref.hist_update(np.log(b2), np.log(p_door(xc))))
mass_near = float(b3[ring_d(xc, 4.0) < 1.0].sum())
NUM["L2"] = {"mass_within_1m_of_4.0_after_two_doors": round(mass_near, 3), "K": K, "bin_m": L / K}
fig, axes = plt.subplots(1, 3, figsize=(10, 2.8), sharey=True)
for ax, b, title, lik in [
    (axes[0], b1, "line 4: first door seen", True),
    (axes[1], b2, "line 3: drive u = 2.5 m", False),
    (axes[2], b3, "line 4: second door seen", True),
]:
    ax.bar(xc, b, width=L / K, color=R["blue"], alpha=0.55, lw=0, label="bel / bel̄  (p_k)")
    if lik:
        ax.plot(xc, p_door(xc) * b.max() / 0.9, color=R["coral"], lw=1.2, label="p(z = door | x) (scaled)")
    for d in DOORS:
        ax.axvline(d, color=R["gray"], lw=0.8, ls=":")
    ax.set_title(title, fontsize=10, loc="left"); ax.set_xlabel("x along ring corridor [m]"); ax.set_yticks([])
    ax.legend(fontsize=7, loc="upper right")
axes[0].set_ylabel("p_k")
suptitle(fig, "Fig L2 · Table 4.1", "Doors seen 2.5 m apart: only the 4 m hypothesis explains both; line 3 is a shift plus a blur")
fig.tight_layout(rect=(0, 0, 1, 0.92))
save(fig, "L2-discrete-bayes")

# ---------------------------------------------------------------------- L3  (4.1)-(4.5), after Fig 4.1


def hist_through_g(Kx, pts_per_bin=200, Ky=40):
    e = np.linspace(MX - 3 * SX, MX + 3 * SX, Kx + 1)
    from scipy.stats import norm
    pk = np.diff(norm.cdf(e, MX, SX)); pk /= pk.sum()
    xs, ws = [], []
    for k in range(Kx):
        xx = np.linspace(e[k], e[k + 1], pts_per_bin)
        xs.append(xx); ws.append(np.full(pts_per_bin, pk[k] / pts_per_bin))
    xs, ws = np.concatenate(xs), np.concatenate(ws)
    ey = np.linspace(0.6, 3.4, Ky + 1)
    hy, _ = np.histogram(g(xs), bins=ey, weights=ws)
    return e, pk, ey, hy / np.diff(ey)


def tv_to_truth(ey, dens):
    ht, _ = np.histogram(ys_true, bins=ey, density=True)
    return 0.5 * float(np.sum(np.abs(dens - ht) * np.diff(ey)))


fig = plt.figure(figsize=(7.4, 5.2))
gs = fig.add_gridspec(2, 2, width_ratios=[1.4, 2.2], height_ratios=[2.2, 1], hspace=0.08, wspace=0.08)
axy = fig.add_subplot(gs[0, 0]); axg = fig.add_subplot(gs[0, 1]); axx = fig.add_subplot(gs[1, 1])
xs_ = np.linspace(MX - 3 * SX, MX + 3 * SX, 400)
e, pk, ey, hy = hist_through_g(10)
axg.plot(xs_, g(xs_), color=P["ink"], lw=1.6, label="g(x)")
for ee in e:
    axg.axvline(ee, color=P["grid"], lw=0.6, ls=":")
axg.set_xlim(xs_[0], xs_[-1]); axg.set_ylim(0.6, 3.4); axg.set_xticklabels([]); axg.legend(loc="upper right")
axx.fill_between(xs_, gauss(xs_, MX, SX), color=P["grid"], alpha=0.35, lw=0, label="p(x)")
axx.bar(e[:-1], pk / np.diff(e), width=np.diff(e), align="edge", color=R["blue"], alpha=0.35, edgecolor=R["blue"], lw=0.8, label="(4.2): p_k / |x_k|, K = 10")
axx.set_xlim(xs_[0], xs_[-1]); axx.set_yticks([]); axx.set_xlabel("x  (input)"); axx.legend(fontsize=7, loc="upper left")
axy.fill_betweenx(yy, py, color=P["grid"], alpha=0.35, lw=0, label="true p(y)")
axy.barh(ey[:-1], hy, height=np.diff(ey), align="edge", color=R["teal"], alpha=0.35, edgecolor=R["teal"], lw=0.8, label="histogram of y")
axy.set_ylim(0.6, 3.4); axy.set_xticks([]); axy.invert_xaxis(); axy.set_ylabel("y = g(x)  (output)"); axy.legend(fontsize=7, loc="upper left")
axy.set_title("Fig L3 · 4.1–4.5  Ten bins carry a two-humped output through g", loc="left", fontsize=10.5, color=P["ink"], pad=10)
NUM["L3"] = {f"TV_K{k}": round(tv_to_truth(*hist_through_g(k)[2:]), 3) for k in (5, 10, 40)}
save(fig, "L3-histogram-transform")

# ---------------------------------------------------------------------- L4  Table 4.2, (4.13)-(4.21)
rng = np.random.default_rng(4)
T4 = 30
hits = rng.random(T4) < 0.55
p_inv = np.where(hits, 0.6, 0.15)  # inverse model p(x | z_t)
lo = ref.prob_to_logodds  # (4.13)
prior = 0.3
l_ok, l_bad = [lo(prior)], [lo(prior)]
for pz in p_inv:
    l_ok.append(float(ref.logodds_update(l_ok[-1], pz, lo(prior))))  # Table 4.2 line 2
    l_bad.append(l_bad[-1] + lo(pz))  # deliberate bug for contrast: forgot "- log prior odds"
l_ok, l_bad = np.array(l_ok), np.array(l_bad)
# oracle: Table 4.1 on two states with the forward model implied by the inverse one, p(z|x) ∝ p(x|z)/p(x)
pb = np.array([prior, 1 - prior])
for pz in p_inv:
    pb = np.array([pz / prior, (1 - pz) / (1 - prior)]) * pb; pb /= pb.sum()
NUM["L4"] = {"bel_logodds_T": round(float(ref.logodds_to_prob(l_ok[-1])), 4), "bel_two_state_T": round(float(pb[0]), 4),
             "bel_forgot_prior_T": round(float(ref.logodds_to_prob(l_bad[-1])), 4), "T": T4, "hits": int(hits.sum()), "prior": prior}
fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.0))
t = np.arange(T4 + 1)
axes[0].step(t, l_ok, where="post", color=R["teal"], lw=1.6, label="Table 4.2 (subtract l₀)")
axes[0].step(t, l_bad, where="post", color=R["coral"], lw=1.3, ls="--", label="forgot − l₀")
axes[0].axhline(0, color=P["grid"], lw=0.8)
axes[0].set_xlabel("measurement t"); axes[0].set_ylabel("l_t  (log odds)")
axes[0].set_title("log odds: a sum, never saturates", fontsize=10, loc="left")
axes[1].step(t, ref.logodds_to_prob(l_ok), where="post", color=R["teal"], lw=1.6, label="bel_t(x) via (4.14)")
axes[1].step(t, ref.logodds_to_prob(l_bad), where="post", color=R["coral"], lw=1.3, ls="--", label="forgot − l₀")
axes[1].axhline(prior, color=R["gray"], lw=0.8, ls=":", label=f"prior p(x) = {prior}")
axes[1].set_ylim(-0.02, 1.02); axes[1].set_xlabel("measurement t"); axes[1].set_ylabel("probability")
fig.legend(*axes[1].get_legend_handles_labels(), loc="lower center", ncol=3, fontsize=8.5)
axes[1].set_title("probability: pinned near 0 or 1", fontsize=10, loc="left")
suptitle(fig, "Fig L4 · Table 4.2", "Every update adds the inverse model's log odds and takes the prior's back out")
fig.tight_layout(rect=(0, 0.08, 1, 0.9))
save(fig, "L4-log-odds")

# ---------------------------------------------------------------------- L5  one pass of Table 4.3
rng = np.random.default_rng(5)
M5 = 60
x_prev = rng.normal(0.0, 1.0, M5)
u5, sq5, z5, sz5 = 2.0, 0.5, 2.8, 0.4
x_bar = x_prev + u5 + rng.normal(0, sq5, M5)  # line 4
logw = -0.5 * ((z5 - x_bar) / sz5) ** 2  # line 5, in log space
w = np.exp(logw - logsumexp(logw))
idx = rng.choice(M5, size=M5, p=w)  # lines 8-11, multinomial as in the table
x_new = x_bar[idx]
# KF posterior for this linear-Gaussian case: the oracle
s2 = 1.0 + sq5**2
k5 = s2 / (s2 + sz5**2)
kf_m, kf_s = u5 + k5 * (z5 - u5), np.sqrt((1 - k5) * s2)
NUM["L5"] = {"M": M5, "distinct_after_resample": int(len(np.unique(idx))), "pf_mean": round(float(x_new.mean()), 3),
             "kf_mean": round(float(kf_m), 3), "kf_std": round(float(kf_s), 3), "pf_std": round(float(x_new.std()), 3)}
fig, axes = plt.subplots(3, 1, figsize=(8, 5.6), sharex=True)
xx = np.linspace(-3, 6, 500)
axes[0].vlines(x_prev, 0, 1, color=R["gray"], lw=0.9, label="particles at t − 1")
axes[0].vlines(x_bar, 1.2, 2.2, color=R["blue"], lw=0.9, label="line 4: each one sampled from the motion model")
axes[0].set_yticks([]); axes[0].legend(fontsize=7.5, loc="upper left", ncol=2); axes[0].set_ylim(0, 3.2)
axes[0].set_title("predict: every particle moves and spreads", fontsize=10, loc="left")
axes[1].vlines(x_bar, 0, w / w.max(), color=R["teal"], lw=1.4, label="line 5: w ∝ p(z_t | x_t)")
axes[1].plot(xx, np.exp(-0.5 * ((z5 - xx) / sz5) ** 2), color=R["coral"], lw=1.2, label="likelihood of z_t = 2.8")
axes[1].set_yticks([]); axes[1].legend(fontsize=7.5, loc="upper left"); axes[1].set_ylim(0, 1.35)
axes[1].set_title("weight: nothing moves, each particle gets a number", fontsize=10, loc="left")
u_, c_ = np.unique(x_new, return_counts=True)
for xv, cv in zip(u_, c_):
    axes[2].plot(np.full(cv, xv), 0.12 * np.arange(1, cv + 1), "o", color=R["teal"], ms=3.2)
axes[2].plot(xx, gauss(xx, kf_m, kf_s) / gauss(kf_m, kf_m, kf_s) * 1.0, color=R["blue"], lw=1.2, ls="--", label="exact posterior (KF)")
axes[2].set_yticks([]); axes[2].legend(fontsize=7.5, loc="upper left"); axes[2].set_xlabel("x"); axes[2].set_ylim(0, 1.6)
axes[2].set_title("resample: draw M with replacement; heavy particles are copied, light ones vanish", fontsize=10, loc="left")
suptitle(fig, "Fig L5 · Table 4.3", "Weighting moves no particle; resampling moves the set")
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "L5-particle-step")

# ---------------------------------------------------------------------- L6  (4.25)-(4.28), after Fig 4.4
f_pdf = lambda x: 0.55 * gauss(x, 2.0, 0.6) + 0.45 * gauss(x, 4.5, 1.4)
g_book_pdf = lambda x: 0.12 * ((x > 0) & (x < 12)) / 12 + 0.88 * gauss(x, 9.0, 1.0)


def g_book_sample(n, r):
    u = r.random(n) < 0.12
    return np.where(u, r.uniform(0, 12, n), r.normal(9.0, 1.0, n))


g_good_pdf = lambda x: gauss(x, 3.5, 2.0)
g_good_sample = lambda n, r: r.normal(3.5, 2.0, n)
g_bad_pdf = lambda x: gauss(x, 9.0, 1.0)  # violates f > 0 => g > 0 in practice
g_bad_sample = lambda n, r: r.normal(9.0, 1.0, n)
from scipy.stats import norm
P_true = 0.55 * norm.cdf(3.0, 2.0, 0.6) + 0.45 * norm.cdf(3.0, 4.5, 1.4) - (0.55 * norm.cdf(0, 2, 0.6) + 0.45 * norm.cdf(0, 4.5, 1.4))


def is_estimate(xs, f, gq):
    est, _ = ref.is_estimate(xs, lambda x: np.log(f(x)), lambda x: np.log(gq(x)), lambda x: (x > 0) & (x < 3))  # (4.28), A = (0, 3)
    return est


rng = np.random.default_rng(6)
Ms = np.array([10, 30, 100, 300, 1000, 3000])
rmse = {}
for name, smp, pdf in [("good", g_good_sample, g_good_pdf), ("book", g_book_sample, g_book_pdf), ("bad", g_bad_sample, g_bad_pdf)]:
    rmse[name] = [float(np.sqrt(np.mean([(is_estimate(smp(m, rng), f_pdf, pdf) - P_true) ** 2 for _ in range(400)]))) for m in Ms]
NUM["L6"] = {"P_true": round(float(P_true), 4), "M": Ms.tolist(), **{f"rmse_{k}": [round(v, 4) for v in vs] for k, vs in rmse.items()}}
fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.4), gridspec_kw={"width_ratios": [1.5, 1]})
xx = np.linspace(0, 12, 600)
rng = np.random.default_rng(66)
xs6 = g_book_sample(120, rng)
w6 = f_pdf(xs6) / g_book_pdf(xs6)
axes[0].plot(xx, f_pdf(xx), color=R["blue"], lw=1.6, label="target f = bel(x_t)")
axes[0].plot(xx, g_book_pdf(xx), color=R["gray"], lw=1.4, label="proposal g = bel̄(x_t)")
axes[0].vlines(xs6, -0.115, -0.095, color=R["gray"], lw=0.7, label="120 samples of g")
axes[0].vlines(xs6, -0.085, -0.085 + 0.13 * w6 / w6.max(), color=R["teal"], lw=1.4, label="weight w = f/g (4.27)")
axes[0].axhline(0, color=P["grid"], lw=0.8); axes[0].set_xlabel("x"); axes[0].set_yticks([]); axes[0].legend(fontsize=7.5, loc="upper right")
axes[0].set_title("most samples land where f is small and get tiny weights", fontsize=10, loc="left")
for name, role, ls, lab in [("good", "teal", "-", "g covers f"), ("book", "gray", "-", "g as in Fig 4.4"), ("bad", "amber", "--", "g = N(9, 1): f > 0 ⇏ g > 0")]:
    axes[1].loglog(Ms, rmse[name], "o" + ls, color=R[role], ms=4, lw=1.3, label=lab)
axes[1].loglog(Ms, rmse["good"][0] * np.sqrt(Ms[0] / Ms), color=P["grid"], lw=0.8, ls=":", label="∝ 1/√M")
axes[1].set_xlabel("M"); axes[1].set_ylabel("RMSE of P(x ∈ A) under f"); axes[1].legend(fontsize=7.5, loc="lower left")
axes[1].set_title("(4.28): same rate, constant set by f vs g", fontsize=10, loc="left")
suptitle(fig, "Fig L6 · 4.25–4.28, Fig 4.4", "Importance sampling is exact on average; the proposal decides how many samples it costs")
fig.tight_layout(rect=(0, 0, 1, 0.9))
save(fig, "L6-importance-sampling")

# ---------------------------------------------------------------------- L7  path space (4.30)-(4.35)
rng = np.random.default_rng(7)
M7, T7 = 40, 30
X = np.zeros((T7 + 1, M7)); A = np.zeros((T7 + 1, M7), dtype=int)
X[0] = rng.normal(0, 1, M7); A[0] = np.arange(M7)
truth = np.cumsum(np.r_[0.0, rng.normal(0, 0.3, T7)])
for t in range(1, T7 + 1):
    xb = X[t - 1] + rng.normal(0, 0.3, M7)
    lw_ = -0.5 * ((truth[t] + rng.normal(0, 0.5) - xb) / 0.5) ** 2
    ww = np.exp(lw_ - logsumexp(lw_))
    a = rng.choice(M7, M7, p=ww)
    X[t] = xb[a]; A[t] = a
# trace ancestry of the final set
alive = [np.arange(M7)]
for t in range(T7, 0, -1):
    alive.append(np.unique(A[t][alive[-1]]))
alive = alive[::-1]  # alive[t] = indices at time t that have descendants at T
n_alive = [len(a) for a in alive]
NUM["L7"] = {"M": M7, "T": T7, "ancestors_at_t0": n_alive[0], "distinct_at_T_minus_10": n_alive[T7 - 10]}
fig, ax = plt.subplots(figsize=(8.2, 3.4))
for t in range(T7 + 1):
    ax.plot(np.full(M7, t), X[t], ".", color=R["gray"], ms=2.5, alpha=0.6)
for t in range(1, T7 + 1):
    for m in range(M7):
        p_ = A[t][m]
        on = p_ in set(alive[t - 1]) and m in set(alive[t])
        if on:
            ax.plot([t - 1, t], [X[t - 1][p_], X[t][m]], color=R["teal"], lw=0.9)
ax.plot(np.arange(T7 + 1), truth, color=P["ink"], lw=1.0, ls="--", label="true x_t")
ax.plot([], [], color=R["teal"], label="paths x0:t that survive to t = 30")
ax.plot([], [], ".", color=R["gray"], label="particles at each t")
ax.set_xlabel("t"); ax.set_ylabel("x"); ax.legend(fontsize=7.5, loc="lower left")
style.fig_label(ax, "Fig L7 · 4.30–4.35", "Every particle carries a path; resampling prunes the old part to a few trunks")
save(fig, "L7-path-space")

# ---------------------------------------------------------------------- L8  sampling variance, after Fig 4.6
rng = np.random.default_rng(8)
fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.0), sharey=True)
for ax, m in zip(axes, (25, 250)):
    ax.fill_between(yy, py, color=P["grid"], alpha=0.35, lw=0, label="true p(y)")
    for r_ in range(3):
        s = g(rng.normal(MX, SX, m))
        ax.plot(yy, gaussian_kde(s, bw_method=0.15)(yy), color=R["teal"], lw=1.1, alpha=0.9, label="KDE of one run" if r_ == 0 else None)
    ax.set_title(f"M = {m}, three independent runs", fontsize=10, loc="left"); ax.set_xlabel("y"); ax.set_yticks([])
    ax.legend(fontsize=7.5, loc="upper right")
sd = {m: float(np.std([g(rng.normal(MX, SX, m)).mean() for _ in range(4000)])) for m in (25, 250, 2500)}
NUM["L8"] = {f"sd_of_mean_M{m}": round(v, 4) for m, v in sd.items()} | {"ratio_25_250": round(sd[25] / sd[250], 2)}
suptitle(fig, "Fig L8 · Fig 4.6", "Same belief, same g, different random numbers: the estimate is itself a random variable")
fig.tight_layout(rect=(0, 0, 1, 0.9))
save(fig, "L8-sampling-variance")

# ---------------------------------------------------------------------- L9  resampling: diversity loss and Table 4.4


def multinomial(w, r):  # book as printed, for contrast (Table 4.3 lines 8-11)
    return r.choice(len(w), len(w), p=w)


low_variance = ref.low_variance_resample  # Table 4.4


rng = np.random.default_rng(9)
M9, T9, runs = 100, 200, 40
dist = {"multi": np.zeros(T9 + 1), "lv": np.zeros(T9 + 1)}
for _ in range(runs):
    for k, fn in (("multi", multinomial), ("lv", low_variance)):
        ids = np.arange(M9)
        dist[k][0] += M9
        for t in range(1, T9 + 1):
            ids = ids[fn(np.full(M9, 1 / M9), rng)]
            dist[k][t] += len(np.unique(ids))
for k in dist:
    dist[k] /= runs
NUM["L9"] = {"M": M9, "runs": runs, "distinct_multinomial_t10": round(float(dist["multi"][10]), 1),
             "distinct_multinomial_t100": round(float(dist["multi"][100]), 1), "distinct_multinomial_t200": round(float(dist["multi"][200]), 1),
             "distinct_lowvar_t200": round(float(dist["lv"][200]), 1)}
fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.2), gridspec_kw={"width_ratios": [1, 1.25]})
axes[0].plot(dist["multi"], color=R["coral"], lw=1.6, label="multinomial (Table 4.3 lines 8–11)")
axes[0].plot(dist["lv"], color=R["teal"], lw=1.6, label="low variance (Table 4.4), and (4.36): both stay at M")
axes[0].set_xlabel("resampling steps (x_t = x_t−1, no sensor)"); axes[0].set_ylabel("distinct particles"); axes[0].set_ylim(0, 108)
axes[0].legend(fontsize=7.5, loc="center right")
axes[0].set_title("static state, equal weights, M = 100", fontsize=10, loc="left")
rng = np.random.default_rng(91)
w9 = rng.gamma(1.0, 1.0, 8); w9 /= w9.sum()
c9 = np.r_[0, np.cumsum(w9)]
r9 = 0.06
ax = axes[1]
for i in range(8):
    ax.add_patch(plt.Rectangle((c9[i], 0.4), w9[i], 0.35, facecolor=R["blue"], alpha=0.15 + 0.5 * w9[i] / w9.max(), edgecolor=P["edge"], lw=0.6))
    if w9[i] > 0.06:
        ax.text(c9[i] + w9[i] / 2, 0.575, f"w[{i+1}]", ha="center", va="center", fontsize=7.5, color=P["ink"])
Uc = r9 + np.arange(8) / 8
pick = np.searchsorted(np.cumsum(w9), Uc)
for m, u_ in enumerate(Uc):
    ax.annotate("", xy=(u_, 0.4), xytext=(u_, 0.12), arrowprops=dict(arrowstyle="-|>", color=R["teal"], lw=1.2))
    ax.text(u_, 0.04, f"{pick[m]+1}", ha="center", fontsize=7.5, color=R["teal_deep"])
ax.text(0, 0.86, "U = r + (m−1)/M, one random r ∈ [0, 1/M); arrow → index i of (4.37)", fontsize=8, color=P["muted"])
ax.set_xlim(-0.01, 1.01); ax.set_ylim(0, 0.95); ax.set_yticks([]); ax.grid(False); ax.set_xlabel("cumulative weight")
ax.set_title("Table 4.4: one comb, M teeth, O(M)", fontsize=10, loc="left")
suptitle(fig, "Fig L9 · (4.36), Table 4.4, Fig 4.7", "Resampling with no information destroys diversity; the comb does it least")
fig.tight_layout(rect=(0, 0, 1, 0.9))
save(fig, "L9-resampling")

# ---------------------------------------------------------------------- L10  bias (4.38)
rng = np.random.default_rng(10)
z10 = 2.0  # prior N(0,1), likelihood N(z; x, 1): exact posterior mean 1.0
Ms10 = [1, 2, 3, 5, 10, 30, 100]
runs10 = 40_000
est = []
for m in Ms10:
    x = rng.normal(0, 1, (runs10, m))
    lw_ = -0.5 * (z10 - x) ** 2
    ww = np.exp(lw_ - logsumexp(lw_, axis=1, keepdims=True))
    est.append(float(np.mean(np.sum(ww * x, axis=1))))  # E[mean after resampling] = E[weighted mean]
NUM["L10"] = {"exact_mean": 1.0, "M": Ms10, "E_estimate": [round(v, 3) for v in est], "runs": runs10}
fig, ax = plt.subplots(figsize=(6.4, 3.2))
ax.semilogx(Ms10, est, "o-", color=R["teal"], lw=1.5, label="E[PF mean after one update]")
ax.axhline(1.0, color=R["blue"], lw=1.2, ls="--", label="exact posterior mean (KF)")
ax.axhline(0.0, color=R["gray"], lw=0.8, ls=":", label="prior mean: what M = 1 returns")
ax.set_xlabel("M"); ax.set_ylabel("mean of x_t"); ax.legend(fontsize=7.5, loc="center right"); ax.set_ylim(-0.1, 1.15)
style.fig_label(ax, "Fig L10 · 4.38", "With M = 1 the measurement is ignored; the bias shrinks like 1/M")
save(fig, "L10-sampling-bias")

# ---------------------------------------------------------------------- L11  deprivation and random injection
rng = np.random.default_rng(11)


def run_kidnap(inject, seed, M=300, T=80, t_kid=30):
    r = np.random.default_rng(seed)
    xt = 0.3
    parts = r.normal(xt, 0.1, M) % L
    err = []
    for t in range(T):
        xt = (xt + 0.5 + r.normal(0, 0.02)) % L
        if t == t_kid:
            xt = (xt + 5.0) % L
        parts = (parts + 0.5 + r.normal(0, 0.05, M)) % L
        z = range_to_next_door(xt) + r.normal(0, 0.1)
        dz = z - range_to_next_door(parts)
        lw_ = np.logaddexp(-0.5 * (dz / 0.1) ** 2, np.log(1e-3))  # small floor for outliers, as ch. 6 does
        ww = np.exp(lw_ - logsumexp(lw_))
        parts = parts[low_variance(ww, r)]
        if inject:
            n = int(0.02 * M)
            parts[r.choice(M, n, replace=False)] = r.uniform(0, L, n)
        # circular mean as the estimate
        est_ = (np.angle(np.mean(np.exp(2j * np.pi * parts / L))) / (2 * np.pi) * L) % L
        err.append(float(ring_d(est_, xt)))
    return np.array(err)


E0 = np.array([run_kidnap(False, s) for s in range(20)])
E1 = np.array([run_kidnap(True, s) for s in range(20)])
med0, med1 = np.median(E0, axis=0), np.median(E1, axis=0)
rec = lambda e: next((t - 30 for t in range(31, len(e)) if np.all(e[t:] < 0.3)), None)
NUM["L11"] = {"runs": 20, "M": 300, "inject_frac": 0.02, "kidnap_m": 5.0,
              "recovered_no_injection": int(sum(rec(e) is not None for e in E0)),
              "recovered_injection": int(sum(rec(e) is not None for e in E1)),
              "median_steps_to_recover_injection": float(np.median([rec(e) for e in E1 if rec(e) is not None])) if any(rec(e) is not None for e in E1) else None,
              "median_err_before_kidnap": round(float(np.median(E0[:, 10:30])), 3)}
fig, ax = plt.subplots(figsize=(7.2, 3.2))
ax.plot(med0, color=R["coral"], lw=1.6, label="no injection")
ax.plot(med1, color=R["teal"], lw=1.6, label="2% random particles after each resample")
ax.axvline(30, color=R["amber"], lw=1.0, ls=":")
ax.text(30.5, 4.4, "kidnap: +5 m", color=R["amber"], fontsize=8.5)
ax.set_xlabel("t"); ax.set_ylabel("median |error| [m], 20 runs"); ax.legend(fontsize=7.5, loc="center right"); ax.set_ylim(-0.1, 5.2)
style.fig_label(ax, "Fig L11 · p. 112–113", "After a kidnap no particle is near the truth; only injected particles can find it")
save(fig, "L11-deprivation")

(OUT / "numbers.json").write_text(json.dumps(NUM, indent=1))
print(json.dumps(NUM, indent=1))
print("wrote", sorted(p.name for p in OUT.glob("*.png")))
