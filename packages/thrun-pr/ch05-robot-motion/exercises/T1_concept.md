# T1 — Concept check

Answer in one or two sentences each. Then compare with `solutions/T1.md`.

1. p(xₜ ∣ uₜ, xₜ₋₁) appears in one line of the Bayes filter (Table 2.1). Which line, and which line of the particle filter (Table 4.3) calls the sampler of this chapter?
2. p. 118 argues that a motion model which overestimates the uncertainty is the safer choice. Why is it safer for a particle filter, and what does it cost you?
3. The book suggests the velocity model for planning and the odometry model for estimation (p. 121). Give the reason, and say which of the two the tracked robot's localization should use and when that answer changes.
4. With only v̂ and ω̂ perturbed, every sample lies on a 2-D surface in (x, y, θ) (p. 129). Why, and what does γ̂ fix? Does the bicycle of book exercise 4 have the same problem?
5. Table 5.1 line 2 divides by zero for one very common motion. Which one, and why does the circle's geometry make that happen (p. 130)?
6. Table 5.4's twelve-uniform sampler: what is its variance, and what range do its values actually lie in? Compare with p. 132.
7. The odometry model treats the odometry poses as a control, not as a measurement (p. 132–134). Name the two reasons, and say why the odometry frame's origin and heading do not matter.
8. Table 5.5 says the difference δrot2 − δ̂rot2 must be truncated to [−π, π] (p. 135). Construct a two-step motion in which forgetting it costs you the density, and say why the bug shows up only some of the time.
9. Why is sampling from the motion model easier than evaluating its density (p. 125)? Which of the two does MCL use and which does grid localization use?
10. Eq. 5.48 conditions on the map by checking only the final pose (p. 143). When is that a good approximation, and what do you change on the robot so that it stays one?
