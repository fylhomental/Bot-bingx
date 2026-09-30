import ccxt, os, time, json
import pandas as pd

API_KEY = os.getenv("BINGX_API_KEY")
API_SECRET = os.getenv("BINGX_SECRET_KEY")

LEV = 5
AMOUNT_USDT = 5
TP_ROE = 40.0
SL_ROE = 20.0
MAX_POS = 5

MEMES = ["DOGE/USDT:USDT","SHIB/USDT:USDT","PEPE/USDT:USDT","BONK/USDT:USDT","WIF/USDT:USDT","FLOKI/USDT:USDT","BOME/USDT:USDT","POPCAT/USDT:USDT","MOG/USDT:USDT","BRETT/USDT:USDT"]

MEM_FILE = "bot_perp_memory.json"

def get_rsi(sym, ex):
    try:
        ohlcv = ex.fetch_ohlcv(sym, '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        delta = df['c'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    except:
        return 50

ex = ccxt.bingx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'options': {'defaultType': 'swap'}
})

print(f"CHASSEUR MEME {LEV}x {AMOUNT_USDT}$ TP {TP_ROE}% SL {SL_ROE}%")

try:
    positions = ex.fetch_positions()
    open_syms = []
    for p in positions:
        if float(p.get('contracts', 0)) == 0:
            continue
        sym = p['symbol']
        if sym not in MEMES:
            continue
        open_syms.append(sym)
        
        # Securise les positions existantes si TP/SL manquant
        try:
            orders = ex.fetch_open_orders(sym)
            if len(orders) < 2:
                entry = float(p['entryPrice'])
                side = p['side']
                qty = float(p['contracts'])
                tp_price = entry * (1 + TP_ROE/100/LEV) if side == 'long' else entry * (1 - TP_ROE/100/LEV)
                sl_price = entry * (1 - SL_ROE/100/LEV) if side == 'long' else entry * (1 + SL_ROE/100/LEV)
                if side == 'long':
                    ex.create_order(sym, 'limit', 'sell', qty, tp_price, {'reduceOnly': True})
                    ex.create_order(sym, 'stop', 'sell', qty, sl_price, {'stopPrice': sl_price, 'reduceOnly': True})
                else:
                    ex.create_order(sym, 'limit', 'buy', qty, tp_price, {'reduceOnly': True})
                    ex.create_order(sym, 'stop', 'buy', qty, sl_price, {'stopPrice': sl_price, 'reduceOnly': True})
                print(f"TP/SL POSE {sym}")
            else:
                print(f"TP/SL deja pose {sym}, skip")
        except Exception as e:
            print(f"Err TP/SL {sym}: {e}")

    print(f"Positions MEME ouvertes ({len(open_syms)}/{MAX_POS}): {open_syms}")

    if len(open_syms) >= MAX_POS:
        print("MAX atteint, pas de nouvel achat")
    else:
        # Scan RSI du plus bas au plus haut
        all_rsi = []
        for sym in MEMES:
            if sym in open_syms:
               
