"""
visualiser.py
─────────────
Real‑time matplotlib visualisation of the Limit Order Book.

Two‑panel layout:
  LEFT  — Live order book table (bid / ask levels) + execution statistics
  RIGHT — Animated market‑depth bar chart

Uses matplotlib.animation.FuncAnimation to redraw every tick.

  • Orange bars  →  bid (buy) side, volume plotted **upward**
  • Blue   bars  →  ask (sell) side, volume plotted **downward**
  • Dashed annotation for best bid / best ask / mid‑price / spread
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import matplotlib
# Try interactive backends in order of preference
for _backend in ("TkAgg", "Qt5Agg", "WXAgg", "GTK3Agg"):
    try:
        matplotlib.use(_backend)
        break
    except ImportError:
        continue

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
import numpy as np

from src.order_book import BookSnapshot, OrderType, Side


# ── configuration ────────────────────────────────────────────────────────
@dataclass
class VisualiserConfig:
    fig_width: float = 18
    fig_height: float = 8
    max_levels: int = 12          # max price levels shown per side
    table_levels: int = 10        # rows in the LOB table per side
    interval_ms: int = 80         # milliseconds between frames
    bid_colour: str = "#F5A623"   # orange
    ask_colour: str = "#4A90D9"   # blue
    mid_colour: str = "#2ECC71"   # green for mid‑price line
    bg_colour: str = "#FAFAFA"
    grid_alpha: float = 0.25
    title: str = "Limit Order Book – Real‑Time Market Depth"


# ── visualiser ───────────────────────────────────────────────────────────
class LOBVisualiser:
    """
    Draws and continuously updates a two‑panel display:
      • Left panel:  order‑book table + execution statistics
      • Right panel: market‑depth bar chart

    Usage
    -----
    >>> vis = LOBVisualiser(config)
    >>> vis.start(snapshot_generator)   # blocking – opens the window
    """

    def __init__(self, config: Optional[VisualiserConfig] = None) -> None:
        self.cfg = config or VisualiserConfig()
        self._fig: Optional[plt.Figure] = None
        self._ax_table: Optional[plt.Axes] = None
        self._ax_chart: Optional[plt.Axes] = None

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

    def save_gif(self, next_snapshot_fn, filepath: str = "lob_simulation.gif",
                 duration_s: float = 15.0, fps: int = 12) -> None:
        """
        Capture the first *duration_s* seconds of the simulation to a GIF.

        Parameters
        ----------
        next_snapshot_fn : callable () -> BookSnapshot
        filepath : str   – output GIF path
        duration_s : float – length in seconds
        fps : int – frames per second in the saved GIF
        """
        self._next = next_snapshot_fn
        self._setup_figure()

        n_frames = int(duration_s * fps)
        interval = 1000 // fps  # ms between frames for saving

        print(f"Recording {n_frames} frames ({duration_s}s @ {fps} fps) …")

        anim = animation.FuncAnimation(
            self._fig,
            self._update,
            frames=n_frames,
            interval=interval,
            blit=False,
            cache_frame_data=False,
            repeat=False,
        )
        anim.save(filepath, writer="pillow", fps=fps,
                  savefig_kwargs={"facecolor": self.cfg.bg_colour})
        plt.close(self._fig)
        print(f"✅  GIF saved → {filepath}")

    # ── figure setup ─────────────────────────────────────────────────
    def _setup_figure(self) -> None:
        self._fig = plt.figure(
            figsize=(self.cfg.fig_width, self.cfg.fig_height))
        self._fig.patch.set_facecolor(self.cfg.bg_colour)
        try:
            self._fig.canvas.manager.set_window_title(self.cfg.title)
        except (AttributeError, TypeError):
            pass  # headless / non‑interactive backend

        # Grid: left 35% for table/stats, right 65% for chart
        gs = gridspec.GridSpec(1, 2, width_ratios=[35, 65],
                               wspace=0.05, left=0.02, right=0.98,
                               top=0.92, bottom=0.08)
        self._ax_table = self._fig.add_subplot(gs[0, 0])
        self._ax_chart = self._fig.add_subplot(gs[0, 1])

    # ── per‑frame draw ───────────────────────────────────────────────
    def _update(self, _frame_num: int) -> None:
        snap: BookSnapshot = self._next()
        self._draw_table_panel(snap)
        self._draw_chart_panel(snap)

    # ══════════════════════════════════════════════════════════════════
    #  LEFT PANEL — Order Book Table + Stats
    # ══════════════════════════════════════════════════════════════════
    def _draw_table_panel(self, snap: BookSnapshot) -> None:
        ax = self._ax_table
        ax.clear()
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        tl = self.cfg.table_levels
        bid_p = snap.bid_prices[:tl]
        bid_v = snap.bid_volumes[:tl]
        ask_p = snap.ask_prices[:tl]
        ask_v = snap.ask_volumes[:tl]

        # ── Title ────────────────────────────────────────────────────
        ax.text(0.50, 0.97, "ORDER BOOK",
                fontsize=13, fontweight="bold", ha="center", va="top",
                fontfamily="monospace",
                color="#333333")

        # ── Column headers ───────────────────────────────────────────
        header_y = 0.93
        ax.text(0.05, header_y, "Vol", fontsize=8, fontweight="bold",
                ha="center", va="top", color=self.cfg.bid_colour,
                fontfamily="monospace")
        ax.text(0.25, header_y, "Bid Price", fontsize=8, fontweight="bold",
                ha="center", va="top", color=self.cfg.bid_colour,
                fontfamily="monospace")
        ax.text(0.50, header_y, "│", fontsize=8, ha="center", va="top",
                color="#AAAAAA", fontfamily="monospace")
        ax.text(0.70, header_y, "Ask Price", fontsize=8, fontweight="bold",
                ha="center", va="top", color=self.cfg.ask_colour,
                fontfamily="monospace")
        ax.text(0.92, header_y, "Vol", fontsize=8, fontweight="bold",
                ha="center", va="top", color=self.cfg.ask_colour,
                fontfamily="monospace")

        # Separator line
        ax.plot([0.01, 0.99], [header_y - 0.015, header_y - 0.015],
                color="#CCCCCC", linewidth=0.8, clip_on=False)

        # ── Table rows ───────────────────────────────────────────────
        row_start = header_y - 0.035
        row_h = 0.032
        max_rows = max(len(bid_p), len(ask_p), 1)

        # Compute max volumes for bar scaling
        max_bid_vol = max(bid_v) if bid_v else 1
        max_ask_vol = max(ask_v) if ask_v else 1

        for i in range(max_rows):
            y = row_start - i * row_h
            if y < 0.32:
                break

            # Bid side (left)
            if i < len(bid_p):
                # Volume bar background
                bar_w = 0.18 * (bid_v[i] / max_bid_vol) if max_bid_vol else 0
                ax.barh(y, bar_w, height=row_h * 0.7, left=0.01,
                        color=self.cfg.bid_colour, alpha=0.20, zorder=1)
                ax.text(0.05, y, f"{bid_v[i]:>5.0f}",
                        fontsize=7.5, ha="center", va="center",
                        fontfamily="monospace", color="#8B6914", zorder=2)
                # Highlight best bid
                weight = "bold" if i == 0 else "normal"
                ax.text(0.25, y, f"{bid_p[i]:.4f}",
                        fontsize=7.5, ha="center", va="center",
                        fontfamily="monospace", fontweight=weight,
                        color=self.cfg.bid_colour, zorder=2)

            # Divider
            ax.text(0.50, y, "│", fontsize=7, ha="center", va="center",
                    color="#DDDDDD", fontfamily="monospace")

            # Ask side (right)
            if i < len(ask_p):
                bar_w = 0.18 * (ask_v[i] / max_ask_vol) if max_ask_vol else 0
                ax.barh(y, bar_w, height=row_h * 0.7,
                        left=0.99 - bar_w,
                        color=self.cfg.ask_colour, alpha=0.20, zorder=1)
                weight = "bold" if i == 0 else "normal"
                ax.text(0.70, y, f"{ask_p[i]:.4f}",
                        fontsize=7.5, ha="center", va="center",
                        fontfamily="monospace", fontweight=weight,
                        color=self.cfg.ask_colour, zorder=2)
                ax.text(0.92, y, f"{ask_v[i]:>5.0f}",
                        fontsize=7.5, ha="center", va="center",
                        fontfamily="monospace", color="#3B6A9C", zorder=2)

        # ── Spread banner ────────────────────────────────────────────
        spread_y = 0.30
        ax.plot([0.01, 0.99], [spread_y + 0.01, spread_y + 0.01],
                color="#CCCCCC", linewidth=0.8, clip_on=False)

        spread_txt = f"Spread: {snap.spread:.4f}" if snap.spread else "Spread: —"
        mid_txt = f"Mid: {snap.mid_price:.4f}" if snap.mid_price else "Mid: —"
        ax.text(0.50, spread_y - 0.01, f"{mid_txt}    {spread_txt}",
                fontsize=9, ha="center", va="top",
                fontfamily="monospace", fontweight="bold",
                color=self.cfg.mid_colour,
                bbox=dict(boxstyle="round,pad=0.3",
                          fc="#E8F8F0", ec=self.cfg.mid_colour, alpha=0.9))

        # ── Execution Statistics ─────────────────────────────────────
        stats = snap.stats
        if stats is not None:
            stats_y = 0.22
            ax.text(0.50, stats_y, "EXECUTION STATISTICS",
                    fontsize=10, fontweight="bold", ha="center", va="top",
                    fontfamily="monospace", color="#333333")

            ax.plot([0.01, 0.99], [stats_y - 0.015, stats_y - 0.015],
                    color="#CCCCCC", linewidth=0.8, clip_on=False)

            row_y = stats_y - 0.04
            line_h = 0.032

            stat_rows = [
                ("Total Orders",    f"{stats.total_orders:,}",      "#333333"),
                ("Limit Orders",    f"{stats.limit_orders:,}",      self.cfg.bid_colour),
                ("Market Orders",   f"{stats.market_orders:,}",     "#E74C3C"),
                ("Cancel Orders",   f"{stats.cancel_orders:,}",     "#9B59B6"),
                ("Volume Filled",   f"{stats.total_volume_filled:,.1f}", "#E74C3C"),
            ]

            for j, (label, val, col) in enumerate(stat_rows):
                y = row_y - j * line_h
                ax.text(0.08, y, label,
                        fontsize=8, ha="left", va="center",
                        fontfamily="monospace", color="#666666")
                ax.text(0.92, y, val,
                        fontsize=8.5, ha="right", va="center",
                        fontfamily="monospace", fontweight="bold", color=col)

            # ── Last order indicator ─────────────────────────────────
            if stats.last_order is not None:
                lo = stats.last_order
                indicator_y = row_y - len(stat_rows) * line_h - 0.02

                type_name = lo.order_type.name
                side_name = lo.side.name
                type_colours = {
                    "LIMIT": self.cfg.bid_colour,
                    "MARKET": "#E74C3C",
                    "CANCEL": "#9B59B6",
                }
                side_colours = {
                    "BID": self.cfg.bid_colour,
                    "ASK": self.cfg.ask_colour,
                }
                tc = type_colours.get(type_name, "#333")
                sc = side_colours.get(side_name, "#333")

                ax.text(0.08, indicator_y, "Last →",
                        fontsize=7.5, ha="left", va="center",
                        fontfamily="monospace", color="#999999")
                ax.text(0.35, indicator_y, type_name,
                        fontsize=8, ha="center", va="center",
                        fontfamily="monospace", fontweight="bold", color=tc,
                        bbox=dict(boxstyle="round,pad=0.15",
                                  fc="white", ec=tc, alpha=0.8, lw=0.8))
                ax.text(0.55, indicator_y, side_name,
                        fontsize=8, ha="center", va="center",
                        fontfamily="monospace", fontweight="bold", color=sc,
                        bbox=dict(boxstyle="round,pad=0.15",
                                  fc="white", ec=sc, alpha=0.8, lw=0.8))

                if lo.order_type is not OrderType.MARKET:
                    price_str = f"@{lo.price:.2f}"
                else:
                    price_str = "MKT"
                ax.text(0.75, indicator_y, f"{price_str} ×{lo.volume:.0f}",
                        fontsize=7.5, ha="center", va="center",
                        fontfamily="monospace", color="#666666")

    # ══════════════════════════════════════════════════════════════════
    #  RIGHT PANEL — Market Depth Chart
    # ══════════════════════════════════════════════════════════════════
    def _draw_chart_panel(self, snap: BookSnapshot) -> None:
        ax = self._ax_chart
        ax.clear()

        ml = self.cfg.max_levels

        bid_prices = snap.bid_prices[:ml]
        bid_vols = snap.bid_volumes[:ml]
        ask_prices = snap.ask_prices[:ml]
        ask_vols = snap.ask_volumes[:ml]

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
        ax.set_xlabel("Price", fontsize=11, fontweight="bold")
        ax.set_ylabel("Volume Available", fontsize=11, fontweight="bold")
        ax.set_title("Market Depth", fontsize=12, fontweight="bold", pad=10)
        ax.axhline(0, color="black", linewidth=0.8, zorder=2)
        ax.grid(axis="y", alpha=self.cfg.grid_alpha, zorder=0)
        ax.legend(loc="upper left", fontsize=8, framealpha=0.85)
        ax.set_facecolor(self.cfg.bg_colour)

        # Super title
        self._fig.suptitle(self.cfg.title, fontsize=14, fontweight="bold",
                           y=0.98, color="#333333")

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
