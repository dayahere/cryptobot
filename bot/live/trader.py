from utils.logger import get_logger
from utils.metrics import orders_placed, orders_filled, trade_pnl, api_errors
log=get_logger('trader')

class PaperBroker:
    def __init__(self, balance=1000.0):
        self.balance=balance; self.pos=0.0; self.avg=0.0
    def buy(self, price, qty, symbol):
        cost = price*qty; self.balance-=cost; 
        self.avg=(self.avg*self.pos+cost)/(self.pos+qty) if self.pos+qty>0 else price
        self.pos+=qty; orders_filled.labels(symbol,'buy').inc(); return price
    def sell(self, price, qty, symbol):
        proceeds=price*qty
        if self.pos>0 and self.avg>0:
            trade_pnl.observe((price-self.avg)/self.avg)
        self.balance+=proceeds; self.pos-=qty; orders_filled.labels(symbol,'sell').inc()
        return price

def place_order(ex, side, symbol, qty, price=None):
    orders_placed.labels(symbol, side, 'market' if price is None else 'limit').inc()
    if ex is None: return True
    try:
        if price is None:
            ex.create_order(symbol,'market',side,qty)
        else:
            ex.create_limit_order(symbol,side,qty,price)
        return True
    except Exception as e:
        api_errors.labels('create_order').inc()
        log.error(f"Order error: {e}"); return False