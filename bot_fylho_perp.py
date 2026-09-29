import ccxt, os, pandas as pd, time
print("=== FYLHO V2.5 12USDT FIX ===")
API_KEY=os.getenv('BINGX_API_KEY')
SECRET=os.getenv('BINGX_SECRET_KEY')
ex=ccxt.bingx({'apiKey':API_KEY,'secret':SECRET,'options':{'defaultType':'swap'},'enableRateLimit':True})
try: ex.set_position_mode(False)
except: pass
mkts=ex.load_markets()
bal=ex.fetch_balance()
free=bal.get('USDT',{}).get('free',0)
print(f"Solde Futures: {free} USDT")
if free < 5:
    print("SOLDE TROP BAS - depose ou ferme positions")
    exit()
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
perps=[s for s in mkts if '/USDT:USDT' in s and 'NCS' not in s and 'USDC' not in s]
top=sorted(perps,key=lambda s:tick.get(s,{}).get('quoteVolume',0) or 0,reverse=True)[:50]
for sym in top:
    try:
        rsi=get_rsi(sym)
        side=None
        if rsi<32: side='LONG'
        elif rsi>73: side='SHORT'
        if not side: continue
        print(f"SIGNAL {side} {sym} RSI {rsi:.1f}")
        # verif solde encore OK
        bal=ex.fetch_balance()
        if bal['USDT']['free'] < 4.5:
            print("Plus assez pour ouvrir, FIN")
            break
        try:
            ex.set_leverage(5,sym,params={'side':'BOTH'})
            ex.set_margin_mode('ISOLATED',sym,params={'side':'BOTH'})
        except: pass
        price=ex.fetch_ticker(sym)['last']
        qty=(4*5)/price  # 4 USDT de marge au lieu de 5
        qty=ex.amount_to_precision(sym,qty)
        oside='buy' if side=='LONG' else 'sell'
        sl=price*0.95 if side=='LONG' else price*1.05
        tp=price*1.10 if side=='LONG' else price*0.90
        sl=ex.price_to_precision(sym,sl)
        tp=ex.price_to_precision(sym,tp)
        params={'positionSide':'BOTH','stopLoss':{'stopPrice':sl},'takeProfit':{'stopPrice':tp}}
        ex.create_market_order(sym,oside,float(qty),params=params)
        print(f"OPEN {side} {sym} 4USDT OK -> reste {bal['USDT']['free']-4:.2f} USDT")
        break # on ouvre 1 seule par run
    except Exception as e:
        print(f"Err {sym} {e}")

print("FIN")