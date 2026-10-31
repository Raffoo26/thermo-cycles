"""T-s and p-h diagrams with the saturation dome and the cycle processes."""

import matplotlib.pyplot as plt
import numpy as np
from CoolProp.CoolProp import PropsSI

from .rankine import BAR, KELVIN, RankineResults


def saturation_dome(fluid: str, n: int = 200):
    """Return (T, s_liquid, s_vapour, p, h_liquid, h_vapour) along the saturation curve."""
    T_triple = PropsSI("Ttriple", fluid)
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


def plot_Ts(r: RankineResults, ax=None, title: str | None = None):
    st, f = r.states, r.fluid
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 6))

    T, s_l, s_v, *_ = saturation_dome(f)
    # liquid + vapour (reversed) as one line, so the dome closes at the critical point
    ax.plot(np.concatenate([s_l, s_v[::-1]]) / 1e3,
            np.concatenate([T, T[::-1]]) - KELVIN, "k-", lw=1, label="Saturation curve")

    # 1-2 pump and 3-4 turbine: straight segments (intermediate states undefined for real processes)
    for a, b in (("1", "2"), ("3", "4")):
        ax.plot([st[a].s / 1e3, st[b].s / 1e3], [st[a].T - KELVIN, st[b].T - KELVIN], "C0-", lw=2)
    # 2-3 boiler and 4-1 condenser: real isobars
    for a, b in (("2", "3"), ("4", "1")):
        Ti, si, _ = _isobar(st[a].p, st[a].h, st[b].h, f)
        ax.plot(si / 1e3, Ti - KELVIN, "C0-", lw=2)

    for name, pt in st.items():
        ax.plot(pt.s / 1e3, pt.T - KELVIN, "o", color="C3")
        ax.annotate(name, (pt.s / 1e3, pt.T - KELVIN), textcoords="offset points",
                    xytext=(6, 4), fontsize=11, fontweight="bold")

    ax.set_xlabel("s [kJ/(kg·K)]")
    ax.set_ylabel("T [°C]")
    ax.set_title(title or f"Rankine cycle — {f} — η = {r.efficiency * 100:.1f} %")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left")
    return ax


def plot_ph(r: RankineResults, ax=None, title: str | None = None):
    st, f = r.states, r.fluid
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 6))

    _, _, _, p, h_l, h_v = saturation_dome(f)
    ax.plot(np.concatenate([h_l, h_v[::-1]]) / 1e3,
            np.concatenate([p, p[::-1]]) / BAR, "k-", lw=1, label="Saturation curve")

    order = ["1", "2", "3", "4", "1"]
    for a, b in zip(order, order[1:]):
        ax.plot([st[a].h / 1e3, st[b].h / 1e3], [st[a].p / BAR, st[b].p / BAR], "C0-", lw=2)
    for name, pt in st.items():
        ax.plot(pt.h / 1e3, pt.p / BAR, "o", color="C3")
        ax.annotate(name, (pt.h / 1e3, pt.p / BAR), textcoords="offset points",
                    xytext=(6, 4), fontsize=11, fontweight="bold")

    ax.set_yscale("log")
    ax.set_xlabel("h [kJ/kg]")
    ax.set_ylabel("p [bar]")
    ax.set_title(title or f"Rankine cycle — {f} — p-h diagram")
    ax.grid(alpha=0.3, which="both")
    ax.legend(loc="upper left")
    return ax
