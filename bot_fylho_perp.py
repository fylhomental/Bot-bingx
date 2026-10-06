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
        gains, losses = [], []
        for i in range(1, len(closes)):
            d = closes[i]-closes[i-1]
            gains.append(max(d,0))
            losses.append(max(-d,0))
        ag = sum(gains[-14:])/14
        al = sum(losses[-14:])/14
        if al == 0: return 70
        rs = ag/al
        return 100 - (100/(1+rs))
    except:
        return 50

def get_top():
    try:
        tickers = exchange.fetch_tickers()
        lst = []
        for s in tickers:
            if ':USDT' not in s: continue
            if any(x in s for x in ['GOLD','NASDAQ','NCCO','NCSI','SPX','DJI']): continue
            # On garde que les petites cryptos < 10$ pour ton solde 26$
            price = tickers[s]['last']
            if price and price < 10:
                lst.append(s)
        lst = sorted(lst, key=lambda x: tickers[x]['quoteVolume'] or 0, reverse=True)
        return lst[:40]
    except:
        return ['DOGE/USDT:USDT','PEPE/USDT:USDT','1000PEPE/USDT:USDT','BONK/USDT:USDT','WIF/USDT:USDT','FLOKI/USDT:USDT','SHIB/USDT:USDT','1000SHIB/USDT:USDT','MEME/USDT:USDT','ORDI/USDT:USDT']

print(f"START BOT 26$ MEME ONLY {datetime.now()}")
bal = exchange.fetch_balance()
usdt = bal['USDT']['free']
print(f"Solde {usdt}")

pos_all = exchange.fetch_positions()
opens = [p for p in pos_all if p.get('contracts') and float(p['contracts'])>0]
print(f"Positions {len(opens)}")

try:
    if len(opens) < 2 and usdt > 5:
        top = get_top()
        print(f"Scan {len(top)} memes <10$")
        for sym in top:
            if any(op['symbol']==sym for op in opens):
                continue
            rsi = get_rsi(sym)
            print(f"{sym} RSI {rsi:.1f}")
            sig = None
            if rsi < 40: sig = 'buy'
            if rsi > 65: sig = 'sell'
            if sig is None: continue

            print(f"SIGNAL {sig} {sym}")
            try:
                ticker = exchange.fetch_ticker(sym)
                price = ticker['last']
                use = usdt * 0.9 # on utilise 90% pour les memes car pas cher
                qty = use / price
                qty = float(exchange.amount_to_precision(sym, qty))

                # On ne touche plus au levier pour eviter l'erreur, ton levier par defaut sur BingX est deja 5-10x
                order = exchange.create_market_order(sym, sig, qty)
                print(f"ORDRE OK {sym} qty {qty}")
                time.sleep(3)

                # SL -8% reel
                new_pos = exchange.fetch_positions([sym])
                entry_price = 0
                for np in new_pos:
                    if float(np.get('contracts',0))>0:
                        entry_price = float(np.get('entryPrice',0))
                        break

                if entry_price > 0:
                    if sig == 'buy':
                        sl = entry_price * 0.92
                        close_side = 'sell'
                    else:
