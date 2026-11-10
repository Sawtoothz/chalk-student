"""T4 — Debug. This EKF for the RangeBearing model contains FOUR planted bugs, each one a real bug
from the field. Find and fix them. `pytest exercises/tests/test_T4.py` passes when all four are fixed.

Do not rewrite the file from scratch; the point is to recognise each symptom.
Symptoms you may see before fixing: divergence after a few hundred steps, the heading estimate
flipping by 2π, NEES climbing without bound, Cholesky failures.
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from ..models import wrap


class BrokenEKF:
    def __init__(self, model, mu0, Sigma0):
        self.model = model
        self.mu = np.array(mu0, dtype=float)
        self.Sigma = np.array(Sigma0, dtype=float)
        self._G = None

    def G(self, u, x):
        v, w = u
        th = x[2]
        dt = self.model.dt
        G = np.eye(3)
        if abs(w) < 1e-9:
            G[0, 2] = -v * dt * np.sin(th)
            G[1, 2] = v * dt * np.cos(th)
            return G
        G[0, 2] = -v / w * np.cos(th) + v / w * np.cos(th + w * dt)
        G[1, 2] = v / w * np.sin(th) - v / w * np.sin(th + w * dt)
        return G

    def H(self, x):
        dx, dy = self.model.m - x[:2]
        q = dx * dx + dy * dy
        r = np.sqrt(q)
        return np.array([[-dx / r, -dy / r, 0.0], [dy / q, -dx / q, -1.0]])

    def predict(self, u):
        if self._G is None:
            self._G = self.G(u, self.mu)
        G = self._G
        self.mu = self.model.g(u, self.mu)
        self.Sigma = G @ self.Sigma @ G.T + self.model.R_proc

    def update(self, z):
        H = self.H(self.mu)
        nu = z - self.model.h(self.mu)
        S = H @ self.Sigma @ H.T + self.model.Q_meas
        K = cho_solve(cho_factor(S), H @ self.Sigma).T
        self.mu = self.mu + K @ nu
        self.Sigma = (np.eye(3) - K @ H) @ self.Sigma
        return nu, S
