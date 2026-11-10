# Chalk — first sessions, one stage each, `/clear` between

Model: Opus 5.5 unless the line says Sonnet. Caveman on. Each session ends with a three-line report and
`HANDOFF.md` in the package; read the report, then `/clear` and paste the next prompt.

## Session 0 — environment (Sonnet)

```
Read CLAUDE.md (this is Chalk). Make the repo run: `uv sync`; `just --list`; `python3 -c "import pymupdf, marimo, plotly, cvxpy"`.
Then in examples/thrun-pr/ch03-gaussian-filters run `python3 -m exercises.T5_sim` and from the root
`python3 scripts/check_package.py examples/thrun-pr/ch03-gaussian-filters` (must print VERDICT: ship).
Hook `just test` into scripts/learner.py record-test (a few lines in the justfile). Report in three lines.
```

## Session 1 — map

```
/teach thrun-pr 4 --stage map
```

## Session 2 — highlight

```
/teach thrun-pr 4 --stage next
```

## Session 3 — lecture

```
/teach thrun-pr 4 --stage next
```

## Session 4 — cards

```
/teach thrun-pr 4 --stage next
```

## Session 5 — exercises

```
/teach thrun-pr 4 --stage next
```

## Session 6 — session + build (Sonnet is fine)

```
/teach thrun-pr 4 --stage next
```
then, same session if context allows, `/teach thrun-pr 4 --stage build`.

## Session 7 — review

```
/teach thrun-pr 4 --stage review
```

Then read `REVIEW.md`, `map.md`, open the Reader, and write your critique into `learner.yaml` under
`feedback:` (or tell the next session). The second chapter should show the difference.

## Constraints that apply to every session

Never write my solutions outside solutions/. Every number in prose comes from a run. Figures follow
viz/README.md. Read only what the stage table in SKILL.md allows. Ask me only if books.yaml or the
PDF is missing.


## GUI instead of the terminal (optional, after Session 0)

`just serve`, open http://localhost:8765, and press **Teach** on Thrun ch. 4. Each press runs one stage through the same
`/teach` skill (`scripts/run_stage.py`); the Run page shows the log and the handoff, and **Continue to <stage>** advances.
Everything below still applies when you prefer the terminal.
