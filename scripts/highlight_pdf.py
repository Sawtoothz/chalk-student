#!/usr/bin/env python3
"""Paint highlights.json into a copy of a PDF chapter.

Usage:
    highlight_pdf.py BOOK.pdf highlights.json OUT.pdf [--first N --last M]

highlights.json:
{
  "book": "thrun-pr",
  "page_offset": 21,              # pdf_page = printed_page + page_offset
  "colors": {"key": "#F5D33D", ...},
  "items": [
    {"page": 41, "kind": "key", "anchor": "exact words from the page", "note": "why it matters"},
    {"page": 42, "kind": "derive", "equation": "3.4", "note": "..."},       # box the equation by its number
    {"page": 43, "kind": "section", "anchor": "3.2.2", "note": "must read"}  # section-level note
  ]
}

Anchors are matched with page.search_for (without dehyphenation, see SEARCH_FLAGS); unmatched ones fall back to a whitespace-insensitive
word match. Any still unmatched are listed in the report and nothing is silently dropped.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pymupdf

DEFAULT_COLORS = {
    "define": "#9FE1CB",   # green: definition / assumption
    "key": "#FAC775",      # yellow: key idea / result
    "derive": "#F09595",   # red box: equation to derive and implement
    "pitfall": "#F5C4B3",  # orange: where it fails
    "link": "#B5D4F4",     # blue: link to your robots / other lessons
    "section": "#D3D1C7",  # gray: section-level reading note
}

KIND_LABEL = {
    "define": "DEFINE", "key": "KEY", "derive": "DERIVE",
    "pitfall": "PITFALL", "link": "LINK", "section": "SECTION",
}


def hex_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def norm(s: str) -> str:
    s = s.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("-\n", "").replace("\n", " ")
    return re.sub(r"\s+", " ", s).strip().lower()


def fuzzy_quads(page: pymupdf.Page, anchor: str):
    """Fallback: match the anchor as a character run over the page's words, ignoring whitespace,
    end-of-line hyphenation, ligatures and the small-caps margin keywords the book prints."""
    words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,wordno
    target = norm(anchor).replace(" ", "")
    # reading order; drop all-caps margin keywords (they interrupt sentences in this book)
    words = sorted(words, key=lambda w: (w[5], w[6], w[7]))
    keep = [w for w in words if not (w[4].isupper() and len(w[4]) > 2)]
    chars, owner = [], []
    for idx, w in enumerate(keep):
        tok = norm(w[4])
        if tok.endswith("-"):
            tok = tok[:-1]
        for ch in tok:
            chars.append(ch)
            owner.append(idx)
    text = "".join(chars)
    pos = text.find(target)
    if pos < 0:
        return None
    hit = sorted(set(owner[pos:pos + len(target)]))
    lines: dict[tuple, pymupdf.Rect] = {}
    for j in hit:
        w = keep[j]
        key = (w[5], w[6])
        r = pymupdf.Rect(*w[:4])
        lines[key] = lines[key] | r if key in lines else r
    return [r.quad for r in lines.values()]


# PyMuPDF's default search flags include TEXT_DEHYPHENATE, which on some two-column pages
# (FAST-LIO2 arXiv pp. 6, 10) returns hit rectangles shifted by a line. Search without it;
# anchors that straddle a hyphenated line break fall through to fuzzy_quads.
SEARCH_FLAGS = pymupdf.TEXTFLAGS_SEARCH & ~pymupdf.TEXT_DEHYPHENATE


def search(page: pymupdf.Page, text: str, **kw):
    return page.search_for(text, textpage=page.get_textpage(flags=SEARCH_FLAGS), **kw)


def _lines(page: pymupdf.Page):
    out = []
    for b in page.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            out.append((pymupdf.Rect(ln["bbox"]), ln["spans"]))
    return out


def _two_column(page: pymupdf.Page, lines) -> bool:
    mid = page.rect.width / 2
    wide = [r for r, _ in lines if r.width > 40]
    return bool(wide) and sum(r.x0 < mid - 10 and r.x1 > mid + 10 for r in wide) < 0.1 * len(wide)


def equation_rect_columns(page: pymupdf.Page, label: str):
    """Two-column pages: box the display lines (math-font lines) next to a standalone label,
    clipped to the label's column."""
    lines = _lines(page)
    if not _two_column(page, lines):
        return None
    labs = [r for r, sp in lines if "".join(s["text"] for s in sp).strip() == label]
    if not labs:
        return None
    lab = labs[0]
    count: dict[str, int] = {}
    for _, sp in lines:
        for s in sp:
            count[s["font"]] = count.get(s["font"], 0) + len(s["text"].strip())
    family = max(count, key=count.get).split("-")[0]
    mid = page.rect.width / 2
    left = lab.x1 < mid

    def is_math(sp) -> bool:
        tot = sum(len(s["text"].strip()) for s in sp)
        prose = sum(len(s["text"].strip()) for s in sp if s["font"].startswith(family))
        return tot > 0 and prose < 0.5 * tot

    incol = [(r, sp) for r, sp in lines if (r.x1 < mid + 5 if left else r.x0 > mid - 5)]

    # Group line fragments into visual rows (math splits one printed row into many fragments).
    rows: list[list] = []
    for r, sp in sorted(incol, key=lambda t: t[0].y0):
        cy = (r.y0 + r.y1) / 2
        for row in rows:
            if abs(cy - row[0]) < 3:
                row[1] |= r
                row[2].extend(sp)
                break
        else:
            rows.append([cy, pymupdf.Rect(r), list(sp)])

    # A display row is mostly math and carries no prose word; prose rows with inline math
    # ("where x = ...", "let H = ...") always have one.
    def has_prose_word(sp) -> bool:
        return any(s["font"].startswith(family) and re.search(r"[A-Za-z]{3,}", s["text"])
                   for s in sp)

    seed = [rect for _, rect, _ in rows if rect.intersects(lab)]
    cand = [rect for _, rect, sp in rows
            if is_math(sp) and not has_prose_word(sp) and rect not in seed]
    region = pymupdf.Rect(lab)
    for r in seed:
        region |= r
    used = list(seed)
    grew = True
    while grew:
        grew = False
        for r in cand:
            if r in used:
                continue
            if r.y1 >= region.y0 - 4 and r.y0 <= region.y1 + 4:
                region |= r
                used.append(r)
                grew = True
    return region + (-3, -2, 3, 2)


