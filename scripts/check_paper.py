#!/usr/bin/env python3
"""Check a paper package: required files, and that every file:line cited in translate.md / implementation.md
is backed by code_refs.json (the rule from references/paper-code.md: no anchor from memory).

    check_paper.py PACKAGE_DIR            -> prints findings, exits 1 on any failure
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

pkg = Path(sys.argv[1])
fails, warns = [], []

required = ["map.md", "translate.md", "implementation.md", "code_refs.json"]
for r in required:
    if not (pkg / r).exists():
        fails.append(f"missing {r}")
if not (pkg / "interactive.html").exists() and not (pkg / "session.py").exists():
    warns.append("no interactive.html or session.py (session stage not run)")

if (pkg / "code_refs.json").exists():
    refs = json.loads((pkg / "code_refs.json").read_text(encoding="utf-8"))
    known: dict[str, set[int]] = {}
    repos = []
    for r in refs.get("repos", []):
        repos.append(r["repo"])
        for hits in r.get("symbols", {}).values():
            for h in hits:
                known.setdefault(h["path"], set()).add(int(h["line"]))
    cited = 0
    for name in ("translate.md", "implementation.md"):
        f = pkg / name
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        # `path/file.ext:123` or `path:120-130` or `:123` continuation after a path was named in the same block
        for m in re.finditer(r"`((?:[\w.-]+/)*[\w.-]+\.(?:cpp|cc|c|h|hpp|py|cu|rs|yaml|yml|txt|md)):(\d+)(?:-(\d+))?`", text):
            path, lo, hi = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
            cited += 1
            lines = known.get(path)
            if lines is None:
                # allow a path cited by a shorter relative form (e.g. esekfom.hpp:378 for include/IKFoM_toolkit/esekfom/esekfom.hpp)
                cand = [p for p in known if p.endswith("/" + path) or p == path]
                if not cand:
                    fails.append(f"{name}: `{path}:{lo}` cites a file not in code_refs.json")
                    continue
                lines = set().union(*(known[p] for p in cand))
            # a cited range is backed if any recorded hit falls inside it or within 40 lines of it (a region read with --show)
            if not any(lo - 40 <= ln <= hi + 40 for ln in lines):
                fails.append(f"{name}: `{path}:{lo}` has no hit within 40 lines in code_refs.json")
        for m in re.finditer(r"https://github\.com/([^/\s)]+/[^/\s)]+)/blob/([0-9a-f]{40})/", text):
            repo = "https://github.com/" + m.group(1)
            sha = m.group(2)
            if not any(r["repo"].rstrip("/") == repo and r["commit"] == sha for r in refs["repos"]):
                fails.append(f"{name}: permalink {repo}@{sha[:8]} not in code_refs.json")
    print(f"{cited} file:line citations checked against {len(repos)} repositories")
    if cited == 0:
        warns.append("no file:line citations found in the cards")
    # licence must be stated in translate.md
    if (pkg / "translate.md").exists() and "licen" not in (pkg / "translate.md").read_text(encoding="utf-8").lower() and "licen" not in (pkg / "README.md").read_text(encoding="utf-8").lower():
        warns.append("licence of the anchored repositories is not mentioned in translate.md or README.md")

# implementation.md must have the step table with checks
if (pkg / "implementation.md").exists():
    t = (pkg / "implementation.md").read_text(encoding="utf-8")
    if not re.search(r"\|\s*#\s*\|\s*build\s*\|\s*check", t, re.I):
        fails.append("implementation.md: no step table with build | check columns")
    if re.search(r"\b\d+(\.\d+)?\s*(ms|%)\b.*\b(measured|result)", t, re.I) and "target" not in t.lower():
        warns.append("implementation.md quotes numbers without saying whether they are targets or results")

for w in warns:
    print("warn:", w)
for f in fails:
    print("FAIL:", f)
print("VERDICT:", "ship" if not fails else "fix")
sys.exit(1 if fails else 0)
