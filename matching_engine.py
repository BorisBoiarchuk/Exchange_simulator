from collections import deque
import heapq
import itertools

class Order:
    def __init__(self, order_id, side, price, quantity):
        self.id = order_id
        self.side = side
        self.price = price
        self.quantity = quantity

class Exchange:
    def __init__(self):
        self.bids = {}          # price -> deque[Order]
        self.asks = {}          # price -> deque[Order]
        self.bid_heap = []      # negative prices
        self.ask_heap = []      # positive prices
        self.trades = []
        self.order_id_counter = itertools.count(1)
        self.last_trade_price = None

    def _best_bid(self):
        while self.bid_heap and -self.bid_heap[0] not in self.bids:
            heapq.heappop(self.bid_heap)
        return -self.bid_heap[0] if self.bid_heap else None

    def _best_ask(self):
        while self.ask_heap and self.ask_heap[0] not in self.asks:
            heapq.heappop(self.ask_heap)
        return self.ask_heap[0] if self.ask_heap else None

    def _add_to_book(self, order):
        book = self.bids if order.side == "bid" else self.asks
        heap = self.bid_heap if order.side == "bid" else self.ask_heap

        if order.price not in book:
            book[order.price] = deque()
            heapq.heappush(heap, -order.price if order.side == "bid" else order.price)

        book[order.price].append(order)

    def place_order(self, side, price, quantity):
        order = Order(next(self.order_id_counter), side, price, quantity)
        trades = []

        if side == "bid":
            while order.quantity > 0:
                best_ask = self._best_ask()
                if best_ask is None or best_ask > order.price:
                    break

                resting_queue = self.asks[best_ask]
                resting = resting_queue[0]

                traded_qty = min(order.quantity, resting.quantity)
                trade_price = resting.price

                trades.append({
                    "bid_order_id": order.id,
                    "ask_order_id": resting.id,
                    "price": trade_price,
                    "quantity": traded_qty,
                })

                self.trades.append(trades[-1])
                self.last_trade_price = trade_price

                order.quantity -= traded_qty
                resting.quantity -= traded_qty

                if resting.quantity == 0:
                    resting_queue.popleft()

                if not resting_queue:
                    del self.asks[best_ask]

        else:
            while order.quantity > 0:
                best_bid = self._best_bid()
                if best_bid is None or best_bid < order.price:
                    break

                resting_queue = self.bids[best_bid]
                resting = resting_queue[0]

                traded_qty = min(order.quantity, resting.quantity)
                trade_price = resting.price

                trades.append({
                    "bid_order_id": resting.id,
                    "ask_order_id": order.id,
                    "price": trade_price,
                    "quantity": traded_qty,
                })

                self.trades.append(trades[-1])
                self.last_trade_price = trade_price

                order.quantity -= traded_qty
                resting.quantity -= traded_qty

                if resting.quantity == 0:
                    resting_queue.popleft()

                if not resting_queue:
                    del self.bids[best_bid]

        if order.quantity > 0:
            self._add_to_book(order)

        return trades

    def get_book(self):
        bids = []
        asks = []

        for price, orders in self.bids.items():
            total_qty = sum(o.quantity for o in orders)
            bids.append({"price": price, "quantity": total_qty})

        for price, orders in self.asks.items():
            total_qty = sum(o.quantity for o in orders)
            asks.append({"price": price, "quantity": total_qty})

        bids.sort(key=lambda x: x["price"], reverse=True)
        asks.sort(key=lambda x: x["price"])
        return {"bids": bids, "asks": asks}

    def get_top_of_book(self):
        best_bid = self._best_bid()
        best_ask = self._best_ask()
        spread = None if best_bid is None or best_ask is None else best_ask - best_bid
        return {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "last_trade": self.last_trade_price,
        }

    def get_trades(self, n=20):
        return list(reversed(self.trades[-n:]))