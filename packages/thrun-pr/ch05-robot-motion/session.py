# /// script
# requires-python = ">=3.11"
# dependencies = ["marimo", "numpy", "plotly"]
# ///
"""Interactive session for Thrun ch. 5 — Robot motion.

    marimo edit session.py        # work in it
    marimo run session.py         # read-only app

Four figures, Fig 2.4a..2.4d: blue = estimate / reference, coral = the book's version (second view),
teal = the thing being taught, gray = structure, amber = warnings. Every "Predict first" cell asks for a
guess before the plot answers it; write the guess down, the gap is where the learning is.

Uses the reference implementation in exercises/solutions so the session works before you have done T3.
Switch USE_MY_CODE to True to drive the plots with your own exercise.py.

Randomness: every sampler is fed from one fixed list of 6000 standard normals (figures/session_draws.json),
consumed in order, so a slider move changes the cloud smoothly and interactive.html (the same figures in
JS) reproduces every readout to two decimals.
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
    from exercises import models

    DRAWS = np.array(json.loads((HERE / "figures" / "session_draws.json").read_text()))

    class Stream:
        """Stands in for np.random.Generator: normal() hands out the next entries of DRAWS, in order."""

        def __init__(self):
            self.i = 0

        def normal(self, loc=0.0, scale=1.0, size=None):
            n = 1 if size is None else int(size)
            z = DRAWS[(self.i + np.arange(n)) % len(DRAWS)]
            self.i += n
            return loc + scale * (z[0] if size is None else z)

    def fx(v, d):
        """Fixed-point with a true minus sign."""
        v = float(v)
        if v != v:
            return "nan"
        return ("−" if v < 0 else "") + f"{abs(v):.{d}f}"

    def book_inverse(x0, Xp, dt):
        """Table 5.1 lines 2-9 exactly as printed (angle swept wrapped; nothing else repaired)."""
        x, y, th = x0
        xp, yp, tp = Xp[..., 0], Xp[..., 1], Xp[..., 2]
        with np.errstate(all="ignore"):
            mu = 0.5 * ((x - xp) * np.cos(th) + (y - yp) * np.sin(th)) / ((y - yp) * np.cos(th) - (x - xp) * np.sin(th))
            xs = (x + xp) / 2 + mu * (y - yp)
            ys = (y + yp) / 2 + mu * (xp - x)
            rs = np.sqrt((x - xs) ** 2 + (y - ys) ** 2)
            dth = models.wrap(np.arctan2(yp - ys, xp - xs) - np.arctan2(y - ys, x - xs))
            v_h = dth / dt * rs
            w_h = dth / dt
            g_h = (tp - th) / dt - w_h
        return v_h, w_h, g_h

    def book_odometry_sample(u, X, alpha, rng):
        """Table 5.6 as printed: no wrap, no rotate-in-place rule, no reverse rule."""
        (xb, yb, tb), (xbp, ybp, tbp) = np.asarray(u[0], float), np.asarray(u[1], float)
        a1, a2, a3, a4 = alpha
        rot1 = np.arctan2(ybp - yb, xbp - xb) - tb
        trans = np.hypot(xbp - xb, ybp - yb)
        rot2 = tbp - tb - rot1
        M = X.shape[0]
        h1 = rot1 - rng.normal(0.0, 1.0, M) * np.sqrt(a1 * rot1**2 + a2 * trans**2)
        h2 = trans - rng.normal(0.0, 1.0, M) * np.sqrt(a3 * trans**2 + a4 * rot1**2 + a4 * rot2**2)
        h3 = rot2 - rng.normal(0.0, 1.0, M) * np.sqrt(a1 * rot2**2 + a2 * trans**2)
        th = X[:, 2]
        return np.stack([X[:, 0] + h2 * np.cos(th + h1), X[:, 1] + h2 * np.sin(th + h1),
                         models.wrap(th + h1 + h3)], axis=-1), (rot1, trans, rot2)

    return (DRAWS, HERE, P, R, Stream, USE_MY_CODE, book_inverse, book_odometry_sample, ex, fx, go, make_subplots, mo,
            models, np, style)


@app.cell
def _(mo):
    mo.md(
        r"""
        # Session t2.4 · Robot motion

        Four figures, one idea: a motion model is a distribution over where a command takes the robot, and
        both of its forms (a sampler and a density) are only as good as their handling of the corners.

        1. **Fig 2.4a** — Table 5.3: the velocity sampler, and what the third noise term $\hat\gamma$ is for.
        2. **Fig 2.4b** — Table 5.1: the density, and the sign of $\hat v$ in line 7.
        3. **Fig 2.4c** — Tables 5.5–5.6: the odometry model, reversing and turning in place.
        4. **Fig 2.4d** — Table 5.7: motion with a map, and the robot that walks through a wall.

        Each slider has a **Predict first** prompt above it. Cards C1–C5 in `translate.md` are the code.
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.4a velocity sampler


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.4a · The velocity sampler (Table 5.3, eq. 5.10–5.16)

        The robot starts at $(0, 0, 0)$ and is commanded $v = 1.0$ m/s and $\omega$ for $\Delta t = 2$ s.
        300 draws of Table 5.3, with the lecture's moderate noise
        $(\alpha_1 \dots \alpha_4) = 0.02$, $(\alpha_5, \alpha_6) = 0.005$ times the sliders below.

        **Predict first.** Set the $\hat\gamma$ scale to 0 (the book's first version, eq. 5.13, without a
        final rotation). The cloud of end positions looks the same. What is wrong with it, and which readout
        will show it?
        """
    )
    return


@app.cell
def _(mo):
    a_w = mo.ui.slider(-1.2, 1.2, value=0.8, step=0.05, label="commanded ω [rad/s]", show_value=True)
    a_s = mo.ui.slider(-1.0, 0.5, value=0.0, step=0.1, label="log₁₀ scale on α₁…α₆", show_value=True)
    a_g = mo.ui.slider(0.0, 4.0, value=1.0, step=0.5, label="γ̂ scale (α₅, α₆ times this)", show_value=True)
    mo.vstack([a_w, a_s, a_g])
    return a_g, a_s, a_w


@app.cell
def _(P, R, Stream, a_g, a_s, a_w, ex, fx, go, mo, models, np, style):
    _v, _dt, _M = 1.0, 2.0, 300
    _w = a_w.value
    _base = np.array(models.ALPHA_VEL_L5)
    _alpha = _base * 10 ** a_s.value
    _alpha[4:] *= a_g.value
    _x0 = np.zeros(3)
    _free = ex.velocity_forward(_x0, _v, _w, 0.0, _dt)
    _Xs = ex.sample_motion_model_velocity((_v, _w), np.tile(_x0, (_M, 1)), _alpha, _dt, Stream())
    _vh, _wh, _gh = ex.velocity_inverse(_x0, _Xs, _dt)
    _back = ex.velocity_forward(_x0, _vh, _wh, _gh, _dt)
    _err = np.maximum(np.hypot(*(_back[:, :2] - _Xs[:, :2]).T), np.abs(models.wrap(_back[:, 2] - _Xs[:, 2])))
    a_bad = int((_err > 1e-9).sum())
    _pc = np.cov(_Xs[:, :2].T, bias=True)
    _ev = np.sort(np.linalg.eigvalsh(_pc))[::-1]
    _dth = models.wrap(_Xs[:, 2] - _free[2])
    _gsd = float(_gh.std())

    a_fig = go.Figure()
    a_fig.add_trace(go.Scatter(x=_Xs[:, 0], y=_Xs[:, 1], mode="markers", name="Table 5.3 samples",
                               marker=dict(size=4, color=R["teal"], opacity=0.5)))
    _t = np.linspace(0, 1, 60)
    _arc = np.array([ex.velocity_forward(_x0, _v, _w, 0.0, _dt * s) for s in _t])
    a_fig.add_trace(go.Scatter(x=_arc[:, 0], y=_arc[:, 1], mode="lines", name="noise-free arc (eq. 5.9)",
                               line=dict(color=R["blue"], width=2)))
    a_fig.add_trace(go.Scatter(x=[_free[0]], y=[_free[1]], mode="markers", name="noise-free end pose",
                               marker=dict(color=R["blue"], size=10, symbol="x")))
    a_fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers", name="start", marker=dict(color=R["gray"], size=10)))
    a_fig.update_layout(title="Fig 2.4a · where 300 draws of one command end up", xaxis_title="x′ [m]",
                        yaxis_title="y′ [m]", height=440)
    a_fig.update_yaxes(scaleanchor="x", scaleratio=1)

    a_tiles = {
        "noise-free end pose (x′, y′, θ′)": f"({fx(_free[0], 2)} m, {fx(_free[1], 2)} m, {fx(_free[2], 2)} rad)",
        "position spread σ major / minor": f"{fx(np.sqrt(_ev[0]), 3)} / {fx(np.sqrt(_ev[1]), 3)} m",
        "heading spread σ(θ′ − θ′₀)": f"{fx(_dth.std(), 3)} rad",
        "γ̂ recovered by Table 5.1, std": f"{fx(_gsd, 3)} rad/s",
        "round trip, samples off by > 1e-9": f"{a_bad} of {_M}",
    }
    _off = a_g.value == 0.0
    style.card(mo.ui.plotly(a_fig), fig="Fig 2.4a · Table 5.3", title="Sampling the velocity model",
               hint="Drag ω through 0 · scale all noise · set γ̂ to 0 and read the last two tiles",
               chip="γ̂ off: samples on a 2-D surface" if _off else "three noise terms: a 3-D cloud",
               chip_state="warn" if _off else "ok", tiles=a_tiles)
    return a_bad, a_fig, a_tiles


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** The $(x', y')$ cloud does not change when $\hat\gamma$ goes to 0 (the
        position tiles are identical; the draws are the same and $\hat\gamma$ only touches $\theta'$). The heading
        spread falls a little (0.381 to 0.340 rad at the default), and the recovered-$\hat\gamma$ tile drops to
        0.000. Every sample then lies on a two-dimensional surface in $(x', y', \theta')$: Table 5.1 asked to
        score a pose off that surface finds no $(\hat v, \hat\omega)$ that reaches it (p. 129). That is why the
        book adds the third term. The round-trip tile is the invariant: `velocity_inverse` of a sample, pushed back
        through `velocity_forward`, returns the sample, 0 of 300 off. It holds while each step turns less than a
        half turn (card C3, trick 6).
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.4b velocity density, sign of v


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.4b · The velocity density and the sign of $\hat v$ (Table 5.1, lines 2–9)

        Same start $(0, 0, 0)$, $\Delta t = 2$ s, the moderate $\alpha$ of Fig 2.4a. Left: the log density
        of the end pose $(x', y')$ (heading fixed to the noise-free one) from the chord-form inverse of
        card C3. Right: the same sum of three log-probabilities with $\hat v$, $\hat\omega$, $\hat\gamma$ from
        the book's lines 2–9 as printed (only $\Delta\theta$ is wrapped, so the seam does not hide the point).

        **Predict first.** Command a **right** turn ($\omega < 0$, $v > 0$). Which panel puts its bright
        ridge on the arc the robot actually drives? What does the right panel show for a **reversing**
        command ($v < 0$, $\omega > 0$)?
        """
    )
    return


