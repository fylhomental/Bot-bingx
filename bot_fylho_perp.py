import ccxt, os, pandas as pd, time
print("=== FYLHO V2.7 32USDT 4x7 ===")
API_KEY=os.getenv('BINGX_API_KEY')
SECRET=os.getenv('BINGX_SECRET_KEY')
ex=ccxt.bingx({'apiKey':API_KEY,'secret':SECRET,'options':{'defaultType':'swap'},'enableRateLimit':True})
try: ex.set_position_mode(False)
except: pass
mkts=ex.load_markets()

bal=ex.fetch_balance()
free=bal.get('USDT',{}).get('free',0)
print(f"Solde Futures Total: {free:.2f} USDT")

positions=ex.fetch_positions()
open_pos=[p for p in positions if float(p.get('contracts',0))>0]
print(f"Positions ouvertes: {len(open_pos)}")
open_syms=[p['symbol'] for p in open_pos]
for p in open_pos:
    print(f" - {p['symbol']} {p['side']} {p['contracts']} PnL {float(p.get('unrealizedPnl',0)):.2f}")

MAX_POS=4
TRADE_USDT=7

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
perps=[s for s in mkts if '/USDT:USDT' in s and 'NCS' not in s and 'USDC' not in s and 'BABY' not in s]
top=sorted(perps,key=lambda s:tick.get(s,{}).get('quoteVolume',0) or 0,reverse=True)[:80]

opened=0
for sym in top:
    if opened>=2: break
    if sym in open_syms: continue
    try:
        rsi=get_rsi(sym)
        side=None
        if rsi<32: side='LONG'
        elif rsi>70: side='SHORT'
        if not side: continue
        print(f"SIGNAL {side} {sym} RSI {rsi:.1f}")

        bal=ex.fetch_balance()
        free=bal.get('USDT',{}).get('free',0)

        if (free < 7.5 or len(open_pos) >= MAX_POS) and open_pos:
            oldest=sorted(open_pos,key=lambda x: x.get('timestamp',0))[0]
            print(f"RECYCLAGE {oldest['symbol']} PnL {float(oldest.get('unrealizedPnl',0)):.2f}")
            close_side='sell' if oldest['side']=='long' else 'buy'
            ex.create_market_order(oldest['symbol'],close_side,float(oldest['contracts']),params={'positionSide':'BOTH','reduceOnly':True})
            print(f"FERME {oldest['symbol']}")
            time.sleep(3)
            positions=ex.fetch_positions()
            open_pos=[p for p in positions if float(p.get('contracts',0))>0]
            open_syms=[p['symbol'] for p in open_pos]

        bal=ex.fetch_balance()
        if bal['USDT']['free'] < 7.5:
            print(f"Solde bas {bal['USDT']['free']:.2f} FIN")
            break

        try:
            ex.set_leverage(5,sym,params={'side':'BOTH'})
            ex.set_margin_mode('ISOLATED',sym,params={'side':'BOTH'})
        except: pass

        price=ex.fetch_ticker(sym)['last']
        qty=(TRADE_USDT*5)/price
        qty=ex.amount_to_precision(sym,qty)
        if float(qty)==0: continue
        oside='buy' if side=='LONG' else 'sell'
        sl=price*0.95 if side=='LONG' else price*1.05
        tp=price*1.10 if side=='LONG' else price*0.90
        sl=ex.price_to_precision(sym,sl)
        tp=ex.price_to_precision(sym,tp)
        params={'positionSide':'BOTH','stopLoss':{'stopPrice':sl},'takeProfit':{'stopPrice':tp}}
        ex.create_market_order(sym,oside,float(qty),params=params)
        print(f"OPEN {side} {sym} 7USDT x5 SL {sl} TP {tp}")
        opened+=1
        time.sleep(2)

    except Exception as e:
        print(f"Err {sym} {e}")

print("FIN RUN")