@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fig <lesson><letter> · <book table / eq.>

        <One sentence on the setup.>

        **Predict first.** <A question with a definite answer that the figure then shows.>
        """
    )
    return


@app.cell
def _(mo):
    s1 = mo.ui.slider(<min>, <max>, value=<v>, step=<s>, label="<what> [<unit>]", show_value=True)
    mo.vstack([s1])
    return (s1,)


@app.cell
def _(P, R, ex, go, mo, np, s1, style):
    # model -> figure -> tiles, all from the same numbers
    ...
    tiles = {"<readout>": f"{value:.2f} <unit>", "<invariant> (should be 0)": f"{resid:.3f}"}
    style.card(mo.ui.plotly(fig), fig="Fig <lesson><letter> · <ref>", title="<finding as a sentence>",
               hint="<what to drag and what to watch>", chip="<state>", chip_state="ok", tiles=tiles)
    return ...


@app.cell
def _(mo):
    mo.md(r"""**What you should have seen.** <Two to four sentences, with the book page.>""")
    return
