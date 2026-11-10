# FAST-LIO2 — teaching package (mock of the paper workflow)

Source: W. Xu, Y. Cai, D. He, J. Lin, F. Zhang, *FAST-LIO2: Fast Direct LiDAR-Inertial Odometry*, IEEE T-RO 38(4), 2022.
Unit: whole paper (13 pages). Lesson: t2.8 (LiDAR-inertial odometry).

This package is a **mock** of what `/teach xu-fastlio2 1` produces for a paper. The paper PDF is not in the repo, so
the stages that read it (map, highlight, lecture) are represented only by `map.md`; the cards and session stages are complete:

| file | stage | what it shows |
| --- | --- | --- |
| `map.md` | map | the paper's sections mapped to the five things a reader must leave with |
| `translate.md` | cards | equation → code cards, each ending in **In the original code**: file, line, permalink at a fixed commit |
| `implementation.md` | cards | the practical implementation proposal: what to build, in what order, against what data, with what checks |
| `code_refs.json` | cards | every file:line above, produced by `scripts/code_refs.py` — the cards cite only from this file |
| `reader.html` | build | `just view xu-fastlio2 1` — the Reader for this package (About, Map, Equation → code, Interactive session, Implementation, Code anchors) |
| `interactive.html` | session | two browser figures: S1 backward propagation (C3), S2 the iterated update with the information-form gain (C4–C5), with Predict-first prompts and live readouts |

The rule the mock demonstrates (see `.claude/skills/teach/references/paper-code.md`): for a paper, the cards stage
never writes a code reference from memory. It clones the authors' repository at a commit, greps the symbols, and cites
`path:line` with a permalink. If the authors published no code, the card says so and points at the closest
independent implementation it can anchor the same way.

Repositories anchored here (all GPL-2.0; our reimplementation is clean-room from the equations, the links are for reading):

- https://github.com/hku-mars/FAST_LIO @ `7cc4175d` — the system
- https://github.com/hku-mars/ikd-Tree @ `c0e36a16` — the incremental k-d tree
- https://github.com/hku-mars/IKFoM @ `59cfc095` — the iterated Kalman filter on manifolds toolkit the system is built on
