# Setup

The step-by-step guide with screenshots is the wiki:
[Install](https://github.com/Sawtoothz/chalk-student/wiki/Install) (Linux, macOS, WSL) and
[Windows with Docker](https://github.com/Sawtoothz/chalk-student/wiki/Windows-and-Docker). This page is the short version.

## Without Docker (Linux, macOS, WSL)

```bash
# Ubuntu / WSL: sudo apt install -y git python3 python3-venv libreoffice-impress && sudo snap install just --classic
# macOS:        brew install git uv just && brew install --cask libreoffice
curl -LsSf https://astral.sh/uv/install.sh | sh     # if uv is not installed yet
git clone https://github.com/Sawtoothz/chalk-student.git && cd chalk-student
uv sync                                               # Python 3.11+ and every library, into .venv
just                                                  # lists the commands
just serve                                            # the app at http://localhost:8765
```

LibreOffice is only needed to rebuild slide PDFs. Every `just` command runs inside `.venv`; no activation needed.

## Docker (Windows, macOS, Linux)

The same app in a container, for machines without the Linux toolchain, e.g. Windows with Docker Desktop.

```bash
docker compose up            # first run builds the image (about 2 GB, a few minutes); then http://localhost:8765
./chalk test thrun-pr 4      # any just recipe, run inside the container (Windows: chalk test thrun-pr 4)
./chalk                      # same as docker compose up
```

- The project folder is mounted at `/app`: packages, `exercise.py` and `learner.yaml` stay on your disk and can be
  edited with any editor. Python lives in `/opt/venv` inside the image.
- Ports are published on `127.0.0.1` only (8765 GUI, 2718 marimo for `just session`).
- AI agents are opt-in: copy `.env.example` to `.env`, set `CHALK_AI=@anthropic-ai/claude-code` (and/or
  `@openai/codex`, `@google/gemini-cli`), then `docker compose build`. Log in once with
  `docker compose run --rm chalk claude` (or `codex login`, `gemini`), or put an API key in `.env`; logins are
  kept in the `chalk-home` volume.
- On Windows, clone with Git for Windows or inside WSL; `.gitattributes` keeps LF line endings so the scripts run
  in the container. A clone inside WSL (`\\wsl$\...`) is much faster than one under `C:\`.

## The annotated chapter

Book pages are copyrighted and not in this repository. With your own copy of the book, put it at the path
`books.yaml` names (e.g. `library/thrun-pr.pdf`) and run `just teach thrun-pr 4`: Chalk adds the package's
highlights and margin notes to your PDF, on your machine, without AI. `just probe <id>` checks the page offset.

## Building your own packages

Install and log in to one AI agent (Claude Code, OpenAI Codex CLI, Gemini CLI, or another), pick it on the app's
**AI** page, add a PDF with the **ADD** tray, and press **Teach**. See the wiki:
[Choose an AI engine](https://github.com/Sawtoothz/chalk-student/wiki/Choose-an-AI-Engine) and
[Build your own chapter](https://github.com/Sawtoothz/chalk-student/wiki/Build-Your-Own-Chapter).
A chapter costs roughly $20–30 with strong models; leave **Auto-run** off until you mean it.

## Keep the app private

The app has no login and lets AI agents edit files in this folder. It listens on `127.0.0.1` only, and the Docker
setup publishes it on `127.0.0.1` only. Keep it that way: never expose it to the internet.
