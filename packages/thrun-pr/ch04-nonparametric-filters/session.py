# /// script
# requires-python = ">=3.11"
# dependencies = ["marimo", "numpy", "scipy", "plotly"]
# ///
"""Interactive session for Thrun ch. 4 — nonparametric filters.

    marimo edit session.py        # work in it
    marimo run session.py         # read-only app

Five figure cards, Fig 2.3a..2.3e, following viz/README.md: blue = estimate / belief, coral = measurement /
likelihood, teal = the quantity being taught, gray = truth and structure. Every card has a **Predict first**
prompt; write your guess down before touching a slider.

Every figure is deterministic (no random draws), so the readouts here and in interactive.html agree
to two decimals. Where the book samples, the session uses quantiles (Fig 2.3c), a slider for the one
random number (Fig 2.3d), or the exact expectation over all draws (Fig 2.3e).

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
    from scipy.special import ndtri
    from scipy.stats import binom, norm

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

    return HERE, P, R, USE_MY_CODE, binom, ex, go, mo, models, ndtri, norm, np, style


@app.cell
def _(mo):
    mo.md(
        r"""
        # Session t2.3 · Nonparametric filters

        Five figures. Work them in order; each slider has a **Predict first** prompt above it.

        1. **Fig 2.3a** — Table 4.1 on the ring corridor: when does a second door sighting leave one mode?
        2. **Fig 2.3b** — Table 4.2 in log odds: what forgetting the prior does to a map cell.
        3. **Fig 2.3c** — importance sampling (4.25)–(4.28): what a bad proposal costs.
        4. **Fig 2.3d** — the low-variance sampler, Table 4.4: one random number, M teeth.
        5. **Fig 2.3e** — sampling bias (4.38): how many particles before the measurement counts.
        """
    )
    return


# ------------------------------------------------------------------ Fig 2.3a histogram filter


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.3a · Table 4.1 on the ring corridor

        10 m ring, doors at 1.5, 4.0 and 7.5 m, 100 bins of 0.1 m. Uniform prior; see a door; drive $u$; see a door again.

        **Predict first.** At $u = 2.5$ m only one door pair is 2.5 m apart. How much of the belief ends up within
        1 m of 4.0 m: more or less than half? Now set $u = 3.5$ m. Which doors are 3.5 m apart, and how many modes survive?
        """
    )
    return


@app.cell
def _(mo):
    a_u = mo.ui.slider(0.0, 5.0, value=2.5, step=0.1, label="drive u [m]", show_value=True)
    a_sig = mo.ui.slider(0.05, 1.0, value=0.3, step=0.05, label="motion noise σ [m]", show_value=True)
    a_pf = mo.ui.slider(0.0, 0.4, value=0.1, step=0.01, label="false-positive floor", show_value=True)
    mo.vstack([a_u, a_sig, a_pf])
    return a_pf, a_sig, a_u


