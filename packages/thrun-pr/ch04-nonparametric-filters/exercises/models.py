"""Shared models for the ch. 4 exercises. Nothing here is an exercise: read it, do not edit it.

Four systems:

1. `RandomWalk1D` — x_t = x_{t-1} + u_t + ε, z_t = x_t + δ. Linear-Gaussian, so the KF of t2.2 is the
   exact posterior: the oracle for the histogram filter and the particle filter (book exercises 1 and 4
   use the ch. 3 car for the same purpose; one dimension keeps a dense grid affordable).

2. `RingCorridor` — the lecture's 10 m ring with doors at 1.5, 4.0, 7.5 m (Fig L2, L11). Binary door
   detector and a range-to-next-door sensor.

3. `Banana` — book exercises 2 and 5 (the ch. 3 exercise 4 system): a robot at the origin with
   unknown heading θ ~ U(−π, π) drives 1 m forward, then measures its x coordinate. The posterior
   over θ has two modes, ±arccos(z).

4. `SymmetricField` — T5. A 9 m × 6 m RoboCup-style field with four identical goalposts and a centre
   spot, placed point-symmetrically. A tracked robot with a velocity motion model sees unlabeled posts by range and
   bearing, so every pose has a mirror twin with the same likelihood.

Conventions: R_proc is motion noise, Q_meas is measurement noise; angles are wrapped with `wrap`.
"""

from __future__ import annotations

import numpy as np


def wrap(a):
    """Wrap angles to [−π, π)."""
    return (np.asarray(a) + np.pi) % (2 * np.pi) - np.pi


def gauss_logpdf(x, mean, std):
    return -0.5 * ((x - mean) / std) ** 2 - np.log(std * np.sqrt(2 * np.pi))


# ------------------------------------------------------------------ 1. random walk


class RandomWalk1D:
    """x_t = x_{t-1} + u_t + N(0, R_proc), z_t = x_t + N(0, Q_meas). Scalars."""

    def __init__(self, R_proc=0.25, Q_meas=0.16, mu0=0.0, var0=1.0):
        self.R_proc, self.Q_meas, self.mu0, self.var0 = R_proc, Q_meas, mu0, var0

    def motion_pdf(self, x_next, u, x_prev):
        return np.exp(gauss_logpdf(x_next, x_prev + u, np.sqrt(self.R_proc)))

    def sample_motion(self, u, X, rng):
        return X + u + rng.normal(0.0, np.sqrt(self.R_proc), size=X.shape)

    def log_lik(self, z, X):
        x = X[:, 0] if X.ndim == 2 else X
        return gauss_logpdf(z, x, np.sqrt(self.Q_meas))

    def simulate(self, controls, rng):
        x = rng.normal(self.mu0, np.sqrt(self.var0))
        xs, zs = [], []
        for u in controls:
            x = x + u + rng.normal(0, np.sqrt(self.R_proc))
            xs.append(x); zs.append(x + rng.normal(0, np.sqrt(self.Q_meas)))
        return np.array(xs), np.array(zs)

    def kf(self, controls, zs):
        """Exact posterior means and variances (the oracle)."""
        m, v, out = self.mu0, self.var0, []
        for u, z in zip(controls, zs):
            m, v = m + u, v + self.R_proc
            k = v / (v + self.Q_meas)
            m, v = m + k * (z - m), (1 - k) * v
            out.append((m, v))
        return np.array(out)


# ------------------------------------------------------------------ 2. ring corridor


class RingCorridor:
    L = 10.0
    DOORS = np.array([1.5, 4.0, 7.5])

    def __init__(self, R_proc=0.3**2, door_sigma=0.25, p_false=0.1, p_peak=0.8, Q_meas=0.1**2):
        self.R_proc, self.door_sigma, self.p_false, self.p_peak, self.Q_meas = R_proc, door_sigma, p_false, p_peak, Q_meas

    def ring_dist(self, a, b):
        d = np.abs(np.asarray(a) - np.asarray(b)) % self.L
        return np.minimum(d, self.L - d)

    def p_door(self, x):
        """p(z = door | x): false-positive floor plus a bump at each door."""
        x = np.asarray(x, float)
        d = self.ring_dist(x[..., None], self.DOORS).min(axis=-1)
        return self.p_false + self.p_peak * np.exp(-0.5 * (d / self.door_sigma) ** 2)

    def motion_pdf(self, x_next, u, x_prev):
        d = self.ring_dist(x_next, np.asarray(x_prev) + u)
        return np.exp(gauss_logpdf(d, 0.0, np.sqrt(self.R_proc)))

    def sample_motion(self, u, X, rng):
        return (X + u + rng.normal(0.0, np.sqrt(self.R_proc), size=X.shape)) % self.L

    def range_to_next_door(self, x):
        return ((self.DOORS - np.asarray(x, float)[..., None]) % self.L).min(axis=-1)

    def log_lik_door(self, z, X):
        x = X[:, 0] if np.ndim(X) == 2 else X
        p = self.p_door(x)
        return np.log(p if z else 1.0 - p)

    def log_lik_range(self, z, X):
        x = X[:, 0] if np.ndim(X) == 2 else X
        return np.logaddexp(gauss_logpdf(z, self.range_to_next_door(x), np.sqrt(self.Q_meas)), np.log(1e-3))


# ------------------------------------------------------------------ 3. banana (book ex. 2, 5)


