// isokit.js: shared Three.js kit for Chalk figures.
// Fixed isometric orthographic stage, flat-toned solids with dark outlines,
// role colours read from figure.css, vision-frame helpers, 2-D plate drawing, eased animation.
// Resolve 'three' with an import map, e.g.
//   {"imports": {"three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"}}

import * as THREE from "three";

export { THREE };

export const ISO_ELEVATION = Math.atan(1 / Math.SQRT2); // 35.264 deg, true isometric

const FALLBACK = {
  light: {
    ink: "#1f1e1d", muted: "#5f5e5a", faint: "#888780",
    edge: "#2c2c2a", bench: "#d3d1c7", foot: "#b4b2a9", grid: "#b4b2a9", plate: "#f5f4ef",
    blue: "#378add", blueDeep: "#0c447c", coral: "#d85a30", coralDeep: "#712b13",
    teal: "#1d9e75", tealDeep: "#085041", gray: "#888780", amber: "#ba7517",
  },
  dark: {
    ink: "#f5f4ef", muted: "#b4b2a9", faint: "#888780",
    edge: "#d3d1c7", bench: "#5f5e5a", foot: "#444441", grid: "#5f5e5a", plate: "#30302e",
    blue: "#378add", blueDeep: "#0c447c", coral: "#d85a30", coralDeep: "#712b13",
    teal: "#1d9e75", tealDeep: "#085041", gray: "#888780", amber: "#ba7517",
  },
};

const kebab = (s) => s.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());

export function isDark(el = document.documentElement) {
  const themed = el.closest ? el.closest("[data-theme]") : null;
  if (themed) return themed.dataset.theme === "dark";
  return matchMedia("(prefers-color-scheme: dark)").matches;
}

// Reads --fig-* tokens from figure.css; falls back to built-in values.
export function readPalette(el = document.documentElement) {
  const dark = isDark(el);
  const cs = getComputedStyle(el);
  const base = FALLBACK[dark ? "dark" : "light"];
  const P = { dark };
  for (const k of Object.keys(base)) {
    const v = cs.getPropertyValue("--fig-" + kebab(k)).trim();
    P[k] = v || base[k];
  }
  return P;
}

// Calls fn whenever the colour scheme changes.
export function onThemeChange(fn) {
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", fn);
  new MutationObserver(fn).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });
}

// Vision camera frame (x right, y down, z forward) to Three.js world (y up).
export const cv = (p) => new THREE.Vector3(p[0], -p[1], -p[2]);

// Pinhole helpers: K = [[f,0,cx],[0,f,cy],[0,0,1]].
export const backProject = (u, v, depth, { f, cx, cy }) => [
  ((u - cx) / f) * depth,
  ((v - cy) / f) * depth,
  depth,
];

export function disposeTree(obj) {
  obj.traverse((o) => {
    if (o.geometry) o.geometry.dispose();
    const mats = o.material ? (Array.isArray(o.material) ? o.material : [o.material]) : [];
    for (const m of mats) {
      if (m.map) m.map.dispose();
      m.dispose();
    }
  });
}

const LIGHT_DIR = new THREE.Vector3(-0.55, 0.62, 0.56).normalize();
const TONES = [0.6, 0.72, 0.84, 0.94];
const TOP_LIFT = 0.12;