@app.cell
def _(P, R, a_pf, a_sig, a_u, ex, go, mo, models, np, style):
    ring = models.RingCorridor(R_proc=a_sig.value**2, p_false=a_pf.value)
    ca = (np.arange(100) + 0.5) * 0.1
    lik_a = ring.p_door(ca)
    b1 = np.exp(ex.hist_update(np.full(100, -np.log(100)), np.log(lik_a)))
    Ta = ex.transition_from_density(ca, a_u.value, ring.motion_pdf)
    b2 = ex.hist_predict(b1, Ta)
    b3 = np.exp(ex.hist_update(np.log(np.maximum(b2, 1e-300)), np.log(lik_a)))
    k_mode = int(np.argmax(b3))
    mass_mode = float(b3[ring.ring_dist(ca, ca[k_mode]) < 1.0].sum())

    figa = go.Figure()
    figa.add_trace(go.Bar(x=ca, y=b1, marker_color=R["gray"], opacity=0.45, name="after first door"))
    figa.add_trace(go.Bar(x=ca, y=b2, marker_color=R["blue"], opacity=0.35, name="after drive (line 3)"))
    figa.add_trace(go.Bar(x=ca, y=b3, marker_color=R["teal"], opacity=0.8, name="after second door (line 4)"))
    figa.add_trace(go.Scatter(x=ca, y=lik_a / lik_a.max() * b3.max(), mode="lines", line=dict(color=R["coral"], width=1.5),
                              name="p(door | x), scaled"))
    figa.update_layout(barmode="overlay", bargap=0, xaxis_title="x along the ring [m]", yaxis_title="p_k", height=380,
                       title="belief after door, drive, door")

    tiles_a = {
        "mode of bel(x)": f"{ca[k_mode]:.2f} m",
        "mass within 1 m of the mode": f"{mass_mode:.2f}",
        "Σ p_k (must be 1)": f"{b3.sum():.3f}",
        "mass at 1.5 / 4.0 / 7.5 m (±0.5 m)": " / ".join(f"{b3[ring.ring_dist(ca, d) < 0.5].sum():.2f}" for d in ring.DOORS),
    }
    style.card(mo.ui.plotly(figa), fig="Fig 2.3a · Table 4.1", title="Line 3 is a shift and a blur; line 4 is a product",
               hint="Drag u and watch which door pair lines up; raise the floor and watch the other modes refuse to die",
               chip="one dominant mode" if mass_mode > 0.5 else "still ambiguous",
               chip_state="ok" if mass_mode > 0.5 else "warn", tiles=tiles_a)
    return b1, b2, b3, ca, figa, k_mode, lik_a, mass_mode, ring, tiles_a


@app.cell
def _(mo):
    mo.accordion({"What you should have seen": mo.md(
        r"""
        At $u = 2.5$ m the 1.5 → 4.0 m pair is the only one consistent with both sightings, and 0.53 of the mass
        sits within 1 m of 4.0 m; the rest is held up by the false-positive floor, which multiplies every bin by at
        least 0.1. At $u = 3.5$ m the 4.0 → 7.5 m pair lines up instead. A wider motion noise blurs line 3 and lets
        mismatched pairs survive. This is the HMM forward pass of p. 87 on 100 states.
        """)})
    return


