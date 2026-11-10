# /// script
# requires-python = ">=3.11"
# dependencies = ["marimo", "numpy", "plotly"]
# ///
"""Interactive session for Labbe ch. 4 — One Dimensional Kalman Filters.

    marimo edit session.py        # work in it
    marimo run session.py         # read-only app

Four figures, Fig 2.2a..2.2d (lesson t2.2): blue = estimate, coral = measurement, teal = the quantity being
taught, gray = truth and structure. Every "Predict first" cell asks for your guess before the plot answers it.

Names follow the repo: R_proc is Labbe's Q (variance added per predict), Q_meas is Labbe's R (sensor variance).

Uses the reference solution in exercises/solutions so the session works before you have finished T3.
Switch USE_MY_CODE to True to drive the plots with your own exercise.py. The noise is drawn once and stored in
figures/session_data.json (make_session_data.py), so interactive.html shows the same numbers.
"""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import json
    import sys
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

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

    DATA = json.loads((HERE / "figures" / "session_data.json").read_text())
    W1, V1, W2, V2 = (np.array(DATA[k]) for k in ("W1", "V1", "W2", "V2"))

    def make_truth(W, V, u_true, R_true, Q_true):
        """x_k = x_{k-1} + u_k + sqrt(R_true) W_k;  z_k = x_k + sqrt(Q_true) V_k."""
        steps = np.broadcast_to(np.asarray(u_true, float), W.shape) + np.sqrt(R_true) * W
        xs = np.cumsum(steps)
        return xs, xs + np.sqrt(Q_true) * V

    def pdf(x, mu, var):
        return np.exp(-0.5 * (x - mu) ** 2 / var) / np.sqrt(2 * np.pi * var)

    def sg(v, d=2, unit=""):
        """Signed number with a true minus sign."""
        return f"{v:+.{d}f}{unit}".replace("-", "−")

    def ug(v, d=2, unit=""):
        return f"{v:.{d}f}{unit}".replace("-", "−")

    return (HERE, P, R, USE_MY_CODE, V1, V2, W1, W2, ex, go, make_subplots, make_truth, mo, np, pdf, sg, style, ug)


@app.cell
def _(mo):
    mo.md(
        r"""
        # Session t2.2 · One-dimensional Kalman filters (Labbe ch. 4)

        Four figures, one filter: five lines of predict and update on a scalar. Work them in order; each has a
        **Predict first** prompt above the sliders. Write the guess down, then move the slider.

        1. **Fig 2.2a** — one update: how $\bar P$ and $Q_{meas}$ decide where the posterior sits (p. 138, p. 150).
        2. **Fig 2.2b** — the dog's 25 steps: initial guess, initial variance, noise settings (pp. 143–148, 164).
        3. **Fig 2.2c** — gain and variance converge; what a hard-coded $K$ costs (pp. 148, 167–168).
        4. **Fig 2.2d** — a too-small $R_{proc}$ and a manoeuvring target: the filter ignores the data (pp. 160–161).
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.2a one update


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.2a · One update, Bayes form against gain form (p. 138, p. 150)

        Prior $\bar x = 10$ m with variance $\bar P$; one measurement $z$ with variance $Q_{meas}$.

        **Predict first.** Set $\bar P = 4$ m² and $Q_{meas} = 1$ m². Does the posterior mean sit closer to the
        prior or to $z$, and by what fraction of $z - \bar x$? Then make $Q_{meas} = 25$ m². Is the posterior
        variance ever larger than the smaller of the two inputs?
        """
    )
    return


@app.cell
def _(mo):
    a_P = mo.ui.slider(0.1, 25, value=4, step=0.1, label="prior variance P̄ [m²]", show_value=True)
    a_Q = mo.ui.slider(0.1, 25, value=1, step=0.1, label="measurement variance Q_meas [m²]", show_value=True)
    a_z = mo.ui.slider(6, 16, value=12, step=0.5, label="measurement z [m]", show_value=True)
    mo.vstack([a_P, a_Q, a_z])
    return a_P, a_Q, a_z


