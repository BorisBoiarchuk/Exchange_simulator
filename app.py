import math
import random
import time

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from matching_engine import Exchange

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None


st.set_page_config(page_title="Exchange Simulator", layout="wide")

DEFAULT_PRODUCTS = ["Stock A", "Stock B", "Stock C"]


if "exchanges" not in st.session_state:
    st.session_state.exchanges = {p: Exchange() for p in DEFAULT_PRODUCTS}

if "selected_product" not in st.session_state:
    st.session_state.selected_product = DEFAULT_PRODUCTS[0]

if "mean_reversion" not in st.session_state:
    st.session_state.mean_reversion = {p: 100 for p in DEFAULT_PRODUCTS}

if "bot_enabled" not in st.session_state:
    st.session_state.bot_enabled = False

if "last_bot_run" not in st.session_state:
    st.session_state.last_bot_run = 0.0

if "bot_log" not in st.session_state:
    st.session_state.bot_log = []


def render_trades(rows):
    st.subheader("Recent Trades")
    if not rows:
        st.write("No trades yet")
        return

    df = pd.DataFrame(rows)[["price", "quantity", "bid_order_id", "ask_order_id"]]
    df.columns = ["Price", "Qty", "Buy ID", "Sell ID"]
    st.table(df.reset_index(drop=True))


def render_price_chart(trades, product_name):
    st.subheader(f"Last Traded Prices — {product_name}")

    if not trades:
        st.write("No trades yet")
        return

    df = pd.DataFrame(trades).copy()
    df = df.iloc[::-1].reset_index(drop=True)
    df["Trade #"] = df.index + 1

    fig = px.line(
        df[-10:], # last 10 trades
        x="Trade #",
        y="price",
        markers=True,
        title=f"Trade Price History — {product_name}",
    )

    fig.update_layout(
        template="plotly_dark",
        xaxis_title="Trade #",
        yaxis_title="Price",
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)

def aggregate_book_side(levels, side, visible_levels=8):
    """
    levels: list of dicts like {"price": 101, "quantity": 25}
    side: "ask" or "bid"
    returns: dataframe-ready rows
    """
    if not levels:
        return []

    # asks should be lowest->highest before trimming
    # bids should be highest->lowest before trimming
    if side == "ask":
        ordered = sorted(levels, key=lambda x: x["price"])
    else:
        ordered = sorted(levels, key=lambda x: x["price"], reverse=True)

    shown = ordered[:visible_levels]
    hidden = ordered[visible_levels:]

    rows = [{"Price": lvl["price"], "Quantity": lvl["quantity"]} for lvl in shown]

    if hidden:
        total_hidden_qty = sum(lvl["quantity"] for lvl in hidden)

        if side == "ask":
            boundary = shown[-1]["price"]
            rows.append({
                "Price": f"{boundary}+",
                "Quantity": total_hidden_qty,
            })
        else:
            boundary = shown[-1]["price"]
            rows.append({
                "Price": f"{boundary}-",
                "Quantity": total_hidden_qty,
            })

    return rows

def sample_bot_price(mean_reversion_price: int, std: float) -> int:
    x = random.gauss(0, std)  # standard normal
    price = round(mean_reversion_price * math.exp(x - 0.5 * std ** 2), 0)
    return max(1, int(price))

def sample_bot_quantity(shape: int, scale: int) -> int:
    return math.ceil(np.random.gamma(shape, scale))  # gamma distribution, mean shape * scale

def bot_step():
    bot_events = []

    for product, exchange in st.session_state.exchanges.items():
        mu = int(st.session_state.mean_reversion[product])
        std = 0.25
        side = random.choice(["bid", "ask"])
        price = sample_bot_price(mu, std)
        quantity = sample_bot_quantity(5, 2)

        trades = exchange.place_order(
            side=side,
            price=price,
            quantity=quantity,
        )

        bot_events.append(
            {
                "time": time.strftime("%H:%M:%S"),
                "product": product,
                "side": side,
                "price": price,
                "quantity": quantity,
                "trades_executed": len(trades),
            }
        )

    st.session_state.bot_log = (bot_events + st.session_state.bot_log)[:20]


