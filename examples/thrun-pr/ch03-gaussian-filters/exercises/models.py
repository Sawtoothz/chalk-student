"""Shared models for the ch. 3 exercises. Nothing here is an exercise: read it, do not edit it.

Two systems:

1. `CarCV`  — book exercises 1-2: 1-D car with random acceleration, Δt = 1, σ_acc² = 1, position
   measurement with σ_z² = 10. State x = (p, v). Linear, so the KF is exact.

2. `RangeBearing` — a planar robot with the velocity motion model (Thrun eq. 5.9) observing a known
   landmark by range and bearing. State x = (x, y, θ), control u = (v, ω), measurement z = (r, φ).
   Nonlinear in θ and in the landmark geometry. This is the tracked-robot case.
"""

from __future__ import annotations

import numpy as np

# ------------------------------------------------------------------ book exercises 1-2


class CarCV:
    """Constant-velocity car. x = (p, v). a_t ~ N(0, 1) acts for Δt = 1."""

    dt = 1.0
    A = np.array([[1.0, 1.0], [0.0, 1.0]])
    B = np.zeros((2, 1))
    # acceleration enters as [dt²/2, dt] a_t, so R = Γ σ² Γᵀ with Γ = [0.5, 1]
    _G = np.array([[0.5], [1.0]])
    R_proc = _G @ _G.T * 1.0
    C = np.array([[1.0, 0.0]])
    Q_meas = np.array([[10.0]])

    @staticmethod
    def step(x, rng):
        a = rng.normal(0.0, 1.0)
        return CarCV.A @ x + CarCV._G[:, 0] * a

    @staticmethod
    def measure(x, rng):
        return CarCV.C @ x + rng.normal(0.0, np.sqrt(10.0), size=1)


# ------------------------------------------------------------------ range-bearing robot


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


class RangeBearing:
    """Planar robot, velocity motion model, one known landmark.

    x = (x, y, θ), u = (v, ω), z = (r, φ). Additive process noise R_proc on x (the book's ch. 3
    assumption; the ch. 5 model puts noise on u instead, which needs the augmented UKF).
    """

    def __init__(self, landmark=(5.0, 3.0), dt=0.1, R_proc=None, Q_meas=None):
        self.m = np.asarray(landmark, dtype=float)
        self.dt = dt
        self.R_proc = np.diag([0.02, 0.02, 0.01]) ** 2 if R_proc is None else np.asarray(R_proc)
        self.Q_meas = np.diag([0.1, np.deg2rad(2.0)]) ** 2 if Q_meas is None else np.asarray(Q_meas)

    # motion g(u, x): eq. 5.9 with the ω→0 limit handled
    def g(self, u, x):
        v, w = u
        x_, y_, th = x
        dt = self.dt
        if abs(w) < 1e-9:
            return np.array([x_ + v * dt * np.cos(th), y_ + v * dt * np.sin(th), th])
        return np.array([
            x_ - v / w * np.sin(th) + v / w * np.sin(th + w * dt),
            y_ + v / w * np.cos(th) - v / w * np.cos(th + w * dt),
            wrap(th + w * dt),
        ])

    # measurement h(x): range and bearing to the landmark
    def h(self, x):
        dx, dy = self.m - x[:2]
        return np.array([np.hypot(dx, dy), wrap(np.arctan2(dy, dx) - x[2])])

    def step(self, x, u, rng):
        return self.g(u, x) + rng.multivariate_normal(np.zeros(3), self.R_proc)

    def measure(self, x, rng):
        z = self.h(x) + rng.multivariate_normal(np.zeros(2), self.Q_meas)
        z[1] = wrap(z[1])
        return z

    def simulate(self, x0, controls, rng):
        xs, zs = [np.asarray(x0, float)], []
        for u in controls:
            xs.append(self.step(xs[-1], u, rng))
            zs.append(self.measure(xs[-1], rng))
        return np.array(xs), np.array(zs)


def figure_eight(n=300, dt=0.1):
    """Controls (v, ω) that drive the robot around a figure-eight; good coverage of θ."""
    t = np.arange(n) * dt
    v = np.full(n, 1.0)
    w = 0.8 * np.sin(2 * np.pi * t / (n * dt) * 2)
    return np.column_stack([v, w])
