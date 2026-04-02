# Multi-Product Exchange Simulator

An interactive trading simulator that models a real-world limit order book with price-time priority, built with **Python** and **Streamlit**.

This project demonstrates how modern electronic exchanges match orders, visualize market activity, and simulate trading behavior.

---

## Features

### Matching Engine

* Price-time priority (FIFO within price levels)
* Limit order matching
* Partial fills supported
* Efficient best bid/ask lookup using heaps

### Interactive UI

* Real-time order book (bids & asks)
* Trade history table
* Price chart (last trades)
* Market summary (spread, last price)

### Trading Bot

* Simulates realistic order flow
* Log-normal price distribution
* Gamma-distributed order sizes
* Configurable mean-reversion per product

### Multi-Asset Support

* Simultaneous simulation of multiple products (e.g., Stock A, B, C)

---

## Demo

Run the app locally to explore the exchange in action:

```bash
streamlit run app.py
```

---

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/exchange-simulator.git
cd exchange-simulator
pip install -r requirements.txt
```

Optional (for auto-refresh bot behavior):

```bash
pip install streamlit-autorefresh
```

---

## How It Works

### Order Matching

Orders are matched using a **limit order book**:

* **Bids** (buy orders): matched against lowest asks
* **Asks** (sell orders): matched against highest bids
* Trades occur when prices cross

Matching follows:

1. Best price first
2. Oldest order first (FIFO)

---

### Example Trade Flow

1. User places a bid at price 100
2. Existing ask at 95 is matched
3. Trade executes at resting order price (95)
4. Remaining quantity continues matching or rests in book

---

### Bot Price Model

Prices are sampled using a log-normal model:

[
price = \mu \cdot e^{X - \frac{1}{2}\sigma^2}, \quad X \sim \mathcal{N}(0, \sigma)
]

This creates realistic, skewed price movements around a mean.

---

## Project Structure

```
.
├── app.py                # Streamlit UI
├── matching_engine.py    # Core exchange logic
└── README.md
```

---

## Tech Stack

* Python
* Streamlit
* Pandas / NumPy
* Plotly

---

## Limitations

This is a **simulation**, not a production trading system.

Missing features:

* Order cancellation / modification
* Market orders (only limit orders supported)
* Persistent storage
* Latency & concurrency modeling
* Advanced order types (IOC, FOK, etc.)

---

## Future Improvements

* Add market and cancel orders
* Introduce multiple trading agents
* PnL tracking per user
* Historical data replay / backtesting
* WebSocket-based real-time updates
* Unit tests for matching engine

---

## Why This Project?

This project is designed to demonstrate:

* Understanding of exchange mechanics
* Data structures for real-time systems
* Simulation of stochastic processes
* Full-stack prototyping with Python

---

## Screenshots (optional)

*Add screenshots of the UI here (order book, chart, etc.)*

---

## Author

Your Name
Boris Boiarchuk | github.com/BorisBoiarchuk/