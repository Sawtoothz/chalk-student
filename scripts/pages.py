#!/usr/bin/env python3
"""Resolve a source (book or paper) and unit (chapter, or the whole paper) from books.yaml.

    pages.py thrun-pr 3 --dir      -> packages/thrun-pr/ch03-gaussian-filters
    pages.py thrun-pr 3 --range    -> "39 84 21"   (printed lo, printed hi, offset)
    pages.py thrun-pr 3 --pdf      -> library/thrun-pr.pdf
    pages.py thrun-pr 3 --json     -> everything as JSON (what the /teach skill reads)
    pages.py thrun-pr --probe      -> guess the printed-to-pdf offset and list the PDF outline
    pages.py --list                -> every source and unit with its package status, as JSON (the GUI reads this)

A paper is a source with `kind: paper`; it has one unit, 1, covering the whole PDF, and an offset of 0
(its "printed" pages are the PDF pages). Everything downstream treats it like a one-chapter book.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "books.yaml"

# stage -> the file whose presence means the stage has finished (order matters)
STAGE_FILES = [
    ("map", "map.md"), ("highlight", "highlights.json"), ("lecture", "lecture.md"), ("cards", "translate.md"),
    ("exercises", "exercises/clues.md"), ("session", "session.py"), ("build", "reader.html"), ("review", "REVIEW.md"),
    ("slides", "slides/review.pdf"),   # optional, after review: class and review decks (references/slides-spec.md)
]
STAGES = [s for s, _ in STAGE_FILES]


def slug(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:40].rstrip("-")


def load() -> dict:
    return yaml.safe_load(INDEX.read_text(encoding="utf-8")) or {}


def save(data: dict) -> None:
    """Write books.yaml, rewriting only the top-level entries that changed. Unchanged entries keep their text,
    and every entry keeps the comment lines above it, so the hand-written file survives an ingest or a GUI upload."""
    text = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
    old = yaml.safe_load(text) or {}
    header, blocks, cur, pending = [], {}, None, []
    for ln in text.splitlines(keepends=True):
        m = re.match(r"^([A-Za-z0-9][\w-]*):", ln)
        if m:
            cur = m.group(1)
            blocks[cur] = {"prefix": pending, "body": [ln]}
            pending = []
        elif cur is None:
            header.append(ln)
        elif ln.strip() == "" or ln.startswith("#"):
            pending.append(ln)  # blank lines and comments belong to the entry below them
        else:
            blocks[cur]["body"].extend(pending + [ln]); pending = []
    out = ["".join(header)]
    for k, v in data.items():
        b = blocks.get(k)
        prefix = "".join(b["prefix"]) if b else "\n"
        if b and old.get(k) == v:
            body = "".join(b["body"])
        else:
            body = yaml.safe_dump({k: v}, sort_keys=False, allow_unicode=True, width=120, default_flow_style=None)
        out.append(prefix + body)
    INDEX.write_text("".join(out).rstrip("\n") + "\n" + "".join(pending), encoding="utf-8")


def units(src: dict) -> dict:
    """chapters of a book, or the single whole-paper unit."""
    if src.get("kind") == "paper":
        n = src.get("pages")
        return {1: {"title": "Whole paper", "pages": [1, n] if n else [1, 1], "lesson": src.get("lesson")}}
    return {int(k): v for k, v in (src.get("chapters") or {}).items()}


def package_dir(src_id: str, src: dict, unit: int) -> Path:
    u = units(src)[unit]
    if src.get("kind") == "paper":
        return ROOT / "packages" / src_id / "paper"
    return ROOT / "packages" / src_id / f"ch{unit:02d}-{slug(u['title'])}"


def status(pkg: Path) -> dict:
    """which stages are done, which is running or failed (from .runs/status.json), what comes next."""
    done = [s for s, f in STAGE_FILES if (pkg / f).exists()]
    st = {"done": done, "next": next((s for s in STAGES if s not in done), None), "running": None, "failed": None}
    sj = pkg / ".runs" / "status.json"
    if sj.exists():
        try:
            j = json.loads(sj.read_text(encoding="utf-8"))
            if j.get("state") == "running":
                st["running"] = j.get("stage")
            elif j.get("state") == "failed":
                st["failed"] = j.get("stage")
            st["last_run"] = j
        except json.JSONDecodeError:
            pass
    hand = pkg / "HANDOFF.md"
    if hand.exists():
        txt = hand.read_text(encoding="utf-8")
        st["handoff"] = txt[:1500]
        m = re.search(r"next[_ -]?stage:\s*(\w+)", txt, re.I)
        if m:
            st["next"] = m.group(1)
    return st


def listing() -> list[dict]:
    out = []
    for sid, src in load().items():
        us = units(src)
        rows = []
        for n, u in sorted(us.items()):
            pkg = package_dir(sid, src, n)
            rows.append({"unit": n, "title": u["title"], "pages": u.get("pages"), "lesson": u.get("lesson"),
                         "package_dir": str(pkg.relative_to(ROOT)), **status(pkg)})
        out.append({"id": sid, "kind": src.get("kind", "book"), "title": src.get("title", sid), "authors": src.get("authors"),
                    "year": src.get("year"), "pdf": src.get("pdf"), "offset": src.get("offset"),
                    "pdf_present": bool(src.get("pdf")) and (ROOT / src["pdf"]).exists(),
                    "sections": src.get("sections"), "units": rows})
    return out


def probe(src_id: str, src: dict):
    import pymupdf

    path = ROOT / src["pdf"]
    if not path.exists():
        sys.exit(f"{src_id}: PDF not found at {path}. Copy it into library/ (or run `just ingest`) and probe again.")
    doc = pymupdf.open(path)
    print(f"{src_id}: {doc.page_count} pdf pages")
    for lvl, title, page in doc.get_toc():
        if lvl <= 2:
            print(f"  {'  ' * (lvl - 1)}pdf {page:4d}  {title}")
    off = guess_offset(doc)
    if off is not None:
        print(f"  likely offset (pdf = printed + offset): {off}")
    known = src.get("offset")
    if known is None:
        print("  books.yaml offset: not set")
    elif off == known:
        print(f"  books.yaml offset {known}: confirmed")
    else:
        print(f"  books.yaml offset {known}: DIFFERS from the guess {off}; check one page by hand")


def guess_offset(doc) -> int | None:
    votes: dict[int, int] = {}
    for p in range(min(20, doc.page_count // 4), min(doc.page_count, 120)):
        lines = [ln.strip() for ln in doc[p].get_text().splitlines() if ln.strip()]
        for cand in lines[:2] + lines[-2:]:
            if cand.isdigit() and 1 <= int(cand) <= doc.page_count:
                off = (p + 1) - int(cand)
                votes[off] = votes.get(off, 0) + 1
    return max(votes, key=votes.get) if votes else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", nargs="?")
    ap.add_argument("unit", nargs="?", type=int)
    ap.add_argument("--dir", action="store_true")
    ap.add_argument("--range", action="store_true")
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        print(json.dumps(listing(), indent=2))
        return 0
    data = load()
    if a.source not in data:
        print(f"unknown source {a.source}; known: {', '.join(data)}", file=sys.stderr)
        return 2
    src = data[a.source]
    if a.probe:
        probe(a.source, src)
        return 0
    if a.unit is None:
        print("chapter (or 1 for a paper) required", file=sys.stderr)
        return 2
    us = units(src)
    u = us.get(a.unit)
    if u is None:
        print(f"unit {a.unit} not in books.yaml for {a.source}", file=sys.stderr)
        return 2
    off = 0 if src.get("kind") == "paper" else src.get("offset")
    if off is None:
        print(f"offset for {a.source} is null; run: pages.py {a.source} --probe", file=sys.stderr)
        return 2
    off = int(off)
    lo, hi = u["pages"]
    pkg = package_dir(a.source, src, a.unit)
    if a.dir:
        print(pkg)
    elif a.range:
        print(lo, hi, off)
    elif a.pdf:
        print(ROOT / src["pdf"])
    else:
        print(json.dumps({
            "book": a.source, "kind": src.get("kind", "book"), "title": src.get("title"), "chapter": a.unit, "chapter_title": u["title"],
            "lesson": u.get("lesson"), "printed_pages": [lo, hi], "pdf_pages": [lo + off, hi + off],
            "offset": off, "pdf": str(ROOT / src["pdf"]), "package_dir": str(pkg), "sections": src.get("sections"),
        }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