@app.cell
def _(mo):
    b_v = mo.ui.slider(-1.2, 1.2, value=1.0, step=0.1, label="commanded v [m/s]", show_value=True)
    b_w = mo.ui.slider(-1.0, 1.0, value=-0.5, step=0.1, label="commanded ω [rad/s]", show_value=True)
    mo.vstack([b_v, b_w])
    return b_v, b_w


@app.cell
def _(P, R, b_v, b_w, book_inverse, ex, fx, go, make_subplots, mo, models, np, style):
    _dt = 2.0
    _a = models.ALPHA_VEL_L5
    _x0 = np.zeros(3)
    _v, _w = b_v.value, b_w.value
    _x1 = ex.velocity_forward(_x0, _v, _w, 0.0, _dt)

    def _lp_book(Xp):
        vh, wh, gh = book_inverse(_x0, Xp, _dt)
        return (ex.log_prob(_v - vh, _a[0] * _v * _v + _a[1] * _w * _w)
                + ex.log_prob(_w - wh, _a[2] * _v * _v + _a[3] * _w * _w)
                + ex.log_prob(gh, _a[4] * _v * _v + _a[5] * _w * _w))

    _g = np.linspace(-3, 3, 41)
    _Xg, _Yg = np.meshgrid(_g, _g)
    _grid = np.stack([_Xg, _Yg, np.full_like(_Xg, _x1[2])], axis=-1)
    _Zc = ex.log_motion_model_velocity(_grid, (_v, _w), _x0, _a, _dt)
    _Zb = _lp_book(_grid)
    _top = float(np.nanmax(_Zc))
    _clip = lambda Z: np.where(np.isfinite(Z), np.clip(Z, _top - 40, _top), np.nan)
    _cs = [[0, "#f1efe8"], [1, R["teal"]]]

    b_fig = make_subplots(rows=1, cols=2, subplot_titles=("chord-form inverse (card C3)", "Table 5.1 line 7 as printed"),
                          horizontal_spacing=0.08)
    for _c, _Z in ((1, _Zc), (2, _Zb)):
        b_fig.add_trace(go.Heatmap(x=_g, y=_g, z=_clip(_Z), colorscale=_cs, zmin=_top - 40, zmax=_top,
                                   showscale=False, hoverinfo="skip"), row=1, col=_c)
        b_fig.add_trace(go.Scatter(x=[_x1[0]], y=[_x1[1]], mode="markers", showlegend=False,
                                   marker=dict(color=R["blue"], size=11, symbol="x")), row=1, col=_c)
        b_fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers", showlegend=False,
                                   marker=dict(color=R["gray"], size=9)), row=1, col=_c)
        b_fig.update_xaxes(title_text="x′ [m]", row=1, col=_c)
    b_fig.update_yaxes(scaleanchor="x", scaleratio=1, row=1, col=1)
    b_fig.update_yaxes(scaleanchor="x2", scaleratio=1, row=1, col=2)
    b_fig.update_yaxes(title_text="y′ [m]", row=1, col=1)
    b_fig.update_layout(title="Fig 2.4b · log p(x′ | u, x) over end position; × = noise-free end pose", height=420)

    _vb, _wb, _gb = (float(np.asarray(t)) for t in book_inverse(_x0, _x1, _dt))
    _vc, _wc, _gc = (float(np.asarray(t)) for t in ex.velocity_inverse(_x0, _x1, _dt))
    _lpc = float(ex.log_motion_model_velocity(_x1, (_v, _w), _x0, _a, _dt))
    _lpb = float(_lp_book(_x1))
    _nan = _vb != _vb
    _wrong = (not _nan) and abs(_vb - _v) > 1e-6
    b_tiles = {
        "commanded v": f"{fx(_v, 2)} m/s",
        "v̂ line 7  |  chord inverse": f"{fx(_vb, 2)}  |  {fx(_vc, 2)} m/s",
        "ω̂ line 8  |  chord inverse": f"{fx(_wb, 2)}  |  {fx(_wc, 2)} rad/s",
        "log p at the noise-free end pose, book": f"{fx(_lpb, 2)}",
        "log p at the noise-free end pose, chord": f"{fx(_lpc, 2)}",
        "book minus chord": f"{fx(_lpb - _lpc, 2)} nats",
    }
    _chip = ("line 7: nan (straight line or no motion)" if _nan
             else "line 7 has the wrong sign" if _wrong else "line 7 agrees with the command")
    style.card(mo.ui.plotly(b_fig), fig="Fig 2.4b · Table 5.1 line 7", title="Which way is forward?",
               hint="Sweep ω from + to − with v > 0 · flip v · stop at ω = 0 and at v = 0",
               chip=_chip, chip_state="warn" if _nan else ("bad" if _wrong else "ok"), tiles=b_tiles)
    return b_fig, b_tiles


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** With $v > 0$, $\omega < 0$ the printed lines give $\hat v < 0$ (line 7
        takes its sign from $\Delta\theta$, and $r^*$ is a distance), so the right panel scores the very pose
        the robot reached with a huge penalty and its ridge sits somewhere else. The chord form takes the sign
        from the displacement along the initial heading and the ridge goes through the cross. For $v < 0$,
        $\omega > 0$ the book's panel is also wrong; whenever $v$ and $\omega$ have the same sign the two agree, which is why the
        printed table looks fine on a left-turning test. At $\omega = 0$ line 2 divides by zero (p. 130) and
        the right panel goes blank; at $v = 0$ a spin in place is booked as $\hat\gamma$ in the chord form
        (card C3, what breaks first, item 4).
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.4c odometry


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.4c · The odometry sampler (Tables 5.5–5.6, eq. 5.34–5.40)

        Particles start at $(0, 0, 0)$. The odometer reports a step of $d$ metres along its own heading
        $\bar\theta$ (negative $d$ is reversing), then a turn of $\psi$. Both clouds use the same 300 normal
        draws, so only the variances differ: coral is Table 5.6 as printed, teal is card C4
        (`rot_for_noise`, rotate-in-place rule). $\alpha = (0.01, 0.0005, 0.01, 0.0005)$ times the slider.

        **Predict first.** Back up 0.5 m in a straight line ($d = −0.5$, $\psi = 0$). Does the printed
        sampler spread the headings more, less, or the same as driving forward 0.5 m? Then set $d = 0$,
        $\psi = 30°$ and change $\bar\theta$: should the answer depend on it?
        """
    )
    return


@app.cell
def _(mo):
    c_d = mo.ui.slider(-1.5, 1.5, value=-0.5, step=0.1, label="odometry step d [m]", show_value=True)
    c_psi = mo.ui.slider(-90, 90, value=0, step=10, label="turn ψ [deg]", show_value=True)
    c_th = mo.ui.slider(-180, 180, value=150, step=15, label="odometry frame heading θ̄ [deg]", show_value=True)
    c_s = mo.ui.slider(-1.0, 1.0, value=0.0, step=0.1, label="log₁₀ scale on α₁…α₄", show_value=True)
    mo.vstack([c_d, c_psi, c_th, c_s])
    return c_d, c_psi, c_s, c_th


@app.cell
def _(R, Stream, book_odometry_sample, c_d, c_psi, c_s, c_th, ex, fx, go, mo, models, np, style):
    _M = 300
    _alpha = np.array(models.ALPHA_ODO_L7) * 10 ** c_s.value
    _tb = np.deg2rad(c_th.value)
    _P0 = np.array([0.0, 0.0, _tb])
    _P1 = np.array([0.0 + c_d.value * np.cos(_tb), 0.0 + c_d.value * np.sin(_tb), _tb + np.deg2rad(c_psi.value)])
    _X0 = np.zeros((_M, 3))
    _Xr = ex.sample_motion_model_odometry((_P0, _P1), _X0, _alpha, Stream())
    _Xb, _dbook = book_odometry_sample((_P0, _P1), _X0, _alpha, Stream())
    _drob = ex.odometry_params(_P0, _P1)
    _free_th = float(models.wrap(_drob[0] + _drob[2]))

    def _spread(X):
        h = float(models.wrap(X[:, 2] - _free_th).std())
        p = float(np.sqrt(((X[:, :2] - X[:, :2].mean(0)) ** 2).sum(1).mean()))
        return h, p

    _hr, _pr = _spread(_Xr)
    _hb, _pb = _spread(_Xb)
    _ratio = _hb / max(_hr, 1e-12)

    c_fig = go.Figure()
    c_fig.add_trace(go.Scatter(x=_Xb[:, 0], y=_Xb[:, 1], mode="markers", name="Table 5.6 as printed",
                               marker=dict(size=4, color=R["coral"], opacity=0.45)))
    c_fig.add_trace(go.Scatter(x=_Xr[:, 0], y=_Xr[:, 1], mode="markers", name="card C4",
                               marker=dict(size=4, color=R["teal"], opacity=0.55)))
    for _X, _col, _nm in ((_Xb, R["coral"], "printed heading"), (_Xr, R["teal"], "C4 heading")):
        _m = _X[:40]
        _xs = np.column_stack([_m[:, 0], _m[:, 0] + 0.06 * np.cos(_m[:, 2]), np.full(len(_m), np.nan)]).ravel()
        _ys = np.column_stack([_m[:, 1], _m[:, 1] + 0.06 * np.sin(_m[:, 2]), np.full(len(_m), np.nan)]).ravel()
        c_fig.add_trace(go.Scatter(x=_xs, y=_ys, mode="lines", line=dict(color=_col, width=1), showlegend=False,
                                   hoverinfo="skip"))
    c_fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers", name="start (heading 0)",
                               marker=dict(color=R["gray"], size=10)))
    c_fig.update_layout(title="Fig 2.4c · odometry step applied to 300 particles (ticks = headings of 40)",
                        xaxis_title="x′ [m]", yaxis_title="y′ [m]", height=440)
    c_fig.update_yaxes(scaleanchor="x", scaleratio=1)

    def _deg(a):
        return fx(np.rad2deg(a), 1)

    c_tiles = {
        "δrot1, δtrans, δrot2 printed": f"{_deg(_dbook[0])}°, {fx(_dbook[1], 2)} m, {_deg(_dbook[2])}°",
        "δrot1, δtrans, δrot2 card C4": f"{_deg(_drob[0])}°, {fx(_drob[1], 2)} m, {_deg(_drob[2])}°",
        "heading spread printed | C4": f"{fx(_hb, 3)} | {fx(_hr, 3)} rad",
        "position spread printed | C4": f"{fx(_pb, 3)} | {fx(_pr, 3)} m",
    }
    _bad = _ratio > 1.2
    style.card(mo.ui.plotly(c_fig), fig="Fig 2.4c · Tables 5.5–5.6", title="The odometry model at its corners",
               hint="Reverse (d < 0) · spin in place (d = 0, ψ ≠ 0) and sweep θ̄ · scale α",
               chip=f"printed variances inflate heading noise ×{fx(_ratio, 1)}" if _bad else "printed and C4 agree",
               chip_state="warn" if _bad else "ok", tiles=c_tiles)
    return c_fig, c_tiles


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** Reversing makes the printed decomposition $\delta_{rot1} = \delta_{rot2}
        = \pm\pi$, and $\alpha_1\delta_{rot}^2$ then inflates the heading noise although the robot never turned;
        `rot_for_noise` measures each rotation from the nearer of straight ahead and straight back, so
        backing up is as quiet as driving forward. For a turn in place ($d = 0$), $\mathrm{atan2}(0, 0)$ gives
        $\delta_{rot1} = -\bar\theta$ in the printed lines, so the heading spread follows the odometer's own
        frame; the 1 cm threshold makes it independent of $\bar\theta$ (card C4, tricks 2–3). The tick marks show
        the heading of 40 particles. The book warns about the unwrapped $\delta_{rot2}$ error on p. 135;
        that bug lives in the density (T4), not in these two samplers.
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.4d motion with a map


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.4d · Motion with a map (Table 5.7, eq. 5.48)

        The robot starts at $(0, 0, 90°)$ facing a wall, commanded $v$ and $\omega = -0.35$ rad/s for
        $\Delta t = 3$ s, noise $\alpha = (0.03 \times 4,\ 0.005 \times 2)$. The wall is $0.15$ m thick; grown
        by the robot radius (0.15 m) it is $0.45$ m thick in configuration space (dashed). 200 particles go
        through `sample_motion_model_with_map`: draws that land in the grown wall are redrawn, at most `cap`
        times. The map is checked at $N$ equally spaced points along the arc, the last one being the end pose.

        **Predict first.** With one check ($N = 1$, the book's end-pose test) and a long step ($v = 1.0$ m/s,
        a 3 m step), what fraction of the accepted particles drove through the wall? How many checks make
        that fraction almost vanish, and what does it cost in rejected particles?
        """
    )
    return


