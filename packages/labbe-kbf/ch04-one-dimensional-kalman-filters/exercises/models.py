"""Shared models for the ch. 4 exercises. Nothing here is an exercise: read it, do not edit it.

Names follow the repo convention: R_proc = Labbe's Q (variance added per predict), Q_meas = Labbe's R
(measurement variance). Every model is scalar; there are no angles in this chapter, so no wrap().

Two systems:

1. `DogHallway` — the chapter's dog (pp. 131–147): position x [m] in a hallway, moving u [m] per step
   with a random-walk error of variance R_proc [m²/step], seen by an RFID position sensor with variance
   Q_meas [m²]. Exactly the model the 1-D Kalman filter assumes, so the filter is optimal on it.

2. `DroneAltitude` — a quadrotor's barometric altitude. State h [m above sea level], known input
   u_k = v_cmd,k · dt [m/step] from the flight controller's commanded climb rate, barometer z [m].
   The vertical tracking error of the attitude/thrust loop is the random walk (R_proc per step, in
   flight only: on the ground the drone does not move). The noise levels are hidden in `T5_sim.py`.
"""

from __future__ import annotations

import numpy as np

# ------------------------------------------------------------------ the book's dog


class DogHallway:
    """x_{k+1} = x_k + u + w_k, w_k ~ N(0, R_proc);  z_k = x_{k+1} + v_k, v_k ~ N(0, Q_meas).

    Defaults are the chapter's 25-step run (p. 147): velocity 1 m/step, Labbe's process_var = 2 (R_proc),
    sensor_var = 4.5 (Q_meas).
    """

    def __init__(self, u=1.0, R_proc=2.0, Q_meas=4.5):
        self.u, self.R_proc, self.Q_meas = float(u), float(R_proc), float(Q_meas)

    def simulate(self, n, rng, x0=0.0, runs=None):
        """Return (xs, zs). xs[..., k] is the true position when zs[..., k] is taken, after k + 1 moves.

        runs=None gives shape (n,); runs=M gives M independent runs, shape (M, n). x0 is the true start.
        """
        shape = (n,) if runs is None else (runs, n)
        steps = self.u + rng.normal(0.0, np.sqrt(self.R_proc), shape)
        xs = x0 + np.cumsum(steps, axis=-1)
        zs = xs + rng.normal(0.0, np.sqrt(self.Q_meas), shape)
        return xs, zs


# ------------------------------------------------------------------ the drone (T5)


class DroneAltitude:
    """Barometric altitude of a quadrotor at 20 Hz.

    h_{k+1} = h_k + v_cmd,k·dt + d_k·dt + w_k,  w_k ~ N(0, R_proc) in flight, 0 on the ground,
    z_k = h_{k+1} + v_k,  v_k ~ N(0, Q_meas), plus optional outlier spikes.
    d_k is an unmodeled vertical wind (zero unless a gust is given). The filter knows v_cmd, not d.
    """

    dt = 0.05

    def __init__(self, R_proc, Q_meas, h0=0.0):
        self.R_proc, self.Q_meas, self.h0 = float(R_proc), float(Q_meas), float(h0)

    @staticmethod
    def mission(dt=0.05):
        """Commanded climb rate [m/s] and on-ground mask for the 70 s test flight.

        0–10 s on the ground (motors armed, no motion), 10–20 s climb 1.0 m/s, 20–35 s hover,
        35–45 s climb 0.5 m/s, 45–55 s hover, 55–65 s descend 1.3 m/s, 65–70 s hover 2 m above the take-off point.
        """
        t = np.arange(int(round(70.0 / dt))) * dt
        v = np.zeros_like(t)
        v[(t >= 10) & (t < 20)] = 1.0
        v[(t >= 35) & (t < 45)] = 0.5
        v[(t >= 55) & (t < 65)] = -1.3
        ground = t < 10.0
        return t, v, ground

    def simulate(self, v_cmd, ground, rng, gust=None, outlier_rate=0.0):
        """Return (h, z, is_outlier). h[k] is the true altitude when z[k] is taken.

        gust: array of unmodeled vertical wind [m/s] per step, or None.
        outlier_rate: fraction of baro samples replaced by a spike of ±2–8 m (prop wash, door slams).
        """
        n = len(v_cmd)
        d = np.zeros(n) if gust is None else np.asarray(gust, float)
        w = np.where(ground, 0.0, rng.normal(0.0, np.sqrt(self.R_proc), n))
        h = self.h0 + np.cumsum(v_cmd * self.dt + d * self.dt + w)
        z = h + rng.normal(0.0, np.sqrt(self.Q_meas), n)
        out = rng.random(n) < outlier_rate
        spikes = rng.choice([-1.0, 1.0], n) * rng.uniform(2.0, 8.0, n)
        z = np.where(out, z + spikes, z)
        return h, z, out
