import ccxt, os, json, time
import pandas as pd

API_KEY = os.getenv("BINGX_API_KEY")
API_SECRET = os.getenv("BINGX_SECRET_KEY")
AMOUNT_USDT = 5
TP_PCT = 30.0
SL_PCT = 15.0
MEM_FILE = "bot_meme_memory.json"
MEME_KEYWORDS = ["DOGE","SHIB","PEPE","BONK","WIF","FLOKI","MEME","BABY","BOME","MEW","POPCAT","BRETT","MOG","TURBO","LADYS","WOJAK","COQ","MYRO","WEN","PONKE"]

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
# On récupère ton solde réel pour ne pas racheter si tu as déjà
holdings = {k: v for k, v in balances.items() if v.get('free', 0) > 0}

all_memes = []
for sym, t in tickers.items():
    if '/USDT' in sym and ':USDT' not in sym:
        base = sym.split('/')[0]
        if any(k in base.upper() for k in MEME_KEYWORDS):
            all_memes.append((sym, t.get('quoteVolume',0)))

print(f"=== CHASSEUR MEME FIX - {len(all_memes)} MEMES - Solde déjà détenu: {list(holdings.keys())} ===")

for sym, vol in all_memes:
    try:
        base = sym.split('/')[0]
        # FIX 1: Si tu as déjà ce coin sur BingX (même 1$), on SKIP, on ne rachète pas
        if base in holdings and holdings[base]['free'] * ex.fetch_ticker(sym)['last'] > 1:
            print(f"{sym} déjà détenu, SKIP")
            continue
        if sym in mem: # double sécurité
            continue

        rsi = get_rsi(sym, ex)
        price = ex.fetch_ticker(sym)['last']
        print(f"{sym} RSI {rsi:.1f}")

        if rsi < 35:
            qty = AMOUNT_USDT / price
            # FIX 2: on force le coût en USDT, pas en quantité de coin
            ex.create_order(sym, 'market', 'buy', qty, None, {'quoteOrderQty': AMOUNT_USDT})
            print(f"ACHAT {sym} pour {AMOUNT_USDT}$")
            mem[sym] = {"entry": price}
            time.sleep(0.5)
    except Exception as e:
        print(f"Err {sym}: {e}")

with open(MEM_FILE, 'w') as f: json.dump(mem, f, indent=2)
