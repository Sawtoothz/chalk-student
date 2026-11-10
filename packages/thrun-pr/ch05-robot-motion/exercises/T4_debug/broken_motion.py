"""T4 — Debug. These motion models for a grid or particle filter contain FIVE planted bugs. Each one is
a bug seen in real localization code, and two of them are what the book's tables print.
Find and fix them. `python -m pytest exercises/tests/test_T4.py -q` passes when all five are fixed.

Do not rewrite the file from scratch, and do not copy your exercise.py over it. The point is to
recognise each one from its symptom.

Symptoms reported by the people who ran it:
- "The grid filter's belief refuses to follow the robot through right-hand turns, and loses it
  completely when the robot backs out of a dock."
- "Every weight became NaN the first time the robot stopped at a door."
- "Localization is fine everywhere except when the robot turns through west, heading ±180°. Then the
  belief collapses for one step and recovers."
- "The grid filter (density) and the particle filter (sampler) disagree on the same log by more
  than the sampling error, and the disagreement grows on long straight legs with a small correction."
- "With the noise switched off, dead reckoning from the particle filter does not reproduce the
  odometry it was fed: every turn comes out too sharp."
"""

from __future__ import annotations

import numpy as np

from ..models import wrap

TRANS_EPS = 0.01


def log_prob_normal(a, b2):
    """Table 5.2 line 2 in the log domain."""
    return -0.5 * (np.log(2 * np.pi * b2) + a * a / b2)


# ---------------------------------------------------------------- velocity model (Table 5.1)


def velocity_inverse(X, Xp, dt):
    """Table 5.1 lines 2–9, with the straight-line case handled. X: (3,); Xp: (3,) or (N, 3)."""
    X, Xp = np.asarray(X, dtype=float), np.asarray(Xp, dtype=float)
    x, y, th = X
    xp, yp, tp = Xp[..., 0], Xp[..., 1], Xp[..., 2]
    den = (y - yp) * np.cos(th) - (x - xp) * np.sin(th)
    straight = np.abs(den) < 1e-9
    den_s = np.where(straight, 1.0, den)
    mu = 0.5 * ((x - xp) * np.cos(th) + (y - yp) * np.sin(th)) / den_s          # line 2
    x_s = 0.5 * (x + xp) + mu * (y - yp)                                       # line 3
    y_s = 0.5 * (y + yp) + mu * (xp - x)                                       # line 4
    r_s = np.hypot(x - x_s, y - y_s)                                           # line 5
    dth = wrap(np.arctan2(yp - y_s, xp - x_s) - np.arctan2(y - y_s, x - x_s))  # line 6
    v_h = dth / dt * r_s                                                       # line 7
    w_h = dth / dt                                                             # line 8
    # straight line: the centre is at infinity, v̂ is the signed distance along the heading
    along = (xp - x) * np.cos(th) + (yp - y) * np.sin(th)
    v_h = np.where(straight, along / dt, v_h)
    w_h = np.where(straight, 0.0, w_h)
    g_h = wrap(tp - th - w_h * dt) / dt                                        # line 9
    return v_h, w_h, g_h


def log_motion_model_velocity(Xp, u, X, alpha, dt):
    """Table 5.1 line 10, as a sum of logs."""
    v, w = u
    a1, a2, a3, a4, a5, a6 = alpha
    v_h, w_h, g_h = velocity_inverse(X, Xp, dt)
    return (log_prob_normal(v - v_h, a1 * v * v + a2 * w * w)
            + log_prob_normal(w - w_h, a3 * v * v + a4 * w * w)
            + log_prob_normal(g_h, a5 * v * v + a6 * w * w))


# ---------------------------------------------------------------- odometry model (Tables 5.5, 5.6)


def odometry_params(P0, P1):
    """Eq. 5.34–5.36 with the rotate-in-place rule."""
    P0, P1 = np.asarray(P0, dtype=float), np.asarray(P1, dtype=float)
    dx, dy = P1[..., 0] - P0[..., 0], P1[..., 1] - P0[..., 1]
    trans = np.hypot(dx, dy)
    rot1 = np.where(trans < TRANS_EPS, 0.0, wrap(np.arctan2(dy, dx) - P0[..., 2]))
    rot2 = P1[..., 2] - P0[..., 2] - rot1
    return rot1, trans, rot2


def rot_for_noise(rot):
    return np.minimum(np.abs(rot), np.abs(wrap(rot - np.pi)))


def odometry_variances(rot1, trans, rot2, alpha):
    a1, a2, a3, a4 = alpha
    n1, n2 = rot_for_noise(rot1), rot_for_noise(rot2)
    return (a1 * n1**2 + a2 * trans**2,
            a3 * trans**2 + a4 * (n1**2 + n2**2),
            a1 * n2**2 + a2 * trans**2)


def log_motion_model_odometry(Xp, u, X, alpha):
    """Table 5.5 in the log domain. Xp: (3,) or (N, 3); u = (odom_prev, odom_now); X: (3,)."""
    rot1, trans, rot2 = odometry_params(*u)
    h_rot1, h_trans, h_rot2 = odometry_params(X, Xp)
    b1, b2, b3 = odometry_variances(h_rot1, h_trans, h_rot2, alpha)
    return (log_prob_normal(wrap(rot1 - h_rot1), b1)
            + log_prob_normal(trans - h_trans, b2)
            + log_prob_normal(rot2 - h_rot2, b3))


def sample_motion_model_odometry(u, X, alpha, rng):
    """Table 5.6 for M particles. Returns a new (M, 3) array."""
    rot1, trans, rot2 = odometry_params(*u)
    b1, b2, b3 = odometry_variances(rot1, trans, rot2, alpha)
    Y = np.array(X, dtype=float)
    M = Y.shape[0]
    h_rot1 = rot1 - rng.normal(size=M) * np.sqrt(b1)
    h_trans = trans - rng.normal(size=M) * np.sqrt(b2)
    h_rot2 = rot2 - rng.normal(size=M) * np.sqrt(b3)
    Y[:, 2] = wrap(Y[:, 2] + h_rot1 + h_rot2)
    Y[:, 0] += h_trans * np.cos(Y[:, 2] + h_rot1)
    Y[:, 1] += h_trans * np.sin(Y[:, 2] + h_rot1)
    return Y
