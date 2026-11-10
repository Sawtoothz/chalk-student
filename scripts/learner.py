#!/usr/bin/env python3
"""Learner state: clues opened, tests run, solutions revealed. Backs `just clue`, `just reveal`,
`just progress`. State lives in learner.yaml at the repo root.

    learner.py clue thrun-pr 3 T3.2 1        show clue 1 of T3.2 and record it
    learner.py reveal thrun-pr 3 T3          copy solutions/T3_solution.py over exercise.py (gated)
    learner.py progress                      print a table per package
    learner.py note thrun-pr 3 "mistake: forgot to wrap bearing"   free-text note for /tutor
"""

from __future__ import annotations

import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "learner.yaml"


def load():
    if STATE.exists():
        return yaml.safe_load(STATE.read_text(encoding="utf-8")) or {}
    return {}


def save(st):
    STATE.write_text(yaml.safe_dump(st, sort_keys=False, allow_unicode=True), encoding="utf-8")


def pkg_dir(book, ch) -> Path:
    out = subprocess.run([sys.executable, ROOT / "scripts/pages.py", book, str(ch), "--dir"], capture_output=True, text=True, check=True)
    return Path(out.stdout.strip())


def key(book, ch):
    return f"{book}/ch{int(ch):02d}"


def clue(book, ch, exercise, n):
    pkg = pkg_dir(book, ch)
    text = (pkg / "exercises/clues.md").read_text(encoding="utf-8")
    m = re.search(rf"^## {re.escape(exercise)}\b.*?\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        sys.exit(f"no clues section for {exercise}")
    items = re.findall(r"^\d+\.\s+(.*)$", m.group(1), re.M)
    n = int(n)
    if not 1 <= n <= len(items):
        sys.exit(f"{exercise} has {len(items)} clues")
    st = load()
    k = key(book, ch)
    st.setdefault(k, {}).setdefault("clues", {}).setdefault(exercise, [])
    if n not in st[k]["clues"][exercise]:
        st[k]["clues"][exercise].append(n)
    st[k].setdefault("log", []).append({"t": dt.datetime.now().isoformat(timespec="minutes"), "clue": f"{exercise}:{n}"})
    save(st)
    print(f"[{exercise} clue {n}/{len(items)}]\n{items[n - 1]}")


def reveal(book, ch, tier):
    pkg = pkg_dir(book, ch)
    st = load()
    k = key(book, ch)
    rec = st.get(k, {})
    tested = rec.get("tests_run", 0) > 0
    tier_clues = [ex for ex in rec.get("clues", {}) if ex.startswith(tier)]
    all_clues = tier_clues and all(len(rec["clues"][ex]) >= 3 for ex in tier_clues)
    if not (tested or all_clues):
        sys.exit(f"not yet: run `just test {book} {ch}` once, or open all clues of {tier}, before revealing")
    if not (pkg / "exercises/solutions").exists():
        sys.exit("This is the student edition: solutions are not included. Use the clues (just clue) and the tests, "
                 "or ask your instructor.")
    src = {"T3": pkg / "exercises/solutions/T3_solution.py"}.get(tier)
    if src is None or not src.exists():
        sys.exit(f"nothing to reveal for {tier}; read exercises/solutions/{tier}.md")
    dst = pkg / "exercises/exercise.py"
    shutil.copy(dst, dst.with_suffix(".py.bak"))
    body = src.read_text(encoding="utf-8").replace("from ..models", "from .models")
    dst.write_text(body, encoding="utf-8")
    rec.setdefault("revealed", []).append({"tier": tier, "t": dt.datetime.now().isoformat(timespec="minutes")})
    st[k] = rec
    save(st)
    print(f"revealed {tier} into {dst} (your version saved as exercise.py.bak)")


def progress():
    st = load()
    if not st:
        print("no learner state yet")
        return
    print(f"{'package':24} {'tests':>6} {'pass':>6} {'clues':>6} revealed")
    for k, rec in st.items():
        if not isinstance(rec, dict):
            continue
        nclues = sum(len(v) for v in rec.get("clues", {}).values())
        print(f"{k:24} {rec.get('tests_run', 0):>6} {rec.get('last_pass', '-'):>6} {nclues:>6} {','.join(r['tier'] for r in rec.get('revealed', []))}")


def record_test(book, ch, passed, failed):
    st = load()
    k = key(book, ch)
    rec = st.setdefault(k, {})
    rec["tests_run"] = rec.get("tests_run", 0) + 1
    rec["last_pass"] = f"{passed}/{passed + failed}"
    rec.setdefault("log", []).append({"t": dt.datetime.now().isoformat(timespec="minutes"), "tests": rec["last_pass"]})
    save(st)


def note(book, ch, text):
    st = load()
    st.setdefault(key(book, ch), {}).setdefault("notes", []).append({"t": dt.datetime.now().isoformat(timespec="minutes"), "note": text})
    save(st)
    print("noted")


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:] or ["progress"]
    {"clue": lambda: clue(*rest), "reveal": lambda: reveal(*rest), "progress": progress,
     "note": lambda: note(rest[0], rest[1], " ".join(rest[2:])),
     "record-test": lambda: record_test(rest[0], rest[1], int(rest[2]), int(rest[3]))}[cmd]()
