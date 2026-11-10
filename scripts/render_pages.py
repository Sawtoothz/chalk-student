#!/usr/bin/env python3
"""Render an annotated chapter PDF to pNN.jpg files (NN = printed page) for build_viewer.py.

    render_pages.py annotated.pdf OUT_DIR [--first-printed 39] [--dpi 96] [--quality 72]

Without --first-printed, the first printed page comes from highlights.json next to the PDF, else from the page header.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pymupdf


def first_printed(doc) -> int:
    for p in range(min(3, doc.page_count)):
        lines = [ln.strip() for ln in doc[p].get_text().splitlines() if ln.strip()]
        for cand in lines[:3] + lines[-3:]:
            if cand.isdigit():
                return int(cand) - p
    raise SystemExit("could not read a printed page number; pass --first-printed")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("out")
    ap.add_argument("--first-printed", type=int)
    ap.add_argument("--dpi", type=int, default=96)
    ap.add_argument("--quality", type=int, default=72)
    a = ap.parse_args()
    doc = pymupdf.open(a.pdf)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fp = a.first_printed
    if fp is None:
        hj = Path(a.pdf).parent / "highlights.json"
        if hj.exists():
            import json
            fp = json.loads(hj.read_text(encoding="utf-8")).get("printed_pages", [None])[0]
    if fp is None:
        fp = first_printed(doc)
    total = 0
    for i, pg in enumerate(doc):
        f = out / f"p{fp + i:02d}.jpg"
        pg.get_pixmap(dpi=a.dpi, annots=True).save(str(f), jpg_quality=a.quality)
        total += f.stat().st_size
    print(f"{doc.page_count} pages -> {out} ({total / 1e6:.2f} MB), printed {fp}..{fp + doc.page_count - 1}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
