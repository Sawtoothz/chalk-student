#!/usr/bin/env python3
"""The AI engines Chalk can drive, and the settings that pick one. Shared by run_stage.py and the GUI.

An engine is a command-line agent that can run non-interactively in this repo: Claude Code (`claude -p`), OpenAI
Codex (`codex exec`), Gemini CLI (`gemini -p`), or any command you give it. Each stage asks for a model tier
(strong or fast, AGENTS.md "Models"); the settings map the tier to a model name per engine.

Settings live in .cache/gui-settings.json (also holds the GUI's Auto-run switch):

    {"auto": false, "engine": "claude",
     "engines": {"codex": {"command": "", "strong": "gpt-…", "fast": ""}, "custom": {"command": "aider --message {prompt} …"}}}

A command is a template split like a shell line (no shell runs it); {prompt}, {model} and {max_turns} are filled in.
If {model} is empty, it is dropped together with the flag in front of it (so the engine uses its own default).

    engines.py                      # list engines, whether each is installed, and the current choice
    engines.py --test codex         # run a one-line prompt through an engine to check it is installed and logged in
"""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = ROOT / ".cache" / "gui-settings.json"

# stage -> model tier (AGENTS.md "Models")
TIER = {"map": "strong", "highlight": "strong", "lecture": "strong", "cards": "strong", "exercises": "strong",
        "review": "strong", "session": "fast", "build": "fast", "slides": "fast"}

ENGINES: dict[str, dict] = {
    "claude": {
        "label": "Claude Code", "bin": "claude", "format": "claude-json", "slash": True,
        "command": "claude -p {prompt} --model {model} --output-format stream-json --verbose "
                   "--max-turns {max_turns} --permission-mode bypassPermissions",
        "strong": "opus", "fast": "sonnet",
        "install": "curl -fsSL https://claude.ai/install.sh | bash   (or: npm install -g @anthropic-ai/claude-code)",
        "login": "claude   (then /login)",
        "note": "Reference engine: the gold examples and every shipped package were built with it.",
    },
    "codex": {
        "label": "OpenAI Codex CLI", "bin": "codex", "format": "codex-json", "slash": False,
        "command": "codex exec --json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -m {model} {prompt}",
        "strong": "", "fast": "",
        "install": "npm install -g @openai/codex",
        "login": "codex login",
        "note": "Reads AGENTS.md. Leave a model empty to use Codex's default.",
    },
    "gemini": {
        "label": "Gemini CLI", "bin": "gemini", "format": "text", "slash": False,
        "command": "gemini -p {prompt} -m {model} --yolo",
        "strong": "", "fast": "",
        "install": "npm install -g @google/gemini-cli",
        "login": "gemini   (sign in once interactively)",
        "note": "Reads GEMINI.md, which imports AGENTS.md. Leave a model empty to use Gemini's default.",
    },
    "custom": {
        "label": "Custom command", "bin": "", "format": "text", "slash": False,
        "command": "",
        "strong": "", "fast": "",
        "install": "", "login": "",
        "note": "Any agent CLI that takes a prompt and works in the current directory, e.g. "
                "aider --yes-always --model {model} --message {prompt}",
    },
}

# What a non-Claude engine is asked to do: it has no /teach command, so it is told where the pipeline is written down.
PROMPT = ("You are running one stage of Chalk's /teach pipeline in this repository. Read AGENTS.md, then "
          ".claude/skills/teach/SKILL.md, and carry out the skill exactly as if invoked as "
          "`/teach {source} {unit} --stage {stage}`. Do only that stage, follow every rule (never write the learner's "
          "solutions outside exercises/solutions/), run the stage's checks, and finish by writing HANDOFF.md as the "
          "skill says. For the review stage, if you cannot start a separate reviewer agent, do the review yourself "
          "with .claude/agents/teach-reviewer.md as your brief, re-reading the book pages you check.")


# ---------------------------------------------------------------- settings
def load_settings() -> dict:
    s = {"auto": False, "engine": "claude", "engines": {}}
    try:
        s.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    if s.get("engine") not in ENGINES:
        s["engine"] = "claude"
    return s


def save_settings(s: dict) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(s, indent=2), encoding="utf-8")


def config(name: str, settings: dict | None = None) -> dict:
    """the engine's defaults with the user's overrides (empty override = default command; models may be empty)"""
    s = settings or load_settings()
    e = dict(ENGINES[name])
    user = (s.get("engines") or {}).get(name) or {}
    if str(user.get("command", "")).strip():
        e["command"] = str(user["command"]).strip()
    for k in ("strong", "fast"):
        if k in user:
            e[k] = str(user[k]).strip()
    return e


def program(e: dict) -> str:
    try:
        return shlex.split(e["command"])[0] if e["command"].strip() else ""
    except ValueError:
        return ""


def installed(e: dict) -> str | None:
    p = program(e)
    return shutil.which(p) if p else None


# ---------------------------------------------------------------- building a run
def build_command(e: dict, prompt: str, model: str, max_turns: int = 200) -> list[str]:
    try:
        parts = shlex.split(e["command"])
    except ValueError as err:
        raise ValueError(f"{e['label']}: cannot parse the command: {err}") from None
    if not parts:
        raise ValueError(f"{e['label']}: no command set; set one on the AI page")
    if "{prompt}" not in " ".join(parts):
        raise ValueError(f"{e['label']}: the command needs a {{prompt}} placeholder")
    out: list[str] = []
    for p in parts:
        if "{model}" in p and not model:
            if out and out[-1].startswith("-") and p == "{model}":
                out.pop()   # drop "-m" / "--model" with the empty value: the engine picks its default
            continue
        out.append(p.replace("{prompt}", prompt).replace("{model}", model).replace("{max_turns}", str(max_turns)))
    return out


