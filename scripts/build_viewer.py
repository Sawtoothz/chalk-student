#!/usr/bin/env python3
"""Build a single-page HTML viewer for a package: annotated pages with their notes, chapter map, lecture with
figures, equation-to-code cards, interactive session, exercises, review record — and for papers the
implementation plan and the code anchors, and the slide decks (slides/class.pdf, slides/review.pdf, rendered to images
here; the stamped study-copy PDF is linked for download). Every part is optional: tabs for files that do not exist yet are hidden,
so the Reader can be built after any stage.

    build_viewer.py PACKAGE_DIR PAGES_DIR OUT.html
PAGES_DIR holds pNN.jpg renders of the annotated PDF (NN = printed page); it may be missing before the highlight stage.
"""

from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

import markdown
import pymupdf

pkg = Path(sys.argv[1]); pages = Path(sys.argv[2]); out = Path(sys.argv[3])
_ann = sorted(pkg.glob("annotated*.pdf"))
HAVE_PAGES = (pkg / "highlights.json").exists() and bool(_ann) and pages.exists()
spec = json.loads((pkg / "highlights.json").read_text(encoding="utf-8")) if HAVE_PAGES else {"printed_pages": [0, 0], "items": []}
lo, hi = spec["printed_pages"]
doc = pymupdf.open(_ann[0]) if HAVE_PAGES else None
meta = {}
mm_ = re.search(r"^---\n(.*?)\n---", (pkg / "map.md").read_text(encoding="utf-8"), re.S)
if mm_:
    for line in mm_.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
TITLE = meta.get("title", pkg.name)
BOOK = meta.get("book", meta.get("source", ""))
LESSON = meta.get("lesson", "")
CHAPTER = meta.get("chapter", "")


def norm(t):
    return re.sub(r"\s+", " ", t.replace("\ufb01", "fi").replace("\ufb02", "fl").replace("-\n", "")).strip().lower()


def ypos(pp, it):
    """Vertical position of a highlight on its page, for reading-order sorting."""
    page = doc[pp - lo]
    if "equation" in it:
        hits = page.search_for(f"({it['equation']})")
        return hits[0].y0 if hits else 1e9
    a = it.get("anchor", "")
    hits = page.search_for(a)
    if hits:
        return hits[0].y0
    words = page.get_text("words")
    tgt = norm(a).replace(" ", "")[:24]
    run = ""
    starts = []
    for w in sorted(words, key=lambda w: (w[5], w[6], w[7])):
        tok = norm(w[4]).rstrip("-")
        starts.append((len(run), w[1]))
        run += tok
    k = run.find(tgt)
    if k < 0:
        return 1e9 - 1
    y = [yy for (st, yy) in starts if st <= k][-1]
    return y

# ---- page images + notes
page_data = []
by_page: dict[int, list] = {}
for it in spec["items"]:
    by_page.setdefault(it["page"], []).append(it)
for pp in (range(lo, hi + 1) if HAVE_PAGES else []):
    img = pages / f"p{pp:02d}.jpg"
    if not img.exists():
        continue
    b64 = base64.b64encode(img.read_bytes()).decode("ascii")
    notes = []
    for it in sorted(by_page.get(pp, []), key=lambda it: (0 if it["kind"] == "section" else 1, ypos(pp, it))):
        notes.append({"kind": it["kind"], "anchor": it.get("anchor", ""), "eq": it.get("equation", ""), "note": it["note"]})
    page_data.append({"p": pp, "img": "data:image/jpeg;base64," + b64, "notes": notes})

