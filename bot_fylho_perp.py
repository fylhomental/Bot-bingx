import ccxt, os, pandas as pd, time
print("=== FYLHO V2.3 FINAL ===")
API_KEY=os.getenv('BINGX_API_KEY')
SECRET=os.getenv('BINGX_SECRET_KEY')
ex=ccxt.bingx({'apiKey':API_KEY,'secret':SECRET,'options':{'defaultType':'swap'},'enableRateLimit':True})
try: ex.set_position_mode(False)
except: pass
mkts=ex.load_markets()
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
perps=[s for s in mkts if '/USDT:USDT' in s and 'NCS' not in s]
top=sorted(perps,key=lambda s:tick.get(s,{}).get('quoteVolume',0) or 0,reverse=True)[:60]
opened=0
MAX_OPEN=2
for sym in top:
    if opened>=MAX_OPEN: break
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
        # SL/TP direct dans l'ordre = plus d'erreur 110424
        sl_price = price*0.95 if side=='LONG' else price*1.05
        tp_price = price*1.10 if side=='LONG' else price*0.90
        sl_price=ex.price_to_precision(sym,sl_price)
        tp_price=ex.price_to_precision(sym,tp_price)
        params={
            'positionSide':'BOTH',
            'stopLoss':{'type':'STOP_MARKET','stopPrice':sl_price},
            'takeProfit':{'type':'TAKE_PROFIT_MARKET','stopPrice':tp_price}
        }
        ex.create_market_order(sym,oside,float(qty),params=params)
        print(f"OPEN {side} {sym} SL {sl_price} TP {tp_price} OK")
        opened+=1
        time.sleep(2)
    except Exception as e:
        print(f"Err {sym} {e}")

print(f"FIN - {opened} positions ouvertes")