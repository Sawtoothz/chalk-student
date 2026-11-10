# T2 — Derivations

Do these by hand in `lesson-notes.md` (your file), then compare with `solutions/T2.md`. Each ends in numbers;
check them with your T3 functions once they pass.

## T2.1 From the product of Gaussians to the Kalman gain (pp. 138, 149–150)

Start from the p. 138 posterior mean μ = (σ̄²μ_z + σ_z²μ̄)/(σ̄² + σ_z²). Rewrite it as μ = μ̄ + K(μ_z − μ̄) and read off
K. Then show the three variance forms of p. 150 are equal: σ̄²σ_z²/(σ̄² + σ_z²) = Kσ_z² = (1 − K)σ̄².
Numbers: the p. 169 example (prior (10, 3), u = 1, R_proc = 2², z = 12, Q_meas = 3.5²). Compute x̄, P̄, y, S, K, x and
P by hand, P by all three forms.

## T2.2 Steady state, its inverse, and the book's 0.13232 (pp. 146, 148, 168)

(a) Require one predict + update to return the same posterior variance. Derive P∞² + R_proc·P∞ − R_proc·Q_meas = 0,
take the positive root, and rationalize it so nothing cancels when R_proc ≫ Q_meas. Show K∞ = P∞/Q_meas.
(b) Show that K∞ depends on R_proc and Q_meas only through r = R_proc/Q_meas, and invert: r as a function of K∞.
(c) Book exercise p. 148 with numbers: P∞, P̄∞ and K∞ for (R_proc, Q_meas) = (40, 2) and (2, 40). Which is smaller,
and why is one of them below 2?
(d) Which r gives the book's "experimentally derived" K = 0.13232 (p. 168)? Compare with r for each filter in the
chapter (table in `map.md`, "Checked against a run"). Which filter was it derived for?

## T2.3 The price of a wrong gain (Joseph form, scalar)

(a) With x = x̄ + K(z − x̄), prior error ē ~ N(0, P̄) and measurement noise v ~ N(0, Q_meas) independent, show that the
posterior error variance is (1 − K)²P̄ + K²Q_meas for any K, and that it equals P̄Q_meas/(P̄ + Q_meas) at K = P̄/(P̄ + Q_meas).
(b) For a fixed K on the random-walk model, find the steady error variance (substitute P̄ = P + R_proc and solve).
State the stable range of K.
(c) Show that this variance is minimal at K∞ (differentiate; the condition reduces to the quadratic of T2.2).
(d) Numbers for the dog (R_proc = 2, Q_meas = 4.5): the variance at K∞, at K = 0.2, at 0.8 and at the book's 0.13232.

## T2.4 A wrong u is an offset, not a lag (pp. 165–167)

(a) A fixed-gain filter adds u per step while the truth moves u − b. Write the recursion of the mean error and find its
steady value. Check the sign: is the estimate ahead of or behind the truth?
(b) Numbers: b = 1 m/step with K = 0.48051 (dog steady gain) and with K = 0.2 (the (2, 40) filter of T2.2).
(c) Contrast with a truth that is a sine in time, tracked with u = 0: what kind of error appears, and which way does
it move as R_proc grows? Why does neither case need a nonlinear filter?
