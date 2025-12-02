# TraidingEngine.py
"""
TraidingEngine.py

A self-contained demo trading engine implementing simulated market prices,
trade placement (buy/sell), portfolio management with profit/loss tracking,
stop-loss and take-profit handling, simple chart generation, and a clean
dashboard interface (programmatic, no UI included).

Class: TraidingEngine

This module is intended for demo/testing purposes only and does not connect
to any real broker or live market data. It simulates prices with a random
walk and supports background simulation via threading.
"""

from __future__ import annotations

import threading
import time
import random
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict, deque
import io

# Optional deps for charts and basic data handling
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class TraidingEngine:
    """
    A demo trading engine that simulates market prices, allows placing
    buy/sell orders, maintains a portfolio, supports simple stop-loss and
    take-profit orders, and can generate basic charts and dashboards.

    Note: For demo usage only. No real money, no real broker connectivity.
    """

    def __init__(self, seed: Optional[int] = None, starting_cash: float = 100000.0):
        """
        Initialize the engine with optional random seed and starting cash.
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        # Basic simulated market data: symbol -> current price
        self.market_data: Dict[str, float] = {
            'AAPL': 150.00,
            'GOOGL': 2800.00,
            'TSLA': 700.00,
            'BTCUSD': 50000.00,
            'ETHUSD': 3500.00,
        }

        # Price history: symbol -> deque of (timestamp, price)
        self.price_history: Dict[str, deque] = {s: deque(maxlen=1000) for s in self.market_data}
        now = datetime.utcnow()
        for s, p in self.market_data.items():
            self.price_history[s].append((now, float(p)))

        # Portfolio: symbol -> {'quantity': float, 'avg_price': float}
        self.portfolio: Dict[str, Dict[str, float]] = {}

        # Cash and realized P/L tracking
        self.cash: float = float(starting_cash)
        self.realized_pnl: float = 0.0

        # Open conditional orders (stop-loss / take-profit): list of dict
        # Each order: {id, symbol, side, quantity, stop_loss, take_profit, status}
        self.conditional_orders: List[Dict[str, Any]] = []

        # Trade history (executed orders)
        self.trade_history: List[Dict[str, Any]] = []

        # For plotting portfolio value over time
        self.portfolio_history: deque = deque(maxlen=1000)  # (timestamp, equity_value)
        self._record_portfolio()

        # Simulation controls
        self.sim_thread: Optional[threading.Thread] = None
        self._simulate_flag = threading.Event()
        self.sim_interval = 1.0  # seconds between ticks
        self.volatility = 0.01  # baseline volatility for random walk

    # ----------------
    # Market simulation
    # ----------------
    def update_market_data(self) -> None:
        """
        Apply a random walk to each symbol's price to simulate market movement.
        Also append the new price to price history.
        """
        for symbol, price in list(self.market_data.items()):
            # percentage change sampled from normal distribution
            pct_change = np.random.normal(loc=0.0, scale=self.volatility)
            # incorporate occasional spikes
            if random.random() < 0.01:
                pct_change += np.random.normal(loc=0, scale=0.05)

            new_price = max(0.0001, float(price * (1 + pct_change)))
            self.market_data[symbol] = new_price
            self.price_history.setdefault(symbol, deque(maxlen=1000)).append((datetime.utcnow(), new_price))

    def simulate_market_changes(self, steps: Optional[int] = None, interval: Optional[float] = None) -> None:
        """
        Run the market simulation loop. If steps is None, runs indefinitely
        until stop_market_simulation() is called. If steps is provided, runs
        that many simulation ticks.
        """
        if interval is None:
            interval = self.sim_interval

        if steps is None:
            self._simulate_flag.set()
            while self._simulate_flag.is_set():
                self.update_market_data()
                self._check_conditional_orders()
                self._record_portfolio()
                time.sleep(interval)
        else:
            for _ in range(steps):
                self.update_market_data()
                self._check_conditional_orders()
                self._record_portfolio()
                time.sleep(interval)

    def start_market_simulation(self, background: bool = True, interval: Optional[float] = None) -> None:
        """
        Start the background market simulation thread.
        """
        if interval is not None:
            self.sim_interval = float(interval)
        if self.sim_thread and self.sim_thread.is_alive():
            return
        self._simulate_flag.set()
        self.sim_thread = threading.Thread(target=self.simulate_market_changes, kwargs={'steps': None}, daemon=True)
        self.sim_thread.start()

    def stop_market_simulation(self) -> None:
        """
        Stop the background market simulation thread.
        """
        self._simulate_flag.clear()
        if self.sim_thread:
            self.sim_thread.join(timeout=2.0)
            self.sim_thread = None

    # ----------------
    # Market access
    # ----------------
    def get_market_price(self, symbol: str) -> float:
        """
        Fetch current simulated market price for a given symbol.
        Raises KeyError if symbol unknown.
        """
        if symbol not in self.market_data:
            raise KeyError(f"Symbol '{symbol}' not found in market data.")
        return float(self.market_data[symbol])

    def add_symbol(self, symbol: str, price: float) -> None:
        """
        Add a new symbol to the simulated market.
        """
        self.market_data[symbol] = float(price)
        self.price_history.setdefault(symbol, deque(maxlen=1000)).append((datetime.utcnow(), float(price)))

    # ----------------
    # Orders & Trades
    # ----------------
    def _generate_id(self) -> str:
        return uuid.uuid4().hex

    def validate_order(self, symbol: str, order_type: str, quantity: float) -> Tuple[bool, str]:
        """
        Basic validation for orders.
        """
        if order_type not in ('buy', 'sell'):
            return False, "order_type must be 'buy' or 'sell'"
        if quantity <= 0:
            return False, "quantity must be positive"
        if symbol not in self.market_data:
            return False, f"Unknown symbol: {symbol}"
        if order_type == 'sell':
            holding = self.portfolio.get(symbol, {}).get('quantity', 0.0)
            if quantity > holding + 1e-9:
                return False, f"Insufficient holdings to sell: have {holding}, tried to sell {quantity}"
        return True, ""

    def place_order(self, symbol: str, order_type: str, quantity: float, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> str:
        """
        Place a market buy/sell order. Executes immediately at current simulated price.
        If stop_loss or take_profit is provided for a buy, a conditional sell order
        is created to protect/take profit on the position.

        Returns an order id or raises ValueError on invalid input.
        """
        ok, msg = self.validate_order(symbol, order_type, quantity)
        if not ok:
            raise ValueError(msg)

        price = self.get_market_price(symbol)
        order_id = self._generate_id()
        executed_at = datetime.utcnow()

        if order_type == 'buy':
            cost = price * quantity
            if cost > self.cash + 1e-9:
                raise ValueError(f"Insufficient cash: need {cost:.2f}, have {self.cash:.2f}")
            # Update portfolio: compute new average price
            pos = self.portfolio.get(symbol)
            if pos:
                old_qty = pos['quantity']
                old_avg = pos['avg_price']
                new_qty = old_qty + quantity
                new_avg = ((old_avg * old_qty) + (price * quantity)) / new_qty
                pos['quantity'] = new_qty
                pos['avg_price'] = new_avg
            else:
                self.portfolio[symbol] = {'quantity': quantity, 'avg_price': price}
            self.cash -= cost
            self.trade_history.append({'id': order_id, 'symbol': symbol, 'side': 'buy', 'quantity': quantity, 'price': price, 'timestamp': executed_at})

            # Attach conditional orders if SL/TP provided
            if stop_loss is not None or take_profit is not None:
                cond = {
                    'id': self._generate_id(),
                    'symbol': symbol,
                    'side': 'sell',
                    'quantity': quantity,
                    'stop_loss': float(stop_loss) if stop_loss is not None else None,
                    'take_profit': float(take_profit) if take_profit is not None else None,
                    'status': 'open',
                    'created_at': executed_at,
                }
                self.conditional_orders.append(cond)
                return f"buy executed at {price:.2f}; conditional order created (id={cond['id']})"

            return f"buy executed at {price:.2f} (id={order_id})"

        else:  # sell
            # Reduce holdings and calculate realized P/L
            pos = self.portfolio.get(symbol)
            if not pos or pos['quantity'] < quantity - 1e-9:
                raise ValueError("Insufficient holdings to sell")
            avg_price = pos['avg_price']
            proceeds = price * quantity
            realized = (price - avg_price) * quantity
            pos['quantity'] -= quantity
            if pos['quantity'] <= 1e-9:
                del self.portfolio[symbol]
            self.cash += proceeds
            self.realized_pnl += realized
            self.trade_history.append({'id': order_id, 'symbol': symbol, 'side': 'sell', 'quantity': quantity, 'price': price, 'timestamp': executed_at, 'realized_pnl': realized})
            return f"sell executed at {price:.2f} (id={order_id}); realized P/L {realized:.2f}"

    def _execute_conditional_sell(self, cond: Dict[str, Any]) -> Optional[str]:
        """
        Execute a conditional sell order when triggered.
        """
        if cond['status'] != 'open':
            return None
        symbol = cond['symbol']
        quantity = cond['quantity']
        # Ensure we still have the quantity to sell (partial fills not implemented)
        holding_qty = self.portfolio.get(symbol, {}).get('quantity', 0.0)
        if holding_qty <= 0:
            cond['status'] = 'cancelled'
            cond['cancelled_at'] = datetime.utcnow()
            return None
        exec_qty = min(holding_qty, quantity)
        price = self.get_market_price(symbol)
        avg_price = self.portfolio[symbol]['avg_price']
        proceeds = price * exec_qty
        realized = (price - avg_price) * exec_qty
        self.portfolio[symbol]['quantity'] -= exec_qty
        if self.portfolio[symbol]['quantity'] <= 1e-9:
            del self.portfolio[symbol]
        self.cash += proceeds
        self.realized_pnl += realized
        cond['status'] = 'triggered'
        cond['triggered_at'] = datetime.utcnow()
        trade_id = self._generate_id()
        self.trade_history.append({'id': trade_id, 'symbol': symbol, 'side': 'sell', 'quantity': exec_qty, 'price': price, 'timestamp': cond['triggered_at'], 'realized_pnl': realized, 'triggered_by': cond['id']})
        return f"Conditional sell executed for {symbol} at {price:.2f}, qty {exec_qty}, realized {realized:.2f}"

    def _check_conditional_orders(self) -> None:
        """
        Check all open conditional orders against the latest prices and execute
        those that meet stop-loss or take-profit criteria.
        """
        for cond in list(self.conditional_orders):
            if cond['status'] != 'open':
                continue
            symbol = cond['symbol']
            price = self.market_data.get(symbol)
            if price is None:
                continue
            triggered = False
            if cond['stop_loss'] is not None and price <= cond['stop_loss']:
                triggered = True
            if cond['take_profit'] is not None and price >= cond['take_profit']:
                triggered = True
            if triggered:
                msg = self._execute_conditional_sell(cond)
                # leave record updated in cond

    # ----------------
    # Portfolio & P/L
    # ----------------
    def calculate_profit_loss(self) -> float:
        """
        Calculate total profit/loss: realized + unrealized
        """
        unrealized = 0.0
        for symbol, pos in self.portfolio.items():
            cur_price = self.market_data.get(symbol, 0.0)
            unrealized += (cur_price - pos['avg_price']) * pos['quantity']
        total = float(self.realized_pnl + unrealized)
        return total

    def _record_portfolio(self) -> None:
        """
        Record current portfolio equity (cash + market value of positions)
        """
        market_value = sum(self.market_data[symbol] * pos['quantity'] for symbol, pos in self.portfolio.items())
        equity = self.cash + market_value
        self.portfolio_history.append((datetime.utcnow(), equity))

    def get_portfolio(self) -> Dict[str, Any]:
        """
        Return a snapshot of the portfolio including positions, cash, realized
        and unrealized P/L, and total equity.
        """
        positions = {s: {'quantity': round(d['quantity'], 8), 'avg_price': float(d['avg_price']), 'market_price': float(self.market_data.get(s, 0.0)), 'market_value': float(self.market_data.get(s, 0.0) * d['quantity']), 'unrealized_pnl': float((self.market_data.get(s, 0.0) - d['avg_price']) * d['quantity'])} for s, d in self.portfolio.items()}
        unrealized = sum(p['unrealized_pnl'] for p in positions.values())
        realized = float(self.realized_pnl)
        market_value = sum(p['market_value'] for p in positions.values())
        equity = float(self.cash + market_value)
        return {
            'cash': float(self.cash),
            'positions': positions,
            'realized_pnl': realized,
            'unrealized_pnl': float(unrealized),
            'total_pnl': float(realized + unrealized),
            'equity': equity,
            'open_conditionals': [c for c in self.conditional_orders if c['status'] == 'open'],
            'trade_history': list(self.trade_history[-50:]),
        }

    def get_dashboard(self) -> Dict[str, Any]:
        """
        Return a simple dashboard summary.
        """
        md = {s: float(p) for s, p in self.market_data.items()}
        pf = self.get_portfolio()
        return {
            'market': md,
            'portfolio': pf,
            'timestamp': datetime.utcnow().isoformat(),
        }

    # ----------------
    # Charts
    # ----------------
    def _figure_to_bytes(self, fig) -> bytes:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def get_price_chart(self, symbol: str, last_n: int = 200) -> bytes:
        """
        Generate a PNG image (bytes) of the price history for a symbol.
        """
        if symbol not in self.price_history:
            raise KeyError(f"Symbol '{symbol}' not found in price history")
        hist = list(self.price_history[symbol])[-last_n:]
        if not hist:
            raise ValueError("No price history for symbol")
        times, prices = zip(*hist)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(times, prices, marker='.', linestyle='-')
        ax.set_title(f"{symbol} Price History")
        ax.set_xlabel('Time')
        ax.set_ylabel('Price')
        fig.autofmt_xdate()
        return self._figure_to_bytes(fig)

    def get_portfolio_chart(self, last_n: int = 200) -> bytes:
        """
        Generate a PNG image (bytes) of the portfolio equity over time.
        """
        hist = list(self.portfolio_history)[-last_n:]
        if not hist:
            raise ValueError("No portfolio history recorded")
        times, equity = zip(*hist)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(times, equity, marker='o')
        ax.set_title('Portfolio Equity Over Time')
        ax.set_xlabel('Time')
        ax.set_ylabel('Equity')
        fig.autofmt_xdate()
        return self._figure_to_bytes(fig)

    # ----------------
    # Utilities
    # ----------------
    def list_symbols(self) -> List[str]:
        return list(self.market_data.keys())

    def get_open_conditionals(self) -> List[Dict[str, Any]]:
        return [c for c in self.conditional_orders if c['status'] == 'open']


# Basic quick demonstration when module run directly (not required for library use)
if __name__ == '__main__':
    engine = TraidingEngine(seed=42)
    print('Initial dashboard:')
    print(engine.get_dashboard())
    print('\nPlacing a buy order for 1 AAPL with SL and TP...')
    print(engine.place_order('AAPL', 'buy', 1.0, stop_loss=140.0, take_profit=160.0))
    # Run a few simulation ticks and show updates
    engine.simulate_market_changes(steps=5, interval=0.2)
    print('\nAfter simulation:')
    print(engine.get_dashboard())
    # Generate charts into bytes and show size
    pchart = engine.get_price_chart('AAPL')
    print(f'Generated AAPL chart bytes: {len(pchart)} bytes')
    bchart = engine.get_portfolio_chart()
    print(f'Generated portfolio chart bytes: {len(bchart)} bytes')