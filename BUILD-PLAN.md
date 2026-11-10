# Chalk build plan

One phase per session. A phase is done when its check passes, not when its code is written.
State between sessions lives in `BUILD-HANDOFF.md`; teaching packages keep their own `HANDOFF.md`.

| Phase | Work | Check | Model |
| --- | --- | --- | --- |
| 0 | Environment: `uv sync`; `just --list`; `python3 scripts/pages.py --list`; `just probe thrun-pr`; `just check thrun-pr 3 examples/thrun-pr/ch03-gaussian-filters`; `just serve`. Fix whatever breaks on this machine. | All six pass: recipes listed, list prints JSON, probe prints `books.yaml offset 21: confirmed`, check prints `VERDICT: ship`, `GET /` returns 200. | Sonnet |
| 1 | First chapter, stage map: `just stage thrun-pr 4 map` (or `/teach thrun-pr 4 --stage map` in a fresh Opus session). | `packages/thrun-pr/ch04-*/map.md` and `HANDOFF.md` exist and `map.md` has the inventory table. | Opus |
| 2 | Stages highlight, lecture, cards: one per session with `--stage next`. | Per stage: the file the stage writes exists and `scripts/check_package.py` does not report it missing. | Opus |
| 3 | Stages exercises, session, build. | `just test thrun-pr 4` runs; the stubs fail and `STUDY_IMPL=solution` passes; `reader.html` opens. | Opus (exercises), Sonnet (session, build) |
| 4 | Stage review on Opus; fix everything the reviewer confirms. | `just check thrun-pr 4` prints `VERDICT: ship`. | Opus |
| 5 | GUI on a real run: `just serve`, Teach on chapter 5 from the browser, watch the log, Continue once. | The Run page streams the log and the Library row advances. | Opus |
| 6 | First paper: `library/xu-fastlio2.pdf`, `/teach xu-fastlio2 1 --stage map` through cards, with `scripts/code_refs.py`. | `just check xu-fastlio2 1` prints `VERDICT: ship`. | Opus |
| 7 | Second book through ingest (`barfoot-se2`), one chapter to map. | Ingest wrote the chapters and the offset is right (probe prints `confirmed`). | Opus |

## Rules that hold in every phase

- Never write Aun's solutions; stubs, oracles and gated `solutions/` only (see `CLAUDE.md`).
- When a stage misbehaves, fix the skill or its references under `.claude/skills/teach/`, not the package,
  and record the change in `BUILD-HANDOFF.md` under "Skill changes".
- Read one file of a gold example at a time, never the whole package.
- At the end of a phase, or at about 60% of context, write `BUILD-HANDOFF.md`, commit, and stop.
