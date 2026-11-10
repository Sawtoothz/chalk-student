# Clues

Three steps per exercise: direction, key idea, near-solution. Open one at a time. Each clue you open is recorded in
`learner.yaml` by `just clue sola-microlie 1 T3.2 1`.

## T1 concept

No clues; every answer is on the page cited in `solutions/T1.md` (pp. 4–17).

## T2.1 Adjoint of SE(2)

1. Write X, X⁻¹ and τ^ as 2+1 block matrices and multiply X τ^ X⁻¹ blockwise. The bottom row stays zero.
2. The top-left block is θ R[1]ₓRᵀ, and a planar rotation commutes with [1]ₓ. The top-right block mixes ρ and θ.
3. Top-right = Rρ − θ[1]ₓt. Read off the column that multiplies θ: −[1]ₓt = (t_y, −t_x).

## T2.2 Blocks of right minus

1. Name 𝒵 = 𝒳⁻¹𝒴 and τ = Log 𝒵. Every Jacobian of τ is J_r⁻¹(τ) times a Jacobian of 𝒵.
2. With respect to 𝒳, 𝒵 is a composition whose left factor is an inverse: chain (65) and (62), then combine the two
   adjoints into one with (34).
3. You reach −J_r⁻¹(τ) Ad_{Exp(τ)}⁻¹. Invert (75) to get Ad_{Exp(τ)}⁻¹ = J_r(τ) J_l⁻¹(τ).

## T2.3 Measurement Jacobian

1. Two blocks: the action of a group element on a point, and the inverse. The action is taken at 𝒳⁻¹, so its rotation
   is Rᵀ.
2. (166) at M = 𝒳⁻¹ is [Rᵀ  Rᵀ[1]ₓb]; (62) is −Ad_𝒳 with Ad_𝒳 from T2.1.
3. Multiply: the left block is −RᵀR = −I; the right block is −(Rᵀ[1]ₓb − Rᵀ[1]ₓt).

## T2.4 Covariance reset

1. Write the same true state two ways, 𝒳̂ Exp(ε) and 𝒳̂⁺ Exp(ε⁺), and solve for ε⁺.
2. Expand Exp(δx + η) to first order in η with the right Jacobian of Exp.
3. Exp(δx + η) ≈ Exp(δx) Exp(J_r(δx) η), so Exp(δx)⁻¹Exp(ε) ≈ Exp(J_r(δx) η).

## T3.1 so3_exp / so3_log

1. Write Rodrigues as R = I + A(θ)[θ]ₓ + B(θ)[θ]ₓ² and find A and B. The trouble is only in evaluating them near θ = 0.
2. A = sin θ/θ = `np.sinc(θ/π)`; B = (1 − cos θ)/θ² = ½(sin(θ/2)/(θ/2))², no subtraction. For Log, go through a
   quaternion: w = cos(θ/2), v = u sin(θ/2), and θ = 2 atan2(‖v‖, w) is accurate at both ends.
3. Matrix → quaternion by Shepperd's method: pick the largest of tr R, R₀₀, R₁₁, R₂₂ and take the square root of
   that one. Flip (w, v) → (−w, −v) if w < 0, then return 2 atan2(‖v‖, w)/‖v‖ · v (and 0 if ‖v‖ = 0).

## T3.2 so3_Jr / so3_Jrinv

1. Same pattern as Exp: I + c₁(θ)W + c₂(θ)W² with W = [θ]ₓ. Only the scalar coefficients need care.
2. (1 − cos θ)/θ² is B from T3.1. (θ − sin θ)/θ³ and the (144) coefficient have no subtraction-free form: switch to a
   Taylor series below |θ| = 0.3.
3. (θ − sin θ)/θ³ = Σₖ (−1)ᵏ θ²ᵏ/(2k+3)!; the (144) coefficient = 1/12 + θ²/720 + θ⁴/30240 + …; above the switch
   write (1 + cos θ)/sin θ = cot(θ/2).

## T3.3 se2_exp / se2_log

