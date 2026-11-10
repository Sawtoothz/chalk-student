# /// script
# requires-python = ">=3.11"
# dependencies = ["marimo", "numpy", "scipy", "plotly"]
# ///
"""Interactive session for Solà et al., "A micro Lie theory for state estimation in robotics" (t2.6).

    marimo edit session.py        # work in it
    marimo run session.py         # read-only app

Four figures, Fig 2.6a..2.6d, each with a Predict-first prompt above its sliders. Colours follow viz/README.md:
blue = estimate / reference, coral = measurement / the other convention, teal = the quantity being taught, gray = structure.

Uses the reference solution in exercises/solutions, so the session works before you have done T3. Set USE_MY_CODE
to True to drive Figs 2.6a–c with your own exercise.py (Fig 2.6d is about a formula, not about your code).
The numbers come from session_lib.py; interactive.html is the same model in plain JS.
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
    import session_lib as lib

    def frame(M, length, color):
        return go.Scatter(x=[M[0, 2], M[0, 2] + length * M[0, 0]], y=[M[1, 2], M[1, 2] + length * M[1, 0]],
                          mode="lines", line=dict(color=color, width=3), showlegend=False, hoverinfo="skip")

    def mark(M, color, symbol, name, size, open_=False):
        return go.Scatter(x=[M[0, 2]], y=[M[1, 2]], mode="markers", name=name,
                          marker=dict(color="rgba(0,0,0,0)" if open_ else color, size=size, symbol=symbol,
                                      line=dict(color=color, width=2)))

    return HERE, P, R, USE_MY_CODE, ex, frame, go, lib, mark, mo, np, style


@app.cell
def _(mo):
    mo.md(
        r"""
        # Session t2.6 · A micro Lie theory

        Four figures, one idea: do the calculus in the tangent space and move between tangent and group only
        through Exp and Log. Work them in order; each has a **Predict first** prompt above its sliders.

        1. **Fig 2.6a** — the same twist $\tau$ on the right and on the left of $X$; $\mathrm{Ad}_X$ reconciles them.
        2. **Fig 2.6b** — a Gaussian on the tangent, drawn on the plane: when the linear ellipse stops being honest.
        3. **Fig 2.6c** — the tag ESKF on the tracked robot (exercise T5): what NIS tuning does and does not fix.
        4. **Fig 2.6d** — the printed coefficient of $J_r^{-1}$ near $\theta = 0$.
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.6a right and left perturbation


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.6a · The same $\tau$ on the right and on the left of $X$

        Pose $X = (x, 1, \theta_X)$ on SE(2); $\tau = (\rho_1, 0.2, \theta_\tau)$, translation first (153).

        **Predict first.** You apply the same twist $\tau$ once on the right of $X$ (body frame) and once on the left
        (world frame). Do they land on the same pose? If not, what single matrix turns one into the other, and does
        it change $\theta$?
        """
    )
    return


@app.cell
def _(mo):
    a_x = mo.ui.slider(-4, 4, value=1.5, step=0.1, label="X position x [m]", show_value=True)
    a_thx = mo.ui.slider(-180, 180, value=40, step=5, label="X heading θ_X [deg]", show_value=True)
    a_rho = mo.ui.slider(-2, 2, value=0.8, step=0.1, label="τ translation ρ₁ [m]", show_value=True)
    a_th = mo.ui.slider(-170, 170, value=50, step=5, label="τ rotation θ_τ [deg]", show_value=True)
    mo.vstack([a_x, a_thx, a_rho, a_th])
    return a_rho, a_th, a_thx, a_x


@app.cell
def _(R, a_rho, a_th, a_thx, a_x, ex, frame, go, lib, mark, mo, np, style):
    ra = lib.fig_a(ex, a_x.value, a_thx.value, a_rho.value, a_th.value)
    fa = go.Figure()
    fa.add_trace(go.Scatter(x=ra["p_right"][:, 0], y=ra["p_right"][:, 1], mode="lines", line=dict(color=R["teal"], width=2), name="X Exp(sτ), s: 0 → 1"))
    fa.add_trace(go.Scatter(x=ra["p_wrong"][:, 0], y=ra["p_wrong"][:, 1], mode="lines", line=dict(color=R["coral"], width=2, dash="dot"), name="Exp(sτ) X"))
    fa.add_trace(mark(ra["X"], R["blue"], "square", "X", 10))
    fa.add_trace(mark(ra["right"], R["teal"], "diamond", "X ⊕ τ", 11))
    fa.add_trace(mark(ra["wrong"], R["coral"], "circle", "Exp(τ) X", 10))
    fa.add_trace(mark(ra["left"], R["teal"], "circle", "Exp(Ad_X τ) X", 18, open_=True))
    for _M, _c in ((ra["X"], R["blue"]), (ra["right"], R["teal"]), (ra["wrong"], R["coral"])):
        fa.add_trace(frame(_M, 0.4, _c))
    fa.add_trace(go.Scatter(x=[0], y=[0], mode="markers", marker=dict(color=R["gray"], size=9, symbol="cross"), name="world origin"))
    fa.update_layout(title="Fig 2.6a · poses on the plane (short bars show the heading)", xaxis_title="x [m]", yaxis_title="y [m]",
                     xaxis_range=[-6, 6], yaxis_range=[-5, 5], height=460)
    fa.update_yaxes(scaleanchor="x", scaleratio=1)
    style.card(mo.ui.plotly(fa), fig="Fig 2.6a · eq. (25), (32), (31)", title="The same τ on the right and on the left of X",
               hint="Drag θ_τ · move X away from the origin · watch the coral pose leave the teal one while the dashed ring stays on it",
               chip="left = right (X commutes with Exp τ)" if ra["special"] else "left ≠ right, Ad_X reconciles them",
               chip_state="warn" if ra["special"] else "ok", tiles=ra["tiles"])
    return fa, ra


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** They land on different positions but with the same heading, because only the
        translation sees the lever arm. Moving $\tau$ through $\mathrm{Ad}_X$ turns the right perturbation into a left
        one: $X \oplus \tau = (\mathrm{Ad}_X \tau) \oplus X$, and the first tile is zero to machine precision for every
        $X$ and $\tau$ (eq. 32, pp. 6–7). The two conventions coincide only when $X$ commutes with $\mathrm{Exp}(\tau)$,
        for instance $\tau = 0$.
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.6b a Gaussian on the tangent


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.6b · A Gaussian on the tangent, drawn on the plane

        Mean $\bar X = (2, 1, \bar\theta)$. $\varepsilon \sim \mathcal N(0, \mathrm{diag}(0.5^2, (0.5 r)^2, \sigma_\theta^2))$
        in the tangent at $\bar X$ (52); 1500 samples $\bar X\,\mathrm{Exp}(\varepsilon)$. The blue ellipse is the 95 %
        contour of the position block $\bar R P_{\rho\rho} \bar R^T$.

        **Predict first.** Raise $\sigma_\theta$ from 5° to 40° with $r = 0.35$ (tracks barely slip sideways). The
        ellipse does not change. Does the cloud of positions? Which of its two axes (along-track or lateral) grows,
        and what does a tight lateral $\sigma_\rho$ do to that growth?
        """
    )
    return


