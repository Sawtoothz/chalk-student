# Start prompts — building Chalk with Claude Code, superpowers, caveman and short sessions

Two prompts. The first opens the project; the second opens every session after it. Build state lives in
`BUILD-HANDOFF.md` at the repo root (teaching packages keep their own `HANDOFF.md` inside `packages/…`).

Before the first prompt, on the VM: `git init && git add -A && git commit -m "chalk starter pack"`, install the
plugins in Claude Code (`/plugin install superpowers`, `/plugin install caveman`), put `thrun-pr.pdf` in `library/`.

---

## Prompt 1 — Session 0 (paste as the first message, model: Sonnet 5.5)

```
/caveman

You are building Chalk, my Claude-as-professor self-study system. Read CLAUDE.md, README.md, SETUP.md and
FIRST-PROMPT.md first; they are the contract. Then use the superpowers workflow in this order:
brainstorming (short — the design is done, only confirm you understand it), writing-plans, executing-plans.

Session rules, for this and every later session:
- Caveman style in chat replies only. Everything written to a file — code, markdown, HANDOFF, commit messages —
  is normal full prose. This is hard rule 6 of the /teach skill and applies to build sessions too.
- One phase per session. When the phase is done, or at ~60% of context, write BUILD-HANDOFF.md
  (template at the end of this message), commit, and stop. Do not start the next phase.
- Never read the gold example packages in full; read the one file you need.
- Tests before claims: a phase is done when its check command passes, not when the code is written.

Phase list (write it to BUILD-PLAN.md with the check for each, then do phase 0 only):
0. Environment: uv sync; just --list works; python3 scripts/pages.py --list; just probe thrun-pr confirms offset 21;
   just check thrun-pr 3 against examples/thrun-pr/ch03-gaussian-filters prints VERDICT: ship;
   just serve starts and / returns 200. Fix whatever breaks on this machine. Check: all six commands pass.
1. First chapter, stage map: just stage thrun-pr 4 map (or /teach thrun-pr 4 --stage map in a fresh session on
   Opus). Check: packages/thrun-pr/ch04-*/map.md and HANDOFF.md exist and map.md has the inventory table.
2. Stages highlight → cards, one per session, --stage next. Check per stage: the file the stage writes exists and
   scripts/check_package.py does not report it missing.
3. Stages exercises → session → build. Check: just test thrun-pr 4 runs; stubs fail, STUDY_IMPL=solution passes;
   reader.html opens.
4. Stage review on Opus; fix everything the reviewer confirms. Check: just check thrun-pr 4 prints VERDICT: ship.
5. GUI on a real run: just serve, Teach on chapter 5 from the browser, watch the log, Continue once. Check: the
   Run page streams and the Library row advances.
6. First paper: library/xu-fastlio2.pdf, /teach xu-fastlio2 1 --stage map … cards with scripts/code_refs.py.
   Check: just check xu-fastlio2 1 prints VERDICT: ship.
7. Second book through ingest (barfoot-se2), one chapter to map. Check: ingest wrote chapters and the offset is right.

Skill fixes: when a stage misbehaves, fix the skill or its references (.claude/skills/teach/), not the package,
and record the change in BUILD-HANDOFF.md under "skill changes" so later sessions know why.

BUILD-HANDOFF.md template:
---
phase_done: <n>
next_phase: <n+1>
model_next: <opus|sonnet>
---
## Done
<what passed, with the command and its last line>
## Skill changes
<file: what and why>
## Open
<anything that failed or was deferred, one line each>
## Next session, first command
<the exact command>
```

---

## Prompt 2 — every later session (paste as the first message; pick the model BUILD-HANDOFF.md names)

```
/caveman

Continue building Chalk. Read BUILD-HANDOFF.md, then BUILD-PLAN.md, then only the files the next phase needs.
Same rules: caveman in chat only; one phase; stop at the phase's check or ~60% context; rewrite BUILD-HANDOFF.md
and commit before stopping. If the phase is a /teach stage, run it exactly as FIRST-PROMPT.md says and do not
touch the package's own HANDOFF.md by hand. Start with the command BUILD-HANDOFF.md names.
```

---

## Model per session

| phase | model |
| --- | --- |
| 0, 5, 7, any fix loop | Sonnet 5.5 |
| 1–4, 6 (stages that read the book or paper), review | Opus 5.5 |

Expect 10–14 sessions of 20–60 minutes. If a session ends without a HANDOFF (crash, context), start the next one
with: "Read git log -3 and git status, infer the phase, write BUILD-HANDOFF.md first, then continue."
