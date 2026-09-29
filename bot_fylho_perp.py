import ccxt, os, pandas as pd, time
print("=== FYLHO V2.2 FIX ===")
API_KEY=os.getenv('BINGX_API_KEY')
SECRET=os.getenv('BINGX_SECRET_KEY')
ex=ccxt.bingx({'apiKey':API_KEY,'secret':SECRET,'options':{'defaultType':'swap'},'enableRateLimit':True})
try: ex.set_position_mode(False)
except: pass
try: mkts=ex.load_markets()
except Exception as e: print(e); exit()
def get_rsi(sym):
    try:
        o=ex.fetch_ohlcv(sym,'1h',limit=100)
        df=pd.DataFrame(o,columns=['t','o','h','l','c','v'])
        d=df['c'].diff()
        g=d.where(d>0,0).rolling(14).mean()
        l=-d.where(d<0,0).rolling(14).mean()
        r=100-(100/(1+g/l))
        return float(r.iloc[-1])
    except: return 50
tick=ex.fetch_tickers()
perps=[s for s in mkts if '/USDT:USDT' in s]
top=sorted(perps,key=lambda s:tick.get(s,{}).get('quoteVolume',0) or 0,reverse=True)[:100]
for sym in top:
    try:
        rsi=get_rsi(sym)
        side=None
        if rsi<35: side='LONG'
        elif rsi>70: side='SHORT'
        if not side: continue
        print(f"SIGNAL {side} {sym} RSI {rsi:.1f}")
        try: ex.set_leverage(5,sym,params={'side':'BOTH'})
        except: pass
        price=ex.fetch_ticker(sym)['last']
        qty=(5*5)/price
        qty=ex.amount_to_precision(sym,qty)
        oside='buy' if side=='LONG' else 'sell'
        ex.create_market_order(sym,oside,float(qty),params={'positionSide':'BOTH'})
        print(f"OPEN {side} {sym} OK")
        time.sleep(1)
        if side=='LONG':
            sl=price*0.95; tp=price*1.10; cside='sell'
        else:
            sl=price*1.05; tp=price*0.90; cside='buy'
        sl=ex.price_to_precision(sym,sl)
        tp=ex.price_to_precision(sym,tp)
        try:
            ex.create_order(sym,'stop_market',cside,float(qty),None,params={'stopPrice':sl,'positionSide':'BOTH'})
            print(f"SL {sl}")
        except Exception as e: print(f"Err SL {e}")
        try:
            ex.create_order(sym,'limit',cside,float(qty),float(tp),params={'positionSide':'BOTH'})
            print(f"TP {tp}")
        except Exception as e: print(f"Err TP {e}")
        time.sleep(1)
    except Exception as e: print(f"Err {sym} {e}")
print("FIN")