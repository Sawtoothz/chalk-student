# /// script
# requires-python = ">=3.11"
# dependencies = ["marimo", "numpy", "scipy", "matplotlib", "plotly"]
# ///
"""Interactive session for Thrun ch. 3 — Gaussian filters.

    marimo edit session.py        # work in it
    marimo run session.py         # read-only app

Each figure follows viz/README.md: Fig 2.2a..2.2d, blue = estimate / linear, coral = measurement /
EKF, teal = the thing being taught, gray = truth and structure. Every "Predict first" cell asks for your
guess before the plot answers it; write the guess down, the gap is where the learning is.

Uses the reference implementation in exercises/solutions so the session works before you have finished
T3. Switch USE_MY_CODE to True to drive the plots with your own exercise.py.
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    from scipy.stats import chi2

    HERE = Path(__file__).resolve().parent
    ROOT = HERE.parents[2]
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(HERE))
    from viz.py import style

    style.register_plotly("light")
    R = style.ROLE
    P = style.palette("light")

    USE_MY_CODE = False
    if USE_MY_CODE:
        from exercises import exercise as ex
    else:
        try:
            from exercises.solutions import T3_solution as ex
        except ImportError:  # student edition: no gated solutions; your own exercise.py drives this
            from exercises import exercise as ex
    from exercises import models

    return HERE, P, R, USE_MY_CODE, chi2, ex, go, mo, models, np, style


@app.cell
def _(mo):
    mo.md(
        r"""
        # Session t2.2 · Gaussian filters

        Four figures, one idea. Work them in order; each slider has a **Predict first** prompt above it.

        1. **Fig 2.2a** — the KF on the book's car: how gain splits the difference.
        2. **Fig 2.2b** — a Gaussian through a nonlinearity: where EKF and UKF disagree with the truth.
        3. **Fig 2.2c** — the tracked robot's range-bearing EKF vs UKF on a figure-eight.
        4. **Fig 2.2d** — consistency: NEES and NIS, and what each noise knob does to them.
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.2a KF on the car


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.2a · Kalman filter on the 1-D car (book exercises 1–2)

        State $(p, v)$, $\Delta t = 1$, random acceleration $\sigma_a^2 = 1$, position sensor $\sigma_z^2$.

        **Predict first.** With a terrible sensor ($\sigma_z^2 = 100$) and a good prior, will the posterior
        mean sit closer to the prior or to the measurement? What happens to the *velocity* estimate when only
        *position* is measured, and why?
        """
    )
    return


@app.cell
def _(mo):
    sz2 = mo.ui.slider(0.1, 100, value=10, step=0.1, label="sensor variance σ_z²", show_value=True)
    steps = mo.ui.slider(1, 30, value=8, step=1, label="steps before the measurement", show_value=True)
    zval = mo.ui.slider(-10, 30, value=12, step=0.5, label="measured position z", show_value=True)
    mo.vstack([sz2, steps, zval])
    return steps, sz2, zval


@app.cell
def _(P, R, ex, go, mo, models, np, steps, style, sz2, zval):
    car = models.CarCV
    mu, Sigma = np.zeros(2), np.diag([1.0, 0.25])
    for _ in range(steps.value):
        mu, Sigma = ex.kf_predict(mu, Sigma, np.zeros(1), car.A, car.B, car.R_proc)
    Q = np.array([[sz2.value]])
    mu_post, Sig_post, nu, S = ex.kf_update(mu, Sigma, np.array([zval.value]), car.C, Q)
    K = Sigma @ car.C.T / S[0, 0]

    def ell(m, C, n_std, color, name, dash=None):
        vals, vecs = np.linalg.eigh(C)
        t = np.linspace(0, 2 * np.pi, 120)
        pts = vecs @ (np.sqrt(np.clip(vals, 0, None))[:, None] * n_std * np.vstack([np.cos(t), np.sin(t)]))
        return go.Scatter(x=m[0] + pts[0], y=m[1] + pts[1], mode="lines", name=name,
                          line=dict(color=color, width=2, dash=dash), showlegend=n_std == 2)

    fig = go.Figure()
    fig.add_trace(ell(mu, Sigma, 2, R["gray"], "prior (predicted)", "dash"))
    fig.add_trace(ell(mu, Sigma, 1, R["gray"], "", "dash"))
    fig.add_vrect(x0=zval.value - 2 * np.sqrt(sz2.value), x1=zval.value + 2 * np.sqrt(sz2.value),
                  fillcolor=R["coral"], opacity=0.12, line_width=0)
    fig.add_vline(x=zval.value, line=dict(color=R["coral"], width=2))
    fig.add_trace(ell(mu_post, Sig_post, 2, R["teal"], "posterior"))
    fig.add_trace(ell(mu_post, Sig_post, 1, R["teal"], ""))
    fig.add_trace(go.Scatter(x=[mu[0], mu_post[0]], y=[mu[1], mu_post[1]], mode="lines+markers",
                             line=dict(color=P["ink"], width=1), marker=dict(size=6), name="mean moves by K·ν"))
    fig.update_layout(title="Fig 2.2a · position–velocity belief before and after one position measurement",
                      xaxis_title="position p [m]", yaxis_title="velocity v [m/s]", height=420)
    fig.update_yaxes(scaleanchor="x", scaleratio=1)

    tiles = {
        "innovation ν": f"{nu[0]:+.2f} m",
        "S = CΣ̄Cᵀ+Q": f"{S[0,0]:.2f} m²",
        "gain K (p, v)": f"({K[0,0]:.2f}, {K[1,0]:.2f})",
        "tr Σ̄ → tr Σ": f"{np.trace(Sigma):.2f} → {np.trace(Sig_post):.2f}",
    }
    style.card(mo.ui.plotly(fig), fig="Fig 2.2a · Table 3.1", title="One measurement, one gain",
               hint="Drag σ_z² down and watch the ellipse collapse onto the red line; drag it up and watch the mean refuse to move",
               chip="update narrows Σ" if np.trace(Sig_post) < np.trace(Sigma) else "update widened Σ (bug)",
               chip_state="ok" if np.trace(Sig_post) < np.trace(Sigma) else "bad", tiles=tiles)
    return K, Q, S, Sig_post, Sigma, car, ell, fig, mu, mu_post, nu, tiles


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** The velocity gain $K_v$ is non-zero although only position is
        measured: the predicted covariance has a $p$–$v$ correlation (the off-diagonal of $A\Sigma A^T$), so a
        surprise in position is partly explained by velocity. With $\sigma_z^2 = 100$ the mean barely moves and
        the posterior ellipse is almost the prior. With $\sigma_z^2 = 0.1$ the posterior collapses onto the
        measurement in $p$ but stays wide in $v$. The tile $\operatorname{tr}\bar\Sigma \to \operatorname{tr}\Sigma$
        must always go down (p. 45).
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.2b nonlinear transform


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.2b · A Gaussian through a nonlinearity (Figs 3.3–3.9)

        Polar to Cartesian: $(r, \theta) \mapsto (r\cos\theta,\ r\sin\theta)$. This is exactly what a range-bearing
        measurement does in reverse, so it is the right nonlinearity to study.

        **Predict first.** As the bearing uncertainty $\sigma_\theta$ grows, which way does the *true* mean of the
        Cartesian point move: outward along the ray, or inward toward the sensor? Which filter catches that?
        """
    )
    return


