# T2 — Derivations

By hand, on paper. Then compare with `solutions/T2.md`.

1. **Where the histogram approximation enters (4.1.3).** Start from (4.6), p(zₜ ∣ xₖ,ₜ) as a ratio of two integrals over the bin. Assume the piecewise constant density (4.2) inside the bin. Show that p(zₜ ∣ xₖ,ₜ) is then exactly the average of p(zₜ ∣ xₜ) over the bin, and that (4.4) replaces this average by the value at x̂ₖ,ₜ. When is (4.4) exact?
2. **The log-odds update (4.15)–(4.20).** Starting from Bayes rule with the normalizer explicit (4.15) and Bayes rule applied to the measurement model (4.16), derive Table 4.2 line 2. Name each term that cancels when you divide (4.17) by (4.18).
3. **The importance weight of the particle filter (4.32)–(4.34).** Write the path posterior bel(x₀:ₜ) with Bayes and Markov (4.32), write the distribution line 4 samples from (4.33), and show that their ratio is η p(zₜ ∣ xₜ). Why does the derivation need the path x₀:ₜ rather than xₜ alone?
4. **Sampling bias with M = 1 and M = 2 (book exercise 3).** A binary state x ∈ {a, b} with prior P(a) = p and likelihoods L_a = p(z ∣ a), L_b = p(z ∣ b). One update of Table 4.3 with no motion. (a) With M = 1, what is the probability that the final particle is a? (b) With M = 2, enumerate the initial pairs and compute the same probability. (c) Evaluate both and the exact posterior at p = 0.5, L_a = 0.9, L_b = 0.1, and at p = 0.3. (d) Which way does the bias point, and why does (4.38) explain it?
