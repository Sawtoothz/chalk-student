# Clues

Three steps per exercise: direction, key idea, near-solution. Open one at a time with
`just clue thrun-pr 5 <exercise> <n>`; each one you open is recorded in `learner.yaml`.

## T1 concept

No clues; the answers are on pp. 117–143 and in lecture L1–L10.

## T2.1 Error samplers

1. Use symmetry for the mean. For the variance, write the triangle as (h − |a|)/h² with h = √6 b.
2. Var of rand(−b, b) is (2b)²/12; variances of independent terms add; a constant factor c scales the variance by c².
3. The extreme of line 2 is when all twelve uniforms sit at ±b at once: ½ · 12 · b.

## T2.2 The circle

1. Two lines: one through (x, y) along (−sin θ, cos θ), one through the chord's midpoint along the chord's normal (y − y′, x′ − x).
2. Set them equal, multiply the x row by cos θ and the y row by sin θ, add: λ drops out and μ is left.
3. For (b) the centre is (0, −2): the robot turns right around a point to its right. r* = 2, Δθ = −0.5, and line 7 multiplies them.

## T2.3 Jacobian determinants

1. γ̂ appears only in the θ′ row. Expand the determinant along the γ̂ column.
2. The 2×2 block has columns (a cos φ, a sin φ) and (b cos φ − c sin φ, b sin φ + c cos φ). Its determinant is a·c.
3. a = Δt sinc h, c = s Δt/2 = v̂Δt² sinc h / 2; then multiply by the Δt from step 1. For odometry, subtract the δ̂rot2 column from the δ̂rot1 column.

## T2.4 A robot with dynamics

1. This is the ch. 3 car: x′ = Ax + Γa with A = [[1, Δt], [0, 1]], Γ = (Δt²/2, Δt).
2. One-step covariance σ²ΓΓᵀ has rank 1. For (c), iterate Σ ← AΣAᵀ + ΓΓᵀ from 0.
3. ρ_T = Σ_xẋ / √(Σ_xx Σ_ẋẋ); for large T, Σ_xx ≈ T³/3, Σ_xẋ ≈ T²/2, Σ_ẋẋ = T.

## T2.5 The bicycle

1. Find where the normals to the two wheels meet: that is the centre of the circle.
2. R = l / tan φ from the rear axle, so ω = v tan φ / l.
3. Move the rear axle with `velocity_forward`, then add l(cos θ′, sin θ′).

## T3.1 log_prob

1. Write the log of (5.11) and (5.12) by hand; floor b² before anything else.
2. Normal: −½(log 2πb² + a²/b²). Triangular: log(1/√(6b²) − |a|/(6b²)) where that is positive.
3. `np.where(p > 0, np.log(np.where(p > 0, p, 1.0)), -np.inf)` avoids the log-of-zero warning.

## T3.2 velocity_forward

1. Rewrite sin(θ + φ) − sin θ and cos θ − cos(θ + φ) with the sum-to-product identities.
2. Both become 2 sin(φ/2) times cos or sin of (θ + φ/2). Divide by ω̂ and you get Δt sinc(φ/2).
3. `s = v_h * dt * np.sinc(half / np.pi)` with `half = 0.5 * w_h * dt`; x′ = x + s cos(θ + half), y′ likewise; θ′ wrapped.

## T3.3 sample_motion_model_velocity

1. Three variances from the commanded (v, ω), then three vectors of M draws.
2. `sample_normal(b2, rng, M)` for each; then one call to your `velocity_forward`.
3. `v_h = v + sample_normal(a1*v*v + a2*w*w, rng, M)`; same pattern for ω̂, and γ̂ without the offset.

## T3.4 velocity_inverse

1. Express the displacement in the start frame: c along the heading, l to the left.
2. On an arc the chord points at half the heading change: half = atan2(l, c), folded into (−π/2, π/2] so that reversing is not read as a half turn. The sign of c is the sign of v̂.
3. `v_h = sgn * hypot(dx, dy) / (dt * sinc(half))`, `w_h = 2 * half / dt`, `g_h = wrap(θ′ − θ − 2·half) / dt`.