def stage_prompt(e: dict, source: str, unit: int, stage: str) -> str:
    if e.get("slash"):
        return f"/teach {source} {unit} --stage {stage}"
    return PROMPT.format(source=source, unit=unit, stage=stage)


def model_for(e: dict, stage: str, override: str | None = None) -> str:
    return override or e.get(TIER.get(stage, "strong"), "") or ""


# ---------------------------------------------------------------- reading the log
def render(fmt: str, line: str) -> dict:
    """one line of an engine's output -> {kind, text} for the Run page; kind: "" text, "tool", "ok", "bad"."""
    try:
        ev = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return {"kind": "", "text": line}
    if not isinstance(ev, dict):
        return {"kind": "", "text": line}
    if ev.get("type") == "chalk":
        return {"kind": "ok", "text": ev.get("msg", "")}
    if fmt == "claude-json":
        return _claude(ev)
    if fmt == "codex-json":
        return _codex(ev)
    return {"kind": "", "text": line}


def _claude(ev: dict) -> dict:
    t = ev.get("type")
    if t == "assistant":
        parts = []
        for c in ev.get("message", {}).get("content", []):
            if c.get("type") == "text":
                parts.append(c["text"].strip())
            elif c.get("type") == "tool_use":
                inp = c.get("input", {}); arg = inp.get("file_path") or inp.get("command") or inp.get("pattern") or ""
                parts.append(f"› {c.get('name')} {str(arg)[:110]}")
        return {"kind": "tool" if parts and parts[0].startswith("›") else "", "text": "\n".join(p for p in parts if p)}
    if t == "result":
        return {"kind": "ok" if not ev.get("is_error") else "bad",
                "text": f"finished: {ev.get('subtype')} · {ev.get('num_turns')} turns · ${ev.get('total_cost_usd', 0):.2f}"}
    return {"kind": "tool", "text": ""}


def _codex(ev: dict) -> dict:
    """codex exec --json: tolerant of both the item.* events and the older {msg: {type: …}} events"""
    item = ev.get("item") if isinstance(ev.get("item"), dict) else None
    msg = ev.get("msg") if isinstance(ev.get("msg"), dict) else None
    t = ev.get("type", "")
    if item is not None:
        it = item.get("type", "")
        if it in ("agent_message", "assistant_message") and t == "item.completed":
            return {"kind": "", "text": str(item.get("text", "")).strip()}
        if it == "command_execution" and t == "item.started":
            return {"kind": "tool", "text": f"› shell {str(item.get('command', ''))[:110]}"}
        if it == "file_change" and t == "item.completed":
            files = ", ".join(str(c.get("path", "")) for c in item.get("changes", []) if isinstance(c, dict))
            return {"kind": "tool", "text": f"› edit {files[:110]}"}
        return {"kind": "tool", "text": ""}
    if msg is not None:
        mt = msg.get("type", "")
        if mt == "agent_message":
            return {"kind": "", "text": str(msg.get("message", "")).strip()}
        if mt == "exec_command_begin":
            cmd = msg.get("command", "")
            cmd = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
            return {"kind": "tool", "text": f"› shell {cmd[:110]}"}
        if mt == "error":
            return {"kind": "bad", "text": str(msg.get("message", ""))}
        return {"kind": "tool", "text": ""}
    if t in ("turn.failed", "error"):
        err = ev.get("error") or ev.get("message") or ""
        return {"kind": "bad", "text": str(err.get("message", err) if isinstance(err, dict) else err)}
    if t == "turn.completed":
        u = ev.get("usage") or {}
        return {"kind": "ok", "text": f"finished · {u.get('input_tokens', '?')} in / {u.get('output_tokens', '?')} out tokens"}
    return {"kind": "tool", "text": ""}


# ---------------------------------------------------------------- test
def test(name: str, settings: dict | None = None, timeout: int = 180) -> dict:
    """run a one-line prompt through the engine (fast model): proves it is installed, logged in and can answer"""
    e = config(name, settings)
    if not installed(e):
        return {"ok": False, "output": f"{program(e) or 'no command'}: not found on PATH. Install: {e['install'] or 'see the tool’s docs'}"}
    try:
        cmd = build_command(e, "Reply with the single word OK and nothing else. Do not run tools or edit files.",
                            e.get("fast", ""), max_turns=1)
    except ValueError as err:
        return {"ok": False, "output": str(err)}
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": f"no answer within {timeout}s (is it waiting for a login? run `{e['login']}` in a terminal)"}
    lines = [render(e["format"], ln) for ln in (r.stdout + "\n" + r.stderr).splitlines() if ln.strip()]
    text = "\n".join(x["text"] for x in lines if x["text"].strip())[-1500:]
    return {"ok": r.returncode == 0 and "OK" in text.upper(), "exit": r.returncode, "output": text or "(no output)",
            "command": shlex.join(c if len(c) < 60 else c[:57] + "…" for c in cmd)}


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--test":
        print(json.dumps(test(sys.argv[2]), indent=2))
        return 0
    s = load_settings()
    for n in ENGINES:
        e = config(n, s)
        mark = "*" if n == s["engine"] else " "
        print(f"{mark} {n:7} {e['label']:18} {'installed: ' + installed(e) if installed(e) else 'not installed'}"
              f"   strong={e['strong'] or '(default)'} fast={e['fast'] or '(default)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
