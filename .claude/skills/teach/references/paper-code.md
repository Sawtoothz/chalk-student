# Papers: the cards stage proposes an implementation and anchors the reference code

For a source with `kind: paper`, the cards stage writes two files instead of one, and every code reference in
them is verified, never recalled.

## translate.md — cards, plus "In the original code"

Same card format as for a book (`templates/card.md`), one card per equation family the paper's method needs, in
the order a reader would implement them. Each card ends with an **In the original code** block:

- `path:line` of the function that implements the equation, taken from `code_refs.json`, nothing else. Line
  numbers are for the pinned commit; say so once at the top of the file.
- What to look at there: the variable names that map to the paper's symbols, the authors' own comments (these are
  often the most honest statement of what is approximated — quote them), tricks present in the code but absent
  from the paper (weights, thresholds, iteration limits). Each such trick goes into the card's **Trick** line and
  into `implementation.md` under *what to copy*.
- One permalink (`…/blob/<sha>/<path>#L<lo>-L<hi>`).
- The licence of the repository, once, in the file header, and what it implies for copying vs. rewriting.

Our snippets are written from the equations (clean-room). They may use the same variable names as the paper, not
the repository's.

## implementation.md — the practical proposal

A short plan a senior engineer could follow without the paper open:

1. **Deliverables**, in order: a prototype in Python for correctness, then (when the method is meant to run on a
   robot) a C++ port for speed. State the target size and rate of each.
2. **Step order** as a table: build → check (the oracle that must pass) → card. Checks are finite differences,
   identities (e.g. the gain identity), synthetic cases with known truth, and one real sequence with ground
   truth. Targets in this table are *to be measured*; the package records a number only after a run.
3. **Data**: the authors' own recordings first (they match the shipped config, so divergence there is a bug),
   then one sequence from Aun's robot. Where the configuration file for that data lives in the repo.
4. **What to copy from the paper / borrow from the code / leave out of the prototype**, three lists with reasons.
5. **Pitfalls the code warns about and the paper does not**: units in fields, initialisation guards, scalar
   covariances, iteration limits — each with the file:line it was found at.
6. **Licence note**: the repository's licence and the clean-room rule.

## code_refs.json — the only source of file:line

Produced by `scripts/code_refs.py <repo url> --grep <symbols…> --json <package>/code_refs.json` before any card is
written. It records repo, commit, licence and, per symbol, the matching `path:line:text` with permalinks. Use
`--show path:lo-hi` to read a region before describing it. Symbols to grep are the function and variable names
the paper's equations become — guess them from the paper, grep, read, refine. Anchor the authors' repository
first; anchor the libraries it builds on (an estimator toolkit, a tree, a solver) when a card's equation lives
there rather than in the system repository. Never cite a line that is not in `code_refs.json`; if a needed symbol
is not found, say so in the card rather than inventing a location.

## The check

`scripts/check_paper.py <package>` (what `just check` runs for a paper) fails on: a missing `map.md`, `translate.md`,
`implementation.md` or `code_refs.json`; any `` `path:line` `` in the cards or the plan with no hit within 40 lines in
`code_refs.json` (cite the exact lines you read with `--show`, and grep enough symbols that every region you
describe has a hit); any permalink whose repo@commit is not recorded. Run it before writing `HANDOFF.md`.

## Exercises for a paper

T2 derives an identity the implementation depends on (for FAST-LIO2: the information-form gain equals the
textbook gain). T3 implements the core update on a synthetic case whose truth is known. T5 is the step-6 run of
`implementation.md` on a real sequence, with the ATE and timing table as the deliverable. No T4 unless the
authors' repository has a documented bug worth reproducing.

Gold example: `examples/xu-fastlio2/paper/` (FAST-LIO2; map, cards, implementation and code_refs only — the
paper PDF is not in the repo).
