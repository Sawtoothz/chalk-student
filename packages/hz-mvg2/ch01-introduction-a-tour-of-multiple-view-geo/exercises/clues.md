# Clues

Three steps per exercise: direction, key idea, near-solution. Open one at a time with
`just clue hz-mvg2 1 <exercise> <n>`; each one you open is recorded in `learner.yaml`.

## T1 concept

No clues. Every answer is on the page cited in the question.

## T2.1 Projective ambiguity

1. (a) is one line of associativity. For (b), ask what H⁻¹ needs, and what H does to its null vector.
2. A singular H has HN = 0 for some N ≠ 0; 0 is not a point of ℙ³, and X and X + λN collide. For (c), count 11 per camera, 3 per point, 2 per image point, and subtract 15.
3. 22 + 3N − 15 ≤ 4N. For the F version: 9 entries − scale − det = 7, one equation per match.

## T2.2 Circular points

1. Substitute w = 0 first: what survives of the circle's equation?
2. x² + y² at (1, ±i): use the plain square, i² = −1. For the converse, write the general conic with 6 coefficients and substitute (1, i, 0); split real and imaginary parts.
3. You get A = C and B = 0. A circle is then 5 − 2 conditions.

## T2.3 Canonical camera and plane homography

1. Multiply [I | 0] by (X, Y, Z, T)ᵀ and see which coordinate disappears.
2. The points that differ only in T are combinations of (X, Y, Z, 0)ᵀ and (0, 0, 0, 1)ᵀ. For (b), write PX as a sum of the columns of P weighted by X, Y, Z, T.
3. For (c): H(X, Y, T)ᵀ = 0 means P(X, Y, 0, T)ᵀ = 0, so that point is the null vector of P.

## T2.4 Same centre

1. Factor KR out of K[R | −RC̃].
2. x = KR(X̃ − C̃). Solve for X̃ − C̃ and substitute into x′. Then do the same for X = (d, 0)ᵀ.
3. H′ = K′R′RᵀK⁻¹. For (c), e′ = P′C with C = (C̃, 1)ᵀ. For (d), a chord of a circle of radius 0.25 m through 8°.

## T2.5 Angles from the IAC

1. Write (KKᵀ)⁻¹ as a product of two inverses.
2. xᵀωy = (K⁻¹x)ᵀ(K⁻¹y), and K⁻¹x is the ray direction in the camera frame.
3. d₂ ∝ ((640 − 320)/f, 0, 1). θ = atan(320/f) for f = 500, 400, 600.

## T2.6 Counting for three views

1. Unknowns up to scale, divided by equations per triplet; round up.
2. Three cameras have 33 DoF; (1.1) removes 15. Each triplet: 6 numbers measured, 3 unknowns added.
3. 26 / 4 → 7; 18 / 3 = 6; the difference between 26 and 18.

## T3.1 dehom (C1)

1. Normalize each row to unit length before looking at its last coordinate.
2. A point is at infinity when |w| / ‖X‖ < tol. Make the input 2-D first with `np.atleast_2d`.
3. `U = Xh / np.linalg.norm(Xh, axis=1, keepdims=True)`; raise if any `abs(U[:, -1]) < tol`; else `Xh[:, :-1] / Xh[:, -1:]`.

## T3.2 circle_conic (C2)

1. Expand (x − aw)² + (y − bw)² − r²w² and read off the coefficients of x², xy, y², xw, yw, w².
2. In a symmetric C, the coefficient of xw is 2·C[0, 2]. So C[0, 2] = C[2, 0] = −a.
3. [[1, 0, −a], [0, 1, −b], [−a, −b, a² + b² − r²]].

## T3.3 camera_centre, depth (C3)

1. The centre is the null vector of a 3×4 matrix: an SVD gives it for any P, even when the centre is at infinity.
2. `_, s, Vt = np.linalg.svd(P)`; the centre is `Vt[-1]`. Depth is eq. 6.15: sign(det M) · w / (T ‖m³‖), with M the left 3×3 and m³ its third row.
3. Check `s[2] < rank_tol * s[0]` before returning. In depth, w = `Xh @ P[2]`; the sign of det M is what makes it survive P → −P.

