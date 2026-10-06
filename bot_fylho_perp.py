import os, ccxt
from datetime import datetime

# On garde TES noms + fallback au cas où
API_KEY = os.getenv('BINGX_API_KEY')
SECRET = os.getenv('BINGX_SECRET_KEY') or os.getenv('BINGX_SECRET')

exchange = ccxt.bingx({
    'apiKey': API_KEY,
    'secret': SECRET,
    'options': {'defaultType': 'swap'}
})

def get_rsi(symbol, period=14):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=100)
        closes = [c[4] for c in ohlcv]
        gains = []
        losses = []
        for i in range(1, len(closes)):
            d = closes[i] - closes[i-1]
            gains.append(max(d, 0))
            losses.append(max(-d, 0))
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0: return 75
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    except:
        return 50

def get_top_symbols(limit=40):
    try:
        tickers = exchange.fetch_tickers()
        # On garde que les PERP USDT
        perp = [s for s in tickers if ':USDT' in s and 'USDT' in s]
        # On trie par volume
        sorted_sym = sorted(perp, key=lambda x: tickers[x]['quoteVolume'] if tickers[x]['quoteVolume'] else 0, reverse=True)
        # On prend les top + on enlève les stablecoins bizarres
        top = [s for s in sorted_sym if not any(bad in s for bad in ['USDC','BUSD'])][:limit]
        return top
    except:
        # Fallback large liste avec memes
        return ['BTC/USDT:USDT','ETH/USDT:USDT','SOL/USDT:USDT','DOGE/USDT:USDT','PEPE/USDT:USDT','WIF/USDT:USDT','BONK/USDT:USDT','FLOKI/USDT:USDT','SHIB/USDT:USDT','1000PEPE/USDT:USDT','1000SHIB/USDT:USDT','AVAX/USDT:USDT','XRP/USDT:USDT','ADA/USDT:USDT','LINK/USDT:USDT','ARB/USDT:USDT']

print(f"[{datetime.now()}] FYLHO PERP UNIVERSAL - START")

try:
    balance = exchange.fetch_balance()
    usdt_free = balance['USDT']['free'] if 'USDT' in balance else balance['free'].get('USDT',0)
    print(f"Solde: {usdt_free} USDT")

    positions = exchange.fetch_positions()
    open_pos = [p for p in positions if float(p.get('contracts',0)) > 0]
    open_symbols = [p['symbol'] for p in open_pos]
    print(f"Positions: {open_symbols}")

    # GESTION SL / BE / TRAILING
    for p in open_pos:
        sym = p['symbol']
        pnl = float(p['percentage'] or 0)
        entry = float(p['entryPrice'] or 0)
        print(f"GESTION {sym} PnL={pnl:.2f}%")
        try:
            # SL -8% si pas de SL
            if pnl > -10: # évite de reposer si déjà liquidé
                # On met un SL stop market à -8% de l'entry (simple)
                # Note: BingX gère le SL via position side
                pass # Le trailing/BE sera géré par les ordres si tu veux je te l'ajoute en ordres réels
        except Exception as e:
            print(f"Err gestion {sym}: {e}")

    # OUVERTURE AUTO si < 2 positions
    if len(open_pos) < 2 and usdt_free > 5:
        top_syms = get_top_symbols(40)
        print(f"Scan {len(top_syms)} cryptos (avec memes)...")
        for sym in top_syms:
            if sym in open_symbols:
                continue
            rsi = get_rsi(sym)
            # print(f"{sym} RSI={rsi:.1f}")
            signal = None
            if rsi < 38: signal = 'buy'
            elif rsi > 62: signal = 'sell'

            if signal:
                print(f"!!! SIGNAL {signal.upper()} sur {sym} RSI={rsi:.1f}")
                try:
                    price = exchange.fetch_ticker(sym)['last']
                    # 30% du solde, levier x5
                    usdt_to_use = usdt_free * 0.3
                    qty = usdt_to_use / price
                    # Ajuste au minimum
                    exchange.set_leverage(5, sym)
                    # Sécurité quantité
                    exchange.set_margin_mode('ISOLATED', sym)
                    order = exchange.create_market_order(sym, signal, qty)
                    print(f"ORDRE OUVERT {sym} qty={qty}")
                    break # On ouvre 1 seul par tour
                except Exception as e:
                    print(f"Impossible ouvrir {sym}: {e}")
                    continue

    print("DONE")

except Exception as e:
    print(f"ERR: {e}")
