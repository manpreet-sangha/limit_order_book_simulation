"""
visualiser.py
─────────────
Real‑time matplotlib visualisation of the Limit Order Book.

Uses matplotlib.animation.FuncAnimation to redraw the market‑depth
bar chart on every tick.  The style mirrors the classic LOB diagram:

  • Orange bars  →  bid (buy) side, volume plotted **upward**
  • Blue   bars  →  ask (sell) side, volume plotted **downward**
  • Dashed annotation for best bid / best ask / mid‑price / spread
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import matplotlib
matplotlib.use("TkAgg")  # ensure interactive backend on all platforms

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

from src.order_book import BookSnapshot


# ── configuration ────────────────────────────────────────────────────────
@dataclass
class VisualiserConfig:
    fig_width: float = 14
    fig_height: float = 7
    max_levels: int = 12          # max price levels shown per side
    interval_ms: int = 80         # milliseconds between frames
    bid_colour: str = "#F5A623"   # orange
    ask_colour: str = "#4A90D9"   # blue
    mid_colour: str = "#2ECC71"   # green for mid‑price line
    bg_colour: str = "#FAFAFA"
    grid_alpha: float = 0.25
    title: str = "Limit Order Book – Market Depth"


# ── visualiser ───────────────────────────────────────────────────────────
class LOBVisualiser:
    """
    Draws and continuously updates the market‑depth chart.

    Usage
    -----
    >>> vis = LOBVisualiser(config)
    >>> vis.start(snapshot_generator)   # blocking – opens the window

    ``snapshot_generator`` must be a callable that returns the next
    ``BookSnapshot`` each time it is called (no arguments).
    """

    def __init__(self, config: Optional[VisualiserConfig] = None) -> None:
        self.cfg = config or VisualiserConfig()
        self._fig: Optional[plt.Figure] = None
        self._ax: Optional[plt.Axes] = None

    # ── public API ───────────────────────────────────────────────────
    def start(self, next_snapshot_fn) -> None:
        """
        Open the interactive window and begin the animation loop.

        Parameters
        ----------
        next_snapshot_fn : callable () -> BookSnapshot
            Called once per frame to obtain the latest book state.
        """
        self._next = next_snapshot_fn
        self._setup_figure()
        self._anim = animation.FuncAnimation(
            self._fig,
            self._update,
            interval=self.cfg.interval_ms,
            blit=False,
            cache_frame_data=False,
        )
        plt.show()

    # ── figure setup ─────────────────────────────────────────────────
    def _setup_figure(self) -> None:
        self._fig, self._ax = plt.subplots(
            figsize=(self.cfg.fig_width, self.cfg.fig_height))
        self._fig.patch.set_facecolor(self.cfg.bg_colour)
        self._ax.set_facecolor(self.cfg.bg_colour)
        self._fig.canvas.manager.set_window_title(self.cfg.title)

    # ── per‑frame draw ───────────────────────────────────────────────
    def _update(self, _frame_num: int) -> None:
        snap: BookSnapshot = self._next()
        ax = self._ax
        ax.clear()

        ml = self.cfg.max_levels

        # --- trim to max_levels ---
        bid_prices = snap.bid_prices[:ml]
        bid_vols = snap.bid_volumes[:ml]
        ask_prices = snap.ask_prices[:ml]
        ask_vols = snap.ask_volumes[:ml]

        # We plot bids with positive volume and asks with negative volume
        # so bids appear above the x‑axis and asks below – matching the
        # reference diagram.
        bar_width = self._bar_width(bid_prices, ask_prices)

        # ── bid bars (positive / upward) ─────────────────────────────
        if bid_prices:
            ax.bar(bid_prices, bid_vols,
                   width=bar_width, color=self.cfg.bid_colour,
                   edgecolor="darkorange", linewidth=0.8,
                   label="Bid (buy)", zorder=3)

        # ── ask bars (negative / downward) ───────────────────────────
        if ask_prices:
            ax.bar(ask_prices, [-v for v in ask_vols],
                   width=bar_width, color=self.cfg.ask_colour,
                   edgecolor="steelblue", linewidth=0.8,
                   label="Ask (sell)", zorder=3)

        # ── reference lines ──────────────────────────────────────────
        if snap.mid_price is not None:
            ax.axvline(snap.mid_price, color=self.cfg.mid_colour,
                       linestyle="--", linewidth=1.4, label="Mid‑price",
                       zorder=4)

        if snap.best_bid is not None:
            ax.axvline(snap.best_bid, color="darkorange",
                       linestyle=":", linewidth=1.0, alpha=0.7, zorder=4)
        if snap.best_ask is not None:
            ax.axvline(snap.best_ask, color="steelblue",
                       linestyle=":", linewidth=1.0, alpha=0.7, zorder=4)

        # ── spread shading ───────────────────────────────────────────
        if snap.best_bid is not None and snap.best_ask is not None:
            ax.axvspan(snap.best_bid, snap.best_ask,
                       alpha=0.08, color="grey", zorder=1)

        # ── annotations ──────────────────────────────────────────────
        self._annotate(ax, snap)

        # ── cosmetics ────────────────────────────────────────────────
        ax.set_xlabel("Price", fontsize=12, fontweight="bold")
        ax.set_ylabel("Volume Available", fontsize=12, fontweight="bold")
        ax.set_title(self.cfg.title, fontsize=14, fontweight="bold", pad=12)
        ax.axhline(0, color="black", linewidth=0.8, zorder=2)
        ax.grid(axis="y", alpha=self.cfg.grid_alpha, zorder=0)
        ax.legend(loc="upper left", fontsize=9, framealpha=0.85)
        self._fig.tight_layout()

    # ── helpers ──────────────────────────────────────────────────────
    @staticmethod
    def _bar_width(bid_prices, ask_prices) -> float:
        all_prices = list(bid_prices) + list(ask_prices)
        if len(all_prices) < 2:
            return 0.005
        diffs = np.diff(sorted(all_prices))
        diffs = diffs[diffs > 1e-9]
        if len(diffs) == 0:
            return 0.005
        return float(np.min(diffs)) * 0.85

    @staticmethod
    def _annotate(ax, snap: BookSnapshot) -> None:
        y_top = ax.get_ylim()[1] if ax.get_ylim()[1] != 0 else 1.0

        if snap.best_bid is not None:
            ax.annotate(f"Best Bid\n{snap.best_bid:.2f}",
                        xy=(snap.best_bid, 0),
                        xytext=(snap.best_bid, y_top * 0.70),
                        fontsize=8, ha="center", color="darkorange",
                        arrowprops=dict(arrowstyle="->",
                                        color="darkorange", lw=1.2))

        if snap.best_ask is not None:
            ax.annotate(f"Best Ask\n{snap.best_ask:.2f}",
                        xy=(snap.best_ask, 0),
                        xytext=(snap.best_ask, y_top * 0.85),
                        fontsize=8, ha="center", color="steelblue",
                        arrowprops=dict(arrowstyle="->",
                                        color="steelblue", lw=1.2))

        if snap.mid_price is not None:
            ax.annotate(f"Mid {snap.mid_price:.2f}",
                        xy=(snap.mid_price, 0),
                        xytext=(snap.mid_price, y_top * 0.55),
                        fontsize=8, ha="center", color=("#2ECC71"),
                        arrowprops=dict(arrowstyle="->",
                                        color="#2ECC71", lw=1.2))

        if snap.spread is not None and snap.best_bid is not None:
            mid_x = (snap.best_bid + snap.best_ask) / 2
            ax.text(mid_x, y_top * -0.90,
                    f"Spread: {snap.spread:.4f}",
                    fontsize=9, ha="center",
                    bbox=dict(boxstyle="round,pad=0.3",
                              fc="white", ec="grey", alpha=0.9))
