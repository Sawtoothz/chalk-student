#!/usr/bin/env python3
"""Structural and functional check of a chapter package.

    check_package.py packages/thrun-pr/ch03-gaussian-filters

Checks: required files exist; lecture figures referenced exist; highlights.json parses and every
item has page/kind/note; the reference solution passes the oracle tests; the shipped exercise stubs
fail them; the T4 broken file fails its grader; the marimo session executes headlessly.
Exit code 0 = ship, 1 = fix first.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REQUIRED = [
    "map.md", "lecture.md", "translate.md", "highlights.json", "session.py", "README.md",
    "exercises/README.md", "exercises/T1_concept.md", "exercises/T2_derivation.md",
    "exercises/exercise.py", "exercises/models.py", "exercises/clues.md", "exercises/T5_robot.md",
    "exercises/tests/test_T3.py", "exercises/tests/test_T4.py",
    "exercises/solutions/T1.md", "exercises/solutions/T2.md", "exercises/solutions/T3_solution.py",
    "exercises/solutions/T4.md", "exercises/solutions/T5.md",
]


def main(pkg: Path) -> int:
    ok = True

    def fail(msg):
        nonlocal ok
        ok = False
        print("FAIL", msg)

    for f in REQUIRED:
        if not (pkg / f).exists():
            fail(f"missing {f}")
    if not list((pkg / "exercises/T4_debug").glob("*.py")):
        fail("missing exercises/T4_debug/*.py")
    if not list(pkg.glob("annotated*.pdf")):
        fail("missing annotated*.pdf (run highlight_pdf.py)")
    if not list((pkg / "figures").glob("*.svg")):
        fail("no figures/*.svg (run figures/make_figures.py)")

    if not pkg.is_dir():
        fail(f"package directory does not exist: {pkg}")
        print("VERDICT: fix first")
        return 1

    # Missing files were reported above; the content checks below run only on files that exist,
    # so a partly built package gets a list of FAIL lines instead of a traceback.
    if (pkg / "lecture.md").exists():
        lec = (pkg / "lecture.md").read_text(encoding="utf-8")
        for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", lec):
            if not (pkg / m.group(1)).exists():
                fail(f"lecture figure missing: {m.group(1)}")

    spec = {"items": [], "printed_pages": [0, 0]}
    if (pkg / "highlights.json").exists():
        spec = json.loads((pkg / "highlights.json").read_text(encoding="utf-8"))
    for i, it in enumerate(spec["items"]):
        if "page" not in it or "kind" not in it or not it.get("note"):
            fail(f"highlights.json item {i} lacks page/kind/note")
        if "anchor" not in it and "equation" not in it:
            fail(f"highlights.json item {i} has neither anchor nor equation")
    lo, hi = spec["printed_pages"]
    bad = [it for it in spec["items"] if not (lo <= it["page"] <= hi)]
    if bad:
        fail(f"{len(bad)} highlights outside printed pages {lo}-{hi}")
    print(f"highlights: {len(spec['items'])} items")

    env = dict(os.environ)
    def pytest(args, expect_pass, label, extra_env=None):
        e = {**env, **(extra_env or {})}
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", *args], cwd=pkg, env=e, capture_output=True, text=True)
        passed = r.returncode == 0
        tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()[-200:]
        print(f"{label}: {tail}")
        if passed != expect_pass:
            fail(f"{label}: expected {'pass' if expect_pass else 'fail'}")

    pytest(["exercises/tests/test_T3.py"], True, "T3 oracle on reference solution", {"STUDY_IMPL": "solution"})
    pytest(["exercises/tests/test_T3.py", "-x"], False, "T3 oracle on shipped stubs (must fail)")
    pytest(["exercises/tests/test_T4.py"], False, "T4 grader on broken file (must fail)")

    sess = pkg / "session.py"
    if not sess.exists():
        print("VERDICT: fix first")
        return 1
    try:
        s = importlib.util.spec_from_file_location("session", sess)
        mod = importlib.util.module_from_spec(s)
        sys.path.insert(0, str(pkg))
        s.loader.exec_module(mod)
        asyncio.run(mod.app.embed())
        print("session: all cells executed")
    except Exception as e:  # noqa: BLE001
        fail(f"session.py did not execute: {e!r}")

    print("VERDICT:", "ship" if ok else "fix first")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]).resolve()))
