"""Shared models for the ch. 5 exercises. Nothing here is an exercise: read it, do not edit it.

What lives here:

1. `wrap` and the conventions: a pose is (x, y, θ), θ in rad, zero along x, counterclockwise positive
   (5.1); M particles are an (M, 3) array; angles are wrapped to [−π, π).
2. Noise presets used by the tests and the lecture: `ALPHA_VEL_L5` (Fig L5a), `ALPHA_ODO_L7` (Fig L7).
3. `WallMap`: the lecture's Fig L8 room, one wall grown by the robot radius (configuration space,
   p. 141). `in_free(X)` answers p(x ∣ m) > 0 for an (M, 3) array of poses.
4. `Bicycle` and `Holonomic`: the parameters of book exercises 4–5 and 7, with the conventions written
   out, so the stubs in `exercise.py` and the oracle tests agree on what a control means.
5. `tracked_route`: the command sequence the T5 tracked robot drives (straights, turns, spins in place,
   reversing). The hidden part of T5 (true noise, slip) is in `T5_sim.py`, not here.

The odometry noise parameters are alpha = (α₁, α₂, α₃, α₄), the velocity ones (α₁, …, α₆), both in the
book's order (Tables 5.1, 5.3, 5.5, 5.6). This chapter has no Gaussian filter, so `R_proc` and
`Q_meas` do not appear; the noise is on the controls.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def wrap(a):
    """Map an angle (or array of angles) to [−π, π)."""
    return (np.asarray(a) + np.pi) % (2 * np.pi) - np.pi


# ------------------------------------------------------------------ noise presets (lecture figures)

ALPHA_VEL_L5 = (0.02, 0.02, 0.02, 0.02, 0.005, 0.005)   # Fig L5a, "moderate"
ALPHA_ODO_L7 = (0.01, 0.0005, 0.01, 0.0005)              # Fig L7, dead reckoning


# ------------------------------------------------------------------ map for C5 (lecture Fig L8)


@dataclass(frozen=True)
class WallMap:
    """A room with one wall, x ∈ [wall_x, wall_x + wall_w], y ∈ [wall_y, wall_y + wall_h], grown by the robot
    radius. Everything else is free. `in_free` is the configuration-space test of p. 141."""

    wall_x: float = 0.2
    wall_y: float = 1.75
    wall_w: float = 2.2
    wall_h: float = 0.15
    radius: float = 0.15

    def in_free(self, X):
        X = np.asarray(X, dtype=float)
        x, y = X[..., 0], X[..., 1]
        r = self.radius
        inside = ((x > self.wall_x - r) & (x < self.wall_x + self.wall_w + r)
                  & (y > self.wall_y - r) & (y < self.wall_y + self.wall_h + r))
        return ~inside


# ------------------------------------------------------------------ book exercises 4-5 (bicycle)


@dataclass(frozen=True)
class Bicycle:
    """Kinematic bicycle (Ackermann car), book exercises 4–5.

    Conventions used in this package (check them against the text of book exercise 4, p. 146, in T2.5):
    - The pose (x, y, θ) is the centre of the FRONT tyre's contact point, θ the heading of the frame
      (rear tyre → front tyre). The book's exercise places the pose there, not at the rear axle.
    - Control u = (v, φ): v is the forward speed of the REAR axle along θ (m/s), φ the steering angle of
      the front wheel relative to θ (rad, positive left), both held constant over Δt.
    - Wheelbase l (m) between the two contact points.
    - Without slip the rear axle moves on a circle with yaw rate ω = v tan φ / l.
    - Noise (exercise 5): v and φ are each perturbed by zero-mean Gaussian noise with the standard
      deviations sigma_v (m/s) and sigma_phi (rad). Map the book's variances onto these two numbers.
      The defaults below are this package's, not the book's ex. 5 values (σ_α = 25°, σ_v² = 50 cm²/s² · v²).
    """

    l: float = 1.0
    sigma_v: float = 0.1
    sigma_phi: float = np.deg2rad(5.0)


# ------------------------------------------------------------------ book exercise 7 (holonomic)


@dataclass(frozen=True)
class Holonomic:
    """Holonomic base (omni wheels, or the quadruped's body-velocity command), book exercise 7.

    Control u = (v_x, v_y, ω): velocities in the ROBOT frame (forward, left, yaw rate), held constant
    over Δt, so the body velocity turns with the robot. The noise follows the book's pattern for the
    velocity model: each of v̂_x, v̂_y, ω̂ gets zero-mean Gaussian noise with variance
    A[i] · (v_x², v_y², ω²), and a final rotation γ̂ with variance A[3] · (v_x², v_y², ω²) as in (5.15).
    A is a 4×3 array of non-negative coefficients.
    """

    A: tuple = ((0.02, 0.005, 0.01),
                (0.005, 0.04, 0.01),
                (0.005, 0.005, 0.03),
                (0.001, 0.001, 0.005))


# ------------------------------------------------------------------ T5 command sequence


def tracked_route(n=600, dt=0.1):
    """Commands (v, ω) at 10 Hz for the T5 tracked robot: straights, left and right arcs, a spin in
    place, a stop, and a reverse leg. Deterministic; T5_sim.py adds what the robot actually does."""
    v = np.zeros(n)
    w = np.zeros(n)
    seg = [  # (duration s, v m/s, ω rad/s)
        (6.0, 0.8, 0.0), (5.0, 0.6, 0.5), (4.0, 0.8, 0.0), (5.0, 0.5, -0.6), (3.0, 0.0, 0.9),
        (2.0, 0.0, 0.0), (6.0, -0.4, 0.0), (4.0, 0.6, -0.3), (5.0, 0.0, -0.8), (20.0, 0.7, 0.25),
    ]
    k = 0
    for dur, vv, ww in seg:
        m = int(round(dur / dt))
        v[k:k + m], w[k:k + m] = vv, ww
        k += m
        if k >= n:
            break
    if k < n:  # repeat the pattern mirrored if a longer run is asked for
        rest = tracked_route(n - k, dt)
        v[k:], w[k:] = rest[:, 0], -rest[:, 1]
    return np.column_stack([v, w])[:n]
