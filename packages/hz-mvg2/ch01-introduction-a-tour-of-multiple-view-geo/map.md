---
book: hz-mvg2
chapter: 1
title: Introduction – a Tour of Multiple View Geometry
printed_pages: [1, 22]
pdf_pages: [19, 40]
lesson: t3.1   # proposed; books.yaml has no lesson ids for hz-mvg2 yet (track t3)
prereqs:
  - t2.6 homogeneous points and transforms (Barfoot ch. 7 §7.3.1; the 4×4 pose acting on (x, y, z, 1) is the Euclidean special case of X' = H X on p. 3)
  - linear algebra: rank, null space, solving A f = 0 by SVD (step (ii) on p. 12 and the factorization algorithm on p. 14 both rely on it)
  - complex numbers in a quadratic form (circular points (1, ±i, 0)ᵀ on p. 5; the absolute conic on p. 6 has no real points)
feeds:
  - hz-mvg2 ch. 2–3 projective geometry of 2D and 3D (no lesson id yet); every informal claim of 1.1 becomes a definition there (line at infinity, circular points, Ω∞, angle formula 3.23)
  - hz-mvg2 ch. 6–8 camera models and the IAC ω; "calibrated = ω known" (p. 9) becomes ω = (K Kᵀ)⁻¹
  - hz-mvg2 ch. 9–12 two-view geometry; steps (i)–(iv) on p. 12 are ch. 11 (F), §9.5 (cameras from F) and ch. 12 (triangulation)
  - hz-mvg2 ch. 18–19 n-view methods and auto-calibration; 1.5 and 1.8 preview them
  - t2.8 graph SLAM and FAST-LIO2; bundle adjustment (p. 14) is the visual factor graph, and "initialize then refine" is how every VIO front end works
  - drone: monocular VIO cannot see metric scale; that is the similarity ambiguity of p. 11 with calibrated cameras, and the IMU is what removes it
  - tracked robot and quadruped: a camera over flat ground or a camera that only rotates gives a homography, not an F (Fig. 1.1 b, c, e and p. 16); a VO initializer that fits only F fails on exactly those frames
  - FORGE and GTSAM: projection factors are x = P X with P = K[R | t]; this chapter's P_{3×4} of rank 3 (p. 7) is the uncalibrated version
status: draft
---

# Chapter map

One idea: picture-taking is linear in homogeneous coordinates, and what a set of images cannot tell you is exactly a group of transformations. Projective space (1.1) makes central projection a 3×4 matrix (1.2). From point matches alone, cameras and points come back only up to a 4×4 projective transformation, eq. (1.1) (1.3–1.6). Pinning down the plane at infinity reduces that ambiguity to affine; pinning down the absolute conic, which is the same as calibrating the cameras, reduces it to similarity (1.7–1.8). Everything else in the chapter is a tour of the machinery (F, trifocal tensor, factorization, bundle adjustment) that the rest of the book builds, plus two applications (1.9–1.10). The chapter is informal by design (p. 1): no proofs, no estimation algorithms, two numbered equations.

| Section | Pages | Verdict | Time | What to take |
| --- | --- | --- | --- | --- |
| 1 (preamble) | 1 | skim | 2 min | Informal on purpose; precise versions start in ch. 2 |
| 1.1 Ubiquitous projective geometry: points at infinity, homogeneous coordinates, homogeneity | 1–3 | must | 30 min | (kx, ky, k) ~ (x, y, 1); points at infinity have last coordinate 0; X' = H_{(n+1)×(n+1)} X moves them to finite points |
| 1.1.1 Affine and Euclidean geometry | 3–6 | must | 35 min | The ladder: projective + line at infinity = affine; + circular points (2D) or absolute conic Ω∞ (3D) = Euclidean; perpendicularity is d₁ᵀ Ω∞ d₂ = 0 |
| 1.2 Camera projections (incl. "Cameras as points", Fig. 1.1) | 6–9 | must | 35 min | P = [I | 0] then a general rank-3 P_{3×4}; coplanar scene gives H_{3×3}; same camera centre means images differ by a homography, whatever the scene |
| 1.2 Calibrated cameras, Example 1.1 | 9–10 | must | 15 min | IAC ω = image of Ω∞; knowing ω lets you measure angles between rays; single-view reconstruction from vanishing points (Fig. 1.2) |
| 1.3 Reconstruction from more than one view | 10–12 | must | 25 min | Eq. (1.1) projective ambiguity; at least 7 points; x'ᵀ F x = 0, F rank 2; the four-step outline on p. 12 and the warning not to implement it from the outline |
| 1.4 Three-view geometry | 12–13 | skim | 10 min | Trifocal tensor T_i^{jk}, 27 entries, eq. (1.2) point–line–line incidence; 4 equations per point triplet, 7 triplets linearly, 6 non-linearly |
| 1.5 Four view geometry and n-view reconstruction | 13–14 | skim | 10 min | Quadrifocal tensor rarely used; affine factorization by SVD (all points in all views); bundle adjustment = ML, needs an initial guess |
| 1.6 Transfer (Fig. 1.3, 1.4) | 14–16 | skim | 10 min | x'' = P'' X after triangulating from two views; with a plane or pure rotation one view suffices (homography); Fig. 1.4 is the projective ambiguity drawn as a mug |
| 1.7 Euclidean reconstruction | 16–17 | must | 15 min | Calibration known ⇔ Euclidean structure known; cones of the ω_i meet in Ω∞; two views give two solutions, three give one |
| 1.8 Auto-calibration | 17–18 | skim | 10 min | Constant calibration; plane at infinity first (hard), then ω linearly (easy); square pixels: 2 rays per image, 8 rays fix a conic, so 4 images |
| 1.9 The reward I: 3D graphical models (Fig. 1.5, 1.6) | 18–20 | skim | 5 min | Pipeline: projective reconstruction → auto-calibration → epipolar-restricted dense matching |
| 1.10 The reward II: video augmentation (Fig. 1.7) | 19–21 | skim | 5 min | Camera motion must be Euclidean, not projective, to insert an object; zoom and principal point may vary |
| Exercises | — | none in the book | in package | Ch. 1 has no end-of-chapter exercises; the package writes its own (T1–T5, `exercises/README.md`) |

Total reading at "must": about 2.5 hours (2 h 35 min), plus about 50 minutes of skims. Coding (exercises T3–T4) about 3 hours, T5 about 2 hours; this is a tour chapter, so the coding is numerical verification of the chapter's claims, not an algorithm. Page 22 is blank.

Depth note: no `learner.yaml` exists yet, so depth is set from Aun's profile alone. He already uses homogeneous transforms and BA daily (GTSAM); the new material is the projective view of them: points at infinity as ordinary points, ambiguity as a group, calibration as a conic. Spend the time there, not on homogeneous-coordinate mechanics.

## Inventory

Definitions: projective transformation (preserves straight lines, p. 1; non-singular H_{(n+1)×(n+1)} on homogeneous coordinates, p. 3), ideal points / points at infinity (p. 2), homogeneous coordinates as equivalence classes (p. 2), projective space ℙⁿ (p. 2), line at infinity and plane at infinity (p. 2), Euclidean transform (p. 2), affine transformation (p. 3, and as "maps the distinguished line to the distinguished line", p. 4), affine geometry (projective plane plus a distinguished line, p. 4), parallelism and equal intervals in affine geometry (p. 4), conic (p. 5), circular points (1, ±i, 0)ᵀ (p. 5), absolute conic Ω∞: X² + Y² + Z² = 0, T = 0 (p. 6), conjugate points w.r.t. Ω∞ (p. 6), central projection, centre of projection, image plane (p. 6), camera matrix P, 3×4 of rank 3 (p. 7), image of the absolute conic ω, calibrated camera (p. 9), projective ambiguity / projective reconstruction (p. 11), critical configurations (p. 11), fundamental matrix F, rank 2 (p. 11), triangulation (p. 12), trifocal tensor T_i^{jk}, covariant / contravariant indices, internal constraints (pp. 12–13), quadrifocal tensor (p. 13), affine camera, factorization algorithm, projective factorization (pp. 13–14), bundle adjustment (p. 14), transfer (p. 14), auto-calibration (p. 17), square-pixel constraint (p. 18).

Algorithms: no numbered algorithm boxes. Two outlines: the fundamental-matrix reconstruction steps (i)–(iv) (p. 12, with the book's own warning that they "should not be implemented directly from this brief description") and the transfer steps (i)–(iii) (p. 16). Named only: affine factorization by SVD (p. 14), bundle adjustment (p. 14), linear auto-calibration given the plane at infinity (p. 18).

Equations (numbered and unnumbered, by page):
- p. 2: dehomogenization (kx, ky, k) → (x, y); (x, y, 0) is a point at infinity.
- p. 3: X' = H_{(n+1)×(n+1)} X.
- p. 5: circle (x − aw)² + (y − bw)² = r²w²; circular points (1, ±i, 0)ᵀ; x² + y² = 0, w = 0.
- p. 6: absolute conic X² + Y² + Z² = 0, T = 0; conjugacy d₁ᵀ Ω∞ d₂ = 0.
- p. 7: P = [I_{3×3} | 0₃]; (x, y, w)ᵀ = P_{3×4} (X, Y, Z, T)ᵀ; plane Z = 0 gives (x, y, w)ᵀ = H_{3×3} (X, Y, T)ᵀ.
- p. 8 (Fig. 1.1): x_i = H_{3×3} X_i (plane to image), x'_i = H'_{3×3} x_i (same centre, two image planes).
- p. 11: P X_i = x_i, P' X_i = x'_i; **(1.1)** P_j X_i = (P_j H⁻¹)(H X_i); x'_iᵀ F x_i = 0.
- p. 12: **(1.2)** Σ_{ijk} xⁱ l'_j l''_k T_i^{jk} = 0.
- p. 13: det F = 0.
- p. 16: x'' = P'' X.

Equations you will implement (as small numerical functions, each with an oracle): dehomogenization with a scale-free point-at-infinity test inside `dehom` (p. 2); X' = H X on ℙ² and ℙ³ (p. 3); circular points lie on every circle (p. 5; oracle: the complex quadratic form evaluates to 0 for random a, b, r); perpendicularity via d₁ᵀ Ω∞ d₂ with Ω∞ = I in a Euclidean frame (p. 6; oracle: dot product of directions); central projection x = P X with P = [I | 0] and with a random rank-3 P (p. 7; oracle: ray test, all (X, Y, Z, T) with fixed X, Y, Z land on one image point); plane-induced H_{3×3} = columns 1, 2, 4 of P (p. 7; oracle: equals P X for points with Z = 0); same-centre homography of Fig. 1.1c (oracle: images of random 3D points, no structure needed); (1.1) projective ambiguity (oracle: identical reprojections for random non-singular 4×4 H); the epipolar constraint as a distance in pixels from x'ᵀ F x, and det F = 0, on a synthetic two-camera scene (pp. 11, 13; F supplied by a reference formula in `models.py`, since computing it is ch. 9); linear triangulation, step (iv) (p. 12; oracle: recovers the generating X to 1e-9 on noise-free data); transfer x'' = P'' X (p. 16) is triangulate-then-project, covered in card C7 and T5 rather than as its own function.

Equations you will derive by hand: (1.1) and why H must be non-singular; why (1, ±i, 0)ᵀ lie on every circle (p. 5); why a circle needs 3 points and a general conic 5 (p. 5); why P = [I | 0] sends (X, Y, Z, T) to (X, Y, Z) and every point of the ray to the same image point (p. 7); why two images with the same centre are related by a homography (Fig. 1.1c, p. 9); the counting arguments: at least 7 points for two views (p. 11), 4 equations per point triplet and 7 triplets for a linear trifocal solve with 27 entries (p. 13), 2n rays and 8 rays for square-pixel auto-calibration (p. 18).

## Dependencies inside the chapter

```
1.1 homogeneous coords, points at infinity, X' = H X
 ├── 1.1.1 ladder: projective ⊃ affine (line/plane at ∞) ⊃ Euclidean (circular points / Ω∞)
 │                                                                   │
 └── 1.2 central projection x = P X, P 3×4 rank 3                    │
       ├── plane → H 3×3; same centre → H' (Fig. 1.1)  ── 1.6 transfer by homography
       ├── calibrated camera = IAC ω known  ←────────────────────────┘
       │      └── Example 1.1 single-view reconstruction
       └── 1.3 two views: ambiguity (1.1), F, triangulation
             ├── 1.4 three views: trifocal tensor (1.2)
             ├── 1.5 n views: factorization, bundle adjustment
             ├── 1.6 transfer x'' = P'' X
             └── 1.7 Euclidean reconstruction (needs ω, i.e. Ω∞)
                   └── 1.8 auto-calibration (find Ω∞ without ω)
                         └── 1.9, 1.10 applications
```

## What this chapter does not cover (and where it is)

- Precise definitions of lines, conics, the line at infinity and the circular points in ℙ²: H&Z ch. 2 (pp. 25–64).
- Planes, quadrics, Ω∞ and the angle formula (3.23) in ℙ³: H&Z ch. 3 (pp. 65–86); conjugate points §2.8.1 (p. 58); Fig. 3.8 (p. 83).
- Estimating H from correspondences (DLT, normalization, cost functions): H&Z ch. 4; error analysis ch. 5.
- The camera matrix as K[R | t], its decomposition, and the IAC ω = (K Kᵀ)⁻¹: H&Z ch. 6–8.
- Epipolar geometry and F from P, P'; cameras from F (§9.5, p. 253): H&Z ch. 9; computing F (the normalized 8-point and 7-point methods): ch. 11; the essential matrix for calibrated cameras: §9.6.
- Triangulation done properly (optimal, not just linear): H&Z ch. 12.
- Trifocal tensor in full: H&Z ch. 15–16; quadrifocal tensor ch. 17.
- Factorization and bundle adjustment: H&Z ch. 18 and Appendix 6 (sparse Levenberg–Marquardt). Robot-side factor-graph view: lesson t2.8.
- Auto-calibration algorithms: H&Z ch. 19; critical configurations: ch. 22.
- Noise, outliers and RANSAC: not in this chapter at all (H&Z ch. 4 §4.7). Every real use of p. 12 needs them.
- Lens distortion: H&Z §7.4; the chapter's camera is a pure pinhole.
- Metric scale from other sensors (IMU, wheel odometry, LiDAR): outside H&Z; lessons t2.8 and t2.11.
