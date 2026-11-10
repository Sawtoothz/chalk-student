"""Shared models for the micro-Lie-theory exercises. Nothing here is an exercise: read it, do not edit it.

Everything in this file is built on `scipy.linalg.expm` / `logm` of the hat matrix, not on closed forms, so it is
independent of the code you write in `exercise.py` and the tests can use it as an oracle.

Conventions (as in the paper and `translate.md`):
- right perturbations, X ⊕ τ = X Exp(τ);
- SE(2) tangent τ = (ρ₁, ρ₂, θ), translation first (153);
- the paper's control noise W (93) is `R_proc`, its measurement noise N (96) is `Q_meas`;
- a pose is stored as a 3×3 homogeneous matrix; `pose(x, y, th)` and `xyth(M)` convert.

Two systems:

1. `SectionV` — the setup of §V (p. 12) as manif's `examples/se2_localization.cpp` builds it: three beacons at
   (2, 0), (2, 1), (2, −1), constant control u = (0.1, 0, 0.05) per step, beacons measured in the body frame
   y = X⁻¹·b + n (95). Gaussian noise (manif's example draws uniform noise, see `implementation.md`), and the control
   noise a tenth of the example's, where a first-order filter is consistent (`translate.md` C8).

2. `TrackedRobot` — a skid-steer / tracked base driving a lap through a yard of AprilTags at surveyed positions.
   Track odometry gives ũ = (v δt, 0, ω δt); the true increment adds noise on all three components, including the
   lateral slip u_s of (92)–(93), which is not zero on tracks. Tags are seen only within `max_range` and only in
   front of the robot. This is the T5 system.
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import expm, logm

J1 = np.array([[0.0, -1.0], [1.0, 0.0]])          # [1]x of (155)


def wrap(a):
    """Wrap an angle (or array of angles) to [−π, π)."""
    return (np.asarray(a) + np.pi) % (2 * np.pi) - np.pi


# ------------------------------------------------------------------ hat / vee (given, not exercises)


def so3_hat(w):
    """[w]x, Ex. 3."""
    return np.array([[0.0, -w[2], w[1]], [w[2], 0.0, -w[0]], [-w[1], w[0], 0.0]])


def so3_vee(W):
    return np.array([W[2, 1], W[0, 2], W[1, 0]])


def se2_hat(tau):
    """τ^ ∈ se(2), (153): [[[θ]x, ρ], [0, 0]]."""
    return np.array([[0.0, -tau[2], tau[0]], [tau[2], 0.0, tau[1]], [0.0, 0.0, 0.0]])


def se2_vee(T):
    return np.array([T[0, 2], T[1, 2], T[1, 0]])


def pose(x, y, th):
    c, s = np.cos(th), np.sin(th)
    return np.array([[c, -s, x], [s, c, y], [0.0, 0.0, 1.0]])


def xyth(M):
    return np.array([M[0, 2], M[1, 2], np.arctan2(M[1, 0], M[0, 0])])


# ------------------------------------------------------------------ reference Exp / Log (oracles, slow)


def so3_Exp_ref(theta):
    return expm(so3_hat(theta))


def so3_Log_ref(R):
    return so3_vee(np.real(logm(R)))


def se2_Exp_ref(tau):
    return expm(se2_hat(tau))


def se2_Log_ref(M):
    """Valid for |θ| < π (logm picks the principal logarithm)."""
    return se2_vee(np.real(logm(M)))


def se2_inv_ref(M):
    return np.linalg.inv(M)


def se2_rplus_ref(X, tau):
    return X @ se2_Exp_ref(tau)


def se2_rminus_ref(Y, X):
    return se2_Log_ref(np.linalg.inv(X) @ Y)


def se2_Ad_ref(M):
    """(31): column i is (M E_i M⁻¹)^v. The generic adjoint, used only as an oracle."""
    Mi = np.linalg.inv(M)
    return np.column_stack([se2_vee(M @ se2_hat(e) @ Mi) for e in np.eye(3)])


def se2_Jr_ref(tau, eps=1e-6):
    """Right Jacobian of SE(2) by central differences of definition (41a), with expm/logm."""
    X = se2_Exp_ref(tau)
    J = np.zeros((3, 3))
    for j in range(3):
        d = np.zeros(3); d[j] = eps
        J[:, j] = (se2_rminus_ref(se2_Exp_ref(tau + d), X) - se2_rminus_ref(se2_Exp_ref(tau - d), X)) / (2 * eps)
    return J


def random_pose(rng, spread=3.0):
    return pose(*rng.uniform(-spread, spread, 2), rng.uniform(-np.pi, np.pi))


def random_spd(rng, n, scale=1.0):
    A = rng.normal(size=(n, n))
    return scale * (A @ A.T / n + 0.2 * np.eye(n))


# ------------------------------------------------------------------ system 1: the setup of §V


class SectionV:
    """§V (p. 12) with manif's numbers: beacons (2, 0), (2, 1), (2, −1); u = (0.1, 0, 0.05) per step.

    R_proc = diag(σ_u²) with σ_u = 0.01 (a tenth of manif's 0.1), Q_meas = diag(0.01²) (manif's 1 cm).
    """

    beacons = np.array([[2.0, 0.0], [2.0, 1.0], [2.0, -1.0]])
    u_nom = np.array([0.1, 0.0, 0.05])

    def __init__(self, sigma_u=0.01, sigma_y=0.01):
        self.R_proc = np.diag([sigma_u] * 3) ** 2
        self.Q_meas = np.diag([sigma_y] * 2) ** 2

    def simulate(self, n, rng, X0=None):
        """Return (Xs, us, ys): true poses (n+1, 3, 3), noisy controls ũ (n, 3) given to the filter, and beacon
        measurements ys (n, 3, 2), one per beacon per step, taken at the pose after the step."""
        X = np.eye(3) if X0 is None else X0.copy()
        Xs, us, ys = [X], [], []
        Lu = np.linalg.cholesky(self.R_proc)
        Ly = np.linalg.cholesky(self.Q_meas)
        for _ in range(n):
            w = Lu @ rng.normal(size=3)
            X = X @ se2_Exp_ref(self.u_nom)            # the true increment is u_nom
            us.append(self.u_nom + w)                  # the filter is told ũ = u + w, w ~ N(0, R_proc)
            Xi = np.linalg.inv(X)
            ys.append([(Xi @ np.r_[b, 1.0])[:2] + Ly @ rng.normal(size=2) for b in self.beacons])
            Xs.append(X)
        return np.array(Xs), np.array(us), np.array(ys)


def fig12_problem(rng, noise=True):
    """The smoothing-and-mapping problem of Fig. 12 (p. 12): three poses, three beacons, factors
    {1, 12, 23, 14, 15, 25, 26, 36} in the paper's 1-based labels: a prior on X₁, motion 1→2 and 2→3, and beacon
    factors (pose, beacon) = (1, 4), (1, 5), (2, 5), (2, 6), (3, 6).

    Returns a dict with the truth, 0-based factor lists, the noise covariances and a perturbed initial guess.
    Motion factors carry u_ij = X_j ⊖ X_i (+ noise); beacon factors carry y = X_i⁻¹·b_k (+ noise).
    """
    sec = SectionV(sigma_u=0.01, sigma_y=0.01)
    poses = [np.eye(3)]
    for _ in range(2):
        poses.append(poses[-1] @ se2_Exp_ref(np.array([1.0, 0.0, 0.5])))
    lmks = [np.array([2.0, 0.0]), np.array([2.0, 1.0]), np.array([2.0, -1.0])]
    P0 = np.diag([0.01, 0.01, 0.01]) ** 2
    Lu, Ly = np.linalg.cholesky(sec.R_proc), np.linalg.cholesky(sec.Q_meas)
    k = 1.0 if noise else 0.0
    motions = [(i, i + 1, se2_rminus_ref(poses[i + 1], poses[i]) + k * Lu @ rng.normal(size=3)) for i in range(2)]
    pairs = [(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)]
    beacons = [(i, j, (np.linalg.inv(poses[i]) @ np.r_[lmks[j], 1.0])[:2] + k * Ly @ rng.normal(size=2))
               for i, j in pairs]
    prior = poses[0].copy()
    init_poses = [X @ se2_Exp_ref(rng.normal(0, 0.1, 3)) for X in poses]
    init_lmks = [b + rng.normal(0, 0.1, 2) for b in lmks]
    return dict(poses=poses, lmks=lmks, prior=prior, P0=P0, R_proc=sec.R_proc, Q_meas=sec.Q_meas,
                motions=motions, beacons=beacons, init_poses=init_poses, init_lmks=init_lmks)


# ------------------------------------------------------------------ system 2: tracked robot in a tag yard


def figure_eight_controls(n, dt=0.1, v=0.5, w_max=0.6):
    """Odometry increments ũ = (v δt, 0, ω δt) for a figure-eight lap; ω crosses zero (straight segments)."""
    t = np.arange(n) * dt
    w = w_max * np.sin(2 * np.pi * t / (n * dt) * 2)
    w[np.abs(w) < 0.05] = 0.0                     # straight segments: θ = ω δt is exactly zero there
    return np.column_stack([np.full(n, v * dt), np.zeros(n), w * dt])


class TrackedRobot:
    """Tracked base, track odometry as control, AprilTags at surveyed positions as beacons (§V-A on a real yard).

    The true increment is u = ũ + w, w ~ N(0, R_proc); the middle component of w is the lateral slip u_s of (92).
    Tag detections are positions in the body frame, y = X⁻¹·b + n, n ~ N(0, Q_meas), kept only if the tag is
    within `max_range` and inside a ±`fov`/2 cone ahead.
    """

    def __init__(self, tags=None, R_proc=None, Q_meas=None, dt=0.1, max_range=5.0, fov=np.deg2rad(120)):
        if tags is None:                          # a 4 x 3 grid of tags over a 9 m x 7 m yard
            tags = [[x, y] for x in (-4.5, -1.5, 1.5, 4.5) for y in (-3.5, 0.0, 3.5)]
        self.tags = np.asarray(tags, float)
        self.dt = dt
        self.R_proc = np.diag([0.01, 0.005, 0.004]) ** 2 if R_proc is None else np.asarray(R_proc)
        self.Q_meas = np.diag([0.05, 0.05]) ** 2 if Q_meas is None else np.asarray(Q_meas)
        self.max_range = max_range
        self.fov = fov
        self.X0 = pose(-3.0, 1.0, 0.0)            # start pose: the figure-eight then stays inside the yard

    def visible(self, X):
        """Indices of tags the camera sees from pose X."""
        p = (np.linalg.inv(X) @ np.column_stack([self.tags, np.ones(len(self.tags))]).T)[:2].T
        r = np.hypot(p[:, 0], p[:, 1])
        bearing = np.arctan2(p[:, 1], p[:, 0])
        return np.flatnonzero((r < self.max_range) & (np.abs(bearing) < self.fov / 2) & (r > 0.3))

    def simulate(self, U, rng, X0=None):
        """Return (Xs, Y, mask): true poses (n+1, 3, 3), detections Y (n, n_tags, 2) and a boolean mask
        (n, n_tags) of which tags were seen at step k (after the k-th motion)."""
        X = self.X0.copy() if X0 is None else X0.copy()
        Lu, Ly = np.linalg.cholesky(self.R_proc), np.linalg.cholesky(self.Q_meas)
        nt = len(self.tags)
        Xs, Y, mask = [X], np.zeros((len(U), nt, 2)), np.zeros((len(U), nt), bool)
        for k, u in enumerate(U):
            X = X @ se2_Exp_ref(u + Lu @ rng.normal(size=3))
            Xi = np.linalg.inv(X)
            for j in self.visible(X):
                Y[k, j] = (Xi @ np.r_[self.tags[j], 1.0])[:2] + Ly @ rng.normal(size=2)
                mask[k, j] = True
            Xs.append(X)
        return np.array(Xs), Y, mask
