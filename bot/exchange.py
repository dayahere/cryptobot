import ccxt, time
from utils.logger import get_logger
log=get_logger('exchange')

def build_exchange(name, key=None, secret=None, password=None, sandbox=False):
    klass = getattr(ccxt, name)
    opts = {'enableRateLimit': True, 'options': {'adjustForTimeDifference': True}}
    if name=='binance':
        opts['options'].update({'recvWindow': 5000})
    if key and secret: opts.update({'apiKey': key, 'secret': secret})
    if password: opts.update({'password': password})
    ex = klass(opts)
    if sandbox and hasattr(ex,'set_sandbox_mode'):
        ex.set_sandbox_mode(True)
    try:
        ex.load_markets()
    except Exception as e:
        log.warning(f"load_markets failed: {e}")
    return ex

def amount_to_precision(ex, symbol, amount):
    try:
        return ex.amount_to_precision(symbol, amount)
    except Exception:
        return amount

def price_to_precision(ex, symbol, price):
    try:
        return ex.price_to_precision(symbol, price)
    except Exception:
        return price


def fetch_ohlcv_safe(ex, symbol, timeframe='1m', limit=500):
    for _ in range(5):
        try:
            return ex.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except Exception as e:
            log.warning(f"fetch_ohlcv retry due to {e}"); time.sleep(1)
    raise