# Chalk

Chalk is a teaching agent for robotics self-study: Claude at the whiteboard. Each textbook chapter, or paper, becomes a teaching package:
annotated PDF with margin notes, chapter map, four-layer lecture with figures, equation-to-code
cards, interactive session, five-tier exercises with clues and gated solutions, reviewed by a
separate agent before it reaches you.

- `SETUP.md` — machine, repo, first run.
- `START-PROMPT.md` — paste-ready prompts to build the project in short sessions (superpowers + caveman + BUILD-HANDOFF.md).
- `FIRST-PROMPT.md` — the first `/teach` session, paste-ready.
- `CLAUDE.md` — the rules Claude Code works under here.
- `.claude/skills/teach/` — the `/teach` skill and its specs.
- `examples/thrun-pr/ch03-gaussian-filters/` — the gold example (Thrun ch. 3).
- `examples/xu-fastlio2/paper/` — the paper example (FAST-LIO2): equation cards that end in the authors' code at a pinned commit, plus a practical implementation plan.
- `viz/` — the figure style shared by every package.
- `scripts/` — deterministic tools: highlights, Jacobian checks, package check, Reader page, learner state, `ingest.py` (PDF → `books.yaml`), `run_stage.py` (headless stage runner).
- `app/` — the GUI (`just serve`): Library with PDF upload, Run page that tails a stage, Reader.
- `docs/` — GUI design notes and the static mockup.

Two ways to use it: **CLI** (Claude Code in this repo, `/teach <source> <unit> --stage …`) or **GUI** (`just serve`, upload a PDF, press Teach). Same stages, same files.
