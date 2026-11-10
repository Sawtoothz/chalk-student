"""Generates the T5 data files. The true noise levels are set here; do not read this file until you
have finished T5 (it is the answer to tasks 2 and 3)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .models import RangeBearing, figure_eight

TRUE_R = np.diag([0.03, 0.03, 0.015]) ** 2
TRUE_Q = np.diag([0.15, np.deg2rad(1.5)]) ** 2


def main(out="data", runs=10, n=400):
    out = Path(__file__).resolve().parent / out
    out.mkdir(exist_ok=True)
    model = RangeBearing(R_proc=TRUE_R, Q_meas=TRUE_Q)
    U = figure_eight(n, model.dt)
    for s in range(runs):
        rng = np.random.default_rng(1000 + s)
        xs, zs = model.simulate(np.array([0.0, 0.0, 0.3]), U, rng)
        np.savez(out / f"t5_run_{s}.npz", xs=xs, zs=zs, U=U, landmark=model.m, dt=model.dt)
    print(f"wrote {runs} runs to {out}")


if __name__ == "__main__":
    main()