@app.cell
def _(mo):
    d_v = mo.ui.slider(0.2, 1.6, value=1.0, step=0.1, label="commanded v [m/s]", show_value=True)
    d_n = mo.ui.slider(1, 20, value=1, step=1, label="map checks per motion N", show_value=True)
    d_cap = mo.ui.slider(1, 10, value=10, step=1, label="retry cap (draws per particle)", show_value=True)
    mo.vstack([d_v, d_n, d_cap])
    return d_cap, d_n, d_v


@app.cell
def _(R, Stream, d_cap, d_n, d_v, ex, fx, go, mo, models, np, style):
    _M, _dt, _w = 200, 3.0, -0.35
    _a = (0.03, 0.03, 0.03, 0.03, 0.005, 0.005)
    _wall = models.WallMap()
    _x0 = np.array([0.0, 0.0, np.pi / 2])
    _u = (d_v.value, _w)
    _N = d_n.value

    def _sampler(u, X, rng):
        return ex.sample_motion_model_velocity(u, X, _a, _dt, rng)

    def _arc_points(Xn, k):
        vh, wh, _ = ex.velocity_inverse(_x0, Xn, _dt)
        return ex.velocity_forward(_x0, vh, wh, 0.0, _dt * k)

    def _in_free_path(Xn):
        ok = np.ones(len(Xn), bool)
        for k in range(1, _N + 1):
            ok &= _wall.in_free(_arc_points(Xn, k / _N))
        return ok

    _X0 = np.tile(_x0, (_M, 1))
    _first = _sampler(_u, _X0, Stream())
    _free_first = float(_wall.in_free(_first).mean())
    _Xn, _pi = ex.sample_motion_model_with_map(_u, _X0, _sampler, _in_free_path, Stream(), max_tries=d_cap.value)
    _acc = _pi > 0
    _crossed = np.zeros(_M, bool)
    for _k in range(1, 201):
        _crossed |= ~_wall.in_free(_arc_points(_Xn, _k / 200))
    _through = _acc & _crossed
    _dead = ~_acc
    _frac_through = float(_through.sum() / max(_acc.sum(), 1))

    d_fig = go.Figure()
    d_fig.add_shape(type="rect", x0=_wall.wall_x, x1=_wall.wall_x + _wall.wall_w, y0=_wall.wall_y,
                    y1=_wall.wall_y + _wall.wall_h, fillcolor=R["gray"], opacity=0.6, line_width=0)
    d_fig.add_shape(type="rect", x0=_wall.wall_x - _wall.radius, x1=_wall.wall_x + _wall.wall_w + _wall.radius,
                    y0=_wall.wall_y - _wall.radius, y1=_wall.wall_y + _wall.wall_h + _wall.radius,
                    line=dict(color=R["gray"], dash="dash", width=1))
    _ok = _acc & ~_crossed
    d_fig.add_trace(go.Scatter(x=_Xn[_ok, 0], y=_Xn[_ok, 1], mode="markers", name="accepted, arc clear",
                               marker=dict(size=5, color=R["teal"], opacity=0.6)))
    d_fig.add_trace(go.Scatter(x=_Xn[_through, 0], y=_Xn[_through, 1], mode="markers", name="accepted, arc crossed the wall",
                               marker=dict(size=7, color=R["amber"], symbol="x")))
    d_fig.add_trace(go.Scatter(x=_Xn[_dead, 0], y=_Xn[_dead, 1], mode="markers", name="π = 0 after the cap",
                               marker=dict(size=6, color=R["coral"], symbol="circle-open")))
    _arc = np.array([ex.velocity_forward(_x0, _u[0], _w, 0.0, _dt * s) for s in np.linspace(0, 1, 60)])
    d_fig.add_trace(go.Scatter(x=_arc[:, 0], y=_arc[:, 1], mode="lines", name="noise-free arc",
                               line=dict(color=R["blue"], width=2)))
    d_fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers", name="start", marker=dict(color=R["gray"], size=10)))
    d_fig.update_layout(title="Fig 2.4d · 200 particles after one step with a wall in the way", xaxis_title="x′ [m]",
                        yaxis_title="y′ [m]", height=480)
    d_fig.update_yaxes(scaleanchor="x", scaleratio=1, range=[-0.5, 3.4])
    d_fig.update_xaxes(range=[-0.8, 3.2])

    _step = d_v.value * _dt / _N
    _thick = _wall.wall_h + 2 * _wall.radius
    d_tiles = {
        "free at the first draw (end pose)": f"{fx(100 * _free_first, 1)} %",
        "π = 0 after the cap": f"{int(_dead.sum())} of {_M}",
        "accepted whose arc crossed the wall": f"{fx(100 * _frac_through, 1)} % ({int(_through.sum())} of {int(_acc.sum())})",
        "check spacing v·Δt / N": f"{fx(_step, 2)} m  (wall in C-space: {fx(_thick, 2)} m)",
    }
    _tunnel = _frac_through > 0.05
    style.card(mo.ui.plotly(d_fig), fig="Fig 2.4d · Table 5.7", title="The end-pose check lets particles through",
               hint="Raise N until the amber × vanish · cut the cap to 1 and count the dead particles · speed up",
               chip="tunnelling: spacing is larger than the wall" if _tunnel else "arc checks keep particles out of the wall",
               chip_state="warn" if _tunnel else "ok", tiles=d_tiles)
    return d_fig, d_tiles


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** With $N = 1$ the only test is the end pose, so a particle that crossed
        the wall in the middle of the arc and landed behind it is accepted (eq. 5.51 drops the path, p. 143):
        77.0 % of the accepted particles at the default, the amber ×. At $N = 10$ (spacing 0.30 m, below the 0.45 m
        configuration-space wall) it is 0.6 %, which is the book's advice to predict often. The price shows in
        the cap tile: the arcs that survive are the minority, so 36 of 200 particles use up all ten draws and
        come back with $\pi = 0$ (resampling removes them); at $N = 1$ none do. Table 5.7's loop has no bound
        (p. 141); the cap is what keeps a robot facing a wall from freezing the filter. A shorter step (smaller $v$,
        or the same $v$ at a higher update rate) gets the same safety without the rejections.

        ## Before you leave

        - [ ] Write, from memory, the three lines that turn $(\hat v, \hat\omega, \hat\gamma)$ into a pose (eq. 5.16), and say why the chord form needs no case for $\omega = 0$.
        - [ ] Say which way $\hat v$ points in Table 5.1 line 7 for a right turn, and the one-line patch.
        - [ ] `pytest exercises/tests/test_T3.py -q` with `STUDY_IMPL=solution`, then without.
        """
    )
    return


if __name__ == "__main__":
    app.run()
