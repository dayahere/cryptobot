import os
from dotenv import load_dotenv; load_dotenv()

EXCHANGE = os.getenv('EXCHANGE','binance')
SYMBOLS = [s.strip() for s in os.getenv('SYMBOLS','BTC/USDT').split(',')]
TIMEFRAME = os.getenv('TIMEFRAME','1m')
PAPER = os.getenv('PAPER_TRADING','true').lower()=='true'
API_KEY = os.getenv('API_KEY'); API_SECRET=os.getenv('API_SECRET')
API_PASSWORD=os.getenv('API_PASSWORD')
BASE=os.getenv('BASE_CURRENCY','USDT')
MAX_NOTIONAL=float(os.getenv('MAX_NOTIONAL_PER_TRADE','100'))
DAILY_LOSS_LIM=float(os.getenv('DAILY_LOSS_LIMIT_PCT','2'))
RISK_ATR=float(os.getenv('RISK_TARGET_ATR_PCT','0.5'))