@app.cell
def _(mo):
    b_r = mo.ui.slider(0.1, 1.0, value=0.35, step=0.05, label="lateral / along-track σ_ρ, r", show_value=True)
    b_sth = mo.ui.slider(1, 60, value=20, step=1, label="σ_θ [deg]", show_value=True)
    b_th = mo.ui.slider(-180, 180, value=30, step=5, label="mean heading θ̄ [deg]", show_value=True)
    mo.vstack([b_r, b_sth, b_th])
    return b_r, b_sth, b_th


@app.cell
def _(R, b_r, b_sth, b_th, ex, frame, go, lib, mo, np, style):
    rb = lib.fig_b(ex, b_r.value, b_sth.value, b_th.value)
    _Xb, _sd = rb["Xb"], rb["sd"]
    _t = np.linspace(0, 2 * np.pi, 73)
    _k = np.sqrt(lib.CHI2_2_95)
    _el = _Xb[:2, :2] @ np.vstack([_k * _sd[0] * np.cos(_t), _k * _sd[1] * np.sin(_t)]) + _Xb[:2, 2:3]
    fb = go.Figure()
    fb.add_trace(go.Scatter(x=rb["pos"][::2, 0], y=rb["pos"][::2, 1], mode="markers", marker=dict(size=3, color=R["gray"], opacity=0.4), name="X̄ Exp(ε) samples"))
    fb.add_trace(go.Scatter(x=_el[0], y=_el[1], mode="lines", line=dict(color=R["blue"], width=2), name="linear 95 % ellipse R̄ P_ρρ R̄ᵀ"))
    fb.add_trace(frame(_Xb, 0.3, R["teal"]))
    fb.add_trace(go.Scatter(x=[_Xb[0, 2]], y=[_Xb[1, 2]], mode="markers", marker=dict(color=R["teal"], size=9, symbol="diamond"), name="X̄"))
    fb.update_layout(title="Fig 2.6b · positions of X̄ Exp(ε)", xaxis_title="x [m]", yaxis_title="y [m]", xaxis_range=[-0.5, 4.5], yaxis_range=[-1.5, 3.5], height=460)
    fb.update_yaxes(scaleanchor="x", scaleratio=1)
    _ok = rb["inside"] > 0.925
    style.card(mo.ui.plotly(fb), fig="Fig 2.6b · eq. (52), (55)", title="A Gaussian on the tangent, drawn on the plane",
               hint="Raise σ_θ · lower r · watch the cloud bend out of the ellipse",
               chip="ellipse honest" if _ok else "cloud outgrows the ellipse", chip_state="ok" if _ok else "warn", tiles=rb["tiles"])
    return fb, rb


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** The tangent Gaussian is exact in $\varepsilon$; what you see on the plane is
        Exp of it. The position is $\bar X$'s translation plus $\bar R\,V(\theta_\varepsilon)\rho$, so a random heading
        rotates the random translation by about $\theta_\varepsilon/2$: the lateral spread of the cloud grows with
        $\sigma_\theta \sigma_{\rho,1}$ (the tile reads 1.26 at $\sigma_\theta = 40°$ and $r = 0.35$, against 1.00 at 5°;
        2.22 at $r = 0.15$; 0.97 at $r = 1$), the along-track spread shrinks slightly, and coverage of the linear
        ellipse falls from about 95 % towards 90 %. Small $\sigma_\theta$: the ellipse is honest, which is why the
        filters of §V can carry $P$ on the tangent (p. 9, eq. 52 and 55). Large $\sigma_\theta$: reset or relinearize
        more often.
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.6c tuning the tag ESKF


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.6c · Tuning the tag ESKF on the tracked robot (T5)

        ESKF on SE(2) with the covariance reset, one of the shipped T5 runs (600 steps, 12 tags). Defaults are the
        task-1 guess: $\sigma_y = 0.10$ m, slip $\sigma = 1$ mm per step.

        **Predict first.** Lower $\sigma_y$ until the NIS average (ANIS) reads about 2. Will ANEES then be near 3?
        Write your guess, then raise the slip $\sigma$ with the second slider and watch which statistic moves and
        which one does not.
        """
    )
    return


@app.cell
def _(mo):
    c_run = mo.ui.slider(0, 2, value=0, step=1, label="T5 run", show_value=True)
    c_sy = mo.ui.slider(0.01, 0.2, value=0.10, step=0.01, label="tag noise σ_y [m]", show_value=True)
    c_slip = mo.ui.slider(0.5, 15, value=1.0, step=0.5, label="slip σ per step [mm]", show_value=True)
    mo.vstack([c_run, c_sy, c_slip])
    return c_run, c_slip, c_sy


@app.cell
def _(R, c_run, c_slip, c_sy, ex, go, lib, mo, np, style):
    rc = lib.fig_c(ex, lib.load_run(c_run.value), c_sy.value, c_slip.value)
    _t = np.arange(len(rc["nees"])) * 0.1
    fc1 = go.Figure(go.Scatter(x=_t, y=rc["nees"], mode="lines", line=dict(color=R["blue"], width=1.2), name="NEES = eᵀP⁻¹e, e = X_true ⊖ X̂"))
    fc1.add_hline(y=lib.CHI2_3_95, line=dict(color=R["blue"], dash="dash", width=1))
    fc1.update_layout(title="Fig 2.6c · NEES per step, 95 % bound of χ²(3)", xaxis_title="time [s]", yaxis_title="NEES", height=320,
                      yaxis_range=[0, max(15, min(float(rc["nees"].max()), 80))])
    fc2 = go.Figure(go.Scatter(y=rc["nis"], mode="lines", line=dict(color=R["coral"], width=1), name="NIS = zᵀZ⁻¹z per detection"))
    fc2.add_hline(y=lib.CHI2_2_95, line=dict(color=R["coral"], dash="dash", width=1))
    fc2.update_layout(title="NIS per tag detection, 95 % bound of χ²(2)", xaxis_title="detection index", yaxis_title="NIS", height=280, yaxis_range=[0, 15])
    style.card(mo.vstack([mo.ui.plotly(fc1), mo.ui.plotly(fc2)]), fig="Fig 2.6c · eq. (99)–(102) · T5", title="Tuning the tag ESKF on the tracked robot",
               hint="σ_y down → NIS up at once · slip σ up → NEES comes down, NIS barely moves",
               chip=rc["verdict"], chip_state={"consistent": "ok", "overconfident": "bad", "conservative": "warn"}[rc["verdict"]], tiles=rc["tiles"])
    return fc1, fc2, rc


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** NIS needs no ground truth, so it is the knob you can turn on the robot:
        $\sigma_y$ drives ANIS to 2 and the position error barely changes. ANEES stays far above 3 anyway (above 25 on
        run 0 when ANIS is 2), because the filter's slip term says "tracks do not slip sideways" and a smaller
        measurement noise cannot absorb the real slip; only the lateral component of $R_{proc}$ brings NEES home
        (card C8, task T5.3; the ten-run numbers are in `exercises/solutions/T5.md`). The gap between NIS and NEES is
        the lesson: a filter can be consistent in what it sees and dishonest in what it knows (p. 12).
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.6d the printed coefficient of (144)


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.6d · The printed $J_r^{-1}$ coefficient near $\theta = 0$

        $d(\theta) = 1/\theta^2 - (1 + \cos\theta)/(2\theta\sin\theta)$, the $W^2$ coefficient of $J_r^{-1}$ (144).
        Coral = as printed, blue = series below 0.3 and $\cot(\theta/2)$ above, teal = your $\theta$. Oracle: a ten-term
        series of $d$.

        **Predict first.** The printed formula subtracts two numbers of size $1/\theta^2$. At $\theta = 10^{-3}$, how
        many of the 16 digits of $d$ are left? And does the rotation Jacobian $J_r^{-1}$ itself come out wrong by that
        much?
        """
    )
    return