st.title("Multi-Product Exchange Simulator")

if st_autorefresh is not None:
    st_autorefresh(interval=5000, key="exchange_bot_refresh")
else:
    st.warning(
        "Auto-refresh is not installed. The bot will only run when the page reruns "
        "(for example after a click). Install it with: pip install streamlit-autorefresh"
    )

st.subheader("Bot Controls")

control_col1, control_col2 = st.columns([1, 3])

with control_col1:
    st.session_state.bot_enabled = st.checkbox(
        "Enable random bot",
        value=st.session_state.bot_enabled,
    )

with control_col2:
    st.caption(
        f"Every 5 seconds, the bot places one random bid or ask of size 10 for each product "
        "at price round(mean_reversion * e^(X - 0.5*sigma^2), 0), where X ~ Normal."
    )

mu_cols = st.columns(len(DEFAULT_PRODUCTS))
for i, product in enumerate(DEFAULT_PRODUCTS):
    with mu_cols[i]:
        st.session_state.mean_reversion[product] = st.number_input(
            f"{product} mean reversion",
            min_value=1,
            value=int(st.session_state.mean_reversion[product]),
            step=1,
            key=f"mu_{product}",
        )

now = time.time()
if st.session_state.bot_enabled and now - st.session_state.last_bot_run >= 5:
    bot_step()
    st.session_state.last_bot_run = now

left, _ = st.columns([1, 5])

with left:
    selected_product = st.selectbox(
        "Product",
        options=list(st.session_state.exchanges.keys()),
        index=list(st.session_state.exchanges.keys()).index(
            st.session_state.selected_product
        ),
        label_visibility="collapsed",
    )

st.session_state.selected_product = selected_product
exchange = st.session_state.exchanges[st.session_state.selected_product]

col1, col2 = st.columns([1, 2.2])

with col1:
    st.subheader(f"Order Entry — {st.session_state.selected_product}")

    side = st.selectbox("Side", ["bid", "ask"])
    price = st.number_input("Price", min_value=1, value=100, step=1)
    quantity = st.number_input("Quantity", min_value=1, value=10, step=1)

    if st.button("Submit Order"):
        trades = exchange.place_order(
            side=side,
            price=int(price),
            quantity=int(quantity),
        )
        if trades:
            st.success(f"Executed {len(trades)} trade(s)")
        else:
            st.info("Order added to book")

    st.subheader("Market Summary")
    top = exchange.get_top_of_book()
    st.write(f"Best Bid: {top['best_bid']}")
    st.write(f"Best Ask: {top['best_ask']}")
    st.write(f"Spread: {top['spread']}")
    st.write(f"Last Trade: {top['last_trade']}")

    st.subheader("Recent Bot Orders")
    if st.session_state.bot_log:
        bot_df = pd.DataFrame(st.session_state.bot_log)[
            ["time", "product", "side", "price", "quantity", "trades_executed"]
        ]
        bot_df.columns = ["Time", "Product", "Side", "Price", "Qty", "Trades"]
        st.table(bot_df.reset_index(drop=True))
    else:
        st.write("No bot orders yet")

with col2:
    book_col, chart_col = st.columns([1.1, 1])

    book = exchange.get_book()
    trades = exchange.get_trades()

    with book_col:
        asks = book["asks"]
        ask_rows = aggregate_book_side(asks, side="ask", visible_levels=8)
        asks_df = pd.DataFrame(ask_rows, columns=["Price", "Quantity"])
        asks_styled = asks_df.style.set_properties(**{"color": "#ff4b4b"})
        st.subheader("Asks")
        st.table(asks_styled)

        bids = book["bids"]
        bid_rows = aggregate_book_side(bids, side="bid", visible_levels=8)
        bids_df = pd.DataFrame(bid_rows, columns=["Price", "Quantity"])
        bids_styled = bids_df.style.set_properties(**{"color": "#00c853"})
        st.subheader("Bids")
        st.table(bids_styled)

    with chart_col:
        render_price_chart(trades, st.session_state.selected_product)

    render_trades(trades)