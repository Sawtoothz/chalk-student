// Numerical core of interactive.html: the same model as session_lib.py (which drives the marimo session).
// Plain JS, no DOM. figures/make_session_data.py pastes this file into interactive.html; compare_session.py runs it in node.
const SC = (function () {
  const CHI2_2_95 = 5.991464547107979, CHI2_3_95 = 7.814727903251179;
  const J1 = [[0, -1], [1, 0]];
  const eye3 = () => [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  const mm = (A, B) => A.map(r => B[0].map((_, j) => r.reduce((s, v, k) => s + v * B[k][j], 0)));
  const T = A => A[0].map((_, j) => A.map(r => r[j]));
  const add = (A, B) => A.map((r, i) => r.map((v, j) => v + B[i][j]));
  const sub = (A, B) => A.map((r, i) => r.map((v, j) => v - B[i][j]));
  const sym = A => A.map((r, i) => r.map((v, j) => 0.5 * (v + A[j][i])));
  const norm = v => Math.sqrt(v.flat(Infinity).reduce((s, x) => s + x * x, 0));
  const sinc = t => (t === 0 ? 1 : Math.sin(t) / t);
  const coefA = th => 0.5 * sinc(th / 2) ** 2;                       // (1 − cos θ)/θ²
  const fact = n => (n <= 1 ? 1 : n * fact(n - 1));
  const coefB = th => { th = Math.abs(th); if (th < 0.3) { let s = 0; for (let k = 0; k < 5; k++) s += (-1) ** k * th ** (2 * k) / fact(2 * k + 3); return s; } return (th - Math.sin(th)) / th ** 3; };
  const coefD = th => { th = Math.abs(th); if (th < 0.3) { const t2 = th * th; return 1 / 12 + t2 / 720 + t2 ** 2 / 30240 + t2 ** 3 / 1209600 + t2 ** 4 / 47900160; } return 1 / th ** 2 - 1 / (2 * th * Math.tan(th / 2)); };

  // ---- shared RNG (same bits as session_lib.make_rng)
  function rng(seed) { let s = (seed >>> 0) || 1; return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; }; }
  function randn(r) { let u = 0, v = 0; while (u === 0) u = r(); while (v === 0) v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }

  // ---- SE(2)
  const pose = (x, y, th) => { const c = Math.cos(th), s = Math.sin(th); return [[c, -s, x], [s, c, y], [0, 0, 1]]; };
  function se2Exp(tau) {
    const th = tau[2], A = sinc(th), B = th * coefA(th);
    const V = [[A, -B], [B, A]];
    return [[Math.cos(th), -Math.sin(th), V[0][0] * tau[0] + V[0][1] * tau[1]], [Math.sin(th), Math.cos(th), V[1][0] * tau[0] + V[1][1] * tau[1]], [0, 0, 1]];
  }
  function se2Log(M) {
    const th = Math.atan2(M[1][0], M[0][0]), A = sinc(th), B = th * coefA(th), d = A * A + B * B;
    // (A I − B J1)(t) / d, with J1 t = (−t_y, t_x)
    const tx = M[0][2], ty = M[1][2];
    return [(A * tx + B * ty) / d, (A * ty - B * tx) / d, th];
  }
  function se2Ad(M) { return [[M[0][0], M[0][1], M[1][2]], [M[1][0], M[1][1], -M[0][2]], [0, 0, 1]]; }   // −J1 t = (t_y, −t_x)
  function se2Inv(M) { const R = [[M[0][0], M[1][0]], [M[0][1], M[1][1]]], t = [M[0][2], M[1][2]]; return [[R[0][0], R[0][1], -(R[0][0] * t[0] + R[0][1] * t[1])], [R[1][0], R[1][1], -(R[1][0] * t[0] + R[1][1] * t[1])], [0, 0, 1]]; }
  function se2Jl(tau) {
    const [r1, r2, th] = tau, A = sinc(th), a = coefA(th), B = th * a, tb = th * coefB(th);
    return [[A, -B, r1 * tb + r2 * a], [B, A, -r1 * a + r2 * tb], [0, 0, 1]];
  }
  const se2Jr = tau => se2Jl(tau.map(v => -v));
  const mv3 = (A, v) => A.map(r => r.reduce((s, a, k) => s + a * v[k], 0));

  function expmSe2(tau) {   // oracle: Taylor series of exp(τ^), 30 terms (|τ| < 4 here)
    const H = [[0, -tau[2], tau[0]], [tau[2], 0, tau[1]], [0, 0, 0]];
    let S = eye3(), term = eye3();
    for (let n = 1; n <= 30; n++) { term = mm(term, H).map(r => r.map(v => v / n)); S = add(S, term); }
    return S;
  }

  // ---- Fig A: right and left perturbation
  function figA(p) {
    const X = pose(p.xX, 1.0, p.thX_deg * Math.PI / 180), tau = [p.rho1, 0.2, p.th_deg * Math.PI / 180];
    const right = mm(X, se2Exp(tau)), wrong = mm(se2Exp(tau), X), left = mm(se2Exp(mv3(se2Ad(X), tau)), X);
    const p_right = [], p_wrong = [];
    for (let i = 0; i <= 40; i++) { const k = i / 40, ks = tau.map(v => v * k); const a = mm(X, se2Exp(ks)), b = mm(se2Exp(ks), X); p_right.push([a[0][2], a[1][2]]); p_wrong.push([b[0][2], b[1][2]]); }
    const inv = norm(sub(right, left)), gap = Math.hypot(wrong[0][2] - right[0][2], wrong[1][2] - right[1][2]);
    return { X, right, wrong, left, p_right, p_wrong, special: gap < 1e-9,
      tiles: { '‖(X ⊕ τ) − Exp(Ad_X τ)·X‖': inv < 1e-12 ? '< 1e-12 ✓' : inv.toExponential(1) + '  ✗',
        'position gap, right vs left τ': gap.toFixed(2) + ' m',
        '‖τ‖ / ‖Ad_X τ‖': norm(tau).toFixed(2) + ' / ' + norm(mv3(se2Ad(X), tau)).toFixed(2),
        'Exp vs expm oracle': norm(sub(se2Exp(tau), expmSe2(tau))) < 1e-12 ? '< 1e-12 ✓' : norm(sub(se2Exp(tau), expmSe2(tau))).toExponential(1) + '  ✗' } };
  }

  // ---- Fig B: Gaussian on the tangent
  const N_B = 1500;
  function stdev(a) { const m = a.reduce((s, v) => s + v, 0) / a.length; return Math.sqrt(a.reduce((s, v) => s + (v - m) ** 2, 0) / (a.length - 1)); }
  function figB(p) {
    const st = p.sig_th_deg * Math.PI / 180, sd = [0.5, 0.5 * p.ratio, st];
    const Xb = pose(2, 1, p.th_mean_deg * Math.PI / 180), r = rng(7), pos = [], q = [];
    let inside = 0;
    for (let i = 0; i < N_B; i++) {
      const eps = [sd[0] * randn(r), sd[1] * randn(r), sd[2] * randn(r)], X = mm(Xb, se2Exp(eps));
      pos.push([X[0][2], X[1][2]]);
      const dx = X[0][2] - Xb[0][2], dy = X[1][2] - Xb[1][2];
      const a = dx * Xb[0][0] + dy * Xb[1][0], l = dx * Xb[0][1] + dy * Xb[1][1];     // (p − t) R
      q.push([a, l]);
      if ((a / sd[0]) ** 2 + (l / sd[1]) ** 2 <= CHI2_2_95) inside++;
    }
    inside /= N_B;
    const sa = stdev(q.map(v => v[0])), sl = stdev(q.map(v => v[1]));
    return { Xb, pos, sd, inside,
      tiles: { 'inside the linear 95 % ellipse (target 95 %)': (100 * inside).toFixed(1) + ' %',
        'along-track std, cloud / ellipse': (sa / sd[0]).toFixed(2), 'lateral std, cloud / ellipse': (sl / sd[1]).toFixed(2), 'σ_θ': st.toFixed(2) + ' rad' } };
  }

  // ---- Fig C: the ESKF on a T5 run (run = {truth, U, dets, tags, err0, P0})
  function solve2(Z, b) { const d = Z[0][0] * Z[1][1] - Z[0][1] * Z[1][0]; return [(Z[1][1] * b[0] - Z[0][1] * b[1]) / d, (-Z[1][0] * b[0] + Z[0][0] * b[1]) / d]; }
  function solve3(P, e) { // Gaussian elimination, 3x3, partial pivoting
    const M = P.map((r, i) => [...r, e[i]]);
    for (let c = 0; c < 3; c++) { let p = c; for (let r = c + 1; r < 3; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r; [M[c], M[p]] = [M[p], M[c]];
      for (let r = 0; r < 3; r++) { if (r === c) continue; const f = M[r][c] / M[c][c]; for (let k = c; k < 4; k++) M[r][k] -= f * M[c][k]; } }
    return M.map((r, i) => r[3] / r[i]);
  }
  function figC(run, p) {
    const Rp = [[0.02 ** 2, 0, 0], [0, (p.sig_slip_mm / 1000) ** 2, 0], [0, 0, 0.01 ** 2]];
    const sy2 = p.sig_y ** 2, Qm = [[sy2, 0], [0, sy2]];
    let X = mm(pose(...run.truth[0]), se2Exp(run.err0)), P = run.P0.map(r => r.slice());
    const nees = [], nis = [], pos = [];
    for (let k = 0; k < run.U.length; k++) {
      const u = run.U[k], F = se2Ad(se2Exp(u.map(v => -v))), G = se2Jr(u);
      P = sym(add(mm(mm(F, P), T(F)), mm(mm(G, Rp), T(G)))); X = mm(X, se2Exp(u));
      for (const [j, y0, y1] of run.dets[k]) {
        const R = [[X[0][0], X[0][1]], [X[1][0], X[1][1]]], d = [run.tags[j][0] - X[0][2], run.tags[j][1] - X[1][2]];
        const e = [R[0][0] * d[0] + R[1][0] * d[1], R[0][1] * d[0] + R[1][1] * d[1]];          // Rᵀ d
        const Jd = [-d[1], d[0]], c3 = [R[0][0] * Jd[0] + R[1][0] * Jd[1], R[0][1] * Jd[0] + R[1][1] * Jd[1]];    // Rᵀ J1 d
        const H = [[-1, 0, -c3[0]], [0, -1, -c3[1]]], z = [y0 - e[0], y1 - e[1]];
        const HP = mm(H, P), Z = sym(add(mm(HP, T(H)), Qm));
        // K = P Hᵀ Z⁻¹ (3x2): row i of K solves Z kᵀ = (H P)[:, i]
        const K = [0, 1, 2].map(i => solve2(Z, [HP[0][i], HP[1][i]]));
        const dx = mv3(K, z), IKH = sub(eye3(), mm(K, H));
        P = add(mm(mm(IKH, P), T(IKH)), mm(mm(K, Qm), T(K)));
        const Jr = se2Jr(dx); P = sym(mm(mm(Jr, P), T(Jr))); X = mm(X, se2Exp(dx));
        const sz = solve2(Z, z); nis.push(z[0] * sz[0] + z[1] * sz[1]);
      }
      const Yt = pose(...run.truth[k + 1]), ee = se2Log(mm(se2Inv(X), Yt)), s = solve3(P, ee);
      nees.push(ee[0] * s[0] + ee[1] * s[1] + ee[2] * s[2]);
      pos.push(Math.hypot(X[0][2] - run.truth[k + 1][0], X[1][2] - run.truth[k + 1][1]));
    }
    const mean = a => a.reduce((s, v) => s + v, 0) / a.length, frac = nees.filter(v => v > CHI2_3_95).length / nees.length;
    const verdict = frac < 0.15 && mean(nees) > 1.5 ? 'consistent' : (frac >= 0.15 ? 'overconfident' : 'conservative');
    return { nees, nis, pos, verdict, frac,
      tiles: { 'ANEES, single run (target 3)': mean(nees).toFixed(2), 'ANIS, single run (target 2)': mean(nis).toFixed(2),
        'position RMSE': (100 * Math.sqrt(mean(pos.map(v => v * v)))).toFixed(2) + ' cm',
        'NEES above the 95 % bound': (100 * frac).toFixed(0) + ' % of steps (expect ≈ 5 %)' } };
  }

  // ---- Fig D: the printed coefficient of (144)
  function dOracle(th, series) { const t2 = th * th; let s = 0; series.forEach((c, k) => { s += c * t2 ** k; }); return s; }
  const dPrinted = th => 1 / th ** 2 - (1 + Math.cos(th)) / (2 * th * Math.sin(th));
  function sci(v, d) { const s = v.toExponential(d); return s.replace(/e([+-])(\d)$/, 'e$10$2'); }
  function figD(log10th, series) {
    const th = 10 ** log10th, ref = dOracle(th, series), ep = Math.abs(dPrinted(th) - ref) / ref, er = Math.abs(coefD(th) - ref) / ref;
    const sweep = [], ps = [], rs = [];
    for (let i = 0; i <= 60; i++) { const t = 10 ** (-6 + i / 10), o = dOracle(t, series); sweep.push(t); ps.push(Math.abs(dPrinted(t) - o) / o); rs.push(Math.abs(coefD(t) - o) / o); }
    const mat = Math.sqrt(2) * th * th * Math.abs(dPrinted(th) - ref);
    const ex10 = v => v === 0 ? '0 (exact)' : (v >= 1e-15 ? v.toExponential(1).replace('e+', 'e') : '< 1e-15 (float64 floor)');
    return { sweep, ps, rs, th, ep, er,
      tiles: { 'θ': sci(th, 1) + ' rad', 'relative error of the printed coefficient': ex10(ep),
        'relative error, series/cot version (series is the oracle below 0.3)': ex10(er), 'error this leaves in J_r⁻¹ (‖·‖_F)': ex10(mat) } };
  }
  return { figA, figB, figC, figD, se2Exp, se2Log, se2Ad, se2Jr, pose, mm, T, CHI2_2_95, CHI2_3_95 };
})();
if (typeof module !== 'undefined') module.exports = SC;
