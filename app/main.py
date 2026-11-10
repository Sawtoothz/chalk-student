"""Chalk GUI — the desk side of the CLI. Three pages (Library, Run, Reader) over the same scripts `just` uses.

    just serve            # uvicorn app.main:app --port 8765
    open http://localhost:8765

Upload a PDF -> scripts/ingest.py -> entry in books.yaml. Press Teach on a unit -> a job runs
scripts/run_stage.py with the AI engine chosen on the AI page (Claude Code, Codex, Gemini CLI or a custom command;
scripts/engines.py); the Run page tails its log over SSE. One job at a time, in the repo's working directory, so stages never race each other.
Bind to localhost or a Tailscale address only; there is no authentication.
"""

from __future__ import annotations

import asyncio
import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from collections import deque
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import engines  # noqa: E402
import pages  # noqa: E402

app = FastAPI(title="Chalk")
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "app" / "templates")
PY = sys.executable

# ---------------------------------------------------------------- settings: Auto-run and the AI engine, kept across restarts
SETTINGS = engines.load_settings()
templates.env.globals["settings"] = SETTINGS
templates.env.globals["engine_label"] = lambda: engines.ENGINES[SETTINGS["engine"]]["label"]


def save_settings():
    engines.save_settings(SETTINGS)


@app.middleware("http")
async def same_origin_posts(request: Request, call_next):
    """The GUI has no login, and it stores commands it will run (the AI page), so a request that changes anything
    must come from the GUI's own pages: a cross-site form or fetch carries a foreign Origin (or Referer) and is refused."""
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        host = request.headers.get("host", "")
        origin = request.headers.get("origin") or request.headers.get("referer") or ""
        if origin and origin != "null":
            from urllib.parse import urlsplit
            if urlsplit(origin).netloc != host:
                return JSONResponse({"detail": "cross-site request refused"}, status_code=403)
        elif origin == "null":
            return JSONResponse({"detail": "cross-site request refused"}, status_code=403)
    return await call_next(request)

# ---------------------------------------------------------------- job queue: one worker, FIFO
class Job:
    def __init__(self, source: str, unit: int, stage: str, model: str | None):
        self.id = uuid.uuid4().hex[:8]; self.source, self.unit, self.stage, self.model = source, unit, stage, model
        self.state = "queued"; self.exit: int | None = None; self.lines: deque[str] = deque(maxlen=5000); self.proc = None
        self.engine = SETTINGS["engine"]; self.format = engines.ENGINES[self.engine]["format"]

JOBS: dict[str, Job] = {}
QUEUE: deque[Job] = deque()
LOCK = threading.Lock()


def worker():
    while True:
        with LOCK:
            job = QUEUE.popleft() if QUEUE else None
        if job is None:
            threading.Event().wait(0.5); continue
        job.state = "running"
        try:   # which stage this job is about to run, so Auto-run can tell whether it finished it
            src = pages.load()[job.source]
            pkg = pages.package_dir(job.source, src, job.unit)
            ran = pages.status(pkg)["next"] if job.stage == "next" else job.stage
        except Exception:
            pkg, ran = None, None
        job.engine = SETTINGS["engine"]; job.format = engines.ENGINES[job.engine]["format"]   # the engine at start time
        cmd = [PY, str(ROOT / "scripts" / "run_stage.py"), job.source, str(job.unit), "--stage", job.stage,
               "--engine", job.engine]
        if job.model:
            cmd += ["--model", job.model]
        job.proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in job.proc.stdout:
            job.lines.append(line.rstrip("\n"))
        exit_ = job.proc.wait()
        state = "done" if exit_ == 0 else ("stopped" if exit_ < 0 else "failed")
        if state == "done":
            auto_next(job, pkg, ran)   # queued before the state flips, so the Run page's reload finds the next job
        job.exit, job.state = exit_, state


