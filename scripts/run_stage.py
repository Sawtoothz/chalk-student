#!/usr/bin/env python3
"""Run one /teach stage headlessly with an AI engine and record it. Shared by `just stage` and the GUI.

    run_stage.py thrun-pr 4 --stage map
    run_stage.py thrun-pr 4 --stage next            # whatever HANDOFF.md names
    run_stage.py thrun-pr 4 --stage review --model opus
    run_stage.py thrun-pr 4 --stage map --engine codex

The engine (Claude Code, Codex, Gemini CLI or a custom command) and its strong/fast models come from the GUI's AI page
(.cache/gui-settings.json, see engines.py); --engine and --model override them for one run.

Writes packages/<src>/<unit>/.runs/<timestamp>-<stage>.log (one JSON event per line, as Claude Code streams them,
plus plain lines for our own messages) and .runs/status.json {state, stage, started, ended, exit, log}.
Exit code is the engine's. Needs the engine's CLI on PATH and the repo as cwd (the pipeline lives in .claude/skills/teach/).
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engines  # noqa: E402
from pages import ROOT, STAGES, load, package_dir, status  # noqa: E402


def resolve_stage(pkg: Path, stage: str) -> str:
    if stage != "next":
        return stage
    st = status(pkg)
    if st.get("next"):
        return st["next"]
    return "map"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("unit", type=int)
    ap.add_argument("--stage", default="next")
    ap.add_argument("--model")
    ap.add_argument("--engine", choices=list(engines.ENGINES), help="default: the one chosen on the GUI's AI page")
    ap.add_argument("--max-turns", type=int, default=200)
    ap.add_argument("--dry-run", action="store_true", help="print the command and exit")
    a = ap.parse_args()

    data = load()
    if a.source not in data:
        print(f"unknown source {a.source}", file=sys.stderr)
        return 2
    pkg = package_dir(a.source, data[a.source], a.unit)
    stage = resolve_stage(pkg, a.stage)
    if stage not in STAGES:
        print(f"unknown stage {stage}; one of {', '.join(STAGES)}", file=sys.stderr)
        return 2
    name = a.engine or engines.load_settings()["engine"]
    eng = engines.config(name)
    model = engines.model_for(eng, stage, a.model)
    prompt = engines.stage_prompt(eng, a.source, a.unit, stage)
    try:
        cmd = engines.build_command(eng, prompt, model, a.max_turns)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    if a.dry_run:
        print(shlex.join(cmd))
        return 0

    runs = pkg / ".runs"
    runs.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log = runs / f"{ts}-{stage}.log"
    stj = runs / "status.json"

    def write_status(state: str, exit_code: int | None = None):
        stj.write_text(json.dumps({"state": state, "stage": stage, "engine": name, "model": model or "default", "started": ts,
                                   "ended": datetime.now(timezone.utc).isoformat() if state != "running" else None,
                                   "exit": exit_code, "log": str(log.relative_to(ROOT))}, indent=2), encoding="utf-8")

    write_status("running")
    t0 = time.time()
    with log.open("w", encoding="utf-8") as fh:
        shown = prompt if eng.get("slash") else f"/teach {a.source} {a.unit} --stage {stage}"
        fh.write(json.dumps({"type": "chalk", "engine": name, "format": eng["format"],
                             "msg": f"{shown}  ({eng['label']}, model {model or 'default'})"}) + "\n"); fh.flush()
        try:
            proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                    stdin=subprocess.DEVNULL,
                                    env={**os.environ, "CHALK_STAGE": stage})
        except FileNotFoundError:
            msg = f"{cmd[0]} not found on PATH. Install {eng['label']} ({eng['install'] or 'see its docs'}) or pick another engine on the AI page."
            fh.write(json.dumps({"type": "chalk", "msg": msg}) + "\n")
            write_status("failed", 127)
            print(msg, file=sys.stderr)
            return 127
        for line in proc.stdout:
            fh.write(line); fh.flush()
            sys.stdout.write(line); sys.stdout.flush()
        code = proc.wait()
        fh.write(json.dumps({"type": "chalk", "msg": f"exit {code} after {time.time() - t0:.0f}s"}) + "\n")
    write_status("done" if code == 0 else "failed", code)
    return code


if __name__ == "__main__":
    sys.exit(main())
