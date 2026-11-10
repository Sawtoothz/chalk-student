@AGENTS.md

# Gemini CLI notes

The project's rules are in `AGENTS.md` (imported above). Gemini CLI has no `/teach` command and no subagents: run a
stage by asking "Read .claude/skills/teach/SKILL.md and run `/teach <source> <unit> --stage <name>`", one stage per
session (`/clear` or a new session between stages). For the `review` stage, use `.claude/agents/teach-reviewer.md`
as your brief, as `AGENTS.md` describes. Use your strongest model (a Pro model) for the stages that read the book.
