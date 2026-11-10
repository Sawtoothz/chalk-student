"""Grader for T4. One test per planted bug in broken_filter.py; each test is built so that only its own
bug can fail it. Passes only when all five are fixed. Oracle: the scalar KF equations (translate.md C1, C3)
evaluated by hand on small numbers."""

from __future__ import annotations

import numpy as np
import pytest

from ..T4_debug.broken_filter import AltitudeFilter


def test_predict_adds_process_variance():
    f = AltitudeFilter(x0=0.0, P0=1.0, R_proc=0.5, sigma_z=3.0)
    f.predict(v_cmd=0.0, dt=1.0)
    assert float(f.P) == pytest.approx(1.5, rel=1e-6), f"P̄ = {float(f.P)}, expected P + R_proc·dt = 1.5"


def test_sensor_sigma_becomes_a_variance():
    f = AltitudeFilter(x0=0.0, P0=4.0, R_proc=0.1, sigma_z=2.0)
    y, S, ok = f.update(1.0)
    assert ok
    assert float(S) == pytest.approx(8.0, rel=1e-6), f"S = {float(S)}, expected P̄ + σ_z² = 4 + 4"
    assert float(f.x) == pytest.approx(0.5, rel=1e-6)


def test_gate_uses_innovation_variance():
    # wide prior right after takeoff: y = 5 m, S = 100 + 1, y²/S = 0.25 → must be accepted
    f = AltitudeFilter(x0=0.0, P0=100.0, R_proc=0.1, sigma_z=1.0, gate=6.635)
    _, _, ok = f.update(5.0)
    assert ok, "a 5 m residual against a 10 m prior standard deviation was rejected"
    # tight prior: y = 5 m, S = 0.01 + 1, y²/S = 24.8 → must be rejected
    g = AltitudeFilter(x0=0.0, P0=0.01, R_proc=0.1, sigma_z=1.0, gate=6.635)
    _, _, ok = g.update(5.0)
    assert not ok and float(g.x) == 0.0


def test_dropout_still_advances_time():
    f = AltitudeFilter(x0=0.0, P0=1.0, R_proc=0.5, sigma_z=1.0)
    f.step(v_cmd=2.0, dt=0.1, z=None)
    assert float(f.x) == pytest.approx(0.2, rel=1e-6), "the drone kept climbing while the baro was silent"
    assert float(f.P) > 1.0, "a tick with no measurement must still grow the variance"


def test_variance_survives_unknown_start_altitude():
    # P0 = 1e8 m² (start altitude unknown), σ_z = 1 m: the posterior variance must be ≈ σ_z² = 1, not 0
    f = AltitudeFilter(x0=0.0, P0=1e8, R_proc=0.1, sigma_z=1.0)
    f.update(37.0)
    assert np.asarray(f.P).dtype == np.float32, "keep the flight controller's float32"
    assert float(f.P) == pytest.approx(1.0, rel=1e-4), f"P = {float(f.P)} after the first baro sample"
    assert float(f.x) == pytest.approx(37.0, rel=1e-6)
