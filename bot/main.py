import time
import datetime as dt
import pandas as pd

from config import *
from exchange import build_exchange, fetch_ohlcv_safe
from strategy.momentum_meanrev import compute_indicators, final_signal, classify_outcome
from strategy.risk import position_size
from utils.logger import get_logger
from utils.metrics import start_server, account_equity, heartbeat, cooldown_active
from utils.notifier import send_email
from live.trader import PaperBroker, place_order

log = get_logger('main')


def to_df(ohlcv):
    """Convert raw OHLCV list to a cleaned DataFrame."""
    if not ohlcv:
        return pd.DataFrame(columns=['ts', 'open', 'high', 'low', 'close', 'vol'])

    df = pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
    df['ts'] = pd.to_datetime(df['ts'], unit='ms', errors='coerce')
    for c in ('open', 'high', 'low', 'close', 'vol'):
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['vol'] = df['vol'].rolling(20, min_periods=1).mean().bfill()
    df = df.dropna(subset=['ts', 'close']).reset_index(drop=True)
    return df


def safe_get_last_numeric(df, key):
    """Return numeric value for key in last row or raise ValueError."""
    if df.empty:
        raise ValueError("empty dataframe")
    last = df.iloc[-1]
    val = last.get(key)
    if pd.isna(val):
        raise ValueError(f"{key} is NaN")
    if isinstance(val, pd.Timestamp):
        raise ValueError(f"{key} is Timestamp")
    return float(val)


def main():
    start_server()

    ex = None if PAPER else build_exchange(EXCHANGE, API_KEY, API_SECRET, API_PASSWORD, sandbox=False)
    broker = PaperBroker(balance=1000.0) if PAPER else None

    equity = 1000.0
    day_start = dt.datetime.utcnow().date()
    start_equity = equity
    cooldown = False

    while True:
        heartbeat.set(time.time())

        # reset daily counters at UTC midnight
        if dt.datetime.utcnow().date() != day_start:
            day_start = dt.datetime.utcnow().date()
            start_equity = equity
            cooldown = False
            cooldown_active.set(0)

        # daily drawdown check
        try:
            if start_equity > 0 and (equity - start_equity) / start_equity * 100 <= -DAILY_LOSS_LIM:
                if not cooldown:
                    cooldown = True
                    cooldown_active.set(1)
                    send_email("Cooldown activated", f"Daily loss limit {DAILY_LOSS_LIM}% hit. Pausing new trades.")
        except Exception:
            log.exception("error checking daily drawdown")

        if cooldown:
            time.sleep(10)
            continue

        for sym in SYMBOLS:
            try:
                tmp_ex = ex if ex is not None else build_exchange(EXCHANGE)
                ohlcv = fetch_ohlcv_safe(tmp_ex, sym, TIMEFRAME, 500)
                df = to_df(ohlcv)
                if df.empty:
                    log.warning(f"{sym}: no valid OHLCV rows; skipping")
                    continue

                df = compute_indicators(df)

                # Coerce all non-ts columns to numeric to avoid Timestamp issues in final_signal
                for col in df.columns:
                    if col != 'ts':
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                df = df.dropna(subset=['ts', 'close']).reset_index(drop=True)
                if df.empty:
                    log.warning(f"{sym}: df became empty after coercion; skipping")
                    continue

                # Compute signal safely
                try:
                    df['signal'] = df.apply(final_signal, axis=1)
                except Exception as e:
                    log.error(f"{sym}: final_signal failed, filling with 'hold': {e}")
                    df['signal'] = 'hold'

                if 'signal' not in df.columns:
                    log.error(f"{sym}: no 'signal' column after final_signal; skipping")
                    continue

                try:
                    classify_outcome(df, horizon=10, symbol=sym)
                except Exception:
                    log.exception(f"{sym}: classify_outcome failed")

                last = df.iloc[-1]
                log.debug(f"{sym} last dtypes: {df.dtypes.to_dict()}")
                log.debug(f"{sym} last values: {last.to_dict()}")

                try:
                    price = safe_get_last_numeric(df, 'close')
                    atr = safe_get_last_numeric(df, 'atr')
                except ValueError as e:
                    log.error(f"{sym} skipping due to bad numeric field: {e}")
                    continue

                side = last.get('signal', None)
                if side not in ('buy', 'sell'):
                    continue

                qty = position_size(equity, atr, price, RISK_ATR, BASE, MAX_NOTIONAL)
                if qty <= 0:
                    continue

                ok = True
                if PAPER:
                    if side == 'buy':
                        broker.buy(price, qty, sym)
                    else:
                        broker.sell(price, qty, sym)
                    equity = broker.balance + broker.pos * price
                else:
                    ok = place_order(ex, side, sym, qty, None)

                account_equity.set(equity)
                if ok:
                    try:
                        send_email(f"Trade {side} {sym}", f"qty={qty} price={price} paper={PAPER}")
                    except Exception as e:
                        log.error(f"Email send failed: {e}")
                    log.info(f"Placed {side} {qty} {sym} @ {price}")

            except Exception:
                log.exception(f"{sym} loop error")
        time.sleep(10)


if __name__ == '__main__':
    main()