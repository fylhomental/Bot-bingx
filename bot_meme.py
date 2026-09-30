import ccxt, os, json, time
import pandas as pd

API_KEY = os.getenv("BINGX_API_KEY")
API_SECRET = os.getenv("BINGX_SECRET_KEY")
AMOUNT_USDT = 5
TP_PCT = 30.0
SL_PCT = 15.0
MEM_FILE = "bot_meme_memory.json"

# Mots clés pour détecter un meme (on attrape tous les nouveaux memes auto)
MEME_KEYWORDS = ["DOGE","SHIB","PEPE","BONK","WIF","FLOKI","MEME","BABY","BOME","MEW","POPCAT","BRETT","MOG","TURBO","LADYS","WOJAK","COQ","MYRO","WEN","PONKE","PEPE2","PORK","PEPECOIN","CAT","DOG","FROG","INU","ELON","AIDOGE","SAMO","HOGE"]

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

ex.load_markets()
tickers = ex.fetch_tickers()

# 1. On récupère TOUS les memes dispo sur BingX SPOT
all_memes = []
for sym, t in tickers.items():
    if '/USDT' in sym and ':USDT' not in sym: # que du SPOT
        base = sym.split('/')[0].upper()
        if any(k in base for k in MEME_KEYWORDS):
            all_memes.append((sym, t.get('quoteVolume',0)))

# 2. On ajoute aussi le TOP 100 plus tradé (pour choper les nouveaux memes qui n'ont pas de mot clé)
top_volume = []
for sym, t in tickers.items():
    if '/USDT' in sym and ':USDT' not in sym and t.get('quoteVolume'):
        if t['quoteVolume'] > 500000: # +500k volume = actif
            # On exclut BTC, ETH, SOL etc
            if sym.split('/')[0] not in ["BTC","ETH","SOL","BNB","XRP","ADA","AVAX","DOT","LINK","MATIC","LTC","BCH","NEAR","APT","ARB","OP"]:
                top_volume.append((sym, t['quoteVolume']))

top_volume.sort(key=lambda x: x[1], reverse=True)
# On prend Top 50 volume hors gros coins = souvent des memes/new coins
for sym, vol in top_volume[:50]:
    if sym not in [x[0] for x in all_memes]:
        all_memes.append((sym, vol))

print(f"=== CHASSEUR MEME UNIVERSAL - {len(all_memes)} MEMES DETECTES ===")
print([x[0] for x in all_memes[:20]])

# 3. Scan RSI de tous les memes détectés
for sym, vol in all_memes:
    try:
        rsi = get_rsi(sym, ex)
        price = ex.fetch_ticker(sym)['last']
        print(f"{sym} Vol {int(vol)} RSI {rsi:.1f}")
        if rsi < 35 and sym not in mem:
            qty = AMOUNT_USDT / price
            ex.create_market_buy_order(sym, qty)
            try:
                bal = ex.fetch_balance()
                coin = sym.split('/')[0]
                qty_real = bal[coin]['free']
            except:
                qty_real = qty
            tp = price * (1 + TP_PCT/100)
            sl = price * (1 - SL_PCT/100)
            try:
                ex.create_limit_sell_order(sym, qty_real, tp)
                ex.create_order(sym, 'STOP_LOSS_LIMIT', 'sell', qty_real, sl, {'stopPrice': sl})
                print(f"TP/SL posé {sym} TP {tp} SL {sl}")
            except Exception as e: print(f"TP/SL err {sym}: {e}")
            mem[sym] = {"entry": price, "rsi": rsi}
        time.sleep(0.15)
    except Exception as e:
        print(f"Err {sym}: {e}")

with open(MEM_FILE, 'w') as f: json.dump(mem, f, indent=2)
