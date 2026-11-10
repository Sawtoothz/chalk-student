"""Every number quoted in translate.md comes from this script.

Run: .venv/bin/python packages/labbe-kbf/ch04-one-dimensional-kalman-filters/figures/card_numbers.py
Plain numpy/scipy; it does not import the exercises (they are written after the cards).
Names follow the repo convention: R_proc = Labbe's Q (process variance), Q_meas = Labbe's R (sensor variance).
"""
import numpy as np
from scipy.stats import chi2


def predict(x, P, u, R_proc):
    return x + u, P + R_proc


def update_bayes(x_bar, P_bar, z, Q_meas):
    # p. 138: N(mu, s2) = N((P_bar z + Q x_bar)/(P_bar + Q), P_bar Q/(P_bar + Q))
    return (P_bar * z + Q_meas * x_bar) / (P_bar + Q_meas), P_bar * Q_meas / (P_bar + Q_meas)


def update_gain(x_bar, P_bar, z, Q_meas):
    # p. 151 / p. 153 Kalman form
    y = z - x_bar
    S = P_bar + Q_meas
    K = P_bar / S
    return x_bar + K * y, (1 - K) * P_bar, y, S, K


def steady_state(R_proc, Q_meas):
    # posterior P_inf: P^2 + R_proc P - R_proc Q_meas = 0, positive root
    P_inf = 0.5 * (-R_proc + np.sqrt(R_proc**2 + 4 * R_proc * Q_meas))
    return P_inf, P_inf / Q_meas


def fixed_gain_var(K, R_proc, Q_meas):
    # steady state of the scalar Joseph recursion P = (1-K)^2 (P + R_proc) + K^2 Q_meas
    a = (1 - K) ** 2
    return (a * R_proc + K**2 * Q_meas) / (1 - a)


print("NUMBERS")
# C1
print("C1 predict N(10,.2^2)+N(15,.7^2):", predict(10.0, 0.2**2, 15.0, 0.7**2))
print("C1 predict (10,3,u=1,R_proc=4):", predict(10.0, 3.0, 1.0, 4.0))

# C2
print("C2 bayes N(10,.2^2) x N(11,.1^2):", update_bayes(10.0, 0.2**2, 11.0, 0.1**2))
print("C2 bayes N(10,1) x N(10,1):", update_bayes(10.0, 1.0, 10.0, 1.0))

# C3
xb, Pb = predict(10.0, 3.0, 1.0, 2.0**2)
x, P, y, S, K = update_gain(xb, Pb, 12.0, 3.5**2)
print(f"C3 p.169: prior ({xb:.3f}, {Pb:.3f}) -> post ({x:.3f}, {P:.3f}), y={y:.3f}, S={S:.3f}, K={K:.5f}")
rng = np.random.default_rng(4)
n = 100_000
xb_r = rng.normal(0, 100, n); Pb_r = 10 ** rng.uniform(-3, 3, n)
z_r = rng.normal(0, 100, n); Q_r = 10 ** rng.uniform(-3, 3, n)
xa, Pa = update_bayes(xb_r, Pb_r, z_r, Q_r)
xg, Pg, *_ = update_gain(xb_r, Pb_r, z_r, Q_r)
print(f"C3 bayes vs gain over {n} random cases: max |dx|/scale = {np.max(np.abs(xa - xg) / (1 + np.abs(xa))):.2e},"
      f" max |dP|/P = {np.max(np.abs(Pa - Pg) / Pa):.2e}")
# dog, p. 143-145: x0 = N(0, 400), R_proc = 1, Q_meas = 2
xb, Pb = predict(0.0, 400.0, 1.0, 1.0)
_, P1, *_ = update_gain(xb, Pb, 1.0, 2.0)
print(f"C3 dog first step: P_bar={Pb:.3f}, P={P1:.4f}")

# Cancellation in (1-K) P_bar when P_bar >> Q_meas
for dtype, Pb_, Qm in [(np.float32, 1e6, 1e-2), (np.float32, 1e8, 1e-2), (np.float64, 1e16, 1e-2)]:
    Pb_ = dtype(Pb_); Qm = dtype(Qm)
    S_ = Pb_ + Qm
    K_ = Pb_ / S_
    P_book = (dtype(1) - K_) * Pb_
    P_safe = Pb_ * Qm / S_
    P_jos = (dtype(1) - K_) ** 2 * Pb_ + K_**2 * Qm
    exact = float(Pb_) * float(Qm) / (float(Pb_) + float(Qm))
    print(f"C3 cancel {dtype.__name__} P_bar={float(Pb_):.0e} Q_meas={float(Qm):.0e}: exact={exact:.6e}"
          f" (1-K)P_bar={float(P_book):.6e} P_bar*Q/S={float(P_safe):.6e} joseph={float(P_jos):.6e}")

