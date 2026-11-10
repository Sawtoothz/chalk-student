"""Generate the lecture figures for H&Z ch. 1 in the Chalk style. Run from the repo root or the package:
    python packages/hz-mvg2/ch01-introduction-a-tour-of-multiple-view-geo/figures/make_figures.py

Every number the lecture quotes is printed here and written to figures/numbers.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from viz.py import style  # noqa: E402

OUT = Path(__file__).resolve().parent
P = style.use("light")
R = style.ROLE
rng = np.random.default_rng(7)
NUM: dict = {}


def save(fig, name):
    fig.savefig(OUT / f"{name}.svg")
    fig.savefig(OUT / f"{name}.png", format="png", dpi=110)
    plt.close(fig)


def dehom(x):
    x = np.asarray(x, dtype=float)
    return x[:-1] / x[-1]


def skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])


def look_rotation(z_world, up_hint=np.array([0.0, 0.0, 1.0])):
    """Rows x_c, y_c, z_c in world coordinates; camera z forward, y down."""
    z = z_world / np.linalg.norm(z_world)
    x = np.cross(z, up_hint)
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    return np.vstack([x, y, z])


def camera(K, Rw, C):
    return K @ np.hstack([Rw, (-Rw @ C)[:, None]])


K = np.array([[500.0, 0, 320], [0, 500.0, 240], [0, 0, 1]])
W_IMG, H_IMG = 640, 480

# ------------------------------------------------------------------ L1: rails and the vanishing point
pitch = np.radians(10.0)
h_cam = 1.6
z_c = np.array([np.cos(pitch), 0.0, -np.sin(pitch)])
x_c = np.array([0.0, -1.0, 0.0])
y_c = np.cross(z_c, x_c)
Rw = np.vstack([x_c, y_c, z_c])
Pcam = camera(K, Rw, np.array([0.0, 0.0, h_cam]))
Hg = Pcam[:, [0, 1, 3]]                       # plane Z = 0  ->  image, p. 7
v = Hg @ np.array([1.0, 0.0, 0.0])            # image of the rails' point at infinity
v_px = dehom(v)
l_inf_img = np.linalg.inv(Hg).T @ np.array([0.0, 0.0, 1.0])  # image of the line at infinity
NUM["L1_vanishing_point_px"] = [round(float(c), 2) for c in v_px]
NUM["L1_pitch_deg"] = 10.0
NUM["L1_camera_height_m"] = h_cam

fig, (a0, a1) = plt.subplots(1, 2, figsize=(10.6, 4.1), gridspec_kw={"width_ratios": [1.15, 1]})
X = np.linspace(2.0, 30.0, 200)
for yr in (-0.75, 0.75):
    a0.plot(X, np.full_like(X, yr), color=R["blue"], lw=1.8)
    pts = np.array([dehom(Hg @ np.array([x, yr, 1.0])) for x in np.linspace(2.0, 400.0, 400)])
    a1.plot(pts[:, 0], pts[:, 1], color=R["blue"], lw=1.8)
for xs in np.arange(2.0, 31.0, 2.0):
    a0.plot([xs, xs], [-0.95, 0.95], color=R["gray"], lw=0.8)
    s = np.array([dehom(Hg @ np.array([xs, yy, 1.0])) for yy in (-0.95, 0.95)])
    a1.plot(s[:, 0], s[:, 1], color=R["gray"], lw=0.8)
a0.annotate("", xy=(31.5, 0), xytext=(27, 0), arrowprops=dict(arrowstyle="->", color=R["teal"], lw=1.6))
a0.text(31.8, 0.0, "(1, 0, 0)ᵀ\nat infinity", color=R["teal_deep"], va="center", fontsize=9)
a0.set_xlim(0, 37); a0.set_ylim(-2.2, 2.2)
a0.set_xlabel("X along track [m]"); a0.set_ylabel("Y [m]")
style.fig_label(a0, "Fig L1a · 1.1", "World plane: rails never meet")
xs_line = np.array([0.0, W_IMG])
ys_line = -(l_inf_img[0] * xs_line + l_inf_img[2]) / l_inf_img[1]
a1.plot(xs_line, ys_line, ls="--", color=R["gray"], lw=1.0)
a1.text(8, ys_line[0] - 8, "horizon = H⁻ᵀ(0, 0, 1)ᵀ", color=P["muted"], fontsize=8.5)
a1.plot(*v_px, "o", color=R["teal"], ms=7, mec=P["edge"], mew=0.6)
a1.text(v_px[0] + 12, v_px[1] + 22, f"v = H(1, 0, 0)ᵀ\n= ({v_px[0]:.0f}, {v_px[1]:.0f}) px", color=R["teal_deep"], fontsize=9)
a1.add_patch(plt.Rectangle((0, 0), W_IMG, H_IMG, fill=False, ec=R["gray"], lw=0.8))
a1.set_xlim(-10, W_IMG + 10); a1.set_ylim(H_IMG + 10, -10); a1.set_aspect("equal")
a1.set_xlabel("u [px]"); a1.set_ylabel("v [px]")
style.fig_label(a1, "Fig L1b · 1.1", "Image: the meeting point is a finite pixel")
fig.tight_layout()
save(fig, "L1-point-at-infinity")

# ------------------------------------------------------------------ L2: the ladder
th = np.radians(25)
H_sim = np.array([[0.8 * np.cos(th), -0.8 * np.sin(th), 0.3], [0.8 * np.sin(th), 0.8 * np.cos(th), 0.1], [0, 0, 1]])
H_aff = np.array([[1.2, 0.55, 0.1], [0.1, 0.75, 0.2], [0, 0, 1]])
H_proj = np.array([[1.2, 0.55, 0.1], [0.1, 0.75, 0.2], [0.35, 0.25, 1]])
Ic = np.array([1.0, 1j, 0.0])


def circular_fixed(H):
    y = H @ Ic
    for target in (Ic, np.conj(Ic)):
        if np.linalg.norm(np.cross(y, target)) < 1e-12 * np.linalg.norm(y):
            return True
    return False


def linf_fixed(H):
    l = np.linalg.inv(H).T @ np.array([0.0, 0.0, 1.0])
    return np.linalg.norm(l[:2]) < 1e-12 * abs(l[2])


def tf(H, xy):
    hom = np.c_[xy, np.ones(len(xy))] @ H.T
    return hom[:, :2] / hom[:, 2:]


def ang(u, w):
    return np.degrees(np.arccos(np.clip(u @ w / np.linalg.norm(u) / np.linalg.norm(w), -1, 1)))


fig, axes = plt.subplots(1, 4, figsize=(11.6, 3.7))
t = np.linspace(0, 2 * np.pi, 300)
circ = np.c_[0.5 + 0.5 * np.cos(t), 0.5 + 0.5 * np.sin(t)]
grid_lines = [np.c_[np.full(50, g), np.linspace(0, 1, 50)] for g in np.linspace(0, 1, 5)] + \
             [np.c_[np.linspace(0, 1, 50), np.full(50, g)] for g in np.linspace(0, 1, 5)]
ladder = []
for ax, (name, H) in zip(axes, [("Euclidean frame", np.eye(3)), ("similarity", H_sim),
                                 ("affine", H_aff), ("projective", H_proj)]):
    for gl in grid_lines:
        q = tf(H, gl)
        ax.plot(q[:, 0], q[:, 1], color=R["gray"], lw=0.7)
    q = tf(H, circ)
    ax.plot(q[:, 0], q[:, 1], color=R["teal"], lw=1.8)
    c = tf(H, np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float))
    corner = ang(c[1] - c[0], c[3] - c[0])
    par = ang(c[1] - c[0], c[2] - c[3])
    lf, cf = linf_fixed(H), circular_fixed(H)
    ladder.append(dict(name=name, corner_deg=round(float(corner), 1), opposite_sides_deg=round(float(par), 1),
                       line_at_infinity_fixed=bool(lf), circular_points_fixed=bool(cf)))
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(name, loc="left", fontsize=10.5, color=P["ink"])
    ax.text(0.0, -0.08, f"corner {corner:.1f}°\nopposite sides {par:.1f}° apart\n"
            f"l∞ fixed: {'yes' if lf else 'no'}\ncircular pts fixed: {'yes' if cf else 'no'}",
            transform=ax.transAxes, va="top", fontsize=8.5, family="monospace", color=P["muted"])
NUM["L2_ladder"] = ladder
fig.suptitle("Fig L2 · 1.1.1  Each rung down the ladder loses one invariant: angles, then parallelism",
             x=0.01, ha="left", fontsize=11.5, color=P["ink"])
fig.tight_layout(rect=(0, 0, 1, 0.95))
save(fig, "L2-ladder")

# ------------------------------------------------------------------ L3: when does a homography explain two views?


def normalize2d(x):
    c = x.mean(0)
    s = np.sqrt(2) / np.mean(np.linalg.norm(x - c, axis=1))
    T = np.array([[s, 0, -s * c[0]], [0, s, -s * c[1]], [0, 0, 1]])
    return T


def fit_h(x1, x2):
    T1, T2 = normalize2d(x1), normalize2d(x2)
    a = np.c_[x1, np.ones(len(x1))] @ T1.T
    b = np.c_[x2, np.ones(len(x2))] @ T2.T
    A = []
    for p, q in zip(a, b):
        A.append(np.r_[np.zeros(3), -q[2] * p, q[1] * p])
        A.append(np.r_[q[2] * p, np.zeros(3), -q[0] * p])
    Hn = np.linalg.svd(np.array(A))[2][-1].reshape(3, 3)
    return np.linalg.inv(T2) @ Hn @ T1


def proj(Pm, Xw):
    x = np.c_[Xw, np.ones(len(Xw))] @ Pm.T
    return x[:, :2] / x[:, 2:]


def rms_transfer(x1, x2):
    Hf = fit_h(x1, x2)
    return float(np.sqrt(np.mean(np.sum((tf(Hf, x1) - x2) ** 2, axis=1))))


n_pts = 60
depth_scene = np.c_[rng.uniform(-2, 2, n_pts), rng.uniform(-1.5, 1.5, n_pts), rng.uniform(4, 12, n_pts)]
plane_scene = np.c_[rng.uniform(-3, 3, n_pts), rng.uniform(-2, 2, n_pts), np.zeros(n_pts)]
plane_scene[:, 2] = 7.0 + 0.4 * plane_scene[:, 0] - 0.3 * plane_scene[:, 1]   # a tilted plane
P1 = camera(K, np.eye(3), np.zeros(3))
yaw = np.radians(15.0)
R2 = np.array([[np.cos(yaw), 0, -np.sin(yaw)], [0, 1, 0], [np.sin(yaw), 0, np.cos(yaw)]])
baselines = np.r_[0.0, np.geomspace(1e-3, 1.0, 40)]
res_depth, res_plane = [], []
for b in baselines:
    P2 = camera(K, R2, np.array([b, 0.05 * b, 0.0]))
    res_depth.append(rms_transfer(proj(P1, depth_scene), proj(P2, depth_scene)))
    res_plane.append(rms_transfer(proj(P1, plane_scene), proj(P2, plane_scene)))
NUM["L3_rotation_deg"] = 15.0
NUM["L3_rms_px_pure_rotation_depth_scene"] = float(f"{res_depth[0]:.1e}")
NUM["L3_rms_px_planar_scene_max_over_baselines"] = float(f"{max(res_plane):.1e}")
i10 = int(np.argmin(abs(baselines - 0.1)))
NUM["L3_rms_px_depth_scene_at_baseline_m"] = {f"{baselines[i10]:.3f}": round(res_depth[i10], 2),
                                              f"{baselines[-1]:.3f}": round(res_depth[-1], 2)}
NUM["L3_scene_depth_m"] = [4, 12]
rd = np.array(res_depth[1:]); bl = baselines[1:]
k1 = int(np.argmax(rd >= 1.0))
NUM["L3_baseline_m_where_rms_reaches_1px"] = round(float(np.exp(np.interp(0.0, np.log(rd[k1 - 1:k1 + 1]), np.log(bl[k1 - 1:k1 + 1])))), 3)
NUM["L3_focal_px_image_size"] = [500, 640, 480]

fig, (a0, a1) = plt.subplots(1, 2, figsize=(12.4, 4.8), gridspec_kw={"width_ratios": [1, 1.45]})
# left: top-down slice of Fig. 1.1c, plus the ray of p. 7
C = np.array([0.0, 0.0])
pts2d = np.array([[-1.6, 5.5], [0.4, 8.0], [1.8, 4.5], [-0.6, 10.0]])
for p in pts2d:
    d = p / np.linalg.norm(p)
    a0.plot([0, p[0]], [0, p[1]], color=R["gray"], lw=0.8)
    a0.plot(*p, "o", color=P["ink"], ms=4)
# image plane 1: z = 2 ; image plane 2: rotated line through (0, 2.4)
for (n, c0, role) in [(np.array([0.0, 1.0]), 2.0, "blue"), (np.array([np.sin(0.45), np.cos(0.45)]), 2.6, "coral")]:
    tvec = np.array([n[1], -n[0]])
    base = n * c0
    seg = np.array([base - 2.2 * tvec, base + 2.2 * tvec])
    a0.plot(seg[:, 0], seg[:, 1], color=R[role], lw=2.2)
    for p in pts2d:
        lam = c0 / (n @ p)
        q = lam * p
        a0.plot(*q, "o", color=R[role], ms=4.5, mec=P["edge"], mew=0.5)
# the ray: (X, Y, Z, T) for several T all on one line through C
ray_dir = np.array([0.4, 8.0])
a0.plot([0, ray_dir[0] * 1.6], [0, ray_dir[1] * 1.6], color=R["teal"], lw=1.0, ls="--")
for Tval in (1.0, 0.7, 0.5, 0.4):
    q = ray_dir / Tval
    if q[1] < 13:
        a0.plot(*q, "s", color=R["teal"], ms=4.5)
a0.text(-3.9, 12.0, "(X, Y, Z, T), T varies:\none ray, one image point", color=R["teal_deep"], fontsize=8.5)
a0.plot(0, 0, "o", color=P["ink"], ms=7)
a0.text(0.2, -0.7, "C", fontsize=10)
a0.text(-3.9, 2.35, "image 1", color=R["blue_deep"], fontsize=9)
a0.text(1.2, 0.55, "image 2", color=R["coral_deep"], fontsize=9)
a0.set_xlim(-4, 4); a0.set_ylim(-1.2, 13); a0.set_aspect("equal")
a0.set_xticks([]); a0.set_yticks([])
style.fig_label(a0, "Fig L3a · 1.2, Fig. 1.1c", "Same centre: both planes cut the same rays")
a1.loglog(baselines[1:], res_depth[1:], color=R["teal"], lw=1.8, label="scene with depth (4–12 m)")
a1.loglog(baselines[1:], np.maximum(res_plane[1:], 1e-16), color=R["blue"], lw=1.6, ls="--", label="planar scene")
a1.axhline(1.0, color=R["amber"], lw=0.9, ls=":")
a1.text(1.1e-3, 1.3, "1 px", color=R["amber"], fontsize=8.5)
a1.set_ylim(1e-15, 1e3)
a1.set_xlabel("baseline between the two centres [m]")
a1.set_ylabel("RMS transfer error of best H [px]")
a1.legend(loc="center left", fontsize=8.5)
a1.text(1.1e-3, 1e-13 * 30, f"b = 0, 15° rotation: {res_depth[0]:.0e} px", fontsize=8.5, color=P["muted"])
style.fig_label(a1, "Fig L3b · 1.2, Fig. 1.1c–e", "One H fits both views only if C stays put or the scene is flat")
fig.tight_layout()
save(fig, "L3-cameras-as-points")

# ------------------------------------------------------------------ L4: angles need the IAC


def ray_angle(x1, x2, omega):
    a, b = np.r_[x1, 1.0], np.r_[x2, 1.0]
    c = (a @ omega @ b) / np.sqrt((a @ omega @ a) * (b @ omega @ b))
    return np.degrees(np.arccos(np.clip(c, -1, 1)))


omega_true = np.linalg.inv(K @ K.T)
u = np.linspace(320, 640, 120)
x0 = np.array([320.0, 240.0])
true_ang = np.array([ray_angle(x0, np.array([uu, 240.0]), omega_true) for uu in u])
fig, ax = plt.subplots(figsize=(6.4, 4.3))
ratios = [0.8, 0.9, 1.1, 1.2]
roles = ["coral", "coral", "blue", "blue"]
alphas = [1.0, 0.55, 0.55, 1.0]
err_edge = {}
for r_, role, al in zip(ratios, roles, alphas):
    Ka = K.copy(); Ka[0, 0] = Ka[1, 1] = 500.0 * r_
    om = np.linalg.inv(Ka @ Ka.T)
    meas = np.array([ray_angle(x0, np.array([uu, 240.0]), om) for uu in u])
    ax.plot(true_ang, meas, color=R[role], alpha=al, lw=1.4, label=f"assumed f = {r_:.1f} f")
    err_edge[f"{r_:.1f}"] = round(float(meas[-1] - true_ang[-1]), 2)
ax.plot(true_ang, true_ang, color=R["teal"], lw=2.2, label="ω = (K Kᵀ)⁻¹ correct")
ax.set_xlabel("true angle between rays [°]")
ax.set_ylabel("angle measured from pixels [°]")
ax.legend(fontsize=8.5, loc="upper left")
ax.text(0.98, 0.04, "cos θ = x₁ᵀωx₂ / √(x₁ᵀωx₁ · x₂ᵀωx₂)", transform=ax.transAxes, ha="right",
        fontsize=9, family="monospace", color=P["muted"])
style.fig_label(ax, "Fig L4 · 1.2 calibrated cameras", "Angles between rays come from ω; a wrong f bends every one")
fig.tight_layout()
save(fig, "L4-iac-angles")
NUM["L4_true_angle_at_image_edge_deg"] = round(float(true_ang[-1]), 2)
NUM["L4_angle_error_at_image_edge_deg_by_f_ratio"] = err_edge

# ------------------------------------------------------------------ L5 and L6: the cube family
V = np.array([[x, y, z] for x in (0, 1) for y in (0, 1) for z in (0, 1)], float)
E = [(i, j) for i in range(8) for j in range(i + 1, 8) if np.sum(np.abs(V[i] - V[j])) == 1]
Vh = np.c_[V, np.ones(8)]
C1, C2 = np.array([3.5, -2.5, 2.8]), np.array([-1.5, -3.8, 2.4])
target = np.array([0.5, 0.5, 0.5])
P1c = camera(K, look_rotation(target - C1), C1)
P2c = camera(K, look_rotation(target - C2), C2)


def F_from_P(Pa, Pb):
    Cn = np.linalg.svd(Pa)[2][-1]
    e2 = Pb @ Cn
    Fm = skew(e2) @ Pb @ np.linalg.pinv(Pa)
    Fm /= np.linalg.norm(Fm)
    return Fm * np.sign(Fm.flat[np.argmax(abs(Fm))])


def iso(X3):
    az, el = np.radians(-28), np.radians(35.26)
    Rz = np.array([[np.cos(az), -np.sin(az), 0], [np.sin(az), np.cos(az), 0], [0, 0, 1]])
    x = X3 @ Rz.T
    return np.c_[x[:, 0], x[:, 2] * np.cos(el) - x[:, 1] * np.sin(el)]


th3 = np.radians(30)
Hs = np.eye(4); Hs[:3, :3] = 1.6 * np.array([[np.cos(th3), -np.sin(th3), 0], [np.sin(th3), np.cos(th3), 0], [0, 0, 1]]); Hs[:3, 3] = [0.4, -0.2, 0.3]
Ha = np.eye(4); Ha[:3, :3] = [[1.0, 0.6, 0.1], [0.0, 0.8, 0.0], [0.3, 0.2, 1.4]]
Hp = np.eye(4); Hp[3, 2] = 0.9                               # projective in the Z direction, as Fig. 1.4
F0 = F_from_P(P1c, P2c)
xs_true = [proj(P1c, V), proj(P2c, V)]
fam = []
fig, axes = plt.subplots(1, 4, figsize=(11.6, 3.9))
for ax, (name, H4, role) in zip(axes, [("true", np.eye(4), "gray"), ("similarity", Hs, "blue"),
                                       ("affine", Ha, "blue"), ("projective", Hp, "teal")]):
    Xh = Vh @ H4.T
    X3 = Xh[:, :3] / Xh[:, 3:]
    Hi = np.linalg.inv(H4)
    Pa, Pb = P1c @ Hi, P2c @ Hi
    xa = (Xh @ Pa.T); xa = xa[:, :2] / xa[:, 2:]
    xb = (Xh @ Pb.T); xb = xb[:, :2] / xb[:, 2:]
    dmax = max(np.abs(xa - xs_true[0]).max(), np.abs(xb - xs_true[1]).max())
    dF = np.linalg.norm(F_from_P(Pa, Pb) - F0)
    fam.append(dict(name=name, max_reprojection_change_px=float(f"{dmax:.1e}"), F_change=float(f"{dF:.1e}")))
    q = iso(X3)
    for i, j in E:
        ax.plot(q[[i, j], 0], q[[i, j], 1], color=R[role], lw=1.8)
    ax.plot(q[:, 0], q[:, 1], "o", color=R[role], ms=3.5)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(name, loc="left", fontsize=10.5, color=P["ink"])
    ax.text(0.0, -0.04, f"Δ pixels: {dmax:.0e} px\nΔ F (unit norm): {dF:.0e}", transform=ax.transAxes,
            va="top", fontsize=8.5, family="monospace", color=P["muted"])
NUM["L5_cube_family"] = fam
fig.suptitle("Fig L5 · eq. (1.1)  Four different 'cubes' with cameras P H⁻¹: identical images, identical F",
             x=0.01, ha="left", fontsize=11.5, color=P["ink"])
fig.tight_layout(rect=(0, 0, 1, 0.94))
save(fig, "L5-projective-ambiguity")

# L6: upgrade a projective reconstruction: pi_inf, then Omega_inf from the calibrated camera's omega
Hgen = np.array([[0.9, 0.3, -0.2, 0.1], [0.1, 1.1, 0.25, -0.2], [-0.15, 0.2, 0.8, 0.3], [0.2, -0.15, 0.6, 1.0]])
Xp = Vh @ Hgen.T                                         # projective reconstruction (homogeneous)
assert np.all(Xp[:, 3] > 0)
Pp1, Pp2 = P1c @ np.linalg.inv(Hgen), P2c @ np.linalg.inv(Hgen)
pi = np.linalg.inv(Hgen).T @ np.array([0, 0, 0, 1.0])    # plane at infinity in the projective frame
pi = pi / pi[3]
HA = np.eye(4); HA[3] = pi                               # sends pi to (0,0,0,1)
Xa = Xp @ HA.T
Pa1, Pa2 = Pp1 @ np.linalg.inv(HA), Pp2 @ np.linalg.inv(HA)
Om1 = Pa1[:, :3].T @ omega_true @ Pa1[:, :3]             # back-project omega through the affine camera
Om2 = Pa2[:, :3].T @ omega_true @ Pa2[:, :3]
Om1n, Om2n = Om1 / np.linalg.norm(Om1), Om2 / np.linalg.norm(Om2)
L = np.linalg.cholesky(Om1n)
HM = np.eye(4); HM[:3, :3] = L.T
Xm = Xa @ HM.T
NUM["L6_Omega_agreement_two_views"] = float(f"{np.linalg.norm(Om1n - Om2n):.1e}")


def cube_metrics(Xh):
    X3 = Xh[:, :3] / Xh[:, 3:]
    groups = {0: [], 1: [], 2: []}
    for i, j in E:
        axis = int(np.argmax(np.abs(V[j] - V[i])))
        groups[axis].append(X3[j] - X3[i])
    par = max(ang(g[0], d) for g in groups.values() for d in g[1:])
    corners = []
    for k in range(8):
        nb = [j for i, j in E if i == k] + [i for i, j in E if j == k]
        dirs = [X3[j] - X3[k] for j in nb]
        corners += [ang(dirs[a], dirs[b]) for a in range(3) for b in range(a + 1, 3)]
    lens = [np.linalg.norm(X3[j] - X3[i]) for i, j in E]
    return X3, par, min(corners), max(corners), max(lens) / min(lens)


fig, axes = plt.subplots(1, 3, figsize=(10.4, 4.0))
up = []
for ax, (name, Xh, role, how) in zip(axes, [("projective", Xp, "coral", "from F alone"),
                                             ("affine", Xa, "blue", "after π∞ is sent to (0,0,0,1)"),
                                             ("metric", Xm, "teal", "after Ω∞ = Mᵀ ω M is sent to I")]):
    X3, par, cmin, cmax, lr = cube_metrics(Xh)
    up.append(dict(name=name, max_nonparallel_deg=round(float(par), 2), corner_min_deg=round(float(cmin), 2),
                   corner_max_deg=round(float(cmax), 2), edge_length_ratio=round(float(lr), 3)))
    q = iso(X3 - X3.mean(0))
    for i, j in E:
        ax.plot(q[[i, j], 0], q[[i, j], 1], color=R[role], lw=1.8)
    ax.plot(q[:, 0], q[:, 1], "o", color=R[role], ms=3.5)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(f"{name}  ({how})", loc="left", fontsize=9.5, color=P["ink"])
    ax.text(0.0, -0.04, f"parallel edges off by ≤ {par:.2f}°\ncorners {cmin:.2f}°–{cmax:.2f}°\n"
            f"edge length max/min {lr:.3f}", transform=ax.transAxes, va="top", fontsize=8.5,
            family="monospace", color=P["muted"])
NUM["L6_upgrade"] = up
fig.suptitle("Fig L6 · 1.7  π∞ restores parallel edges; Ω∞ restores right angles and equal lengths",
             x=0.01, ha="left", fontsize=11.5, color=P["ink"])
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "L6-euclidean-upgrade")

(OUT / "numbers.json").write_text(json.dumps(NUM, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(NUM, indent=2, ensure_ascii=False))