# ------------------------------------------------------------------ Fig 2.3b log odds


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.3b · Table 4.2: one occupancy cell in log odds

        30 readings from an inverse sensor model, hit or miss in a fixed pattern with the hit rate below.
        Teal: Table 4.2. Coral: the same code with "$-\,l_0$" forgotten.

        **Predict first.** With prior 0.5 the two curves coincide. With prior 0.3 and a 55% hit rate, does forgetting
        the prior make the cell look *more* or *less* occupied? Can it flip the final answer?
        """
    )
    return


@app.cell
def _(mo):
    b_prior = mo.ui.slider(0.05, 0.95, value=0.3, step=0.05, label="prior p(x)", show_value=True)
    b_rate = mo.ui.slider(0.0, 1.0, value=0.55, step=0.05, label="hit rate", show_value=True)
    b_hit = mo.ui.slider(0.5, 0.95, value=0.6, step=0.05, label="p(x | hit)", show_value=True)
    b_miss = mo.ui.slider(0.05, 0.5, value=0.15, step=0.05, label="p(x | miss)", show_value=True)
    mo.vstack([b_prior, b_rate, b_hit, b_miss])
    return b_hit, b_miss, b_prior, b_rate


@app.cell
def _(R, b_hit, b_miss, b_prior, b_rate, ex, go, mo, np, style):
    Tb = 30
    hits_b = ((np.arange(1, Tb + 1) * 0.6180339887498949) % 1.0) < b_rate.value   # fixed low-discrepancy pattern
    pinv_b = np.where(hits_b, b_hit.value, b_miss.value)
    l0_b = float(ex.prob_to_logodds(b_prior.value))
    l_ok, l_bad = [l0_b], [l0_b]
    for pz_b in pinv_b:
        l_ok.append(float(ex.logodds_update(l_ok[-1], pz_b, l0_b)))
        l_bad.append(float(ex.logodds_update(l_bad[-1], pz_b, 0.0)))     # the bug: prior never taken out
    two = np.array([b_prior.value, 1 - b_prior.value])
    for pz_b in pinv_b:                                                  # oracle: Table 4.1 on two states
        two = np.array([pz_b / b_prior.value, (1 - pz_b) / (1 - b_prior.value)]) * two
        two /= two.sum()
    bel_ok, bel_bad = float(ex.logodds_to_prob(l_ok[-1])), float(ex.logodds_to_prob(l_bad[-1]))

    tb = np.arange(Tb + 1)
    figb = go.Figure()
    figb.add_trace(go.Scatter(x=tb, y=l_ok, mode="lines", line=dict(color=R["teal"], width=2, shape="hv"), name="l_t, Table 4.2"))
    figb.add_trace(go.Scatter(x=tb, y=l_bad, mode="lines", line=dict(color=R["coral"], width=1.5, dash="dash", shape="hv"), name="l_t, forgot − l₀"))
    figb.add_trace(go.Scatter(x=tb[1:][hits_b], y=np.zeros(hits_b.sum()), mode="markers", marker=dict(color=R["gray"], size=6, symbol="line-ns-open"), name="hit"))
    figb.update_layout(xaxis_title="reading t", yaxis_title="log odds l_t", height=360, title="log odds over 30 readings")

    tiles_b = {
        "bel_T, Table 4.2": f"{bel_ok:.3f}",
        "bel_T, Table 4.1 on two states": f"{two[0]:.3f}",
        "|difference| (must be 0)": f"{abs(bel_ok - two[0]):.3f}",
        "bel_T with − l₀ forgotten": f"{bel_bad:.3f}",
    }
    flipped = (bel_ok > 0.5) != (bel_bad > 0.5)
    style.card(mo.ui.plotly(figb), fig="Fig 2.3b · Table 4.2, (4.20)", title="Add the evidence, take the prior back out",
               hint="Set the prior to 0.5 and the curves merge; move it away and the dashed curve drifts with no evidence",
               chip="forgetting l₀ flips the answer" if flipped else "same side of 0.5",
               chip_state="warn" if flipped else "ok", tiles=tiles_b)
    return Tb, bel_bad, bel_ok, figb, flipped, hits_b, l0_b, l_bad, l_ok, pinv_b, tb, tiles_b, two


@app.cell
def _(mo):
    mo.accordion({"What you should have seen": mo.md(
        r"""
        Table 4.2 and Table 4.1 on two states agree exactly at every setting: log odds is a reparameterization, not
        an approximation. Forgetting $-l_0$ adds the prior's log odds once per reading, $T\,l_0$ in total, so with
        prior 0.3 the cell drifts toward free by 0.85 per reading and, at the defaults, reports 0.000 where the
        right answer is 0.999. With prior 0.5, $l_0 = 0$ and the bug is invisible: the reason it survives in grid
        code (p. 96 says "addition"; (4.20) subtracts).
        """)})
    return


# ------------------------------------------------------------------ Fig 2.3c importance sampling


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.3c · Importance sampling, (4.25)–(4.28)

        Target $f = 0.55\,\mathcal N(2, 0.6^2) + 0.45\,\mathcal N(4.5, 1.4^2)$ (Fig L6), estimate $P_f(0 < x < 3)$.
        Proposal $g = \mathcal N(\mu_g, \sigma_g^2)$. The $M$ samples are the quantiles of $g$, so the figure is
        deterministic; random draws add the $1/\sqrt M$ jitter of lecture L8 on top.

        **Predict first.** Put $g$ at $\mu_g = 9$, $\sigma_g = 1$, where the book's Fig 4.4 has it. Is the estimate
        too high or too low? What does $N_\text{eff}/M$ say, and is that warning enough?
        """
    )
    return


@app.cell
def _(mo):
    c_mu = mo.ui.slider(0.0, 10.0, value=3.5, step=0.1, label="proposal mean μ_g", show_value=True)
    c_sd = mo.ui.slider(0.3, 4.0, value=2.0, step=0.1, label="proposal std σ_g", show_value=True)
    c_M = mo.ui.slider(10, 2000, value=200, step=10, label="samples M", show_value=True)
    mo.vstack([c_mu, c_sd, c_M])
    return c_M, c_mu, c_sd


