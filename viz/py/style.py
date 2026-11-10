"""Study figure style for Python: matplotlib, Plotly, marimo cards and viser scenes.

Same palette and rules as viz/web/figure.css and isokit.js:
  blue  = camera 1 / estimate / reference frame
  coral = camera 2 / measurement / second view
  teal  = the quantity being taught (ray, point, constraint)
  gray  = structure
  amber = warning / special case

Usage
-----
    from viz.py import style
    style.use("light")                 # matplotlib rcParams
    style.register_plotly()            # Plotly template "chalk"
    card = style.card(content, fig="Fig 2.2", title="EKF vs UKF", hint="Drag the noise slider")
    style.bundle("viz/web/examples/fig-3-4-stereo-rig.html")  # self-contained HTML for marimo
"""

from __future__ import annotations

import base64
import html as _html
import re
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

ROLE = {
    "blue": "#378ADD",
    "blue_deep": "#0C447C",
    "coral": "#D85A30",
    "coral_deep": "#712B13",
    "teal": "#1D9E75",
    "teal_deep": "#085041",
    "gray": "#888780",
    "amber": "#BA7517",
}

THEMES = {
    "light": {
        "surface": "#FFFFFF",
        "tile": "#F5F4EF",
        "ink": "#1F1E1D",
        "muted": "#5F5E5A",
        "faint": "#888780",
        "edge": "#2C2C2A",
        "grid": "#B4B2A9",
        "border": "#E1E0DA",
    },
    "dark": {
        "surface": "#262624",
        "tile": "#30302E",
        "ink": "#F5F4EF",
        "muted": "#B4B2A9",
        "faint": "#888780",
        "edge": "#D3D1C7",
        "grid": "#5F5E5A",
        "border": "#3D3D3A",
    },
}

CYCLE = [ROLE["blue"], ROLE["coral"], ROLE["teal"], ROLE["gray"], ROLE["amber"]]

MONO = ["SF Mono", "Menlo", "Consolas", "DejaVu Sans Mono", "monospace"]
SANS = ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans", "sans-serif"]


def palette(theme: str = "light") -> dict:
    """Theme colours merged with role colours."""
    return {**THEMES[theme], **ROLE}


# ---------------------------------------------------------------- matplotlib


def use(theme: str = "light") -> dict:
    """Apply the Chalk style to matplotlib and return the palette."""
    import matplotlib as mpl
    from cycler import cycler

    p = palette(theme)
    mpl.rcParams.update(
        {
            "figure.facecolor": p["surface"],
            "figure.edgecolor": p["surface"],
            "figure.dpi": 110,
            "savefig.facecolor": p["surface"],
            "savefig.bbox": "tight",
            "savefig.format": "svg",
            "svg.fonttype": "none",
            "axes.facecolor": p["surface"],
            "axes.edgecolor": p["grid"],
            "axes.linewidth": 0.8,
            "axes.labelcolor": p["muted"],
            "axes.labelsize": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "medium",
            "axes.titlecolor": p["ink"],
            "axes.titlelocation": "left",
            "axes.titlepad": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "axes.prop_cycle": cycler(color=CYCLE),
            "grid.color": p["grid"],
            "grid.alpha": 0.35,
            "grid.linewidth": 0.6,
            "xtick.color": p["faint"],
            "ytick.color": p["faint"],
            "xtick.labelcolor": p["muted"],
            "ytick.labelcolor": p["muted"],
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "xtick.major.size": 3,
            "ytick.major.size": 3,
            "font.family": "sans-serif",
            "font.sans-serif": SANS,
            "font.monospace": MONO,
            "font.size": 10,
            "text.color": p["ink"],
            "legend.frameon": False,
            "legend.fontsize": 9,
            "legend.labelcolor": p["muted"],
            "lines.linewidth": 1.6,
            "lines.markersize": 5,
            "patch.edgecolor": p["edge"],
            "patch.linewidth": 0.8,
            "image.cmap": "cividis",
            "mathtext.fontset": "cm",
        }
    )
    return p


