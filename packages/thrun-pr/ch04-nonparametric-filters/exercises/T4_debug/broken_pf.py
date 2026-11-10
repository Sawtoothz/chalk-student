"""T4 — Debug. This particle filter contains FOUR planted bugs, each one seen in real MCL code.
Find and fix them. `pytest exercises/tests/test_T4.py` passes when all four are fixed.

Do not rewrite the file from scratch; the point is to recognise each symptom.
Symptoms you may see before fixing: an IndexError or a resampled set made of the first few particles,
NaN estimates as soon as the sensor model gets realistic, the filter forgetting a measurement it took
one step ago, and a robot facing ±180° reported as facing 0°.
"""

from __future__ import annotations

import numpy as np
from scipy.special import logsumexp

from ..models import wrap


class BrokenPF:
    """Particles X (M, n), weights carried across steps (4.36), resampling on N_eff < neff_frac · M.
    `sample_motion(u, X, rng)` and `log_lik(z, X)` as in exercise.py; `angle_idx` lists heading columns."""

    def __init__(self, X, sample_motion, log_lik, rng, neff_frac=0.5, angle_idx=()):
        self.X = np.array(X, dtype=float)
        self.M = len(self.X)
        self.w = np.full(self.M, 1.0 / self.M)
        self.sample_motion, self.log_lik, self.rng = sample_motion, log_lik, rng
        self.neff_frac, self.angle_idx = neff_frac, tuple(angle_idx)

    def resample(self, w):
        """Table 4.4. Returns indices."""
        M = len(w)
        r = self.rng.uniform(0.0, 1.0 / M)
        c = w[0]
        i = 0
        idx = np.empty(M, dtype=int)
        for m in range(M):
            U = r + m / M
            while U > c:
                i += 1
                c += w[i]
            idx[m] = i
        return idx

    def step(self, u, z):
        self.X = self.sample_motion(u, self.X, self.rng)                 # line 4
        for j in self.angle_idx:
            self.X[:, j] = wrap(self.X[:, j])
        self.w = np.exp(self.log_lik(z, self.X))                         # line 5
        self.w /= self.w.sum()
        n_eff = 1.0 / np.sum(self.w**2)
        if n_eff < self.neff_frac * self.M:
            idx = self.resample(self.w * self.M)
            self.X = self.X[idx]
            self.w = np.full(self.M, 1.0 / self.M)
        return n_eff

    def estimate(self):
        """Weighted mean and covariance of the particle set."""
        w = self.w / self.w.sum()
        mu = w @ self.X
        D = self.X - mu
        for j in self.angle_idx:
            D[:, j] = wrap(D[:, j])
        cov = (D * w[:, None]).T @ D / (1.0 - np.sum(w**2))
        return mu, cov
