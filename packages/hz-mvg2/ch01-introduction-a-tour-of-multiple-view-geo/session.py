# /// script
# requires-python = ">=3.11"
# dependencies = ["marimo", "numpy", "scipy", "matplotlib", "plotly"]
# ///
"""Interactive session for H&Z ch. 1 — a tour of multiple view geometry.

    marimo edit session.py        # work in it
    marimo run session.py         # read-only app

Four figures, Fig 3.1a..3.1d, colours as in viz/README.md: blue = reference, coral = measurement /
second view, teal = the quantity being taught, gray = structure. Every "Predict first" cell asks for
your guess before the plot answers it; write the guess down.

Uses the reference solution in exercises/solutions so the session works before you have done T3.
Switch USE_MY_CODE to True to drive the plots with your own exercise.py. The arithmetic lives in
session_model.py; interactive.html re-implements it in JS from the same data.
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
    import session_model as sm

    return HERE, P, R, USE_MY_CODE, ex, go, mo, np, sm, style


@app.cell
def _(mo):
    mo.md(
        r"""
        # Session t3.1 · A tour of multiple view geometry

        Four figures, one idea: images are linear in homogeneous coordinates, and what they cannot
        tell you is a group of transformations. Each slider has a **Predict first** prompt above it.

        1. **Fig 3.1a** — parallel rails: a point at infinity is an ordinary image point (pp. 2–3, 7).
        2. **Fig 3.1b** — eq. (1.1): move the whole reconstruction by a 4×4 $H$, the images do not change (p. 11).
        3. **Fig 3.1c** — $\mathbf{x}'^\top F \mathbf{x} = 0$: an epipolar line and what noise does to it (pp. 11–12).
        4. **Fig 3.1d** — the tracked robot: when one homography is enough (Fig. 1.1, pp. 7, 9, 16).
        """
    )
    return


# ------------------------------------------------------------------ Fig 3.1a


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 3.1a · Points at infinity (pp. 2–3, 7)

        Two parallel floor rails seen by the tracked robot's camera (h = 0.55 m). The rails never meet
        in the world; the ideal point $(\mathbf{d}, 0)^\top$ of their direction is an ordinary point
        of $\mathbb{P}^3$, and $\mathbf{x} = P\,(\mathbf{d}, 0)^\top$ is where they meet in the image.

        **Predict first.** Pitch the camera down 15° → 40°. Does the vanishing point move up or down in the
        image, and by how many pixels (f = 500 px)? Then turn the rails to 90° from the camera heading:
        where do they meet?
        """
    )
    return


@app.cell
def _(mo):
    a_pitch = mo.ui.slider(0, 45, value=15, step=1, label="camera pitch [deg]", show_value=True)
    a_gap = mo.ui.slider(0.4, 3.0, value=1.2, step=0.1, label="rail gap [m]", show_value=True)
    a_yaw = mo.ui.slider(0, 90, value=0, step=1, label="rail direction vs heading [deg]", show_value=True)
    mo.vstack([a_pitch, a_gap, a_yaw])
    return a_gap, a_pitch, a_yaw


