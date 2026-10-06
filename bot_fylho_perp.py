import os, ccxt, time
from datetime import datetime

API_KEY = os.getenv('BINGX_API_KEY')
SECRET = os.getenv('BINGX_SECRET_KEY') or os.getenv('BINGX_SECRET')

exchange = ccxt.bingx({
    'apiKey': API_KEY,
    'secret': SECRET,
    'options': {'defaultType': 'swap'}
})

def get_rsi(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=100)
        closes = [c[4] for c in ohlcv]
        gains, losses = [], []
        for i in range(1, len(closes)):
            d = closes[i]-closes[i-1]
            gains.append(max(d,0))
            losses.append(max(-d,0))
        avg_gain = sum(gains[-14:])/14
        avg_loss = sum(losses[-14:])/14
        if avg_loss == 0: return 75
        rs = avg_gain/avg_loss
        return 100 - (100/(1+rs))
    except: return 50

def get_top_symbols(limit=45):
    try:
        tickers = exchange.fetch_tickers()
        perp = [s for s in tickers if ':USDT' in s]
        sorted_sym = sorted(perp, key=lambda x: tickers[x]['quoteVolume'] or 0, reverse=True)
        top = [s for s in sorted_sym if not any(b in s for b in ['USDC','BUSD'])][:limit]
        return top
    except:
        return ['BTC/USDT:USDT','ETH/USDT:USDT','SOL/USDT:USDT','DOGE/USDT:USDT','PEPE/USDT:USDT','WIF/USDT:USDT','BONK/USDT:USDT','FLOKI/USDT:USDT','SHIB/USDT:USDT','1000PEPE/USDT:USDT','1000SHIB/USDT:USDT','AVAX/USDT:USDT','XRP/USDT:USDT','ARB/USDT:USDT','LINK/USDT:USDT','MEME/USDT:USDT','ORDI/USDT:USDT']

print(f"[{datetime.now()}] FYLHO UNIVERSE MEME + SL REEL START")

try:
    balance = exchange.fetch_balance()
    usdt_free = balance['USDT']['free']
    print(f"Solde: {usdt_free:.2f} USDT")

    positions = exchange.fetch_positions()
    open_pos = [p for p in positions if float(p.get('contracts',0)) > 0]
    open_syms = [p['symbol'] for p in open_pos]
    print(f"Positions ouvertes: {open_syms}")

    # Si 0-1 position -> cherche nouvelle entrée
    if len(open_pos) < 2 and usdt_free > 5:
        top = get_top_symbols(45)
        print(f"Scan {len(top)} coins avec memes...")
        for sym in top:
            if sym in open_syms: continue
            rsi = get_rsi(sym)
            signal = None
            if rsi < 38: signal = 'buy'
            elif rsi > 62: signal = 'sell'
            if not signal: continue

            print(f"SIGNAL {signal.upper()} {sym} RSI={rsi:.1f}")
            try:
                price = exchange.fetch_ticker(sym)['last']
                usdt_use = usdt_free * 0.35 # 35% de 26$ ~ 9$
                qty = usdt_use / price
                qty = float(exchange.amount_to_precision(sym, qty))

                exchange.set_leverage(5, sym)
                try: exchange.set_margin_mode('ISOLATED', sym)
                except: pass

                # OUVERTURE MARCHE
                order = exchange.create_market_order(sym, signal, qty)
                print(f"Ouvert {sym} {signal} qty={qty}")
                time.sleep(2)

                # RECUPERE PRIX D'ENTREE REEL
                pos = [p for p in exchange.fetch_positions([sym]) if float(p.get('contracts',0))>0]
                if not pos: continue
                entry = float(pos
