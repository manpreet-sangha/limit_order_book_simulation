"""
main.py
───────
Entry point – wires together the order book engine, synthetic data
generator, and real‑time visualiser.

Run:
    python main.py              # live interactive window
    python main.py --gif        # save a 15‑second GIF instead
    python main.py --gif 20     # save a 20‑second GIF

Press Ctrl+C or close the window to stop the live view.
"""

import sys

from src.order_book import LimitOrderBook
from src.synthetic_data import SyntheticOrderGenerator, GeneratorConfig
from src.visualiser import LOBVisualiser, VisualiserConfig


def main() -> None:
    # ── 1. Create the core order book ────────────────────────────────
    book = LimitOrderBook()

    # ── 2. Configure & create the synthetic data generator ───────────
    gen_config = GeneratorConfig(
        initial_price=100.0,
        tick_size=0.01,
        n_initial_levels=8,
        initial_vol_min=1,
        initial_vol_max=10,
        prob_limit=0.55,
        prob_market=0.20,
        prob_cancel=0.25,
        limit_spread_ticks=15,
        limit_vol_min=1,
        limit_vol_max=8,
        market_vol_min=1,
        market_vol_max=5,
        seed=42,
    )
    generator = SyntheticOrderGenerator(gen_config, book)

    # ── 3. Seed the book with initial liquidity ──────────────────────
    generator.seed_book()

    # ── 4. Build a closure that the visualiser calls each frame ──────
    order_stream = generator.stream()
    tick = [0]  # mutable counter

    def next_snapshot():
        """Process the next synthetic order and return the new snapshot."""
        order = next(order_stream)
        tick[0] += 1
        return book.process_order(order, timestamp=tick[0])

    # ── 5. Configure & launch the real‑time visualiser ───────────────
    vis_config = VisualiserConfig(
        fig_width=18,
        fig_height=8,
        max_levels=12,
        table_levels=10,
        interval_ms=80,       # ≈ 12.5 updates / second
        title="Limit Order Book – Real‑Time Market Depth",
    )
    visualiser = LOBVisualiser(vis_config)

    # ── 6. Choose mode: live view or GIF capture ─────────────────────
    if "--gif" in sys.argv:
        idx = sys.argv.index("--gif")
        duration = float(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 15.0
        visualiser.save_gif(next_snapshot,
                            filepath="lob_simulation.gif",
                            duration_s=duration,
                            fps=12)
    else:
        visualiser.start(next_snapshot)   # blocks until window is closed


if __name__ == "__main__":
    main()
