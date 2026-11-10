"""Generates the T5 data files: a tracked (skid-steer) robot driving `models.tracked_route`, logged with
ground truth (motion capture), wheel-track odometry and the commands. The true slip, the track-width
error and the slip bursts are set here; do not read this file until you have finished T5 (it is the
answer to tasks 3 and 5).

Run from the package folder: python -m exercises.T5_sim
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .models import tracked_route, wrap

DT = 0.1
X0 = np.array([0.0, 0.0, 0.0])
TRUE = dict(
    chi=1.3,             # effective / nominal track width: the encoders over-report every turn by 30 %
    ctrl_v=0.02,         # m/s, track speed controller error (what the tracks do vs the command)
    ctrl_w=0.03,         # rad/s
    slip_v=0.03,         # m/s per m/s of |v|: longitudinal slip, proportional to speed
    slip_w0=0.02,        # rad/s, lateral skid at any motion
    slip_w1=0.08,        # rad/s per rad/s of |ω_tracks|: skid grows with the turn rate
    p_burst=0.02,        # per moving step: a track catches a rut or a kerb
    burst_w=0.5,         # rad/s, std of the yaw jolt in a burst
    burst_v=(0.3, 0.8),  # forward speed kept in a burst, uniform range
    lateral=0.005,       # m per step, sideways skid of the hull (off the arc)
    yaw_jitter=0.004,    # rad per step, heading jitter not explained by the arc
)


def chord(X, v, w, dt):
    half = 0.5 * w * dt
    s = v * dt * np.sinc(half / np.pi)
    return np.array([X[0] + s * np.cos(X[2] + half), X[1] + s * np.sin(X[2] + half), wrap(X[2] + w * dt)])


def simulate(rng, n=600, odom0=None):
    U = tracked_route(n, DT)
    odom0 = np.array([3.0, -1.0, 1.0]) if odom0 is None else odom0
    xs, od = [X0.copy()], [odom0.copy()]
    bursts = []
    for t, (v, w) in enumerate(U):
        moving = v != 0.0 or w != 0.0
        v_tr = v + (TRUE["ctrl_v"] * rng.normal() if moving else 0.0)
        w_tr = w + (TRUE["ctrl_w"] * rng.normal() if moving else 0.0)
        v_true, w_true = v_tr, w_tr / TRUE["chi"]
        if moving:
            v_true += TRUE["slip_v"] * abs(v_tr) * rng.normal()
            w_true += (TRUE["slip_w0"] + TRUE["slip_w1"] * abs(w_tr)) * rng.normal()
            if rng.random() < TRUE["p_burst"]:
                v_true *= rng.uniform(*TRUE["burst_v"])
                w_true += TRUE["burst_w"] * rng.normal()
                bursts.append(t)
        x_new = chord(xs[-1], v_true, w_true, DT)
        if moving:   # real hulls do not stay on the arc: sideways skid and heading jitter
            lat = TRUE["lateral"] * rng.normal()
            x_new[0] -= lat * np.sin(x_new[2]); x_new[1] += lat * np.cos(x_new[2])
            x_new[2] = wrap(x_new[2] + TRUE["yaw_jitter"] * rng.normal())
        xs.append(x_new)
        od.append(chord(od[-1], v_tr, w_tr, DT))      # odometry integrates what the tracks did
    return np.array(xs), np.array(od), U, np.array(bursts, dtype=int)


def main(out="data", runs=10, n=600):
    out = Path(__file__).resolve().parent / out
    out.mkdir(exist_ok=True)
    for s in range(runs):
        rng = np.random.default_rng(3000 + s)
        xs, od, U, bursts = simulate(rng, n, odom0=np.array([3.0 + s, -1.0, 1.0 - 0.2 * s]))
        np.savez(out / f"t5_run_{s}.npz", xs=xs, odom=od, U=U, dt=DT)
        del bursts   # not in the file: finding them is part of task 5
    print(f"wrote {runs} runs to {out}")


if __name__ == "__main__":
    main()
