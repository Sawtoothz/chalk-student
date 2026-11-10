#!/usr/bin/env python3
"""Finite-difference check of analytic Jacobians, on vectors and on manifolds.

Euclidean model mode (unchanged; run from the package dir, needs exercises.models.<Model>.g/.h):

    fd_check.py exercises.exercise:G_jac --model RangeBearing --arg u --wrap 2
    fd_check.py exercises.exercise:H_jac --model RangeBearing --wrap 1

Function mode (any callable; chosen whenever --in or --point is given):

    fd_check.py <module:f> [--jac <module:J>] --point <SPEC> --in <SPACE> [--out <SPACE>]
                [--dim n] [--extra <EXPR>] [--wrap rows] [--n 10] [--seed 0] [--eps 1e-6]

  f(x, *extra) is the function, J(x, *extra) its analytic Jacobian. Without --jac, f must return the
  pair (value, J), as `point_to_plane(x, p_L, u, q) -> (z, H)` does.
  --point   module:func (called with an np.random.Generator if it takes an argument) or a Python
            expression in np, rng and the helpers of this module (so3_exp, se3_exp, unit), e.g.
            "so3_exp(rng.normal(size=3))". One sample point per call; --n points are drawn.
  --extra   expression in np, rng, x, unit, ... returning a tuple of extra arguments of f and J.
  SPACE     euclid | so3-left | so3-right | se3-left | se3-right | module:func.
            Input (--in): x' = retract(x, d), d in R^dim. so3-left: exp(d^) C; so3-right: C exp(d^);
            se3-left: exp(d^) T; se3-right: T exp(d^); SE(3) tangent is Barfoot's xi = [rho; phi]
            (translation first). A custom module:func is retract(x, d) and needs --dim
            (e.g. exercises.models:boxplus --dim 24).
            Output (--out, default euclid): the difference f(x') minus f(x) as a vector.
            euclid: a - b (rows in --wrap wrapped); so3-left: log(C1 C0^T); so3-right: log(C0^T C1);
            se3-left: log(T1 T0^-1); se3-right: log(T0^-1 T1). A custom module:func is minus(a, b) = a [-] b,
            the boxminus order (e.g. exercises.models:boxminus).

  Example, FAST-LIO2's H of Eq. 12 through the state's boxplus (from packages/xu-fastlio2/paper):
    fd_check.py exercises.solutions.T3_solution:point_to_plane --point exercises.models:random_state \\
        --in exercises.models:boxplus --dim 24 --extra "(rng.normal(size=3), unit(rng.normal(size=3)), rng.normal(size=3))"

From Python:
    from scripts.fd_check import check_jacobian, check_jacobian_manifold, SO3_LEFT, SE3_LEFT
    check_jacobian(lambda x: model.g(u, x), lambda x: G_jac(model, u, x), x, wrap_rows=(2,))
    check_jacobian_manifold(lambda C: C @ p, lambda C: -hat(C @ p), C, SO3_LEFT)    # d(Cp)/d(psi) = -(Cp)^
    check_jacobian_manifold(so3_exp, so3_left_jacobian, phi, EUCLID, SO3_LEFT)       # output on SO(3)

Central differences in the local coordinates of the output at f(x), eps = 1e-6, ten random points.
Prints the worst entry and both matrices on failure.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import re
import sys
from pathlib import Path
from typing import Callable, NamedTuple

import numpy as np


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


# ------------------------------------------------------------------ Euclidean (original API)


def numeric_jacobian(f, x, eps=1e-6, wrap_rows=()):
    y0 = np.atleast_1d(f(x))
    J = np.zeros((y0.size, x.size))
    for j in range(x.size):
        d = np.zeros_like(x); d[j] = eps
        diff = np.atleast_1d(f(x + d)) - np.atleast_1d(f(x - d))
        for r in wrap_rows:
            diff[r] = wrap(diff[r])
        J[:, j] = diff / (2 * eps)
    return J


def _compare(Ja, Jn, rtol, atol):
    Ja = np.asarray(Ja, dtype=float)
    if Ja.shape != Jn.shape and Ja.size == Jn.size:
        Ja = Ja.reshape(Jn.shape)
    if Ja.shape != Jn.shape:
        raise AssertionError(f"Jacobian shape mismatch: analytic {Ja.shape}, numeric {Jn.shape}")
    err = np.abs(Ja - Jn)
    tol = atol + rtol * np.abs(Jn).max()
    if err.max() > tol:
        i, j = np.unravel_index(err.argmax(), err.shape)
        raise AssertionError(
            f"Jacobian mismatch at entry ({i},{j}): analytic {Ja[i, j]:.6g}, numeric {Jn[i, j]:.6g}\n"
            f"analytic:\n{Ja}\nnumeric:\n{Jn}"
        )
    return err.max()


def check_jacobian(f, J_analytic, x, rtol=1e-5, atol=1e-7, wrap_rows=()):
    Jn = numeric_jacobian(f, x, wrap_rows=wrap_rows)
    return _compare(J_analytic(x), Jn, rtol, atol)


# ------------------------------------------------------------------ SO(3), SE(3) (numpy only)


def hat(v):
    """so(3) hat: hat(a) @ b = a x b."""
    return np.array([[0.0, -v[2], v[1]], [v[2], 0.0, -v[0]], [-v[1], v[0], 0.0]])


def vee(K):
    return np.array([K[2, 1], K[0, 2], K[1, 0]])


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def so3_exp(phi):
    """Rodrigues: exp(phi^)."""
    phi = np.asarray(phi, float)
    th2 = float(phi @ phi)
    K = hat(phi)
    if th2 < 1e-12:  # Taylor to third order
        return np.eye(3) + K + 0.5 * K @ K
    th = np.sqrt(th2)
    return np.eye(3) + np.sin(th) / th * K + (1 - np.cos(th)) / th2 * K @ K


def so3_log(C):
    """log(C)^vee with angle in [0, pi]; robust at small angles and near pi."""
    C = np.asarray(C, float)
    c = (np.trace(C) - 1) / 2
    w = vee(C - C.T)  # = 2 sin(th) a, accurate even where cos(th) is not
    s = 0.5 * np.linalg.norm(w)
    th = np.arctan2(s, c)
    if th < 1e-6:
        return (0.5 + th * th / 12) * w
    if np.pi - th > 1e-3:
        return th / (2 * s) * w
    # near pi: a a^T = ((C + C^T)/2 - cos th I) / (1 - cos th); sign of a from w
    S = (0.5 * (C + C.T) - c * np.eye(3)) / (1 - c)
    k = int(np.argmax(np.diag(S)))
    a = S[:, k] / np.linalg.norm(S[:, k])
    if a @ w < 0:
        a = -a
    return np.arctan2(0.5 * (a @ w), c) * a


def so3_left_jacobian(phi):
    """Barfoot (8.37a): J(phi) = sin th/th I + (1 - sin th/th) a a^T + (1 - cos th)/th a^; exp((phi+d)^) ~ exp((J d)^) exp(phi^)."""
    phi = np.asarray(phi, float)
    th2 = float(phi @ phi)
    K = hat(phi)
    if th2 < 1e-12:
        return np.eye(3) + 0.5 * K + K @ K / 6
    th = np.sqrt(th2)
    return np.eye(3) + (1 - np.cos(th)) / th2 * K + (th - np.sin(th)) / (th2 * th) * K @ K


def so3_right_jacobian(phi):
    return so3_left_jacobian(-np.asarray(phi, float))


def se3_hat(xi):
    """xi = [rho; phi] -> 4x4 (Barfoot 8.14)."""
    X = np.zeros((4, 4))
    X[:3, :3] = hat(xi[3:6])
    X[:3, 3] = xi[0:3]
    return X


def se3_exp(xi):
    """Barfoot (8.33-8.34): T = [C, J rho; 0^T, 1]."""
    xi = np.asarray(xi, float)
    T = np.eye(4)
    T[:3, :3] = so3_exp(xi[3:6])
    T[:3, 3] = so3_left_jacobian(xi[3:6]) @ xi[0:3]
    return T


def se3_log(T):
    """Inverse of se3_exp: [rho; phi] with rho = J^-1 r (8.35)."""
    T = np.asarray(T, float)
    phi = so3_log(T[:3, :3])
    rho = np.linalg.solve(so3_left_jacobian(phi), T[:3, 3])
    return np.r_[rho, phi]


def se3_inv(T):
    Ti = np.eye(4)
    Ti[:3, :3] = T[:3, :3].T
    Ti[:3, 3] = -T[:3, :3].T @ T[:3, 3]
    return Ti


def point_odot(p):
    """Barfoot (8.163): for homogeneous p = [eps; eta], p^odot = [eta I, -eps^; 0^T, 0^T] (4x6)."""
    p = np.asarray(p, float)
    out = np.zeros((4, 6))
    out[:3, :3] = p[3] * np.eye(3)
    out[:3, 3:] = -hat(p[:3])
    return out


class Space(NamedTuple):
    """retract(x, d) = x [+] d with d in R^dim; minus(a, b) = a [-] b, a vector (the boxminus order)."""
    retract: Callable
    minus: Callable
    dim: int | None


EUCLID = Space(lambda x, d: x + d, lambda a, b: a - b, None)
SO3_LEFT = Space(lambda C, d: so3_exp(d) @ C, lambda C1, C0: so3_log(C1 @ C0.T), 3)
SO3_RIGHT = Space(lambda C, d: C @ so3_exp(d), lambda C1, C0: so3_log(C0.T @ C1), 3)
SE3_LEFT = Space(lambda T, d: se3_exp(d) @ T, lambda T1, T0: se3_log(T1 @ se3_inv(T0)), 6)
SE3_RIGHT = Space(lambda T, d: T @ se3_exp(d), lambda T1, T0: se3_log(se3_inv(T0) @ T1), 6)
SPACES = {"euclid": EUCLID, "so3-left": SO3_LEFT, "so3-right": SO3_RIGHT, "se3-left": SE3_LEFT, "se3-right": SE3_RIGHT}


# ------------------------------------------------------------------ manifold API


def numeric_jacobian_manifold(f, x, retract, minus=None, dim=None, eps=1e-6, wrap_rows=()):
    """J[:, j] = (f(x [+] eps e_j) [-] f(x)  -  f(x [+] -eps e_j) [-] f(x)) / 2 eps.

    retract: input space, a Space (SO3_LEFT, ...) or a callable retract(x, d) with d in R^dim
             (dim defaults to the Space's, else x.size).
    minus:   output space, a Space or a callable minus(a, b) = a [-] b returning a vector;
             default: a - b with rows in wrap_rows wrapped.
    """
    if isinstance(retract, Space):
        dim = dim or retract.dim
        retract = retract.retract
    if isinstance(minus, Space):
        minus = minus.minus
    if dim is None:
        dim = np.asarray(x).size
    if minus is None:
        minus = EUCLID.minus
    y0 = f(x)

    def loc(y):
        d = np.atleast_1d(np.asarray(minus(y, y0), dtype=float)).ravel()
        for r in wrap_rows:
            d[r] = wrap(d[r])
        return d

    cols = []
    for j in range(dim):
        e = np.zeros(dim); e[j] = eps
        cols.append((loc(f(retract(x, e))) - loc(f(retract(x, -e)))) / (2 * eps))
    return np.column_stack(cols)


def check_jacobian_manifold(f, J_analytic, x, retract, minus=None, dim=None, rtol=1e-5, atol=1e-7,
                            wrap_rows=(), eps=1e-6):
    """Check J_analytic(x) against numeric_jacobian_manifold. Returns the worst abs error; raises on failure.

    check_jacobian_manifold(lambda C: C @ p, lambda C: -hat(C @ p), C, SO3_LEFT)         # out: R^3
    check_jacobian_manifold(so3_exp, so3_left_jacobian, phi, EUCLID, SO3_LEFT)            # out: SO(3)
    check_jacobian_manifold(z, H, x, models.boxplus, dim=24)                              # custom [+]
    """
    Jn = numeric_jacobian_manifold(f, x, retract, minus, dim, eps=eps, wrap_rows=wrap_rows)
    return _compare(J_analytic(x), Jn, rtol, atol)


# ------------------------------------------------------------------ CLI


_FUNC = re.compile(r"^[A-Za-z_][\w.]*:[A-Za-z_]\w*$")


def _load(spec):
    mod, fn = spec.split(":")
    return getattr(importlib.import_module(mod), fn)


def _space(spec):
    """A built-in Space name or module:func (a custom retract for --in, minus for --out)."""
    if spec in SPACES:
        return SPACES[spec]
    if _FUNC.match(spec):
        return _load(spec)
    raise SystemExit(f"unknown space {spec!r}: use one of {', '.join(SPACES)} or module:func")


def _namespace(rng, **kw):
    return {"np": np, "rng": rng, "unit": unit, "hat": hat, "so3_exp": so3_exp, "se3_exp": se3_exp, **kw}


def _sampler(spec):
    if _FUNC.match(spec):
        fn = _load(spec)
        try:
            takes_arg = len(inspect.signature(fn).parameters) > 0
        except (TypeError, ValueError):
            takes_arg = True
        return (lambda rng: fn(rng)) if takes_arg else (lambda rng: fn())
    return lambda rng: eval(spec, _namespace(rng))


def main_function(a) -> int:
    f_raw = _load(a.target)
    J_raw = _load(a.jac) if a.jac else None
    retract, minus = _space(a.inp), _space(a.out)
    dim = a.dim
    if not isinstance(retract, Space) and dim is None:
        raise SystemExit("a custom --in space needs --dim")
    sample = _sampler(a.point)
    rng = np.random.default_rng(a.seed)
    worst = 0.0
    for _ in range(a.n):
        x = sample(rng)
        extra = tuple(eval(a.extra, _namespace(rng, x=x))) if a.extra else ()
        if J_raw is None:
            f = lambda s: f_raw(s, *extra)[0]
            J = lambda s: f_raw(s, *extra)[1]
        else:
            f = lambda s: f_raw(s, *extra)
            J = lambda s: J_raw(s, *extra)
        worst = max(worst, check_jacobian_manifold(f, J, x, retract, minus, dim, rtol=a.rtol, atol=a.atol,
                                                   wrap_rows=a.wrap, eps=a.eps))
    print(f"{a.target}: OK at {a.n} points (in {a.inp}, out {a.out}), worst abs error {worst:.2e}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("target", help="module:function, e.g. exercises.exercise:G_jac")
    ap.add_argument("--model", default="RangeBearing", help="class in exercises.models (model mode)")
    ap.add_argument("--arg", choices=["u", "none"], default="none", help="whether the Jacobian takes a control u (model mode)")
    ap.add_argument("--wrap", type=int, nargs="*", default=[], help="output rows that are angles")
    ap.add_argument("--n", type=int, default=10)
    g = ap.add_argument_group("function mode (any of --in/--point selects it)")
    g.add_argument("--jac", help="module:func of the analytic Jacobian; omitted: target returns (value, J)")
    g.add_argument("--point", help="module:func(rng) or expression giving one sample point")
    g.add_argument("--in", dest="inp", help="input space: " + "|".join(SPACES) + "|module:retract")
    g.add_argument("--out", default="euclid", help="output space: " + "|".join(SPACES) + "|module:minus")
    g.add_argument("--dim", type=int, help="tangent dimension of the input (needed for a custom --in)")
    g.add_argument("--extra", help="expression in np, rng, x giving a tuple of extra arguments")
    g.add_argument("--seed", type=int, default=0)
    g.add_argument("--eps", type=float, default=1e-6)
    g.add_argument("--rtol", type=float, default=1e-5)
    g.add_argument("--atol", type=float, default=1e-7)
    a = ap.parse_args()

    sys.path.insert(0, str(Path.cwd()))
    if a.inp or a.point:
        if not (a.inp and a.point):
            ap.error("function mode needs both --in and --point")
        return main_function(a)

    mod, fn = a.target.split(":")
    J = getattr(importlib.import_module(mod), fn)
    models = importlib.import_module("exercises.models")
    model = getattr(models, a.model)()
    rng = np.random.default_rng(0)
    worst = 0.0
    for k in range(a.n):
        x = np.array([rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(-np.pi, np.pi)])
        if a.arg == "u":
            u = np.array([rng.uniform(0.2, 1.5), 0.0 if k % 3 == 0 else rng.uniform(-1.5, 1.5)])
            worst = max(worst, check_jacobian(lambda s: model.g(u, s), lambda s: J(model, u, s), x, wrap_rows=a.wrap))
        else:
            worst = max(worst, check_jacobian(model.h, lambda s: J(model, s), x, wrap_rows=a.wrap))
    print(f"{a.target}: OK at {a.n} states, worst abs error {worst:.2e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