# ---- slide decks: slides/<style>.pdf -> embedded JPEGs; notes and titles from slides/<style>.yaml
def _slides() -> dict:
    import yaml
    decks = {}
    for style in ("class", "review"):
        pdf, spec_f = pkg / "slides" / f"{style}.pdf", pkg / "slides" / f"{style}.yaml"
        if not pdf.exists() or not spec_f.exists():
            continue
        spec_s = yaml.safe_load(spec_f.read_text(encoding="utf-8")) or {}
        items = spec_s.get("slides", [])
        d = pymupdf.open(pdf)
        out = []
        for i, page in enumerate(d):
            pix = page.get_pixmap(dpi=96)   # 1280 x 720
            jpg = pix.tobytes("jpeg", jpg_quality=80)
            sl = items[i] if i < len(items) else {}
            out.append({"img": "data:image/jpeg;base64," + base64.b64encode(jpg).decode("ascii"),
                        "title": str(sl.get("title", "")), "notes": str(sl.get("notes", "")).strip(),
                        "source": str(sl.get("source", ""))})
        decks[style] = {"slides": out, "pdf": f"slides/{style}.pdf",
                        "title": str(spec_s.get("title", ""))}
    return decks

SLIDES = _slides()

# ---- markdown docs, with figures inlined
def load_md(name: str) -> str:
    if not (pkg / name).exists():
        return ""
    s = (pkg / name).read_text(encoding="utf-8")
    s = re.sub(r"^---\n.*?\n---\n", "", s, count=1, flags=re.S)  # strip front matter
    def fig(m):
        rel = m.group(1)
        f = pkg / rel
        if f.suffix == ".svg" and f.exists():
            svg = f.read_text(encoding="utf-8")
            svg = svg[svg.find("<svg"):]
            return f'<figure class="lfig">{svg}</figure>'
        return m.group(0)
    return re.sub(r"!\[[^\]]*\]\(([^)]+)\)", fig, s)

def render(md: str) -> str:
    md = re.sub(r"```latex\n([\s\S]*?)```", lambda m: '\n<div class="math-block">$$' + m.group(1).strip() + '$$</div>\n', md)
    return markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])


def _opt(rel: str, wrap: str | None = None) -> str:
    f = pkg / rel
    if not f.exists():
        return ""
    t = f.read_text(encoding="utf-8")
    return wrap.replace("__BODY__", t) if wrap else t

def _code_refs() -> str:
    f = pkg / "code_refs.json"
    if not f.exists():
        return ""
    import html as _h
    refs = json.loads(f.read_text(encoding="utf-8"))
    rows = ["<p>Every file:line cited in the cards, as produced by <code>scripts/code_refs.py</code>. Links open the pinned commit.</p>",
            "<table><tr><th>symbol</th><th>location</th><th>line</th></tr>"]
    for r in refs.get("repos", []):
        rows.append(f"<tr><td colspan=3><b>{_h.escape(r['repo'])}</b> @ {r['commit'][:12]} — {_h.escape(r.get('licence',''))}</td></tr>")
        for sym, hits in r.get("symbols", {}).items():
            for h in hits[:4]:
                rows.append(f"<tr><td><code>{_h.escape(sym)}</code></td><td><a href='{h['url']}'>{_h.escape(h['path'])}:{h['line']}</a></td><td><code>{_h.escape(h['text'][:90])}</code></td></tr>")
    rows.append("</table>")
    return "\n".join(rows)

_ex = [_opt("exercises/README.md"), _opt("exercises/T1_concept.md"), _opt("exercises/T2_derivation.md"),
       _opt("exercises/exercise.py", "# T3 — Implementation stubs\n\n```python\n__BODY__\n```"),
       _opt("exercises/T4_debug/broken_ekf.py", "# T4 — Debug\n\n```python\n__BODY__\n```"),
       _opt("exercises/T5_robot.md"), _opt("exercises/clues.md")]
docs_md = {
    "map": load_md("map.md"),
    "lecture": load_md("lecture.md"),
    "cards": load_md("translate.md"),
    "implementation": load_md("implementation.md"),
    "exercises": "\n\n---\n\n".join(x for x in _ex if x),
    "review": _opt("REVIEW.md"),
}
docs = {k: (render(v) if v else "") for k, v in docs_md.items()}
docs["refs"] = _code_refs()
docs["about"] = render(_opt("README.md"))
HAVE = {k: bool(v) for k, v in docs.items()}
HAVE["reader"] = HAVE_PAGES and bool(page_data)
HAVE["session"] = (pkg / "interactive.html").exists() or (pkg / "session.py").exists()
HAVE["slides"] = bool(SLIDES)

