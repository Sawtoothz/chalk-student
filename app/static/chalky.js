/* Chalky — the Library's mascot: a stick of chalk in a green Chalk wrapper who lives in the shelf room.
   It picks something to do at random: strolls the floor, hops up to the chalkboard ledge and writes a short formula
   (erasing the last one first), sits on the window sill watching the moon, reads a tiny book, naps, looks around,
   or does a little dance. Click it and it hops and says a tip (or what stage is running).
   shelf.js owns the canvas and the loop:  const c = Chalky.create();  each frame  c.update(dt, world); c.draw(ctx, world)
   world = { OY, board: {x,y,w,h} | null (room coords), busy: 'text' | null }.  c.hit(x, y), c.poke(world) -> text,
   c.board = { lines: [...], shown: n } is drawn by shelf.js on the chalkboard; c.say = { text, until } | null. */
(function (global) {
  const C = { body: '#f3efe4', shade: '#d3ccb8', eye: '#2a2420', shut: '#7a6f5f', band: '#3ec294', bandLo: '#2a8f6b',
              book: '#2f4f6f', page: '#f4efe2', cheek: '#e8b4a0' };
  const FLOOR = { y: 186, x0: 8, x1: 470 }, SILL = { y: 74, x0: 60, x1: 116 };
  const LINES = [['X=FX+BU', 'P=FPF+Q'], ['K=PH/S'], ['Z-HX'], ['SLAM'], ['WRAP IT!'], ['X=AX+BU'], ['PI=3.14'],
                 ['MAP', 'NOISE'], ['LOG ODDS'], ['1+1=2'], ['W=1/M'], ['MU SIGMA']];
  const TIPS = [
    'Auto-run in the top bar runs every stage for you.',
    'Drop a PDF anywhere on the room to add it.',
    'After review, Make slides builds a class deck and a review deck.',
    'Every number in a package comes from a run, never from memory.',
    'I never write your solutions. That part is yours!',
    'Arrow keys turn the pages of an open book.',
    'Wrap your angles before they meet a gain.',
    'A test with no oracle is not a test.',
    'Thrun’s Q is Q_meas here. Never a bare Q.',
  ];
  const rand = (a, b) => a + Math.random() * (b - a);
  const pick = a => a[Math.floor(Math.random() * a.length)];
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  function create() {
    const m = { x: rand(250, 420), y: FLOOR.y, facing: 1, perch: 'floor', pose: 'stand', q: [], cur: null,
                blinkAt: rand(1, 3), blink: 0, walkT: 0, zs: [], dust: [], board: { lines: [], shown: 0 }, say: null, tipN: 0 };

    function range(p, w) {
      if (p === 'floor') return [FLOOR.x0, FLOOR.x1, FLOOR.y];
      if (p === 'sill') return [SILL.x0, SILL.x1, SILL.y];
      const b = w.board; return [b.x + 6, b.x + b.w - 6, b.y + b.h + 3];
    }
    function toPerch(p, x, w) {   // walk to a take-off point, then hop
      const steps = [];
      if (p === m.perch) { steps.push({ t: 'walk', x }); return steps; }
      const [a0, a1] = range(m.perch, w), [b0, b1, by] = range(p, w);
      const tx = clamp(x, b0, b1);
      steps.push({ t: 'walk', x: clamp(tx, a0, a1) });
      steps.push({ t: 'hop', p, x: tx, y: by });
      return steps;
    }
    function plan(w) {
      const opts = [['stroll', 30], ['look', 14], ['nap', 9], ['read', 12], ['window', 10], ['dance', 4]];
      if (w.board) opts.push(['write', w.busy ? 30 : 16]);
      let r = Math.random() * opts.reduce((s, o) => s + o[1], 0), what = 'stroll';
      for (const [k, wt] of opts) { if ((r -= wt) <= 0) { what = k; break; } }
      const q = [];
      if (what === 'stroll') {
        const [x0, x1] = range(m.perch, w); q.push({ t: 'walk', x: rand(x0, x1) });
        if (m.perch !== 'floor' && Math.random() < 0.6) q.push(...toPerch('floor', rand(20, 460), w));
      } else if (what === 'look') q.push({ t: 'act', pose: 'look', d: rand(2, 4) });
      else if (what === 'nap') { if (m.perch !== 'floor') q.push(...toPerch('floor', rand(30, 200), w)); q.push({ t: 'act', pose: 'nap', d: rand(6, 11) }); }
      else if (what === 'read') q.push({ t: 'act', pose: 'read', d: rand(5, 9) });
      else if (what === 'window') { q.push(...toPerch('sill', rand(70, 92), w)); q.push({ t: 'face', f: 1 }, { t: 'act', pose: 'gaze', d: rand(4, 8) }); }
      else if (what === 'dance') q.push({ t: 'act', pose: 'dance', d: 2.2 });
      else if (what === 'write') {
        const b = w.board;
        q.push(...toPerch('ledge', b.x + b.w - 30, w), { t: 'face', f: -1 });
        if (m.board.lines.length) q.push({ t: 'erase' });
        q.push({ t: 'write', lines: pick(LINES) }, { t: 'act', pose: 'look', d: 1.6 });
      }
      return q;
    }

    function start(s, w) {
      m.cur = s; s.el = 0;
      if (s.t === 'hop') { s.x0 = m.x; s.y0 = m.y; s.d = 0.55 + Math.abs(s.y - m.y) / 230; s.yc = Math.min(m.y, s.y) - 22 - Math.abs(s.y - m.y) * 0.25; m.facing = s.x >= m.x ? 1 : -1; m.pose = 'hop'; }
      if (s.t === 'walk') m.pose = 'walk';
      if (s.t === 'act') m.pose = s.pose;
      if (s.t === 'face') { m.facing = s.f; m.cur = null; }
      if (s.t === 'write') { m.board.lines = s.lines; m.board.shown = 0; s.total = s.lines.join('').length; m.pose = 'write'; }
      if (s.t === 'erase') { m.pose = 'write'; s.from = m.board.shown; }
    }
    function update(dt, w) {
      dt = Math.min(dt, 0.1);
      if (m.perch === 'ledge' && !w.board) { m.perch = 'floor'; m.y = FLOOR.y; m.q = []; m.cur = null; }   // window got short
      if (m.perch === 'ledge' && w.board && !(m.cur && m.cur.t === 'hop')) m.y = w.board.y + w.board.h + 3;
      if (!m.cur) { if (!m.q.length) m.q = plan(w); start(m.q.shift(), w); }
      const s = m.cur;
      if (s) {
        s.el += dt;
        if (s.t === 'walk') {
          const d = s.x - m.x; m.facing = d >= 0 ? 1 : -1; m.walkT += dt;
          m.x += Math.sign(d) * Math.min(Math.abs(d), 24 * dt);
          if (Math.abs(s.x - m.x) < 0.5) { m.cur = null; m.pose = 'stand'; }
        } else if (s.t === 'hop') {
          const u = clamp(s.el / s.d, 0, 1);
          m.x = s.x0 + (s.x - s.x0) * u;
          m.y = (1 - u) * (1 - u) * s.y0 + 2 * (1 - u) * u * s.yc + u * u * s.y;
          if (u >= 1) { m.perch = s.p; m.y = s.y; m.cur = null; m.pose = 'stand'; puff(m.x, m.y, 4); }
        } else if (s.t === 'act') {
          if (s.pose === 'look' && Math.random() < dt * 0.9) m.facing *= -1;
          if (s.pose === 'nap' && (s.zt = (s.zt || 0) + dt) > 0.9) { s.zt = 0; m.zs.push({ x: m.x + 3, y: m.y - 12, a: 0 }); }
          if (s.pose === 'dance') m.facing = Math.floor(s.el * 5) % 2 ? 1 : -1;
          if (s.el >= s.d) { m.cur = null; m.pose = 'stand'; }
        } else if (s.t === 'write') {
          const n = Math.min(s.total, Math.floor(s.el / 0.32));
          if (n > m.board.shown) { m.board.shown = n; if (w.board) chalkDust(w.board, n); }
          if (n >= s.total && s.el > s.total * 0.32 + 0.3) { m.cur = null; m.pose = 'stand'; }
        } else if (s.t === 'erase') {
          m.board.shown = Math.max(0, s.from - Math.floor(s.el / 0.06));
          if (w.board && Math.random() < 0.5) chalkDust(w.board, m.board.shown);
          if (m.board.shown === 0) { m.board.lines = []; m.cur = null; }
        }
      }
      // blink, z's, dust
      m.blinkAt -= dt; if (m.blinkAt <= 0) { m.blink = 0.13; m.blinkAt = rand(2, 5); }
      m.blink = Math.max(0, m.blink - dt);
      m.zs.forEach(z => { z.a += dt; z.y -= 7 * dt; z.x += 3 * dt; }); m.zs = m.zs.filter(z => z.a < 2.4);
      m.dust.forEach(d => { d.a += dt; d.y += d.vy * dt; d.x += d.vx * dt; d.vy += 30 * dt; }); m.dust = m.dust.filter(d => d.a < d.life);
      if (m.say && performance.now() > m.say.until) m.say = null;
    }
    function puff(x, y, n) { for (let i = 0; i < n; i++) m.dust.push({ x: x + rand(-3, 3), y: y - 1, vx: rand(-8, 8), vy: rand(-14, -4), a: 0, life: rand(0.3, 0.6) }); }
    function chalkDust(b, n) {
      const pos = writePos(b, n);
      m.dust.push({ x: pos.x + rand(0, 3), y: pos.y + 5, vx: rand(-4, 4), vy: rand(0, 6), a: 0, life: rand(0.5, 1.1) });
      m.x += (clamp(pos.x - 4, b.x + 6, b.x + b.w - 6) - m.x) * 0.5;   // follow the hand along the line
    }
    function writePos(b, n) {   // where character n (counting across lines) is written
      let i = n, line = 0; const L = m.board.lines;
      while (line < L.length - 1 && i > L[line].length) { i -= L[line].length; line++; }
      return { x: b.x + 76 + Math.max(0, i - 1) * 4, y: b.y + 7 + line * 9 };
    }

    function draw(ctx, w) {
      // dust and z's behind nothing in particular: drawn first so Chalky stays on top
      m.dust.forEach(d => { ctx.fillStyle = `rgba(240,236,224,${(1 - d.a / d.life).toFixed(2)})`; ctx.fillRect(Math.round(d.x), Math.round(d.y), 1, 1); });
      m.zs.forEach(z => { ctx.globalAlpha = Math.max(0, 1 - z.a / 2.4); zGlyph(ctx, Math.round(z.x), Math.round(z.y)); ctx.globalAlpha = 1; });
      const x = Math.round(m.x), y = Math.round(m.y), f = m.facing, pose = m.pose;
      const sit = pose === 'nap' || pose === 'read' || pose === 'gaze';
      const bob = pose === 'dance' ? (Math.floor(performance.now() / 120) % 2) : 0;
      const top = y - (sit ? 10 : 12) - bob;
      const px = (dx, dy, c) => { ctx.fillStyle = c; ctx.fillRect(x + dx, top + dy, 1, 1); };
      const row = (x0, x1, dy, c) => { ctx.fillStyle = c; ctx.fillRect(x + x0, top + dy, x1 - x0 + 1, 1); };
      if (pose !== 'hop') { ctx.fillStyle = 'rgba(0,0,0,.28)'; ctx.fillRect(x - 3, y, 7, 1); }
      // body: rounded top, a shaded side, the green wrapper
      const bodyRows = sit ? 10 : 10;
      row(-1, 1, 0, C.body);
      for (let r = 1; r < bodyRows; r++) { row(-2, 2, r, C.body); px(f > 0 ? -2 : 2, r, C.shade); }
      row(-2, 2, 6, C.band); row(-2, 2, 7, C.band); px(f > 0 ? -2 : 2, 6, C.bandLo); px(f > 0 ? -2 : 2, 7, C.bandLo);
      // face
      const shut = pose === 'nap' || m.blink > 0;
      const e1 = f > 0 ? 0 : -2, e2 = f > 0 ? 2 : 0;
      if (shut) { px(e1, 4, C.shut); px(e2, 4, C.shut); }
      else if (pose === 'gaze') { px(e1, 2, C.eye); px(e2, 2, C.eye); }    // looking up at the moon
      else { px(e1, 3, C.eye); px(e2, 3, C.eye); }
      if (m.say || pose === 'dance') px(f > 0 ? 1 : -1, 5, C.eye);
      if (pose !== 'nap') px(f > 0 ? 2 : -2, 4, C.cheek);
      // arms
      const sw = pose === 'walk' ? (Math.floor(m.walkT * 6) % 2) : 0;
      if (pose === 'write') { px(3 * f, 3, C.body); px(3 * f, 2, C.body); px(3 * f, 1, '#ffffff'); px(-3 * f, 5, C.body); }
      else if (pose === 'read') {
        const bx = f > 0 ? 2 : -7; ctx.fillStyle = C.book; ctx.fillRect(x + bx, top + 4, 6, 4);
        ctx.fillStyle = C.page; ctx.fillRect(x + bx + 1, top + 4, 4, 3);
        const flip = Math.floor(performance.now() / 1300) % 2; ctx.fillStyle = '#bdb4a0'; ctx.fillRect(x + bx + (flip ? 2 : 3), top + 4, 1, 3);
      } else if (pose === 'dance' || (m.say && pose !== 'nap')) { px(-3, 2, C.body); px(3, 2, C.body); px(-3, 3, C.body); px(3, 3, C.body); }
      else if (!sit) { px(-3, 5 + sw, C.body); px(3, 6 - sw, C.body); }
      // legs
      if (!sit) {
        const lg = pose === 'walk' ? (Math.floor(m.walkT * 8) % 2) : 0;
        if (pose === 'hop') { px(-1, 10, C.shade); px(1, 10, C.shade); }
        else { px(-1, 10, C.shade); px(1, 10, C.shade); px(-1 - lg, 11, C.shade); px(1 + lg, 11, C.shade); }
      } else { px(-2, 9, C.shade); px(2, 9, C.shade); }
    }
    function zGlyph(ctx, x, y) { ctx.fillStyle = '#cfd8e8'; ctx.fillRect(x, y, 3, 1); ctx.fillRect(x + 1, y + 1, 1, 1); ctx.fillRect(x, y + 2, 3, 1); }

    return {
      update, draw,
      get board() { return m.board; },
      get say() { return m.say; },
      pos: () => ({ x: m.x, y: m.y }),
      hit: (x, y) => x >= m.x - 4 && x <= m.x + 4 && y >= m.y - 14 && y <= m.y + 1,
      poke(w) {
        const text = w && w.busy && Math.random() < 0.6 ? w.busy : TIPS[m.tipN++ % TIPS.length];
        m.say = { text, until: performance.now() + 4200 };
        if (!m.cur || m.cur.t !== 'hop') { const [, , py] = range(m.perch, w); m.q = []; start({ t: 'hop', p: m.perch, x: m.x, y: py }, w); m.cur.d = 0.45; m.cur.yc = py - 14; }
        return text;
      },
    };
  }
  global.Chalky = { create };
})(window);
