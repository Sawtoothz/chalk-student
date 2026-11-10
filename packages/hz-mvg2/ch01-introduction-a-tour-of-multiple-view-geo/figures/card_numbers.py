"""Execute every Python block of translate.md, check naive against robust and against oracles,
and write every number the cards quote to card_numbers.json.

Run: python3 figures/card_numbers.py   (from the package dir or anywhere)
"""
import json
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CARDS = HERE.parent / "translate.md"
OUT = HERE / "card_numbers.json"

blocks = re.findall(r"```python\n(.*?)```", CARDS.read_text(), flags=re.S)
ns: dict = {}
for i, b in enumerate(blocks):
    try:
        exec(compile(b, f"translate.md:block{i}", "exec"), ns)
    except Exception as e:  # pragma: no cover
        raise SystemExit(f"block {i} failed: {e!r}\n{b}")
g = type("NS", (), ns)  # attribute access to the cards' functions
print(f"executed {len(blocks)} python blocks")

rng = np.random.default_rng(1)
NUM: dict = {}
ok = lambda cond, msg: (_ for _ in ()).throw(AssertionError(msg)) if not cond else None


def rot(axis, deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    if axis == "x":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


K = np.array([[500.0, 0, 320], [0, 500.0, 240], [0, 0, 1]])

# ---------------- C1 ----------------
x = np.array([3.0, -2.0])
ok(np.allclose(g.dehom(g.hom(x))[0], g.dehom_naive(g.hom_naive(x))), "C1 hom/dehom")
ok(g.at_infinity(np.array([1e-13, 1e-13, 1e-13])).item() is False, "C1 scale-free finite")
ok(g.at_infinity(np.array([1.0, 2.0, 1e-17])).item() is True, "C1 scale-free infinite")
ok(g.same_point(np.array([1.0, 2.0, 1.0]), np.array([-2.0, -4.0, -2.0])), "C1 same point")
Hs = [np.eye(3) + rng.standard_normal((3, 3)) for _ in range(500)]
raw = np.eye(3)
with np.errstate(over="ignore", invalid="ignore"):
    for H in Hs:
        raw = H @ raw
comp = g.compose(*Hs)
NUM["c1_chain_log10_max_raw"] = int(np.floor(np.log10(np.max(np.abs(raw)))))
ok(abs(np.linalg.norm(comp) - 1) < 1e-12, "C1 compose unit norm")
ok(np.allclose(comp, raw / np.linalg.norm(raw), atol=1e-9) or np.allclose(comp, -raw / np.linalg.norm(raw), atol=1e-9),
   "C1 compose direction")

# ---------------- C2 ----------------
a, b, r = 2.0, -1.0, 3.0
C = g.circle_conic(a, b, r)
for pt in (g.I_PT, g.J_PT):
    ok(abs(g.conic_eval(C, pt)) < 1e-14 and abs(g.circle_form_naive(pt, a, b, r)) < 1e-14, "C2 circular points")
NUM["c2_bilinear_at_I"] = float(abs(g.conic_eval(C, g.I_PT)))
NUM["c2_hermitian_at_I"] = float(np.real(np.vdot(g.I_PT, C @ g.I_PT)))
for _ in range(20):  # naive form == matrix form on random real points
    p = rng.standard_normal(3)
    ok(abs(g.circle_form_naive(p, a, b, r) - g.conic_eval(C, p)) < 1e-10, "C2 matrix form")
Hc = np.eye(3) + 0.3 * rng.standard_normal((3, 3))
Cp = g.conic_transform(C, Hc)
pts = []
for t in np.linspace(0, 2 * np.pi, 7)[:-1]:  # points on the circle map onto C'
    q = Hc @ np.array([a + r * np.cos(t), b + r * np.sin(t), 1.0])
    ok(abs(q @ Cp @ q) / (q @ q) < 1e-12, "C2 conic transform")
d1, d2 = rng.standard_normal(3), rng.standard_normal(3)
d2p = d2 - (d2 @ d1) / (d1 @ d1) * d1
ok(g.perpendicular(3 * d1, 0.1 * d2p), "C2 perpendicular scale-free")
ok(abs(g.conjugacy(d1, d2) - d1 @ d2 / np.linalg.norm(d1) / np.linalg.norm(d2)) < 1e-14, "C2 conjugacy = cosine")

# ---------------- C3 ----------------
R1, C1t = rot("y", 0), np.zeros(3)
P1 = g.make_camera(K, R1, C1t)
R2 = rot("y", -6) @ rot("x", 2)
C2t = np.array([1.0, 0.1, 0.0])
P2 = g.make_camera(K, R2, C2t)
Cc = g.camera_centre(P2)
ok(np.allclose(Cc[:3] / Cc[3], C2t), "C3 centre")
Xw = np.column_stack([rng.uniform(-3, 3, 60), rng.uniform(-2, 2, 60), rng.uniform(4, 12, 60)])
Xh = g.hom(Xw)
ok(np.allclose(g.dehom(g.project(P1, Xh))[0], g.project_naive(P1, Xh[0])), "C3 naive = robust")
for k in (0.3, -2.0, 7.0):  # ray test: (X, Y, Z, T) with T varying -> same pixel under [I|0]
    ok(np.allclose(g.dehom(g.project(g.P0_naive, np.array([1.0, 2.0, 3.0, k]))), [[1 / 3, 2 / 3]]), "C3 ray")
ok(np.allclose(g.depth(P1, Xh), Xw[:, 2]), "C3 depth")
ok(np.all(g.depth(P1, -Xh) > 0), "C3 depth sign-invariant")
ok(np.all(g.depth(P1, g.hom(-Xw)) < 0), "C3 behind")

# ---------------- C4 ----------------
Pg = g.make_camera(K, rot("x", -100), np.array([0.0, -2.0, 1.6]))  # looks along +y, pitched down, 1.6 m up
Hp = g.plane_homography(Pg)
XYp = np.column_stack([rng.uniform(-3, 3, 20), rng.uniform(2, 20, 20)])
a_ = g.dehom(g.project(Pg, np.column_stack([XYp, np.zeros(20), np.ones(20)])))
b_ = g.dehom(g.apply_homography(Hp, g.hom(XYp)))
ok(np.allclose(a_, b_), "C4 plane H")
ok(np.allclose(g.plane_homography_naive(Pg) / np.linalg.norm(Pg[:, [0, 1, 3]]), Hp), "C4 naive")
Rr = rot("y", 15)
Hr = g.rotation_homography(K, Rr)
ok(np.allclose(Hr, g.rotation_homography_naive(K, Rr) / np.linalg.norm(g.rotation_homography_naive(K, Rr))), "C4 rot naive")
x1 = g.project(P1, Xh)
x2 = g.project(g.make_camera(K, Rr, C1t), Xh)
ok(g.transfer_rms_px(Hr, x1, x2) < 1e-9, "C4 same-centre H")

# ---------------- C5 ----------------
def H_with_cond(c):
    U, _, Vt = np.linalg.svd(rng.standard_normal((4, 4)))
    return U @ np.diag(np.geomspace(1, 1 / c, 4)) @ Vt

Ps = [P1, P2]
for c, key in ((1e1, "c5_maxpx_cond1e1"), (1e8, "c5_maxpx_cond1e8")):
    H = H_with_cond(c)
    Pn, Xn = g.apply_ambiguity(Ps, Xh, H)
    NUM[key] = float(f"{g.max_reprojection_change_px(Ps, Xh, Pn, Xn):.1e}")
Pn_naive, Xn_naive = g.apply_ambiguity_naive(Ps, Xh, H_with_cond(10))
H = np.eye(4); H[3] = [0, 0, 1 / 8.0, -0.5]  # sends plane Z = 4 to infinity: splits the 4..12 m scene
flags = g.crosses_infinity(Xh, H)
ok(np.array_equal(flags, (Xw[:, 2] < 4) != (np.median(Xw[:, 2]) < 4)), "C5 crosses infinity")

# ---------------- C6 ----------------
F = g.F_from_cameras(P1, P2)
x1, x2 = g.project(P1, Xh), g.project(P2, Xh)
x1, x2 = x1 / x1[:, 2:], x2 / x2[:, 2:]
ok(np.max(g.epipolar_distance_px(F, x1, x2)) < 1e-9, "C6 epipolar")
ok(abs(g.epipolar_residual_naive(F, x1[0], x2[0])) < 1e-9, "C6 naive")
ok(abs(g.F_row_naive(x1[0], x2[0]) @ F.ravel() - x2[0] @ F @ x1[0]) < 1e-9, "C6 row")
ok(np.allclose(g.F_design(x1, x2) @ F.ravel(), np.einsum("ni,ij,nj->n", x2, F, x1)), "C6 design")
NUM["c6_rank2_gap_exact"] = float(f"{g.rank2_gap(F):.1e}")
try:
    g.F_from_cameras(P1, g.make_camera(K, Rr, C1t)); ok(False, "C6 same centre should raise")
except ValueError:
    pass
n1 = x1.copy(); n2 = x2.copy()
n1[:, :2] += rng.standard_normal((60, 2)); n2[:, :2] += rng.standard_normal((60, 2))
NUM["c6_alg_median"] = float(f"{np.median(np.abs(np.einsum('ni,ij,nj->n', n2, F, n1))):.2g}")
NUM["c6_dist_median_px"] = round(float(np.median(g.epipolar_distance_px(F, n1, n2))), 2)
s_raw = np.linalg.svd(g.F_design(x1, x2), compute_uv=False)
m1, _ = g.normalize_pts(x1); m2, _ = g.normalize_pts(x2)
s_norm = np.linalg.svd(g.F_design(m1, m2), compute_uv=False)
NUM["c6_condA_raw"] = float(f"{s_raw[0] / s_raw[7]:.1e}")
NUM["c6_condA_norm"] = float(f"{s_norm[0] / s_norm[7]:.0f}")

# ---------------- C7 ----------------
errs = []
for i in range(len(Xh)):
    Xt = g.triangulate([P1, P2], [x1[i], x2[i]])
    Xn_ = g.triangulate_naive(P1, P2, x1[i], x2[i])
    Xtrue = Xh[i] / np.linalg.norm(Xh[i])
    errs.append(min(np.linalg.norm(Xt - Xtrue), np.linalg.norm(Xt + Xtrue)))
    ok(g.same_point(Xn_, Xtrue, 1e-8), "C7 naive")
    g.triangulate_checked([P1, P2], [x1[i], x2[i]])
NUM["c7_noisefree_max_err"] = float(f"{max(errs):.0e}")
P3 = g.make_camera(K, rot("y", 8), np.array([-1.0, 0.0, 0.5]))
ok(np.allclose(g.dehom(g.transfer(P3, g.triangulate([P1, P2], [x1[0], x2[0]]))),
               g.dehom(g.project(P3, Xh[0]))), "C7 transfer")
# point at infinity on the optical axis of camera 1 (T = 0): a star, a vanishing point
Xinf = np.array([0.0, 0.0, 1.0, 0.0])
xf1, xf2 = g.project(P1, Xinf)[0], g.project(P2, Xinf)[0]
xf1, xf2 = xf1 / xf1[2], xf2 / xf2[2]
angle = lambda u, v: np.degrees(np.arctan2(np.linalg.norm(np.cross(u, v)), u @ v))
Xh_inf = g.triangulate([P1, P2], [xf1, xf2])
NUM["c7_inf_hom_T_over_norm"] = float(f"{abs(Xh_inf[3]):.0e}")
NUM["c7_inf_hom_dir_err_deg"] = float(f"{min(angle(Xh_inf[:3], Xinf[:3]), angle(-Xh_inf[:3], Xinf[:3])):.0e}")
A = np.array([xf1[0] * P1[2] - P1[0], xf1[1] * P1[2] - P1[1], xf2[0] * P2[2] - P2[0], xf2[1] * P2[2] - P2[1]])
xyz = np.linalg.lstsq(A[:, :3], -A[:, 3], rcond=None)[0]  # inhomogeneous method: X = (X, Y, Z, 1)
res_inhom = np.linalg.norm(A[:, :3] @ xyz + A[:, 3]) / np.linalg.norm(A)
NUM["c7_inf_inhom_range_m"] = float(f"{np.linalg.norm(xyz):.2g}")
NUM["c7_inf_inhom_resid"] = float(f"{res_inhom:.1e}")
reps = []
for i in range(len(Xh)):
    Xt = g.triangulate([P1, P2], [n1[i], n2[i]])
    for P, xx in ((P1, n1[i]), (P2, n2[i])):
        y = P @ Xt
        reps.append(np.hypot(*(y[:2] / y[2] - xx[:2])))
NUM["c7_noisy_median_reproj_px"] = round(float(np.median(reps)), 2)

# ---------------- C8 ----------------
om = g.omega_naive(K)
xa, xb = np.array([320.0, 240.0, 1.0]), np.array([640.0, 240.0, 1.0])
ok(abs(g.ray_angle(K, xa, xb)[0] - g.ray_angle_naive(xa, xb, om)) < 1e-12, "C8 naive = robust")
ok(abs(np.degrees(g.ray_angle(K, xa, xb)[0]) - 32.62) < 0.005, "C8 lecture edge angle")
ok(abs(g.ray_angle_omega(xa, xb, 7.3 * om) - g.ray_angle(K, xa, xb)[0]) < 1e-12, "C8 omega scale")
NUM["c8_cond_KKt"] = float(f"{np.linalg.cond(K @ K.T):.1e}")
NUM["c8_cond_K"] = float(f"{np.linalg.cond(K):.1e}")
# 1 px apart near the image edge, in float32 (an embedded board) and float64
xs1, xs2 = np.array([600.0, 240.0, 1.0]), np.array([601.0, 240.0, 1.0])
true = np.arctan2(601 - 320, 500) - np.arctan2(600 - 320, 500)  # same row, principal row: exact difference
NUM["c8_small_true_urad"] = round(true * 1e6, 2)
f32 = np.float32
K32, om32 = K.astype(f32), om.astype(f32)
a32, b32 = xs1.astype(f32), xs2.astype(f32)
c32 = (a32 @ om32 @ b32) / np.sqrt((a32 @ om32 @ a32) * (b32 @ om32 @ b32))
NUM["c8_small_arccos_f32_urad"] = round(float(np.arccos(np.clip(c32, f32(-1), f32(1)))) * 1e6, 2)
d1_ = np.linalg.solve(K32, a32).astype(f32); d2_ = np.linalg.solve(K32, b32).astype(f32)
NUM["c8_small_atan2_f32_urad"] = round(float(np.arctan2(np.linalg.norm(np.cross(d1_, d2_)), d1_ @ d2_)) * 1e6, 2)
NUM["c8_small_atan2_f64_urad"] = round(float(g.ray_angle(K, xs1, xs2)[0]) * 1e6, 2)

# ---------------- C9 ----------------
pi_bad = np.array([0.3, -0.5, 0.8, 1e-14]); pi_bad /= np.linalg.norm(pi_bad)
NUM["c9_cond_eq102"] = float(f"{np.linalg.cond(g.affine_upgrade_naive(pi_bad)):.0e}")
Hh = g.affine_upgrade(pi_bad)
NUM["c9_cond_householder"] = round(float(np.linalg.cond(Hh)), 3)
e = np.linalg.solve(Hh.T, pi_bad)
ok(np.allclose(e[:3], 0, atol=1e-12), "C9 Householder maps pi to e4")
# full chain: projective -> affine -> metric on the C6 scene
Hproj = H_with_cond(20)
Pp, Xp = g.apply_ambiguity([P1, P2], Xh, Hproj)
pi = np.linalg.solve(Hproj.T, np.array([0, 0, 0, 1.0]))  # plane at infinity in the projective frame: H^-T e4
for HA in (g.affine_upgrade_naive(pi / pi[3]), g.affine_upgrade(pi)):
    Pa, Xa = g.upgrade(Pp, Xp, HA)
    ok(np.allclose(np.linalg.solve(HA.T, pi)[:3] / np.linalg.norm(np.linalg.solve(HA.T, pi)), 0, atol=1e-9), "C9 HA")
    M = Pa[0][:, :3]
    Hm = g.metric_upgrade(M, om)
    Hm_naive = g.metric_upgrade_naive(M, om)
    Pm, Xm = g.upgrade(Pa, Xa, Hm)
    Mm = Pm[0][:, :3]
    W = Mm @ Mm.T
    ok(np.allclose(W / W[2, 2], K @ K.T / (K @ K.T)[2, 2], atol=1e-8), "C9 M_M M_M^T ~ K K^T")
    Pm2, _ = g.upgrade(Pa, Xa, Hm_naive)
    W2 = Pm2[0][:, :3] @ Pm2[0][:, :3].T
    ok(np.allclose(W2 / W2[2, 2], W / W[2, 2], atol=1e-8), "C9 naive = robust")
    Pm3, _ = g.upgrade(Pa, Xa, g.metric_upgrade(M, -3 * om))
    W3 = Pm3[0][:, :3] @ Pm3[0][:, :3].T
    ok(np.allclose(W3 / W3[2, 2], W / W[2, 2], atol=1e-8), "C9 omega sign and scale")

OUT.write_text(json.dumps(NUM, indent=2) + "\n")
print(json.dumps(NUM, indent=2))
print("all card checks passed")
