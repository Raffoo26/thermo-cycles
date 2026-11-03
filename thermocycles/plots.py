"""T-s and p-h diagrams for any cycle of the package, plus an exergy bar chart.

Each cycle result lists its processes in r.paths as (from_state, to_state, kind):
    "isobar"   -> constant-pressure heat exchange, drawn along the real path
    "line"     -> compression / expansion, drawn as a straight segment
    "throttle" -> throttling (irreversible), drawn dashed
"""

from functools import lru_cache

import matplotlib.pyplot as plt
import numpy as np
from CoolProp.CoolProp import PropsSI

from .core import BAR, KELVIN


@lru_cache(maxsize=32)
def saturation_dome(fluid: str, n: int = 200):
    """Return (T, s_liquid, s_vapour, p, h_liquid, h_vapour) along the saturation curve."""
    T_triple = max(PropsSI("Ttriple", fluid), PropsSI("Tmin", fluid))
    T_crit = PropsSI("Tcrit", fluid)
    T = np.linspace(T_triple + 0.5, T_crit - 0.05, n)
    s_l = np.array([PropsSI("S", "T", t, "Q", 0, fluid) for t in T])
    s_v = np.array([PropsSI("S", "T", t, "Q", 1, fluid) for t in T])
    p = np.array([PropsSI("P", "T", t, "Q", 0, fluid) for t in T])
    h_l = np.array([PropsSI("H", "T", t, "Q", 0, fluid) for t in T])
    h_v = np.array([PropsSI("H", "T", t, "Q", 1, fluid) for t in T])
    return T, s_l, s_v, p, h_l, h_v


def _isobar(p: float, h_from: float, h_to: float, fluid: str, n: int = 100):
    """(T, s, h) points along an isobar between two enthalpies; follows the real path inside the dome too."""
    h = np.linspace(h_from, h_to, n)
    T = np.array([PropsSI("T", "P", p, "H", hh, fluid) for hh in h])
    s = np.array([PropsSI("S", "P", p, "H", hh, fluid) for hh in h])
    return T, s, h


def _title(r, diagram: str) -> str:
    return f"{r.name} — {r.fluid} — {r.headline or diagram}"


def _finish(ax, r, title, xlabel, ylabel, default):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title or default)
    ax.grid(alpha=0.3, which="both")
    if ax.get_legend_handles_labels()[0]:
        ax.legend(loc="upper left")
    return ax


def _mark_points(ax, pts, log_y: bool = False):
    """Mark the state points; labels of points that almost coincide are spread apart."""
    if not pts:
        return
    xs = np.array([x for x, _ in pts.values()])
    ys = np.array([np.log10(y) if log_y else y for _, y in pts.values()])
    span_x = (xs.max() - xs.min()) or 1.0
    span_y = (ys.max() - ys.min()) or 1.0
    offsets = [(6, 4), (6, -14), (-16, 4), (-16, -14)]
    placed = []
    for (name, (x, y)), yy in zip(pts.items(), ys):
        crowd = sum(1 for px, py in placed
                    if abs(px - x) / span_x < 0.03 and abs(py - yy) / span_y < 0.03)
        placed.append((x, yy))
        ax.plot(x, y, "o", color="C3")
        ax.annotate(name, (x, y), textcoords="offset points", xytext=offsets[crowd % len(offsets)],
                    fontsize=11, fontweight="bold")


def plot_Ts(r, ax=None, title: str | None = None):
    """T-s diagram of any cycle result."""
    st, f = r.states, r.fluid
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 6))

    if r.show_dome:
        T, s_l, s_v, *_ = saturation_dome(f)
        ax.plot(np.concatenate([s_l, s_v[::-1]]) / 1e3,
                np.concatenate([T, T[::-1]]) - KELVIN, "k-", lw=1, label="Saturation curve")

    throttle_label = "Throttling (irreversible)"
    for a, b, kind in r.paths:
        if kind == "isobar":
            Ti, si, _ = _isobar(st[a].p, st[a].h, st[b].h, f)
            ax.plot(si / 1e3, Ti - KELVIN, "C0-", lw=2)
        else:
            style = "C0--" if kind == "throttle" else "C0-"
            label = throttle_label if kind == "throttle" else None
            ax.plot([st[a].s / 1e3, st[b].s / 1e3], [st[a].T - KELVIN, st[b].T - KELVIN],
                    style, lw=2, label=label)

    _mark_points(ax, {n: (p.s / 1e3, p.T - KELVIN) for n, p in st.items()})
    return _finish(ax, r, title, "s [kJ/(kg·K)]", "T [°C]", _title(r, "T-s diagram"))


def plot_ph(r, ax=None, title: str | None = None):
    """p-h diagram (logarithmic pressure axis) of any cycle result."""
    st, f = r.states, r.fluid
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 6))

    if r.show_dome:
        _, _, _, p, h_l, h_v = saturation_dome(f)
        ax.plot(np.concatenate([h_l, h_v[::-1]]) / 1e3,
                np.concatenate([p, p[::-1]]) / BAR, "k-", lw=1, label="Saturation curve")

    for a, b, kind in r.paths:
        style = "C0--" if kind == "throttle" else "C0-"
        label = "Throttling (irreversible)" if kind == "throttle" else None
        ax.plot([st[a].h / 1e3, st[b].h / 1e3], [st[a].p / BAR, st[b].p / BAR], style, lw=2, label=label)

    _mark_points(ax, {n: (pt.h / 1e3, pt.p / BAR) for n, pt in st.items()}, log_y=True)
    ax.set_yscale("log")
    return _finish(ax, r, title, "h [kJ/kg]", "p [bar]", f"{r.name} — {r.fluid} — p-h diagram")


def plot_exergy(ex, ax=None, title: str | None = None):
    """Horizontal bar chart of the exergy destroyed in each component."""
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 4.5))
    rows = ex.table()[::-1]
    names = [r["Component"] for r in rows]
    values = [r["Exergy destroyed [kJ/kg]"] for r in rows]
    bars = ax.barh(names, values, color="C3")
    for bar, row in zip(bars, rows):
        ax.annotate(f"{row['Share of fuel [%]']:.1f} %", (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                    xytext=(4, 0), textcoords="offset points", va="center", fontsize=9)
    ax.set_xlabel("Exergy destroyed [kJ/kg]  (labels: % of fuel exergy)")
    ax.set_title(title or f"Exergy destruction — second-law efficiency {ex.efficiency * 100:.1f} %")
    ax.grid(alpha=0.3, axis="x")
    ax.margins(x=0.15)
    return ax


# Backwards-compatible names
plot_refrigeration_Ts = plot_Ts
plot_refrigeration_ph = plot_ph
