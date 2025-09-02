# utils/metrics.py
from prometheus_client import Counter, Gauge, Histogram, start_http_server
import os, time

METRICS_PORT = int(os.getenv('METRICS_PORT', '9101'))

# --- Existing metrics ---
orders_placed = Counter('orders_placed_total', 'Total orders placed', ['symbol', 'side', 'type'])
orders_filled = Counter('orders_filled_total', 'Total orders filled', ['symbol', 'side'])
trade_pnl = Histogram('trade_pnl_r', 'R multiple per trade',
                      buckets=[-5, -3, -2, -1, -0.5, 0, 0.5, 1, 2, 3, 5])
slippage_bps = Histogram('slippage_bps', 'Execution slippage in bps',
                         buckets=[-50, -20, -10, -5, -3, -1, 0, 1, 3, 5, 10, 20, 50])
account_equity = Gauge('account_equity', 'Account equity in quote currency')
api_errors = Counter('api_errors_total', 'Exchange API errors', ['endpoint'])
heartbeat = Gauge('bot_heartbeat_seconds', 'Epoch seconds heartbeat')
cooldown_active = Gauge('cooldown_active', '1 when daily loss limit hit, else 0')

signal_tp = Counter('signal_true_positives', 'Signals correctly predicting direction', ['symbol'])
signal_fp = Counter('signal_false_positives', 'Signals incorrectly predicting direction', ['symbol'])
signal_fn = Counter('signal_false_negatives', 'Missed moves', ['symbol'])

# --- New daily performance metrics ---
# These reset naturally in Grafana queries by grouping on day(timestamp)
trades_won = Counter('trades_won_total', 'Number of profitable trades', ['symbol', 'side'])
trades_lost = Counter('trades_lost_total', 'Number of losing trades', ['symbol', 'side'])
trades_breakeven = Counter('trades_breakeven_total', 'Number of breakeven trades', ['symbol', 'side'])

# Total realised PnL in quote currency (can be negative)
realised_pnl = Counter('realised_pnl_total', 'Cumulative realised PnL in quote currency', ['symbol', 'side'])

# Rolling PnL gauge (e.g., reset daily in your bot logic)
daily_pnl = Gauge('daily_pnl', 'Realised PnL for the current day in quote currency')

# --- Helper functions ---
def start_server():
    """Start the Prometheus metrics HTTP server."""
    start_http_server(METRICS_PORT)
    print(f"[metrics] Prometheus metrics server started on port {METRICS_PORT}")

def heartbeat_set(ts: float = None):
    """Update the heartbeat to now or a given timestamp."""
    if ts is None:
        ts = time.time()
    heartbeat.set(ts)

def record_api_error(endpoint: str):
    """Increment API error counter for a given endpoint."""
    api_errors.labels(endpoint=endpoint).inc()

def record_trade(symbol: str, side: str, pnl_value: float):
    """
    Record a completed trade's outcome and PnL.
    side: 'buy' or 'sell'
    pnl_value: realised PnL in quote currency (positive, negative, or zero)
    """
    if pnl_value > 0:
        trades_won.labels(symbol=symbol, side=side).inc()
    elif pnl_value < 0:
        trades_lost.labels(symbol=symbol, side=side).inc()
    else:
        trades_breakeven.labels(symbol=symbol, side=side).inc()

    realised_pnl.labels(symbol=symbol, side=side).inc(pnl_value)
    # Update daily PnL gauge (you can reset this in your bot at midnight)
    daily_pnl.set(daily_pnl._value.get() + pnl_value)