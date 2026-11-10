#!/usr/bin/env python3
"""Check a package's slide decks (the `slides` stage).

    check_slides.py packages/thrun-pr/ch05-robot-motion

Checks, for each of slides/class.yaml and slides/review.yaml:
  - the spec parses; every slide has a known layout, a title, and a `source` naming the package file it came from;
  - deck length: chapter 20-30 slides, paper 12-18;
  - every figure exists; every equation renders with matplotlib mathtext;
  - class decks: every content slide has speaker notes;
  - variety: a class deck uses at least 4 slides from the diagram layouts (agenda, steps, compare, stats, key,
    predict) and at most 40% plain bullet slides; a review deck at least 2; no run of 3 plain bullet slides;
  - each diagram layout has its fields (steps 2-5, columns 2-3, stats 2-4, choices <= 4, a statement, a question);
  - every decimal number in slide text, tables and notes appears in the package's reviewed text
    (lecture, cards, map, implementation plan, README, REVIEW, figures/*.json) -- numbers come from runs, not memory;
  - no line of code on a slide is copied from exercises/solutions/ unless the cards show it too;
  - the .pdf exists, is newer than the spec, has one page per slide, and is a marked study copy: every page has the
    visible "Created by Chalk" marks and the invisible notice to AI assistants, the metadata names Chalk, and no
    .pptx sits next to it (student edition);
  - nothing in the rendered PDF runs past the content area or off the slide (titles into the body, bullets into
    the footer).
Exit code 0 = ship, 1 = fix first.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_slides import LAYOUTS, NOTICE, STAMP, VISUAL, render_equation  # noqa: E402

RANGE = {"chapter": (20, 30), "paper": (12, 18)}
CORPUS = ["lecture.md", "translate.md", "map.md", "implementation.md", "README.md", "REVIEW.md"]
NUM = re.compile(r"(?<![\w.])-?\d+\.\d+(?![\w.])")
PT = 72  # PDF points per inch; make_slides lays out a 13.333 x 7.5 in slide
CONTENT_BOTTOM = (7.5 - 0.75) * PT + 6   # make_slides BOTTOM, plus a little slack for descenders
TITLE_BOTTOM = 1.45 * PT + 4             # make_slides TOP


NEEDS = {"agenda": ("items", 2, 7), "steps": ("steps", 2, 5), "compare": ("columns", 2, 3), "stats": ("stats", 2, 4),
         "predict": ("choices", 0, 4)}
MIN_VISUAL = {"class": 4, "review": 2}


def _bullet_text(bullets):
    out = []
    for b in bullets or []:
        if isinstance(b, dict):
            out.append(str(b.get("text", ""))); out += [str(x) for x in b.get("sub", [])]
        else:
            out.append(str(b))
    return out


def slide_text(s: dict) -> str:
    parts = [str(s.get(k, "")) for k in ("title", "subtitle", "meta", "caption", "notes", "takeaway", "statement",
                                          "detail", "question")]
    parts += _bullet_text(s.get("bullets"))
    parts += [str(x) for x in s.get("items") or []] + [str(x) for x in s.get("choices") or []]
    for st in s.get("steps") or []:
        parts += [str(st.get("title", "")), str(st.get("text", ""))]
    for c in s.get("columns") or []:
        parts.append(str(c.get("heading", ""))); parts += _bullet_text(c.get("bullets"))
    for st in s.get("stats") or []:
        parts += [str(st.get("value", "")), str(st.get("label", ""))]
    for wv in s.get("where") or []:
        parts += [str(x) for x in (wv if isinstance(wv, (list, tuple)) else wv.values())]
    t = s.get("table")
    if t:
        parts += [str(c) for row in [t.get("header", [])] + t.get("rows", []) for c in row]
    return "\n".join(parts)


def main(pkg: Path) -> int:
    ok = True

    def fail(msg):
        nonlocal ok
        ok = False
        print("FAIL", msg)

    kind = "paper" if pkg.name == "paper" else "chapter"
    lo, hi = RANGE[kind]
    corpus = "\n".join((pkg / f).read_text(encoding="utf-8") for f in CORPUS if (pkg / f).exists())
    corpus += "\n".join(f.read_text(encoding="utf-8") for f in (pkg / "figures").glob("*.json")) if (pkg / "figures").exists() else ""
    known_nums = set(NUM.findall(corpus))
    cards = (pkg / "translate.md").read_text(encoding="utf-8") if (pkg / "translate.md").exists() else ""
    card_lines = {ln.strip() for ln in cards.splitlines()}
    sol_lines = set()
    for f in (pkg / "exercises" / "solutions").glob("*") if (pkg / "exercises" / "solutions").exists() else []:
        if f.is_file() and f.suffix in (".py", ".md"):
            sol_lines |= {ln.strip() for ln in f.read_text(encoding="utf-8").splitlines() if len(ln.strip()) >= 25}

    for style in ("class", "review"):
        sp = pkg / "slides" / f"{style}.yaml"
        if not sp.exists():
            fail(f"missing slides/{style}.yaml"); continue
        try:
            spec = yaml.safe_load(sp.read_text(encoding="utf-8"))
            slides = spec["slides"]
        except Exception as e:
            fail(f"slides/{style}.yaml does not parse: {e}"); continue
        n = len(slides)
        if not lo <= n <= hi:
            fail(f"{style}: {n} slides, expected {lo}-{hi} for a {kind}")
        lays = [s.get("layout", "bullets") for s in slides]
        nvis = sum(l in VISUAL for l in lays)
        if nvis < MIN_VISUAL[style]:
            fail(f"{style}: {nvis} diagram slides (agenda/steps/compare/stats/key/predict), want at least {MIN_VISUAL[style]}")
        if style == "class" and lays.count("bullets") > 0.4 * n:
            fail(f"{style}: {lays.count('bullets')} of {n} slides are plain bullets, want at most 40%")
        for i in range(len(lays) - 2):
            if lays[i:i + 3] == ["bullets"] * 3:
                fail(f"{style} slides {i + 1}-{i + 3}: three plain bullet slides in a row; make one a diagram")
                break
        for i, s in enumerate(slides, 1):
            tag = f"{style} slide {i}"
            lay = s.get("layout", "bullets")
            if lay not in LAYOUTS:
                fail(f"{tag}: unknown layout {lay!r}")
            if not str(s.get("title", "")).strip():
                fail(f"{tag}: no title")
            if not str(s.get("source", "")).strip():
                fail(f"{tag}: no source (which package file is this slide from?)")
            if style == "class" and lay not in ("title", "section") and not str(s.get("notes", "")).strip():
                fail(f"{tag}: class slide without speaker notes")
            if lay in NEEDS:
                key, a, b = NEEDS[lay]
                k = len(s.get(key) or [])
                if not a <= k <= b:
                    fail(f"{tag}: {lay} needs {a}-{b} {key}, has {k}")
            if lay == "key" and not str(s.get("statement", "")).strip():
                fail(f"{tag}: key slide without a statement")
            if lay == "predict" and not str(s.get("question", "")).strip():
                fail(f"{tag}: predict slide without a question")
            if lay == "figure":
                f = pkg / str(s.get("figure", ""))
                if not s.get("figure") or not f.is_file():
                    fail(f"{tag}: figure {s.get('figure')!r} not found")
            for e in s.get("equations") or []:
                tex = e["tex"] if isinstance(e, dict) else e
                try:
                    render_equation(tex, pkg / "slides" / ".eq")
                except ValueError as err:
                    fail(f"{tag}: {err}")
            for num in set(NUM.findall(slide_text(s))):
                if num not in known_nums and num.lstrip("-") not in known_nums:
                    fail(f"{tag}: number {num} does not appear in the package's reviewed text")
            for ln in str(s.get("code", "")).splitlines():
                t = ln.strip()
                if len(t) >= 25 and t in sol_lines and t not in card_lines:
                    fail(f"{tag}: code line copied from exercises/solutions/: {t[:60]}")
        pdf = sp.with_suffix(".pdf")
        if sp.with_suffix(".pptx").exists():
            fail(f"slides/{style}.pptx exists; the student edition ships PDF only (run just slides)")
        if not pdf.exists() or pdf.stat().st_mtime < sp.stat().st_mtime:
            fail(f"slides/{style}.pdf missing or older than the spec (run just slides)"); continue
        doc = pymupdf.open(pdf)
        if "Chalk" not in (doc.metadata or {}).get("creator", ""):
            fail(f"{style}: PDF metadata does not name Chalk (not stamped; run just slides)")
        for i, page in enumerate(doc, 1):
            t = " ".join(page.get_text().split())
            if STAMP not in t or "CREATED BY CHALK" not in t or NOTICE[:80] not in t:
                fail(f"{style} slide {i}: watermark or AI notice missing (run just slides)")
                break
        if doc.page_count != n:
            fail(f"{style}: PDF has {doc.page_count} pages for {n} slides")
        foot = str(spec.get("footer", spec.get("title", "")))
        for i, page in enumerate(doc, 1):
            W, Hh = page.rect.width, page.rect.height
            seen = set()
            for b in page.get_text("dict")["blocks"]:
                for line in b.get("lines", []):
                    txt = "".join(sp_["text"] for sp_ in line["spans"]).strip()
                    if not txt:
                        continue
                    x0, y0, x1, y1 = line["bbox"]
                    if line["dir"][1] != 0 or txt == STAMP or all(sp_["size"] < 5 for sp_ in line["spans"]):
                        continue   # the study-copy marks: diagonal watermark, corner line, invisible notice
                    if txt == foot or txt.isdigit() and y0 > CONTENT_BOTTOM - 6:
                        continue   # footer and slide number
                    if (x1 > W + 1 or y1 > Hh + 1) and "off" not in seen:
                        seen.add("off"); fail(f"{style} slide {i}: text off the slide: {txt[:50]!r}")
                    elif y1 > CONTENT_BOTTOM and i > 1 and "foot" not in seen:
                        seen.add("foot"); fail(f"{style} slide {i}: text runs into the footer (cut bullets or split the slide): {txt[:50]!r}")
            lay = slides[i - 1].get("layout", "bullets") if i <= n else ""
            if lay not in ("title", "section"):
                # the title is the text that starts at the top of the slide; its size marks its continuation lines
                lines = [l for b in page.get_text("dict")["blocks"] for l in b.get("lines", []) if l["spans"]]
                top = [l for l in lines if l["bbox"][1] < 0.6 * PT]
                tsize = max((sp_["size"] for l in top for sp_ in l["spans"]), default=0)
                ttxt = " ".join(str(slides[i - 1].get("title", "")).split())
                for l in lines:
                    txt = "".join(sp_["text"] for sp_ in l["spans"]).strip()
                    if (txt and txt in ttxt and any(abs(sp_["size"] - tsize) < 0.5 for sp_ in l["spans"])
                            and l["bbox"][3] > TITLE_BOTTOM):
                        fail(f"{style} slide {i}: title runs into the content area (shorten it)")
                        break
        print(f"checked {style}: {n} slides")
    print("VERDICT:", "ship" if ok else "fix first")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]).resolve()))