@app.cell
def _(P, R, a_gap, a_pitch, a_yaw, ex, go, mo, np, sm, style):
    ra = sm.fig_a(ex, a_pitch.value, a_gap.value, a_yaw.value)
    fa = go.Figure()
    fa.add_shape(type="rect", x0=0, y0=0, x1=640, y1=480, line=dict(color=R["gray"], width=1))
    for _i, (_u, _v) in enumerate(ra["rails"]):
        fa.add_trace(go.Scatter(x=_u, y=_v, mode="lines", line=dict(color=R["blue"], width=3), name="rail", showlegend=_i == 0))
    if ra["vp"] is not None:
        fa.add_trace(go.Scatter(x=[ra["vp"][0]], y=[ra["vp"][1]], mode="markers", marker=dict(color=R["teal"], size=12, symbol="diamond"), name="vanishing point"))
    fa.add_hline(y=sm.CY - sm.F_PX * np.tan(np.radians(a_pitch.value)), line=dict(color=R["gray"], dash="dot", width=1))
    fa.update_layout(
        title="image of two parallel rails: they meet at x = P (d, 0)ᵀ",
        xaxis=dict(title="u [px]", range=[-300, 940]),
        yaxis=dict(title="v [px]", range=[680, -200], scaleanchor="x"),
        height=420,
    )
    style.card(mo.ui.plotly(fa), fig="Fig 3.1a · pp. 2–3, 7", title="Parallel lines meet at an image point; w = 0 puts it at infinity",
               hint="Drag pitch and watch the horizon row; drag the direction to 90° and watch w.", chip=ra["chip"][0],
               chip_state=ra["chip"][1], tiles=ra["tiles"])
    return fa, ra


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** The vanishing point rides the horizon row $v_0 - f\tan(\text{pitch})$:
        raising the pitch moves it up by f(tan 40° − tan 15°) px; read the row off the tile at both settings. At 90° to the heading the rails are parallel to the
        image plane, $w = 0$, and the vanishing point is itself a point at infinity of the image. This is
        the "points at infinity are ordinary points" claim of p. 3, in a camera (p. 7).
        """
    )
    return


# ------------------------------------------------------------------ Fig 3.1b


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 3.1b · The projective ambiguity (eq. 1.1, p. 11)

        Two cameras, 60 points. Replace every point $\mathbf{X}_i$ by $H\mathbf{X}_i$ and every camera $P$ by
        $P H^{-1}$, with $H = \begin{bmatrix} I & 0 \\ \mathbf{v}^\top & 1 \end{bmatrix}$. Gray = the true scene, teal = what
        the same images are equally happy with.

        **Predict first.** At $s = 0.08$ (the depth component of $\mathbf{v}$), does the max reprojection
        change come out at about 0.1 px, 1 px, or round-off? Which points reach the plane at infinity first as $s$ goes negative, the near ones or the far ones, and at what $s$?
        """
    )
    return


@app.cell
def _(mo):
    b_s = mo.ui.slider(-0.12, 0.3, value=0.08, step=0.01, label="v_z (depth part of v)", show_value=True)
    b_u = mo.ui.slider(-0.2, 0.2, value=0.0, step=0.01, label="v_x (sideways part of v)", show_value=True)
    mo.vstack([b_s, b_u])
    return b_s, b_u


@app.cell
def _(R, b_s, b_u, ex, go, mo, sm, style):
    rb = sm.fig_b(ex, b_s.value, b_u.value)
    fb = go.Figure()
    fb.add_trace(go.Scatter(x=rb["orig"][:, 0], y=rb["orig"][:, 2], mode="markers", marker=dict(color=R["gray"], size=6), name="true scene"))
    fb.add_trace(go.Scatter(x=rb["new"][:, 0], y=rb["new"][:, 2], mode="markers", marker=dict(color=R["teal"], size=7), name="after H (same images)"))
    _C2, _C2n, _C1n = rb["C"]
    fb.add_trace(go.Scatter(x=[0, _C2[0]], y=[0, _C2[2]], mode="markers", marker=dict(color=R["gray"], size=11, symbol="triangle-up"), name="true cameras"))
    fb.add_trace(go.Scatter(x=[_C1n[0], _C2n[0]], y=[_C1n[2], _C2n[2]], mode="markers", marker=dict(color=R["blue"], size=11, symbol="triangle-up"), name="cameras after H"))
    fb.update_layout(
        title="top view (X, Z): same two images, a different 'reconstruction'",
        xaxis=dict(title="X [m]", range=[-25, 25]), yaxis=dict(title="Z [m]", range=[-6, 40], scaleanchor="x"), height=440,
    )
    style.card(mo.ui.plotly(fb), fig="Fig 3.1b · eq. (1.1), p. 11", title="The images cannot tell the scene from its image under H",
               hint=f"{rb['dropped']} points too near infinity to draw." if rb["dropped"] else "Push v_z negative until points fly off.",
               chip=rb["chip"][0], chip_state=rb["chip"][1], tiles=rb["tiles"])
    return fb, rb


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** Reprojection never changes (the tile stays at round-off) while lengths,
        depths and ratios of lengths change freely. Points with $\mathbf{v}^\top\mathbf{X} + 1 < 0$ went through the plane at
        infinity, the far ones first, at $v_z = -1/Z_{max}$ ($Z_{max}$ = 11.9 m here, so about −0.084), so a projective reconstruction does not even know which side of the camera is in front.
        Page 11 only says the reconstruction is fixed up to H; front and back (cheirality) is H&Z ch. 21, p. 515.
        """
    )
    return


# ------------------------------------------------------------------ Fig 3.1c


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 3.1c · The epipolar constraint (pp. 11–12)

        Image 2 of the cards' scene. A point $\mathbf{x}$ in image 1 gives the line $\mathbf{l}' = F\mathbf{x}$ in
        image 2; the match $\mathbf{x}'$ must lie on it. Every line passes through the epipole $\mathbf{e}'$
        (far to the right here). Noise is added to the image-2 points only.

        **Predict first.** With 1 px of noise on every image-2 point, is the median distance of $\mathbf{x}'$ to its line
        about 0.3, 0.7 or 1.4 px? Why is it not the noise std?
        """
    )
    return