@app.cell
def _(P, R, a_P, a_Q, a_z, ex, go, mo, np, pdf, sg, style, ug):
    _xb = 10.0
    _x, _P, _y, _S, _ = ex.update(_xb, a_P.value, a_z.value, a_Q.value)
    _xB, _PB, _logc = ex.update_bayes(_xb, a_P.value, a_z.value, a_Q.value)
    _K = a_P.value / _S
    _g = np.linspace(2, 20, 500)

    _fig = go.Figure()
    _fig.add_trace(go.Scatter(x=_g, y=pdf(_g, _xb, a_P.value), name="prior N(x̄, P̄)", line=dict(color=R["gray"], dash="dash", width=2)))
    _fig.add_trace(go.Scatter(x=_g, y=pdf(_g, a_z.value, a_Q.value), name="likelihood N(z, Q_meas)", line=dict(color=R["coral"], width=2)))
    _fig.add_trace(go.Scatter(x=_g, y=pdf(_g, _x, _P), name="posterior", line=dict(color=R["teal"], width=3), fill="tozeroy",
                              fillcolor="rgba(29,158,117,0.12)"))
    _fig.add_trace(go.Scatter(x=[_xb, _x, a_z.value], y=[0, 0, 0], mode="markers", showlegend=False,
                              marker=dict(size=9, color=[R["gray"], R["teal"], R["coral"]])))
    _fig.update_layout(title="prior × likelihood → posterior (one update)", xaxis_title="position [m]",
                       yaxis_title="density [1/m]", height=360)

    _tiles = {
        "gain K = P̄/(P̄+Q_meas)": ug(_K, 3),
        "posterior mean": ug(_x, 3, " m"),
        "posterior variance P": ug(_P, 3, " m²"),
        "P vs min(P̄, Q_meas)": f"{ug(_P, 3)} < {ug(min(a_P.value, a_Q.value), 3)}",
        "Bayes form − gain form, x / P (should be 0)": f"{abs(_xB - _x):.3f} / {abs(_PB - _P):.3f}",
        "evidence log c = log N(z; x̄, S)": ug(_logc, 3),
    }
    _st = "prior-dominated" if _K < 0.5 else "measurement-dominated"
    mo.vstack([style.card(mo.ui.plotly(_fig), fig="Fig 2.2a · p. 138, p. 150",
                          title="The posterior is narrower than both inputs and sits near the narrower one",
                          hint="Drag P̄ and Q_meas against each other; K moves the mean the fraction K of the way from x̄ to z.",
                          chip=_st, chip_state="ok", tiles=_tiles)])
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** With $\bar P = 4$ and $Q_{meas} = 1$ the gain is $K = 0.8$, so the mean moves
        80 % of the way to $z$ (p. 150: $\mu = \bar\mu + K(z - \bar\mu)$). The variance is $\bar P Q_{meas}/(\bar P + Q_{meas})$,
        always below both inputs: an update never loses information, a predict always does (pp. 136, 146). The two
        "should be 0" tiles are the whole point of p. 149–150: the Bayes-form product and the gain form are the same
        formula.
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.2b the dog's 25 steps


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.2b · The dog filter, 25 steps (pp. 143–148, Interactive Plots p. 164)

        True dog: $u = 1$ m/step, $R_{proc} = 2$ m², RFID sensor $Q_{meas} = 4.5$ m² (p. 147, the same draws every
        time). The filter starts at $x_0$ with variance $P_0$ and uses the sliders for $R_{proc}$ and $Q_{meas}$.

        **Predict first.** The dog starts at 0 m. Put $x_0 = 20$ m with $P_0 = 400$ m². Is the estimate at step 5
        still wrong by 20 m? Now set $P_0 = 1$ m². How many steps until the filter is back on the dog, and what
        number sets that rate?
        """
    )
    return


@app.cell
def _(mo):
    b_x0 = mo.ui.slider(-30, 30, value=0, step=1, label="initial guess x₀ [m]", show_value=True)
    b_P0 = mo.ui.slider(1, 500, value=400, step=1, label="initial variance P₀ [m²]", show_value=True)
    b_R = mo.ui.slider(0.1, 10, value=2, step=0.1, label="filter R_proc [m²/step]", show_value=True)
    b_Q = mo.ui.slider(0.5, 25, value=4.5, step=0.5, label="filter Q_meas [m²]", show_value=True)
    mo.vstack([b_x0, b_P0, b_R, b_Q])
    return b_P0, b_Q, b_R, b_x0


@app.cell
def _(R, V1, W1, b_P0, b_Q, b_R, b_x0, ex, go, make_truth, mo, np, style, sg, ug):
    _xs, _zs = make_truth(W1, V1, 1.0, 2.0, 4.5)
    _out = ex.run_filter(_zs, b_x0.value, b_P0.value, 1.0, b_R.value, b_Q.value)
    _k = np.arange(1, len(_zs) + 1)
    _est, _sd = _out[:, 0], np.sqrt(_out[:, 1])
    _Pinf, _Kinf = ex.steady_state(b_R.value, b_Q.value)
    _gap = _out[-1, 1] - _Pinf
    _rms = float(np.sqrt(np.mean((_est - _xs) ** 2)))
    _nis = ex.nis(_out[:, 4], _out[:, 5])

    _fig = go.Figure()
    _fig.add_trace(go.Scatter(x=np.r_[_k, _k[::-1]], y=np.r_[_est + _sd, (_est - _sd)[::-1]], fill="toself", mode="none",
                              fillcolor="rgba(55,138,221,0.18)", name="estimate ±1σ", hoverinfo="skip"))
    _fig.add_trace(go.Scatter(x=_k, y=_xs, name="true position", line=dict(color=R["gray"], width=2)))
    _fig.add_trace(go.Scatter(x=_k, y=_zs, name="RFID measurements", mode="markers", marker=dict(color=R["coral"], size=6)))
    _fig.add_trace(go.Scatter(x=np.r_[0, _k], y=np.r_[b_x0.value, _est], name="Kalman estimate", line=dict(color=R["blue"], width=2.5)))
    _fig.update_layout(title="dog in a hallway: the filter's belief against the truth", xaxis_title="step k",
                       yaxis_title="position [m]", height=380)

    _tiles = {
        "estimate after 25 steps": ug(_est[-1], 2, " m"),
        "true position": ug(_xs[-1], 2, " m"),
        "P after 25 steps": ug(_out[-1, 1], 4, " m²"),
        "fixed point P∞ (solve P² + R_proc·P − R_proc·Q_meas = 0)": ug(_Pinf, 4, " m²"),
        "P₂₅ − P∞ (→ 0, any x₀)": sg(_gap, 4, " m²"),
        "RMS error vs truth / mean NIS (≈ 1)": f"{_rms:.2f} m / {_nis.mean():.2f}",
    }
    _conv = abs(_gap) < 1e-3
    mo.vstack([style.card(mo.ui.plotly(_fig), fig="Fig 2.2b · pp. 143–148, 164",
                          title="P and K forget x₀ at a rate set by the variances, not by the data",
                          hint="Move x₀ and P₀: the first step uses K ≈ 1 when P₀ is large. Then raise Q_meas and watch the lag.",
                          chip="P at the fixed point" if _conv else "P still converging",
                          chip_state="ok" if _conv else "warn", tiles=_tiles)])
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** With $x_0 = 20$ and $P_0 = 400$ the first gain is 0.989 and the step-1 error is
        already −3.6 m: the first measurement replaces $x_0$ (pp. 144, 146: $\bar P = 401$ for the book's $R_{proc} = 1$).
        With $P_0 = 1$ the first gain is 0.4, the step-1 error is still 11.0 m, and it is −0.5 m by step 5 (p. 161–162: the
        initial error washes out at a rate set by the variances). The posterior variance never looks at $z$:
        $P_{25} - P_\infty$ is 0 for any $x_0$, and for the book's settings $P_\infty = 2.1623$ m² (p. 148).
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.2c gain and variance converge


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.2c · Gain and variance converge; a hard-coded $K$ (pp. 148, 167–168)

        No data enters: $P_k$ and $K_k$ depend only on $P_0$, $R_{proc}$, $Q_{meas}$. $P_0 = 400$ m². The coral line is
        the posterior variance a *fixed* gain $K$ would achieve on the same random walk.

        **Predict first.** Double $R_{proc}$ and keep $Q_{meas}$. Does $K_\infty$ go up or down, and by about how much?
        Then multiply *both* by 10. What happens to $K_\infty$, and what happens to $P_\infty$?
        """
    )
    return


