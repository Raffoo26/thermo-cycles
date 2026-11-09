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


def _isobar(p: float, h_from: float, h_to: float, fluid: str, n: int = 50):
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


def plot_hrsg(c, ax=None, title: str | None = None, n: int = 60):
    """Temperature–heat (T-Q) diagram of the heat recovery steam generator of a combined cycle.

    x axis: heat transferred per kg of air, from the stack (cold end) to the gas turbine exhaust."""
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 5))
    gas, steam, k = c.gas, c.steam, c.steam_per_air
    exhaust = gas.states["y"] if "y" in gas.states else gas.states["4"]

    h_g = np.linspace(c.stack.h, exhaust.h, n)
    T_g = np.array([PropsSI("T", "P", c.stack.p, "H", h, gas.fluid) for h in h_g])
    ax.plot((h_g - c.stack.h) / 1e3, T_g - KELVIN, "C3-", lw=2, label=f"Gas ({gas.fluid})")

    boiler = next(comp for comp in steam.components if comp.name == "Boiler")
    s_fw, s_out = boiler.inlets[0][0], boiler.outlets[0][0]
    T_w, _, h_w = _isobar(s_fw.p, s_fw.h, s_out.h, steam.fluid, n)
    ax.plot(k * (h_w - s_fw.h) / 1e3, T_w - KELVIN, "C0-", lw=2, label=f"Water / steam ({steam.fluid})")
    reheater = next((comp for comp in steam.components if comp.name == "Reheater"), None)
    if reheater is not None:
        s_in, s_rh = reheater.inlets[0][0], reheater.outlets[0][0]
        m = reheater.inlets[0][1]
        q0 = k * (s_out.h - s_fw.h)
        T_r, _, h_r = _isobar(s_in.p, s_in.h, s_rh.h, steam.fluid, n)
        ax.plot((q0 + k * m * (h_r - s_in.h)) / 1e3, T_r - KELVIN, "C0--", lw=2, label="Reheat")

    q_pinch = k * (PropsSI("H", "P", s_fw.p, "Q", 0, steam.fluid) - s_fw.h) / 1e3
    T_sat = PropsSI("T", "P", s_fw.p, "Q", 0, steam.fluid) - KELVIN
    ax.annotate("", xy=(q_pinch, T_sat), xytext=(q_pinch, c.T_gas_pinch - KELVIN),
                arrowprops=dict(arrowstyle="<->", color="k"))
    ax.annotate(f"pinch {c.pinch_K:.1f} K", (q_pinch, (T_sat + c.T_gas_pinch - KELVIN) / 2),
                xytext=(8, 0), textcoords="offset points", va="center", fontsize=10)
    ax.set_xlabel("Heat transferred [kJ per kg of air]")
    ax.set_ylabel("T [°C]")
    ax.set_title(title or f"HRSG T-Q diagram — stack {c.stack.T - KELVIN:.0f} °C")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left")
    return ax