@app.cell
def _(mo):
    c_idx = mo.ui.slider(0, 59, value=7, step=1, label="point index", show_value=True)
    c_sigma = mo.ui.slider(0.0, 3.0, value=1.0, step=0.1, label="noise σ on image 2 [px]", show_value=True)
    mo.vstack([c_idx, c_sigma])
    return c_idx, c_sigma


@app.cell
def _(R, c_idx, c_sigma, ex, go, mo, np, sm, style):
    rc = sm.fig_c(ex, c_idx.value, c_sigma.value)
    fc = go.Figure()
    _xs = np.array([-100.0, 740.0])
    for _k in range(0, 60, 5):
        _l = sm.two_view_scene().F @ rc["x"][_k]
        fc.add_trace(go.Scatter(x=_xs, y=-(_l[0] * _xs + _l[2]) / _l[1], mode="lines", line=dict(color=R["gray"], width=1), opacity=0.35, showlegend=False, hoverinfo="skip"))
    _l = rc["line"]
    fc.add_trace(go.Scatter(x=_xs, y=-(_l[0] * _xs + _l[2]) / _l[1], mode="lines", line=dict(color=R["blue"], width=3), name="l′ = F x"))
    fc.add_trace(go.Scatter(x=rc["xp"][:, 0], y=rc["xp"][:, 1], mode="markers", marker=dict(color=R["coral"], size=5, opacity=0.5), name="x′ (all points)"))
    fc.add_trace(go.Scatter(x=[rc["xp"][rc["idx"], 0]], y=[rc["xp"][rc["idx"], 1]], mode="markers", marker=dict(color=R["coral"], size=11), name="this x′"))
    fc.add_trace(go.Scatter(x=[rc["xp"][rc["idx"], 0], rc["foot"][0]], y=[rc["xp"][rc["idx"], 1], rc["foot"][1]], mode="lines", line=dict(color=R["teal"], width=3), name="distance"))
    fc.add_shape(type="rect", x0=0, y0=0, x1=640, y1=480, line=dict(color=R["gray"], width=1))
    fc.update_layout(title="image 2: epipolar lines of every 5th point, and the selected match",
                     xaxis=dict(title="u′ [px]", range=[-40, 680]), yaxis=dict(title="v′ [px]", range=[520, -40], scaleanchor="x"), height=440)
    style.card(mo.ui.plotly(fc), fig="Fig 3.1c · pp. 11–12", title="A match lies on its epipolar line; noise moves it off by less than σ",
               hint="Set σ to 0, then raise it and compare the median with σ.", chip=rc["chip"][0], chip_state=rc["chip"][1], tiles=rc["tiles"])
    return fc, rc


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** Only the component of the noise perpendicular to the line counts, so the median distance
        sits below σ. The noise-free residual is zero to round-off and $\det F = 0$: F has rank 2, which is why the lines
        meet in one point (p. 11). F has 7 degrees of freedom and each match gives one equation x′ᵀFx = 0, so seven matches is the least that can
        pin it down (to one or three solutions, §11.1.2). The book states the "at least 7 points" of p. 11 without this reason.
        """
    )
    return


# ------------------------------------------------------------------ Fig 3.1d


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 3.1d · When one homography is enough (Fig. 1.1, pp. 7, 9, 16)

        The tracked robot drives $d$ metres forward and turns by $\psi$. Floor points are a plane (a $3\times3$ $H$ on
        $(X, Y, 1)$, p. 7); a rotation about the camera centre needs only $H = K R K^{-1}$, whatever the scene (Fig. 1.1c).
        Teal segments: where the rotation-only $H$ predicts each point versus where it really is.

        **Predict first.** Set $d = 0$ and mount offset 0: what do the teal segments look like? Now give the
        camera a 0.3 m offset ahead of the turning centre, still $d = 0$. Does the rotation-only $H$ still work?
        """
    )
    return


