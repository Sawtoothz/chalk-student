"""Generates the T5 data files. The true noise, outlier rate and the kidnap are set here; do not read
this file until you have finished T5 (it is the answer to tasks 5 and 6)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .models import SymmetricField, field_controls

TRUE = dict(slip_v=0.05, slip_w=0.08, slip_df=3.0,          # Student-t slip on (v, ω): tracks slip in bursts
            sigma_r=0.15, sigma_b=np.deg2rad(3.0), p_outlier=0.05)
X0 = np.array([-2.5, -1.2, 0.3])
KIDNAP_T, KIDNAP_TO = 300, np.array([0.5, -2.8, np.pi / 2])   # referee places the robot at the sideline


def main(out="data", runs=10, n=400):
    out = Path(__file__).resolve().parent / out
    out.mkdir(exist_ok=True)
    f = SymmetricField()
    U = field_controls(n)
    for s in range(runs):
        rng = np.random.default_rng(2000 + s)
        x = X0.copy()
        xs, zs = [x.copy()], []
        for t, (v, w) in enumerate(U):
            if v != 0.0 or w != 0.0:
                v_n = v + TRUE["slip_v"] * rng.standard_t(TRUE["slip_df"])
                w_n = w + TRUE["slip_w"] * rng.standard_t(TRUE["slip_df"])
                x = f.move(x, v_n, w_n)[0]
            if t == KIDNAP_T:
                x = KIDNAP_TO.copy()
            xs.append(x.copy())
            zs.append(f.sense(x, rng, TRUE["sigma_r"], TRUE["sigma_b"], TRUE["p_outlier"]))
        np.savez(out / f"t5_run_{s}.npz", xs=np.array(xs), zs=np.array(zs), U=U, dt=f.dt)
    print(f"wrote {runs} runs to {out}")


if __name__ == "__main__":
    main()
