# Limit Order Book Simulation & Real-Time Visualisation

> A fully modular Python simulation of a **Limit Order Book (LOB)** with synthetic order-flow generation and a real-time market-depth visualisation powered by `matplotlib`.

![Market Depth Visualisation](limit%20order%20book%20visualisation%20market%20depth.png)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
  - [Limit Order Book Engine](#limit-order-book-engine)
  - [Synthetic Data Generator](#synthetic-data-generator)
  - [Real-Time Visualiser](#real-time-visualiser)
- [Key Concepts](#key-concepts)
- [Dependencies](#dependencies)
- [License](#license)

---

## Overview

This project simulates the core mechanics of a **Limit Order Book** — the fundamental data structure used by modern exchanges to match buyers and sellers. It generates a continuous stream of synthetic orders (limit, market, and cancel) and visualises the evolving market depth in real time.

The visualisation mirrors the classic LOB diagram:

| Element | Description |
|---|---|
| **Orange bars (↑)** | Bid (buy) side — volume plotted upward |
| **Blue bars (↓)** | Ask (sell) side — volume plotted downward |
| **Green dashed line** | Mid-price |
| **Shaded grey band** | Bid-ask spread |
| **Annotations** | Best bid, best ask, mid-price, and spread |

---

## Features

- **Price-level aggregated LOB** with O(n log n) snapshot generation
- **Three order types**: Limit, Market, and Cancel
- **Configurable synthetic data engine** with tuneable arrival rates, spread width, and volume distributions
- **Real-time animation** at ~12.5 fps (configurable) using `matplotlib.animation.FuncAnimation`
- **Fully reproducible** via seeded random number generators (`numpy` + stdlib `random`)
- **Clean modular architecture** — each component is independently testable

---

## Project Structure

```
limit order book/
│
├── main.py                  # Entry point — wires everything together
├── requirements.txt         # Python dependencies
├── README.md                # This file
│
├── src/
│   ├── __init__.py          # Package exports
│   ├── order_book.py        # Core LOB engine (orders, matching, snapshots)
│   ├── synthetic_data.py    # Synthetic order-flow generator
│   └── visualiser.py        # Real-time matplotlib market-depth chart
│
└── limit order book visualisation market depth.png  # Reference diagram
```

---

## Installation

### Prerequisites

- **Python 3.10+**
- A graphical environment (the visualiser opens an interactive `matplotlib` window)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/manpreet-sangha/limit_order_book_simulation.git
cd limit_order_book_simulation

# 2. Create a virtual environment (recommended)
python -m venv .venv

# 3. Activate it
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## Usage

```bash
python main.py
```

A window will open showing the real-time market-depth chart. The order book updates continuously with synthetic orders. **Press `Ctrl+C` or close the window to stop.**

---

## Configuration

All parameters are exposed as dataclass configs in `main.py`:

### Generator Config (`GeneratorConfig`)

| Parameter | Default | Description |
|---|---|---|
| `initial_price` | `100.0` | Starting mid-price |
| `tick_size` | `0.01` | Minimum price increment |
| `n_initial_levels` | `8` | Levels seeded on each side at startup |
| `initial_vol_min / max` | `1 / 10` | Volume range for seeded levels |
| `prob_limit` | `0.55` | Probability of a limit order per tick |
| `prob_market` | `0.20` | Probability of a market order per tick |
| `prob_cancel` | `0.25` | Probability of a cancellation per tick |
| `limit_spread_ticks` | `15` | Max offset from mid-price (in ticks) |
| `limit_vol_min / max` | `1 / 8` | Volume range for new limit orders |
| `market_vol_min / max` | `1 / 5` | Volume range for market orders |
| `seed` | `42` | Random seed for reproducibility |

### Visualiser Config (`VisualiserConfig`)

| Parameter | Default | Description |
|---|---|---|
| `fig_width / fig_height` | `14 / 7` | Figure dimensions (inches) |
| `max_levels` | `12` | Maximum price levels shown per side |
| `interval_ms` | `80` | Milliseconds between animation frames |
| `bid_colour` | `#F5A623` | Colour for bid bars |
| `ask_colour` | `#4A90D9` | Colour for ask bars |

---

## How It Works

### Limit Order Book Engine

**`src/order_book.py`**

The `LimitOrderBook` class maintains two dictionaries (`_bids` and `_asks`) mapping price levels to aggregated volume. It supports:

- **Limit orders** — add volume at a specific price level
- **Market orders** — consume volume from the opposite side (price-time priority)
- **Cancel orders** — remove volume from a specific price level

After every order, a `BookSnapshot` is returned containing sorted price/volume arrays, best bid/ask, mid-price, and spread.

### Synthetic Data Generator

**`src/synthetic_data.py`**

The `SyntheticOrderGenerator` produces an infinite stream of context-aware orders:

1. **Limit orders** — placed at random offsets from the current mid-price
2. **Market orders** — randomly sized, consuming liquidity from the opposite side
3. **Cancel orders** — target a random existing price level and remove a fraction of its volume

Arrival rates are controlled by `prob_limit`, `prob_market`, and `prob_cancel`. The generator references the live order book to make realistic cancellation decisions.

### Real-Time Visualiser

**`src/visualiser.py`**

Uses `matplotlib.animation.FuncAnimation` to redraw the depth chart every `interval_ms` milliseconds. Each frame:

1. Calls the snapshot generator to process the next synthetic order
2. Clears and redraws bid bars (upward, orange) and ask bars (downward, blue)
3. Overlays reference lines for mid-price, best bid, best ask
4. Shades the bid-ask spread and annotates key values

---

## Key Concepts

| Term | Definition |
|---|---|
| **Limit Order** | An order to buy/sell at a specific price or better |
| **Market Order** | An order to buy/sell immediately at the best available price |
| **Bid** | A buy order — the price a buyer is willing to pay |
| **Ask** | A sell order — the price a seller is willing to accept |
| **Spread** | The difference between the best ask and best bid |
| **Mid-Price** | The average of the best bid and best ask |
| **Market Depth** | The total range of prices with resting orders |
| **LOB Levels** | Individual price levels with aggregated volume |

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `matplotlib` | ≥ 3.7 | Real-time animated visualisation |
| `numpy` | ≥ 1.24 | Fast random number generation & array ops |

---

## License

This project is open-source. See the repository for licence details.

---

**Author:** Manpreet Sangha  
**Repository:** [github.com/manpreet-sangha/limit_order_book_simulation](https://github.com/manpreet-sangha/limit_order_book_simulation)