@app.cell
def _(mo):
    sth = mo.ui.slider(1, 60, value=25, step=1, label="bearing std σ_θ [deg]", show_value=True)
    sr = mo.ui.slider(0.01, 1.0, value=0.1, step=0.01, label="range std σ_r [m]", show_value=True)
    alpha = mo.ui.slider(0.1, 1.0, value=1.0, step=0.05, label="UKF α", show_value=True)
    mo.vstack([sth, sr, alpha])
    return alpha, sr, sth


@app.cell
def _(P, R, alpha, ex, go, mo, np, sr, sth, style):
    rng = np.random.default_rng(0)
    mu_p = np.array([5.0, 0.0])
    Sig_p = np.diag([sr.value ** 2, np.deg2rad(sth.value) ** 2])
    f = lambda q: np.array([q[0] * np.cos(q[1]), q[0] * np.sin(q[1])])

    samp = rng.multivariate_normal(mu_p, Sig_p, 20000)
    ys = np.column_stack([samp[:, 0] * np.cos(samp[:, 1]), samp[:, 0] * np.sin(samp[:, 1])])
    mc_m, mc_C = ys.mean(0), np.cov(ys.T)

    J = np.array([[np.cos(mu_p[1]), -mu_p[0] * np.sin(mu_p[1])], [np.sin(mu_p[1]), mu_p[0] * np.cos(mu_p[1])]])
    ekf_m, ekf_C = f(mu_p), J @ Sig_p @ J.T

    X, wm, wc = ex.sigma_points(mu_p, Sig_p, alpha=alpha.value, beta=2.0, kappa=1.0)
    ukf_m, ukf_C, _ = ex.unscented_transform(np.column_stack([f(X[:, i]) for i in range(X.shape[1])]), wm, wc, np.zeros((2, 2)))

    def ell2(m, C, color, name, dash=None):
        vals, vecs = np.linalg.eigh(C)
        t = np.linspace(0, 2 * np.pi, 120)
        pts = vecs @ (np.sqrt(np.clip(vals, 0, None))[:, None] * 2 * np.vstack([np.cos(t), np.sin(t)]))
        return go.Scatter(x=m[0] + pts[0], y=m[1] + pts[1], mode="lines", name=name, line=dict(color=color, width=2, dash=dash))

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=ys[::10, 0], y=ys[::10, 1], mode="markers", marker=dict(size=3, color=R["gray"], opacity=0.35), name="true samples"))
    fig2.add_trace(ell2(mc_m, mc_C, P["ink"], "true 2σ (Monte Carlo)"))
    fig2.add_trace(ell2(ekf_m, ekf_C, R["blue"], "EKF (tangent) 2σ", "dash"))
    fig2.add_trace(ell2(ukf_m, ukf_C, R["coral"], "UKF (sigma points) 2σ", "dot"))
    fig2.add_trace(go.Scatter(x=[mc_m[0]], y=[mc_m[1]], mode="markers", marker=dict(color=P["ink"], size=9, symbol="x"), name="true mean"))
    fig2.add_trace(go.Scatter(x=[ekf_m[0]], y=[ekf_m[1]], mode="markers", marker=dict(color=R["blue"], size=8), name="EKF mean"))
    fig2.add_trace(go.Scatter(x=[ukf_m[0]], y=[ukf_m[1]], mode="markers", marker=dict(color=R["coral"], size=8), name="UKF mean"))
    fig2.add_trace(go.Scatter(x=[0], y=[0], mode="markers", marker=dict(color=R["teal"], size=10, symbol="square"), name="sensor"))
    fig2.update_layout(title="Fig 2.2b · (r, θ) → (x, y): the true cloud bends; the tangent cannot",
                       xaxis_title="x [m]", yaxis_title="y [m]", height=460)
    fig2.update_yaxes(scaleanchor="x", scaleratio=1)

    e_ekf = np.linalg.norm(ekf_m - mc_m); e_ukf = np.linalg.norm(ukf_m - mc_m)
    tiles2 = {
        "true mean x": f"{mc_m[0]:.3f} m  (EKF says {ekf_m[0]:.3f})",
        "mean error EKF / UKF": f"{e_ekf:.3f} / {e_ukf:.3f} m",
        "cov error ‖·‖ EKF / UKF": f"{np.linalg.norm(ekf_C - mc_C):.3f} / {np.linalg.norm(ukf_C - mc_C):.3f}",
        "2nd-order term": f"−r σ_θ²/2 = {-mu_p[0] * np.deg2rad(sth.value) ** 2 / 2:.3f} m",
    }
    style.card(mo.ui.plotly(fig2), fig="Fig 2.2b · eq. 3.51 vs 3.69", title="Linearization error grows with the width of the prior",
               hint="Push σ_θ to 60°: the EKF mean stays at x = 5 while the truth slides inward; the UKF follows it",
               chip="UKF closer than EKF" if e_ukf < e_ekf else "EKF closer (small σ_θ)",
               chip_state="ok" if e_ukf <= e_ekf + 1e-9 else "warn", tiles=tiles2)
    return J, X, e_ekf, e_ukf, ekf_C, ekf_m, ell2, f, fig2, mc_C, mc_m, mu_p, rng, samp, Sig_p, tiles2, ukf_C, ukf_m, wc, wm, ys


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** The true mean moves *inward*: $E[r\cos\theta] = r\,e^{-\sigma_\theta^2/2}
        \approx r(1 - \sigma_\theta^2/2)$. The tangent has no second derivative, so the EKF mean never moves (p. 67:
        "the EKF captures only the first order term"). The UKF mean tracks the inward shift because the two
        outer sigma points both land at smaller $x$ than the centre one. Both filters still draw an ellipse
        over what is really a banana (p. 63).
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.2c robot EKF vs UKF


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.2c · Tracked robot, range–bearing to one landmark

        Velocity motion model (eq. 5.9), figure-eight controls, one landmark. EKF in blue, UKF in coral,
        truth in gray, 2σ ellipses every 25 steps.

        **Predict first.** Move the landmark close to the path (e.g. (1.0, 0.5)). Which filter's ellipses stop
        containing the truth first, and at which part of the path?
        """
    )
    return


@app.cell
def _(mo):
    lmx = mo.ui.slider(-2, 8, value=5.0, step=0.1, label="landmark x", show_value=True)
    lmy = mo.ui.slider(-2, 6, value=3.0, step=0.1, label="landmark y", show_value=True)
    seed = mo.ui.slider(0, 9, value=0, step=1, label="noise seed", show_value=True)
    mo.vstack([lmx, lmy, seed])
    return lmx, lmy, seed


@app.cell
def _(P, R, chi2, ex, go, lmx, lmy, mo, models, np, seed, style):
    model = models.RangeBearing(landmark=(lmx.value, lmy.value))
    N = 300
    U = models.figure_eight(N, model.dt)
    rng3 = np.random.default_rng(seed.value)
    x0 = np.array([0.0, 0.0, 0.3])
    xs, zs = model.simulate(x0, U, rng3)

    def run(step):
        m = x0 + rng3.normal(0, [0.05, 0.05, 0.02]); S = np.diag([0.05, 0.05, 0.02]) ** 2
        M, Cv, NE, NI = [m], [S], [], []
        for t in range(N):
            m, S, nu, Sm = step(m, S, U[t], zs[t], model, model.R_proc, model.Q_meas)
            e = m - xs[t + 1]; e[2] = models.wrap(e[2])
            M.append(m); Cv.append(S); NE.append(ex.nees(e, S)); NI.append(ex.nis(nu, Sm))
        return np.array(M), Cv, np.array(NE), np.array(NI)

    Mek, Cek, NEek, NIek = run(ex.ekf_step)
    Muk, Cuk, NEuk, NIuk = run(ex.ukf_step)

    def ell3(m, C, color):
        vals, vecs = np.linalg.eigh(C[:2, :2])
        t = np.linspace(0, 2 * np.pi, 60)
        pts = vecs @ (np.sqrt(np.clip(vals, 0, None))[:, None] * 2 * np.vstack([np.cos(t), np.sin(t)]))
        return go.Scatter(x=m[0] + pts[0], y=m[1] + pts[1], mode="lines", line=dict(color=color, width=1), showlegend=False, hoverinfo="skip")

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=xs[:, 0], y=xs[:, 1], mode="lines", line=dict(color=R["gray"], width=2), name="truth"))
    fig3.add_trace(go.Scatter(x=Mek[:, 0], y=Mek[:, 1], mode="lines", line=dict(color=R["blue"], width=1.5), name="EKF"))
    fig3.add_trace(go.Scatter(x=Muk[:, 0], y=Muk[:, 1], mode="lines", line=dict(color=R["coral"], width=1.5, dash="dot"), name="UKF"))
    for tc in range(0, N + 1, 25):
        fig3.add_trace(ell3(Mek[tc], Cek[tc], R["blue"]))
        fig3.add_trace(ell3(Muk[tc], Cuk[tc], R["coral"]))
    fig3.add_trace(go.Scatter(x=[model.m[0]], y=[model.m[1]], mode="markers", marker=dict(color=R["teal"], size=12, symbol="diamond"), name="landmark"))
    fig3.update_layout(title="Fig 2.2c · figure-eight with one range-bearing landmark", xaxis_title="x [m]", yaxis_title="y [m]", height=500)
    fig3.update_yaxes(scaleanchor="x", scaleratio=1)

    rmin = np.hypot(*(xs[:, :2] - model.m).T).min()
    worst_ek = NEek.max(); worst_uk = NEuk.max()
    tiles3 = {
        "ANEES EKF / UKF, single run (target 3)": f"{NEek.mean():.2f} / {NEuk.mean():.2f}",
        "ANIS EKF / UKF, single run (target 2)": f"{NIek.mean():.2f} / {NIuk.mean():.2f}",
        "closest approach": f"{rmin:.2f} m",
        "worst NEES EKF / UKF": f"{worst_ek:.1f} / {worst_uk:.1f}  (95% bound {chi2.ppf(0.95, 3):.1f})",
    }
    frac_ek = (NEek > chi2.ppf(0.95, 3)).mean()
    state = "ok" if frac_ek < 0.15 else "warn"
    tiles3["NEES > 95% bound, EKF"] = f"{100 * frac_ek:.0f}% of steps (expect ≈ 5%)"
    style.card(mo.ui.plotly(fig3), fig="Fig 2.2c · Tables 3.3 and 3.4", title="EKF and UKF on the tracked robot",
               hint="Drag the landmark onto the path and watch the blue ellipses shrink while the error does not",
               chip="EKF consistent" if state == "ok" else "EKF overconfident", chip_state=state, tiles=tiles3)
    return Cek, Cuk, Mek, Muk, N, NEek, NEuk, NIek, NIuk, U, ell3, fig3, frac_ek, model, rmin, rng3, run, state, tiles3, worst_ek, worst_uk, x0, xs, zs


# ------------------------------------------------------------------ Fig 2.2d consistency


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.2d · Consistency: NEES and NIS

        Same run as above. NEES $= e^T\Sigma^{-1}e \sim \chi^2(3)$ if the filter is honest; NIS
        $= \nu^T S^{-1}\nu \sim \chi^2(2)$. The dashed line is the 95% quantile.

        **Predict first.** Scale the filter's $R_{proc}$ by 0.1 (the filter *thinks* motion is more precise than
        it is). Which statistic reacts first, NEES or NIS? Now scale $Q_{meas}$ by 0.1 instead. Same question.
        """
    )
    return