def _interactive() -> str:
    """The package's own interactive.html, else a pointer to the marimo session."""
    f = pkg / "interactive.html"
    if f.exists():
        t = f.read_text(encoding="utf-8")
        if t.lstrip().lower().startswith("<!doctype"):   # a full document: sandbox it in a frame
            import html as _h
            return f'<iframe class="ixframe" title="Interactive session" srcdoc="{_h.escape(t, quote=True)}"></iframe>'
        return t
    return ('<div class="doc"><p>This chapter\'s interactive session is the marimo notebook '
            '<code>session.py</code>. Run <code>just session</code> to open it. A browser version '
            '(<code>interactive.html</code> in the package) has not been built for this chapter yet.</p></div>')


counts = {}
for it in spec["items"]:
    counts[it["kind"]] = counts.get(it["kind"], 0) + 1

html = r"""<title>__TITLE__ · Chalk</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: a reading desk. Left, the annotated page; right, the margin notes. Other tabs are long-form text at 68ch. */
:root{
  --paper:#f7f5ef; --sheet:#fffdf8; --ink:#1f1e1d; --ink2:#5b5952; --ink3:#8a877d; --rule:#dedbd1; --accent:#1d9e75; --accent-ink:#0b5c43;
  --define:#9fe1cb; --key:#fac775; --derive:#f09595; --pitfall:#f5c4b3; --link:#b5d4f4; --section:#d3d1c7;
  --code-bg:#f0ede4;
  --serif:"Source Serif 4",Georgia,"Times New Roman",serif; --sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif; --mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#1c1c1a;--sheet:#262624;--ink:#f1efe8;--ink2:#b8b5aa;--ink3:#86837a;--rule:#3b3a36;--accent:#3ec294;--accent-ink:#bdf0da;--define:#2f6b55;--key:#7a5518;--derive:#7a2f2f;--pitfall:#6b3a28;--link:#2c4f78;--section:#4a4944;--code-bg:#1f1f1d;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#1c1c1a;--sheet:#262624;--ink:#f1efe8;--ink2:#b8b5aa;--ink3:#86837a;--rule:#3b3a36;--accent:#3ec294;--accent-ink:#bdf0da;--define:#2f6b55;--key:#7a5518;--derive:#7a2f2f;--pitfall:#6b3a28;--link:#2c4f78;--section:#4a4944;--code-bg:#1f1f1d;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55}
header{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--paper);border-bottom:1px solid var(--rule);padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:10;background:var(--paper)}
.hd{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 18px;padding-block:12px 0;max-width:1240px;margin:0 auto}
.hd h1{font:600 18px/1.2 var(--sans);margin:0}
.hd .sub{font-family:var(--mono);font-size:12px;color:var(--ink3);letter-spacing:.02em}
nav{display:flex;gap:2px;overflow-x:auto;max-width:1240px;margin:0 auto}
nav button{appearance:none;border:0;background:none;font:500 13.5px var(--sans);color:var(--ink2);padding:10px 12px;border-bottom:2px solid transparent;cursor:pointer;white-space:nowrap}
nav button[aria-selected="true"]{color:var(--ink);border-bottom-color:var(--accent)}
nav button:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
main{padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:18px 48px;max-width:1240px;margin:0 auto}
.panel[hidden]{display:none}
/* reader */
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:12.5px;color:var(--ink2);margin-bottom:12px}
.legend span{display:inline-flex;align-items:center;gap:6px}
.sw{width:14px;height:10px;border-radius:2px;display:inline-block}
.reader{display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:20px;align-items:start}
.pagebox{background:var(--sheet);border:1px solid var(--rule);border-radius:4px;padding:8px}
.pagebox img{display:block;width:100%;height:auto;border-radius:2px}
.pnav{display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap}
.pnav button{font:500 13px var(--sans);border:1px solid var(--rule);background:var(--sheet);color:var(--ink);border-radius:6px;padding:6px 10px;cursor:pointer}
.pnav button:disabled{opacity:.4;cursor:default}
.pnav .pno{font-family:var(--mono);font-size:13px;color:var(--ink2);min-width:140px}
.pnav select{font:13px var(--sans);border:1px solid var(--rule);background:var(--sheet);color:var(--ink);border-radius:6px;padding:5px 8px}
.notes{display:flex;flex-direction:column;gap:8px}
.notes h2{font:600 13px var(--sans);color:var(--ink3);text-transform:uppercase;letter-spacing:.08em;margin:4px 0 2px}
.note{border-left:4px solid var(--section);background:var(--sheet);border-radius:0 6px 6px 0;padding:8px 12px}
.note .k{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3)}
.note .a{font-family:var(--serif);font-size:14px;color:var(--ink2);font-style:italic;margin:2px 0 4px}
.note .n{font-size:13.5px;line-height:1.5}
.note[data-kind="define"]{border-color:var(--define)} .note[data-kind="key"]{border-color:var(--key)} .note[data-kind="derive"]{border-color:var(--derive)}
.note[data-kind="pitfall"]{border-color:var(--pitfall)} .note[data-kind="link"]{border-color:var(--link)} .note[data-kind="section"]{border-color:var(--section)}
.note .n b{font-weight:600}
.empty{color:var(--ink3);font-size:13px}
/* long-form */
.doc{max-width:72ch;font-family:var(--serif);font-size:16.5px;line-height:1.62}
.doc h1{font:600 26px/1.2 var(--sans);text-wrap:balance;margin:0 0 .6em}
.doc h2{font:600 20px/1.25 var(--sans);text-wrap:balance;margin:1.8em 0 .5em;padding-top:.6em;border-top:1px solid var(--rule)}
.doc h3{font:600 16px/1.3 var(--sans);margin:1.4em 0 .4em}
.doc p{margin:0 0 .9em}
.doc ul,.doc ol{padding-left:1.3em;margin:0 0 .9em}
.doc li{margin:.2em 0}
.doc code{font-family:var(--mono);font-size:.86em;background:var(--code-bg);padding:1px 5px;border-radius:4px}
.doc pre{font-family:var(--mono);font-size:12.5px;line-height:1.5;background:var(--code-bg);border:1px solid var(--rule);border-radius:6px;padding:12px 14px;overflow-x:auto;margin:0 0 1em}
.doc pre code{background:none;padding:0;font-size:inherit}
.doc table{border-collapse:collapse;font-family:var(--sans);font-size:13.5px;margin:0 0 1.1em;display:block;overflow-x:auto;max-width:100%}
.doc th,.doc td{border-bottom:1px solid var(--rule);padding:6px 10px;text-align:left;vertical-align:top}
.doc th{font-weight:600;color:var(--ink2);white-space:nowrap}
.doc blockquote{border-left:3px solid var(--accent);margin:0 0 1em;padding:2px 14px;color:var(--ink2)}
.doc hr{border:0;border-top:1px solid var(--rule);margin:2em 0}
.doc strong{font-weight:600}
.doc .lfig{margin:1.2em 0;background:#fff;border:1px solid var(--rule);border-radius:6px;padding:6px}
.doc .lfig svg{display:block;width:100%;height:auto}
.doc mjx-container[display="true"]{overflow-x:auto;overflow-y:hidden;margin:.6em 0 1em}
.doc .math-block{margin:.4em 0 1em;font-size:1.05em}
.stats{display:flex;flex-wrap:wrap;gap:8px 18px;font-family:var(--mono);font-size:12.5px;color:var(--ink2);margin:0 0 14px}
.ixframe{width:100%;height:1500px;border:0;border-radius:8px;background:transparent}
/* slides */
.sbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px}
.seg{display:inline-flex;border:1px solid var(--rule);border-radius:7px;overflow:hidden}
.seg button{appearance:none;border:0;background:var(--sheet);color:var(--ink2);font:500 13px var(--sans);padding:6px 12px;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--accent);color:#fff}
.sbar .btn{font:500 13px var(--sans);border:1px solid var(--rule);background:var(--sheet);color:var(--ink);border-radius:6px;padding:6px 10px;cursor:pointer;text-decoration:none}
.sbar .btn:disabled{opacity:.4;cursor:default}
.sbar .sno{font-family:var(--mono);font-size:13px;color:var(--ink2);min-width:84px;text-align:center}
.sbar .grow{flex:1}
.stage{background:#fff;border:1px solid var(--rule);border-radius:6px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06);max-width:max(560px,calc((100vh - 330px) * 16 / 9));margin:0 auto}
.snotes,.thumbs{max-width:max(560px,calc((100vh - 330px) * 16 / 9));margin-left:auto;margin-right:auto}
.stage img{display:block;width:100%;height:auto;aspect-ratio:16/9;cursor:pointer}
.stage:fullscreen{display:flex;align-items:center;justify-content:center;background:#000;border:0;border-radius:0}
.stage:fullscreen img{width:auto;max-width:100vw;max-height:100vh;object-fit:contain}
.snotes{margin-top:12px;background:var(--sheet);border:1px solid var(--rule);border-radius:6px;padding:10px 14px;font-size:14px;line-height:1.55;white-space:pre-wrap}
.snotes .k{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3);display:block;margin-bottom:4px}
.snotes .src{display:block;margin-top:6px;font-family:var(--mono);font-size:11.5px;color:var(--ink3)}
.thumbs{display:flex;gap:8px;overflow-x:auto;padding:10px 2px 4px}
.thumbs button{flex:0 0 auto;width:128px;padding:0;border:2px solid transparent;border-radius:4px;background:none;cursor:pointer}
.thumbs button[aria-current="true"]{border-color:var(--accent)}
.thumbs img{display:block;width:100%;border-radius:2px;border:1px solid var(--rule)}
@media (max-width:820px){.reader{grid-template-columns:1fr}.doc{font-size:15.5px}}
@media (prefers-reduced-motion:no-preference){.panel{animation:fade .18s ease-out}@keyframes fade{from{opacity:.4}to{opacity:1}}}
</style>

<header>
  <div class="hd"><h1>__TITLE__</h1><span class="sub">Chalk · __BOOK__ · __UNIT__ · lesson __LESSON__</span></div>
  <nav role="tablist" id="tabs">
    <button role="tab" aria-selected="false" data-tab="about">About</button>
    <button role="tab" aria-selected="true" data-tab="reader">Annotated chapter</button>
    <button role="tab" aria-selected="false" data-tab="map">Chapter map</button>
    <button role="tab" aria-selected="false" data-tab="lecture">Lecture</button>
    <button role="tab" aria-selected="false" data-tab="cards">Equation to code</button>
    <button role="tab" aria-selected="false" data-tab="session">Interactive session</button>
    <button role="tab" aria-selected="false" data-tab="slides">Slides</button>
    <button role="tab" aria-selected="false" data-tab="implementation">Implementation</button>
    <button role="tab" aria-selected="false" data-tab="refs">Code anchors</button>
    <button role="tab" aria-selected="false" data-tab="exercises">Exercises</button>
    <button role="tab" aria-selected="false" data-tab="review">Review record</button>
  </nav>
</header>

<main>
<section class="panel" id="panel-reader">
  <div class="legend">
    <span><i class="sw" style="background:var(--define)"></i>definition / assumption</span>
    <span><i class="sw" style="background:var(--key)"></i>key idea</span>
    <span><i class="sw" style="background:var(--derive)"></i>equation to derive and implement</span>
    <span><i class="sw" style="background:var(--pitfall)"></i>where it fails</span>
    <span><i class="sw" style="background:var(--link)"></i>link to your robots / other lessons</span>
    <span><i class="sw" style="background:var(--section)"></i>section verdict</span>
  </div>
  <div class="stats" id="stats"></div>
  <div class="pnav">
    <button id="prev">‹ Prev</button>
    <span class="pno" id="pno"></span>
    <button id="next">Next ›</button>
    <label for="jump" style="font-size:13px;color:var(--ink2)">Go to</label>
    <select id="jump"></select>
  </div>
  <div class="reader">
    <div class="pagebox"><img id="pimg" alt="Annotated textbook page"></div>
    <aside class="notes" id="notes"></aside>
  </div>
</section>
<section class="panel" id="panel-map" hidden><article class="doc" id="doc-map"></article></section>
<section class="panel" id="panel-lecture" hidden><article class="doc" id="doc-lecture"></article></section>
<section class="panel" id="panel-cards" hidden><article class="doc" id="doc-cards"></article></section>
<section class="panel" id="panel-session" hidden>__INTERACTIVE__</section>
<section class="panel" id="panel-slides" hidden>
  <div class="sbar">
    <span class="seg" role="group" aria-label="Deck style"><button type="button" data-style="class" aria-pressed="true">Class</button><button type="button" data-style="review" aria-pressed="false">Review</button></span>
    <button class="btn" id="sprev" type="button">‹ Prev</button>
    <span class="sno" id="sno"></span>
    <button class="btn" id="snext" type="button">Next ›</button>
    <span class="grow"></span>
    <button class="btn" id="sfull" type="button">Full screen</button>
    <a class="btn" id="spdf" download>Download PDF</a>
  </div>
  <div class="stage" id="sstage"><img id="simg" alt=""></div>
  <div class="snotes" id="snotes"></div>
  <div class="thumbs" id="sthumbs" aria-label="All slides"></div>
</section>
<section class="panel" id="panel-implementation" hidden><article class="doc" id="doc-implementation"></article></section>
<section class="panel" id="panel-refs" hidden><article class="doc" id="doc-refs"></article></section>
<section class="panel" id="panel-about" hidden><article class="doc" id="doc-about"></article></section>
<section class="panel" id="panel-exercises" hidden><article class="doc" id="doc-exercises"></article></section>
<section class="panel" id="panel-review" hidden><article class="doc" id="doc-review"></article></section>
</main>

<script>
window.MathJax = {tex:{inlineMath:[], displayMath:[['$$','$$']]}, svg:{fontCache:'global'}, startup:{typeset:false}};
</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-svg.js"></script>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<script>
const KEY = __KEY__;
const PAGES = __PAGES__;
const DOCS = __DOCS__;
const COUNTS = __COUNTS__;
const HAVE = __HAVE__;
const SLIDES = __SLIDES__;
document.querySelectorAll('#tabs button').forEach(b => { if (!HAVE[b.dataset.tab]) b.remove(); });
const KIND = {define:"definition", key:"key idea", derive:"derive and implement", pitfall:"where it fails", link:"link", section:"section verdict"};

// --- reader
let idx = 0;
const pimg = document.getElementById('pimg'), notes = document.getElementById('notes'), pno = document.getElementById('pno'), jump = document.getElementById('jump');
PAGES.forEach((pg, i) => { const o = document.createElement('option'); o.value = i; o.textContent = `p. ${pg.p} (${pg.notes.length})`; jump.appendChild(o); });
document.getElementById('stats').textContent = Object.entries(COUNTS).map(([k, v]) => `${v} ${KIND[k] || k}`).join('  ·  ') + `  ·  ${PAGES.length} pages`;
function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;'); }
function fmtNote(n){ return esc(n).replace(/\b(WHY|ROBOT|CODE|TEST|DEFINE|SHAPES|PITFALL|FIGURE|COST|SESSION|IMPLEMENT|PRACTICAL|GEOMETRY|RESULT|READING|EXERCISE|HOW|SUMMARY|FACTOR 2|THE IDEA|THE DUALITY|KEY SUBSTITUTION|ALGORITHM WALK-THROUGH)(?= ?[0-9]*:)/g, '<b>$1</b>'); }
function show(i){
  if (!PAGES.length) return;
  idx = Math.max(0, Math.min(PAGES.length - 1, i));
  const pg = PAGES[idx];
  pimg.src = pg.img; pno.textContent = `printed page ${pg.p} · ${idx + 1} / ${PAGES.length}`; jump.value = idx;
  document.getElementById('prev').disabled = idx === 0; document.getElementById('next').disabled = idx === PAGES.length - 1;
  notes.innerHTML = `<h2>Notes on this page</h2>` + (pg.notes.length ? pg.notes.map(n =>
    `<div class="note" data-kind="${n.kind}"><div class="k">${KIND[n.kind] || n.kind}${n.eq ? ' · eq. (' + n.eq + ')' : ''}</div>` +
    (n.anchor ? `<div class="a">“${esc(n.anchor)}”</div>` : '') + `<div class="n">${fmtNote(n.note)}</div></div>`).join('') : '<div class="empty">No notes on this page.</div>');
  try { localStorage.setItem(KEY+'-page', idx); } catch (e) {}
}
document.getElementById('prev').onclick = () => show(idx - 1);
document.getElementById('next').onclick = () => show(idx + 1);
jump.onchange = e => show(+e.target.value);
document.addEventListener('keydown', e => { if (document.getElementById('panel-reader').hidden) return; if (e.key === 'ArrowLeft') show(idx - 1); if (e.key === 'ArrowRight') show(idx + 1); });
let start = 0; try { start = +(localStorage.getItem(KEY+'-page') || 0) || 0; } catch (e) {}
show(start);

// --- slides
const sState = {style: Object.keys(SLIDES)[0] || 'class', i: 0};
try { const st = JSON.parse(localStorage.getItem(KEY+'-slides') || '{}'); if (SLIDES[st.style]) { sState.style = st.style; sState.i = st.i || 0; } } catch (e) {}
function fileUrl(rel){   // works from the GUI (/reader/<src>/<unit>) and from the package folder (file://)
  return location.protocol === 'file:' ? rel : location.pathname.replace(/\/$/, '') + '/' + rel;
}
function sThumbs(){
  const deck = SLIDES[sState.style]; const box = document.getElementById('sthumbs'); box.innerHTML = '';
  deck.slides.forEach((s, i) => { const b = document.createElement('button'); b.type = 'button'; b.title = `${i + 1}. ${s.title}`;
    b.innerHTML = `<img loading="lazy" alt="Slide ${i + 1}: ${esc(s.title)}" src="${s.img}">`; b.onclick = () => sShow(i); box.appendChild(b); });
}
function sShow(i){
  const deck = SLIDES[sState.style]; if (!deck) return;
  sState.i = Math.max(0, Math.min(deck.slides.length - 1, i));
  const s = deck.slides[sState.i];
  const img = document.getElementById('simg'); img.src = s.img; img.alt = `Slide ${sState.i + 1}: ${s.title}`;
  document.getElementById('sno').textContent = `${sState.i + 1} / ${deck.slides.length}`;
  document.getElementById('sprev').disabled = sState.i === 0; document.getElementById('snext').disabled = sState.i === deck.slides.length - 1;
  document.getElementById('snotes').innerHTML = `<span class="k">Speaker notes</span>` + (s.notes ? esc(s.notes) : '<span style="color:var(--ink3)">None for this slide.</span>') + (s.source ? `<span class="src">from ${esc(s.source)}</span>` : '');
  document.querySelectorAll('#sthumbs button').forEach((b, k) => { b.setAttribute('aria-current', k === sState.i); if (k === sState.i) { const box = b.parentElement; if (b.offsetLeft < box.scrollLeft || b.offsetLeft + b.offsetWidth > box.scrollLeft + box.clientWidth) box.scrollLeft = b.offsetLeft - box.clientWidth / 2 + b.offsetWidth / 2; } });
  try { localStorage.setItem(KEY+'-slides', JSON.stringify(sState)); } catch (e) {}
}
function sStyle(style){
  if (!SLIDES[style]) return;
  if (style !== sState.style) sState.i = 0;
  sState.style = style;
  document.querySelectorAll('.seg button').forEach(b => b.setAttribute('aria-pressed', b.dataset.style === style));
  document.getElementById('spdf').href = fileUrl(SLIDES[style].pdf);
  sThumbs(); sShow(sState.i);
}
if (HAVE.slides) {
  document.querySelectorAll('.seg button').forEach(b => { if (!SLIDES[b.dataset.style]) b.disabled = true; b.onclick = () => sStyle(b.dataset.style); });
  document.getElementById('sprev').onclick = () => sShow(sState.i - 1);
  document.getElementById('snext').onclick = () => sShow(sState.i + 1);
  document.getElementById('simg').onclick = () => sShow(sState.i + 1);
  document.getElementById('sfull').onclick = () => { const st = document.getElementById('sstage'); document.fullscreenElement ? document.exitFullscreen() : st.requestFullscreen && st.requestFullscreen(); };
  document.addEventListener('keydown', e => {
    if (document.getElementById('panel-slides').hidden) return;
    if (['ArrowRight', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); sShow(sState.i + 1); }
    if (['ArrowLeft', 'PageUp'].includes(e.key)) { e.preventDefault(); sShow(sState.i - 1); }
    if (e.key === 'Home') sShow(0);
    if (e.key === 'End') sShow(1e9);
    if (e.key === 'f') document.getElementById('sfull').click();
  });
  sStyle(sState.style);
}

// --- tabs and docs
const rendered = {};
function renderDoc(name){
  if (rendered[name]) return;
  const el = document.getElementById('doc-' + name);
  el.innerHTML = DOCS[name];
  rendered[name] = true;
  if (window.MathJax && MathJax.typesetPromise) MathJax.typesetPromise([el]).catch(() => {});
}
function select(tab){
  document.querySelectorAll('#tabs button').forEach(b => b.setAttribute('aria-selected', b.dataset.tab === tab));
  document.querySelectorAll('.panel').forEach(p => p.hidden = p.id !== 'panel-' + tab);
  if (tab !== 'reader' && tab !== 'session' && tab !== 'slides') renderDoc(tab);
  if (tab === 'session' && window.__ixRedraw) setTimeout(() => window.__ixRedraw(), 0);
  try { localStorage.setItem(KEY+'-tab', tab); } catch (e) {}
  window.scrollTo(0, 0);
}
document.getElementById('tabs').addEventListener('click', e => { const b = e.target.closest('button'); if (b) select(b.dataset.tab); });
const FIRST = HAVE.reader ? 'reader' : (HAVE.cards ? 'cards' : 'map');
let tab = FIRST; try { tab = localStorage.getItem(KEY+'-tab') || FIRST; } catch (e) {}
const h = location.hash.replace('#', ''); if (HAVE[h]) tab = h;
if (!HAVE[tab]) tab = FIRST;
select(tab);
</script>
"""
UNIT = f"ch. {CHAPTER} · pp. {lo}–{hi}" if HAVE_PAGES else (f"ch. {CHAPTER}" if CHAPTER and meta.get("kind") != "paper" else "paper")
html = (html.replace("__UNIT__", UNIT)
        .replace("__PAGES__", json.dumps(page_data))
        .replace("__DOCS__", json.dumps(docs))
        .replace("__COUNTS__", json.dumps(counts)).replace("__HAVE__", json.dumps(HAVE))
        .replace("__SLIDES__", json.dumps(SLIDES))
        .replace("__TITLE__", TITLE).replace("__BOOK__", BOOK).replace("__CHAPTER__", str(CHAPTER)).replace("__LESSON__", LESSON)
        .replace("__KEY__", json.dumps(pkg.name))
        .replace("__INTERACTIVE__", _interactive()))
out.write_text(html, encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size/1e6:.2f} MB)")
