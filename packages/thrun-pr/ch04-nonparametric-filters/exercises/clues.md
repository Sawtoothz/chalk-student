# Clues

Three steps per exercise: direction, key idea, near-solution. Open one at a time with
`just clue thrun-pr 4 T3.2 1`; each clue you open is recorded in `learner.yaml`.

## T1 concept

No clues; the answers are on pp. 85–89, 94–100, 102, 108–113.

## T2.1 Histogram approximation

1. Write p(z ∣ xₖ) as p(z, xₖ)/p(xₖ) and express both as integrals over the bin of densities over the continuous state.
2. Under (4.2) the state density is the constant pₖ/|xₖ| inside the bin; it comes out of both integrals.
3. You are left with |xₖ|⁻¹ ∫ p(z ∣ x) dx over the bin; compare a bin average with the value at the bin mean for an affine and for a curved function.

## T2.2 Log-odds update

1. Write Bayes rule for x and for ¬x with the same denominator; you want their ratio.
2. Replace p(zₜ ∣ x) by p(x ∣ zₜ) p(zₜ)/p(x) (4.16); everything that does not depend on the state cancels in the ratio.
3. The ratio is (inverse-model odds) × (previous odds) × (1 − p(x))/p(x); take logs and read off Table 4.2 line 2.

## T2.3 Particle-filter weight

1. Keep the whole path x₀:ₜ as the state; the recursion over paths needs no integral.
2. Target: η p(zₜ ∣ xₜ) p(xₜ ∣ xₜ₋₁, uₜ) bel(x₀:ₜ₋₁). Proposal: what line 4 does to a path drawn from bel(x₀:ₜ₋₁).
3. Divide: the motion term and bel(x₀:ₜ₋₁) appear in both and cancel.

## T2.4 Bias at M = 1 and M = 2

1. With no motion, line 4 is a draw from the prior; enumerate the possible initial particle sets.
2. For M = 2: (a, a), (b, b), and one of each with probability 2p(1 − p); only the mixed pair uses the weights.
3. P(a) = p² + 2p(1 − p) L_a/(L_a + L_b); compare with p L_a/(p L_a + (1 − p) L_b).

## T3.1 transition_from_density, hist_predict

1. Broadcasting: centres as a column for x_next and as a row for x_prev give the K×K matrix in one call.
2. (4.5): the η is per source bin i, so every column of T must sum to 1.
3. `T = motion_pdf(c[:, None], u, c[None, :]); T / T.sum(axis=0, keepdims=True)`; line 3 is then `T @ p`.

## T3.2 hist_update, hist_density

1. Stay in log space: add, then normalize so the log probabilities sum (after exp) to 1.
2. η in log space is subtracting `logsumexp`. For (4.2), find the bin with `np.searchsorted(edges, x, side="right") − 1`.
3. `a = log_lik + log_p_bar; return a − logsumexp(a)`; density is `p[k] / np.diff(edges)[k]`, zeroed outside the edges.

## T3.3 Log odds

1. Three one-liners; scipy already has the functions (4.13) and (4.14) describe.
2. `scipy.special.logit` is (4.13); `scipy.special.expit` is (4.14) without overflow. Clip p before `logit`.
3. Line 2: `l + prob_to_logodds(p_inv) − l0`, then `np.clip` only when bounds are given.

## T3.4 is_estimate

1. Compute log weights log f − log g first; check the support condition on them before anything else.
2. Normalize with `logsumexp`; the estimate is Σ w̃ h(x); N_eff = 1/Σ w̃².
3. Raise when `log_g` is −inf at a sample where `log_f` is finite; then `wn = np.exp(logw − logsumexp(logw))`.

## T3.5 Resamplers

1. (4.37) for all U at once is a binary search into the cumulative weights.
2. Low variance: U = r + m/M with one r ∈ [0, 1/M). Stratified: U = (m + uₘ)/M with M independent uₘ. Normalize the cumulative sum by its last entry.
3. `cw = np.cumsum(w); cw /= cw[-1]; np.minimum(np.searchsorted(cw, U, side="left"), M − 1)`.

## T3.6 pf_step

1. Order: move (line 4), wrap angles, add log likelihood to the carried log weights, normalize, compute N_eff, then decide.
2. Resample only if N_eff < neff_frac · M; after it, weights are uniform (4.36) and injection replaces round(inject · M) particles.
3. `logw = logw + log_lik(z, X); logw −= logsumexp(logw); n_eff = 1/np.exp(logsumexp(2*logw))`.

## T3.7 weighted_mean_cov

1. Normalize the weights; the linear columns are a weighted average.
2. Headings: average unit vectors and take `arctan2`; wrap deviations before the outer product; divide by 1 − Σw̃².
3. `cov = (D * w[:, None]).T @ D / (1 − np.sum(w**2))`; check against `np.cov(X.T, aweights=w)`.

## T4 Debug

1. Read each method against its card: `resample` against C5, `step` against C4, `estimate` against C6.
2. Ask of each line: what does it assume about the scale of w, what happens at log-likelihood −3000, what does it do to a heading of ±π, and where did the previous weights go.
3. One bug in `resample`, two in the two weight lines of `step`, one in `estimate`.

## T5 Robot

1. Start with tasks 1 and 4: get a filter that converges from the own half, then see how M changes it.
2. Use the heaviest cluster for the estimate, gate the step on u = 0, and keep the outlier floor; read NEES as a median and as a fraction above 11.34.
3. For task 6, compute log of the weighted mean likelihood per detection before each update and plot it; compare it with log(eps).
