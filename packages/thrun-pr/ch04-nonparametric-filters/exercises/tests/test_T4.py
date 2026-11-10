"""Grader for T4. Each test isolates one planted bug in broken_pf.py; all four pass only when all are fixed."""

from __future__ import annotations

import numpy as np

from .. import models
from ..T4_debug.broken_pf import BrokenPF

still = lambda u, X, r: X.copy()


def test_resampler_handles_any_weight_scale():
    """Table 4.4 assumes Σw = 1. The same weights at any scale must give the same, valid draw."""
    rng = np.random.default_rng(0)
    M = 40
    w = rng.gamma(0.5, 1.0, M); w /= w.sum()
    for scale in (1.0, 0.5, M, 1e-6):
        pf = BrokenPF(np.zeros((M, 1)), still, None, np.random.default_rng(1))
        try:
            idx = pf.resample(scale * w)
        except IndexError:
            raise AssertionError(f"resample ran off the end with Σw = {scale:g}")
        cnt = np.bincount(idx, minlength=M)
        assert cnt.sum() == M
        assert np.all(cnt >= np.floor(M * w)) and np.all(cnt <= np.ceil(M * w)), f"copy counts wrong at Σw = {scale:g}"


def test_weights_carry_across_steps_without_resampling():
    """(4.36): two measurements of a static state with no resampling in between must both count."""
    rng = np.random.default_rng(2)
    M = 50_000
    X = rng.normal(0.0, 1.0, (M, 1))
    mild = lambda z, X: -0.5 * ((z - X[:, 0]) / 2.0) ** 2
    pf = BrokenPF(X, still, mild, rng, neff_frac=0.01)
    pf.step(0.0, 1.5)
    pf.step(0.0, 1.5)
    mu, _ = pf.estimate()
    exact = 1.0 * (2 * 1.5 / 4.0) / (1.0 + 2 / 4.0)      # prior N(0,1), two readings with variance 4
    assert abs(mu[0] - exact) < 0.03, f"posterior mean {mu[0]:.3f}, exact {exact:.3f}"


def test_survives_realistic_log_likelihoods():
    """A beam model sums hundreds of log terms: log p(z | x) of −3000 is normal. The estimate must not be NaN."""
    rw = models.RandomWalk1D()
    rng = np.random.default_rng(3)
    M = 20_000
    deep = lambda z, X: rw.log_lik(z, X) - 3000.0
    pf = BrokenPF(rng.normal(0, 1, (M, 1)), rw.sample_motion, deep, rng, neff_frac=0.0)
    pf.step(0.0, 0.8)
    mu, cov = pf.estimate()
    v0 = rw.var0 + rw.R_proc; k = v0 / (v0 + rw.Q_meas)
    assert np.isfinite(mu[0]), "estimate is NaN"
    assert abs(mu[0] - k * 0.8) < 0.03 and abs(cov[0, 0] - (1 - k) * v0) < 0.03


def test_heading_estimate_near_pi():
    rng = np.random.default_rng(4)
    M = 2000
    X = np.column_stack([rng.normal(0, 0.1, M), rng.normal(0, 0.1, M), models.wrap(np.pi + rng.normal(0, 0.1, M))])
    pf = BrokenPF(X, still, None, rng, angle_idx=(2,))
    mu, cov = pf.estimate()
    assert abs(models.wrap(mu[2] - np.pi)) < 0.02, f"heading {mu[2]:.2f} rad, true ±π"
    assert cov[2, 2] < 0.02
