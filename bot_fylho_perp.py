import os, ccxt, time
from datetime import datetime

API_KEY = os.getenv('BINGX_API_KEY')
SECRET = os.getenv('BINGX_SECRET_KEY')

exchange = ccxt.bingx({
    'apiKey': API_KEY,
    'secret': SECRET,
    'options': {'defaultType': 'swap'}
})
exchange.load_markets()

def get_rsi(sym):
    try:
        ohlcv = exchange.fetch_ohlcv(sym, '15m', limit=100)
        closes = [c[4] for c in ohlcv]
        g, l = [], []
        for i in range(1, len(closes)):
            d = closes[i]-closes[i-1]
            g.append(max(d,0)); l.append(max(-d,0))
        ag = sum(g[-14:])/14; al = sum(l[-14:])/14
        if al == 0: return 70
        return 100 - (100/(1+ag/al))
    except: return 50

print("START", datetime.now())
bal = exchange.fetch_balance()
usdt = bal['USDT']['free']
poses = [p for p in exchange.fetch_positions() if p.get('contracts') and float(p['contracts'])>0]
print(f"Solde {usdt} Positions {len(poses)}")

if len(poses) >= 1:
    print("Deja en position, on stop")
else:
    tickers = exchange.fetch_tickers()
    coins = []
    for s in tickers:
        if ':USDT' not in s: continue
        if any(x in s for x in ['GOLD','NASDAQ','NCCO']): continue
        last = tickers[s]['last']
        if last and last < 3:
            coins.append(s)
    coins = sorted(coins, key=lambda x: tickers[x]['quoteVolume'] or 0, reverse=True)[:30]
    print(f"Scan {len(coins)} memes")

    for sym in coins:
        rsi = get_rsi(sym)
        print(f"{sym} RSI {rsi:.1f}")
        sig = None
        if rsi < 38: sig = 'buy'
        if rsi > 62: sig = 'sell'
        if not sig: continue

        print(f"SIGNAL {sig} {sym}")
        try:
            price = exchange.fetch_ticker(sym)['last']
            qty = (usdt * 0.4) / price
            qty_str = exchange.amount_to_precision(sym, qty)
            qty = float(qty_str)
            print(f"Tentative {sym} qty {qty}")
            exchange.create_market_order(sym, sig, qty)
            print(f"ORDRE OK {sym} - FIN DU RUN")
            break # STOP ICI, 1 seul par run
        except Exception as e:
            print(f"Err {sym} {e}")
            continue

print("DONE")