// Builds the drawing kit for one palette. Rebuild after a theme change.
export function makeKit(P) {
  const edgeMat = new THREE.LineBasicMaterial({
    color: P.edge,
    transparent: true,
    opacity: P.dark ? 0.7 : 0.85,
  });

  // Flat four-tone shading from a fixed light, plus crisp outline edges.
  function solid(geo, color, { edges = true, threshold = 28, edgeColor } = {}) {
    const g = geo.index ? geo.toNonIndexed() : geo.clone();
    const pos = g.attributes.position;
    const col = new Float32Array(pos.count * 3);
    const base = new THREE.Color(color);
    const white = new THREE.Color(1, 1, 1);
    const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
    const n = new THREE.Vector3(), e = new THREE.Vector3();
    const tone = new THREE.Color();
    for (let i = 0; i < pos.count; i += 3) {
      a.fromBufferAttribute(pos, i);
      b.fromBufferAttribute(pos, i + 1);
      c.fromBufferAttribute(pos, i + 2);
      n.subVectors(b, a).cross(e.subVectors(c, a)).normalize();
      if (n.y > 0.72) {
        tone.copy(base).lerp(white, TOP_LIFT);
      } else if (n.y < -0.72) {
        tone.copy(base).multiplyScalar(TONES[0]);
      } else {
        const d = n.dot(LIGHT_DIR);
        const k = d > 0.45 ? 3 : d > 0.05 ? 2 : d > -0.4 ? 1 : 0;
        tone.copy(base).multiplyScalar(TONES[k]);
      }
      for (let j = 0; j < 3; j++) {
        col[(i + j) * 3] = tone.r;
        col[(i + j) * 3 + 1] = tone.g;
        col[(i + j) * 3 + 2] = tone.b;
      }
    }
    g.setAttribute("color", new THREE.BufferAttribute(col, 3));
    const mesh = new THREE.Mesh(
      g,
      new THREE.MeshBasicMaterial({
        vertexColors: true,
        polygonOffset: true,
        polygonOffsetFactor: 1,
        polygonOffsetUnits: 1,
      }),
    );
    if (edges) {
      const em = edgeColor ? new THREE.LineBasicMaterial({ color: edgeColor }) : edgeMat;
      mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo, threshold), em));
    }
    return mesh;
  }

  // Segment between two points in the vision frame. style: "solid" | "dash" | "dot".
  function line(a, b, color, { style = "solid", opacity = 1, vision = true } = {}) {
    const pa = vision ? cv(a) : a, pb = vision ? cv(b) : b;
    const geo = new THREE.BufferGeometry().setFromPoints([pa, pb]);
    let mat;
    if (style === "dash") {
      mat = new THREE.LineDashedMaterial({ color, dashSize: 0.09, gapSize: 0.06, transparent: true, opacity });
    } else if (style === "dot") {
      mat = new THREE.LineDashedMaterial({ color, dashSize: 0.02, gapSize: 0.06, transparent: true, opacity });
    } else {
      mat = new THREE.LineBasicMaterial({ color, transparent: true, opacity });
    }
    const l = new THREE.Line(geo, mat);
    if (style !== "solid") l.computeLineDistances();
    return l;
  }

  // Translucent triangle (e.g. an epipolar plane) from three vision-frame points.
  function sheet(pts, color, opacity = 0.14) {
    const geo = new THREE.BufferGeometry().setFromPoints(pts.map(cv));
    return new THREE.Mesh(
      geo,
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity, side: THREE.DoubleSide, depthWrite: false }),
    );
  }

  // Image-plane frustum at distance `depth`, in the camera's own vision frame.
  function frustum(intr, color, { depth = 0.55, opacity = 0.5 } = {}) {
    const { W, H } = intr;
    const corners = [[0, 0], [W, 0], [W, H], [0, H]].map(([u, v]) => backProject(u, v, depth, intr));
    const pts = [];
    corners.forEach((q, i) => {
      pts.push(cv([0, 0, 0]), cv(q), cv(q), cv(corners[(i + 1) % 4]));
    });
    return new THREE.LineSegments(
      new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({ color, transparent: true, opacity }),
    );
  }

  // Camera body with lens, accessory shoe and frustum. Origin = optical centre.
  function cameraBody(color, deep, intr, { frustumDepth = 0.55 } = {}) {
    const g = new THREE.Group();
    const body = solid(new THREE.BoxGeometry(0.34, 0.22, 0.2), color);
    body.position.z = 0.07;
    g.add(body);
    const lens = solid(new THREE.CylinderGeometry(0.075, 0.088, 0.15, 24).rotateX(Math.PI / 2), deep);
    lens.position.z = -0.1;
    g.add(lens);
    const shoe = solid(new THREE.BoxGeometry(0.11, 0.045, 0.09), deep);
    shoe.position.set(0.06, 0.13, 0.07);
    g.add(shoe);
    if (intr) g.add(frustum(intr, color, { depth: frustumDepth }));
    return g;
  }

  // Ground grid centred at (x, z) on the floor plane y.
  function floor({ y = -0.9, size = 9, divisions = 18, x = 1, z = -2.2 } = {}) {
    const grid = new THREE.GridHelper(size, divisions, P.grid, P.grid);
    grid.material.transparent = true;
    grid.material.opacity = P.dark ? 0.35 : 0.5;
    grid.position.set(x, y, z);
    return grid;
  }

  // Ball on a thin post with a foot, standing on the floor plane. pos: Three.js world vector.
  function marker(pos, color, { floorY = -0.9, radius = 0.09 } = {}) {
    const g = new THREE.Group();
    const ball = new THREE.Mesh(
      new THREE.SphereGeometry(radius, 24, 16),
      new THREE.MeshBasicMaterial({ color }),
    );
    ball.position.copy(pos);
    g.add(ball);
    if (pos.y > floorY + radius) {
      const h = pos.y - floorY - radius;
      const post = solid(new THREE.CylinderGeometry(0.014, 0.014, h, 8), P.gray, { threshold: 40 });
      post.position.set(pos.x, floorY + h / 2, pos.z);
      g.add(post);
      const foot = solid(new THREE.CylinderGeometry(0.09, 0.11, 0.035, 20), P.foot);
      foot.position.set(pos.x, floorY + 0.018, pos.z);
      g.add(foot);
    }
    return g;
  }

  // Bench: rail on two legs, scaled to a span along x. Call .setSpan(x0, x1) to move it.
  function bench({ railY = -0.4, floorY = -0.9 } = {}) {
    const g = new THREE.Group();
    const rail = solid(new THREE.BoxGeometry(1, 0.08, 0.32), P.bench);
    rail.position.y = railY;
    const legH = railY - 0.04 - floorY;
    const legA = solid(new THREE.BoxGeometry(0.08, legH, 0.26), P.bench);
    const legB = solid(new THREE.BoxGeometry(0.08, legH, 0.26), P.bench);
    legA.position.y = legB.position.y = floorY + legH / 2;
    g.add(rail, legA, legB);
    g.setSpan = (x0, x1, overhang = 0.5) => {
      rail.scale.x = x1 - x0 + 2 * overhang;
      rail.position.x = (x0 + x1) / 2;
      legA.position.x = x0 - overhang + 0.08;
      legB.position.x = x1 + overhang - 0.08;
    };
    return g;
  }

  // Carriage block that sits on the bench rail under a camera.
  function carriage({ railY = -0.4 } = {}) {
    const c = solid(new THREE.BoxGeometry(0.15, 0.25, 0.15), P.foot);
    c.position.y = railY + 0.165;
    return c;
  }

  // Small sphere drawn without shading (pierce points, landmarks).
  function point(pos, color, radius = 0.028) {
    const m = new THREE.Mesh(new THREE.SphereGeometry(radius, 12, 8), new THREE.MeshBasicMaterial({ color }));
    m.position.copy(pos);
    return m;
  }

  return { P, solid, line, sheet, frustum, cameraBody, floor, marker, bench, carriage, point };
}

