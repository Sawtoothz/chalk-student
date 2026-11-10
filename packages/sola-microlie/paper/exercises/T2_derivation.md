# T2 — Derivations

Do these by hand in `lesson-notes.md` (your file), then compare with `solutions/T2.md`. Each one ends with numbers;
check yours with the functions you write in T3 (the tests do not grade T2).

Notation as in the paper: right ⊕, J^𝒴_𝒳 is the right Jacobian (41a), SE(2) tangent τ = (ρ, θ), [1]ₓ = [[0, −1], [1, 0]]
(155), X = [[R, t], [0, 1]].

## T2.1 The adjoint of SE(2), (159)

Start from (29), Ad_𝒳 τ = (𝒳 τ^ 𝒳⁻¹)^∨, with τ^ from (153). Multiply the block matrices, use R[1]ₓRᵀ = [1]ₓ for a
planar rotation, and read off the 3×3 matrix that maps (ρ, θ) to the vee of the product. You should get
Ad_X = [[R, −[1]ₓ t], [0, 1]] (p. 16).

Numbers: X = pose(1, 2, π/2). Write Ad_X.

## T2.2 The two blocks of right minus, (82) and (83)

τ = 𝒴 ⊖ 𝒳 = Log(𝒳⁻¹𝒴). Derive J^τ_𝒴 = J_r⁻¹(τ) and J^τ_𝒳 = −J_l⁻¹(τ) using only the chain rule (58) and the elementary
blocks: inverse (62), composition (65)–(66), Log (79), and Ad_{Exp(τ)} = J_l(τ) J_r⁻¹(τ) (75). This is the proof
under (83), p. 11; write every step.

Numbers: X = I, Y = pose(1, 0, π/2). Give τ, J^τ_Y and J^τ_X in closed form (they contain π/4 and 1/2).

## T2.3 The measurement Jacobian of §V-A

e = 𝒳⁻¹·b (95). Show H = J^e_𝒳 = −[I₂  Rᵀ[1]ₓ(b − t)] by chaining the action block (166), taken at the group element
𝒳⁻¹ (not at 𝒳), with the inverse block (62). Then give J^e_b from (167).

Numbers: X = pose(1, 2, π/2), b = (2, 0). Give e, H and J^e_b.

## T2.4 The covariance reset after the update (not in the paper)

After (101), 𝒳̂⁺ = 𝒳̂ ⊕ δx. Write the true state as 𝒳 = 𝒳̂ ⊕ ε, with ε ~ N(δx, P⁺) in the tangent at 𝒳̂ (that is what
(102) gives you). Define the new error ε⁺ by 𝒳 = 𝒳̂⁺ ⊕ ε⁺. Show that to first order ε⁺ ≈ J_r(δx)(ε − δx), and
conclude P ← J_r(δx) P⁺ J_r(δx)ᵀ. Which approximation of (43) do you use, and why does (102) correspond to J_r ≈ I?

Numbers: δx = (0.1, −0.05, 0.2), P⁺ = diag(0.05, 0.05, 0.1)². Give J_r(δx) to four decimals and the reset P. By what
fraction (Frobenius norm) does the reset change P?
