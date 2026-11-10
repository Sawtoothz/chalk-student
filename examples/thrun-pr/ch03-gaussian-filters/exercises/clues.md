# Clues

Three steps per exercise: direction, key idea, near-solution. Open one at a time. Each clue you open
is recorded in `learner.yaml` by `just clue t2.2 T3.2 1`.

## T1 concept

No clues; the answers are all on pp. 39–43, 54–63, 65–71, 71–79.

## T2.1 Inversion lemma → Kalman gain

1. In the lemma, the matrix being inverted on the left is a sum of "something you can invert" and a low-rank product. Match Σ̄⁻¹ + CᵀQ⁻¹C to that pattern.
2. R ↔ Σ̄⁻¹, P ↔ Cᵀ, Q ↔ Q⁻¹. Apply the lemma, then simplify (Q + CΣ̄Cᵀ) using R⁻¹ = Σ̄.
3. After the lemma you have Σ̄ − Σ̄Cᵀ(Q + CΣ̄Cᵀ)⁻¹CΣ̄. Factor Σ̄ out on the right and recognise K.

## T2.2 Joseph form

1. Write the posterior error e = x − μ as a linear function of the prior error ē = x − μ̄ and the noise δ.
2. e = (I − KC)ē − Kδ. Take the covariance; ē and δ are independent.
3. Expand (I − KC)Σ̄(I − KC)ᵀ + KQKᵀ and substitute K = Σ̄Cᵀ(CΣ̄Cᵀ + Q)⁻¹; the cross terms cancel the KQKᵀ term exactly.

## T2.3 Exercise 4(b)

1. Only the third column of G is not trivial; θ appears in the first two rows through cos and sin.
2. G = [[1, 0, −sin θ], [0, 1, cos θ], [0, 0, 1]] at θ = 0 gives G = [[1, 0, 0], [0, 1, 1], [0, 0, 1]].
3. Σ̄ = GΣGᵀ has Σ̄_yy = 0.01 + 10000: the EKF says the robot is at (1, 0) with a tall thin ellipse along y. The truth is a ring of radius 1 around the origin; its mass is nowhere near x = 1 for most of the ring.

## T3.1 kf_predict / kf_update

1. Lines 2–3 are two lines of NumPy. For the update, compute ν and S first and keep them.
2. K = Σ̄CᵀS⁻¹ means Kᵀ = S⁻ᵀ(CΣ̄ᵀ) = S⁻¹(CΣ̄) because S is symmetric. That is one `cho_solve`.
3. Joseph form: `I_KC @ Sigma_bar @ I_KC.T + K @ Q_meas @ K.T`, then symmetrize.

## T3.2 G_jac / H_jac

1. Differentiate g row by row with respect to (x, y, θ). Only θ is nontrivial. Remember the |ω| < 1e-9 branch has a different g.
2. For h: write r = √q, q = dx² + dy², dx = m_x − x. ∂r/∂x = −dx/r. The bearing is atan2(dy, dx) − θ; ∂atan2/∂x = dy/q (watch the sign from dx = m_x − x).
3. H = [[−dx/r, −dy/r, 0], [dy/q, −dx/q, −1]]. Run `test_H_jacobian_matches_finite_differences` and read the two matrices printed on failure.

## T3.3 ekf_step

1. Mean lines use g and h, covariance lines use G and H. H is evaluated at μ̄, after g.
2. Wrap ν[1] before passing it to kf_update; wrap μ[2] after.
3. `nu = z - model.h(mu_bar); nu[1] = wrap(nu[1]); mu, Sigma, nu, S = kf_update(mu_bar, Sigma_bar, z, H, Q_meas, nu=nu)`.

## T3.4 sigma_points / unscented_transform / ukf_step

1. (n+λ)Σ = LLᵀ by Cholesky; the sigma points are μ ± columns of L. Weights from eq. 3.67; w_c⁰ differs from w_m⁰.
2. For angles, average deviations from column 0, not raw values: mean = Y[:,0] + wrap(Y − Y[:,0]) @ wm.
3. Redraw sigma points from (μ̄, Σ̄) at line 6. Line 13 is Σ̄ − K S Kᵀ; line 10 uses deviations of the *redrawn* points from μ̄.

## T3.5 information form

1. Ω = Σ⁻¹ by solving Σ X = I with Cholesky; ξ = Σ⁻¹μ is one more solve with the same factor.
2. Update is pure addition: Ω + CᵀQ⁻¹C and ξ + CᵀQ⁻¹z. Use `solve(Q, C)` and `solve(Q, z)`.
3. Total ignorance Ω = 0 must work: nothing in `if_update` may invert Ω.

## T3.6 nees / nis

1. Quadratic form with an inverse covariance.
2. `e @ solve(Sigma, e)`.
3. Same for ν and S.

## T4 debug

1. Run `pytest exercises/tests/test_T4.py -v`. Each failing test names its bug class.
2. Check the Jacobian with finite differences; check when it is computed; check what happens to an angle of 2π − 0.1; check what (I − KH)Σ̄ does to symmetry.
3. See `solutions/T4.md` (only after the first two clues).

## T5 robot

1. Task 2: ANIS > 2 means S is too small, so Q_meas (or Σ̄ through R_proc) is too small. Scale Q_meas up until ANIS ≈ 2 before touching R_proc.
2. Task 3: the weakly observable state is θ when the robot drives straight toward or away from the landmark (bearing rate is zero). NEES on θ grows there even when NIS is fine.
3. Task 4: at r = 0.5 m, H's 1/q terms are 4 rad/m²; a 0.1 m position error is a 0.4 rad linearization error in bearing. The UKF stays consistent longer; the EKF needs a smaller Δt or a gate.