def equation_rect(page: pymupdf.Page, number: str):
    """Rect around the text block that carries the equation label (3.4)."""
    label = f"({number})"
    col = equation_rect_columns(page, label)
    if col is not None:
        return col
    hits = search(page, label)
    if not hits:
        return None
    lab = hits[0]
    best = None
    for b in page.get_text("blocks"):
        r = pymupdf.Rect(*b[:4])
        if r.intersects(lab):
            best = r if best is None else best | r
    if best is None:
        return None
    # extend to the right margin of the text column so the whole equation is boxed
    best.x1 = max(best.x1, page.rect.width - 60)
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("highlights")
    ap.add_argument("out")
    ap.add_argument("--first", type=int, help="first pdf page to keep (1-based)")
    ap.add_argument("--last", type=int, help="last pdf page to keep (1-based)")
    args = ap.parse_args()

    spec = json.loads(Path(args.highlights).read_text(encoding="utf-8"))
    colors = {**DEFAULT_COLORS, **spec.get("colors", {})}
    off = spec.get("page_offset", 0)
    doc = pymupdf.open(args.pdf)
    report = {"matched": 0, "fuzzy": 0, "equations": 0, "unmatched": []}

    for it in spec["items"]:
        pno = it["page"] + off - 1
        page = doc[pno]
        kind = it.get("kind", "key")
        rgb = hex_rgb(colors[kind])
        title = KIND_LABEL.get(kind, kind.upper())
        note = it.get("note", "")

        if "equation" in it:
            r = equation_rect(page, it["equation"])
            if r is None:
                report["unmatched"].append({**it, "reason": "equation label not found"})
                continue
            a = page.add_rect_annot(r)
            a.set_colors(stroke=rgb)
            a.set_border(width=1.2)
            a.set_info(title=title, content=f"Eq. ({it['equation']}): {note}")
            a.update()
            report["equations"] += 1
            continue

        if kind == "section":
            hits = search(page, it["anchor"]) or page.search_for(it["anchor"])
            if not hits:
                report["unmatched"].append({**it, "reason": "section heading not found"})
                continue
            r = hits[0]
            a = page.add_text_annot(pymupdf.Point(r.x0 - 22, r.y0), f"{title}: {note}", icon="Note")
            a.set_colors(stroke=rgb)
            a.update()
            report["matched"] += 1
            continue

        quads = search(page, it["anchor"], quads=True)
        how = "matched"
        if not quads:
            quads = fuzzy_quads(page, it["anchor"])
            how = "fuzzy"
        if not quads:
            # last resort: PyMuPDF's dehyphenating search (rectangles can be off on some pages)
            quads = page.search_for(it["anchor"], quads=True)
            how = "fuzzy"
        if not quads:
            report["unmatched"].append({**it, "reason": "anchor not found"})
            continue
        a = page.add_highlight_annot(quads)
        a.set_colors(stroke=rgb)
        a.set_info(title=title, content=note)
        a.update()
        report[how] += 1

    if args.first or args.last:
        first = (args.first or 1) - 1
        last = (args.last or doc.page_count) - 1
        doc.select(list(range(first, last + 1)))
    doc.save(args.out, garbage=3, deflate=True)

    print(json.dumps({k: v for k, v in report.items() if k != "unmatched"}))
    for u in report["unmatched"]:
        print("UNMATCHED", json.dumps(u, ensure_ascii=False))
    return 1 if report["unmatched"] else 0


if __name__ == "__main__":
    sys.exit(main())
