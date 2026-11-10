# T2 — Derivations

Do these by hand in `lesson-notes.md` (your file), then compare with `solutions/T2.md`.

## T2.1 The inversion lemma to the Kalman gain (eq. 3.38 → 3.45 → 3.47)

Start from the information-form covariance update

```latex
\Sigma_t = (C_t^T Q_t^{-1} C_t + \bar\Sigma_t^{-1})^{-1}
```

and the lemma (Table 3.2) (R + P Q Pᵀ)⁻¹ = R⁻¹ − R⁻¹P(Q⁻¹ + PᵀR⁻¹P)⁻¹PᵀR⁻¹. Show that Σₜ = (I − KₜCₜ)Σ̄ₜ with Kₜ = Σ̄ₜCₜᵀ(CₜΣ̄ₜCₜᵀ + Qₜ)⁻¹. State which matrix plays R, P and Q in the lemma.

## T2.2 Joseph form

Show that for any gain K (not only the optimal one), (I − KC)Σ̄(I − KC)ᵀ + KQKᵀ is the covariance of μ̄ + K(z − Cμ̄) when z = Cx + δ, δ ~ N(0, Q), and that it equals (I − KC)Σ̄ when K is the Kalman gain. Then explain why the first form is preferred in code.

## T2.3 Book exercise 4(b): EKF prediction for an uncertain heading

State x = (x, y, θ), μ = 0, Σ = diag(0.01, 0.01, 10000). Motion g(x) = (x + cos θ, y + sin θ, θ), no noise. Write G = ∂g/∂x at μ, compute Σ̄ = GΣGᵀ, and state the resulting Gaussian. Sketch (by hand) the true posterior over (x, y) and the EKF ellipse on the same axes. Where does the EKF put the mean, and where is most of the true probability mass?
