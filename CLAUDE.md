@AGENTS.md

# Claude Code notes

The project's rules are in `AGENTS.md` (imported above); this file adds what is specific to Claude Code.

- `/teach <source> <unit> --stage <name>` is the skill in `.claude/skills/teach/`; the reviewer is the
  `teach-reviewer` subagent in `.claude/agents/`.
- Models: run the book-reading stages on Opus 5.5 (the strong tier); `session`, `build`, `slides` and fix loops on
  Sonnet 5.5 (the fast tier). `teach-reviewer` is pinned to Fable 5.1 when the plan has it, else Opus 5.5, in its front
  matter. Haiku 5.5 is for plumbing only, never for anything that touches the book. `/tutor` (later) on Sonnet.
- Switch to Sonnet only after `just check` says ship and the remaining work is wording or figures.
- `/clear` between stages.
- Use the superpowers workflow: brainstorm, plan, implement. One plan per chapter package.
- The caveman plugin is on for chat replies. It never changes what is written into a package.
