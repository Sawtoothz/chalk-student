"""T4 — Debug. This is a drone's barometric-altitude filter written the way it often first appears on a
flight controller: a scalar Kalman filter in float32, fed the commanded climb rate and the barometer. It
contains FIVE planted bugs, four of them from real flight logs and one numerical-hygiene trap. Find and
fix them. `pytest exercises/tests/test_T4.py` passes when all five are fixed.

Do not rewrite the file from scratch; the point is to recognise each symptom.
Symptoms you may see before fixing: the estimate lags the baro on every climb and the lag gets worse with
a better barometer; the filter throws away good baro samples right after takeoff; after a baro dropout the
altitude jumps; tuning the "sensor noise" parameter does something different from what its name says;
with an unknown start altitude the variance collapses to zero and the estimate freezes.

Names: R_proc = process variance per second [m²/s] (Labbe's Q); Q_meas = baro variance [m²] (Labbe's R).
"""

from __future__ import annotations

import numpy as np

f32 = np.float32


class AltitudeFilter:
    def __init__(self, x0, P0, R_proc, sigma_z, gate=None):
        """x0 [m], P0 [m²], R_proc [m²/s], sigma_z = baro noise standard deviation [m] (datasheet RMS)."""
        self.x = f32(x0)
        self.P = f32(P0)
        self.R_proc = f32(R_proc)
        self.Q_meas = f32(sigma_z)
        self.gate = gate                     # e.g. 6.635 for a 99% chi-square(1) gate, or None

    def predict(self, v_cmd, dt):
        """Move by the commanded climb rate v_cmd [m/s] for dt [s]."""
        self.x = self.x + f32(v_cmd) * f32(dt)
        self.P = self.P + self.Q_meas * f32(dt)

    def update(self, z):
        """Fuse one baro sample z [m]. Return (y, S, accepted)."""
        z = f32(z)
        y = z - self.x
        S = self.P + self.Q_meas
        if self.gate is not None and y * y > f32(self.gate) * self.Q_meas:
            return y, S, False
        K = self.P / S
        self.x = self.x + K * y
        self.P = (f32(1.0) - K) * self.P
        return y, S, True

    def step(self, v_cmd, dt, z=None):
        """One control tick. z is None when the baro sample did not arrive this tick."""
        if z is None:
            return None
        self.predict(v_cmd, dt)
        return self.update(z)
