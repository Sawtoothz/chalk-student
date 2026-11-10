"""Fixed standard-normal draws shared by session.py and interactive.html, so both compute the same readouts.

    .venv/bin/python figures/make_session_data.py

Writes figures/session_data.json and replaces the line between the DATA markers in ../interactive.html
(if that file exists). Truth and measurements are built from these draws in both languages:
x_k = x_{k-1} + u_k + sqrt(R_true) * W[k];  z_k = x_k + sqrt(Q_true) * V[k].
"""
import json
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
rng = np.random.default_rng(4)
data = {"W1": rng.standard_normal(25), "V1": rng.standard_normal(25),   # Fig 2.2b, 25 steps (p. 147)
        "W2": rng.standard_normal(40), "V2": rng.standard_normal(40)}   # Fig 2.2d, 40 steps
data = {k: [round(float(v), 6) for v in a] for k, a in data.items()}
(HERE / "session_data.json").write_text(json.dumps(data))

html = HERE.parent / "interactive.html"
if html.exists():
    txt = html.read_text()
    new = "/*DATA*/const DATA=" + json.dumps(data) + ";/*END DATA*/"
    txt2, n = re.subn(r"/\*DATA\*/.*?/\*END DATA\*/", lambda m: new, txt, flags=re.S)
    assert n == 1, "DATA markers not found in interactive.html"
    html.write_text(txt2)
print("ok", {k: len(v) for k, v in data.items()})