@app.cell
def _(mo):
    c_R = mo.ui.slider(0.1, 10, value=2, step=0.1, label="R_proc [m²/step]", show_value=True)
    c_Q = mo.ui.slider(0.5, 50, value=4.5, step=0.5, label="Q_meas [m²]", show_value=True)
    c_K = mo.ui.slider(0.01, 0.99, value=0.13, step=0.01, label="hard-coded gain K", show_value=True)
    mo.vstack([c_R, c_Q, c_K])
    return c_K, c_Q, c_R


@app.cell
def _(R, c_K, c_Q, c_R, ex, go, make_subplots, mo, np, style, ug):
    _N = 30
    _x, _Pk, _Ks = 0.0, 400.0, []
    _Ps = []
    for _ in range(_N):
        _xbar, _Pbar = ex.predict(_x, _Pk, 0.0, c_R.value)
        _x, _Pk, _y, _S, _ok = ex.update(_xbar, _Pbar, 0.0, c_Q.value)   # z = 0: P and K never depend on z
        _Ks.append(_Pbar / _S)
        _Ps.append(_Pk)
    _Pinf, _Kinf = ex.steady_state(c_R.value, c_Q.value)
    _Pfix = ex.fixed_gain_variance(c_K.value, c_R.value, c_Q.value)
    _r_fix = ex.ratio_from_gain(c_K.value)
    _kk = np.arange(1, _N + 1)
    _near = np.nonzero(np.abs(np.array(_Ks) - _Kinf) < 0.01 * _Kinf)[0]
    _first = int(_near[0]) + 1 if len(_near) else None

    _fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                         subplot_titles=("gain K_k = P̄/(P̄ + Q_meas)", "posterior variance P_k [m²]"))
    _fig.add_trace(go.Scatter(x=_kk, y=_Ks, name="K_k", line=dict(color=R["teal"], width=2.5)), row=1, col=1)
    _fig.add_hrect(y0=_Kinf * 0.99, y1=_Kinf * 1.01, fillcolor="rgba(29,158,117,0.2)", line_width=0, row=1, col=1)
    _fig.add_hline(y=c_K.value, line=dict(color=R["coral"], dash="dot"), row=1, col=1)
    _fig.add_trace(go.Scatter(x=_kk, y=_Ps, name="P_k", line=dict(color=R["blue"], width=2.5)), row=2, col=1)
    _fig.add_hline(y=_Pinf, line=dict(color=R["gray"], dash="dash"), row=2, col=1)
    _fig.add_hline(y=_Pfix, line=dict(color=R["coral"], dash="dot"), row=2, col=1)
    _fig.update_yaxes(type="log", row=2, col=1)
    _fig.update_xaxes(title_text="step k", row=2, col=1)
    _fig.update_layout(height=520, showlegend=False,
                       title="K and P converge; dashed gray = fixed point, dotted coral = your fixed K")

    _tiles = {
        "K∞ / P∞": f"{ug(_Kinf, 4)} / {ug(_Pinf, 4, ' m²')}",
        "K∞²/(1−K∞) − R_proc/Q_meas (should be 0)": f"{abs(ex.ratio_from_gain(_Kinf) - c_R.value / c_Q.value):.3f}",
        "steps until K_k is within 1% of K∞": "more than 30" if _first is None else str(_first),
        "variance of the hard-coded K": ug(_Pfix, 4, " m²"),
        "that variance / P∞ (cost of not adapting)": ug(_Pfix / _Pinf, 3, "×"),
        "R_proc/Q_meas your K assumes": ug(_r_fix, 5),
    }
    _chip = "K at the optimum" if abs(c_K.value - _Kinf) < 0.005 else ("K too low: slow" if c_K.value < _Kinf else "K too high: noisy")
    mo.vstack([style.card(mo.ui.plotly(_fig), fig="Fig 2.2c · pp. 148, 167–168",
                          title="Only the ratio R_proc/Q_meas sets K∞; the scale sets P∞",
                          hint="Scale R_proc and Q_meas together: K∞ stays, P∞ scales. Slide K to P∞'s optimum.",
                          chip=_chip, chip_state="ok" if _chip == "K at the optimum" else "warn", tiles=_tiles)])
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** $K_\infty$ solves $K^2/(1 - K) = R_{proc}/Q_{meas}$: multiplying both by
        10 leaves it where it was, and $P_\infty$ grows ten-fold (it is in m²). Doubling $R_{proc}$ alone raises the
        gain, because a belief that decays faster should listen more. The book's $K = 0.13232$ (p. 168) implies
        a ratio of $0.0202$, which matches none of the chapter's filters (see `map.md`); the last tile is how you check
        any hard-coded gain against the filter it should have come from.
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.2d process variance too small


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.2d · Too small an $R_{proc}$ and a manoeuvring target (pp. 160–161)

        True target: velocity 1 m/step for 20 steps, then the velocity you set; $R_{proc} = 1$ m², $Q_{meas} = 4$ m².
        The filter always believes velocity 1 and uses the slider for its own $R_{proc}$. Start at the honest
        $R_{proc} = 1$.

        **Predict first.** Drop the filter's $R_{proc}$ to $10^{-3}$ m². Does the filter *notice* that the target
        manoeuvred? Look at $K$ and the innovation, not just the plot.
        """
    )
    return


@app.cell
def _(mo):
    d_R = mo.ui.slider(-3, 1, value=0, step=0.1, label="log₁₀ of filter R_proc  (0 → 1 m²)", show_value=True)
    d_v = mo.ui.slider(1, 3, value=2, step=0.1, label="target velocity after step 20 [m/step]", show_value=True)
    d_u = mo.ui.slider(0, 3, value=1, step=0.1, label="velocity the filter assumes [m/step]", show_value=True)
    mo.vstack([d_R, d_v, d_u])
    return d_R, d_u, d_v


@app.cell
def _(R, V2, W2, d_R, d_u, d_v, ex, go, make_subplots, make_truth, mo, np, style, sg, ug):
    _n = len(W2)
    _utrue = np.where(np.arange(_n) < 20, 1.0, d_v.value)
    _xs, _zs = make_truth(W2, V2, _utrue, 1.0, 4.0)
    _Rf = 10 ** d_R.value
    _out = ex.run_filter(_zs, _zs[0], 4.0, d_u.value, _Rf, 4.0, None)
    _k = np.arange(1, _n + 1)
    _est, _sd = _out[:, 0], np.sqrt(_out[:, 1])
    _nis = ex.nis(_out[:, 4], _out[:, 5])
    _frac = float(np.mean(_nis > ex.CHI2_1DOF_99))
    _Kk = _out[:, 3] / _out[:, 5]
    _err = _est[-1] - _xs[-1]

    _fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12, row_heights=[0.62, 0.38],
                         subplot_titles=("position [m]", "NIS = y²/S  (dashed: 99% χ² bound, 6.635)"))
    _fig.add_trace(go.Scatter(x=np.r_[_k, _k[::-1]], y=np.r_[_est + 2 * _sd, (_est - 2 * _sd)[::-1]], fill="toself", mode="none",
                              fillcolor="rgba(55,138,221,0.18)", name="estimate ±2σ", hoverinfo="skip"), row=1, col=1)
    _fig.add_trace(go.Scatter(x=_k, y=_xs, name="true position", line=dict(color=R["gray"], width=2)), row=1, col=1)
    _fig.add_trace(go.Scatter(x=_k, y=_zs, name="measurements", mode="markers", marker=dict(color=R["coral"], size=5)), row=1, col=1)
    _fig.add_trace(go.Scatter(x=_k, y=_est, name="filter", line=dict(color=R["blue"], width=2.5)), row=1, col=1)
    _fig.add_trace(go.Scatter(x=_k, y=_nis, name="NIS", line=dict(color=R["teal"], width=1.8), showlegend=False), row=2, col=1)
    _fig.add_hline(y=ex.CHI2_1DOF_99, line=dict(color=R["gray"], dash="dash"), row=2, col=1)
    _fig.add_vline(x=20.5, line=dict(color=R["gray"], dash="dot"))
    _fig.update_xaxes(title_text="step k", row=2, col=1)
    _fig.update_layout(height=560, title="the filter cannot see its own failure in the position plot")

    _tiles = {
        "filter R_proc": ug(_Rf, 4, " m²"),
        "gain K at the last step": ug(_Kk[-1], 3),
        "error at step 40 (filter − truth)": sg(_err, 2, " m"),
        "mean NIS (honest and matched: ≈ 1)": ug(_nis.mean(), 2),
        "NIS above the 99% bound": f"{100 * _frac:.1f}% of steps (expect ≈ 1%)",
        "P at the last step": ug(_out[-1, 1], 4, " m²"),
    }
    if _frac > 0.25:
        _chip, _cs = "diverged: ignores the data", "bad"
    elif _frac > 0.05:
        _chip, _cs = "overconfident", "warn"
    else:
        _chip, _cs = "consistent", "ok"
    mo.vstack([style.card(mo.ui.plotly(_fig), fig="Fig 2.2d · pp. 160–161",
                          title="A small R_proc makes K small, so a model error is never corrected",
                          hint="Slide R_proc down, then raise the velocity after step 20. NIS is what tells you, not the 2σ band.",
                          chip=_chip, chip_state=_cs, tiles=_tiles)])
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** At $R_{proc} = 10^{-3}$ m² (target velocity 2 m/step after step 20) the gain at
        step 40 is 0.028, the filter is 10.9 m behind the target, its 1σ is 0.33 m, and 40 % of the steps are above the
        99 % NIS bound: sure and wrong ("The filter does not 'notice' that it is diverging", p. 161). The position plot shows a confident line; NIS
        is what shows the failure. At the honest $R_{proc} = 1$ m² the same target gives gain 0.39, an error of 1.3 m
        (the lag of a constant-velocity filter on a velocity step) and 2.5 % of steps above the bound.
        Setting the assumed velocity to 2 with the target at 1 (honest $R_{proc}$) leaves a 4.4 m error at step 40 but
        the gain stays at 0.39: the variances decide whether the filter can correct a wrong model, and `lecture.md`
        (p. 165–167 note) separates that from lag. T5's gust is this failure on a drone.

        ## Before you leave

        - [ ] Write the five lines of predict and update from memory, with `R_proc` and `Q_meas`.
        - [ ] State what fixes $K_\infty$ and what fixes $P_\infty$.
        - [ ] `pytest exercises/tests -q`
        """
    )
    return


if __name__ == "__main__":
    app.run()
