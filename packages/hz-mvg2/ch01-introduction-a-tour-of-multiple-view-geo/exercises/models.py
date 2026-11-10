"""Shared models for the ch. 1 exercises. Nothing here is an exercise: read it, do not edit it.

Two systems and a small toolbox:

1. `two_view_scene` — the cards' scene (translate.md C6). K with f = 500 px, principal point
   (320, 240), image 640 × 480 px. P1 = K[I | 0] at the origin; P2 at C = (1, 0.1, 0) m with
   R = R_y(−6°) R_x(2°). Points at 4–12 m depth. `F` is the reference fundamental matrix from the
   closed form for P = K[I | 0], P′ = K′[R | t] (§9.2, p. 244), not from anything you implement.

2. `robot_camera` + `floor_and_clutter` — the tracked robot. World frame: X right, Y forward, Z up,
   floor Z = 0. A camera mounted h = 0.55 m above the floor, pitched 15° down, on a robot at
   (x, y) with yaw ψ. This is the scene of Fig. 1.1 (b, c) on a robot: floor points are a plane
   (so two views of them differ by a homography), and a skid turn on the spot keeps the centre
   (Fig. 1.1c: again a homography, whatever the scene). T5 runs on it.

3. Given tools for T5 (chapters 4, 9 and 11 machinery, not chapter 1): `fit_homography`
   (normalized DLT, Algorithm 4.2), `fit_fundamental` (normalized 8-point with rank 2,
   Algorithm 11.1), `essential_candidates` (the four (R, t) of §9.6). You write these yourself in
   the ch. 4 and ch. 11 packages; here they are tools.

Conventions: points are rows (N×3 in ℙ², N×4 in ℙ³); a map acts as `X @ H.T`. H&Z's P = K[R | t]
maps world to camera, t = −R C̃ (eq. 6.8, p. 156). A robot pose is the camera in the world: the
inverse. `robot_camera` does that conversion once.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np

W_PX, H_PX = 640, 480
K_LECTURE = np.array([[500.0, 0.0, 320.0], [0.0, 500.0, 240.0], [0.0, 0.0, 1.0]])
MOUNT_H = 0.55      # m, camera height above the floor
MOUNT_PITCH = 15.0  # deg, camera pitched down


# ------------------------------------------------------------------ basics


def rot(axis: str, deg: float) -> np.ndarray:
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    if axis == "x":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def hom(x) -> np.ndarray:
    """(N, n) → (N, n+1): append a 1 (p. 2, "add an extra coordinate")."""
    x = np.atleast_2d(np.asarray(x, float))
    return np.hstack([x, np.ones((len(x), 1))])


def project(P, Xh) -> np.ndarray:
    """x = P X for rows (p. 7). Homogeneous image points, not divided."""
    return np.atleast_2d(Xh) @ P.T


def pixels(xh) -> np.ndarray:
    """Divide by w. For display and pixel errors only; the points must be finite."""
    xh = np.atleast_2d(xh)
    return xh[:, :2] / xh[:, 2:]


def make_camera(K, R, C_tilde) -> np.ndarray:
    """P = K [R | −R C̃] (eq. 6.8, p. 156). R maps world to camera."""
    C_tilde = np.asarray(C_tilde, float)
    return K @ np.hstack([R, (-R @ C_tilde)[:, None]])


def skew(v) -> np.ndarray:
    return np.array([[0.0, -v[2], v[1]], [v[2], 0.0, -v[0]], [-v[1], v[0], 0.0]])


def normalize_F(F) -> np.ndarray:
    """Unit Frobenius norm, sign fixed so the largest-magnitude entry is positive."""
    F = F / np.linalg.norm(F)
    return F * np.sign(F.flat[np.argmax(np.abs(F))])


def F_reference(K1, K2, R, t) -> np.ndarray:
    """F for P = K1 [I | 0], P′ = K2 [R | t]: F = K2⁻ᵀ [t]× R K1⁻¹ (§9.2, p. 244). Normalized."""
    return normalize_F(np.linalg.inv(K2).T @ skew(t) @ R @ np.linalg.inv(K1))


def in_image(xh, margin=0.0) -> np.ndarray:
    u = pixels(xh)
    return (u[:, 0] >= margin) & (u[:, 0] <= W_PX - margin) & (u[:, 1] >= margin) & (u[:, 1] <= H_PX - margin)


def depth_z(R, C_tilde, Xw) -> np.ndarray:
    """Depth of world points along the optical axis of K[R | −RC̃]. Used to build scenes."""
    return (np.atleast_2d(Xw) - C_tilde) @ R[2]


# ------------------------------------------------------------------ system 1: the cards' scene


def two_view_scene(n: int = 60, seed: int = 1) -> SimpleNamespace:
    rng = np.random.default_rng(seed)
    K = K_LECTURE.copy()
    R1, C1 = np.eye(3), np.zeros(3)
    R2, C2 = rot("y", -6) @ rot("x", 2), np.array([1.0, 0.1, 0.0])
    P1, P2 = make_camera(K, R1, C1), make_camera(K, R2, C2)
    Xw = np.column_stack([rng.uniform(-3, 3, n), rng.uniform(-2, 2, n), rng.uniform(4, 12, n)])
    Xh = hom(Xw)
    x1, x2 = hom(pixels(project(P1, Xh))), hom(pixels(project(P2, Xh)))
    t2 = -R2 @ C2
    return SimpleNamespace(K=K, R1=R1, C1=C1, R2=R2, C2=C2, t2=t2, P1=P1, P2=P2,
                           Xw=Xw, Xh=Xh, x1=x1, x2=x2, F=F_reference(K, K, R2, t2))


# ------------------------------------------------------------------ system 2: the tracked robot


def robot_camera(x=0.0, y=0.0, yaw_deg=0.0, h=MOUNT_H, pitch_deg=MOUNT_PITCH, fwd=0.0, K=K_LECTURE):
    """Camera on a robot at (x, y) on the floor with yaw ψ (CCW from +Y, seen from above).

    The camera sits h above the floor and `fwd` metres ahead of the robot's turning centre.
    Returns (P, R, C̃) with H&Z's R (world → camera). Camera axes: x right, y down, z optical.
    """
    p = np.radians(pitch_deg)
    # camera axes expressed in the robot frame (columns): right, down-ish, forward-down
    R_mount = np.column_stack([[1.0, 0.0, 0.0], [0.0, -np.sin(p), -np.cos(p)], [0.0, np.cos(p), -np.sin(p)]])
    R_wc = rot("z", yaw_deg) @ R_mount           # camera → world
    C_tilde = np.array([x, y, 0.0]) + rot("z", yaw_deg) @ np.array([0.0, fwd, h])
    R = R_wc.T                                   # H&Z: world → camera
    return make_camera(K, R, C_tilde), R, C_tilde


def floor_and_clutter(rng, n_floor=150, n_clutter=150, floor=True, clutter=True) -> tuple[np.ndarray, np.ndarray]:
    """World points (N, 3) and a floor mask. Floor: Z = 0, X ∈ [−4, 4], Y ∈ [1, 9] m.
    Clutter: boxes and shelving, X ∈ [−5, 5], Y ∈ [3, 11], Z ∈ [0.05, 2.0] m."""
    pts, mask = [], []
    if floor:
        pts.append(np.column_stack([rng.uniform(-4, 4, n_floor), rng.uniform(1, 9, n_floor), np.zeros(n_floor)]))
        mask.append(np.ones(n_floor, bool))
    if clutter:
        pts.append(np.column_stack([rng.uniform(-5, 5, n_clutter), rng.uniform(3, 11, n_clutter),
                                    rng.uniform(0.05, 2.0, n_clutter)]))
        mask.append(np.zeros(n_clutter, bool))
    return np.vstack(pts), np.concatenate(mask)


def seen_by(cams, Xw, margin=5.0) -> np.ndarray:
    """Mask of points in front of every camera (≥ 0.5 m) and inside every image."""
    ok = np.ones(len(Xw), bool)
    for P, R, C in cams:
        ok &= depth_z(R, C, Xw) > 0.5
        ok &= in_image(project(P, hom(Xw)), margin)
    return ok


# ------------------------------------------------------------------ given tools for T5


def normalize_pts(x):
    """Algorithm 4.2 normalization: centroid to 0, RMS distance √2. x: (N, 2) pixels. Returns (N×3, T)."""
    x = np.asarray(x, float)
    c = x.mean(axis=0)
    s = np.sqrt(2) / np.sqrt(np.mean(np.sum((x - c) ** 2, axis=1)))
    T = np.array([[s, 0, -s * c[0]], [0, s, -s * c[1]], [0, 0, 1]])
    return hom(x) @ T.T, T


def fit_homography(u1, u2) -> np.ndarray:
    """Normalized DLT (Algorithm 4.2): x2 ~ H x1. u1, u2: (N, 2) pixels, N ≥ 4. Unit Frobenius norm."""
    a, T1 = normalize_pts(u1)
    b, T2 = normalize_pts(u2)
    rows = []
    for (x, y, w), (xp, yp, wp) in zip(a, b):
        X = np.array([x, y, w])
        rows.append(np.concatenate([np.zeros(3), -wp * X, yp * X]))
        rows.append(np.concatenate([wp * X, np.zeros(3), -xp * X]))
    Hn = np.linalg.svd(np.array(rows))[2][-1].reshape(3, 3)
    H = np.linalg.solve(T2, Hn @ T1)
    return H / np.linalg.norm(H)


def fit_fundamental(u1, u2) -> np.ndarray:
    """Normalized 8-point with rank 2 enforced (Algorithm 11.1): x2ᵀ F x1 = 0. N ≥ 8. Normalized F."""
    a, T1 = normalize_pts(u1)
    b, T2 = normalize_pts(u2)
    A = np.einsum("ni,nj->nij", b, a).reshape(len(a), 9)
    Fn = np.linalg.svd(A)[2][-1].reshape(3, 3)
    U, s, Vt = np.linalg.svd(Fn)
    Fn = U @ np.diag([s[0], s[1], 0.0]) @ Vt
    return normalize_F(T2.T @ Fn @ T1)


def essential_candidates(E) -> list[tuple[np.ndarray, np.ndarray]]:
    """The four (R, t) with P′ = [R | t] for E = [t]× R, ‖t‖ = 1 (§9.6). Pick by cheirality."""
    U, _, Vt = np.linalg.svd(E)
    if np.linalg.det(U) < 0:
        U = -U
    if np.linalg.det(Vt) < 0:
        Vt = -Vt
    W = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    t = U[:, 2]
    return [(U @ W @ Vt, t), (U @ W @ Vt, -t), (U @ W.T @ Vt, t), (U @ W.T @ Vt, -t)]
