import os, ccxt, time
from datetime import datetime
API_KEY=os.getenv('BINGX_API_KEY')
SECRET=os.getenv('BINGX_SECRET_KEY')
ex=ccxt.bingx({'apiKey':API_KEY,'secret':SECRET,'options':{'defaultType':'swap'}})
ex.load_markets()

def set_leverage(sym, lev=3):
    try:
        ex.set_leverage(lev, sym)
    except:
        pass
    try:
        ex.set_margin_mode('CROSSED', sym)
    except:
        pass

def get_rsi(sym):
    try:
        ohlcv=ex.fetch_ohlcv(sym,'15m',limit=100)
        c=[x[4] for x in ohlcv]
        g=[];l=[]
        for i in range(1,len(c)):
            d=c[i]-c[i-1]
            g.append(max(d,0));l.append(max(-d,0))
        ag=sum(g[-14:])/14
        al=sum(l[-14:])/14
        if al==0:
            return 70
        rs=ag/al
        return 100-(100/(1+rs))
    except:
        return 50

print("START",datetime.now())
usdt=ex.fetch_balance()['USDT']['free']
poses=[p for p in ex.fetch_positions() if float(p.get('contracts',0))>0]
print(f"Solde {usdt:.2f} Positions {len(poses)}")

if len(poses)>=1:
    print("1 position max, on attend")
else:
    if usdt>5:
        ticks=ex.fetch_tickers()
        coins=[s for s in ticks if ':USDT' in s and ticks[s]['last'] and ticks[s]['last']<5 and 'GOLD' not in s]
        coins=sorted(coins,key=lambda x:ticks[x]['quoteVolume'] or 0,reverse=True)[:50]
        print(f"Scan {len(coins)}")
        for sym in coins:
            rsi=get_rsi(sym)
            sig='buy' if rsi<32 else 'sell' if rsi>70 else None
            if not sig:
                continue
            print(f"SIGNAL {sig} {sym} RSI {rsi:.1f}")
            try:
                set_leverage(sym,3)
                price=ex.fetch_ticker(sym)['last']
                qty=float(ex.amount_to_precision(sym,(usdt*0.35)/price))
                ex.create_market_order(sym,sig,qty)
                print(f"ORDRE OK {sym} 3x qty {qty}")
                time.sleep(3)
                sl=price*0.88 if sig=='buy' else price*1.12
                try:
                    ex.create_order(sym,'stop_market','sell' if sig=='buy' else 'buy',qty,None,{'stopPrice':sl})
                    print(f"SL OK {sl}")
                except Exception as e:
                    print(f"SL err {e} mais 3x safe")
                break
            except Exception as e:
                print(f"Err {sym} {e}")
                break
print("DONE")
