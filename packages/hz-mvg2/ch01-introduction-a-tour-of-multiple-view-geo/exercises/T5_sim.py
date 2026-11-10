"""Generates the T5 data files. The true motions and the noise level are set here; do not read this
file until you have finished T5 (it is the answer to tasks 2–4).

Run from the package dir: `python3 -m exercises.T5_sim`.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .models import K_LECTURE, MOUNT_H, floor_and_clutter, hom, pixels, project, robot_camera, seen_by

TRUE_SIGMA_PX = 0.6        # detector noise, both images, both axes
OUTLIER_FRAC = 0.15        # for the *_outliers copy: matches replaced by random pixels
CAM_FWD = 0.25             # camera ahead of the turning centre (m)

# name: (second robot pose (x, y, yaw°), camera fwd offset, floor, clutter)
PAIRS = {
    "pan":        ((0.00, 0.00, 8.0), 0.0, True, True),     # camera turns on a pan unit; centre fixed
    "floor_only": ((0.00, 0.30, 0.0), CAM_FWD, True, False),
    "drive_turn": ((0.02, 0.30, 3.0), CAM_FWD, True, True),
    "skid_turn":  ((0.00, 0.00, 8.0), CAM_FWD, True, True),  # robot turns on the spot; camera is 0.25 m ahead
    "creep":      ((0.00, 0.02, 2.0), CAM_FWD, True, True),
    "drive_far":  ((0.10, 0.50, -4.0), CAM_FWD, True, True),
}


def make_pair(name, rng):
    (x, y, yaw), fwd, floor, clutter = PAIRS[name]
    cam1 = robot_camera(fwd=fwd)
    cam2 = robot_camera(x, y, yaw, fwd=fwd)
    Xw, is_floor = floor_and_clutter(rng, 250, 250, floor=floor, clutter=clutter)
    keep = seen_by([cam1, cam2], Xw)
    Xw, is_floor = Xw[keep], is_floor[keep]
    u1 = pixels(project(cam1[0], hom(Xw))) + rng.normal(0, TRUE_SIGMA_PX, (len(Xw), 2))
    u2 = pixels(project(cam2[0], hom(Xw))) + rng.normal(0, TRUE_SIGMA_PX, (len(Xw), 2))
    return dict(u1=u1, u2=u2, floor=is_floor, K=K_LECTURE, h=MOUNT_H), dict(cam1=cam1, cam2=cam2, Xw=Xw)


def main(out="data"):
    out = Path(__file__).resolve().parent / out
    out.mkdir(exist_ok=True)
    for k, name in enumerate(PAIRS):
        rng = np.random.default_rng(500 + k)
        d, _ = make_pair(name, rng)
        np.savez(out / f"t5_{name}.npz", **d)
        if name == "drive_turn":
            d = dict(d)
            n = len(d["u2"])
            bad = rng.choice(n, int(OUTLIER_FRAC * n), replace=False)
            d["u2"] = d["u2"].copy()
            d["u2"][bad] = rng.uniform([0, 0], [640, 480], (len(bad), 2))
            np.savez(out / f"t5_{name}_outliers.npz", **d)
        print(f"{name:12} {len(d['u1'])} matches, {int(d['floor'].sum())} on the floor")
    print(f"wrote to {out}")


if __name__ == "__main__":
    main()
