"""
synthetic_data.py
─────────────────
Synthetic order‑flow generator for the LOB simulation.

Produces a realistic stream of limit / market / cancel orders using
configurable Poisson arrival rates and price distributions centred on a
drifting reference price.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterator

import numpy as np

from src.order_book import Order, OrderType, Side, LimitOrderBook


# ── configuration ────────────────────────────────────────────────────────
@dataclass
class GeneratorConfig:
    """All tuneable knobs for the synthetic data engine."""
    initial_price: float = 100.0       # starting mid‑price
    tick_size: float = 0.01            # minimum price increment
    n_initial_levels: int = 8          # levels seeded on each side
    initial_vol_min: int = 1           # min volume per seeded level
    initial_vol_max: int = 10          # max volume per seeded level

    # arrival probabilities per tick  (should sum ≤ 1)
    prob_limit: float = 0.55
    prob_market: float = 0.20
    prob_cancel: float = 0.25

    # limit order placement
    limit_spread_ticks: int = 15       # max offset from mid in ticks
    limit_vol_min: int = 1
    limit_vol_max: int = 8

    # market order sizing
    market_vol_min: int = 1
    market_vol_max: int = 5

    # cancel sizing  (fraction of level to remove)
    cancel_frac_min: float = 0.2
    cancel_frac_max: float = 1.0

    seed: int | None = 42              # reproducibility


# ── generator ────────────────────────────────────────────────────────────
class SyntheticOrderGenerator:
    """
    Yields an infinite stream of Order objects driven by the config above.
    Keeps a reference to the live order book so it can make context‑aware
    decisions (e.g. cancel only existing levels).
    """

    def __init__(self, config: GeneratorConfig, book: LimitOrderBook) -> None:
        self.cfg = config
        self.book = book
        self.rng = np.random.default_rng(config.seed)
        random.seed(config.seed)

    # ── seed the book with initial liquidity ─────────────────────────
    def seed_book(self) -> None:
        """Place symmetric limit orders around the initial mid‑price."""
        mid = self.cfg.initial_price
        tick = self.cfg.tick_size

        for i in range(1, self.cfg.n_initial_levels + 1):
            bid_price = round(mid - i * tick, 6)
            ask_price = round(mid + i * tick, 6)
            bid_vol = self.rng.integers(self.cfg.initial_vol_min,
                                        self.cfg.initial_vol_max + 1)
            ask_vol = self.rng.integers(self.cfg.initial_vol_min,
                                        self.cfg.initial_vol_max + 1)
            self.book.process_order(
                Order(OrderType.LIMIT, Side.BID, bid_price, float(bid_vol)))
            self.book.process_order(
                Order(OrderType.LIMIT, Side.ASK, ask_price, float(ask_vol)))

    # ── infinite stream ──────────────────────────────────────────────
    def stream(self) -> Iterator[Order]:
        """Yield orders forever."""
        while True:
            yield self._next_order()

    # ── single order generation ──────────────────────────────────────
    def _next_order(self) -> Order:
        r = self.rng.random()
        if r < self.cfg.prob_limit:
            return self._random_limit()
        elif r < self.cfg.prob_limit + self.cfg.prob_market:
            return self._random_market()
        else:
            return self._random_cancel()

    def _random_limit(self) -> Order:
        side = Side.BID if self.rng.random() < 0.5 else Side.ASK
        mid = self.book.mid_price or self.cfg.initial_price
        offset = self.rng.integers(1, self.cfg.limit_spread_ticks + 1)
        tick = self.cfg.tick_size

        if side is Side.BID:
            price = round(mid - offset * tick, 6)
        else:
            price = round(mid + offset * tick, 6)

        vol = float(self.rng.integers(self.cfg.limit_vol_min,
                                       self.cfg.limit_vol_max + 1))
        return Order(OrderType.LIMIT, side, price, vol)

    def _random_market(self) -> Order:
        side = Side.BID if self.rng.random() < 0.5 else Side.ASK
        vol = float(self.rng.integers(self.cfg.market_vol_min,
                                       self.cfg.market_vol_max + 1))
        return Order(OrderType.MARKET, side, volume=vol)

    def _random_cancel(self) -> Order:
        snap = self.book.snapshot()
        # pick a random occupied side / level to cancel from
        bid_levels = list(zip(snap.bid_prices, snap.bid_volumes))
        ask_levels = list(zip(snap.ask_prices, snap.ask_volumes))
        all_levels = ([(Side.BID, p, v) for p, v in bid_levels] +
                      [(Side.ASK, p, v) for p, v in ask_levels])

        if not all_levels:
            # nothing to cancel → fall back to a limit order
            return self._random_limit()

        side, price, vol = random.choice(all_levels)
        frac = self.rng.uniform(self.cfg.cancel_frac_min,
                                self.cfg.cancel_frac_max)
        cancel_vol = round(vol * frac, 6)
        return Order(OrderType.CANCEL, side, price, cancel_vol)
