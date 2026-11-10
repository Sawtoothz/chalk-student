# Exercise spec

Five tiers per chapter. Each exercise has a three-step clue ladder and a solution. Solutions for T3
are revealed by `just reveal` only after a test run or all three clues; the rest are markdown that
Aun opens after attempting.

| Tier | What | Count | Graded by |
| --- | --- | --- | --- |
| T1 concept | short questions with definite answers | 6–10 | `solutions/T1.md` |
| T2 derivation | derive by hand; recompute a book example | 2–4 | `solutions/T2.md` |
| T3 implementation | fill stubs in `exercise.py` | 6–12 functions | `tests/test_T3.py` with oracles |
| T4 debug | find 3–5 planted bugs in a working implementation | 1 file | `tests/test_T4.py` |
| T5 robot | apply and tune on a system like Aun's robots; write a half-page report | 1 | `solutions/T5.md` numbers |

Fold the book's own exercises into these tiers where they fit and say so in `exercises/README.md`.

## T1

Questions whose answer is in the chapter and can be checked in two sentences. Mix: assumptions,
where a symbol appears, cost, why a step is done at this point and not another, one "when would you
use X instead of Y". Answers cite the page.

## T2

Derivations the chapter does but a student should redo (inversion lemma to the gain), proofs the
chapter skips but code relies on (Joseph form), and the book's worked exercise redone with numbers.
Solutions show every step and the final numbers.

## T3

`models.py` holds the systems (the book's toy and one that resembles Aun's robots) and is never
edited by Aun. `exercise.py` holds stubs with docstrings that name the book line or equation and the
return contract. Order the stubs as the cards order them.

Oracle tests, one or more per stub, each with an oracle that is independent of the student's code:

- dense reference formula (`np.linalg.inv` is fine in a test);
- finite differences for every Jacobian at ten random states, with angle rows wrapped;
- Monte Carlo propagation (10⁵–10⁶ samples) for anything that approximates a distribution;
- algebraic identities (information form equals covariance form; UT exact for linear maps; KF
  equals UKF on a linear system);
- a stress test (thousands of steps with a tiny noise) for numerical hygiene;
- a consistency test over M independent runs with bands wide enough for a correct implementation
  and tight enough to catch an overconfident one. One run is not a consistency test.

`STUDY_IMPL=solution` grades the reference solution; the shipped stubs must fail every test; the
reference must pass every test. Both are checked by `check_package.py`.

## T4

Take the reference implementation, plant 3–5 bugs that each come from the field (sign in a
Jacobian, stale linearization, missing angle wrap, lost symmetry, wrong linearization point, wrong
noise added at the wrong step), with a header listing the symptoms Aun may see. One grader test per
bug, written so that only that bug fails it. Prove it: all tests fail as shipped, all pass with the
bugs fixed in a temp copy. `solutions/T4.md` is a table: where, bug, symptom, fix. If a planted
"bug" is the book's own form (ch. 3's `(I − KC)Σ̄`), say so honestly and call it hygiene.

## T5

The transfer exercise. A hidden-noise simulation (`T5_sim.py`) of a system like Aun's robots; tasks
that go from an initial guess through tuning with the statistics he can measure on the robot (NIS)
to the ones that need ground truth (NEES); a stress case where the method's assumption breaks; a
robustness case (outliers, gating); and a half-page report. `solutions/T5.md` gives the hidden
parameters and the reference numbers from an actual run of the reference solution on the shipped
data, in a table, with the one or two observations that matter.

## Clues (`clues.md`)

One `## <exercise>` section per exercise, three numbered clues:
1. direction (where to look, what shape the answer has);
2. the key idea or formula;
3. near-solution (the line of code or the substitution, short of the whole answer).

`just clue` records each one opened in `learner.yaml`.

## By chapter type

- Algorithm chapters (filters, solvers, SLAM): the mix above.
- Model chapters (motion and sensor models, camera models): T3 implements the models and their
  Jacobians; T4 plants bugs in a sampler or likelihood; T5 fits the model to logged data.
- Theory chapters (convexity, duality, projective geometry): T2 grows to 4–6 derivations; T3
  implements checkers (is this set convex, is this point on this conic, KKT residual); T5 is a
  modelling exercise with CVXPY or OpenCV as oracle.
- Geometry chapters: T3 implements the estimators with OpenCV as oracle; T4 plants normalisation
  and sign bugs; T5 runs on Aun's own images.
