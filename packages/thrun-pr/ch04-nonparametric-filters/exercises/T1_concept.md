# T1 — Concept check

Answer in one or two sentences each. Then compare with `solutions/T1.md`.

1. Table 4.1 line 3 over all k is one linear-algebra operation. Which one, what are the shapes, and when does it become a convolution?
2. (4.4) and (4.5) replace bin-to-bin probabilities by densities at a representative state. Where exactly does the histogram filter approximate, and what controls the size of the error?
3. Table 4.2 line 2 subtracts the prior's log odds at every update. Why every update and not once, and what happens to a map if you add it instead?
4. Why does Table 4.2 use an inverse measurement model p(x ∣ z) instead of the forward model p(z ∣ x)? Give the book's example.
5. In Table 4.3, which line moves particles and which line changes how many copies each has? Which line uses the measurement?
6. (4.25) needs f(x) > 0 ⟹ g(x) > 0. In the particle filter, what are f and g, and why does the condition hold automatically? A kidnap still breaks the filter: what does it break, if not this condition?
7. A robot stands still with no sensor and the particle filter resamples every step. What happens to the particle set, and what two changes does the book propose (p. 109)?
8. Give the three advantages of the low-variance sampler (p. 111). Which one matters most on a stationary robot?
9. With M = 1 the particle filter ignores every measurement. Why, in one sentence, and which equation shows it?
10. Random particle injection (p. 113) reduces particle deprivation. Why does the book call it a last resort?