def auto_next(job: Job, pkg: Path | None, ran: str | None):
    """Auto-run: when the stage just run is now done and the unit has another stage, queue it.
    Stops when the switch is off, the stage did not produce its file (no loop), a stage failed, or the package is finished."""
    if not SETTINGS.get("auto") or pkg is None or ran is None:
        return
    st = pages.status(pkg)
    if ran not in st["done"]:
        job.lines.append(json.dumps({"type": "chalk", "msg": f"Auto-run stopped: {ran} did not produce its file."}))
        return
    if not st["next"]:
        job.lines.append(json.dumps({"type": "chalk", "msg": "Auto-run: every stage is done."}))
        return
    nxt = Job(job.source, job.unit, "next", None)
    with LOCK:
        JOBS[nxt.id] = nxt; QUEUE.append(nxt)
    job.lines.append(json.dumps({"type": "chalk", "msg": f"Auto-run: {st['next']} queued."}))

threading.Thread(target=worker, daemon=True).start()


def current_job_for(source: str, unit: int) -> Job | None:
    for j in reversed(list(JOBS.values())):
        if j.source == source and j.unit == unit:
            return j
    return None

# ---------------------------------------------------------------- pages
def listing_with_jobs() -> list:
    srcs = pages.listing()
    for s in srcs:
        for u in s["units"]:
            j = current_job_for(s["id"], u["unit"])
            u["job"] = {"id": j.id, "state": j.state, "stage": j.stage} if j else None
    return srcs


@app.get("/", response_class=HTMLResponse)
def library(request: Request):
    srcs = listing_with_jobs()
    return templates.TemplateResponse(request, "library.html", {"sources": srcs, "stages": pages.STAGES})


@app.get("/run/{source}/{unit}", response_class=HTMLResponse)
def run_page(request: Request, source: str, unit: int):
    src = pages.load().get(source)
    if not src:
        raise HTTPException(404)
    pkg = pages.package_dir(source, src, unit)
    st = pages.status(pkg)
    j = current_job_for(source, unit)
    u = pages.units(src)[unit]
    return templates.TemplateResponse(request, "run.html", {
        "source": source, "src": src, "unit": unit, "u": u, "status": st, "stages": pages.STAGES,
        "job": j, "stage_files": dict(pages.STAGE_FILES)})


@app.get("/reader/{source}/{unit}")
def reader(source: str, unit: int):
    src = pages.load().get(source)
    if not src:
        raise HTTPException(404)
    pkg = pages.package_dir(source, src, unit)
    f = pkg / "reader.html"
    if not f.exists() and not build_reader(pkg, source, unit):
        raise HTTPException(404, "no reader yet — run the build stage")
    return HTMLResponse(with_back_bar(f.read_text(encoding="utf-8"), source, unit, src))


READER_LOCK = threading.Lock()


def build_reader(pkg: Path, source: str | None = None, unit: int | None = None) -> bool:
    """reader.html is build output, not in git, so a fresh clone has none: build it from the package's files exactly as
    `just view` does (deterministic scripts, no AI, a few seconds). If the source PDF is on disk (library/open/ ships
    openly licensed ones; students may add their own copy) and annotated.pdf is missing, annotate it first, as
    `just teach` does, so the Annotated chapter tab appears. Returns whether the Reader exists afterwards."""
    with READER_LOCK:
        out = pkg / "reader.html"
        if out.exists():
            return True
        if not (pkg / "map.md").exists():
            return False
        if source and unit is not None and not (pkg / "annotated.pdf").exists() and (pkg / "highlights.json").exists():
            try:
                src = pages.load()[source]
                pdf = ROOT / src["pdf"]
                lo, hi = pages.units(src)[unit]["pages"]
                off = 0 if src.get("kind") == "paper" else int(src.get("offset") or 0)
                if pdf.exists():
                    subprocess.run([PY, str(ROOT / "scripts" / "highlight_pdf.py"), str(pdf), str(pkg / "highlights.json"),
                                    str(pkg / "annotated.pdf"), "--first", str(lo + off), "--last", str(hi + off)],
                                   cwd=ROOT, capture_output=True, timeout=600)
            except Exception:
                pass
        if (pkg / "annotated.pdf").exists():
            subprocess.run([PY, str(ROOT / "scripts" / "render_pages.py"), str(pkg / "annotated.pdf"), str(pkg / ".pages")],
                           cwd=ROOT, capture_output=True, timeout=600)
        subprocess.run([PY, str(ROOT / "scripts" / "build_viewer.py"), str(pkg), str(pkg / ".pages"), str(out)],
                       cwd=ROOT, capture_output=True, timeout=600)
        return out.exists()