def fig_label(ax, number: str, title: str, theme: str = "light") -> None:
    """Card-style heading: small mono figure number above a medium-weight title."""
    p = palette(theme)
    ax.set_title("")
    ax.text(0, 1.12, number, transform=ax.transAxes, fontsize=8.5, color=p["faint"],
            family="monospace", va="bottom")
    ax.text(0, 1.04, title, transform=ax.transAxes, fontsize=12, color=p["ink"],
            weight="medium", va="bottom")


def cov_ellipse(ax, mean, cov, n_std: float = 2.0, role: str = "blue", fill_alpha: float = 0.15, **kw):
    """Covariance ellipse: role-coloured outline over a translucent fill of the same colour."""
    import numpy as np
    from matplotlib.patches import Ellipse

    cov = np.asarray(cov, dtype=float)[:2, :2]
    vals, vecs = np.linalg.eigh(cov)
    vals = np.clip(vals, 0.0, None)
    angle = np.degrees(np.arctan2(vecs[1, 1], vecs[0, 1]))
    w, h = 2 * n_std * np.sqrt(vals[::-1])
    col = ROLE[role]
    e = Ellipse(mean, w, h, angle=angle, facecolor=col, alpha=fill_alpha, edgecolor="none")
    o = Ellipse(mean, w, h, angle=angle, facecolor="none", edgecolor=col, linewidth=1.4, **kw)
    ax.add_patch(e)
    ax.add_patch(o)
    return o


def draw_frame(ax, T, length: float = 0.3, label: str | None = None, theme: str = "light"):
    """2-D or 3-D frame axes (x coral, y teal, z blue) from a homogeneous transform T."""
    import numpy as np

    T = np.asarray(T, dtype=float)
    dim = T.shape[0] - 1
    o = T[:dim, dim]
    cols = [ROLE["coral"], ROLE["teal"], ROLE["blue"]]
    for i in range(dim):
        d = T[:dim, i] * length
        if dim == 2:
            ax.plot([o[0], o[0] + d[0]], [o[1], o[1] + d[1]], color=cols[i], lw=1.6)
        else:
            ax.plot([o[0], o[0] + d[0]], [o[1], o[1] + d[1]], [o[2], o[2] + d[2]], color=cols[i], lw=1.6)
    if label:
        p = palette(theme)
        if dim == 2:
            ax.text(o[0], o[1], " " + label, color=p["muted"], fontsize=9)
        else:
            ax.text(o[0], o[1], o[2], " " + label, color=p["muted"], fontsize=9)


# ---------------------------------------------------------------- Plotly


def plotly_template(theme: str = "light"):
    """Plotly template with the Chalk palette."""
    import plotly.graph_objects as go

    p = palette(theme)
    axis = dict(
        gridcolor=_rgba(p["grid"], 0.35),
        zerolinecolor=_rgba(p["grid"], 0.6),
        linecolor=p["grid"],
        tickfont=dict(color=p["muted"], size=11),
        title=dict(font=dict(color=p["muted"], size=12)),
    )
    scene_axis = dict(
        backgroundcolor=p["surface"],
        gridcolor=_rgba(p["grid"], 0.45),
        zerolinecolor=_rgba(p["grid"], 0.7),
        showbackground=False,
        tickfont=dict(color=p["muted"], size=10),
        title=dict(font=dict(color=p["muted"], size=11)),
    )
    return go.layout.Template(
        layout=dict(
            font=dict(family=", ".join(SANS), color=p["ink"], size=12),
            paper_bgcolor=p["surface"],
            plot_bgcolor=p["surface"],
            colorway=CYCLE,
            title=dict(x=0, xanchor="left", font=dict(size=15, color=p["ink"])),
            margin=dict(l=48, r=16, t=48, b=40),
            xaxis=axis,
            yaxis=axis,
            legend=dict(font=dict(color=p["muted"], size=11), bgcolor="rgba(0,0,0,0)"),
            hoverlabel=dict(font=dict(family=", ".join(MONO), size=11), bgcolor=p["tile"],
                            bordercolor=p["border"]),
            scene=dict(
                xaxis=scene_axis,
                yaxis=scene_axis,
                zaxis=scene_axis,
                camera=dict(projection=dict(type="orthographic"), eye=dict(x=1.25, y=1.25, z=1.0)),
            ),
            sliders=[dict(font=dict(color=p["muted"]), activebgcolor=ROLE["teal"])],
        )
    )


