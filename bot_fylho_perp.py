import os, ccxt, time
from datetime import datetime

API_KEY = os.getenv('BINGX_API_KEY')
SECRET = os.getenv('BINGX_SECRET_KEY') or os.getenv('BINGX_SECRET')

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
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except:
        return 50

def get_top():
    try:
        tickers = exchange.fetch_tickers()
        lst = [s for s in tickers if ':USDT' in s]
        lst = sorted(lst, key=lambda x: tickers[x]['quoteVolume'] or 0, reverse=True)
        lst = [s for s in lst if 'USDC' not in s][:45]
        return lst
    except:
        return ['BTC/USDT:USDT','ETH/USDT:USDT','SOL/USDT:USDT','DOGE/USDT:USDT','PEPE/USDT:USDT','WIF/USDT:USDT','BONK/USDT:USDT','FLOKI/USDT:USDT','SHIB/USDT:USDT','XRP/USDT:USDT']

print("START BOT UNIVERSE MEME + SL REEL")
print(datetime.now())

try:
    bal = exchange.fetch_balance()
    usdt = bal['USDT']['free']
    print(f"Solde {usdt}")

    pos_all = exchange.fetch_positions()
    opens = []
    for p in pos_all:
        contracts = p.get('contracts')
        if contracts and float(contracts) > 0:
            opens.append(p)

    print(f"Positions {len(opens)}")

    if len(opens) < 2 and usdt > 5:
        top = get_top()
        for sym in top:
            already = False
            for op in opens:
                if op['symbol'] == sym:
                    already = True
            if already:
                continue

            rsi = get_rsi(sym)
            sig = None
            if rsi < 38:
                sig = 'buy'
            if rsi > 62:
                sig = 'sell'
            if sig is None:
                continue

            print(f"SIGNAL {sig} {sym} RSI {rsi}")

            try:
                ticker = exchange.fetch_ticker(sym)
                price = ticker['last']
                use = usdt * 0.35
                qty = use / price
                qty = float(exchange.amount_to_precision(sym, qty))

                exchange.set_leverage(5, sym)
                order = exchange.create_market_order(sym, sig, qty)
                print(f"ORDRE OK {sym}")
                time.sleep(3)

                # Pose SL reel -8%
                new_pos = exchange.fetch_positions([sym])
                entry_price = 0
                for np in new_pos:
                    if float(np.get('contracts',0)) > 0:
                        entry_price = float(np.get('entryPrice',0))

                if entry_price > 0:
                    if sig == 'buy':
                        sl = entry_price * 0.92
                        close_side = 'sell'
                    else:
                        sl = entry_price * 1.08
                        close_side = 'buy'
                    sl = float(exchange.price_to_precision(sym, sl))
                    try:
                        exchange.create_order(sym, 'stop', close_side, qty, None, {'stopPrice': sl})
                        print(f"SL -8% pose a {sl}")
                    except Exception as e:
                        print(f"SL err {e}")

                break
            except Exception as e:
                print(f"Err {sym} {e}")
                continue

    print("DONE")

except Exception as e:
    print(f"ERR {e}")
