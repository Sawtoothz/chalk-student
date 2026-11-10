# T1 — Concept check

Answer in one or two sentences each. Then compare with `solutions/T1.md`.

1. Three assumptions make the KF posterior exactly Gaussian. Name them and say which one a tracked robot with a velocity motion model violates.
2. Line 4 of Table 3.1 inverts a matrix. What size is it, and why does that matter more than the size of Σ?
3. Predict and update: which one increases uncertainty, which one decreases it, and why is the posterior after an update always narrower than both the prior and the measurement?
4. In the EKF, where does g appear and where does G appear? What goes wrong if you use G μ in line 2?
5. The EKF linearizes h at μ̄ₜ. Why not at μₜ₋₁?
6. Name the two factors (p. 61, p. 80) that decide how bad the EKF linearization is. Which one can you control at run time, and how?
7. Why does the UKF capture more of the Taylor expansion than the EKF, and what does that cost per step?
8. State the duality between KF and IF in one sentence, and give one situation where the IF is the only sensible choice.
