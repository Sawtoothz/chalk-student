"""Compares the readout tiles of session_lib.py (marimo) and session_core.js (interactive.html) on default settings.

    python figures/compare_session.py        (from the package directory; needs node)
"""
import json
import subprocess
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PKG))
import session_lib as L  # noqa: E402
from exercises.solutions import T3_solution as ex  # noqa: E402

DEFAULTS = dict(a=dict(xX=1.5, thX_deg=40.0, rho1=0.8, th_deg=50.0), b=dict(ratio=0.35, sig_th_deg=20.0, th_mean_deg=30.0),
                c=dict(run=0, sig_y=0.10, sig_slip_mm=1.0), d=dict(log10=-3.0))
JS = """
const SC=require('./figures/session_core.js'), D=require('./figures/session_runs.json'), a=%s;
const out={a:SC.figA(a.a).tiles,b:SC.figB(a.b).tiles,c:SC.figC(D.runs[a.c.run],a.c).tiles,d:SC.figD(a.d.log10,D.d_series).tiles};
console.log(JSON.stringify(out));
"""


def main():
    js = json.loads(subprocess.run(["node", "-e", JS % json.dumps(DEFAULTS)], cwd=PKG, capture_output=True, text=True, check=True).stdout)
    d = DEFAULTS
    py = dict(a=L.fig_a(ex, **d["a"])["tiles"], b=L.fig_b(ex, **d["b"])["tiles"],
              c=L.fig_c(ex, L.load_run(d["c"]["run"]), d["c"]["sig_y"], d["c"]["sig_slip_mm"])["tiles"], d=L.fig_d(d["d"]["log10"])["tiles"])
    norm = lambda s: s.replace("−", "-")
    bad = 0
    for fig in py:
        for k, v in py[fig].items():
            same = norm(v) == norm(js[fig].get(k, "MISSING"))
            bad += not same
            print(f"{'ok ' if same else 'DIFF'} {fig} · {k}: py={v!r} js={js[fig].get(k)!r}")
    print("DIFFERENCES:", bad)
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
