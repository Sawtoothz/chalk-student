#!/usr/bin/env python3
"""Run every code block of translate.md and recompute every number the cards quote.

    python3 packages/thrun-pr/ch05-robot-motion/figures/card_checks.py

1. Executes the ```python blocks of translate.md in order, in one namespace.
2. Compiles the ```cpp blocks together with a small main (g++, Eigen) and compares its output with the Python.
3. Checks every robust card function against the reference exercises/solutions/T3_solution.py on random
   inputs, so the cards and the gated solution cannot drift apart.
4. Computes the numbers quoted in the cards, writes figures/card_numbers.json, and fails if a quoted string
   is missing from translate.md. Numbers that the cards take from the lecture are read from numbers.json.

Holds no model code of its own beyond Table 5.1 lines 2-7 as printed (book_vhat). It imports the solution,
so read it after T3.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parents[2]
sys.path.insert(0, str(ROOT))
from scripts.fd_check import numeric_jacobian  # noqa: E402

sys.path.insert(0, str(PKG))
from exercises.solutions import T3_solution as ref  # noqa: E402

MD = (PKG / "translate.md").read_text()
LECT = json.loads((HERE / "numbers.json").read_text())

ns: dict = {}
for block in re.findall(r"```python\n(.*?)```", MD, flags=re.S):
    exec(compile(block, "translate.md", "exec"), ns)
g = type("NS", (), ns)  # attribute access to the card functions
wrap = ns["wrap"]

OUT: dict = {}
QUOTED: list[str] = []
FAIL: list[str] = []


def quote(s: str):
    QUOTED.append(s)


def sci(x: float, d: int = 1) -> str:
    """1.3e-11 -> '1.3 × 10⁻¹¹' as written in the cards."""
    sup = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    m, e = f"{x:.{d}e}".split("e")
    return f"{m} × 10{str(int(e)).translate(sup)}"


rng = np.random.default_rng(5)
np.seterr(all="ignore")

# ------------------------------------------------------------------ cards == reference solution
def _same(name, a, b, tol=1e-12):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.shape != b.shape or not np.allclose(a, b, atol=tol, rtol=tol, equal_nan=True):
        FAIL.append(f"card {name} disagrees with T3_solution")


_r = np.random.default_rng(42)
_X = np.column_stack([_r.uniform(-3, 3, 500), _r.uniform(-3, 3, 500), _r.uniform(-np.pi, np.pi, 500)])
_x0 = np.array([0.3, -0.2, 0.9])
_av, _ao, _dt = (0.02, 0.02, 0.02, 0.02, 0.005, 0.005), (0.05, 0.01, 0.05, 0.01), 0.7
_aa, _bb = _r.normal(0, 1, 500), _r.uniform(0.0, 2.0, 500)
_same("log_prob_normal", g.log_prob_normal(_aa, _bb), ref.log_prob(_aa, _bb))
_same("log_prob_triangular", g.log_prob_triangular(_aa, _bb), ref.log_prob(_aa, _bb, "triangular"))
_same("rot_for_noise", g.rot_for_noise(_X[:, 2]), ref.rot_for_noise(_X[:, 2]))
_vw = (_r.uniform(-2, 2, 500), _r.uniform(-1.5, 1.5, 500) * _r.choice([1, 1e-9, 0], 500), _r.uniform(-0.3, 0.3, 500))
_same("velocity_forward", g.velocity_forward(_X, *_vw, _dt), ref.velocity_forward(_X, *_vw, _dt))
_same("velocity_inverse", g.velocity_inverse(_x0, _X, _dt), ref.velocity_inverse(_x0, _X, _dt), tol=1e-9)
for _pd in (False, True):
    _same(f"log_motion_model_velocity(pose_density={_pd})", g.log_motion_model_velocity(_X, (1.0, 0.8), _x0, _av, _dt, pose_density=_pd),
          ref.log_motion_model_velocity(_X, (1.0, 0.8), _x0, _av, _dt, pose_density=_pd), tol=1e-9)
_P1 = _X + _r.normal(0, 0.5, _X.shape)
_same("odometry_params", g.odometry_params(_X, _P1), ref.odometry_params(_X, _P1))
for _u in [(np.zeros(3), np.array([1.5, 1.0, 1.2])), (np.zeros(3), np.array([-0.5, 0.0, 0.0])), (np.zeros(3), np.array([0.0, 0.0, 2.8]))]:
    for _pd in (False, True):
        _same(f"log_motion_model_odometry(pose_density={_pd})", g.log_motion_model_odometry(_X, _u, _x0, _ao, pose_density=_pd),
              ref.log_motion_model_odometry(_X, _u, _x0, _ao, pose_density=_pd), tol=1e-9)
    _same("sample_motion_model_odometry", g.sample_motion_model_odometry(_u, _X, _ao, np.random.default_rng(1)),
          ref.sample_motion_model_odometry(_u, _X, _ao, np.random.default_rng(1)))
_same("sample_motion_model_velocity", g.sample_motion_model_velocity((1.0, 0.8), _X, _av, _dt, np.random.default_rng(2)),
      ref.sample_motion_model_velocity((1.0, 0.8), _X, _av, _dt, np.random.default_rng(2)))
_free = lambda X: np.asarray(X)[..., 0] < 1.0
_cs = lambda u_, X, r_: g.sample_motion_model_velocity(u_, X, _av, 1.0, r_)
_rs = lambda u_, X, r_: ref.sample_motion_model_velocity(u_, X, _av, 1.0, r_)
_c = g.sample_motion_model_with_map((1.0, 0.0), np.zeros((300, 3)), _cs, _free, np.random.default_rng(3))
_d = ref.sample_motion_model_with_map((1.0, 0.0), np.zeros((300, 3)), _rs, _free, np.random.default_rng(3))
_same("sample_motion_model_with_map (poses)", _c[0], _d[0]); _same("sample_motion_model_with_map (weights)", _c[1], _d[1])
OUT["cards_vs_reference"] = "agree" if not any("T3_solution" in f for f in FAIL) else "DISAGREE"

# ------------------------------------------------------------------ C1
k = 30.0
while g.prob_normal_naive(k, 1.0) > 0:
    k = round(k + 0.1, 1)
OUT["C1_prob_normal_zero_at_sigma"] = k
quote(f"{k} b")
OUT["C1_naive_density_at_rest"] = str(g.prob_normal_naive(np.zeros(1), np.zeros(1))[0])
assert np.isnan(g.prob_normal_naive(np.zeros(1), np.zeros(1))[0])
try:
    g.prob_normal_naive(0.0, 0.0); raise AssertionError("expected ZeroDivisionError")
except ZeroDivisionError:
    pass
assert np.isfinite(g.log_prob_normal(0.0, 0.0))
N = 1_000_000
r = np.random.default_rng(0)
t = time.perf_counter()
for _ in range(5):
    0.5 * r.uniform(-1, 1, (N, 12)).sum(-1)
t12 = time.perf_counter() - t
t = time.perf_counter()
for _ in range(5):
    r.normal(0, 1, N)
tn = time.perf_counter() - t
OUT["C1_speedup_rng_normal_vs_12_uniforms"] = round(t12 / tn, 1)
quote("about 7× faster")
if not 6.0 <= t12 / tn <= 8.0:
    print(f"warning: timing ratio now {t12 / tn:.1f}x, the card says about 7x (timings vary)")
for name, s in [("normal", g.sample_normal), ("triangular", g.sample_triangular)]:
    var = s(4.0, rng, 400_000).var()
    assert abs(var - 4.0) < 0.05, (name, var)
    assert np.all(s(0.0, rng, 3) == 0)
# triangular density integrates to 1, normal log = log of naive
a = np.linspace(-4, 4, 200_001)
assert abs(np.exp(g.log_prob_triangular(a, 1.0)).sum() * (a[1] - a[0]) - 1) < 1e-4
assert np.allclose(g.log_prob_normal(a, 2.0), np.log(g.prob_normal_naive(a, 2.0)))

# ------------------------------------------------------------------ C2
x0 = (2.0, -1.0, 0.7)


def fwd_ref(x0, v, w, dt):
    x, y, th = (np.longdouble(c) for c in x0)
    v, w, dt = np.longdouble(v), np.longdouble(w), np.longdouble(dt)
    h = w * dt / 2
    sc = np.sin(h) / h if h != 0 else np.longdouble(1)
    return x + v * dt * sc * np.cos(th + h), y + v * dt * sc * np.sin(th + h)


zero_a = (0,) * 6
book_err, chord_err = {}, {}
for w in [1e-6, 1e-9, 1e-12, 0.0]:
    xr, yr = fwd_ref(x0, 1.0, w, 1.0)
    pb = g.sample_motion_model_velocity_naive((1.0, np.float64(w)), x0, zero_a, 1.0, rng)
    pc = g.velocity_forward(np.array(x0), 1.0, w, 0.0, 1.0)
    book_err[w] = float(max(abs(pb[0] - xr), abs(pb[1] - yr)))
    chord_err[w] = float(max(abs(pc[0] - xr), abs(pc[1] - yr)))
OUT["C2_book_form_err_m"] = {str(k): v for k, v in book_err.items()}
OUT["C2_chord_form_err_m"] = {str(k): v for k, v in chord_err.items()}
assert np.isnan(book_err[0.0])
assert max(chord_err.values()) < 2e-16
quote("below 2 × 10⁻¹⁶ m")
quote(sci(book_err[1e-9]) + " m")
# chord form equals the book's form away from w = 0
pb = g.sample_motion_model_velocity_naive((1.0, 0.8), x0, zero_a, 2.0, rng)
assert np.allclose(pb[:2], g.velocity_forward(np.array(x0), 1.0, 0.8, 0.0, 2.0)[:2], atol=1e-14)
# sampler: vectorized output shape, wrapped heading, noise-free limit
Xs = g.sample_motion_model_velocity((1.0, 0.8), np.tile(x0, (1000, 1)), (0.02,) * 4 + (0.005,) * 2, 2.0, rng)
assert Xs.shape == (1000, 3) and np.all(np.abs(Xs[:, 2]) <= np.pi)

# ------------------------------------------------------------------ C3
o = np.zeros(3)


def book_vhat(x, xp):
    """Table 5.1 lines 2-7, copied from the naive card, returning v_hat."""
    (x_, y, th), (xp_, yp, _) = x, xp
    mu = 0.5 * ((x_ - xp_) * np.cos(th) + (y - yp) * np.sin(th)) / ((y - yp) * np.cos(th) - (x_ - xp_) * np.sin(th))
    xs, ys = (x_ + xp_) / 2 + mu * (y - yp), (y + yp) / 2 + mu * (xp_ - x_)
    rs = np.hypot(x_ - xs, y - ys)
    dth = np.arctan2(yp - ys, xp_ - xs) - np.arctan2(y - ys, x_ - xs)
    lam = (ys - y) * np.cos(th) - (xs - x_) * np.sin(th)
    return dth * rs, lam * dth   # dt = 1


cases = [(1.0, -0.5), (-1.0, 0.5), (1.0, 0.5)]
vb, vc, vl = [], [], []
for v, w in cases:
    xp = g.velocity_forward(o, v, w, 0.0, 1.0)
    b, lam = book_vhat(o, xp)
    vb.append(round(float(b), 3)); vl.append(round(float(lam), 3))
    vc.append(round(float(g.velocity_inverse(o, xp, 1.0)[0]), 3))
OUT["C3_line7_vhat"] = vb; OUT["C3_chord_vhat"] = vc; OUT["C3_lambda_patch_vhat"] = vl
assert vb == [-1.0, 1.0, 1.0] and vc == [1.0, -1.0, 1.0] and vl == vc
quote("v̂ = −1.0, 1.0 and 1.0 m/s"); quote("1.0, −1.0 and 1.0 m/s")
assert vb == LECT["L5"]["book_line7_vhat_for_(1,-0.5)_(-1,0.5)_(1,0.5)"]
a_mod = (0.02, 0.02, 0.02, 0.02, 0.005, 0.005)
xp = g.velocity_forward(o, 1.0, -0.5, 0.0, 1.0)
lr = np.log(g.motion_model_velocity_naive(xp, (1.0, -0.5), o, a_mod, 1.0)) - g.log_motion_model_velocity(xp, (1.0, -0.5), o, a_mod, 1.0)
OUT["C3_log_ratio_book_vs_fixed_right_turn"] = round(float(lr), 2)
quote("e⁻" + str(round(-float(lr))).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")))
# straight line
xp0 = g.velocity_forward(o, 1.0, 0.0, 0.0, 1.0)
assert np.isnan(g.motion_model_velocity_naive(xp0, (1.0, 0.0), o, a_mod, 1.0))
assert np.isfinite(g.log_motion_model_velocity(xp0, (1.0, 0.0), o, a_mod, 1.0))
xp9 = g.velocity_forward(o, 1.0, 1e-9, 0.0, 1.0)
rel9 = abs(book_vhat(o, xp9)[0] - 1.0)
OUT["C3_book_vhat_rel_err_at_w_1e-9"] = float(rel9)
quote(sci(rel9) + " relative")
# round trip
worst, n = 0.0, 0
while n < 20_000:
    v = rng.uniform(-2, 2); w = rng.uniform(-1.5, 1.5) * rng.choice([1, 1e-6, 0]); gm = rng.uniform(-0.3, 0.3)
    dt = rng.uniform(0.05, 2.0)
    if abs(w * dt) >= 0.98 * np.pi or abs(v) < 1e-3:
        continue
    X = np.array([rng.uniform(-5, 5), rng.uniform(-5, 5), rng.uniform(-np.pi, np.pi)])
    e = np.array(g.velocity_inverse(X, g.velocity_forward(X, v, w, gm, dt), dt)) - [v, w, gm]
    worst = max(worst, float(np.abs(e).max())); n += 1
OUT["C3_round_trip_worst"] = worst
assert worst < 1e-10
quote(sci(worst) + " over 20 000 random cases")
# Jacobian determinant against fd_check's central differences
worst = 0.0
for _ in range(10):
    X = rng.uniform(-3, 3, 3); dt = rng.uniform(0.1, 1.5)
    nz = np.array([rng.uniform(-2, 2), rng.uniform(-1.5, 1.5), rng.uniform(-0.3, 0.3)])
    Jn = numeric_jacobian(lambda m: g.velocity_forward(X, m[0], m[1], m[2], dt), nz, wrap_rows=(2,))
    d = abs(np.linalg.det(Jn)); an = g.velocity_jacobian_det(nz[0], nz[1], dt)
    worst = max(worst, abs(d - an) / an)
OUT["C3_jacdet_rel_err"] = worst
assert worst < 1e-7
quote(sci(worst) + " relative over ten random cases")
# with the Jacobian the pose density integrates to 1 (grid over x', y', theta')
av, uv, dtv = a_mod, (1.0, 0.8), 2.0
xs_ = np.linspace(-0.6, 2.8, 121); ys_ = np.linspace(-0.3, 3.0, 121); ts_ = np.linspace(-np.pi, np.pi, 241, endpoint=False)
XX, YY, TT = np.meshgrid(xs_, ys_, ts_, indexing="ij")
P = np.stack([XX, YY, TT], -1)
cell = (xs_[1] - xs_[0]) * (ys_[1] - ys_[0]) * (ts_[1] - ts_[0])
mass_v = float(np.exp(g.log_motion_model_velocity(P, uv, o, av, dtv, pose_density=True)).sum() * cell)
OUT["C3_pose_density_mass"] = round(mass_v, 4)
assert abs(mass_v - 1) < 0.02, mass_v
quote(f"integrates to {mass_v:.4f}")

# ------------------------------------------------------------------ C4
a_odo = (0.01, 0.0005, 0.01, 0.0005)       # lecture L7
M = 100_000


def vec_sample(b2, rng_):
    return rng_.normal(0.0, 1.0, M) * np.sqrt(b2)


# rotation in place, 30 deg at theta_bar = 150 deg
ob0 = np.array([0.0, 0.0, np.deg2rad(150)]); ob1 = np.array([0.0, 0.0, np.deg2rad(180)])
rot1_book = np.arctan2(0.0, 0.0) - ob0[2]
Xb = g.sample_motion_model_odometry_naive((ob0, ob1), (0.0, 0.0, 0.0), a_odo, rng, sample=vec_sample)
Xr = g.sample_motion_model_odometry((ob0, ob1), np.zeros((M, 3)), a_odo, rng)
sb, sr = float(wrap(Xb[2] - np.pi / 6).std()), float(wrap(Xr[:, 2] - np.pi / 6).std())
OUT["C4_inplace_rot1_book_deg"] = round(float(np.rad2deg(rot1_book)), 1)
OUT["C4_inplace_heading_std_book_rad"] = round(sb, 3); OUT["C4_inplace_heading_std_robust_rad"] = round(sr, 3)
quote(f"δrot1 = −{abs(np.rad2deg(rot1_book)):.1f}°"); quote(f"{sb:.3f} rad"); quote(f"{sr:.3f} rad, the same at any θ̄")
# independent of the frame heading
Xr2 = g.sample_motion_model_odometry((np.array([1, 2, -1.0]), np.array([1, 2, -1.0 + np.pi / 6])), np.zeros((M, 3)), a_odo, rng)
assert abs(wrap(Xr2[:, 2] - np.pi / 6).std() - sr) < 0.002
# reversing 0.5 m
ob0 = np.zeros(3); ob1 = np.array([-0.5, 0.0, 0.0]); ob1f = np.array([0.5, 0.0, 0.0])
Xb = g.sample_motion_model_odometry_naive((ob0, ob1), (0.0, 0.0, 0.0), a_odo, rng, sample=vec_sample)
Xr = g.sample_motion_model_odometry((ob0, ob1), np.zeros((M, 3)), a_odo, rng)
Xf = g.sample_motion_model_odometry((ob0, ob1f), np.zeros((M, 3)), a_odo, rng)
sb, sr, sf = (float(wrap(z).std()) for z in (Xb[2], Xr[:, 2], Xf[:, 2]))
OUT["C4_reverse_heading_std_rad"] = {"book": round(sb, 4), "robust": round(sr, 4), "forward": round(sf, 4)}
quote(f"{sb:.3f} rad with the book's variances"); quote(f"{sr:.4f} rad with `rot_for_noise`"); quote(f"0.5 m forward ({sf:.4f} rad)")
# Jacobian det = trans
worst = 0.0
for _ in range(10):
    X = rng.uniform(-3, 3, 3); nz = np.array([rng.uniform(-1, 1), rng.uniform(0.1, 2), rng.uniform(-1, 1)])
    f = lambda m: np.array([X[0] + m[1] * np.cos(X[2] + m[0]), X[1] + m[1] * np.sin(X[2] + m[0]), X[2] + m[0] + m[2]])
    Jn = numeric_jacobian(f, nz)
    worst = max(worst, abs(abs(np.linalg.det(Jn)) - nz[1]) / nz[1])
OUT["C4_jacdet_rel_err"] = worst
assert worst < 1e-7
quote(sci(worst) + " relative over ten random cases")
# robust density with Jacobian integrates to 1; with all-forward data it agrees with the naive density up to the
# variance choice; the robust sampler reproduces the odometry displacement when alpha = 0
ao = (0.05, 0.01, 0.05, 0.01); u = (np.zeros(3), np.array([1.5, 1.0, np.deg2rad(70)]))
xs_ = np.linspace(0.0, 3.0, 121); ys_ = np.linspace(-0.5, 2.5, 121)
XX, YY, TT = np.meshgrid(xs_, ys_, ts_, indexing="ij")
P = np.stack([XX, YY, TT], -1)
cell = (xs_[1] - xs_[0]) * (ys_[1] - ys_[0]) * (ts_[1] - ts_[0])
mass_o = float(np.exp(g.log_motion_model_odometry(P, u, o, ao, pose_density=True)).sum() * cell)
OUT["C4_pose_density_mass"] = round(mass_o, 4)
assert abs(mass_o - 1) < 0.02, mass_o
quote(f"integrates to {mass_o:.4f}")
X0 = np.array([[1.0, -2.0, 2.5]])
moved = g.sample_motion_model_odometry(u, X0, (0, 0, 0, 0), rng)[0]
rot = X0[0, 2] - u[0][2]
want = [X0[0, 0] + np.cos(rot) * 1.5 - np.sin(rot) * 1.0, X0[0, 1] + np.sin(rot) * 1.5 + np.cos(rot) * 1.0, wrap(X0[0, 2] + np.deg2rad(70))]
assert np.allclose(moved, want, atol=1e-12)

# ------------------------------------------------------------------ C5
free = lambda X: np.asarray(X)[..., 0] < 1.0          # a wall at x >= 1 m
samp = lambda u_, X, rng_: g.sample_motion_model_velocity(u_, X, a_mod, 1.0, rng_)
Xn, pi = g.sample_motion_model_with_map((1.0, 0.0), np.zeros((5000, 3)), samp, free, rng, max_tries=10)
assert np.all(free(Xn[pi > 0])) and pi.mean() > 0.9
Xn, pi = g.sample_motion_model_with_map((1.0, 0.0), np.full((50, 3), [5.0, 0, 0]), samp, free, rng, max_tries=4)
assert np.all(pi == 0)                                   # inside the wall: terminates, weight 0

# ------------------------------------------------------------------ C++ blocks
cpp = "\n".join(re.findall(r"```cpp\n(.*?)```", MD, flags=re.S))
main = r"""
#include <cstdio>
int main() {
  std::mt19937_64 rng(1);
  const Pose x0(2.0, -1.0, 0.7);
  const Pose p = velocity_forward(x0, 1.0, 0.8, 0.1, 2.0);
  const VelocityNoise n = velocity_inverse(x0, p, 2.0);
  const std::array<double, 6> av{0.02, 0.02, 0.02, 0.02, 0.005, 0.005};
  const std::array<double, 4> ao{0.05, 0.01, 0.05, 0.01};
  const Pose o0(0, 0, 0), o1(1.5, 1.0, 70 * M_PI / 180);
  const Pose xq(1.4, 1.1, 1.1);
  std::printf("%.15g %.15g %.15g\n", p(0), p(1), p(2));
  std::printf("%.15g %.15g %.15g\n", n.v_h, n.w_h, n.g_h);
  std::printf("%.15g\n", log_motion_model_velocity(Pose(1.0, 1.2, 1.5), 1.0, 0.8, Pose(0, 0, 0), av, 2.0));
  std::printf("%.15g\n", log_motion_model_odometry(xq, o0, o1, Pose(0, 0, 0), ao));
  Eigen::Matrix3Xd X = Eigen::Matrix3Xd::Zero(3, 200);
  sample_motion_model_velocity(1.0, 0.8, X, av, 2.0, rng);
  sample_motion_model_odometry(o0, o1, X, ao, rng);
  auto sampler = [&](Eigen::Matrix3Xd& Y) { sample_motion_model_velocity(1.0, 0.0, Y, av, 1.0, rng); };
  Eigen::Matrix3Xd W = Eigen::Matrix3Xd::Zero(3, 100);
  const Eigen::VectorXd pi = sample_motion_model_with_map(W, sampler, [](const Pose& q) { return q(0) < 1.0; });
  std::printf("%d %.3f\n", X.allFinite() ? 1 : 0, pi.mean());
  return 0;
}
"""
with tempfile.TemporaryDirectory() as td:
    src = Path(td) / "cards.cpp"; exe = Path(td) / "cards"
    src.write_text(cpp + main)
    cc = subprocess.run(["g++", "-std=c++17", "-O1", "-Wall", "-Wextra", "-I/usr/include/eigen3", str(src), "-o", str(exe)],
                        capture_output=True, text=True)
    if cc.returncode != 0:
        print(cc.stderr); FAIL.append("C++ blocks do not compile")
    else:
        if cc.stderr.strip():
            print("g++ warnings:\n" + cc.stderr)
        lines = subprocess.run([str(exe)], capture_output=True, text=True, check=True).stdout.split("\n")
        cp = np.array(lines[0].split(), float); cn = np.array(lines[1].split(), float)
        pp = g.velocity_forward(np.array([2.0, -1.0, 0.7]), 1.0, 0.8, 0.1, 2.0)
        assert np.allclose(cp, pp, atol=1e-12), (cp, pp)
        assert np.allclose(cn, g.velocity_inverse(np.array([2.0, -1.0, 0.7]), pp, 2.0), atol=1e-12)
        assert np.isclose(float(lines[2]), g.log_motion_model_velocity(np.array([1.0, 1.2, 1.5]), (1.0, 0.8), o, a_mod, 2.0), atol=1e-9)
        assert np.isclose(float(lines[3]), g.log_motion_model_odometry(np.array([1.4, 1.1, 1.1]), u, o, ao), atol=1e-9)
        fin, pim = lines[4].split()
        assert fin == "1" and float(pim) > 0.9
        OUT["cpp"] = "compiled; forward, inverse, both log densities agree with Python to 1e-9"

# ------------------------------------------------------------------ quoted strings
missing = [s for s in QUOTED if s not in MD]
for s in missing:
    FAIL.append(f"quoted number not found in translate.md: {s!r}")
(HERE / "card_numbers.json").write_text(json.dumps(OUT, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(OUT, indent=2, ensure_ascii=False))
print(f"{len(QUOTED) - len(missing)}/{len(QUOTED)} quoted numbers found in translate.md")
if FAIL:
    print("FAIL:\n  " + "\n  ".join(FAIL))
    sys.exit(1)
print("OK")
