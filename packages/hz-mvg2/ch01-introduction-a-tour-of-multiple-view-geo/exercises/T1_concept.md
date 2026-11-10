# T1 — Concept check

Answer each in one or two sentences, from the chapter (printed pages 1–22). Then compare with `solutions/T1.md`.

1. Why is (x, y, 0)ᵀ called a point at infinity, and what happens to it under a Euclidean transformation compared with a general projective transformation (pp. 2–3)?
2. Projective geometry has no parallel lines and no ratios of lengths. What one object do you add to the projective plane to get affine geometry, and which transformations keep it fixed (pp. 3–4)?
3. To go from affine to Euclidean geometry you add another object, in the plane and in space. Name both, say where each one lives, and say why you will never see a real point of either (pp. 5–6).
4. A camera matrix P is 3×4 of rank 3 (p. 7). What is its null vector, and how many degrees of freedom does P have?
5. Fig. 1.1 shows two situations in which two images are related by a 3×3 homography. Name them. Which of the two holds whatever the scene, and what does that mean for a tracked robot's visual-odometry initializer?
6. What does "calibrated camera" mean in this chapter (p. 9), and what can you measure from a single image of a calibrated camera that you cannot measure from an uncalibrated one?
7. From point matches alone, with no calibration, what can be reconstructed and up to what (p. 11)? How many matches at least, and what is a critical configuration?
8. The fundamental matrix is 3×3. What constraint does it put on a match, what is its rank, and how many degrees of freedom does it have (pp. 11, 13)? Why does the rank matter in code?
9. The chapter outlines reconstruction from two views in four steps (p. 12) and then warns you not to implement it from the outline. Give two things the outline leaves out that a working implementation needs.
10. Two calibrated views and three calibrated views: how many Euclidean reconstructions does each allow (p. 17), and what is left unknown even in the best case?
