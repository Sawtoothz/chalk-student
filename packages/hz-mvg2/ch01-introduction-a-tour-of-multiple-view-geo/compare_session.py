"""Compare the readout tiles of session_model.py (Python) and interactive.html (JS, run in node with a
stub DOM) on the default settings and a few edge settings. Exit 1 on any difference.
Run from the package: python3 compare_session.py"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    from exercises.solutions import T3_solution as ex  # noqa: E402
except ImportError:  # student edition: no gated solutions; your own exercise.py drives this
    from exercises import exercise as ex  # noqa: E402
import session_model as sm  # noqa: E402

html = (HERE / "interactive.html").read_text()
script = re.search(r"<script>(.*)</script>", html, re.S).group(1)

CASES = [
    ("a", dict(pitch=15, gap=1.2, yaw=0)), ("a", dict(pitch=40, gap=1.2, yaw=0)), ("a", dict(pitch=15, gap=1.2, yaw=90)),
    ("a", dict(pitch=0, gap=2.0, yaw=35)),
    ("b", dict(s=0.08, u=0.0)), ("b", dict(s=0.0, u=0.0)), ("b", dict(s=-0.12, u=0.0)), ("b", dict(s=0.2, u=-0.15)),
    ("c", dict(idx=7, sigma=1.0)), ("c", dict(idx=7, sigma=0.0)), ("c", dict(idx=33, sigma=2.5)),
    ("d", dict(drive=0.3, turn=10, fwd=0.0)), ("d", dict(drive=0.0, turn=10, fwd=0.0)), ("d", dict(drive=0.0, turn=10, fwd=0.3)),
    ("d", dict(drive=1.0, turn=30, fwd=0.5)),
]
FN = {"a": sm.fig_a, "b": sm.fig_b, "c": sm.fig_c, "d": sm.fig_d}
ARGS = {"a": ("pitch", "gap", "yaw"), "b": ("s", "u"), "c": ("idx", "sigma"), "d": ("drive", "turn", "fwd")}

js = """
const el=()=>({value:'0',textContent:'',innerHTML:'',dataset:{},addEventListener(){}});
global.document={getElementById:()=>null,documentElement:{}};
global.getComputedStyle=()=>({getPropertyValue:()=>''});
global.window=global;
""" + script + """
const cases=%s;const out=[];
for(const [k,a] of cases){const f=window.__ixCompute['compute'+k.toUpperCase()];const r=f(...a);out.push({tiles:r.tiles,chip:r.chip})}
console.log(JSON.stringify(out));
""" % json.dumps([[k, [v[a] for a in ARGS[k]]] for k, v in CASES])
with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, dir="/tmp") as f:
    f.write(js)
res = subprocess.run(["node", f.name], capture_output=True, text=True)
if res.returncode:
    print(res.stderr); sys.exit(1)
jsout = json.loads(res.stdout)
bad = 0
for (k, kw), j in zip(CASES, jsout):
    p = FN[k](ex, **kw)
    ok = True
    if list(p["tiles"].items()) != list(j["tiles"].items()):
        ok = False
        for (pk, pv), (jk, jv) in zip(p["tiles"].items(), j["tiles"].items()):
            if (pk, pv) != (jk, jv):
                print(f"  DIFF fig {k} {kw}: {pk!r}: py={pv!r} js={jv!r}")
    if list(p["chip"]) != list(j["chip"]):
        ok = False; print(f"  DIFF chip fig {k} {kw}: py={p['chip']} js={j['chip']}")
    bad += not ok
    print(("ok  " if ok else "FAIL"), k, kw)
print("tiles agree on all cases" if not bad else f"{bad} case(s) differ")
sys.exit(1 if bad else 0)
