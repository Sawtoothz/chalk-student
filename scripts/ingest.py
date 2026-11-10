#!/usr/bin/env python3
"""Add a PDF to the library: copy it, read its outline, guess the page offset, write the entry to books.yaml.

    ingest.py /path/to/file.pdf --id boyd-cvx                     # book: chapters from the table of contents
    ingest.py /path/to/paper.pdf --id grisetti-gslam --kind paper  # paper: one unit, section list kept for the map stage
    ingest.py file.pdf --id x --dry-run                            # print the entry, change nothing

Used by `just ingest` and by the GUI upload. Prints the resulting entry as JSON.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

import pymupdf
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pages import ROOT, guess_offset, load, save  # noqa: E402

CHAPTER_RE = re.compile(r"^\s*(?:chapter\s+)?(\d{1,2})\b[\s.:\-—]*(.*)$", re.I)


def chapters_from_toc(doc, offset: int | None) -> dict:
    """numbered chapters from the outline -> {n: {title, pages:[lo, hi]}} in printed pages.
    Uses whichever outline level (1 or 2) holds the most entries that look like 'N Title' / 'Chapter N Title'."""
    toc = [(lvl, t.strip(), p) for lvl, t, p in doc.get_toc() if t.strip()]
    best: list = []
    by_level = {}
    for L in (1, 2):
        found = []
        for lvl, title, page in toc:
            if lvl != L:
                continue
            m = CHAPTER_RE.match(title)
            # '1.1 Intro' leaves '1 Intro' after the number: a section, not a chapter; '10 3D Reconstruction' is a chapter
            if m and m.group(2) and not re.match(r"^\d+(\s|\.\d|$)", m.group(2)):
                found.append((int(m.group(1)), m.group(2).strip(), page))
        by_level[L] = found
        if len(found) > len(best):
            best = found
    if best:  # chapters split across levels (H&Z: ch. 1 at level 1, the rest under Part headings at level 2)
        have = {n for n, _, _ in best}
        other = by_level[1] if best is by_level[2] else by_level[2]
        best = sorted(best + [c for c in other if c[0] not in have], key=lambda c: c[2])
    if not best:
        best = chapters_from_page_heads(doc, toc)
    if not best and not toc:
        return chapters_from_contents(doc, offset)
    if not best:
        return {}
    off = offset or 0
    out = {}
    for i, (n, title, page) in enumerate(best):
        nxt = best[i + 1][2] - 1 if i + 1 < len(best) else doc.page_count
        # a chapter also ends at the next level-1 entry that is not a chapter (part divider, appendix, bibliography)
        starts = {b[2] for b in best}
        brk = next((p - 1 for lvl, t, p in toc if p > page and lvl <= 1 and p not in starts and not CHAPTER_RE.match(t)), doc.page_count)
        end_pdf = min(nxt, brk)
        out[n] = {"title": title, "pages": [max(1, page - off), max(1, end_pdf - off)]}
    return out


def chapters_from_page_heads(doc, toc) -> list:
    """Fallback for outlines with unnumbered chapter titles (e.g. Barfoot): an outline entry at level 1 or 2 is
    chapter n when its first page's text starts with the bare number n (the next in sequence, which skips running
    heads such as '4 / Introduction') on one line and a title on the next. The title comes from the outline with
    editing markup such as 'orange (2ed new)' removed, since page titles can wrap."""
    found, last = [], 0
    for lvl, title, page in toc:
        if lvl > 2 or not 1 <= page <= doc.page_count:
            continue
        lines = [ln.strip() for ln in doc[page - 1].get_text().splitlines() if ln.strip()]
        if len(lines) < 2 or lines[0] not in (str(last + 1), f"Chapter {last + 1}"):
            continue
        head = re.sub(r"^\(2ed [a-z]+\)\s*", "", lines[1])
        clean = re.sub(r"^.*\(2ed [a-z]+\)\s*", "", title).strip()
        if head.split() and head.split()[0].lower() == (clean.split() or [""])[0].lower():
            last += 1
            found.append((last, clean, page))
    return found

def chapters_from_contents(doc, offset: int | None) -> dict:
    """Fallback for PDFs with no outline at all (e.g. Rawlings-Mayne-Diehl): read the printed Contents pages, where a
    chapter is the bare number n (next in sequence), its title, its printed page, then its first section 'n.1'.
    Appendices ('B', title, page, 'B.1') only mark where the last chapter ends."""
    toks: list[str] = []
    for i in range(min(doc.page_count, 60)):
        text = doc[i].get_text()
        if not toks and "Contents" not in text[:300]:
            continue
        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not re.fullmatch(r"[. ]+", ln.strip())]
        if toks and not any(re.match(r"^(\d+|[A-Z])\.\d", ln) for ln in lines):
            break  # past the Contents pages
        toks += [re.sub(r"[ .]+$", "", ln) for ln in lines]
    found, apps, n = [], [], 1
    for j in range(len(toks) - 3):
        a, title, page, sec = toks[j:j + 4]
        if not page.isdigit() or re.match(r"^[\d.]+$", title):
            continue
        if a == str(n) and sec == f"{n}.1":
            found.append((n, title, int(page))); n += 1
        elif re.fullmatch(r"[A-Z]", a) and sec == f"{a}.1" and found:
            apps.append(int(page))
    if not found:
        return {}
    off = offset or 0
    last = (min(p for p in apps if p > found[-1][2]) - 1) if any(p > found[-1][2] for p in apps) else doc.page_count - off
    out = {}
    for i, (k, title, page) in enumerate(found):
        end = found[i + 1][2] - 1 if i + 1 < len(found) else last
        out[k] = {"title": title, "pages": [page, end]}
    return out


def sections_from_toc(doc) -> list[str]:
    secs = [t.strip() for lvl, t, _ in doc.get_toc() if lvl <= 2 and t.strip()]
    if secs:
        return secs[:30]
    # no outline: numbered headings from the text of the first pages
    heads = []
    for p in range(min(doc.page_count, 20)):
        for ln in doc[p].get_text().splitlines():
            if re.match(r"^\s*\d{1,2}(\.\d)?\s+[A-Z][^.]{3,60}$", ln.strip()):
                heads.append(ln.strip())
    return heads[:30]


def guess_meta(doc) -> dict:
    meta = doc.metadata or {}
    title = (meta.get("title") or "").strip()
    if not title:
        first = [ln.strip() for ln in doc[0].get_text().splitlines() if ln.strip()]
        title = max(first[:6], key=len) if first else ""
    author = (meta.get("author") or "").strip()
    year = None
    m = re.search(r"(19|20)\d{2}", meta.get("creationDate", "") or "")
    if m:
        year = int(m.group(0))
    return {"title": title[:120], "authors": author[:120], "year": year}


def ingest(pdf: Path, sid: str, kind: str, title: str | None, authors: str | None, year: int | None, dry: bool) -> dict:
    doc = pymupdf.open(pdf)
    meta = guess_meta(doc)
    dest = ROOT / "library" / f"{sid}.pdf"
    entry: dict = {
        "title": title or meta["title"] or sid, "authors": authors or meta["authors"] or None, "year": year or meta["year"],
        "pdf": str(dest.relative_to(ROOT)), "kind": kind,
    }
    if kind == "paper":
        entry.update({"pages": doc.page_count, "offset": 0, "sections": sections_from_toc(doc), "lesson": None})
        note = f"paper, {doc.page_count} pages, {len(entry['sections'])} sections found"
    else:
        off = guess_offset(doc)
        chapters = chapters_from_toc(doc, off)
        entry.update({"offset": off, "track": None, "chapters": chapters})
        note = f"book, {doc.page_count} pages, {len(chapters)} chapters from the outline, offset {'guessed ' + str(off) if off is not None else 'unknown'}"
        if not chapters:
            note += " — no numbered chapters in the outline; add them by hand or teach it as a paper"
    if not dry:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if pdf.resolve() != dest.resolve():
            shutil.copyfile(pdf, dest)
        data = load()
        prev = data.get(sid) or {}
        # re-ingest keeps the hand-curated fields unless given on the command line
        for k, given in (("title", title), ("authors", authors), ("year", year)):
            if not given and prev.get(k):
                entry[k] = prev[k]
        if kind == "paper" and not entry.get("sections") and prev.get("sections"):
            entry["sections"] = prev["sections"]
        for k in ("track", "lesson"):
            if prev.get(k) and not entry.get(k):
                entry[k] = prev[k]
        data[sid] = entry
        save(data)
    return {"id": sid, "note": note, "entry": entry, "written": not dry}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--id", required=True, help="short id, e.g. boyd-cvx")
    ap.add_argument("--kind", choices=["book", "paper"], default="book")
    ap.add_argument("--title")
    ap.add_argument("--authors")
    ap.add_argument("--year", type=int)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,40}", a.id):
        print("id must be lowercase letters, digits and dashes", file=sys.stderr)
        return 2
    if not a.pdf.exists():
        print(f"no such file: {a.pdf}", file=sys.stderr)
        return 2
    print(json.dumps(ingest(a.pdf, a.id, a.kind, a.title, a.authors, a.year, a.dry_run), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
