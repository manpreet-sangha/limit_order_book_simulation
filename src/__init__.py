"""
src — Limit Order Book Simulation & Visualisation
══════════════════════════════════════════════════
Modules
-------
order_book      Core LOB engine (orders, matching, snapshots)
synthetic_data  Synthetic order-flow generator
visualiser      Real-time matplotlib market-depth chart
"""

from src.order_book import (
    LimitOrderBook,
    Order,
    OrderType,
    Side,
    BookSnapshot,
    ExecutionStats,
)
from src.synthetic_data import (
    SyntheticOrderGenerator,
    GeneratorConfig,
)
from src.visualiser import (
    LOBVisualiser,
    VisualiserConfig,
)

__all__ = [
    # order_book
    "LimitOrderBook",
    "Order",
    "OrderType",
    "Side",
    "BookSnapshot",
    "ExecutionStats",
    # synthetic_data
    "SyntheticOrderGenerator",
    "GeneratorConfig",
    # visualiser
    "LOBVisualiser",
    "VisualiserConfig",
]
