"""Grader for T4. Passes only when all five planted bugs in broken_motion.py are fixed.
Each test is written so that exactly one planted bug makes it fail."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import norm

from ..models import ALPHA_ODO_L7, ALPHA_VEL_L5, wrap
from ..T4_debug import broken_motion as bm
from .test_T3 import book_forward_ld, ref_odometry_compose, ref_odometry_variances


def test_robot_at_rest_gives_finite_log_densities():
    """Robot stopped: every variance is zero. The log density of 'it did not move' must be finite."""
    x0 = np.array([1.0, 2.0, 0.4])
    with np.errstate(all="ignore"):
        lo = bm.log_motion_model_odometry(x0, (x0, x0), x0, ALPHA_ODO_L7)
        lv = bm.log_motion_model_velocity(x0, (0.0, 0.0), x0, ALPHA_VEL_L5, 0.1)
    assert np.isfinite(lo), f"odometry log density at rest is {lo}"
    assert np.isfinite(lv), f"velocity log density at rest is {lv}"


@pytest.mark.parametrize("v,w", [(1.0, -0.5), (-1.0, 0.5), (-1.0, -0.5), (1.0, 0.5)])
def test_velocity_inverse_recovers_right_turns_and_reversing(v, w):
    x0 = np.array([0.0, 0.0, 0.7]); dt = 1.0
    xp = book_forward_ld(x0, v, w, 0.0, dt).astype(float)
    v_h, w_h, g_h = bm.velocity_inverse(x0, xp, dt)
    np.testing.assert_allclose([v_h, w_h, g_h], [v, w, 0.0], atol=1e-9,
                               err_msg=f"(v, ω) = ({v}, {w}) recovered as ({float(v_h):.3f}, {float(w_h):.3f})")


def test_odometry_density_is_invariant_to_rotating_the_world():
    """Rotate x_{t-1} and the hypotheses together about the origin: nothing may change. The rotations
    move the headings across ±π."""
    o0 = np.array([0.0, 0.0, 0.0]); o1 = np.array([0.4, 0.05, 0.3])
    x0 = np.array([1.0, 0.5, 2.9])
    hyps = np.array([ref_odometry_compose(x0, 0.12, 0.40, 0.2 + d) for d in np.linspace(-0.05, 0.05, 11)])
    base = bm.log_motion_model_odometry(hyps, (o0, o1), x0, ALPHA_ODO_L7)
    for phi in (0.15, 0.4, -2.0):
        c, s = np.cos(phi), np.sin(phi)
        rot = lambda P: np.stack([c * P[..., 0] - s * P[..., 1], s * P[..., 0] + c * P[..., 1], wrap(P[..., 2] + phi)], -1)
        got = bm.log_motion_model_odometry(rot(hyps), (o0, o1), rot(x0), ALPHA_ODO_L7)
        np.testing.assert_allclose(got, base, atol=1e-8, err_msg=f"rotating the world by {phi} rad changed the density")


def test_odometry_density_uses_the_measured_deltas_in_its_variances():
    """Eq. 5.44–5.46: the variances are a function of the measured δ, so they are the same for every
    hypothesis; the density over hypotheses is then a Gaussian in the three δ̂ errors."""
    o0 = np.array([0.0, 0.0, 0.3]); o1 = np.array([0.5, 0.3, 0.9])
    x0 = np.array([3.0, -2.0, -1.0])
    (r1, t, r2), b2 = ref_odometry_variances(o0, o1, ALPHA_ODO_L7)
    errs = [(0.0, 0.0, 0.0), (0.02, -0.15, 0.03), (-0.05, 0.2, -0.01), (0.1, 0.1, 0.1)]
    hyps = np.array([ref_odometry_compose(x0, r1 + e1, t + e2, r2 + e3) for e1, e2, e3 in errs])
    ref = [norm.logpdf(e1, scale=np.sqrt(b2[0])) + norm.logpdf(e2, scale=np.sqrt(b2[1]))
           + norm.logpdf(e3, scale=np.sqrt(b2[2])) for e1, e2, e3 in errs]
    np.testing.assert_allclose(bm.log_motion_model_odometry(hyps, (o0, o1), x0, ALPHA_ODO_L7), ref, rtol=1e-9, atol=1e-9)


def test_odometry_sampler_without_noise_reproduces_the_odometry():
    o = [np.array([0.0, 0.0, 0.2]), np.array([0.5, 0.2, 0.9]), np.array([0.8, 0.7, 1.8]), np.array([0.6, 1.1, 2.6])]
    X = np.array([[0.0, 0.0, 0.2]])
    for k in range(3):
        X = bm.sample_motion_model_odometry((o[k], o[k + 1]), X, (0.0, 0.0, 0.0, 0.0), np.random.default_rng(k))
        e = X[0] - o[k + 1]; e[2] = wrap(e[2])
        np.testing.assert_allclose(e, 0.0, atol=1e-12, err_msg=f"step {k + 1}: dead reckoning left the odometry")