1. Exp: rotation from θ, translation V(θ)ρ with V = (sin θ/θ) I + ((1 − cos θ)/θ)[1]ₓ (158).
2. Reuse the coefficients of T3.1: (1 − cos θ)/θ = θ·B(θ). For Log, θ = atan2(R₁₀, R₀₀) and ρ = V⁻¹t.
3. V = A I + B′[1]ₓ is a scaled rotation, so V⁻¹ = (A I − B′[1]ₓ)/(A² + B′²), never singular for |θ| ≤ π.

## T3.4 se2_Ad / se2_Jr

1. Ad is T2.1's result. J_r: the left 2×2 is a transposed V; the third column is the hard part.
2. Implement J_l (164) and get J_r(τ) = J_l(−τ) by (76). Rewrite J_l's third column with a(θ) = (1 − cos θ)/θ² and
   b(θ) = (θ − sin θ)/θ³ so that nothing cancels.
3. J_l = [[A, −θa, ρ₁θb + ρ₂a], [θa, A, −ρ₁a + ρ₂θb], [0, 0, 1]], A = sin θ/θ. Check the third column at θ = 0:
   it must be (ρ₂/2, −ρ₁/2) for J_l.

## T3.5 se2_rminus

1. The value is one Log. The two blocks are (82) and (83), both in terms of J_r⁻¹ at ±τ.
2. J_l⁻¹(τ) = J_r⁻¹(−τ) by (76). J_r⁻¹ of SE(2): invert J_r blockwise, it is [[V′, c], [0, 1]].
3. [[V′, c], [0, 1]]⁻¹ = [[V′⁻¹, −V′⁻¹c], [0, 1]]; J_Y = J_r⁻¹(τ), J_X = −J_r⁻¹(−τ).

## T3.6 beacon_expect

1. e = Rᵀ(b − t). H_X is T2.3; H_b is the rotation that e applies to b.
2. H_X = −[I  Rᵀ[1]ₓ(b − t)], H_b = Rᵀ.
3. `-np.hstack([np.eye(2), (R.T @ J1 @ (b - t))[:, None]])`. If the FD test fails only at θ ≠ 0, you have R where
   Rᵀ belongs.

## T3.7 eskf_predict / eskf_update

1. Predict is (99)–(100) with F and G from the ⊕ blocks. Update is a Kalman update with H from T3.6 and ⊕ instead of +.
2. F = Ad_{Exp(−u)} (no inverse), G = J_r(u). Gain: solve Z Kᵀ = H P with `cho_solve(cho_factor(Z), H @ P).T`. Apply
   δx on the right: X Exp(δx).
3. Joseph: (I − KH) P (I − KH)ᵀ + K Q_meas Kᵀ, then, if reset, J_r(δx) P J_r(δx)ᵀ; symmetrize with ½(P + Pᵀ).

## T3.8 sam_linearize / sam_solve

1. Stack blocks of rows: 3 for the prior, 3 per motion, 2 per beacon. Each residual touches at most two column blocks.
2. Ω^{T/2} = L⁻¹ for Σ = LLᵀ. The residual is measurement − expectation, so each block of J is −Ω^{T/2} times the
   expectation's Jacobian: motion uses se2_rminus's blocks, beacon uses beacon_expect's.
3. Prior row: +Sp·J_Y of (X₀ ⊖ prior). Motion rows: −Su·J_X at pose i, −Su·J_Y at pose j. Beacon rows: −Sy·H_X at the
   pose, −Sy·H_b at the landmark. Solve with `np.linalg.lstsq(J, -r)`.

## T4 debug

1. Run `pytest exercises/tests/test_T4.py -v`. Each failing test names the place to look.
2. Evaluate Exp at θ = 0; compare F with the inverse of the generic adjoint; FD-check H at a turned pose, not at I;
   ask in which tangent δx lives.
3. See `solutions/T4.md` (only after the first two clues).

## T5 robot

1. Task 2: once ANIS ≈ 2, NIS can no longer tell whether R_proc or Q_meas is wrong. Look at NEES per component of the
   error (ρ₁, ρ₂, θ) to see which direction is overconfident.
2. Task 3: the overconfident direction is lateral, ρ₂. Which term of (93) drives lateral motion?
3. Task 4: the reset fixes the tangent, not the linearization point of H. Task 5: gate on zᵀZ⁻¹z before the update,
   with the threshold `scipy.stats.chi2.ppf(0.99, 2)`.
