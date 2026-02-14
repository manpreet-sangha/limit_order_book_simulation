"""
test_smoke.py
─────────────
Headless smoke test for the LOB engine + synthetic data generator.
Verifies all core functionality without opening any GUI windows.
"""

import sys
sys.path.insert(0, ".")

from src.order_book import LimitOrderBook, Order, OrderType, Side
from src.synthetic_data import SyntheticOrderGenerator, GeneratorConfig


def test_order_book_engine():
    print("=" * 55)
    print("  TEST 1: Order Book Engine")
    print("=" * 55)

    book = LimitOrderBook()

    # Add limit orders
    book.process_order(Order(OrderType.LIMIT, Side.BID, 99.99, 5.0))
    book.process_order(Order(OrderType.LIMIT, Side.BID, 99.98, 3.0))
    book.process_order(Order(OrderType.LIMIT, Side.ASK, 100.01, 4.0))
    book.process_order(Order(OrderType.LIMIT, Side.ASK, 100.02, 6.0))

    snap = book.snapshot()
    print(f"  Best Bid:   {snap.best_bid}")
    print(f"  Best Ask:   {snap.best_ask}")
    print(f"  Mid Price:  {snap.mid_price}")
    print(f"  Spread:     {snap.spread}")
    print(f"  Bid levels: {list(zip(snap.bid_prices, snap.bid_volumes))}")
    print(f"  Ask levels: {list(zip(snap.ask_prices, snap.ask_volumes))}")

    assert snap.best_bid == 99.99, f"Expected best_bid=99.99, got {snap.best_bid}"
    assert snap.best_ask == 100.01, f"Expected best_ask=100.01, got {snap.best_ask}"
    assert snap.mid_price == 100.0, f"Expected mid_price=100.0, got {snap.mid_price}"
    assert snap.spread == 0.02, f"Expected spread=0.02, got {snap.spread}"
    print("  ✓ Limit orders correct\n")

    # Market order — BUY eats ask side
    book.process_order(Order(OrderType.MARKET, Side.BID, volume=2.0))
    snap2 = book.snapshot()
    print(f"  After market BUY of 2:")
    print(f"  Ask levels: {list(zip(snap2.ask_prices, snap2.ask_volumes))}")
    assert snap2.ask_volumes[0] == 2.0, f"Expected ask vol=2.0, got {snap2.ask_volumes[0]}"
    print("  ✓ Market order correct\n")

    # Cancel order
    book.process_order(Order(OrderType.CANCEL, Side.BID, 99.99, 3.0))
    snap3 = book.snapshot()
    print(f"  After cancel 3 from bid @ 99.99:")
    print(f"  Bid levels: {list(zip(snap3.bid_prices, snap3.bid_volumes))}")
    assert snap3.bid_volumes[0] == 2.0, f"Expected bid vol=2.0, got {snap3.bid_volumes[0]}"
    print("  ✓ Cancel order correct\n")

    # Full cancel — level should disappear
    book.process_order(Order(OrderType.CANCEL, Side.BID, 99.99, 2.0))
    snap4 = book.snapshot()
    assert snap4.best_bid == 99.98, f"Expected best_bid=99.98, got {snap4.best_bid}"
    print(f"  After full cancel of bid @ 99.99:")
    print(f"  Best bid now: {snap4.best_bid}")
    print("  ✓ Level removal correct\n")

    print("  ★ Order Book Engine: ALL PASS\n")


def test_synthetic_data_generator():
    print("=" * 55)
    print("  TEST 2: Synthetic Data Generator")
    print("=" * 55)

    book = LimitOrderBook()
    config = GeneratorConfig(
        initial_price=100.0,
        tick_size=0.01,
        n_initial_levels=5,
        seed=42,
    )
    generator = SyntheticOrderGenerator(config, book)

    # Seed book
    generator.seed_book()
    snap = book.snapshot()
    print(f"  After seeding:")
    print(f"  Bid levels: {len(snap.bid_prices)}")
    print(f"  Ask levels: {len(snap.ask_prices)}")
    print(f"  Best bid:   {snap.best_bid}")
    print(f"  Best ask:   {snap.best_ask}")
    assert len(snap.bid_prices) == 5, f"Expected 5 bid levels, got {len(snap.bid_prices)}"
    assert len(snap.ask_prices) == 5, f"Expected 5 ask levels, got {len(snap.ask_prices)}"
    print("  ✓ Seeding correct\n")

    # Stream 100 orders and check nothing crashes
    stream = generator.stream()
    order_types_seen = set()
    for i in range(100):
        order = next(stream)
        order_types_seen.add(order.order_type)
        book.process_order(order, timestamp=i)

    snap_final = book.snapshot()
    print(f"  After 100 synthetic orders:")
    print(f"  Order types seen: {[ot.name for ot in order_types_seen]}")
    print(f"  Bid levels: {len(snap_final.bid_prices)}")
    print(f"  Ask levels: {len(snap_final.ask_prices)}")
    print(f"  Best bid:   {snap_final.best_bid}")
    print(f"  Best ask:   {snap_final.best_ask}")
    print(f"  Mid price:  {snap_final.mid_price}")
    print(f"  Spread:     {snap_final.spread}")

    assert OrderType.LIMIT in order_types_seen, "No LIMIT orders generated"
    assert OrderType.MARKET in order_types_seen, "No MARKET orders generated"
    assert OrderType.CANCEL in order_types_seen, "No CANCEL orders generated"
    print("  ✓ All order types generated\n")

    print("  ★ Synthetic Data Generator: ALL PASS\n")


def test_reproducibility():
    print("=" * 55)
    print("  TEST 3: Reproducibility (seeded RNG)")
    print("=" * 55)

    snapshots = []
    for run in range(2):
        book = LimitOrderBook()
        config = GeneratorConfig(seed=123)
        gen = SyntheticOrderGenerator(config, book)
        gen.seed_book()
        stream = gen.stream()
        for i in range(50):
            order = next(stream)
            book.process_order(order, timestamp=i)
        snapshots.append(book.snapshot())

    s1, s2 = snapshots
    assert s1.bid_prices == s2.bid_prices, "Bid prices differ between runs"
    assert s1.bid_volumes == s2.bid_volumes, "Bid volumes differ between runs"
    assert s1.ask_prices == s2.ask_prices, "Ask prices differ between runs"
    assert s1.ask_volumes == s2.ask_volumes, "Ask volumes differ between runs"
    print(f"  Run 1 mid: {s1.mid_price}  |  Run 2 mid: {s2.mid_price}")
    print("  ✓ Both runs produce identical book state\n")

    print("  ★ Reproducibility: PASS\n")


def test_visualiser_import():
    print("=" * 55)
    print("  TEST 4: Visualiser Import Check")
    print("=" * 55)

    from src.visualiser import LOBVisualiser, VisualiserConfig
    cfg = VisualiserConfig()
    vis = LOBVisualiser(cfg)
    print(f"  Config: {cfg.fig_width}x{cfg.fig_height}, {cfg.interval_ms}ms interval")
    print(f"  Bid colour: {cfg.bid_colour}  Ask colour: {cfg.ask_colour}")
    print("  ✓ Visualiser imports and instantiates correctly\n")

    print("  ★ Visualiser Import: PASS\n")


if __name__ == "__main__":
    test_order_book_engine()
    test_synthetic_data_generator()
    test_reproducibility()
    test_visualiser_import()

    print("=" * 55)
    print("  ✅  ALL TESTS PASSED")
    print("=" * 55)