def build_missing_readers():
    """At startup: every package that passed review but has no Reader (a fresh clone) gets one, so the Library shows it
    finished and Teach does not re-run its build stage."""
    for sid, src in (pages.load() or {}).items():
        for unit in pages.units(src):
            try:
                pkg = pages.package_dir(sid, src, unit)
            except Exception:
                continue
            if (pkg / "REVIEW.md").exists() and not (pkg / "reader.html").exists():
                build_reader(pkg, sid, unit)


threading.Thread(target=build_missing_readers, daemon=True).start()


BACK_CSS = """<style id="chalk-back-css">
.chalk-back{display:flex;align-items:center;gap:4px;margin-right:6px}
.chalk-back a{font:600 13px/1 var(--sans,system-ui);color:var(--ink2,#444);text-decoration:none;padding:7px 10px;
  border:1px solid var(--rule,#ddd);border-radius:6px;background:var(--paper,#fff)}
.chalk-back a:hover,.chalk-back a:focus-visible{color:var(--ink,#111);border-color:var(--ink3,#888)}
.chalk-back a.home::before{content:"\\2190";margin-right:6px}
</style>"""


def with_back_bar(html: str, source: str, unit: int, src: dict) -> str:
    """The Reader file is standalone (it also opens from file://), so the way back to Chalk is added only when the
    GUI serves it: a Library link that reopens this book at its contents, a Run link, and Esc as a shortcut."""
    from html import escape
    title = escape(str(src.get("title", source)))
    nav = (f'<nav class="chalk-back" aria-label="Chalk"><a class="home" href="/#{escape(source)}" '
           f'title="Back to {title} in the Library (Esc)">Library</a>'
           f'<a href="/run/{escape(source)}/{unit}" title="Stages and log for this unit">Run</a></nav>')
    key = ("<script>document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!e.defaultPrevented&&"
           "!document.fullscreenElement&&!/INPUT|TEXTAREA|SELECT/.test(e.target.tagName))"
           f"location.href='/#{escape(source)}';}});</script>")
    if '<div class="hd">' in html:
        html = html.replace('<div class="hd">', '<div class="hd">' + nav, 1)
    else:   # a reader without the usual header: pin the links to the top-left
        html += '<div style="position:fixed;top:8px;left:8px;z-index:99">' + nav + "</div>"
    return BACK_CSS + html + key   # reader.html is a fragment (no <head>/<body>); browsers accept both ends


@app.get("/reader/{source}/{unit}/slides/{name}")
def slide_file(source: str, unit: int, name: str):
    """the Reader's Slides tab downloads: class|review .pdf (stamped study copy), nothing else from the package"""
    if not re.fullmatch(r"(class|review)\.pdf", name):
        raise HTTPException(404)
    src = pages.load().get(source)
    if not src:
        raise HTTPException(404)
    f = pages.package_dir(source, src, unit) / "slides" / name
    if not f.exists():
        raise HTTPException(404, "no slides yet — run the slides stage")
    slug = f"{source}-{unit}-{name}"
    return FileResponse(f, filename=slug)

# ---------------------------------------------------------------- api
@app.get("/settings")
def get_settings():
    return SETTINGS


@app.post("/settings")
async def set_settings(request: Request):
    body = await request.json()
    if "auto" in body:
        SETTINGS["auto"] = bool(body["auto"])
    new = copy.deepcopy(SETTINGS.get("engines") or {})
    for name, conf in (body.get("engines") or {}).items():
        if name in engines.ENGINES and isinstance(conf, dict):
            cur = new.setdefault(name, {})
            for k in ("command", "strong", "fast"):
                if k in conf:
                    cur[k] = str(conf[k])[:2000].strip()
            if cur.get("command"):   # validate before anything is kept
                try:
                    engines.build_command(engines.config(name, {"engines": new}), "x", "m")
                except ValueError as e:
                    raise HTTPException(400, str(e))
    SETTINGS["engines"] = new
    if body.get("engine") in engines.ENGINES:
        SETTINGS["engine"] = body["engine"]
    save_settings()
    return SETTINGS


