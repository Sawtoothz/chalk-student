/* Chalk library shelf — the Library's front page, in pixel art.
   A bookshelf (one labelled spine per book on disk, on the middle shelf), a filing box of papers (one tabbed sheet per
   paper) and an ADD letter tray on the side table, drawn on a small canvas scaled up with crisp pixels. The canvas is
   as tall as the window's aspect needs: extra height is wall above the room, so the scene fills the screen.
   Hover lifts an item; click selects it (books and papers) or asks to add a PDF (the tray).
   Usage: const shelf = Shelf.mount(canvasEl, sources, { onSelect(id) {}, onAdd() {}, a11y: containerEl })
     shelf.rectOf(id) -> the item's rectangle on screen (for the open-book animation); shelf.colorOf(id);
     shelf.setDropping(bool) highlights the tray while a file is dragged over the scene.
   sources: pages.listing() entries (id, kind, title, authors, pdf_present, units[{unit,title,done,next,job}]).
   Keyboard: one visually hidden button per item goes into opts.a11y; focusing it lifts the item. */
(function (global) {
  const W = 480, BASE_H = 200;

  /* ---- 3×5 pixel font */
  const GLYPH = {
    A: '010101111101101', B: '110101110101110', C: '011100100100011', D: '110101101101110', E: '111100110100111',
    F: '111100110100100', G: '011100101101011', H: '101101111101101', I: '111010010010111', J: '001001001101010',
    K: '101101110101101', L: '100100100100111', M: '101111111101101', N: '110101101101101', O: '010101101101010',
    P: '110101110100100', Q: '010101101110011', R: '110101110101101', S: '011100010001110', T: '111010010010010',
    U: '101101101101111', V: '101101101101010', W: '101101111111101', X: '101101010101101', Y: '101101010010010',
    Z: '111001010100111', 0: '111101101101111', 1: '010110010010111', 2: '110001010100111', 3: '110001010001110',
    4: '101101111001001', 5: '111100110001110', 6: '011100111101111', 7: '111001010010010', 8: '111101111101111',
    9: '111101111001110', '-': '000000111000000', '.': '000000000000010', ' ': '000000000000000', '+': '000010111010000',
    '=': '000111000111000', '/': '001001010100100', '!': '010010010000010', '?': '110001010000010',
  };
  function glyph(ctx, ch, x, y, c) {
    const g = GLYPH[ch] || GLYPH[' ']; ctx.fillStyle = c;
    for (let i = 0; i < 15; i++) if (g[i] === '1') ctx.fillRect(x + (i % 3), y + Math.floor(i / 3), 1, 1);
  }
  const textH = (ctx, s, x, y, c) => [...s].forEach((ch, i) => glyph(ctx, ch, x + i * 4, y, c));   // left to right
  const textV = (ctx, s, x, y, c) => [...s].forEach((ch, i) => glyph(ctx, ch, x, y + i * 6, c));   // stacked down a spine

  /* ---- palette: a small fixed set */
  const P = {
    wall: '#2b2420', wallDot: '#352b25', floor: '#5a3d26', floorLine: '#4a3220', floorHi: '#6b4a2f',
    frame: '#6b4524', frameHi: '#8a5a30', frameLo: '#4a2e17', back: '#1d1714', board: '#7a5030', boardHi: '#9a6a3c',
    spines: ['#7a2e2e', '#2f4f6f', '#3d5a40', '#6b4f2a', '#5a3e6b', '#2e5f63', '#8a6a2a', '#4a4a58'],
    gold: '#d9b45a', paper: '#f4efe2', paperLo: '#d6cfbd', ink: '#2a2420', box: '#b07a3a', boxHi: '#c99248', boxLo: '#8a5c28',
    chalk: '#3ec294', sel: '#8fe0c2', shadow: 'rgba(0,0,0,.35)', plant: '#4f7a43', plantHi: '#6b9a55', pot: '#a8553a',
    tray: '#7a5030', trayHi: '#9a6a3c', trayLo: '#55361c',
  };
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const hash = s => { let h = 0; for (const c of s) h = (h * 31 + c.charCodeAt(0)) | 0; return Math.abs(h); };
  const shortTitle = s => s.title.split(/[:—]/)[0].replace(/,\s*\d.*$/, '').trim();
  const ready = s => s.units.filter(u => u.done && u.done.includes('review')).length;   // slides are optional
  const started = s => s.units.filter(u => u.done && u.done.length && !u.done.includes('review')).length;
  function statusLine(s) {
    if (s.kind === 'paper') return ready(s) ? 'package reviewed' : started(s) ? 'in preparation' : 'not started';
    return `${ready(s)} of ${s.units.length} chapters ready` + (started(s) ? `, ${started(s)} in progress` : '');
  }
  const surname = s => (s.authors || shortTitle(s)).split(/[,\s]/)[0];
  // books: first author; papers: a one-word short title (FAST-LIO2), else the first author (GRISETTI)
  const label = (s, n) => (s.kind === 'paper' && !/\s/.test(shortTitle(s)) ? shortTitle(s) : surname(s))
    .normalize('NFD').toUpperCase().replace(/[^A-Z0-9 .-]/g, '').slice(0, n);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  /* ---- static scenery (in the 480×200 room), drawn once into a buffer */
  const SHELF = { x: 222, y: 10, w: 236, h: 178, boards: [58, 126, 184] };  // middle shelf is the tallest: it holds the labelled spines
  const BOX = { x: 40, y: 128, w: 120, h: 34 };
  const TRAY = { x: 166, y: 150, w: 30, h: 11 };   // ADD letter tray on the side table, right of the paper box
  function scenery(ctx) {
    seed = 7;
    ctx.fillStyle = P.wall; ctx.fillRect(0, 0, W, BASE_H);
    for (let i = 0; i < 260; i++) { ctx.fillStyle = P.wallDot; ctx.fillRect(Math.floor(rnd() * W), Math.floor(rnd() * 176), 1, 1); }
    ctx.fillStyle = P.floor; ctx.fillRect(0, 186, W, 14);
    ctx.fillStyle = P.floorHi; ctx.fillRect(0, 186, W, 1);
    ctx.fillStyle = P.floorLine; for (let x = 0; x < W; x += 37) ctx.fillRect(x, 190 + (x % 3) * 3, 22, 1);

    // night window, top left
    ctx.fillStyle = P.frameLo; ctx.fillRect(56, 18, 64, 56);
    ctx.fillStyle = '#1e2c44'; ctx.fillRect(60, 22, 56, 48);
    ctx.fillStyle = '#2a3c5c'; ctx.fillRect(60, 22, 56, 14);
    ctx.fillStyle = '#e8e2c8'; ctx.fillRect(98, 28, 6, 6); ctx.fillRect(97, 29, 8, 4);
    ctx.fillStyle = '#cfd8e8'; [[68, 30], [80, 54], [72, 60], [108, 56], [92, 26]].forEach(([x, y]) => ctx.fillRect(x, y, 1, 1));
    ctx.fillStyle = P.frame; ctx.fillRect(87, 22, 2, 48); ctx.fillRect(60, 45, 56, 2);
    ctx.fillStyle = P.frameHi; ctx.fillRect(54, 74, 68, 3);

    // side table (holds the paper box and the ADD tray); a potted plant on the floor beside it
    ctx.fillStyle = P.frameLo; ctx.fillRect(34, 162, 166, 4);
    ctx.fillStyle = P.frame; ctx.fillRect(34, 161, 166, 2);
    ctx.fillStyle = P.frameLo; ctx.fillRect(40, 166, 4, 20); ctx.fillRect(192, 166, 4, 20);
    const px = 202;
    ctx.fillStyle = P.pot; ctx.fillRect(px, 174, 14, 12); ctx.fillStyle = '#8a4430'; ctx.fillRect(px, 174, 14, 2);
    ctx.fillStyle = P.plant; [[px + 6, 152, 2, 22], [px + 2, 158, 2, 16], [px + 10, 156, 2, 18], [px - 2, 164, 2, 10], [px + 14, 162, 2, 12]].forEach(r => ctx.fillRect(...r));
    ctx.fillStyle = P.plantHi; [[px + 6, 152, 1, 6], [px + 10, 156, 1, 5], [px + 2, 158, 1, 5]].forEach(r => ctx.fillRect(...r));

    // bookshelf frame
    const S = SHELF;
    ctx.fillStyle = P.shadow; ctx.fillRect(S.x + 4, S.y + 4, S.w, S.h - 2);
    ctx.fillStyle = P.frame; ctx.fillRect(S.x, S.y, S.w, S.h);
    ctx.fillStyle = P.back; ctx.fillRect(S.x + 6, S.y + 6, S.w - 12, S.h - 10);
    ctx.fillStyle = P.frameHi; ctx.fillRect(S.x, S.y, S.w, 2); ctx.fillRect(S.x, S.y, 2, S.h);
    ctx.fillStyle = P.frameLo; ctx.fillRect(S.x + S.w - 2, S.y, 2, S.h);
    S.boards.forEach(y => { ctx.fillStyle = P.board; ctx.fillRect(S.x + 2, y, S.w - 4, 4); ctx.fillStyle = P.boardHi; ctx.fillRect(S.x + 2, y, S.w - 4, 1); });
  }

  /* decorative spines on a shelf, deterministic */
  function filler(ctx, y, x0, x1, s0, maxH) {
    seed = s0; let x = x0;
    while (x < x1 - 5) {
      const w = 5 + Math.floor(rnd() * 5), h = Math.min(maxH, 30 + Math.floor(rnd() * 20));
      if (x + w > x1) break;
      const c = P.spines[Math.floor(rnd() * P.spines.length)];
      if (rnd() < 0.08 && x + h < x1) {  // a book lying flat
        ctx.fillStyle = c; ctx.fillRect(x, y - w, h, w); ctx.fillStyle = P.gold; ctx.fillRect(x + 3, y - w + 1, 1, w - 2);
        x += h + 1; continue;
      }
      ctx.fillStyle = c; ctx.fillRect(x, y - h, w, h);
      ctx.fillStyle = 'rgba(255,255,255,.12)'; ctx.fillRect(x, y - h, 1, h);
      ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fillRect(x + w - 1, y - h, 1, h);
      if (rnd() < 0.7) { ctx.fillStyle = P.gold; ctx.fillRect(x + 1, y - h + 4, w - 2, 1); ctx.fillRect(x + 1, y - 6, w - 2, 1); }
      x += w + (rnd() < 0.15 ? 2 : 0);
    }
  }

  /* ---- items */
  function layout(books, papers) {
    const items = [];
    const S = SHELF; let x = S.x + 10;
    books.forEach(s => {
      const lab = label(s, 7), h = Math.max(46, lab.length * 6 + 16);  // at most 7 letters: 58 px fits the 64 px shelf
      if (x + 16 > S.x + S.w - 10) return;
      items.push({ src: s, kind: 'book', x, y: S.boards[1] - h, w: 16, h, lab, color: P.spines[hash(s.id) % P.spines.length] });
      x += 19;
    });
    const fillFrom = x + 2;
    const ps = papers.slice(0, 6), step = ps.length > 1 ? Math.min(50, (BOX.w - 16 - 48) / (ps.length - 1)) : 0;
    ps.forEach((s, i) => {   // side by side while they fit, then fanned
      const lab = label(s, 10);
      items.push({ src: s, kind: 'paper', x: Math.round(BOX.x + 8 + i * step), y: BOX.y - 26 - (i % 2) * 4, w: Math.max(44, lab.length * 4 + 8), h: 44, lab });
    });
    items.push({ src: null, kind: 'tray', x: TRAY.x, y: TRAY.y - 6, w: TRAY.w, h: TRAY.h + 6 });
    return { items, fillFrom };
  }
  function outline(ctx, x, y, w, h) {
    ctx.fillStyle = P.sel; ctx.fillRect(x - 2, y - 2, w + 4, 1); ctx.fillRect(x - 2, y + h + 1, w + 4, 1); ctx.fillRect(x - 2, y - 2, 1, h + 4); ctx.fillRect(x + w + 1, y - 2, 1, h + 4);
  }
  function drawBook(ctx, it, lift, sel) {
    const y = it.y - lift;
    ctx.fillStyle = it.color; ctx.fillRect(it.x, y, it.w, it.h);
    ctx.fillStyle = 'rgba(255,255,255,.18)'; ctx.fillRect(it.x, y, 2, it.h);
    ctx.fillStyle = 'rgba(0,0,0,.3)'; ctx.fillRect(it.x + it.w - 2, y, 2, it.h);
    ctx.fillStyle = P.gold; ctx.fillRect(it.x + 2, y + 3, it.w - 4, 1); ctx.fillRect(it.x + 2, y + it.h - 4, it.w - 4, 1);
    textV(ctx, it.lab, it.x + 6, y + 7, '#f4efe2');
    const n = Math.min(6, ready(it.src));  // one green pixel per reviewed chapter, up to 6
    for (let i = 0; i < n; i++) { ctx.fillStyle = P.chalk; ctx.fillRect(it.x + 3 + (i % 3) * 4, y + it.h - 10 + Math.floor(i / 3) * 3, 2, 2); }
    if (sel) outline(ctx, it.x, y, it.w, it.h);
  }
  function drawSheet(ctx, it, lift, sel) {
    const y = it.y - lift;
    ctx.fillStyle = P.paperLo; ctx.fillRect(it.x + 1, y + 1, it.w, it.h);
    ctx.fillStyle = P.paper; ctx.fillRect(it.x, y, it.w, it.h);
    ctx.fillStyle = P.chalk; ctx.fillRect(it.x + 2, y - 3, 12, 3);  // tab
    textH(ctx, it.lab, it.x + 4, y + 4, P.ink);
    ctx.fillStyle = P.paperLo; for (let i = 0; i < 4; i++) ctx.fillRect(it.x + 4, y + 13 + i * 4, it.w - 10 - (i % 2) * 8, 1);
    if (ready(it.src)) { ctx.fillStyle = P.chalk; ctx.fillRect(it.x + it.w - 6, y + 3, 3, 3); }
    if (sel) outline(ctx, it.x, y, it.w, BOX.y - y + 1);
  }
  function drawBox(ctx) {  // front of the filing box, over the lower part of the sheets
    const B = BOX;
    ctx.fillStyle = P.box; ctx.fillRect(B.x, B.y, B.w, B.h);
    ctx.fillStyle = P.boxHi; ctx.fillRect(B.x, B.y, B.w, 2);
    ctx.fillStyle = P.boxLo; ctx.fillRect(B.x, B.y + B.h - 2, B.w, 2); ctx.fillRect(B.x + B.w - 2, B.y, 2, B.h);
    ctx.fillStyle = '#efe2c4'; ctx.fillRect(B.x + 38, B.y + 12, 44, 11);
    textH(ctx, 'PAPERS', B.x + 48, B.y + 15, P.ink);
  }
  function drawTray(ctx, lift, glow, t) {  // letter tray: a blank sheet with a chalk plus rises when hovered
    const T = TRAY, sy = T.y - 5 - lift;
    ctx.fillStyle = P.paperLo; ctx.fillRect(T.x + 4, sy + 1, 22, 8);
    ctx.fillStyle = P.paper; ctx.fillRect(T.x + 3, sy, 22, 8);
    const pc = glow && Math.floor(t / 300) % 2 ? P.sel : P.chalk;
    glyph(ctx, '+', T.x + 12, sy + 1, pc); glyph(ctx, '+', T.x + 13, sy + 1, pc);
    ctx.fillStyle = P.tray; ctx.fillRect(T.x, T.y, T.w, T.h);
    ctx.fillStyle = P.trayHi; ctx.fillRect(T.x, T.y, T.w, 1); ctx.fillRect(T.x, T.y, 1, T.h);
    ctx.fillStyle = P.trayLo; ctx.fillRect(T.x, T.y + T.h - 1, T.w, 1); ctx.fillRect(T.x + T.w - 1, T.y, 1, T.h);
    ctx.fillStyle = '#efe2c4'; ctx.fillRect(T.x + 8, T.y + 3, 15, 7);
    textH(ctx, 'ADD', T.x + 10, T.y + 4, P.ink);
    if (glow) outline(ctx, T.x, sy, T.w, T.y + T.h - sy);
  }

  /* ---- mount */
  function mount(canvas, sources, opts) {
    opts = opts || {};
    const ctx = canvas.getContext('2d');
    const onDisk = sources.filter(s => s.pdf_present && s.units && s.units.length);
    const { items, fillFrom } = layout(onDisk.filter(s => s.kind !== 'paper'), onDisk.filter(s => s.kind === 'paper'));

    const bg = document.createElement('canvas'); bg.width = W; bg.height = BASE_H;
    const b = bg.getContext('2d'); scenery(b);
    filler(b, SHELF.boards[0], SHELF.x + 8, SHELF.x + SHELF.w - 8, 3, 40);
    filler(b, SHELF.boards[1], fillFrom, SHELF.x + SHELF.w - 8, 11, 56);
    filler(b, SHELF.boards[2], SHELF.x + 8, SHELF.x + SHELF.w - 8, 29, 50);

    let H = BASE_H, OY = 0;   // canvas height and the room's offset in it (wall fills the space above)
    function boardRect() {    // canvas coordinates; null when the wall above the room is too short for it
      if (OY < 34) return null;
      const w = 124, h = 30; return { x: 88 - w / 2, y: Math.max(3, Math.round((OY + 14 - h) / 2)), w, h };
    }
    // the mascot (app/static/chalky.js), if loaded; it learns the room through world()
    const chalky = global.Chalky ? global.Chalky.create() : null;
    const running = sources.flatMap(s => s.units.filter(u => u.job && ['queued', 'running'].includes(u.job.state))
      .map(u => `${shortTitle(s)}${s.kind === 'paper' ? '' : ' ch. ' + u.unit}: ${u.job.stage === 'next' ? u.next : u.job.stage}, ${u.job.state}`));
    const busy = running.length ? `I\u2019m watching ${running[0]}.` : null;
    function world() {
      const B = boardRect();
      return { OY, board: B ? { x: B.x, y: B.y - OY, w: B.w, h: B.h } : null, busy };
    }
    function fit() {
      const r = canvas.parentNode.getBoundingClientRect();
      H = r.width && r.height ? Math.max(BASE_H, Math.min(BASE_H * 3, Math.round(W * r.height / r.width))) : BASE_H;
      OY = H - BASE_H;
      canvas.width = W; canvas.height = H; ctx.imageSmoothingEnabled = false;
      draw();
    }

    let hover = null, focus = null, selected = opts.selected || null, dropping = false;
    const MASCOT = { kind: 'mascot' };
    const lifts = new Map(items.map(it => [it, 0]));
    const reduce = global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches;
    function draw(t) {
      ctx.fillStyle = P.wall; ctx.fillRect(0, 0, W, H);
      seed = 101; ctx.fillStyle = P.wallDot;
      for (let i = 0; i < OY * 1.4; i++) ctx.fillRect(Math.floor(rnd() * W), Math.floor(rnd() * OY), 1, 1);
      const B = boardRect();
      if (B) {   // a chalkboard on the wall above the window, when the window is tall enough to show one
        const bw = B.w, bh = B.h, bx = B.x, by = B.y;
        ctx.fillStyle = P.frameLo; ctx.fillRect(bx - 3, by - 3, bw + 6, bh + 6);
        ctx.fillStyle = P.frame; ctx.fillRect(bx - 3, by - 3, bw + 6, 1); ctx.fillRect(bx - 3, by - 3, 1, bh + 6);
        ctx.fillStyle = '#2f4a3a'; ctx.fillRect(bx, by, bw, bh);
        ctx.fillStyle = 'rgba(255,255,255,.05)'; ctx.fillRect(bx + 6, by + 4, 30, 2); ctx.fillRect(bx + 50, by + 22, 26, 1);
        [...'CHALK'].forEach((ch, i) => { const g = GLYPH[ch]; ctx.fillStyle = '#e8eee6';
          for (let k = 0; k < 15; k++) if (g[k] === '1') ctx.fillRect(bx + 8 + i * 12 + (k % 3) * 3, by + 7 + Math.floor(k / 3) * 3, 3, 3); });
        ctx.fillStyle = P.chalk; ctx.fillRect(bx + 8, by + 25, 56, 1);
        if (chalky) {   // whatever Chalky last wrote, up to the character it has reached
          let left = chalky.board.shown;
          chalky.board.lines.forEach((ln, li) => { const vis = ln.slice(0, Math.max(0, left)); left -= ln.length; textH(ctx, vis, bx + 76, by + 7 + li * 9, '#e8eee6'); });
        }
        ctx.fillStyle = P.frameHi; ctx.fillRect(bx - 4, by + bh + 3, bw + 8, 2);
        ctx.fillStyle = '#f4efe2'; ctx.fillRect(bx + 10, by + bh + 1, 6, 2);
        ctx.fillStyle = '#c9a46a'; ctx.fillRect(bx + bw - 22, by + bh, 10, 3);
      }
      ctx.save(); ctx.translate(0, OY);
      ctx.drawImage(bg, 0, 0);
      items.filter(i => i.kind === 'book').forEach(it => drawBook(ctx, it, Math.round(lifts.get(it)), it.src.id === selected));
      items.filter(i => i.kind === 'paper').forEach(it => drawSheet(ctx, it, Math.round(lifts.get(it)), it.src.id === selected));
      drawBox(ctx);
      const tray = items.find(i => i.kind === 'tray');
      drawTray(ctx, Math.round(lifts.get(tray)), dropping || tray === hover || tray === focus, t || 0);
      if (chalky) chalky.draw(ctx, world());
      ctx.restore();
    }
    let raf = null, last = 0;
    const live = chalky && !reduce;   // with a mascot the room animates continuously (paused by the browser in hidden tabs)
    function animate(t) {  // ease the hovered or focused item up, the rest back down; blink the tray while dropping
      let moving = dropping || live;
      if (live) { const dt = last ? (t - last) / 1000 : 0; last = t; chalky.update(dt, world()); placeSay(); }
      items.forEach(it => {
        const goal = (it === hover || it === focus || (dropping && it.kind === 'tray')) ? (it.kind === 'tray' ? 4 : 5) : 0;
        const v = lifts.get(it), nv = reduce ? goal : v + (goal - v) * 0.35;
        lifts.set(it, Math.abs(goal - nv) < 0.2 ? goal : nv); if (lifts.get(it) !== goal) moving = true;
      });
      draw(t); raf = moving ? requestAnimationFrame(animate) : null;
    }
    const kick = () => { if (!raf) raf = requestAnimationFrame(animate); };

    const tip = document.createElement('div'); tip.className = 'shelf-tip'; tip.hidden = true;
    canvas.parentNode.appendChild(tip);
    const bubble = document.createElement('div'); bubble.className = 'chalky-say'; bubble.hidden = true; bubble.setAttribute('role', 'status');
    canvas.parentNode.appendChild(bubble);
    function placeSay() {   // speech bubble over Chalky's head while it talks
      const say = chalky && chalky.say;
      if (!say) { bubble.hidden = true; return; }
      const { s, ox, oy } = toRoom({ clientX: 0, clientY: 0 }), r = canvas.parentNode.getBoundingClientRect(), p = chalky.pos();
      bubble.hidden = false; if (bubble.textContent !== say.text) bubble.textContent = say.text;
      bubble.style.left = Math.max(8, Math.min(r.width - bubble.offsetWidth - 8, ox - r.left + p.x * s - bubble.offsetWidth / 2)) + 'px';
      bubble.style.top = Math.max(4, oy - r.top + (p.y + OY - 16) * s - bubble.offsetHeight) + 'px';
    }
    function toRoom(e) {   // client point -> room pixel, accounting for object-fit: contain letterboxing
      const r = canvas.getBoundingClientRect(), s = Math.min(r.width / W, r.height / H);
      const ox = r.left + (r.width - W * s) / 2, oy = r.top + (r.height - H * s) / 2;
      return { x: (e.clientX - ox) / s, y: (e.clientY - oy) / s - OY, s, ox, oy };
    }
    function at(e) {
      const { x, y } = toRoom(e);
      if (chalky && chalky.hit(x, y)) return MASCOT;
      // sheets stand behind the box front: only their visible top counts
      return [...items].reverse().find(it => x >= it.x && x < it.x + it.w && y >= it.y - 6 && y < (it.kind === 'paper' ? BOX.y : it.y + it.h)) || null;
    }
    canvas.addEventListener('mousemove', e => {
      const it = at(e);
      if (it !== hover) { hover = it; canvas.style.cursor = it ? 'pointer' : 'default'; kick(); }
      if (it) {
        const r = canvas.parentNode.getBoundingClientRect();
        tip.hidden = false; tip.style.left = Math.min(e.clientX - r.left + 14, r.width - 300) + 'px'; tip.style.top = (e.clientY - r.top + 14) + 'px';
        tip.innerHTML = it === MASCOT ? '<b>Chalky</b><br>Click to say hello' : it.kind === 'tray' ? '<b>Add a PDF</b><br>Click, or drop a PDF anywhere on the room'
          : `<b>${esc(it.src.title)}</b><br>${esc(it.src.authors || '')}${it.src.year ? ', ' + it.src.year : ''}<br>${statusLine(it.src)}`;
      } else tip.hidden = true;
    });
    canvas.addEventListener('mouseleave', () => { hover = null; tip.hidden = true; kick(); });
    const choose = it => {
      tip.hidden = true;
      if (it === MASCOT) { chalky.poke(world()); placeSay(); if (!live) { draw(); setTimeout(() => { bubble.hidden = true; }, 4200); } kick(); return; }
      if (it.kind === 'tray') { opts.onAdd && opts.onAdd(); return; }
      selected = it.src.id; draw(); opts.onSelect && opts.onSelect(it.src.id);
    };
    canvas.addEventListener('click', e => { const it = at(e); if (it) choose(it); });

    if (opts.a11y) items.forEach(it => {
      const btn = document.createElement('button'); btn.type = 'button'; btn.className = 'sr-only';
      btn.textContent = it.kind === 'tray' ? 'Add a PDF to the library' : `${it.kind === 'paper' ? 'Paper' : 'Book'}: ${it.src.title}. ${statusLine(it.src)}.`;
      btn.addEventListener('focus', () => { focus = it; kick(); });
      btn.addEventListener('blur', () => { focus = null; kick(); });
      btn.addEventListener('click', () => choose(it));
      opts.a11y.appendChild(btn);
    });
    fit();
    global.addEventListener('resize', fit);
    if (live) kick();

    function rectOf(id) {   // on-screen rectangle of a book spine or paper sheet, for the open animation
      const it = items.find(i => i.src && i.src.id === id); if (!it) return null;
      const { s, ox, oy } = toRoom({ clientX: 0, clientY: 0 });
      const h = it.kind === 'paper' ? BOX.y - it.y : it.h;
      return { left: ox + it.x * s, top: oy + (it.y + OY - Math.round(lifts.get(it))) * s, width: it.w * s, height: h * s };
    }
    return {
      items, rectOf, mascot: chalky,
      colorOf: id => (items.find(i => i.src && i.src.id === id) || {}).color || P.spines[hash(id) % P.spines.length],
      select: id => { selected = id; draw(); },
      setDropping: v => { if (v !== dropping) { dropping = v; kick(); } },
    };
  }

  global.Shelf = { mount, statusLine };
})(window);
