import pandas as pd, numpy as np
from ta.volatility import AverageTrueRange
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from strategy.ai.model import load_pretrained, FEATURE_ORDER
from utils.metrics import signal_tp, signal_fp, signal_fn


def compute_indicators(df):
    df['ema_fast'] = EMAIndicator(df['close'], window=20).ema_indicator()
    df['ema_slow'] = EMAIndicator(df['close'], window=50).ema_indicator()
    atr = AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
    df['atr'] = pd.to_numeric(atr, errors='coerce')  # Ensure atr is numeric
    df['ret1'] = df['close'].pct_change().fillna(0)
    df['z'] = (df['close'] - df['close'].rolling(20).mean()) / (df['close'].rolling(20).std() + 1e-9)
    df['rsi'] = RSIIndicator(df['close'], window=14).rsi().fillna(50)
    df['vol'] = pd.to_numeric(df['vol'], errors='coerce')  # Ensure vol is numeric
    df['vol'] = df['vol'].rolling(20).mean().bfill()
    return df


def model_signal(row):
    model = load_pretrained()
    if model is None:
        return None

    safe_feats = []
    for k in FEATURE_ORDER:
        val = row.get(k, 0.0)
        # Convert Timestamp to numeric seconds if needed
        if isinstance(val, pd.Timestamp):
            val = val.timestamp()
        # Coerce to float, replacing bad values with 0.0
        try:
            val = float(val)
        except (TypeError, ValueError):
            val = 0.0
        safe_feats.append(val)

    feats = np.array(safe_feats, dtype=float)
    try:
        y = model.predict(feats.reshape(1, -1))[0]
    except Exception as e:
        # If model prediction fails, log and return flat
        print(f"model_signal error: {e}")
        return 'flat'

    return 'buy' if y == 1 else 'sell'


def rule_signal(row):
    mom = 1 if (row.ema_fast>row.ema_slow) else -1
    meanrev = -1 if row.z>2 else (1 if row.z<-2 else 0)
    score = mom*0.6 + meanrev*0.4
    if score>0.5: return 'buy'
    if score<-0.5: return 'sell'
    return 'flat'


def final_signal(row):
    try:
        ms = model_signal(row)
        rs = rule_signal(row)
        if ms is None:
            return rs
        return ms if ms == rs else 'flat'
    except Exception as e:
        print(f"final_signal error: {e}")
        return 'flat'


def classify_outcome(df, horizon=10, symbol=''):
    if len(df)<horizon+1: return
    sig=df.iloc[-(horizon+1)]
    future = df['close'].iloc[-1]/sig['close']-1
    if sig['signal']=='buy':
        (signal_tp if future>0 else signal_fp).labels(symbol).inc()
    elif sig['signal']=='sell':
        (signal_tp if future<0 else signal_fp).labels(symbol).inc()
    else:
        if abs(future)>0.01: signal_fn.labels(symbol).inc()