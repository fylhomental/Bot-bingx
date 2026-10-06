import os, ccxt, time
from datetime import datetime
API_KEY=os.getenv('BINGX_API_KEY')
SECRET=os.getenv('BINGX_SECRET_KEY')
ex=ccxt.bingx({'apiKey':API_KEY,'secret':SECRET,'options':{'defaultType':'swap'}})
ex.load_markets()

def get_rsi(sym):
    try:
        ohlcv=ex.fetch_ohlcv(sym,'15m',limit=100)
        c=[x[4] for x in ohlcv]
        g=[];l=[]
        for i in range(1,len(c)):
            d=c[i]-c[i-1]
            g.append(max(d,0));l.append(max(-d,0))
        ag=sum(g[-14:])/14; al=sum(l[-14:])/14
        if al==0: return 70
        rs=ag/al
        return 100-(100/(1+rs))
    except: return 50

print("START",datetime.now())
usdt=ex.fetch_balance()['USDT']['free']
poses=[p for p in ex.fetch_positions() if float(p.get('contracts',0))>0]
print(f"Solde {usdt:.2f} Positions {len(poses)}")

# Si position existe -> on pose le SL dessus
for p in poses:
    sym=p['symbol']
    side='sell' if p['side']=='long' else 'buy'
    qty=float(p['contracts'])
    entry=float(p.get('entryPrice',0) or ex.fetch_ticker(sym)['last'])
    sl=entry*0.92 if p['side']=='long' else entry*1.08
    print(f"Pose SL pour {sym} entry {entry} sl {sl}")
    try:
        # Methode BingX correcte
        ex.create_order(sym,'stop_market',side,qty,None,{'stopPrice':sl})
        print(f"SL OK {sym} {sl}")
    except Exception as e:
        print(f"SL err1 {e}")
        try:
            ex.create_order(sym,'market',side,qty,None,{'stopPrice':sl,'type':'STOP_MARKET'})
            print(f"SL OK2 {sl}")
        except Exception as e2:
            print(f"SL err2 {e2}")

# Si 0 position, on ouvre 1 seule
if len(poses)==0 and usdt>5:
    ticks=ex.fetch_tickers()
    coins=[s for s in ticks if ':USDT' in s and ticks[s]['last'] and ticks[s]['last']<5 and 'GOLD' not in s]
    coins=sorted(coins,key=lambda x:ticks[x]['quoteVolume'] or 0,reverse=True)[:50]
    print(f"Scan {len(coins)} coins")
    for sym in coins:
        if any(p['symbol']==sym for p in poses): continue
        rsi=get_rsi(sym)
        sig='buy' if rsi<35 else 'sell' if rsi>68 else None
        if not sig: continue
        print(f"SIGNAL {sig} {sym} RSI {rsi:.1f}")
        try:
            price=ex.fetch_ticker(sym)['last']
            qty=float(ex.amount_to_precision(sym,(usdt*0.40)/price))
            ex.create_market_order(sym,sig,qty)
            print(f"ORDRE OK {sym} qty {qty}")
            time.sleep(2)
            sl=price*0.92 if sig=='buy' else price*1.08
            ex.create_order(sym,'stop_market','sell' if sig=='buy' else 'buy',qty,None,{'stopPrice':sl})
            print(f"SL OK {sl}")
            break
        except Exception as e:
            print(f"Err {sym} {e}")
            break
print("DONE")
