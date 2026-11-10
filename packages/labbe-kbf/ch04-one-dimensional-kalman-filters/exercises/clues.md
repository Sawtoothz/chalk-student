# Clues

Three steps per exercise: direction, key idea, near-solution. Open one at a time with
`just clue labbe-kbf 4 <exercise> <n>`, e.g. `just clue labbe-kbf 4 T3.3 1`; each one opened is recorded in
`learner.yaml`. Each clue is one line on purpose.

## T1 concept

No clues; the answers are on pp. 134–138, 146–153, 155–161 and 165–168, and in translate.md C3–C4.

## T2.1 Product of Gaussians to the Kalman gain

1. Add and subtract σ̄²μ̄ in the numerator of the p. 138 mean, then split the fraction into "μ̄" plus "something times (μ_z − μ̄)".
2. μ = μ̄ + [σ̄²/(σ̄² + σ_z²)](μ_z − μ̄), so K = σ̄²/(σ̄² + σ_z²) and 1 − K = σ_z²/(σ̄² + σ_z²); multiply each by the other variance.
3. Numbers: x̄ = 11, P̄ = 3 + 4 = 7, S = 7 + 12.25 = 19.25, K = 7/19.25; the three variance forms must print the same 4.455 to three decimals.

## T2.2 Steady state and its inverse

1. Write the variance after predict (P + R_proc) and push it through the update variance; set the result equal to P.
2. P(P + R_proc + Q_meas) = (P + R_proc)Q_meas gives P² + R_proc·P − R_proc·Q_meas = 0; multiply the root by (R_proc + √…)/(R_proc + √…) to rationalize; divide the quadratic by Q_meas² and use K = P/Q_meas.
3. K² + rK − r = 0 with r = R_proc/Q_meas, so r = K²/(1 − K); for (2, 40) everything is a round number (r = 0.05).

## T2.3 The price of a wrong gain

1. Write the posterior error as (1 − K)·(prior error) − K·(measurement noise); the two are independent.
2. At the fixed point P = (1 − K)²(P + R_proc) + K²Q_meas, a linear equation in P; stable when |1 − K| < 1.
3. For the minimum, write f = N/D with D = K(2 − K); in N′D − ND′ = 0 the R_proc terms collect to −(1 − K)R_proc and the Q_meas terms to K²Q_meas.

## T2.4 A wrong u is an offset

1. Take expectations: the noise terms vanish; only the per-step bias b survives in the mean error recursion.
2. m_{k+1} = (1 − K)(m_k + b), the fixed point m = (1 − K)m + (1 − K)b.
3. m = b(1 − K)/K: a gain of 0.2 gives four steps' worth of bias; for the sine, think of which way an exponential average of a moving signal errs.

## T3.1 predict

1. Two lines; the only decision is what dt multiplies.
2. Means add and variances add (p. 136); a random walk's variance grows linearly in elapsed time, so R_proc is multiplied by dt as well as u.
3. Check P >= 0 and R_proc >= 0 first and raise ValueError; then `return x + u * dt, P + R_proc * dt`.

## T3.2 update_bayes

1. Precisions (1/variance) add; handle P_bar = inf and P_bar = 0 before you divide by P_bar.
2. 1/P = 1/P̄ + 1/Q_meas, x = P(x̄/P̄ + z/Q_meas); the dropped constant is the pdf of z under N(x̄, P̄ + Q_meas).
3. `log_c = -0.5 * (np.log(2 * np.pi * S) + (z - x_bar) ** 2 / S)` with S = P_bar + Q_meas; with P_bar = inf return (z, Q_meas, -np.inf).

## T3.3 update / joseph_variance

1. Compute y and S first and keep both; the gate and the return tuple need them.
2. p. 150: σ² = Kσ_z² = (1 − K)σ̄²; the first form never subtracts K from 1, which is what float32 needs at P̄/Q_meas = 1e8.
3. `P = P_bar * Q_meas / S`; the gate test is `y * y > gate * S` (S, not Q_meas); Joseph is `(1 - K)**2 * P_bar + K**2 * Q_meas`.

## T3.4 run_filter / nis

1. The p. 147 loop with predict and update calls; store the prior before the update overwrites it.
2. `us = np.broadcast_to(np.asarray(u, float), zs.shape)` lets one loop take a scalar or a per-step u.
3. `out[k] = x, P, x_bar, P_bar, y, S` after each update; nis is `y**2 / S` on arrays.

## T3.5 steady_state / ratio_from_gain

1. The quadratic from T2.2; the test at R_proc = 1, Q_meas = 1e-10 fails the textbook root −R/2 + √(…)/2 by about 1e-8.
2. P∞ = 2R_proc·Q_meas/(R_proc + √(R_proc² + 4R_proc·Q_meas)), K∞ = P∞/Q_meas.
3. ratio_from_gain is `K * K / (1 - K)` after the range check.

## T3.6 fixed_gain_filter / fixed_gain_variance

1. The fixed-gain filter is run_filter without P: x̄ = x + u, x = x̄ + K(z − x̄).
2. The variance is the fixed point of T2.3 (b): P(1 − (1 − K)²) = (1 − K)²R_proc + K²Q_meas.
3. `a = (1 - K)**2; return (a * R_proc + K**2 * Q_meas) / (1 - a)`, after checking 0 < K < 2.

## T4 debug

1. Run `pytest exercises/tests/test_T4.py -v`; each test name says which behaviour is broken, and each fails for exactly one bug.
2. Check every variance against its name and unit (σ or σ²? process or sensor?), what the gate divides by, what a tick without a baro sample should still do, and which variance form float32 can survive at P̄/Q_meas = 1e8.
3. See `solutions/T4.md` (only after the first two clues).

## T5 robot

1. Task 1: ANIS ≫ 1 means S = P̄ + Q_meas is too small for the residuals you see; fix Q_meas from the ground segment before you touch R_proc, because on the ground R_proc plays no part in the truth.
2. Task 3: with Q_meas fixed, ANIS falls monotonically as R_proc grows, so bisect on log R_proc; the log-likelihood peaks near the same value; a positive lag-1 autocorrelation means the filter lags (R_proc too small), a negative one means it chases the noise (R_proc too large).
3. Task 4: the gain depends only on R_proc/Q_meas (T2.2 b) and the datasheet pair has almost the true ratio, so the estimate is nearly the same; only the reported P is wrong, by roughly the factor Q_meas is wrong by.
