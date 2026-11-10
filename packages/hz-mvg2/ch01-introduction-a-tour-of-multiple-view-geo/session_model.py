"""Numbers behind the four session figures (session.py and interactive.html).

Every function returns the arrays a figure plots and the readout tiles, computed with the reference
solution in `exercises/solutions/T3_solution.py` and the shared scenes in `exercises/models.py`.
`interactive.html` re-implements the same arithmetic in JS from the data in `scene_data()`;
`compare_session.py` checks the tiles agree on the default settings.

Pass `ex` = the solution module (or the learner's `exercise.py`).
"""

from __future__ import annotations

import numpy as np

from exercises import models
from exercises.models import W_PX, H_PX, hom, pixels, project, robot_camera, two_view_scene

K = models.K_LECTURE
F_PX, CX, CY = K[0, 0], K[0, 2], K[1, 2]

DEFAULTS = {
    "a": dict(pitch=15, gap=1.2, yaw=0),
    "b": dict(s=0.08, u=0.0),
    "c": dict(idx=7, sigma=1.0),
    "d": dict(drive=0.3, turn=10, fwd=0.0),
}


# ------------------------------------------------------------------ formatting shared with the JS


def fx(v: float, d: int) -> str:
    """Fixed decimals, true minus, no negative zero. JS `fx` does the same."""
    r = round(float(v), d)
    if r == 0:
        r = 0.0
    s = f"{abs(r):.{d}f}"
    return ("−" + s) if r < 0 else s


def tiny(v: float, unit: str = "px", tol: float = 1e-6) -> str:
    """Round-off level residuals print as a bound, not as digits that differ between languages."""
    if abs(v) < tol:
        return f"< 1e\u22126 {unit}"
    return f"{fx(v, 3)} {unit}"


# ------------------------------------------------------------------ data the JS port embeds


def scene_data() -> dict:
    sc = two_view_scene()
    rng = np.random.default_rng(11)
    Xw, floor = models.floor_and_clutter(rng, 150, 150)
    noise = np.random.default_rng(2).standard_normal((len(sc.x1), 2))
    return dict(
        K=K.tolist(), W=W_PX, H=H_PX,
        two_view=dict(Xw=sc.Xw.tolist(), C2=sc.C2.tolist(), R2=sc.R2.tolist(), F=sc.F.tolist(), noise=noise.tolist()),
        robot=dict(Xw=Xw.tolist(), floor=floor.astype(int).tolist(), mount_h=models.MOUNT_H),
    )


# ------------------------------------------------------------------ Fig 3.1a: rails and a point at infinity


def fig_a(ex, pitch, gap, yaw):
    P, R, C = robot_camera(pitch_deg=pitch)
    psi = np.radians(yaw)
    d = np.array([np.sin(psi), np.cos(psi), 0.0])
    s = np.linspace(0.3, 80.0, 400)
    rails = []
    for side in (-1, 1):
        X = np.column_stack([side * gap / 2 + s * d[0], s * d[1], np.zeros_like(s)])
        zc = (X - C) @ R[2]
        xh = project(P, hom(X))
        u = xh[:, :2] / xh[:, 2:]
        keep = (zc > 0.05) & (u[:, 0] > -300) & (u[:, 0] < 940) & (u[:, 1] > -200) & (u[:, 1] < 680)
        rails.append((u[keep, 0], u[keep, 1]))
    vh = project(P, np.append(d, 0.0))[0]          # image of the ideal point (d, 0): x = P X, p. 7
    unit = vh / np.linalg.norm(vh)
    at_inf = abs(unit[2]) < 1e-9
    vp = None if at_inf else (float(ex.dehom(vh)[0][0]), float(ex.dehom(vh)[0][1]))
    horizon = CY - F_PX * np.tan(np.radians(pitch))
    inside = vp is not None and 0 <= vp[0] <= W_PX and 0 <= vp[1] <= H_PX
    tiles = {
        "vanishing point (u, v)": "at infinity: w = 0" if at_inf else f"({fx(vp[0], 1)}, {fx(vp[1], 1)}) px",
        "w of x = P (d, 0)ᵀ, scaled to ‖x‖ = 1": fx(unit[2], 4),
        "floor horizon row  v₀ − f tan(pitch)": fx(horizon, 1) + " px",
        "vp row − horizon row (should be 0)": "—" if at_inf else tiny(vp[1] - horizon),
    }
    chip = ("w = 0: still a point at infinity", "bad") if at_inf else (
        ("vanishing point inside the image", "ok") if inside else ("vanishing point outside the image", "warn"))
    return dict(rails=rails, vp=vp, tiles=tiles, chip=chip)


# ------------------------------------------------------------------ Fig 3.1b: eq. (1.1), projective ambiguity


