# Teaching style

Aun is a senior engineer-educator. He wants low-level detail, pictures, and the path from an
abstract equation to code that runs on a robot. Tone: a colleague explaining at a whiteboard. No
preamble, no "in this section we will", no cheerleading.

## Lecture (`lecture.md`)

Front matter: `lesson`, `title`, `source` (book, chapter, pages), `figures`, `status: draft`.

One section per must-read chapter section, numbered `L1`, `L2`, … Each section has exactly four
layers, in this order and with these bold labels:

1. **Picture.** One sentence pointing at a generated figure, then the figure
   (`![](figures/L2-predict-update.svg)`). The figure shows the idea, not the chapter's plot.
2. **Intuition.** Two to five sentences in plain words. What the method does, why it works, what
   it is afraid of.
3. **Formal.** The book's equations with the book's numbers, in `latex` fenced blocks for display
   math. Shapes of every symbol the first time it appears. Algorithm tables as markdown tables with
   the book's line numbers. One paragraph on the derivation's one idea when there is one.
4. **Your robots.** Where this runs on the tracked robot, quadruped, drone, FORGE, PRISM, or the
   RoboCup map. Concrete: which matrix, which sensor, which failure Aun has seen.

Skim sections get one paragraph under a heading, no layers. Skip sections get one line.

End with `L<n>. How to tell which method you need`: a symptom → likely cause → try table.

Add a **Notation warning** paragraph wherever the book's symbols conflict with the rest of the
repo or with Barfoot (R/Q swap, row vs column convention, angle conventions).

Length: about 50 words of lecture per must-read page. Thrun ch. 3 (46 pages) came to 2,400 words.

## Figures (`figures/make_figures.py`)

- Generated, never hand-drawn, with `viz.py.style` (`style.use()`, `cov_ellipse`, `draw_frame`,
  `fig_label`). Save SVG and PNG.
- Each figure answers one question and its title states the answer
  ("Sigma points see the curvature; the tangent does not").
- Colours by role (viz/README.md). Truth in the ink colour or gray, estimate blue, measurement
  coral, the taught quantity teal.
- Monte Carlo truth where the point is approximation error: draw the samples faintly behind the
  fitted ellipses.
- Look at every PNG before moving on. Fix clipped labels, missing glyphs, squeezed panels.

## Cards (`translate.md`)

One card per algorithm or equation family, `C1`…, in the order a student implements them. Each card:

- **Shapes.** Every symbol with its dimensions.
- **Naive.** Python that reads line for line like the book, with the book's line numbers as comments.
- **Robust.** The version to actually use. Each trick is a numbered item with a name in bold and one
  sentence on why: `cho_solve` instead of `inv`, Joseph form, symmetrize, sequential updates,
  wrap angles before the gain, finite-difference check, Mahalanobis gate, redraw sigma points,
  Cholesky as square root, never form Ω⁻¹.
- **Eigen.** C++ with fixed sizes where known, `LDLT`/`LLT`, `.noalias()`, `.eval()` where aliasing
  bites.
- **Cost.** Big-O with which product dominates in practice.
- **What breaks first.** Ordered list of the failure modes in the order they appear in practice.

Cards are checked by the reviewer against the book page and by the oracle tests against the
reference solution. A trick that is folklore rather than fact gets a one-line justification or a
citation (Bar-Shalom, Maybeck, Simon).

## Session (`session.py` and `interactive.html`)

Three to five figure cards, each following `viz/README.md`:

- Figure number `Fig <lesson><letter>` tied to the book table or equation it shows.
- A **Predict first** prompt above the controls: a question with a definite answer that the figure
  then shows. Aun writes his guess down before touching the slider.
- Controls that change the thing being taught (noise, spread, linearization point), not cosmetics.
- Readout tiles driven by the same model as the plot. One tile is an invariant or residual that
  proves the concept (x₂ᵀFx₁, NEES fraction above bound, KKT residual).
- A status chip that changes at the special case.
- A collapsed **What you should have seen** after the figure, two to four sentences, with the book
  page that says it.

`session.py` is a marimo notebook (unique names across cells; `mo.ui.slider`; `style.card`). It uses
the reference solution so it runs before Aun has done T3; `USE_MY_CODE = True` switches to his
`exercise.py`. `interactive.html` is the same figures in plain JS with Plotly (`templates/interactive.html`),
so the Reader page needs no Python. Readouts in both must agree to two decimals on the default settings;
write that comparison down in `REVIEW.md`.

## Language

- British or American spelling, consistently within a package (the gold example is American).
- Equation references are the book's: `eq. 3.45`, `Table 3.1 line 4`, `p. 53`.
- Units on every number. True minus signs in readouts.
- No sentences that start with "Note that" or "It is important to".