@app.cell
def _(mo):
    d_drive = mo.ui.slider(0.0, 1.0, value=0.3, step=0.05, label="drive forward d [m]", show_value=True)
    d_turn = mo.ui.slider(0, 30, value=10, step=1, label="turn ψ [deg]", show_value=True)
    d_fwd = mo.ui.slider(0.0, 0.5, value=0.0, step=0.05, label="camera ahead of turning centre [m]", show_value=True)
    mo.vstack([d_drive, d_turn, d_fwd])
    return d_drive, d_fwd, d_turn


@app.cell
def _(R, d_drive, d_fwd, d_turn, ex, go, mo, sm, style):
    rd = sm.fig_d(ex, d_drive.value, d_turn.value, d_fwd.value)
    fd = go.Figure()
    _sx, _sy = [], []
    for _p, _q in zip(rd["pred"], rd["u2"]):
        _sx += [_p[0], _q[0], None]
        _sy += [_p[1], _q[1], None]
    fd.add_trace(go.Scatter(x=_sx, y=_sy, mode="lines", line=dict(color=R["teal"], width=2), name="rotation-only H → actual"))
    _fl = rd["floor"]
    fd.add_trace(go.Scatter(x=rd["u2"][_fl, 0], y=rd["u2"][_fl, 1], mode="markers", marker=dict(color=R["coral"], size=6), name="floor points, view 2"))
    fd.add_trace(go.Scatter(x=rd["u2"][~_fl, 0], y=rd["u2"][~_fl, 1], mode="markers", marker=dict(color=R["coral"], size=7, symbol="diamond-open"), name="clutter points, view 2"))
    fd.add_shape(type="rect", x0=0, y0=0, x1=640, y1=480, line=dict(color=R["gray"], width=1))
    fd.update_layout(title="view 2: prediction by x′ = K R K⁻¹ x against the measured x′",
                     xaxis=dict(title="u′ [px]", range=[-20, 660]), yaxis=dict(title="v′ [px]", range=[500, -20], scaleanchor="x"), height=460)
    style.card(mo.ui.plotly(fd), fig="Fig 3.1d · Fig. 1.1, pp. 7, 9, 16", title="Rotation needs one H for everything; translation leaves only the floor",
               hint="d = 0 and offset 0 is Fig. 1.1c; the floor tile is the plane of Fig. 1.1b.", chip=rd["chip"][0],
               chip_state=rd["chip"][1], tiles=rd["tiles"])
    return fd, rd


@app.cell
def _(mo):
    mo.md(
        r"""
        **What you should have seen.** At $d = 0$ with the camera on the turning centre the segments vanish for every
        point, floor or clutter: same centre, images differ by a homography (p. 9). Move the camera 0.3 m ahead of the centre and
        a pure turn becomes a translation of the camera, so parallax appears (a mount offset is a baseline).
        The floor tile stays at round-off all the time because the plane Z = 0 has its own $H$ (p. 7); that is why a
        visual-odometry initializer must try both $H$ and $F$ (T5).
        """
    )
    return


if __name__ == "__main__":
    app.run()
