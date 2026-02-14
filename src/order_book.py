"""
order_book.py
─────────────
Core Limit Order Book engine.

Maintains bid (buy) and ask (sell) sides as sorted dictionaries of
{price: volume}.  Supports limit orders, market orders, and cancellations.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple


# ── enums ────────────────────────────────────────────────────────────────
class Side(Enum):
    BID = auto()   # buy side
    ASK = auto()   # sell side


class OrderType(Enum):
    LIMIT = auto()
    MARKET = auto()
    CANCEL = auto()


# ── order data class ─────────────────────────────────────────────────────
@dataclass
class Order:
    order_type: OrderType
    side: Side
    price: float = 0.0       # ignored for market orders
    volume: float = 0.0


# ── snapshot returned after every update ─────────────────────────────────
@dataclass
class BookSnapshot:
    """Immutable view of the order book at a single point in time."""
    bid_prices: List[float]       # descending (best bid first)
    bid_volumes: List[float]
    ask_prices: List[float]       # ascending  (best ask first)
    ask_volumes: List[float]
    best_bid: Optional[float]
    best_ask: Optional[float]
    mid_price: Optional[float]
    spread: Optional[float]
    timestamp: float = 0.0


# ── limit order book ─────────────────────────────────────────────────────
class LimitOrderBook:
    """
    Price‑level aggregated Limit Order Book.

    Internally keeps two dicts:
        _bids  {price: volume}   – buy  side, best = max price
        _asks  {price: volume}   – sell side, best = min price
    """

    def __init__(self) -> None:
        self._bids: Dict[float, float] = {}
        self._asks: Dict[float, float] = {}
        self._time: float = 0.0

    # ── properties ───────────────────────────────────────────────────
    @property
    def best_bid(self) -> Optional[float]:
        return max(self._bids) if self._bids else None

    @property
    def best_ask(self) -> Optional[float]:
        return min(self._asks) if self._asks else None

    @property
    def mid_price(self) -> Optional[float]:
        bb, ba = self.best_bid, self.best_ask
        if bb is not None and ba is not None:
            return round((bb + ba) / 2, 6)
        return None

    @property
    def spread(self) -> Optional[float]:
        bb, ba = self.best_bid, self.best_ask
        if bb is not None and ba is not None:
            return round(ba - bb, 6)
        return None

    # ── internal helpers ─────────────────────────────────────────────
    def _add_limit(self, side: Side, price: float, volume: float) -> None:
        book = self._bids if side is Side.BID else self._asks
        book[price] = book.get(price, 0.0) + volume

    def _cancel(self, side: Side, price: float, volume: float) -> None:
        book = self._bids if side is Side.BID else self._asks
        if price in book:
            book[price] -= volume
            if book[price] <= 1e-12:
                del book[price]

    def _execute_market(self, side: Side, volume: float) -> None:
        """
        A market BUY eats into the ASK side (lowest prices first).
        A market SELL eats into the BID side (highest prices first).
        """
        if side is Side.BID:
            book = self._asks
            sorter = sorted(book.keys())           # ascending
        else:
            book = self._bids
            sorter = sorted(book.keys(), reverse=True)  # descending

        remaining = volume
        for price in sorter:
            if remaining <= 0:
                break
            available = book[price]
            filled = min(available, remaining)
            book[price] -= filled
            remaining -= filled
            if book[price] <= 1e-12:
                del book[price]

    # ── public API ───────────────────────────────────────────────────
    def process_order(self, order: Order, timestamp: float = 0.0) -> BookSnapshot:
        """Apply an order and return a new snapshot of the book."""
        self._time = timestamp

        if order.order_type is OrderType.LIMIT:
            self._add_limit(order.side, order.price, order.volume)
        elif order.order_type is OrderType.MARKET:
            self._execute_market(order.side, order.volume)
        elif order.order_type is OrderType.CANCEL:
            self._cancel(order.side, order.price, order.volume)

        return self.snapshot(timestamp)

    def snapshot(self, timestamp: float = 0.0) -> BookSnapshot:
        """Return a frozen snapshot of the current book state."""
        bid_prices = sorted(self._bids.keys(), reverse=True)
        ask_prices = sorted(self._asks.keys())
        return BookSnapshot(
            bid_prices=bid_prices,
            bid_volumes=[self._bids[p] for p in bid_prices],
            ask_prices=ask_prices,
            ask_volumes=[self._asks[p] for p in ask_prices],
            best_bid=self.best_bid,
            best_ask=self.best_ask,
            mid_price=self.mid_price,
            spread=self.spread,
            timestamp=timestamp,
        )

    def reset(self) -> None:
        self._bids.clear()
        self._asks.clear()
        self._time = 0.0
