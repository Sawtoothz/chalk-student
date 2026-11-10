# viz: Chalk figure style

One look for every interactive session and figure in the Chalk repo. The reference is
`web/examples/fig-3-4-stereo-rig.html` (Fig 3.4, two-camera epipolar geometry).

```
viz/
  web/
    figure.css                       card, stage, plates, tiles, chip, legend; light and dark tokens
    isokit.js                        Three.js kit: isometric stage, toned solids, rig parts, plates, easing
    examples/
      fig-3-4-stereo-rig.html        reference figure built only from the kit
  py/
    style.py                         matplotlib, Plotly, marimo card, page bundler, viser theme
```

## Rules

Every figure `/teach` produces follows these. A figure that breaks one is sent back.

### Card

- Rounded card (12 px radius, 0.5 px border), never full-bleed.
- Header: mono figure number and topic (`Fig 3.4 · epipolar geometry`), then a medium-weight title.
  The figure number is the lesson number; a lesson with several figures uses `Fig 3.4b`, `Fig 3.4c`.
- Status chip on the right: `ok` (green) while the concept holds, `warn` (amber) at a special case
  (degenerate configuration, point behind a camera, filter divergence), `bad` (red) only for errors.
- One hint line under the header that names the interactions, joined with `·`.

### Stage

- Orthographic camera at the true isometric elevation, 35.26°. Dragging turns the scene about the
  vertical axis only. No free orbit, no zoom.
- Concepts are physical objects: cameras with lenses on carriages, a bench with legs, targets on posts,
  a floor grid. Build them from `makeKit(P)`, never ad hoc meshes.
- Solids are flat four-tone shaded from one fixed light with dark outlines (`kit.solid`).
- Labels are HTML tags that track their objects (`stage.tag`), 11 px, muted; the taught object's label
  is strong.

### Colour carries meaning

| Role | Colour | Use |
| --- | --- | --- |
| blue | `#378ADD` | camera 1, estimate, reference frame |
| coral | `#D85A30` | camera 2, measurement, second view |
| teal | `#1D9E75` | the quantity being taught: ray, point, constraint, plane |
| gray | `#888780` | structure: bench, posts, baselines, epipoles |
| amber | `#BA7517` | warnings and special cases |

The same role keeps the same colour in every track: in Track 2 the estimate is blue and the
measurement coral; in Track 7 the predicted horizon is blue and the executed trajectory coral.
Frames draw x coral, y teal, z blue.

### Plates and plots

- 2-D image views are ground-glass plates (`plate()`): registration marks, principal-point cross,
  marks with dark rings, dashed lines for constraints.
- Static plots use `style.use()`; interactive plots use the Plotly template `chalk`.
  Same palette, left-aligned titles, no top or right spines, light grid.

### Readouts

- Every number comes from the same model that moves the parts. No hard-coded numbers.
- Each figure shows one residual or invariant that proves the concept
  (x₂ᵀFx₁ = 0, NEES inside its bounds, KKT residual, Bellman error).
- Mono, tabular numerals, true minus sign, units on every value (`fmt()`).

### Motion

- Sliders and drags ease toward their target (`animate`, `stage.ease`); nothing jumps.
- Under `prefers-reduced-motion` everything snaps.

## Using it

Standalone page (served from the repo, e.g. `python -m http.server`):

```html
<link rel="stylesheet" href="../figure.css">
<script type="importmap">
{"imports": {"three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
             "isokit": "../isokit.js"}}
</script>
```

In marimo:

```python
from viz.py import style
style.use("light")
style.register_plotly()

mo.iframe(style.bundle("viz/web/examples/fig-3-4-stereo-rig.html"), height="900px")
style.card(fig_plotly, fig="Fig 2.2", title="EKF vs UKF on one nonlinearity",
           hint="Drag the noise slider", chip="consistent", tiles={"NEES": "2.8"})
```

`bundle()` inlines `figure.css` and `isokit.js` so the page runs inside an iframe; Three.js still loads
from the CDN.

In viser:

```python
style.viser_theme(server, "light")

@server.on_client_connect
def _(client):
    style.iso_view(client, target=(0.5, -0.3, 1.6), distance=7)
```

viser renders in perspective; `iso_view` matches the isometric elevation and azimuth.

## Checks before a figure ships

1. Open it in light and dark; every label and line is readable in both.
2. Drag to both rotation extremes; no label overlaps another or leaves the stage.
3. Push every slider to both ends; the chip changes state at the special case and back.
4. The residual readout stays at zero (or its bound) across the whole slider range.
5. Turn on reduced motion; nothing animates.
