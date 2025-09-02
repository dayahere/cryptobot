def position_size(equity, atr, price, risk_pct=0.5, base_quote='USDT', max_notional=100.0):
    if atr<=0: return 0
    notional = min(max_notional, equity * (risk_pct/100.0))
    qty = notional / price
    return round(qty, 6)