## T3.5 velocity_noise_jacobian

1. Differentiate your chord form: s = v̂Δt sinc(h), φ = θ + h, h = ω̂Δt/2.
2. ∂/∂v̂: Δt sinc h (cos φ, sin φ, 0). ∂/∂ω̂ needs d sinc/dh · Δt/2 and the rotation of the chord. ∂/∂γ̂ = (0, 0, Δt).
3. d sinc/dh = (h cos h − sin h)/h²; below |h| = 10⁻³ use −h/3 + h³/30.

## T3.6 log_motion_model_velocity

1. Three `log_prob` terms, added. For the pose density, one more term.
2. Subtract log|det J| from T3.5, with |v̂| floored at STEP_EPS/Δt before building J.
3. `lp - np.log(np.abs(np.linalg.det(velocity_noise_jacobian(X, v_floor, w_h, dt))))` works for (N, 3, 3).

## T3.7 odometry_params

1. Lines 2–4 of Table 5.5, vectorized with `[..., i]` so P0 and P1 can both be arrays.
2. Wrap rot1 and rot2; below TRANS_EPS set rot1 = 0 so the whole turn goes into rot2.
3. `rot1 = np.where(trans < TRANS_EPS, 0.0, wrap(np.arctan2(dy, dx) - P0[..., 2]))`.

## T3.8 sample_motion_model_odometry

1. The measured δ come from u once; the variances from the measured δ through `rot_for_noise`.
2. δ̂ = δ − noise (Table 5.6 lines 5–7), then (5.40) for all particles at once.
3. Read θ before you write anything; return a new array.

## T3.9 log_motion_model_odometry

1. Call `odometry_params` twice: on u (measured) and on (X, Xp) (hypotheses).
2. Same variances as the sampler. Wrap the two angular errors.
3. pose density: `lp - np.log(np.maximum(h_trans, TRANS_EPS))`.

## T3.10 sample_motion_model_with_map

1. One sampler call for everyone, then a loop of at most max_tries − 1 rounds over the failures.
2. Redraw from the original X (x_{t-1}) for the failing rows only; keep an `ok` mask.
3. `Xn[bad] = sampler(u, X[bad], rng); ok[bad] = in_free(Xn[bad])`; return `ok.astype(float)` as π.

## T3.11 sample_motion_model_bicycle

1. Move the reference point to the rear axle first.
2. The rear axle follows the velocity model with ω̂ = v̂ tan φ̂ / l and no γ̂.
3. Rear = X − l(cos θ, sin θ, ·); call `velocity_forward(rear, v_h, v_h*tan(phi_h)/l, 0, dt)`; front = rear′ + l(cos θ′, sin θ′).

## T3.12 sample_motion_model_holonomic

1. In the world frame the body velocity rotates with θ(t) = θ + ω̂t. Integrate it over [0, Δt].
2. ∫₀^Δt R(ω̂t) dt = Δt sinc(h) R(h) with h = ω̂Δt/2: the same chord trick as T3.2, applied to (v_x, v_y).
3. Δp = Δt sinc(h) R(θ + h) (v̂_x, v̂_y); θ′ = θ + (ω̂ + γ̂)Δt; variances `np.asarray(model.A) @ (vx², vy², ω²)`.

## T4 debug

1. Run the grader: each failing test names one symptom from the file's header.
2. Bugs live in: a density with zero variance; line 7; a missing wrap; which δ the variances use; the order of an in-place update.
3. Compare each function with its card in translate.md (C1, C3 trick 1, C4 tricks 1 and 4, the C4 Eigen comment).

## T5 robot

1. Start with tasks 1–2 and plot the per-step errors against δtrans before fitting anything else.
2. The worst steps are spins (odometry under 3 cm); the remaining error has a slope in heading.
3. Fit χ as Σa² / Σab with a the odometry heading change and b the true one, both per 1 s step.
