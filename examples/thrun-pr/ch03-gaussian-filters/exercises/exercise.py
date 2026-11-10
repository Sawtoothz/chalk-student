"""T3 — Implementation. Fill every function marked TODO. Do not change signatures.

Oracle tests: `pytest exercises/tests -q`. Cards: translate.md (C1–C5).
Conventions: R_proc = Thrun's R (process noise), Q_meas = Thrun's Q (measurement noise).
Angles: index 2 of the robot state and index 1 of its measurement are angles; wrap them.
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from .models import wrap  # noqa: F401  (you will need it)


# ---------------------------------------------------------------- C1 Kalman filter


def kf_predict(mu, Sigma, u, A, B, R_proc):
    """Table 3.1 lines 2–3. Return (mu_bar, Sigma_bar)."""
    raise NotImplementedError("TODO")


def kf_update(mu_bar, Sigma_bar, z, C, Q_meas, nu=None):
    """Table 3.1 lines 4–6 in Joseph form.

    If `nu` is given, use it as the innovation (the EKF passes z − h(mu_bar)); otherwise nu = z − C mu_bar.
    Return (mu, Sigma, nu, S) with S the innovation covariance. Never call np.linalg.inv.
    """
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------- C4 Jacobians (range-bearing model)


def G_jac(model, u, x):
    """∂g/∂x for RangeBearing.g at (u, x). 3×3. Handle |ω| < 1e-9 like the model does."""
    raise NotImplementedError("TODO")


def H_jac(model, x):
    """∂h/∂x for RangeBearing.h at x. 2×3."""
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------- C2 EKF


def ekf_step(mu, Sigma, u, z, model, R_proc, Q_meas):
    """Table 3.3, with angle wrapping of the bearing innovation and of θ.

    Return (mu, Sigma, nu, S). Reuse kf_update with C = H and nu passed in.
    """
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------- C3 UKF


def sigma_points(mu, Sigma, alpha=1e-3, beta=2.0, kappa=0.0):
    """Eq. 3.66–3.67. Return (X, wm, wc) with X of shape (n, 2n+1)."""
    raise NotImplementedError("TODO")


def unscented_transform(Y, wm, wc, noise_cov, angle_idx=()):
    """Eq. 3.69. Y: (d, 2n+1) propagated points. Return (mean, cov, deviations).

    For indices in angle_idx, compute the mean of that row relative to column 0 (wrap Y[i] − Y[i,0]
    before averaging) and wrap the deviations.
    """
    raise NotImplementedError("TODO")


def ukf_step(mu, Sigma, u, z, model, R_proc, Q_meas, alpha=1e-3, beta=2.0, kappa=0.0):
    """Table 3.4 lines 2–13. Redraw sigma points at line 6. Return (mu, Sigma, nu, S)."""
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------- C5 information form


def to_information(mu, Sigma):
    """Eq. 3.70–3.71. Return (xi, Omega). Use a factorization, not inv."""
    raise NotImplementedError("TODO")


def from_information(xi, Omega):
    """Eq. 3.72–3.73. Return (mu, Sigma)."""
    raise NotImplementedError("TODO")


def if_update(xi_bar, Omega_bar, z, C, Q_meas):
    """Table 3.5 lines 4–5. Return (xi, Omega)."""
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------- consistency statistics (T5)


def nees(err, Sigma):
    """Normalized estimation error squared: eᵀ Σ⁻¹ e."""
    raise NotImplementedError("TODO")


def nis(nu, S):
    """Normalized innovation squared: νᵀ S⁻¹ ν."""
    raise NotImplementedError("TODO")
