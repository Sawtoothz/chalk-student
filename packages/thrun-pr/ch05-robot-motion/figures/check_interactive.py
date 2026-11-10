"""Compare the readout tiles of interactive.html (headless Chrome, JS) with session.py (marimo, Python).

    python3 figures/check_interactive.py

Both are driven from the same fixed normal draws, so every tile string must be identical on every scenario.
Needs google-chrome on PATH. Plotly is stubbed out: only the tiles and chips are compared, not the pictures.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent

SCENARIOS = [  # (figure, slider overrides)
    ("A", {}), ("A", {"a_g": 0}), ("A", {"a_w": 1.2, "a_s": 0.5}), ("A", {"a_w": 0}), ("A", {"a_w": -0.7, "a_s": -0.5}),
    ("B", {}), ("B", {"b_w": 0}), ("B", {"b_v": -1, "b_w": 0.5}), ("B", {"b_v": 1, "b_w": 0.5}),
    ("B", {"b_v": 0, "b_w": 0.5}), ("B", {"b_v": -0.6, "b_w": -0.8}),
    ("C", {}), ("C", {"c_d": 0, "c_psi": 30}), ("C", {"c_d": 0, "c_psi": 30, "c_th": 0}), ("C", {"c_d": 0.5}),
    ("C", {"c_d": 1.2, "c_psi": -60, "c_th": -90, "c_s": 0.3}),
    ("D", {}), ("D", {"d_n": 10}), ("D", {"d_cap": 1}), ("D", {"d_v": 1.6, "d_cap": 1}), ("D", {"d_v": 0.5, "d_n": 5}),
]
DEFAULTS = {"A": {"a_w": 0.8, "a_s": 0.0, "a_g": 1.0}, "B": {"b_v": 1.0, "b_w": -0.5},
            "C": {"c_d": -0.5, "c_psi": 0, "c_th": 150, "c_s": 0.0}, "D": {"d_v": 1.0, "d_n": 1, "d_cap": 10}}
TILES = {"A": "a_tiles", "B": "b_tiles", "C": "c_tiles", "D": "d_tiles"}

HARNESS = """
<script>
window.addEventListener('load',()=>{
  const SC=%s, DEF=%s, out=[];
  const set=(id,v)=>{const el=document.getElementById(id);el.value=String(v);el.dispatchEvent(new Event('input'))};
  for(const [fig,ov] of SC){
    const all=Object.assign({},DEF[fig],ov);for(const k in all)set(k,all[k]);
    out.push({fig,ov,tiles:window.__ixReadouts()[fig],chip:document.getElementById('chip'+fig).textContent,state:document.getElementById('chip'+fig).dataset.state});
  }
  document.body.insertAdjacentHTML('beforeend','<pre id="result">'+JSON.stringify(out).replace(/</g,'&lt;')+'</pre>');
});
</script>
"""


def run_js():
    html = (PKG / "interactive.html").read_text()
    page = ("<!doctype html><html><body><script>window.Plotly={react(){}};</script><div id='panel-session'>" + html + "</div>"
            + HARNESS % (json.dumps(SCENARIOS), json.dumps(DEFAULTS)) + "</body></html>")
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "harness.html"
        f.write_text(page)
        r = subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=60000",
                            "--dump-dom", f"file://{f}"], capture_output=True, text=True, timeout=300)
    dom = r.stdout
    i = dom.rfind('<pre id="result">')
    if i < 0:
        sys.exit("no result in DOM; stderr:\n" + r.stderr[-1500:])
    body = dom[i + len('<pre id="result">'):dom.find("</pre>", i)]
    import html as H
    return json.loads(H.unescape(body))


class V:
    def __init__(self, v):
        self.value = v


def run_py(m, fig, ov):
    kw = {k: V(v) for k, v in {**DEFAULTS[fig], **ov}.items()}
    _, defs = m.app.run(defs=kw)
    return defs[TILES[fig]]


def main():
    sys.path.insert(0, str(PKG))
    s = importlib.util.spec_from_file_location("session", PKG / "session.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    bad = 0
    for row in run_js():
        py = run_py(m, row["fig"], row["ov"])
        js = row["tiles"]
        diffs = [(k, py.get(k), js.get(k)) for k in sorted(set(py) | set(js)) if py.get(k) != js.get(k)]
        print(("OK  " if not diffs else "DIFF"), row["fig"], row["ov"], "| chip:", row["chip"], f"[{row['state']}]")
        for k, a, b in diffs:
            print("     ", k, "| py:", a, "| js:", b)
        bad += bool(diffs)
    print("VERDICT:", "readouts agree" if not bad else f"{bad} scenario(s) differ")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
