# T2 — Derivations

Do them on paper. Every one is a claim the chapter states without proof (or proves later) that the
T3 code and the T5 initializer rely on. Compare with `solutions/T2.md` only after you have an answer.
Clues: `just clue hz-mvg2 1 T2.<n> <1|2|3>`.

## T2.1 The projective ambiguity (1.1) and the 7-point count (p. 11)

(a) Show that P_j X_i = x_ij implies (P_j H⁻¹)(H X_i) = x_ij for any non-singular 4×4 H.
(b) Say exactly what goes wrong if H is singular. Two separate things break.
(c) Count unknowns and measurements for two uncalibrated views of N points, allowing for (1.1),
and show that N ≥ 7. Then explain the same 7 from the degrees of freedom of F.

## T2.2 The circular points (p. 5)

(a) Show that (1, ±i, 0)ᵀ lie on every circle (x − aw)² + (y − bw)² = r²w².
(b) Show the converse: a conic through both circular points is a circle (possibly degenerate).
(c) Use (a) and (b) to explain why a circle is fixed by 3 points and a general conic by 5.

## T2.3 The canonical camera and the plane homography (p. 7)

(a) For P = [I | 0], show that every point (X, Y, Z, T)ᵀ with X, Y, Z fixed and any T images to the
same point, and identify the set of those points in ℙ³.
(b) For a general P = [p₁ p₂ p₃ p₄], show that points on the plane Z = 0 map by H = [p₁ p₂ p₄].
(c) Show that H is singular exactly when the camera centre lies on that plane. What is the robot case?

## T2.4 Same centre, any scene: a homography (Fig. 1.1c, p. 9)

(a) Two cameras P = K[R | −RC̃] and P′ = K′[R′ | −R′C̃] share the centre C̃. Show that x′ = H′x for every
scene point, finite or at infinity, and give H′. Show it is non-singular.
(b) Reduce it to p. 204's H′ = KRK⁻¹.
(c) What does (9.1), F = [e′]× P′P⁺ with e′ = P′C, give in this case?
(d) A tracked robot turns on the spot by 8° with the camera 0.25 m ahead of the turning centre. How far
does the camera centre move? Is the pair still a homography? (T5 has this pair.)

## T2.5 Angles from the IAC, with numbers (p. 9; eq. 8.9 and Result 8.17, p. 210)

(a) With ω = (KKᵀ)⁻¹, show that xᵀωy = (K⁻¹x)ᵀ(K⁻¹y), and so (8.9) is the cosine of the angle between
the back-projected rays.
(b) For the lecture's K (f = 500 px, principal point (320, 240)), write ω up to scale.
(c) Compute the angle between the rays through the principal point and through (640, 240). Then compute
what a camera that believes f = 400 px, and one that believes f = 600 px, would report.

## T2.6 Counting for three views (p. 13)

(a) The trifocal tensor has 27 entries. Each point triplet gives 4 linear equations (p. 13). Show that
7 triplets are needed for a linear solution.
(b) Show that 6 triplets suffice in principle (p. 13) by counting the degrees of freedom of three
uncalibrated cameras up to (1.1), and what each triplet adds.
(c) The difference between (a) and (b) is the number of internal constraints of the tensor. How many?
