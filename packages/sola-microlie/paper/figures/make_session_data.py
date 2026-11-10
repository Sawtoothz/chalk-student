"""Builds interactive.html: pastes session_core.js and the data of T5 runs 0–2 into interactive_src.html.

    python figures/make_session_data.py        (from the package directory)
"""
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PKG))
import session_lib as L  # noqa: E402


def runs_json(n=3):
    out = []
    for i in range(n):
        r = L.load_run(i)
        dets = [[[int(j), float(r["Y"][k, j, 0]), float(r["Y"][k, j, 1])] for j in range(r["mask"].shape[1]) if r["mask"][k, j]]
                for k in range(len(r["U"]))]
        out.append(dict(truth=r["truth"].tolist(), U=r["U"].tolist(), dets=dets, tags=r["tags"].tolist(),
                        err0=r["err0"].tolist(), P0=r["P0"].tolist()))
    return out


def main():
    here = Path(__file__).resolve().parent
    data = dict(runs=runs_json(), d_series=L.D_SERIES)
    (here / "session_runs.json").write_text(json.dumps(data))
    html = (here / "interactive_src.html").read_text()
    html = html.replace("/*__CORE__*/", (here / "session_core.js").read_text())
    html = html.replace("/*__DATA__*/null", json.dumps(data))
    (PKG / "interactive.html").write_text(html)
    print("wrote interactive.html", len(html) // 1024, "KB")


if __name__ == "__main__":
    main()