def register_plotly(theme: str = "light", name: str = "chalk") -> str:
    """Register the template under `name` and make it the default."""
    import plotly.io as pio

    pio.templates[name] = plotly_template(theme)
    pio.templates.default = name
    return name


# ---------------------------------------------------------------- marimo


def card(content, fig: str, title: str, hint: str | None = None, chip: str | None = None,
         chip_state: str = "ok", tiles: dict | None = None):
    """Wrap marimo content (a plot, widget or Html) in the Chalk figure card.

    tiles: {"label": "value"} readouts shown under the content.
    """
    import marimo as mo

    css = _figure_css()
    head = [
        '<div class="fig-head"><div>',
        f'<div class="fig-num">{_html.escape(fig)}</div>',
        f'<div class="fig-title">{_html.escape(title)}</div>',
        "</div>",
    ]
    if chip:
        head.append(f'<div class="fig-chip" data-state="{chip_state}">{_html.escape(chip)}</div>')
    head.append("</div>")
    if hint:
        head.append(f'<div class="fig-hint">{_html.escape(hint)}</div>')
    tile_html = ""
    if tiles:
        cells = "".join(
            f'<div class="fig-tile"><div class="k">{_html.escape(k)}</div>'
            f'<div class="v">{_html.escape(str(v))}</div></div>'
            for k, v in tiles.items()
        )
        tile_html = f'<div class="fig-tiles">{cells}</div>'
    top = mo.Html(f"<style>{css}</style>" + "".join(head))
    parts = [top, content]
    if tile_html:
        parts.append(mo.Html(tile_html))
    return mo.Html(f'<div class="fig-card">{mo.vstack(parts, gap=0.5).text}</div>')


def bundle(page: str | Path) -> str:
    """Return a self-contained copy of a viz/web page: figure.css and isokit.js are inlined.

    'three' stays on the CDN. Use in marimo with mo.iframe(style.bundle(path), height="760px").
    """
    page = Path(page)
    src = page.read_text(encoding="utf-8")
    css = _figure_css()
    src = re.sub(r'<link[^>]+href="[^"]*figure\.css"[^>]*>', f"<style>{css}</style>", src)
    js = (WEB_DIR / "isokit.js").read_text(encoding="utf-8")
    data_url = "data:text/javascript;base64," + base64.b64encode(js.encode("utf-8")).decode("ascii")
    src = re.sub(r'"isokit"\s*:\s*"[^"]*"', f'"isokit": "{data_url}"', src)
    return src


def _figure_css() -> str:
    return (WEB_DIR / "figure.css").read_text(encoding="utf-8")


# ---------------------------------------------------------------- viser


def viser_theme(server, theme: str = "light") -> None:
    """Match a viser server's UI to the Chalk palette."""
    dark = theme == "dark"
    kwargs = dict(dark_mode=dark, brand_color=_rgb(ROLE["teal"]), show_logo=False)
    try:
        server.gui.configure_theme(**kwargs)
    except TypeError:
        server.gui.configure_theme(dark_mode=dark)
    try:
        server.scene.set_up_direction("+y")
    except AttributeError:
        pass


def iso_view(client, target=(0.0, 0.0, 0.0), distance: float = 6.0, azimuth_deg: float = 35.0) -> None:
    """Point a viser client's camera at `target` from the isometric elevation (35.26 deg), y up."""
    import math

    el = math.atan(1 / math.sqrt(2))
    az = math.radians(azimuth_deg)
    tx, ty, tz = target
    client.camera.position = (
        tx + distance * math.cos(el) * math.sin(az),
        ty + distance * math.sin(el),
        tz + distance * math.cos(el) * math.cos(az),
    )
    client.camera.look_at = target
    client.camera.up_direction = (0.0, 1.0, 0.0)


def role_rgb(role: str) -> tuple[int, int, int]:
    """Role colour as an RGB tuple (viser, Rerun and Open3D take tuples)."""
    return _rgb(ROLE[role])


# ---------------------------------------------------------------- helpers


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _rgba(hex_color: str, alpha: float) -> str:
    r, g, b = _rgb(hex_color)
    return f"rgba({r},{g},{b},{alpha})"
