import os, ccxt, time
from datetime import datetime
API_KEY = os.getenv('BINGX_API_KEY')
SECRET = os.getenv('BINGX_SECRET_KEY')
exchange = ccxt.bingx({'apiKey': API_KEY, 'secret': SECRET, 'options': {'defaultType': 'swap'}})

def get_rsi(sym):
    try:
        ohlcv = exchange.fetch_ohlcv(sym, '15m', limit=100)
        closes = [c[4] for c in ohlcv]
        g, l = [], []
        for i in range(1, len(closes)):
            d = closes[i]-closes[i-1]
            g.append(max(d,0)); l.append(max(-d,0))
        ag = sum(g[-14:])/14; al = sum(l[-14:])/14
        if al==0: return 70
        return 100 - (100/(1+ag/al))
    except: return 50

print("START", datetime.now())
usdt = exchange.fetch_balance()['USDT']['free']
poses = [p for p in exchange.fetch_positions() if p.get('contracts') and float(p['contracts'])>0]
print(f"Solde {usdt} Positions {len(poses)}")

# GESTION EXISTANTES
for p in poses:
    pnl = float(p['percentage'] or 0)
    sym = p['symbol']
    print(f"{sym} PnL {pnl:.2f}%")
    # Si +1.5% on passe en BE (SL a l'entry)
    if pnl >= 1.5:
        try:
            entry = float(p['entryPrice'])
            side = 'sell' if p['side']=='long' else 'buy'
            qty = float(p['contracts'])
            sl = float(exchange.price_to_precision(sym, entry))
            exchange.create_order(sym, 'stop', side, qty, None, {'stopPrice': sl})
            print(f"BE pose {sym}")
        except: pass

if len(poses) < 2 and usdt > 5:
    tickers = exchange.fetch_tickers()
    coins = [s for s in tickers if ':USDT' in s and tickers[s]['last'] and tickers[s]['last']<3 and 'GOLD' not in s and 'NASDAQ' not in s]
    coins = sorted(coins, key=lambda x: tickers[x]['quoteVolume'] or 0, reverse=True)[:35]
    for sym in coins:
        if any(p['symbol']==sym for p in poses): continue
        rsi = get_rsi(sym)
        sig = 'buy' if rsi<38 else 'sell' if rsi>62 else None
        if not sig: continue
        print(f"SIGNAL {sig} {sym} RSI {rsi:.1f}")
        try:
            price = exchange.fetch_ticker(sym)['last']
            qty = float(exchange.amount_to_precision(sym, (usdt*0.35)/price))
            exchange.create_market_order(sym, sig, qty)
            print(f"ORDRE OK {sym}")
            time.sleep(2)
            sl = price*0.92 if sig=='buy' else price*1.08
            sl = float(exchange.price_to_precision(sym, sl))
            side = 'sell' if sig=='buy' else 'buy'
            exchange.create_order(sym, 'stop', side, qty, None, {'stopPrice': sl})
            print(f"SL -8% {sl}")
            break
        except Exception as e:
            print(f"Err {sym} {e}")
            continue
print("DONE")