@app.cell
def _(R, c_M, c_mu, c_sd, ex, go, mo, ndtri, norm, np, style):
    f_logpdf = lambda x: np.logaddexp(np.log(0.55) + norm.logpdf(x, 2.0, 0.6), np.log(0.45) + norm.logpdf(x, 4.5, 1.4))
    g_logpdf = lambda x: norm.logpdf(x, c_mu.value, c_sd.value)
    xs_c = c_mu.value + c_sd.value * ndtri((np.arange(c_M.value) + 0.5) / c_M.value)
    inA = lambda x: ((x > 0) & (x < 3)).astype(float)
    est_c, neff_c = ex.is_estimate(xs_c, f_logpdf, g_logpdf, inA)
    P_true = float(0.55 * (norm.cdf(3, 2, 0.6) - norm.cdf(0, 2, 0.6)) + 0.45 * (norm.cdf(3, 4.5, 1.4) - norm.cdf(0, 4.5, 1.4)))
    lw_c = f_logpdf(xs_c) - g_logpdf(xs_c)
    w_c = np.exp(lw_c - lw_c.max())

    xx_c = np.linspace(-1, 12, 500)
    figc = go.Figure()
    figc.add_trace(go.Scatter(x=xx_c, y=np.exp(f_logpdf(xx_c)), mode="lines", line=dict(color=R["blue"], width=2), name="target f"))
    figc.add_trace(go.Scatter(x=xx_c, y=np.exp(g_logpdf(xx_c)), mode="lines", line=dict(color=R["gray"], width=2), name="proposal g"))
    stem_y = np.column_stack([np.zeros_like(xs_c), -0.15 * w_c, np.full_like(xs_c, np.nan)]).ravel()
    figc.add_trace(go.Scatter(x=np.repeat(xs_c, 3), y=stem_y, mode="lines", line=dict(color=R["teal"], width=1),
                              name="weight f/g (down)"))
    figc.add_vrect(x0=0, x1=3, fillcolor=R["teal"], opacity=0.06, line_width=0)
    figc.update_layout(xaxis_title="x", yaxis_title="density / weight", height=360, title="samples of g, weighted toward f")

    tiles_c = {
        "IS estimate (4.28)": f"{est_c:.3f}",
        "exact P_f(0 < x < 3)": f"{P_true:.3f}",
        "error": f"{est_c - P_true:+.3f}".replace("-", "−"),
        "N_eff / M": f"{neff_c / c_M.value:.3f}",
    }
    bad_c = neff_c / c_M.value < 0.1
    style.card(mo.ui.plotly(figc), fig="Fig 2.3c · (4.25)–(4.28)", title="The proposal decides what the samples can see",
               hint="Slide g away from f and watch N_eff collapse; shrink σ_g and watch a mode of f disappear",
               chip="proposal misses the target" if bad_c else "proposal covers f",
               chip_state="warn" if bad_c else "ok", tiles=tiles_c)
    return P_true, bad_c, est_c, f_logpdf, figc, stem_y, g_logpdf, inA, lw_c, neff_c, tiles_c, w_c, xs_c, xx_c


@app.cell
def _(mo):
    mo.accordion({"What you should have seen": mo.md(
        r"""
        With $g$ covering $f$ the estimate is within a few thousandths of 0.587 and $N_\text{eff}/M$ is large. At
        $\mu_g = 9$, $\sigma_g = 1$ almost no sample lands where $f$ has mass; the few that do carry all the weight,
        and $N_\text{eff}/M$ falls toward $1/M$. The estimate is then decided by one or two samples. Narrow $g$ around one
        mode of $f$ and the other mode is invisible: the estimate is wrong with a respectable $N_\text{eff}$, which is
        why $N_\text{eff}$ is a symptom, not a proof (support condition, p. 100; proposal, p. 102).
        """)})
    return


