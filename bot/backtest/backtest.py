import pandas as pd

def run_backtest(df, fee_bps=7):
    pos=0; cash=10000; eq=10000; avg=0
    for i in range(1,len(df)):
        sig=df['signal'].iloc[i-1]; px=float(df['close'].iloc[i])
        if sig=='buy' and pos<=0:
            qty= (eq*0.01)/px; pos+=qty; avg=px*(1+fee_bps/1e4); cash-=qty*avg
        elif sig=='sell' and pos>0:
            cash+=pos*px*(1-fee_bps/1e4); pos=0
        eq=cash+pos*px
    return eq