def fig_b(ex, s, u):
    sc = two_view_scene()
    H = np.eye(4)
    H[3, :3] = [u, 0.0, s]                          # H = [[I, 0], [vᵀ, 1]]: the perspective part of eq. (1.1)
    Ps, Xn = ex.apply_ambiguity([sc.P1, sc.P2], sc.Xh, H)
    wraw = sc.Xh @ H[3]                             # the fourth coordinate of H X before any rescaling
    near_inf = np.abs(Xn[:, 3]) < 0.02
    flipped = wraw < 0
    ok = ~near_inf
    XYZ = Xn[ok, :3] / Xn[ok, 3:]
    err = max(np.abs(pixels(project(P, sc.Xh)) - pixels(project(Pn, Xn))).max() for P, Pn in zip((sc.P1, sc.P2), Ps))
    C2h = H @ np.append(sc.C2, 1.0)                 # camera centres move with H too
    C1h = H @ np.array([0, 0, 0, 1.0])
    C1n, C2n = C1h[:3] / C1h[3], C2h[:3] / C2h[3]
    base = float(np.linalg.norm(C2n - C1n))
    d01_true = float(np.linalg.norm(sc.Xw[0] - sc.Xw[1]))
    d01_new = float(np.linalg.norm(Xn[0, :3] / Xn[0, 3] - Xn[1, :3] / Xn[1, 3])) if not (near_inf[0] or near_inf[1]) else float("nan")
    tiles = {
        "max reprojection change, both views": tiny(err),
        "points past the plane at infinity (4th coord < 0)": f"{int(flipped.sum())} of {len(flipped)}",
        "baseline ‖C₂ − C₁‖: true → after H": f"{fx(1.0 * np.linalg.norm(sc.C2), 2)} → {'—' if base != base else fx(base, 2)} m",
        "distance points 0–1: true → after H": f"{fx(d01_true, 2)} → {'—' if d01_new != d01_new else fx(d01_new, 2)} m",
    }
    if s == 0 and u == 0:
        chip = ("H = I: nothing moved", "ok")
    elif flipped.any():
        chip = (f"{int(flipped.sum())} points went through infinity", "warn")
    else:
        chip = ("images unchanged, structure bent", "ok")
    return dict(orig=sc.Xw, new=XYZ, C=(sc.C2, C2n, C1n), dropped=int(near_inf.sum()), tiles=tiles, chip=chip)


# ------------------------------------------------------------------ Fig 3.1c: x′ᵀ F x = 0


def fig_c(ex, idx, sigma):
    sc = two_view_scene()
    noise = np.random.default_rng(2).standard_normal((len(sc.x1), 2))
    xp_all = sc.x2.copy()
    xp_all[:, :2] += sigma * noise
    x, xp = sc.x1[idx], xp_all[idx]
    line = sc.F @ x
    alg = float(xp @ line)
    dist = float(ex.epipolar_distance_px(sc.F, x, xp)[0])
    dists = ex.epipolar_distance_px(sc.F, sc.x1, xp_all)
    e2 = sc.K @ sc.t2
    det = float(np.linalg.det(sc.F))
    foot = xp - (alg / (line[0] ** 2 + line[1] ** 2)) * np.array([line[0], line[1], 0.0])
    tiles = {
        "x′ᵀ F x  (F has ‖F‖ = 1)": fx(alg, 4),
        "distance of x′ to its epipolar line": fx(dist, 3) + " px",
        "median distance, all 60 points": fx(float(np.median(dists)), 3) + " px",
        "|det F|  (rank 2 ⇒ 0)": "< 1e−12" if abs(det) < 1e-12 else fx(det, 3),
        "epipole e′ = K t′": f"({fx(e2[0] / e2[2], 0)}, {fx(e2[1] / e2[2], 0)}) px",
    }
    chip = ("on the line (noise-free)", "ok") if dist < 1e-6 else (
        (f"within 1 px of the line", "ok") if dist < 1.0 else (f"{fx(dist, 1)} px off the line", "warn"))
    return dict(x=sc.x1, xp=xp_all, idx=idx, line=line, foot=foot, tiles=tiles, chip=chip)


# ------------------------------------------------------------------ Fig 3.1d: when one homography is enough


def fig_d(ex, drive, turn, fwd):
    rng = np.random.default_rng(11)
    Xw, floor = models.floor_and_clutter(rng, 150, 150)
    c1 = robot_camera(0.0, 0.0, 0.0, fwd=fwd)
    c2 = robot_camera(0.0, drive, turn, fwd=fwd)
    seen = models.seen_by([c1, c2], Xw)
    P1, R1, C1 = c1
    P2, R2, C2 = c2
    X = hom(Xw[seen])
    fl = floor[seen]
    x1, x2 = project(P1, X), project(P2, X)
    u2 = pixels(x2)
    H_rot = ex.rotation_homography(K, R2 @ R1.T)
    pred = pixels(x1 @ H_rot.T)
    err = np.hypot(*(pred - u2).T)
    H1, H2 = ex.plane_homography(P1), ex.plane_homography(P2)
    H12 = H2 @ np.linalg.inv(H1)
    # floor check: x2 = H12 x1 with H12 = H2 H1⁻¹ built from the plane homographies of P1 and P2 (p. 7)
    floor_err = np.hypot(*(pixels(x1[fl] @ H12.T) - u2[fl]).T)
    base = float(np.linalg.norm(C2 - C1))
    med_f = float(np.median(err[fl]))
    med_c = float(np.median(err[~fl]))
    tiles = {
        "baseline ‖C₂ − C₁‖": fx(base, 3) + " m",
        "floor H transfer error, max": tiny(float(floor_err.max())),
        "rotation-only H, floor median error": fx(med_f, 2) + " px",
        "rotation-only H, clutter median error": fx(med_c, 2) + " px",
        "points seen in both views": f"{int(seen.sum())} ({int(fl.sum())} floor)",
    }
    if base < 1e-9:
        chip = ("pure rotation: one H for every point", "ok")
    elif med_c > 1.0:
        chip = ("parallax: floor is one H, clutter is not", "warn")
    else:
        chip = ("small parallax: H still close", "ok")
    return dict(pred=pred, u2=u2, floor=fl, tiles=tiles, chip=chip)
