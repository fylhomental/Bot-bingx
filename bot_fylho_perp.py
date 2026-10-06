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
        gains = []
        losses = []
        for i in range(1, len(closes)):
            d = closes[i] - closes[i-1]
            if d > 0:
                gains.append(d)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-d)
        ag = sum(gains[-14:]) / 14
        al = sum(losses[-14:]) / 14
        if al == 0:
            return 70
        rs = ag / al
        return 100 - (100 / (1 + rs))
    except:
        return 50

print("START", datetime.now())
bal = exchange.fetch_balance()
usdt = bal['USDT']['free']
print(f"Solde {usdt}")

positions = exchange.fetch_positions()
opens = []
for p in positions:
    if p.get('contracts') and float(p['contracts']) > 0:
        opens.append(p)

print(f"Positions {len(opens)}")

# scan memes only <10$ pour 26$
tickers = exchange.fetch_tickers()
coins = []
for s in tickers:
    if ':USDT' not in s:
        continue
    if 'GOLD' in s or 'NASDAQ' in s or 'NCCO' in s:
        continue
    last = tickers[s]['last']
    if last and last < 2:
        coins.append(s)

coins = sorted(coins, key=lambda x: tickers[x]['quoteVolume'] or 0, reverse=True)[:30]
print(f"Scan {len(coins)} coins")

for sym in coins:
    is_open = False
    for op in opens:
        if op['symbol'] == sym:
            is_open = True
    if is_open:
        continue

    rsi = get_rsi(sym)
    print(f"{sym} RSI {rsi:.1f}")

    sig = None
    if rsi < 40:
        sig = 'buy'
    if rsi > 65:
        sig = 'sell'
    if sig is None:
        continue

    print(f"SIGNAL {sig} {sym}")
    try:
        price = exchange.fetch_ticker(sym)['last']
        qty = (usdt * 0.9) / price
        qty = float(exchange.amount_to_precision(sym, qty))
        order = exchange.create_market_order(sym, sig, qty)
        print(f"ORDRE OK {sym}")
        time.sleep(3)
        # SL -8%
        entry = 0
        for np in exchange.fetch_positions([sym]):
            if float(np.get('contracts',0)) > 0:
                entry = float(np.get('entryPrice',0))
        if entry > 0:
            sl = entry * 0.92 if sig == 'buy' else entry * 1.08
            sl = float(exchange.price_to_precision(sym, sl))
            side = 'sell' if sig == 'buy' else 'buy'
            exchange.create_order(sym, 'stop', side, qty, None, {'stopPrice': sl})
            print(f"SL pose {sl}")
        break
    except Exception as e:
        print(f"Err {sym} {e}")
        continue

print("DONE")