## T3.4 plane_homography, rotation_homography (C4)

1. For the plane, which column of P multiplies Z? For the rotation, T2.4 gives H′; you need K⁻¹ without `inv`.
2. H = P[:, [0, 1, 3]], then a condition-number check. K is upper triangular: K R K⁻¹ = ((K⁻ᵀ)(K R)ᵀ)ᵀ.
3. `solve_triangular(K.T, (K @ R_rel).T, lower=True).T`, then divide by the Frobenius norm.

## T3.5 apply_ambiguity (C5)

1. Cameras get H⁻¹ on the right, points get H on the left; points are rows.
2. P H⁻¹ = (H⁻ᵀ Pᵀ)ᵀ, which is one `np.linalg.solve(H.T, P.T)`. Points: `Xh @ H.T`.
3. Normalize each camera by its Frobenius norm and each point row to unit length; check `np.linalg.cond(H)` first.

## T3.6 epipolar_distance_px (C6)

1. l′ = F x is a line (a, b, c); the distance of a pixel (u, v, 1) to it is a 2-D formula.
2. distance = |x′ᵀ l′| / √(a² + b²). Not ‖l′‖: c has the units of pixels·a and swamps the denominator.
3. `l = x @ F.T`; `np.abs(np.sum(xp * l, axis=1)) / np.hypot(l[:, 0], l[:, 1])`.

## T3.7 triangulate (C7)

1. x × (PX) = 0 gives two independent linear equations in X per view. Stack them and take a null vector.
2. Rows x·p³ᵀ − p¹ᵀ and y·p³ᵀ − p²ᵀ, with (x, y) the pixel after dividing by w. Normalize each row, then SVD.
3. `x = x / x[2]`; `rows += [x[0]*P[2] - P[0], x[1]*P[2] - P[1]]`; `X = np.linalg.svd(A)[2][-1]`. Do not set T = 1.

## T3.8 ray_angle (C8)

1. Back-project instead of forming ω: d = K⁻¹x is the ray.
2. θ = atan2(‖d₁ × d₂‖, d₁ · d₂) is accurate at 0 and at π; arccos is not.
3. `d1 = solve_triangular(K, np.atleast_2d(x1).T, lower=False).T`, same for d2, then the atan2 row-wise.

## T3.9 affine_upgrade, metric_upgrade (C9)

1. Affine: you need any well-conditioned H with H⁻ᵀπ ∝ e₄; an orthogonal H has H⁻ᵀ = H. Metric: factor Ω∞ = MᵀωM.
2. A Householder reflection Q = I − 2vvᵀ/(vᵀv) with v = p + sign(p₄) e₄ (p = π/‖π‖) sends p to a multiple of e₄. For metric, Cholesky Ω∞ = LLᵀ and use Lᵀ as the top-left block.
3. Symmetrize Ω∞ and flip its sign if its trace is negative before `np.linalg.cholesky`; `H[:3, :3] = L.T`.

## T4 debug

1. There are five bugs, one per function. Run each grader test and read its message; each test calls one function only.
2. Two are normalisation (what you divide by), two are sign or transpose, one is the wrong column.
3. Compare each line with its card in `translate.md` (C3, C4, C6, C7, C9): the robust version names the trick the bug breaks.

## T5 robot

1. Fit both models on every pair and compare residuals in pixels before deciding anything. Estimate the noise from the F residual.
2. With noise only, the H residual is about √2 times the F residual (both images' noise enters the transfer, one dimension enters the epipolar distance). Much more than that means real parallax. For scale, triangulate the floor points and fit a plane: camera 1's height above it is h in metres.
3. Gate the floor points on parallax (C8's ray_angle between K⁻¹x and RᵀK⁻¹x′) before the plane fit, and refit F on random halves to see whether the translation direction is stable.