# ------------------------------------------------------------------ Fig 2.3d low-variance sampler


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.3d · Table 4.4: the low-variance sampler

        $M = 20$ particles with weights $w_i \propto \exp(-(i - 8)^2 / 2s^2)$. The comb has $M$ teeth $1/M$ apart; the
        only random number is the offset $r \in [0, 1/M)$, here a slider.

        **Predict first.** At $s = 3$, how many distinct particles survive? Independent draws (Table 4.3 lines 8–11)
        would keep how many on average? Then set $s = 20$ (almost equal weights): what does the comb return?
        """
    )
    return


@app.cell
def _(mo):
    d_s = mo.ui.slider(0.5, 20.0, value=3.0, step=0.5, label="weight spread s", show_value=True)
    d_r = mo.ui.slider(0.0, 0.99, value=0.5, step=0.01, label="offset r · M", show_value=True)
    mo.vstack([d_s, d_r])
    return d_r, d_s


@app.cell
def _(R, d_r, d_s, ex, go, mo, np, style):
    Md = 20
    wd = np.exp(-((np.arange(Md) - 8.0) ** 2) / (2 * d_s.value**2)); wd /= wd.sum()

    class _FixedR:
        """Stands in for the generator: Table 4.4 line 3 draws r once; the slider supplies it."""
        def __init__(self, r): self.r = r
        def uniform(self, lo, hi): return lo + self.r * (hi - lo)

    idx_d = ex.low_variance_resample(wd, _FixedR(d_r.value))
    cnt_d = np.bincount(idx_d, minlength=Md)
    neff_d = 1.0 / np.sum(wd**2)
    surv_multi = float(np.sum(1 - (1 - wd) ** Md))           # E[distinct] for M independent draws
    dev_d = float(np.max(np.abs(cnt_d - Md * wd)))

    figd = go.Figure()
    figd.add_trace(go.Bar(x=np.arange(1, Md + 1), y=Md * wd, marker_color=R["blue"], opacity=0.35, name="expected copies M·wᵢ"))
    figd.add_trace(go.Bar(x=np.arange(1, Md + 1), y=cnt_d, marker_color=R["teal"], opacity=0.85, name="copies from the comb"))
    figd.update_layout(barmode="overlay", xaxis_title="particle i", yaxis_title="copies", height=340, title="copies per particle")

    tiles_d = {
        "N_eff": f"{neff_d:.2f}",
        "distinct survivors, comb": f"{int(np.sum(cnt_d > 0))}",
        "E[distinct], independent draws": f"{surv_multi:.2f}",
        "max |copies − M·wᵢ| (must be < 1)": f"{dev_d:.2f}",
    }
    style.card(mo.ui.plotly(figd), fig="Fig 2.3d · Table 4.4, (4.37), Fig 4.7", title="One random number, M teeth",
               hint="Drag r and watch copies move by at most one; widen s until the comb returns every particle once",
               chip="copies within ⌊Mw⌋..⌈Mw⌉" if dev_d < 1 else "copy count off by ≥ 1 (bug)",
               chip_state="ok" if dev_d < 1 else "bad", tiles=tiles_d)
    return Md, cnt_d, dev_d, figd, idx_d, neff_d, surv_multi, tiles_d, wd


@app.cell
def _(mo):
    mo.accordion({"What you should have seen": mo.md(
        r"""
        Every particle gets $\lfloor M w_i\rfloor$ or $\lceil M w_i\rceil$ copies whatever $r$ is, so the max-deviation tile
        never reaches 1; $r$ only decides which particles get the extra copy. Independent draws keep fewer distinct
        particles on average and can give any particle anywhere from 0 to $M$ copies. With exactly equal weights the
        comb returns each particle exactly once (at $s = 20$ all 20 survive): the second advantage on p. 111, and why the stationary robot of
        lecture L9 keeps its diversity.
        """)})
    return


# ------------------------------------------------------------------ Fig 2.3e sampling bias


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig 2.3e · Sampling bias, (4.38)

        A binary state $\{a, b\}$, prior $P(a) = p$, likelihoods $L_a$, $L_b$; one update of Table 4.3 with no motion.
        The curve is the **exact** expected probability that a resampled particle is $a$, summed over every possible
        initial draw: $\sum_k \binom{M}{k} p^k (1-p)^{M-k}\, \frac{k L_a}{k L_a + (M-k) L_b}$.

        **Predict first.** With $p = 0.5$, $L_a = 0.9$, $L_b = 0.1$ the posterior is 0.9. What does the filter give at
        $M = 1$? At $M = 2$ (T2.4)? How large must $M$ be before the bias is below 0.01?
        """
    )
    return


