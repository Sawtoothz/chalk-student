"""Generates the T5 data files. The true noise levels are set here; do not read this file until you have finished
T5 (it is the answer to tasks 2 and 3).

    python -m exercises.T5_sim        (from the package directory)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .models import TrackedRobot, figure_eight_controls, xyth

TRUE_R = np.diag([0.012, 0.008, 0.004]) ** 2      # per 0.1 s step: along-track, lateral slip u_s, yaw
TRUE_Q = np.diag([0.04, 0.04]) ** 2               # tag position in the body frame
OUTLIER_RATE = 0.05                               # misread tag IDs in the *_outliers files


def main(out="data", runs=10, n=600):
    out = Path(__file__).resolve().parent / out
    out.mkdir(exist_ok=True)
    robot = TrackedRobot(R_proc=TRUE_R, Q_meas=TRUE_Q)
    U = figure_eight_controls(n, robot.dt)
    for s in range(runs):
        rng = np.random.default_rng(2000 + s)
        Xs, Y, mask = robot.simulate(U, rng)
        truth = np.array([xyth(X) for X in Xs])
        np.savez_compressed(out / f"t5_run_{s}.npz", truth=truth, U=U, Y=Y, mask=mask, tags=robot.tags, dt=robot.dt)
        # misread IDs: the detection of tag j is reported as the position of another tag, seen from the true pose
        Yo = Y.copy()
        bad = mask & (rng.random(mask.shape) < OUTLIER_RATE)
        Ly = np.linalg.cholesky(TRUE_Q)
        for k, j in zip(*np.nonzero(bad)):
            other = rng.choice([i for i in range(len(robot.tags)) if i != j])
            Xi = np.linalg.inv(Xs[k + 1])
            Yo[k, j] = (Xi @ np.r_[robot.tags[other], 1.0])[:2] + Ly @ rng.normal(size=2)
        np.savez_compressed(out / f"t5_outliers_run_{s}.npz", truth=truth, U=U, Y=Yo, mask=mask, tags=robot.tags,
                 dt=robot.dt, outlier=bad)
    print(f"wrote {2 * runs} files to {out}")


if __name__ == "__main__":
    main()
