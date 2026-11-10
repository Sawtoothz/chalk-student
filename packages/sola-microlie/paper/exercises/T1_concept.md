# T1 — Concept check

Answer in one or two sentences each, then compare with `solutions/T1.md`. Page numbers are the paper's
(arXiv:1812.01537v9; PDF page = printed page).

1. The covariance of an SE(2) pose stored as a 3×3 matrix is 3×3, and that of an SE(3) pose stored as a 4×4 matrix is
   6×6. Why not 9×9 and 16×16? Where is this covariance defined?
2. Right ⊕ (25) and left ⊕ (27): in which frame is τ expressed in each? Which one does the paper default to, and which
   one does the gyro integration (56) R_k = R_{k−1} Exp(ω δt) use?
3. What does Ad_𝒳 do to a tangent vector, and how does (32) 𝒳 ⊕ τ = (Ad_𝒳 τ) ⊕ 𝒳 tell you how to convert a
   covariance from the local tangent at 𝒳 to the global tangent at ℰ?
4. The right Jacobian (41a) is the ordinary limit definition of a derivative with two operators replaced. Which two,
   by what? What are the dimensions of J^{𝒳·p}_𝒳 for 𝒳 ∈ SE(3), p ∈ ℝ³?
5. J_r⁻¹ appears in the Jacobian of Log (79) and in both ⊖ blocks (82)–(83). For SO(3), at which angles does J_r(θ)
   become singular, and why does that never bite inside a filter whose Log returns |θ| ≤ π?
6. In the ESKF of §V-A, F = Ad_{Exp(u)}⁻¹ and G = J_r(u) (100). Which elementary blocks are they, and why is F not
   the identity even though the error δx is a local (body-frame) quantity?
7. Two poses 𝒳₁, 𝒳₂ in the plane. Compare the position part of 𝒳₂ ⊖ 𝒳₁ when the pose is treated as SE(2) and when
   it is treated as the composite ⟨ℝ², SO(2)⟩ (Ex. 7). Which do you want for the error state of a filter whose
   covariance you will gate on?
8. Why does the smoothing problem of Fig. 12 need the prior factor on 𝒳₁? What happens to JᵀJ without it?
9. A unit quaternion and its negative are the same rotation. Why does the quaternion Log (133) flip q to w ≥ 0
   first, and what does it return otherwise?
10. The update (101)–(102) moves 𝒳̂ by δx but leaves P as it is. Which tangent space does P describe after the
    update, which one should it describe, and when does the difference matter?
