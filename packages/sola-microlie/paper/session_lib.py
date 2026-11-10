"""Numbers behind the four session figures (session.py, interactive.html).

No plotting here: each `fig_*` returns the arrays a figure draws plus the readout tiles, computed from the
reference solution (or from your exercise.py when `ex` is your module). `figures/session_core.js` is the same
model in plain JS; `figures/compare_session.py` checks that the two agree on the default settings.
"""

from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path

import numpy as np

from exercises.models import pose, se2_Exp_ref

DATA = Path(__file__).resolve().parent / "exercises" / "data"
CHI2_2_95, CHI2_3_95 = 5.991464547107979, 7.814727903251179

# ---------------------------------------------------------------- shared deterministic RNG (same bits as the JS)


def make_rng(seed):
    s = [(seed & 0xFFFFFFFF) or 1]

    def r():
        x = s[0]
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        s[0] = x
        return x / 4294967296

    return r


def randn(r):
    u = v = 0.0
    while u == 0:
        u = r()
    while v == 0:
        v = r()
    return math.sqrt(-2 * math.log(u)) * math.cos(2 * math.pi * v)


# ---------------------------------------------------------------- Fig 2.6a: right and left perturbation, eq. (25), (31), (75)


def fig_a(ex, xX=1.5, thX_deg=40.0, rho1=0.8, th_deg=50.0):
    X = pose(xX, 1.0, math.radians(thX_deg))
    tau = np.array([rho1, 0.2, math.radians(th_deg)])
    right = X @ ex.se2_exp(tau)                                   # X ⊕ τ (25)
    wrong = ex.se2_exp(tau) @ X                                   # the same τ applied on the left
    left = ex.se2_exp(ex.se2_Ad(X) @ tau) @ X                     # Exp(Ad_X τ) X: the same τ, moved to the global frame
    s = np.linspace(0, 1, 41)
    p_right = np.array([(X @ ex.se2_exp(k * tau))[:2, 2] for k in s])
    p_wrong = np.array([(ex.se2_exp(k * tau) @ X)[:2, 2] for k in s])
    inv = float(np.linalg.norm(right - left))
    gap = float(np.linalg.norm(wrong[:2, 2] - right[:2, 2]))
    oracle = float(np.linalg.norm(ex.se2_exp(tau) - se2_Exp_ref(tau)))
    return dict(X=X, right=right, wrong=wrong, left=left, p_right=p_right, p_wrong=p_wrong,
                tiles={"‖(X ⊕ τ) − Exp(Ad_X τ)·X‖": "< 1e-12 ✓" if inv < 1e-12 else f"{inv:.1e}  ✗",
                       "position gap, right vs left τ": f"{gap:.2f} m",
                       "‖τ‖ / ‖Ad_X τ‖": f"{np.linalg.norm(tau):.2f} / {np.linalg.norm(ex.se2_Ad(X) @ tau):.2f}",
                       "Exp vs expm oracle": "< 1e-12 ✓" if oracle < 1e-12 else f"{oracle:.1e}  ✗"},
                special=gap < 1e-9)


# ---------------------------------------------------------------- Fig 2.6b: a Gaussian on the tangent, eq. (52), (55)

N_B = 1500


def fig_b(ex, ratio=0.35, sig_th_deg=20.0, th_mean_deg=30.0):
    st = math.radians(sig_th_deg)
    sd = np.array([0.5, 0.5 * ratio, st])
    Xb = pose(2.0, 1.0, math.radians(th_mean_deg))
    r = make_rng(7)
    pos = np.empty((N_B, 2))
    for i in range(N_B):
        eps = sd * np.array([randn(r), randn(r), randn(r)])
        pos[i] = (Xb @ ex.se2_exp(eps))[:2, 2]
    Rb, tb = Xb[:2, :2], Xb[:2, 2]
    q = (pos - tb) @ Rb                                           # body-frame offsets (along, lateral)
    inside = float(np.mean((q[:, 0] / sd[0]) ** 2 + (q[:, 1] / sd[1]) ** 2 <= CHI2_2_95))
    sa, sl = float(q[:, 0].std(ddof=1)), float(q[:, 1].std(ddof=1))
    return dict(Xb=Xb, pos=pos, sd=sd,
                tiles={"inside the linear 95 % ellipse (target 95 %)": f"{100 * inside:.1f} %",
                       "along-track std, cloud / ellipse": f"{sa / sd[0]:.2f}",
                       "lateral std, cloud / ellipse": f"{sl / sd[1]:.2f}",
                       "σ_θ": f"{st:.2f} rad"},
                inside=inside)


# ---------------------------------------------------------------- Fig 2.6c: tuning the ESKF on a T5 run, (99)–(102)