@app.cell
def _(mo):
    rscale = mo.ui.slider(-1.0, 1.0, value=0.0, step=0.1, label="log₁₀ scale on filter R_proc", show_value=True)
    qscale = mo.ui.slider(-1.0, 1.0, value=0.0, step=0.1, label="log₁₀ scale on filter Q_meas", show_value=True)
    mo.vstack([rscale, qscale])
    return qscale, rscale


@app.cell
def _(N, P, R, U, chi2, ex, go, mo, model, models, np, qscale, rscale, style, x0, xs, zs):
    Rf = model.R_proc * 10 ** rscale.value
    Qf = model.Q_meas * 10 ** qscale.value
    rng4 = np.random.default_rng(0)
    md_ = x0 + rng4.normal(0, [0.05, 0.05, 0.02]); Sd = np.diag([0.05, 0.05, 0.02]) ** 2
    NE, NI, Z = [], [], []
    for td in range(N):
        md_, Sd, nud, Smd = ex.ekf_step(md_, Sd, U[td], zs[td], model, Rf, Qf)
        ed = md_ - xs[td + 1]; ed[2] = models.wrap(ed[2])
        NE.append(ex.nees(ed, Sd)); NI.append(ex.nis(nud, Smd)); Z.append(nud / np.sqrt(np.diag(Smd)))
    NE, NI, Z = np.array(NE), np.array(NI), np.array(Z)
    tt = np.arange(N) * model.dt

    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=tt, y=NE, mode="lines", line=dict(color=R["blue"], width=1.2), name="NEES"))
    fig4.add_trace(go.Scatter(x=tt, y=NI, mode="lines", line=dict(color=R["coral"], width=1.2), name="NIS"))
    fig4.add_hline(y=chi2.ppf(0.95, 3), line=dict(color=R["blue"], dash="dash", width=1))
    fig4.add_hline(y=chi2.ppf(0.95, 2), line=dict(color=R["coral"], dash="dash", width=1))
    fig4.update_layout(title="Fig 2.2d · NEES and NIS over time with 95% χ² bounds", xaxis_title="time [s]", yaxis_title="normalized squared error", height=340, yaxis_range=[0, max(15, min(NE.max(), 60))])

    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(x=tt, y=Z[:, 0], mode="lines", line=dict(color=R["teal"], width=1), name="ν_r / √S_rr"))
    fig5.add_trace(go.Scatter(x=tt, y=Z[:, 1], mode="lines", line=dict(color=R["gray"], width=1), name="ν_φ / √S_φφ"))
    for yv in (-3, 3):
        fig5.add_hline(y=yv, line=dict(color=P["muted"], dash="dot", width=1))
    fig5.update_layout(title="Normalized innovations: the first plot to open on the real robot", xaxis_title="time [s]", yaxis_title="σ", height=300)

    an, ai = NE.mean(), NI.mean()
    frac = (NE > chi2.ppf(0.95, 3)).mean()
    verdict = "consistent" if frac < 0.15 and an > 1.5 else ("overconfident" if frac >= 0.15 else "conservative")
    tiles4 = {
        "ANEES, single run (target 3)": f"{an:.2f}",
        "ANIS, single run (target 2)": f"{ai:.2f}",
        "NEES > 95% bound": f"{100 * frac:.0f}% of steps (expect ≈ 5%)",
        "innovations beyond ±3σ": f"{100 * (np.abs(Z) > 3).mean():.1f}%",
    }
    style.card(mo.vstack([mo.ui.plotly(fig4), mo.ui.plotly(fig5)]), fig="Fig 2.2d · consistency", title="What the two noise knobs do",
               hint="R_proc down → both climb slowly; Q_meas down → NIS jumps at once. Find the setting where both sit on their targets",
               chip=verdict, chip_state={"consistent": "ok", "overconfident": "bad", "conservative": "warn"}[verdict], tiles=tiles4)
    return NE, NI, Qf, Rf, Sd, Z, ai, an, ed, fig4, fig5, frac, md_, nud, rng4, Smd, td, tiles4, tt, verdict


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** Shrinking $Q_{meas}$ makes $S$ small immediately, so NIS jumps on the
        very next update; NEES follows as the over-trusted measurements pull the state around. Shrinking
        $R_{proc}$ lets $\bar\Sigma$ stay small while the real motion wanders, so NEES climbs over tens of steps
        while NIS lags behind it. NIS is what you can measure on the robot; NEES is what you actually care
        about. Tune $Q$ with NIS first, then $R$ with a ground-truth run. That is exercise T5.

        ## Before you leave

        - [ ] Write, from memory, the five lines of Table 3.1 and the two substitutions that make Table 3.3.
        - [ ] State the two factors on p. 80 that decide linearization error.
        - [ ] `pytest exercises/tests -q`
        """
    )
    return


if __name__ == "__main__":
    app.run()
