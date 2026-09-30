import ccxt, os, json, time
import pandas as pd

API_KEY = os.getenv("BINGX_API_KEY")
API_SECRET = os.getenv("BINGX_SECRET_KEY")

LEV = 20
AMOUNT_USDT = 36.70
TP_ROE = 30.0  # +30% ROE
SL_ROE = 15.0  # -15% ROE
MEM_FILE = "bot_perp_memory.json"

# Liste PERP
SYMBOLS = ["BTC/USDT:USDT","ETH/USDT:USDT","SOL/USDT:USDT","INJ/USDT:USDT","TAO/USDT:USDT","AVAX/USDT:USDT","ARB/USDT:USDT"]

def get_rsi(sym, ex):
    try:
        ohlcv = ex.fetch_ohlcv(sym, '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        delta = df['c'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        return float((100 - (100 / (1 + rs))).iloc[-1])
    except: return 50

ex = ccxt.bingx({
    'apiKey': API_KEY, 
    'secret': API_SECRET,
    'options': {'defaultType': 'swap'}
})

print(f"=== CHASSEUR PERP {LEV}x - TP {TP_ROE}% ROE / SL {SL_ROE}% ROE ===")

positions = ex.fetch_positions()
open_syms = [p['symbol'] for p in positions if float(p.get('contracts',0)) > 0]
print(f"Positions ouvertes: {open_syms}")

# 1. Si tu as deja INJ ouvert sans TP/SL -> on le corrige direct
for p in positions:
    if float(p.get('contracts',0)) == 0: continue
    sym = p['symbol']
    entry = float(p['entryPrice'])
    side = p['side'] # long / short
    qty = float(p['contracts'])
    
    print(f"CORRECTION TP/SL pour {sym} entry {entry}")
    tp_price = entry * (1 + TP_ROE/100/LEV) if side == 'long' else entry * (1 - TP_ROE/100/LEV)
    sl_price = entry * (1 - SL_ROE/100/LEV) if side == 'long' else entry * (1 + SL_ROE/100/LEV)

    try:
        # BingX V2 : on pose 2 ordres reduceOnly
        if side == 'long':
            ex.create_order(sym, 'limit', 'sell', qty, tp_price, {'reduceOnly': True})
            ex.create_order(sym, 'stop', 'sell', qty, sl_price, {'stopPrice': sl_price, 'reduceOnly': True})
        else:
            ex.create_order(sym, 'limit', 'buy', qty, tp_price, {'reduceOnly': True})
            ex.create_order(sym, 'stop', 'buy', qty, sl_price, {'stopPrice': sl_price, 'reduceOnly': True})
        print(f"TP/SL POSE {sym} TP {tp_price:.4f} SL {sl_price:.4f}")
    except Exception as e:
        print(f"Erreur TP/SL {sym}: {e}")

# 2. Cherche nouvelles entrees
for sym in SYMBOLS:
    if sym in open_syms: continue
    try:
        r
