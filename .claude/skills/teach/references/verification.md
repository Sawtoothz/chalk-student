# Verification

Nothing reaches Aun unchecked. Two layers: deterministic scripts, then a reviewer that did not write
the package.

## Scripts (run by `just check`)

`scripts/check_package.py <pkg>`:
- required files present; lecture figures exist; highlights.json well-formed and in range;
- `STUDY_IMPL=solution pytest exercises/tests/test_T3.py` passes;
- `pytest exercises/tests/test_T3.py` on the stubs fails;
- `pytest exercises/tests/test_T4.py` on the broken file fails;
- `session.py` executes headlessly.

`scripts/highlight_pdf.py` must report no UNMATCHED items.
`scripts/fd_check.py` on every Jacobian in the reference solution.

## Reviewer (`.claude/agents/teach-reviewer.md`)

Spawned with the package path and the chapter's PDF page range. It reads the chapter itself and
checks, in this order:
1. every equation in `lecture.md` and `translate.md` against the book, symbol by symbol;
2. every page citation;
3. every claim attributed to the book;
4. T2 solutions re-derived by hand;
5. Jacobians re-differentiated by hand and checked numerically;
6. a sample of ten highlight anchors against their notes;
7. invented numbers, misleading statements, anything a graduate robotics engineer would object to.

It returns CONFIRMED errors, DOUBTFUL items, and a verdict. All CONFIRMED items are fixed; all
DOUBTFUL items are addressed (fixed, or the text made explicit about what is and is not from the
book). The report and the fixes go into `REVIEW.md`.

## Things the ch. 3 review caught, to pre-empt

- A referenced script that did not exist.
- A geometric claim that was false (Cholesky columns as principal axes).
- A numerical claim with the wrong sign (UKF centre weights for small α).
- A note that was true but not about its anchored sentence.
- Two invented numbers (a matrix size, "one standard deviation").
- Attribution drift: a convention from the UKF literature presented as the book's; an innovation
  gate presented as the book's Mahalanobis definition.

## Numbers

Every number in prose traces to one of: the book page (cite it), a test (name it), or a run whose
command is in the package (`T5_sim.py` + the solution). Session readouts are compared between the
Python and JS versions and the comparison is recorded in `REVIEW.md`.