// Isometric orthographic stage with drag-to-turn around the vertical axis.
export class Stage {
  constructor(host, { span = 2.25, azimuth = 0.62, elevation = ISO_ELEVATION, dragRate = 0.009 } = {}) {
    this.host = host;
    this.span = span;
    this.elevation = elevation;
    this.az = azimuth;
    this.goalAz = azimuth;
    this.target = new THREE.Vector3();
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(window.devicePixelRatio || 1);
    host.insertBefore(this.renderer.domElement, host.firstChild);
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 100);
    this.static = new THREE.Group();
    this.dyn = new THREE.Group();
    this.scene.add(this.static, this.dyn);

    let dragging = false, lastX = 0;
    host.addEventListener("pointerdown", (e) => {
      if (e.target !== this.renderer.domElement) return;
      dragging = true;
      lastX = e.clientX;
      host.setPointerCapture(e.pointerId);
      host.classList.add("is-dragging");
    });
    host.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      this.goalAz -= (e.clientX - lastX) * dragRate;
      lastX = e.clientX;
    });
    const end = () => {
      dragging = false;
      host.classList.remove("is-dragging");
    };
    host.addEventListener("pointerup", end);
    host.addEventListener("pointercancel", end);
  }

  resetStatic() {
    this.scene.remove(this.static);
    disposeTree(this.static);
    this.static = new THREE.Group();
    this.scene.add(this.static);
    return this.static;
  }

  resetDynamic() {
    this.scene.remove(this.dyn);
    disposeTree(this.dyn);
    this.dyn = new THREE.Group();
    this.scene.add(this.dyn);
    return this.dyn;
  }

  place() {
    const w = this.host.clientWidth, h = this.host.clientHeight;
    this.renderer.setSize(w, h, false);
    this.renderer.domElement.style.width = w + "px";
    this.renderer.domElement.style.height = h + "px";
    const s = this.span;
    Object.assign(this.camera, { left: (-s * w) / h, right: (s * w) / h, top: s, bottom: -s });
    this.camera.updateProjectionMatrix();
    const r = 14, el = this.elevation, t = this.target;
    this.camera.position.set(
      t.x + r * Math.cos(el) * Math.sin(this.az),
      t.y + r * Math.sin(el),
      t.z + r * Math.cos(el) * Math.cos(this.az),
    );
    this.camera.lookAt(t);
  }

  // Eases the azimuth toward the drag goal; returns true while turning.
  ease(rate = 0.16) {
    const d = this.goalAz - this.az;
    if (Math.abs(d) <= 1e-4) {
      this.az = this.goalAz;
      return false;
    }
    this.az += matchMedia("(prefers-reduced-motion: reduce)").matches ? d : d * rate;
    return true;
  }

  render() {
    this.place();
    this.renderer.render(this.scene, this.camera);
  }

  // Positions an HTML label over a world point.
  tag(el, world, dx = 0, dy = 0) {
    const p = world.clone().project(this.camera);
    el.style.left = ((p.x + 1) / 2) * this.host.clientWidth + dx + "px";
    el.style.top = ((1 - p.y) / 2) * this.host.clientHeight + dy + "px";
  }
}

