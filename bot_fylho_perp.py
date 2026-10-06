import os, ccxt, time
from datetime import datetime

API_KEY = os.getenv('BINGX_API_KEY')
SECRET = os.getenv('BINGX_SECRET_KEY')

exchange = ccxt.bingx({
    'apiKey': API_KEY,
    'secret': SECRET,
    'options': {'defaultType': 'swap'}
})

def get_rsi(sym):
    try:
        ohlcv = exchange.fetch_ohlcv(sym, '15m', limit=100)
        closes = [c[4] for c in ohlcv]
        g, l = [], []
        for i in range(1, len(closes)):
            d = closes[i]-closes[i-1]
            g.append(max(d,0))
            l.append(max(-d,0))
        ag = sum(g[-14:])/14
        al = sum(l[-14:])/14
        if al == 0: return 70
        return 100 - (100/(1+ag/al))
    except:
        return 50

print("START", datetime.now())
bal = exchange.fetch_balance()
usdt = bal['USDT']['free']
print(f"Solde {usdt}")

pos = [p for p in exchange.fetch_positions() if p.get('contracts') and float(p['contracts'])>0]
print(f"Positions {len(pos)}")

# Si déjà 1 position on ne rouvre pas
if len(pos) >= 2:
    print("Deja 2 positions, on ne touche pas")
else:
    tickers = exchange.fetch_tickers()
    coins = []
    for s in tickers:
        if ':USDT' not in s: continue
        if any(x in s for x in ['GOLD','NASDAQ','NCCO']): continue
        if tickers[s]['last'] and tickers[s]['last'] < 2:
            coins.append(s)
    coins = sorted(coins, key=lambda x: tickers[x]['quoteVolume'] or 0, reverse=True)[:25]

    for sym in coins:
        if any(p['symbol']==sym for p in pos): continue
        rsi = get_rsi(sym)
        print(f"{sym} RSI {rsi:.1f}")
        sig = None
        if rsi < 40: sig = 'buy'
        if rsi > 65: sig = 'sell'
        if not sig: continue

        print(f"SIGNAL {sig} {sym}")
        try:
            price = exchange.fetch_ticker(sym)['last']
            qty = (usdt * 0.8) / price
            qty = float(exchange.amount_to_precision(sym, qty))

            # OUVERTURE
            exchange.create_market_order(sym, sig, qty)
            print(f"ORDRE OK {sym} qty {qty}")
            time.sleep(2)

            # SL -8% direct sur prix, pas besoin de fetch position
            sl = price * 0.92 if sig == 'buy' else price * 1.08
            sl = float(exchange.price_to_precision(sym, sl))
            side = 'sell' if sig == 'buy' else 'buy'
            try:
                exchange.create_order(sym, 'stop', side, qty, None, {'stopPrice': sl})
                print(f"SL -8% pose a {sl}")
            except Exception as e:
                print(f"SL info {e}")

            break # 1 SEUL ordre par run
        except Exception as e:
            print(f"Err {sym} {e}")
            continue

print("DONE")