@app.cell
def _(mo):
    e_M = mo.ui.slider(1, 50, value=2, step=1, label="particles M", show_value=True)
    e_p = mo.ui.slider(0.05, 0.95, value=0.5, step=0.05, label="prior P(a)", show_value=True)
    e_La = mo.ui.slider(0.05, 1.0, value=0.9, step=0.05, label="L_a = p(z | a)", show_value=True)
    e_Lb = mo.ui.slider(0.05, 1.0, value=0.1, step=0.05, label="L_b = p(z | b)", show_value=True)
    mo.vstack([e_M, e_p, e_La, e_Lb])
    return e_La, e_Lb, e_M, e_p


@app.cell
def _(R, binom, e_La, e_Lb, e_M, e_p, go, mo, np, style):
    def pf_prob_a(M, p, La, Lb):
        k = np.arange(M + 1)
        frac = np.where(k == 0, 0.0, k * La / np.maximum(k * La + (M - k) * Lb, 1e-300))
        return float(np.sum(binom.pmf(k, M, p) * frac))

    exact_e = e_p.value * e_La.value / (e_p.value * e_La.value + (1 - e_p.value) * e_Lb.value)
    Ms_e = np.arange(1, 51)
    curve_e = np.array([pf_prob_a(m, e_p.value, e_La.value, e_Lb.value) for m in Ms_e])
    pf_e = curve_e[e_M.value - 1]
    m_ok = next((int(m) for m, v in zip(Ms_e, curve_e) if abs(v - exact_e) < 0.01), None)

    fige = go.Figure()
    fige.add_trace(go.Scatter(x=Ms_e, y=curve_e, mode="lines+markers", line=dict(color=R["teal"], width=2), marker=dict(size=4), name="E[P(a)] after one PF update"))
    fige.add_hline(y=exact_e, line=dict(color=R["blue"], dash="dash"), annotation_text="exact posterior")
    fige.add_hline(y=e_p.value, line=dict(color=R["gray"], dash="dot"), annotation_text="prior (M = 1)")
    fige.add_trace(go.Scatter(x=[e_M.value], y=[pf_e], mode="markers", marker=dict(color=R["coral"], size=11), name="your M"))
    fige.update_xaxes(type="log")
    fige.update_layout(xaxis_title="M", yaxis_title="P(a)", height=360, title="the filter under-uses the measurement at small M")

    tiles_e = {
        "exact posterior P(a | z)": f"{exact_e:.3f}",
        "PF expectation at this M": f"{pf_e:.3f}",
        "bias": f"{pf_e - exact_e:+.3f}".replace("-", "−"),
        "smallest M with |bias| < 0.01": f"{m_ok}" if m_ok else "> 50",
    }
    style.card(mo.ui.plotly(fige), fig="Fig 2.3e · (4.38)", title="Normalization costs one degree of freedom",
               hint="Start at M = 1 (the prior, exactly) and slide up; change L_a / L_b and watch the needed M move",
               chip="bias below 0.01" if abs(pf_e - exact_e) < 0.01 else "biased toward the prior",
               chip_state="ok" if abs(pf_e - exact_e) < 0.01 else "warn", tiles=tiles_e)
    return Ms_e, curve_e, exact_e, fige, m_ok, pf_e, pf_prob_a, tiles_e


@app.cell
def _(mo):
    mo.accordion({"What you should have seen": mo.md(
        r"""
        $M = 1$ returns the prior exactly, whatever the likelihoods: (4.38). $M = 2$ gives 0.700 at the defaults, the
        T2.4 answer. The bias always points toward the prior and shrinks with $M$; p. 112 says only that it becomes "less and less pronounced", gives no rate. The stronger the
        measurement (larger $L_a/L_b$), the more particles the filter needs before it believes it, which is the
        discrete face of the proposal problem in Fig 2.3c.
        """)})
    return


if __name__ == "__main__":
    app.run()
