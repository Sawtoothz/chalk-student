"""T4 — Debug. This ESKF on SE(2) with beacons (§V-A, p. 12) contains FOUR planted bugs, each one a real bug from
the field. Find and fix them. `pytest exercises/tests/test_T4.py` passes when all four are fixed.

Do not rewrite the file from scratch, and do not import your exercise.py: the point is to recognise each symptom
and to find the line that causes it.

Symptoms you may see before fixing:
- NaN in the pose and in P as soon as the robot drives straight;
- the filter is fine while the robot is near the origin facing +x, and drifts off once it has turned and moved away;
- P that grows the wrong way through a turn, then NEES far above 3;
- a heading that converges and a position that does not, with beacons that are only ever seen from one side.

Conventions as in translate.md: right ⊕, τ = (ρ₁, ρ₂, θ), R_proc = the paper's W (93), Q_meas = its N (96).
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import cho_factor, cho_solve

J1 = np.array([[0.0, -1.0], [1.0, 0.0]])


class BrokenESKF:
    def __init__(self, X0, P0, R_proc, Q_meas):
        self.X = np.array(X0, dtype=float)
        self.P = np.array(P0, dtype=float)
        self.R_proc = np.asarray(R_proc, float)
        self.Q_meas = np.asarray(Q_meas, float)

    # ------------------------------------------------------------ SE(2) blocks (App. C)

    @staticmethod
    def exp(tau):                                           # (156), V(θ) of (158)
        r, th = tau[:2], tau[2]
        c, s = np.cos(th), np.sin(th)
        V = np.array([[s / th, -(1 - c) / th], [(1 - c) / th, s / th]])
        M = np.eye(3)
        M[:2, :2] = [[c, -s], [s, c]]
        M[:2, 2] = V @ r
        return M

    @staticmethod
    def Ad(M):                                              # (159)
        A = np.eye(3)
        A[:2, :2] = M[:2, :2]
        A[:2, 2] = -J1 @ M[:2, 2]
        return A

    @staticmethod
    def Jr(tau):                                            # (163), third column without cancellation
        r1, r2, th = tau
        h = th / 2
        A = np.sinc(th / np.pi)                             # sin θ / θ
        a = 0.5 * np.sinc(h / np.pi) ** 2                   # (1 − cos θ)/θ²
        b = (th - np.sin(th)) / th ** 3 if abs(th) > 0.3 else 1 / 6 - th ** 2 / 120 + th ** 4 / 5040
        B = th * a
        return np.array([[A, B, r1 * th * b - r2 * a],
                         [-B, A, r1 * a + r2 * th * b],
                         [0.0, 0.0, 1.0]])

    # ------------------------------------------------------------ the filter

    def F(self, u):                                         # (100): J of X ⊕ u with respect to X, (80)
        return self.Ad(self.exp(u))

    def G(self, u):                                         # (100): J of X ⊕ u with respect to u, (81)
        return self.Jr(u)

    def expect(self, b):                                    # (95): e = X⁻¹·b, and H = J^e_X
        R, t = self.X[:2, :2], self.X[:2, 2]
        d = b - t
        e = R.T @ d
        H = -np.hstack([np.eye(2), (R @ J1 @ d)[:, None]])
        return e, H

    def predict(self, u):                                   # (99)-(100)
        F, G = self.F(u), self.G(u)
        self.X = self.X @ self.exp(u)
        P = F @ self.P @ F.T + G @ self.R_proc @ G.T
        self.P = 0.5 * (P + P.T)

    def update(self, y, b):                                 # (101)-(102), Joseph form; returns (z, Z)
        e, H = self.expect(b)
        z = y - e
        Z = H @ self.P @ H.T + self.Q_meas
        K = cho_solve(cho_factor(Z), H @ self.P).T
        dx = K @ z
        IKH = np.eye(3) - K @ H
        P = IKH @ self.P @ IKH.T + K @ self.Q_meas @ K.T
        self.X = self.exp(dx) @ self.X
        self.P = 0.5 * (P + P.T)
        return z, Z
