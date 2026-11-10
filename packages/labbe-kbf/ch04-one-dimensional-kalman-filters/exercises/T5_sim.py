"""Generates the T5 data files. The true noise levels are set here; do not read this file until you
have finished T5 (it is the answer to tasks 2 and 3).

Run from the package directory: python -m exercises.T5_sim
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .models import DroneAltitude

TRUE_R_PROC = 0.04 ** 2     # m² per 50 ms step, in flight: vertical tracking error of the thrust loop
TRUE_Q_MEAS = 0.45 ** 2     # m²: baro noise with the props spinning (the datasheet's 0.1 m is for a still board)
H0 = 18.6                   # m above sea level: the take-off point
GUST = (28.0, 32.0, -1.2)   # start [s], end [s], vertical wind [m/s] the flight controller does not know about
OUTLIER_RATE = 0.03


def main(out="data", runs=10):
    out = Path(__file__).resolve().parent / out
    out.mkdir(exist_ok=True)
    t, v_cmd, ground = DroneAltitude.mission()
    model = DroneAltitude(TRUE_R_PROC, TRUE_Q_MEAS, h0=H0)
    gust = np.where((t >= GUST[0]) & (t < GUST[1]), GUST[2], 0.0)
    for s in range(runs):
        rng = np.random.default_rng(4000 + s)
        h, z, _ = model.simulate(v_cmd, ground, rng)
        _, z_out, _ = model.simulate(v_cmd, ground, np.random.default_rng(4000 + s), outlier_rate=OUTLIER_RATE)
        h_gust, z_gust, _ = model.simulate(v_cmd, ground, np.random.default_rng(4000 + s), gust=gust)
        np.savez(out / f"t5_run_{s}.npz", t=t, dt=model.dt, v_cmd=v_cmd, u=v_cmd * model.dt, ground=ground,
                 h=h, z=z, z_out=z_out, h_gust=h_gust, z_gust=z_gust)
    print(f"wrote {runs} runs to {out}")


if __name__ == "__main__":
    main()
