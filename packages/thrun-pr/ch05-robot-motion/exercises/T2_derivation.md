# T2 — Derivations

Do these by hand in your own notes, then compare with `solutions/T2.md`. Every number in the
solutions comes from a run of the reference solution in this repo.

## T2.1 Book exercise 8 and Table 5.4: the error samplers

(a) Prove that the triangular density (5.12) has mean 0 and variance b². (b) Show that Table 5.4's
two samplers have variance b². (c) State the exact range of values each sampler can return, and
compare with the claim on p. 132.

## T2.2 Table 5.1 lines 2–7: the circle, and where the sign goes (eq. 5.17–5.24)

(a) The centre (x*, y*) lies on the line through (x, y) perpendicular to the heading θ and on the
perpendicular bisector of the chord to (x′, y′). Write both as parametric lines, intersect them, and
recover μ of line 2. (b) Work the example x = (0, 0, 0), u = (1 m/s, −0.5 rad/s), Δt = 1 s: compute the
end pose, μ, the centre, r*, Δθ and v̂ from line 7. (c) Show that the signed radius
λ = (y* − y) cos θ − (x* − x) sin θ gives v̂ = λΔθ/Δt with the right sign in all four quadrants of
(sign v, sign ω).

## T2.3 From a density over noise to a density over poses

(a) For the chord form x′ = x + v̂Δt sinc(ω̂Δt/2) cos(θ + ω̂Δt/2), y′ likewise with sin,
θ′ = θ + (ω̂ + γ̂)Δt, show that |det ∂(x′, y′, θ′)/∂(v̂, ω̂, γ̂)| = |v̂| Δt⁴ sinc²(ω̂Δt/2) / 2.
(b) Show that for the odometry model (5.40) the same determinant with respect to
(δ̂rot1, δ̂trans, δ̂rot2) is δ̂trans. (c) Explain in two sentences why (5.32) is not a density over
(x′, y′, θ′), and when that matters in practice.

## T2.4 Book exercises 1–3: a robot with dynamics (the drone's first step)

These are adapted rather than reproduced; check the book's wording on p. 145. A 1-D robot has
state (x, ẋ). Over each Δt = 1 s it receives a random acceleration a ~ N(0, σ²) with σ² = 1, held
constant over the interval. (a) Write the one-step mean and covariance of (x′, ẋ′) given (x, ẋ), and
the correlation coefficient of x′ and ẋ′. (b) Condition the Gaussian of (a) on an observed x′: what is
the distribution of ẋ′, and why is it degenerate? (c) Starting from rest with zero uncertainty, give
the covariance after T = 1, 2, 5, 10 steps and the limit of the correlation coefficient as T grows.
(d) Say which part of this is the drone's prediction step, and what replaces a in practice.

## T2.5 Book exercise 4: the kinematic bicycle

Using the conventions in `models.Bicycle` (pose at the front tyre, speed v at the rear axle, steering
φ, wheelbase l): (a) show that the rear axle moves on a circle with ω = v tan φ / l; (b) write the
front tyre's new pose after Δt in terms of the rear axle's, and say what happens as φ → 0;
(c) check `models.Bicycle` against the book's text of exercise 4 (p. 146; there is no figure) and write down any convention that
differs (reference point, which wheel's speed is commanded).
