"""Self-test of scripts/fd_check.py: the SO(3)/SE(3) helpers, the manifold checker (known Jacobians pass,
wrong ones fail), the unchanged Euclidean API, and the function-mode CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import fd_check as fd  # noqa: E402
from scripts.fd_check import (  # noqa: E402
    SE3_LEFT, SE3_RIGHT, SO3_LEFT, SO3_RIGHT, check_jacobian, check_jacobian_manifold, hat, point_odot,
    se3_exp, se3_log, so3_exp, so3_left_jacobian, so3_log, so3_right_jacobian,
)

SEEDS = range(8)


def rand_rot(rng, scale=1.0):
    return so3_exp(rng.normal(0, scale, 3))


def rand_pose(rng):
    return se3_exp(np.r_[rng.normal(0, 2, 3), rng.normal(0, 1, 3)])


# ------------------------------------------------------------------ helpers


@pytest.mark.parametrize("th", [0.0, 1e-9, 1e-5, 0.3, 1.0, 2.5, np.pi - 1e-2, np.pi - 1e-5, np.pi - 1e-8])
def test_so3_exp_log_round_trip(th):
    rng = np.random.default_rng(1)
    for _ in range(20):
        phi = th * fd.unit(rng.normal(size=3))
        C = so3_exp(phi)
        np.testing.assert_allclose(C @ C.T, np.eye(3), atol=1e-12)
        assert np.linalg.det(C) == pytest.approx(1.0, abs=1e-12)
        np.testing.assert_allclose(so3_exp(so3_log(C)), C, atol=1e-9)
        if th < np.pi - 1e-3:
            np.testing.assert_allclose(so3_log(C), phi, atol=1e-9)


def test_so3_exp_matches_matrix_series():
    from scipy.linalg import expm
    rng = np.random.default_rng(2)
    for _ in range(20):
        phi = rng.normal(0, 1.5, 3)
        np.testing.assert_allclose(so3_exp(phi), expm(hat(phi)), atol=1e-12)


@pytest.mark.parametrize("seed", SEEDS)
def test_se3_exp_log_round_trip(seed):
    from scipy.linalg import expm
    rng = np.random.default_rng(seed)
    xi = np.r_[rng.normal(0, 2, 3), rng.uniform(0, 3.0) * fd.unit(rng.normal(size=3))]   # |phi| < pi: log is unique
    T = se3_exp(xi)
    np.testing.assert_allclose(T, expm(fd.se3_hat(xi)), atol=1e-10)   # translation first: xi = [rho; phi]
    np.testing.assert_allclose(se3_log(T), xi, atol=1e-9)
    np.testing.assert_allclose(fd.se3_inv(T) @ T, np.eye(4), atol=1e-12)


# ------------------------------------------------------------------ known Jacobians pass


@pytest.mark.parametrize("seed", SEEDS)
def test_rotated_point_left_and_right(seed):
    rng = np.random.default_rng(seed)
    C, p = rand_rot(rng), rng.normal(size=3)
    check_jacobian_manifold(lambda R: R @ p, lambda R: -hat(R @ p), C, SO3_LEFT)      # Barfoot 8.179
    check_jacobian_manifold(lambda R: R @ p, lambda R: -R @ hat(p), C, SO3_RIGHT)


@pytest.mark.parametrize("seed", SEEDS)
def test_rotated_point_wrt_rotation_vector_is_minus_Cp_hat_J(seed):
    """Barfoot 8.170: d(exp(phi^) v)/d phi = -(C v)^ J(phi), J the left Jacobian."""
    rng = np.random.default_rng(seed)
    phi, v = rng.normal(0, 1, 3), rng.normal(size=3)
    check_jacobian(lambda f: so3_exp(f) @ v, lambda f: -hat(so3_exp(f) @ v) @ so3_left_jacobian(f), phi)


@pytest.mark.parametrize("seed", SEEDS)
def test_so3_jacobians_by_exp(seed):
    """exp((phi+d)^) = exp((J_l d)^) exp(phi^) = exp(phi^) exp((J_r d)^) to first order."""
    rng = np.random.default_rng(seed)
    phi = rng.normal(0, 1, 3)
    check_jacobian_manifold(so3_exp, so3_left_jacobian, phi, fd.EUCLID, SO3_LEFT)
    check_jacobian_manifold(so3_exp, so3_right_jacobian, phi, fd.EUCLID, SO3_RIGHT)


@pytest.mark.parametrize("seed", SEEDS)
def test_se3_point_jacobians(seed):
    rng = np.random.default_rng(seed)
    T, p = rand_pose(rng), rng.normal(size=3)
    ph = np.r_[p, 1.0]
    act = lambda X: (X @ ph)[:3]
    check_jacobian_manifold(act, lambda X: np.hstack([np.eye(3), -hat(act(X))]), T, SE3_LEFT)
    check_jacobian_manifold(lambda X: X @ ph, lambda X: point_odot(X @ ph), T, SE3_LEFT)     # (Tp)^odot, 8.179
    check_jacobian_manifold(act, lambda X: X[:3, :3] @ np.hstack([np.eye(3), -hat(p)]), T, SE3_RIGHT)


@pytest.mark.parametrize("seed", SEEDS)
def test_inverse_on_so3_maps_left_to_right(seed):
    """(exp(d^) C)^-1 = C^T exp(-d^): output in the right chart moves by -d."""
    rng = np.random.default_rng(seed)
    C = rand_rot(rng)
    check_jacobian_manifold(lambda R: R.T, lambda R: -np.eye(3), C, SO3_LEFT, SO3_RIGHT)


def test_rotation_near_pi_still_checks():
    rng = np.random.default_rng(3)
    for _ in range(10):
        C = so3_exp((np.pi - 1e-4) * fd.unit(rng.normal(size=3)))
        p = rng.normal(size=3)
        check_jacobian_manifold(lambda R: R, lambda R: np.eye(3), C, SO3_LEFT, SO3_LEFT)   # identity map near pi
        check_jacobian_manifold(lambda R: R @ p, lambda R: -hat(R @ p), C, SO3_LEFT)


# ------------------------------------------------------------------ wrong Jacobians fail


@pytest.mark.parametrize("seed", SEEDS)
def test_sign_flip_fails(seed):
    rng = np.random.default_rng(seed)
    C, p = rand_rot(rng), rng.normal(size=3)
    with pytest.raises(AssertionError):
        check_jacobian_manifold(lambda R: R @ p, lambda R: hat(R @ p), C, SO3_LEFT)


@pytest.mark.parametrize("seed", SEEDS)
def test_left_right_confusion_fails(seed):
    rng = np.random.default_rng(seed)
    C, p = rand_rot(rng), rng.normal(size=3)
    with pytest.raises(AssertionError):
        check_jacobian_manifold(lambda R: R @ p, lambda R: -R @ hat(p), C, SO3_LEFT)
    with pytest.raises(AssertionError):
        check_jacobian_manifold(so3_exp, so3_left_jacobian, rng.normal(0, 1, 3), fd.EUCLID, SO3_RIGHT)


@pytest.mark.parametrize("seed", SEEDS)
def test_rotation_first_ordering_fails_on_se3(seed):
    rng = np.random.default_rng(seed)
    T, p = rand_pose(rng), rng.normal(size=3)
    act = lambda X: (X @ np.r_[p, 1.0])[:3]
    with pytest.raises(AssertionError):     # GTSAM-style [phi; rho] against Barfoot's [rho; phi]
        check_jacobian_manifold(act, lambda X: np.hstack([-hat(act(X)), np.eye(3)]), T, SE3_LEFT)


# ------------------------------------------------------------------ Euclidean API unchanged


def test_check_jacobian_euclid_with_wrap():
    f = lambda x: np.array([x[0] * x[1], fd.wrap(x[2] + 3.0)])
    J = lambda x: np.array([[x[1], x[0], 0.0], [0.0, 0.0, 1.0]])
    x = np.array([0.3, -1.2, np.pi - 3.0 + 1e-8])   # output angle sits on the wrap seam
    assert check_jacobian(f, J, x, wrap_rows=(1,)) < 1e-6
    with pytest.raises(AssertionError):
        check_jacobian(f, lambda x: -J(x), x, wrap_rows=(1,))
    np.testing.assert_allclose(fd.numeric_jacobian(f, x, wrap_rows=(1,)), J(x), atol=1e-7)


# ------------------------------------------------------------------ CLI


def run_cli(*args, cwd=ROOT):
    env = {**os.environ, "PYTHONPATH": str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")}
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "fd_check.py"), *args], cwd=cwd,
                          capture_output=True, text=True, env=env)


def test_cli_function_mode_pass_and_fail(tmp_path):
    (tmp_path / "jacmod.py").write_text(
        "import numpy as np\n"
        "from scripts.fd_check import hat\n"
        "P = np.array([0.3, -1.0, 2.0])\n"
        "def f(C): return C @ P\n"
        "def J(C): return -hat(C @ P)\n"
        "def J_bad(C): return -C @ hat(P)\n"
        "def g(T, p): return (T @ np.r_[p, 1.0])[:3]\n"
        "def G(T, p): return np.hstack([np.eye(3), -hat(g(T, p))])\n"
    )
    env_args = dict(cwd=tmp_path)
    ok = run_cli("jacmod:f", "--jac", "jacmod:J", "--point", "so3_exp(rng.normal(size=3))", "--in", "so3-left", **env_args)
    assert ok.returncode == 0, ok.stderr
    assert "OK at 10 points" in ok.stdout
    bad = run_cli("jacmod:f", "--jac", "jacmod:J_bad", "--point", "so3_exp(rng.normal(size=3))", "--in", "so3-left", **env_args)
    assert bad.returncode != 0 and "Jacobian mismatch" in bad.stderr
    se3 = run_cli("jacmod:g", "--jac", "jacmod:G", "--point", "se3_exp(rng.normal(size=6))", "--in", "se3-left",
                  "--extra", "(rng.normal(size=3),)", **env_args)
    assert se3.returncode == 0, se3.stderr
