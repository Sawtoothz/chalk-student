# Chalk: student edition

Chalk turns robotics textbook chapters and research papers into **teaching packages**: a chapter map, a lecture with
figures, equation-to-code cards, an interactive session, slide decks, and five tiers of exercises with clues and
oracle tests. An AI agent builds each package and a second pass reviews it against the book. You learn from them.

![The Chalk library](https://raw.githubusercontent.com/wiki/Sawtoothz/chalk-student/images/library.png)

**📘 Tutorial: [the wiki](https://github.com/Sawtoothz/chalk-student/wiki)**, with screenshots, step by step.

## Quick start

**Windows** (or any OS with [Docker Desktop](https://www.docker.com/products/docker-desktop/)):

```powershell
git clone https://github.com/Sawtoothz/chalk-student.git
cd chalk-student
chalk                         # macOS / Linux: ./chalk     first run builds the container, a few minutes
```

**Linux / macOS** without Docker (needs [`uv`](https://docs.astral.sh/uv/) and [`just`](https://just.systems/)):

```bash
git clone https://github.com/Sawtoothz/chalk-student.git
cd chalk-student
uv sync
just serve
```

Then open **http://localhost:8765**. Details: [Install](https://github.com/Sawtoothz/chalk-student/wiki/Install) ·
[Windows with Docker](https://github.com/Sawtoothz/chalk-student/wiki/Windows-and-Docker).

## Included packages

| Package | Source | Open with |
| --- | --- | --- |
| One-dimensional Kalman filters (**open example**, book included) | Labbe, *Kalman and Bayesian Filters in Python*, ch. 4 (CC BY 4.0) | `just view labbe-kbf 4` |
| A micro Lie theory (**open example**, paper included, easy read) | Solà, Deray, Atchuthan, 2018 (CC BY-NC-SA 4.0) | `just view sola-microlie 1` |
| Nonparametric filters | Thrun, Burgard, Fox, *Probabilistic Robotics*, ch. 4 | `just view thrun-pr 4` |
| Robot motion | *Probabilistic Robotics*, ch. 5 | `just view thrun-pr 5` |
| A tour of multiple view geometry | Hartley, Zisserman, *Multiple View Geometry*, ch. 1 | `just view hz-mvg2 1` |
| Gaussian filters (worked example) | *Probabilistic Robotics*, ch. 3 | `examples/thrun-pr/ch03-gaussian-filters/` |

The two **open examples** ship with their source PDFs (`library/open/`), so the Reader's annotated-page tab works
out of the box; start with them. For the others, the book is not included: the lecture, cards and exercises work
without it; with your own copy of the PDF at the path in `books.yaml`, `just teach <book> <chapter>` adds the annotated pages.

Studying these needs **no AI account**. To build packages for your own chapters, set up an AI agent (Claude Code,
Codex, Gemini CLI or another): see [Choose an AI engine](https://github.com/Sawtoothz/chalk-student/wiki/Choose-an-AI-Engine).

## Daily commands

| Command | What it does |
| --- | --- |
| `just test thrun-pr 4` | Run the oracle tests against your `exercises/exercise.py` |
| `just clue thrun-pr 4 T3.2 1` | Show the first clue of exercise T3.2 |
| `just session thrun-pr 4` | Open the interactive notebook |
| `just` | List every command |

With Docker, type `chalk` (Windows) or `./chalk` instead of `just`.

## Two rules

- **Chalk never writes your solutions.** This edition ships without reference solutions: the stubs, tests and clues
  are there so that you write the code.
- **The slides are study copies.** The PDFs are watermarked "Created by Chalk", and there is no PowerPoint version.
  Build your own slides when you present. See
  [Slides and academic honesty](https://github.com/Sawtoothz/chalk-student/wiki/Slides-and-Academic-Honesty).

## What's in the repository

| Path | What |
| --- | --- |
| `packages/` | The teaching packages (one folder per chapter or paper) |
| `examples/` | Worked example packages that new packages are measured against |
| `app/` | The Library app (`just serve`) |
| `scripts/` | The tools behind the commands: tests, clues, Reader, slides, checks |
| `.claude/skills/teach/` | The `/teach` pipeline an AI agent follows to build a package |
| `AGENTS.md` | The rules every AI agent works under in this project |
| `books.yaml` | The books and papers the Library knows, with chapter page ranges (PDFs not included) |

## License

[MIT](LICENSE). The license covers Chalk's code and the teaching material written for it. Short passages quoted
from the books and papers (highlight anchors, equations, page citations) remain the property of their authors and
publishers and are included for teaching; those books themselves are not in this repository.

Exceptions: the openly licensed sources in `library/open/` and the packages built from them keep their own terms,
stated in `library/open/README.md` and each package's `LICENSE.md`: Labbe's book and `packages/labbe-kbf/` are
CC BY 4.0; Solà et al.'s paper and `packages/sola-microlie/` are CC BY-NC-SA 4.0 (non-commercial, share-alike).
