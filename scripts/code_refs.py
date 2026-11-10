#!/usr/bin/env python3
"""Anchor "in the original code" references to real lines of a real commit, so cards never cite from memory.

    code_refs.py https://github.com/hku-mars/FAST_LIO --grep h_share_model df_dx esti_plane
    code_refs.py https://github.com/hku-mars/FAST_LIO --show src/laserMapping.cpp:638-660
    code_refs.py https://github.com/hku-mars/FAST_LIO --grep ... --json packages/x/paper/code_refs.json

Shallow-clones into .cache/repos/<owner>-<name> (gitignored), prints the commit, the licence, and for each symbol
the matching lines as `path:line  text` plus a permalink to that commit. --json appends the matches to a file the
cards stage cites from. Only GitHub/GitLab-style https URLs; use --branch for a non-default branch.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "repos"
SKIP = re.compile(r"\.(png|jpg|jpeg|gif|pdf|bag|pcd|bin|so|a|o|zip|gz)$|/(build|\.git|third_party|thirdparty)/", re.I)


def clone(url: str, branch: str | None) -> tuple[Path, str]:
    m = re.match(r"https?://(github|gitlab)\.com/([^/]+)/([^/.]+)", url)
    if not m:
        sys.exit("expected https://github.com/<owner>/<repo>")
    owner, name = m.group(2), m.group(3)
    dest = CACHE / f"{owner}-{name}"
    if not dest.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        cmd = ["git", "clone", "-q", "--depth", "1"] + (["--branch", branch] if branch else []) + [url, str(dest)]
        subprocess.run(cmd, check=True)
    sha = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    return dest, sha


def licence(dest: Path) -> str:
    for n in ("LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING"):
        f = dest / n
        if f.exists():
            head = f.read_text(encoding="utf-8", errors="replace")[:300]
            for key in ("GNU GENERAL PUBLIC LICENSE", "Apache License", "MIT License", "BSD", "Mozilla Public"):
                if key.lower() in head.lower():
                    return key + (" v2" if "Version 2" in head and "GNU" in key else " v3" if "Version 3" in head and "GNU" in key else "")
            return head.splitlines()[0].strip()
    return "no LICENSE file found"


def grep(dest: Path, symbol: str, limit: int) -> list[dict]:
    out = []
    for f in sorted(dest.rglob("*")):
        if not f.is_file() or SKIP.search(str(f)) or f.suffix.lower() not in {".cpp", ".cc", ".c", ".h", ".hpp", ".py", ".cu", ".rs", ".m", ".jl", ".launch", ".yaml", ".yml", ".cmake", ".txt", ".md"}:
            continue
        try:
            for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if symbol in line:
                    out.append({"path": str(f.relative_to(dest)), "line": i, "text": line.strip()[:160]})
                    if len(out) >= limit:
                        return out
        except OSError:
            pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--branch")
    ap.add_argument("--grep", nargs="*", default=[])
    ap.add_argument("--show", nargs="*", default=[], help="path:lo-hi")
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()

    dest, sha = clone(a.url, a.branch)
    base = a.url.rstrip("/") + f"/blob/{sha}/"
    print(f"{a.url}  @ {sha[:12]}  licence: {licence(dest)}")
    refs = {"repo": a.url, "commit": sha, "licence": licence(dest), "symbols": {}}
    for sym in a.grep:
        hits = grep(dest, sym, a.limit)
        refs["symbols"][sym] = [{**h, "url": f"{base}{h['path']}#L{h['line']}"} for h in hits]
        print(f"\n{sym}: {len(hits)} hit(s)")
        for h in hits:
            print(f"  {h['path']}:{h['line']}  {h['text']}")
    for spec in a.show:
        path, rng = spec.split(":")
        lo, hi = (int(x) for x in rng.split("-")) if "-" in rng else (int(rng), int(rng))
        lines = (dest / path).read_text(encoding="utf-8", errors="replace").splitlines()
        print(f"\n{path}:{lo}-{hi}   {base}{path}#L{lo}-L{hi}")
        for i in range(lo, min(hi, len(lines)) + 1):
            print(f"{i:5d}  {lines[i - 1]}")
    if a.json:
        old = json.loads(a.json.read_text(encoding="utf-8")) if a.json.exists() else {"repos": []}
        prev = next((r for r in old["repos"] if r["repo"] == refs["repo"]), None)
        if prev and prev.get("commit") == refs["commit"]:          # same commit: merge symbols, keep earlier ones
            prev["symbols"].update(refs["symbols"]); prev["licence"] = refs["licence"]
        else:
            old["repos"] = [r for r in old["repos"] if r["repo"] != refs["repo"]] + [refs]
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(old, indent=2), encoding="utf-8")
        print(f"\nwrote {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
