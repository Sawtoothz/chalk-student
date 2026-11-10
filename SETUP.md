# Setup and first run

## 1. Machine (half a day)

On the A6000 Proxmox host, an Ubuntu 24.04 VM with Tailscale. Then:

```bash
sudo apt install -y python3.12-venv build-essential cmake libreoffice-impress   # LibreOffice: renders the slide PDFs
curl -LsSf https://astral.sh/uv/install.sh | sh
cargo install just          # or: sudo snap install just --classic
pipx install marimo          # or rely on uv sync below
```

code-server for browser editing (optional but recommended):

```bash
curl -fsSL https://code-server.dev/install.sh | sh
sudo systemctl enable --now code-server@$USER
# then edit ~/.config/code-server/config.yaml: bind-addr 0.0.0.0:8080, auth password
```

## 2. Repo

```bash
unzip chalk-starter.zip && cd chalk
git init && git add -A && git commit -m "chalk: starter pack"
uv sync
mkdir -p library && cp /path/to/thrun-pr.pdf library/
just probe thrun-pr          # confirms offset 21
just check examples/..       # see 4 below
```

Claude Code in the repo picks up `CLAUDE.md`, `.claude/skills/teach/` and `.claude/agents/`.
Install the superpowers plugin if not already installed, and the caveman plugin
(`/plugin install caveman` or per its README) for terse chat replies; it does not affect package files.

## 3. Prove the pipeline on the gold example

```bash
cd examples/thrun-pr/ch03-gaussian-filters
python3 -m exercises.T5_sim                      # regenerates exercises/data/
cd ../../..
python3 scripts/check_package.py examples/thrun-pr/ch03-gaussian-filters
python3 scripts/render_pages.py examples/thrun-pr/ch03-gaussian-filters/annotated.pdf examples/thrun-pr/ch03-gaussian-filters/.pages
python3 scripts/build_viewer.py examples/thrun-pr/ch03-gaussian-filters examples/thrun-pr/ch03-gaussian-filters/.pages examples/thrun-pr/ch03-gaussian-filters/reader.html
```

Open `reader.html` in a browser (from Tailscale: `python3 -m http.server` in the package dir).
Open `session.py` with `marimo edit`.

## 4. Models

Set the session model to Opus 5.5 for `/teach`. The reviewer agent pins its own model in
`.claude/agents/teach-reviewer.md` (`model: opus`; change to the Fable identifier if your plan has it).
Use Sonnet 5.5 for fix loops after `just check` says ship. See the Models table in `CLAUDE.md`.

## 5. First real run

Chapter 4 (nonparametric filters) is the first target: a different algorithm family from the
example, and it leads straight into MCL on the tracked robot. It runs as short sessions, one stage
each, with `/clear` between; the prompts are in `FIRST-PROMPT.md`. Expect six to eight sessions of
ten to twenty minutes. After the last one, read `REVIEW.md` first, then `map.md`, then the Reader.

Then your critique: what to cut, what was shallow, which note or exercise missed. Put it in
`learner.yaml` under `feedback:` or tell Claude Code directly; the second run of `/teach` should
show the difference.

## 6. Daily loop

```
just teach <book> <ch>      # only the deterministic rebuild; the skill is run in Claude Code
just check <book> <ch>
just view  <book> <ch>      # Reader page
just session <book> <ch>    # marimo
just test  <book> <ch>      # your exercise.py against the oracles
just clue  <book> <ch> T3.2 1
just reveal <book> <ch> T3  # gated
```


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

## GUI mode

```bash
just serve                      # http://localhost:8765 on this machine
just serve 100.x.y.z 8765       # or a Tailscale address, to use it from the laptop
```

Library: drop a PDF with a short id (`boyd-cvx`), pick book or paper, Add to library. A book gets its chapters from
the PDF outline and a guessed printed-page offset (check it once against any page; the Library shows a form if the
guess failed). Press **Teach** on a unit; the Run page shows the stage list, the live log of the AI agent's session,
and the last HANDOFF. **Continue to <stage>** runs the next stage. **Open reader**
appears after the build stage. The app runs one stage at a time.

**AI engine** (the **AI:** link in the top bar): pick which agent runs the stages and which models it uses.

| Engine | Install | Log in once |
| --- | --- | --- |
| Claude Code (default; every shipped package was built with it) | `curl -fsSL https://claude.ai/install.sh \| bash` | `claude`, then `/login` |
| OpenAI Codex CLI | `npm install -g @openai/codex` | `codex login` |
| Gemini CLI | `npm install -g @google/gemini-cli` | `gemini` |
| Custom command | any agent CLI that takes a prompt, e.g. `aider --yes-always --model {model} --message {prompt}` | its own |

Set a **strong** model (the stages that read the book, exercises, review) and a **fast** one (session, build,
slides); empty means the engine's default. **Test** sends a one-line prompt to prove the tool is installed and logged
in. The choice is saved in `.cache/gui-settings.json` and also used by `just stage`; `just engines` lists them.
Every engine follows the same pipeline (`.claude/skills/teach/`) and rules (`AGENTS.md`), and every package must
still pass `just check` and review whatever built it.
**Auto-run** (switch in the top bar, remembered across restarts): when on, Teach runs every stage of the unit in turn,
map → … → review → slides, without pressing Continue; it stops on a failure, on Stop, or when switched off. A whole
chapter costs about $20–30.
After review, **Make slides** builds two slide decks (Class, with speaker notes; Review, for revision) as PDF study
copies; the Reader's **Slides** tab shows them and offers the PDF download. This edition makes no `.pptx`: each PDF
is watermarked "Created by Chalk" and carries a notice asking AI tools not to turn it into a presentation. Use the
slides to learn the chapter, then build your own talk. Re-render after editing a deck's YAML with `just slides <book> <chapter>`.