print(f"C3 gate chi2(1) 0.99 quantile = {chi2.ppf(0.99, 1):.3f}, 0.95 = {chi2.ppf(0.95, 1):.3f}")

# C4 steady state
for name, Rp, Qm in [("dog p143", 1.0, 2.0), ("dog p147", 2.0, 4.5), ("thermo p156", 0.05**2, 0.13**2)]:
    P_inf, K_inf = steady_state(Rp, Qm)
    P = 400.0 if "dog" in name else 1000.0
    for k in range(1, 10_000):
        P = update_bayes(0, P + Rp, 0, Qm)[1]
        if abs(P - P_inf) < 1e-6 * P_inf:
            break
    print(f"C4 {name}: P_inf={P_inf:.5f}, P_bar_inf={P_inf + Rp:.5f}, K_inf={K_inf:.5f},"
          f" K from P_bar={(P_inf + Rp) / (P_inf + Rp + Qm):.5f}, steps to 1e-6 rel={k}")

Rp, Qm = 2.0, 4.5
P_inf, K_inf = steady_state(Rp, Qm)
for K in [K_inf, 0.2, 0.8]:
    print(f"C4 fixed gain K={K:.5f} on dog (2, 4.5): steady var={fixed_gain_var(K, Rp, Qm):.5f}")
# Monte Carlo check of fixed_gain_var: random-walk truth, fixed-gain filter
rng = np.random.default_rng(7)
runs, steps = 2000, 400
for K in [K_inf, 0.2, 0.8]:
    truth = np.zeros(runs); est = np.zeros(runs); errs = []
    for k in range(steps):
        truth = truth + 1.0 + rng.normal(0, np.sqrt(Rp), runs)
        z = truth + rng.normal(0, np.sqrt(Qm), runs)
        est = est + 1.0
        est = est + K * (z - est)
        if k >= 100:
            errs.append(est - truth)
    print(f"C4 MC fixed gain K={K:.5f}: error variance={np.var(np.array(errs)):.4f} ({runs} runs, steps 100-399)")

# biased input: filter assumes u_f, truth moves u_t; steady offset = (u_f - u_t)(1 - K)/K
K = K_inf
est, truth = 0.0, 0.0
for k in range(500):
    truth += 0.0
    est = est + 1.0
    est = est + K * (truth - est)
print(f"C4 bias: u error 1.0, K={K:.5f}: steady offset={est - truth:.4f}, formula={(1 - K) / K:.4f}")

# relative error of (1-K) P_bar in float32 as P_bar / Q_meas grows
Qm = np.float32(1.0)
for ratio in [1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8]:
    Pb_ = np.float32(ratio)
    K_ = Pb_ / (Pb_ + Qm)
    exact = ratio / (ratio + 1.0)
    rb = abs(float((np.float32(1) - K_) * Pb_) - exact) / exact
    rs = abs(float(Pb_ * Qm / (Pb_ + Qm)) - exact) / exact
    print(f"C3 float32 P_bar/Q_meas={ratio:.0e}: rel err (1-K)P_bar={rb:.1e}, P_bar*Q/S={rs:.1e}")

# transient: mean error from a bad x0 (e0 = 100 m) shrinks by (1 - K_k) per step.
# Full KF with P0 = 100^2 vs fixed gain K_inf; steps until the mean error is below 1 m.
for name, Rp, Qm in [("dog p147", 2.0, 4.5), ("large noise p162", 2.0, 30000.0)]:
    P_inf, K_inf = steady_state(Rp, Qm)
    res = {}
    for mode in ["kf", "fixed"]:
        e, P = 100.0, 100.0**2
        for k in range(1, 100_000):
            if mode == "kf":
                Pb = P + Rp
                K = Pb / (Pb + Qm)
                P = Pb * Qm / (Pb + Qm)
            else:
                K = K_inf
            e *= 1 - K
            if abs(e) < 1.0:
                break
        res[mode] = k
    print(f"C4 transient {name}: e0=100 m -> <1 m in {res['kf']} steps (KF, P0=1e4) vs {res['fixed']} (fixed K_inf={K_inf:.5f})")

# stable root vs textbook root when R_proc >> Q_meas
for Rp, Qm in [(1.0, 1e-6), (1.0, 1e-10)]:
    naive = 0.5 * (-Rp + np.sqrt(Rp**2 + 4 * Rp * Qm))
    stable = 2 * Rp * Qm / (Rp + np.sqrt(Rp**2 + 4 * Rp * Qm))
    it = 1.0
    for _ in range(200):
        it = (it + Rp) * Qm / (it + Rp + Qm)
    print(f"C4 root R_proc={Rp:g} Q_meas={Qm:g}: textbook={naive:.10e} stable={stable:.10e} iterated={it:.10e}")