@app.cell
def _(mo):
    d_t = mo.ui.slider(-6, 0, value=-3, step=0.1, label="log₁₀ θ [rad]", show_value=True)
    d_t
    return (d_t,)


@app.cell
def _(R, d_t, go, lib, mo, np, style):
    rd = lib.fig_d(d_t.value)
    _floor = lambda v: np.maximum(v, 1e-17)
    fd = go.Figure()
    fd.add_trace(go.Scatter(x=rd["sweep"], y=_floor(rd["ps"]), mode="lines", line=dict(color=R["coral"], width=2), name="printed (144)"))
    fd.add_trace(go.Scatter(x=rd["sweep"], y=_floor(rd["rs"]), mode="lines", line=dict(color=R["blue"], width=2), name="series below 0.3, cot above (1e-17 = exact zero)"))
    fd.add_trace(go.Scatter(x=[rd["th"]] * 2, y=[1e-17, 10], mode="lines", line=dict(color=R["teal"], width=2), name="your θ"))
    fd.update_layout(title="Fig 2.6d · relative error of the coefficient d(θ)", xaxis_title="θ [rad]", yaxis_title="relative error", height=360)
    fd.update_xaxes(type="log")
    fd.update_yaxes(type="log", range=[-17, 1])
    _bad, _warn = rd["ep"] > 1e-3, rd["ep"] > 1e-8
    style.card(mo.ui.plotly(fd), fig="Fig 2.6d · eq. (144)", title="The printed J_r⁻¹ coefficient near θ = 0",
               hint="Drag θ below 10⁻² · watch the coral curve climb while the blue one stays on the floor",
               chip="fewer than 3 digits left" if _bad else ("printed formula degrading" if _warn else "ok"),
               chip_state="bad" if _bad else ("warn" if _warn else "ok"), tiles=rd["tiles"])
    return fd, rd


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** The coefficient loses about two digits for every decade of $\theta$ below
        $10^{-1}$ (relative error $\propto \varepsilon/\theta^2$, eq. 144): about nine digits are left at $\theta = 10^{-3}$
        and three at $10^{-6}$. The matrix it multiplies is $O(\theta^2)$, so the error in $J_r^{-1}$ itself stays under
        the float64 floor at every $\theta$ here: the printed formula "works" as a Jacobian, which is why libraries
        ship it, and fails only where the coefficient is used on its own. Below $\theta \approx 10^{-4}$ the exact
        digits of the printed error differ between libm builds (one ulp of `cos` changes them); only the order of
        magnitude is stable. The series below 0.3 removes the cancellation (App. B, pp. 14–15).

        ## Before you leave

        - [ ] From memory: write $X \oplus \tau$, $\mathrm{Ad}_X$ and the relation between them (25), (31), (32).
        - [ ] Say why $P$ lives on the tangent at $\hat X$ and what the reset $J_r(\delta x)\,P\,J_r(\delta x)^T$ does (102).
        - [ ] `pytest exercises/tests -q` with `STUDY_IMPL=solution`, then on your own `exercise.py`.
        """
    )
    return


if __name__ == "__main__":
    app.run()