def engine_rows() -> list[dict]:
    rows = []
    for name, d in engines.ENGINES.items():
        e = engines.config(name, SETTINGS)
        user = (SETTINGS.get("engines") or {}).get(name) or {}
        rows.append({"name": name, "label": d["label"], "note": d["note"], "install": d["install"], "login": d["login"],
                     "default_command": d["command"], "command": user.get("command", ""), "strong": e["strong"],
                     "fast": e["fast"], "path": engines.installed(e), "chosen": SETTINGS["engine"] == name})
    return rows


@app.get("/ai", response_class=HTMLResponse)
def ai_page(request: Request):
    return templates.TemplateResponse(request, "ai.html", {"page": "ai", "rows": engine_rows(), "tiers": engines.TIER})


@app.post("/ai/test/{name}")
def ai_test(name: str):
    if name not in engines.ENGINES:
        raise HTTPException(404)
    return engines.test(name, SETTINGS)


@app.get("/sources")
def sources():
    return listing_with_jobs()


@app.post("/sources")
async def upload(file: UploadFile, id: str = Form(...), kind: str = Form("book"), title: str = Form(""), authors: str = Form(""), year: str = Form("")):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "PDF only")
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp); tmp_path = Path(tmp.name)
    cmd = [PY, str(ROOT / "scripts" / "ingest.py"), str(tmp_path), "--id", id, "--kind", kind]
    if title: cmd += ["--title", title]
    if authors: cmd += ["--authors", authors]
    if year.strip().isdigit(): cmd += ["--year", year.strip()]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    tmp_path.unlink(missing_ok=True)
    if r.returncode != 0:
        msg = (r.stderr.strip() or r.stdout.strip()).splitlines() or ["ingest failed"]
        raise HTTPException(400, f"Could not read this PDF: {msg[-1]}")   # last line, not the traceback
    return RedirectResponse("/", status_code=303)


@app.put("/sources/{source}")
async def edit_source(source: str, request: Request):
    body = await request.json()
    data = pages.load()
    if source not in data:
        raise HTTPException(404)
    for k in ("offset", "title", "authors", "year", "kind", "chapters", "track"):
        if k in body:
            data[source][k] = body[k]
    pages.save(data)
    return data[source]


@app.post("/teach/{source}/{unit}")
def teach(source: str, unit: int, stage: str = Form("next"), model: str = Form("")):
    if source not in pages.load():
        raise HTTPException(404)
    j = current_job_for(source, unit)
    if j and j.state in ("queued", "running"):
        return RedirectResponse(f"/run/{source}/{unit}", status_code=303)
    job = Job(source, unit, stage, model or None)
    with LOCK:
        JOBS[job.id] = job; QUEUE.append(job)
    return RedirectResponse(f"/run/{source}/{unit}", status_code=303)


@app.post("/jobs/{job_id}/stop")
def stop(job_id: str):
    j = JOBS.get(job_id)
    if j and j.proc and j.state == "running":
        j.proc.terminate()
    return JSONResponse({"ok": True})


@app.get("/jobs/{job_id}/stream")
async def stream(job_id: str):
    j = JOBS.get(job_id)
    if not j:
        raise HTTPException(404)

    async def gen():
        sent = 0
        while True:
            lines = list(j.lines)
            for line in lines[sent:]:
                ev = engines.render(j.format, line)
                if ev["text"].strip():  # system/user/tool-result events carry no display text
                    yield f"data: {json.dumps(ev)}\n\n"
            sent = len(lines)
            if j.state in ("done", "failed", "stopped") and sent >= len(j.lines):
                yield f"event: end\ndata: {json.dumps({'state': j.state, 'exit': j.exit})}\n\n"; return
            await asyncio.sleep(0.4)
    return StreamingResponse(gen(), media_type="text/event-stream")