TAGS_GUESS = (0.02, 0.01)       # along-track and yaw sigma of the task-1 R_proc


def load_run(i):
    d = np.load(DATA / f"t5_run_{i}.npz")
    P0 = np.diag([0.05, 0.05, 0.02]) ** 2
    err = np.linalg.cholesky(P0) @ np.random.default_rng(i).normal(size=3)     # as in T5_reference.run
    return dict(truth=d["truth"], U=d["U"], Y=d["Y"], mask=d["mask"], tags=d["tags"], err0=err, P0=P0)


def fig_c(ex, run, sig_y=0.10, sig_slip_mm=1.0):
    Rp = np.diag([TAGS_GUESS[0], sig_slip_mm / 1000, TAGS_GUESS[1]]) ** 2
    Qm = np.eye(2) * sig_y ** 2
    X = pose(*run["truth"][0]) @ ex.se2_exp(run["err0"])
    P = run["P0"].copy()
    nees, nis, pos = [], [], []
    for k in range(len(run["U"])):
        X, P = ex.eskf_predict(X, P, run["U"][k], Rp)
        for j in np.flatnonzero(run["mask"][k]):
            X, P, z, Z = ex.eskf_update(X, P, run["Y"][k, j], run["tags"][j], Qm, reset=True)
            nis.append(float(z @ np.linalg.solve(Z, z)))
        e = ex.se2_rminus(pose(*run["truth"][k + 1]), X)[0]
        nees.append(float(e @ np.linalg.solve(P, e)))
        pos.append(float(np.hypot(*(X[:2, 2] - run["truth"][k + 1, :2]))))
    nees, nis, pos = np.array(nees), np.array(nis), np.array(pos)
    frac = float((nees > CHI2_3_95).mean())
    verdict = "consistent" if frac < 0.15 and nees.mean() > 1.5 else ("overconfident" if frac >= 0.15 else "conservative")
    return dict(nees=nees, nis=nis, pos=pos, verdict=verdict,
                tiles={"ANEES, single run (target 3)": f"{nees.mean():.2f}",
                       "ANIS, single run (target 2)": f"{nis.mean():.2f}",
                       "position RMSE": f"{100 * np.sqrt((pos ** 2).mean()):.2f} cm",
                       "NEES above the 95 % bound": f"{100 * frac:.0f} % of steps (expect ≈ 5 %)"})


# ---------------------------------------------------------------- Fig 2.6d: the printed coefficient of (144) near θ = 0

_B2N = [Fraction(1, 6), Fraction(-1, 30), Fraction(1, 42), Fraction(-1, 30), Fraction(5, 66), Fraction(-691, 2730),
        Fraction(7, 6), Fraction(-3617, 510), Fraction(43867, 798), Fraction(-174611, 330)]
D_SERIES = [float(-(-1) ** n * _B2N[n - 1] / math.factorial(2 * n)) for n in range(1, 11)]   # d = Σ c_n θ^(2n−2)


def d_oracle(th):
    """Series of 1/θ² − cot(θ/2)/(2θ), ten terms: exact to double precision for θ ≤ 1."""
    t2 = th * th
    return sum(c * t2 ** k for k, c in enumerate(D_SERIES))


def d_printed(th):
    return 1 / th ** 2 - (1 + math.cos(th)) / (2 * th * math.sin(th))


def d_robust(th):
    from exercises.solutions.T3_solution import _coef_d
    return float(_coef_d(th))


def fig_d(log10_theta=-3.0):
    th = 10 ** log10_theta
    ref = d_oracle(th)
    ep = abs(d_printed(th) - ref) / ref
    er = abs(d_robust(th) - ref) / ref
    sweep = 10 ** np.linspace(-6, 0, 61)
    ps = np.array([abs(d_printed(t) - d_oracle(t)) / d_oracle(t) for t in sweep])
    rs = np.array([abs(d_robust(t) - d_oracle(t)) / d_oracle(t) for t in sweep])
    mat = math.sqrt(2) * th * th * abs(d_printed(th) - ref)           # ‖Δd · [n]x²θ²‖_F in J_r⁻¹ (144)
    def ex10(v):                    # "9.8e-4": same string as JS v.toExponential(1)
        if v == 0:
            return "0 (exact)"
        if v < 1e-15:
            return "< 1e-15 (float64 floor)"
        m, e = f"{v:.1e}".split("e")
        return f"{m}e{int(e)}"
    return dict(sweep=sweep, ps=ps, rs=rs, th=th, ep=ep, er=er,
                tiles={"θ": f"{th:.1e} rad",
                       "relative error of the printed coefficient": ex10(ep),
                       "relative error, series/cot version (series is the oracle below 0.3)": ex10(er),
                       "error this leaves in J_r⁻¹ (‖·‖_F)": ex10(mat)})
