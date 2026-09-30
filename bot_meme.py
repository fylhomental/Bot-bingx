import ccxt, os, json, time
import pandas as pd

API_KEY = os.getenv("BINGX_API_KEY")
API_SECRET = os.getenv("BINGX_SECRET_KEY")
AMOUNT_USDT = 5
TP_PCT = 30.0
SL_PCT = 15.0
MEM_FILE = "bot_meme_memory.json"
MEME_KEYWORDS = ["DOGE","SHIB","PEPE","BONK","WIF","FLOKI","MEME","BABY","BOME","MEW","POPCAT","BRETT","MOG","TURBO","LADYS","WOJAK","COQ","MYRO","WEN","PONKE","PEPE2","PORK","CAT","DOG","FROG","INU"]

def get_rsi(s, ex):
    try:
        ohlcv = ex.fetch_ohlcv(s, '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain/loss
        return float((100 - (100/(1+rs))).iloc[-1])
    except: return 50

ex = ccxt.bingx({'apiKey': API_KEY, 'secret': API_SECRET, 'options': {'defaultType': 'spot'}})
mem = json.load(open(MEM_FILE)) if os.path.exists(MEM_FILE) else {}

tickers = ex.fetch_tickers()
balances = ex.fetch_balance()
holdings = {k: v for k, v in balances.items() if isinstance(v, dict) and v.get('free',0) > 0}

all_memes = []
for sym, t in tickers.items():
    if '/USDT' in sym and ':USDT' not in sym:
        base = sym.split('/')[0].upper()
        if any(k in base for k in MEME_KEYWORDS):
            all_memes.append((sym, t.get('quoteVolume',0)))

print(f"CHASSEUR MEME FIX - {len(all_memes)} MEMES - Deja possede: {list(holdings.keys())[:10]}")

for sym, vol in all_memes:
    try:
        base = sym.split('/')[0]
        if base in holdings:
            # Si tu possedes deja plus de 1$ de ce coin, on skip
            try:
                val = holdings[base]['free'] * ex.fetch_ticker(sym)['last']
                if val > 1:
                    print(f"{sym} deja en portefeuille {val:.2f}$ -> SKIP")
                    continue
            except: pass
        if sym in mem:
            continue

        rsi = get_rsi(sym, ex)
        price = ex.fetch_ticker(sym)['last']
        print(f"{sym} RSI {rsi:.1f} Prix {price}")

        if rsi < 35:
            qty = AMOUNT_USDT / price
            order = ex.create_order(sym, 'market', 'buy', qty, None, {'quoteOrderQty': AMOUNT_USDT})
            print(f"ACHAT {sym} pour {AMOUNT_USDT}$")
            time.sleep(0.8)
            # On recupere la quantite reelle
            bal2 = ex.fetch_balance()
            qty_real = bal2[base]['free'] if base in bal2 else qty

            tp = price * (1 + TP_PCT/100)
            sl = price * (1 - SL_PCT/100)
            try:
                ex.create_limit_sell_order(sym, qty_real, tp)
                ex.create_order(sym, 'STOP_LOSS_LIMIT', 'sell', qty_real, sl, {'stopPrice': sl})
                print(f"TP/SL pose {sym} TP {tp} SL {sl}")
            except Exception as e:
                print(f"Erreur TP/SL {sym}: {e}")

            mem[sym] = {"entry": price, "rsi": rsi}
            time.sleep(0.5)
    except Exception as e:
        print(f"Err {sym}: {e}")

with open(MEM_FILE, 'w') as f:
    json.dump(mem, f, indent=2)