// Eases `state` toward `goal` each frame and calls draw() while anything moves.
// `tick` is an optional extra easer (e.g. () => stage.ease()) that returns true while moving.
// Returns { invalidate() } to force a redraw after non-eased changes.
export function animate(state, goal, draw, { rate = 0.16, eps = 1e-4, tick = null } = {}) {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let dirty = true;
  function frame() {
    let moving = tick ? tick() : false;
    for (const k of Object.keys(goal)) {
      const d = goal[k] - state[k];
      if (Math.abs(d) > eps) {
        state[k] += reduce ? d : d * rate;
        moving = true;
      } else {
        state[k] = goal[k];
      }
    }
    if (moving || dirty) {
      dirty = false;
      draw();
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  addEventListener("resize", () => (dirty = true));
  return { invalidate: () => (dirty = true) };
}

// Clips the homogeneous line a*u + b*v + c = 0 to the image rectangle.
export function clipLine([a, b, c], W, H) {
  const p = [];
  if (Math.abs(b) > 1e-9) {
    for (const u of [0, W]) {
      const v = -(a * u + c) / b;
      if (v >= 0 && v <= H) p.push([u, v]);
    }
  }
  if (Math.abs(a) > 1e-9) {
    for (const v of [0, H]) {
      const u = -(b * v + c) / a;
      if (u >= 0 && u <= W) p.push([u, v]);
    }
  }
  return p.length >= 2 ? [p[0], p[p.length - 1]] : null;
}

export const inImage = (p, W, H) => !!p && p[0] >= 0 && p[0] <= W && p[1] >= 0 && p[1] <= H;

// Ground-glass image plate on a <canvas>. Coordinates are image pixels (W x H).
export function plate(canvas, W, H, P) {
  const g = canvas.getContext("2d");
  const s = canvas.width / W;
  const font = Math.round(11 * s) + "px ui-monospace, SF Mono, Menlo, Consolas, monospace";

  return {
    pick(e) {
      const r = canvas.getBoundingClientRect();
      return [
        Math.max(1, Math.min(W - 1, ((e.clientX - r.left) / r.width) * W)),
        Math.max(1, Math.min(H - 1, ((e.clientY - r.top) / r.height) * H)),
      ];
    },
    clear({ cx = W / 2, cy = H / 2 } = {}) {
      const cw = canvas.width, ch = canvas.height, m = 5 * s, k = 7 * s;
      g.clearRect(0, 0, cw, ch);
      g.strokeStyle = P.gray;
      g.lineWidth = s;
      g.globalAlpha = 0.6;
      for (const [x, y, sx, sy] of [[m, m, 1, 1], [cw - m, m, -1, 1], [m, ch - m, 1, -1], [cw - m, ch - m, -1, -1]]) {
        g.beginPath();
        g.moveTo(x + k * sx, y);
        g.lineTo(x, y);
        g.lineTo(x, y + k * sy);
        g.stroke();
      }
      g.globalAlpha = 0.35;
      g.lineWidth = 0.75 * s;
      g.beginPath();
      g.moveTo((cx - 4.5) * s, cy * s);
      g.lineTo((cx + 4.5) * s, cy * s);
      g.moveTo(cx * s, (cy - 4.5) * s);
      g.lineTo(cx * s, (cy + 4.5) * s);
      g.stroke();
      g.globalAlpha = 1;
      g.font = font;
    },
    crosshair([u, v], color, alpha = 0.35) {
      g.strokeStyle = color;
      g.globalAlpha = alpha;
      g.setLineDash([2 * s, 2.5 * s]);
      g.lineWidth = 0.75 * s;
      g.beginPath();
      g.moveTo(u * s, 0);
      g.lineTo(u * s, canvas.height);
      g.moveTo(0, v * s);
      g.lineTo(canvas.width, v * s);
      g.stroke();
      g.setLineDash([]);
      g.globalAlpha = 1;
    },
    mark([u, v], color, label, { ring = true, radius = 4 } = {}) {
      g.fillStyle = color;
      g.beginPath();
      g.arc(u * s, v * s, radius * s, 0, 7);
      g.fill();
      if (ring) {
        g.strokeStyle = P.edge;
        g.lineWidth = 0.75 * s;
        g.stroke();
      }
      if (label) {
        g.fillStyle = P.ink;
        g.fillText(label, (u + 6) * s, (v - 6) * s);
      }
    },
    ghost([u, v], label) {
      g.fillStyle = P.gray;
      g.beginPath();
      g.arc(u * s, v * s, 3 * s, 0, 7);
      g.fill();
      if (label) {
        g.fillStyle = P.muted;
        g.fillText(label, (u + 5) * s, (v + 12) * s);
      }
    },
    line(l, color, { dash = [6, 3.5], width = 1.5 } = {}) {
      const seg = clipLine(l, W, H);
      if (!seg) return false;
      g.strokeStyle = color;
      g.lineWidth = width * s;
      g.setLineDash(dash.map((d) => d * s));
      g.beginPath();
      g.moveTo(seg[0][0] * s, seg[0][1] * s);
      g.lineTo(seg[1][0] * s, seg[1][1] * s);
      g.stroke();
      g.setLineDash([]);
      return true;
    },
    note(text, color = P.muted) {
      g.fillStyle = color;
      g.fillText(text, 7 * s, canvas.height - 7 * s);
    },
  };
}

// Number formatting for readouts: true minus sign, fixed decimals, tiny values in exponent form.
export function fmt(v, d = 2) {
  if (v === null || v === undefined || Number.isNaN(v)) return "n/a";
  const a = Math.abs(v);
  const s = a !== 0 && a < 1e-3 ? a.toExponential(1) : a.toFixed(d);
  return (v < 0 ? "−" : "") + s;
}