class Banana:
    """x = (x, y, θ). Start at (0, 0) with θ ~ U(−π, π). Drive d = 1 m: x' = x + d cos θ, y' = y + d sin θ.
    Then measure z = x' + N(0, Q_meas). No motion noise, so the state after the drive is a function of θ."""

    def __init__(self, d=1.0, Q_meas=0.1**2):
        self.d, self.Q_meas = d, Q_meas

    def sample_prior(self, M, rng):
        return np.column_stack([np.zeros(M), np.zeros(M), rng.uniform(-np.pi, np.pi, M)])

    def sample_motion(self, u, X, rng):
        X = X.copy()
        X[:, 0] += u * np.cos(X[:, 2]); X[:, 1] += u * np.sin(X[:, 2])
        return X

    def log_lik(self, z, X):
        return gauss_logpdf(z, X[:, 0], np.sqrt(self.Q_meas))


# ------------------------------------------------------------------ 4. symmetric field (T5)


class SymmetricField:
    """Field [−4.5, 4.5] × [−3, 3]. Posts at (±4.5, ±0.8) and a centre spot at (0, 0), all looking the same
    to the detector: the set is invariant under (x, y, θ) → (−x, −y, θ + π).

    Robot state (x, y, θ); control (v, ω) with the velocity motion model; noise on the control (ch. 5 style):
    v_noisy = v + slip_v, ω_noisy = ω + slip_ω. Sensor: range and bearing to every post within `max_range`
    and the ±`fov` cone (9 m, ±75° by default), unlabeled, padded to 5 rows with NaN.
    """

    POSTS = np.array([[4.5, 0.8], [4.5, -0.8], [-4.5, 0.8], [-4.5, -0.8], [0.0, 0.0]])
    XLIM, YLIM = 4.5, 3.0

    def __init__(self, dt=0.1, max_range=9.0, fov=np.deg2rad(75.0)):
        self.dt, self.max_range, self.fov = dt, max_range, fov

    def move(self, X, v, w):
        """Velocity motion model for arrays X (M, 3), v, w (M,) or scalars."""
        X = np.atleast_2d(X)
        th = X[:, 2]
        w_safe = np.where(np.abs(w) < 1e-9, 1e-9, w)
        out = np.empty_like(X)
        out[:, 0] = X[:, 0] - v / w_safe * np.sin(th) + v / w_safe * np.sin(th + w_safe * self.dt)
        out[:, 1] = X[:, 1] + v / w_safe * np.cos(th) - v / w_safe * np.cos(th + w_safe * self.dt)
        out[:, 2] = wrap(th + w * self.dt)
        return out

    def expected(self, X):
        """Range and bearing from each pose to each landmark: arrays (M, 5)."""
        X = np.atleast_2d(X)
        dx = self.POSTS[None, :, 0] - X[:, None, 0]
        dy = self.POSTS[None, :, 1] - X[:, None, 1]
        return np.hypot(dx, dy), wrap(np.arctan2(dy, dx) - X[:, None, 2])

    def sense(self, x, rng, sigma_r, sigma_b, p_outlier):
        r, b = self.expected(x)
        r, b = r[0], b[0]
        vis = (r < self.max_range) & (np.abs(b) < self.fov)
        z = np.full((len(self.POSTS), 2), np.nan)
        k = 0
        for j in np.flatnonzero(vis):
            if rng.random() < p_outlier:
                z[k] = [rng.uniform(0.3, self.max_range), rng.uniform(-self.fov, self.fov)]
            else:
                z[k] = [r[j] + rng.normal(0, sigma_r), wrap(b[j] + rng.normal(0, sigma_b))]
            k += 1
        return z

    def log_lik(self, z, X, sigma_r, sigma_b, eps=1e-3):
        """Unlabeled detections: each detection is explained by the best-matching post (sum over posts
        of the Gaussian, plus an outlier floor eps). Returns (M,)."""
        r_hat, b_hat = self.expected(X)
        ll = np.zeros(len(np.atleast_2d(X)))
        for zr, zb in z:
            if np.isnan(zr):
                continue
            lr = gauss_logpdf(zr, r_hat, sigma_r) + gauss_logpdf(wrap(zb - b_hat), 0.0, sigma_b)
            ll += np.logaddexp(np.log(eps), -np.log(len(self.POSTS)) + np.logaddexp.reduce(lr, axis=1))
        return ll

    def sample_uniform(self, n, rng, own_half=False):
        x = rng.uniform(-self.XLIM, 0.0 if own_half else self.XLIM, n)
        return np.column_stack([x, rng.uniform(-self.YLIM, self.YLIM, n), rng.uniform(-np.pi, np.pi, n)])

    @staticmethod
    def mirror(X):
        X = np.atleast_2d(X).copy()
        X[:, :2] *= -1; X[:, 2] = wrap(X[:, 2] + np.pi)
        return X


def field_controls(n=400, stop=(150, 200)):
    """(v, ω) for T5: a loop in the own half, a stop, then a sweep across the field."""
    t = np.arange(n)
    v = np.where(t < 150, 0.5, 0.3)
    w = np.where(t < 150, 2 * np.pi / (150 * 0.1), 0.03)
    v[(t >= stop[0]) & (t < stop[1])] = 0.0
    w[(t >= stop[0]) & (t < stop[1])] = 0.0
    return np.column_stack([v, w])
