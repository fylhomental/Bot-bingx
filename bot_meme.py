import os, ccxt, requests, pandas as pd, time

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")
API_KEY = os.getenv("BINGX_API_KEY")
SECRET = os.getenv("BINGX_SECRET") or os.getenv("BINGX_SECRET_KEY") or os.getenv("BINGX_API_SECRET")

AMOUNT_USDT = 5
MAX_POS = 20
RSI_THRESHOLD = 35

# VRAIS MEMES SEULEMENT
MEMES = [
    "DOGE/USDT","SHIB/USDT","PEPE/USDT","BONK/USDT","WIF/USDT",
    "FLOKI/USDT","ORDI/USDT","BOME/USDT","POPCAT/USDT","MOG/USDT",
    "BRETT/USDT","MEME/USDT","TURBO/USDT","LADYS/USDT","PENGU/USDT"
]
VRAIS_MEMES_COINS = [s.split('/')[0] for s in MEMES] # ['DOGE','SHIB',...]

def tg(msg):
    try:
        if TOKEN and CHAT:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT, "text": msg}, timeout=15)
    except: pass

def get_rsi(closes, period=14):
    delta = closes.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rsi = 100 - (100 / (1 + gain/loss))
    return float(rsi.iloc[-1])

print(f"CHASSEUR SPOT SECURISE {AMOUNT_USDT}$ max {MAX_POS} coins (memes uniquement)")

try:
    ex = ccxt.bingx({'apiKey': API_KEY,'secret': SECRET,'enableRateLimit': True})
    bal = ex.fetch_balance()
    free_usdt = bal.get('USDT',{}).get('free',0) if isinstance(bal.get('USDT'), dict) else 0

    # Tous tes coins en spot
    all_owned = [k for k,v in bal.items() if isinstance(v, dict) and v.get('total',0)>0 and k not in ['USDT','info','free','used','total']]
    # On ne compte QUE les vrais memes pour le 20 max
    owned_meme = [c for c in all_owned if c in VRAIS_MEMES_COINS]

    print(f"Tous en Spot: {all_owned}")
    print(f"Deja en Spot (memes): {owned_meme} ({len(owned_meme)}/{MAX_POS})")

    scans, achats, erreurs = [], [], []

    for sym in MEMES:
        coin = sym.split('/')[0]
        if coin in owned_meme:
            scans.append(f"{sym} deja possede")
            continue
        try:
            ohlcv = ex.fetch_ohlcv(sym,'1d',limit=50)
            closes = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])['c']
            rsi = get_rsi(closes)
            scans.append(f"{sym} RSI {rsi:.1f}")
            print(f"{sym} RSI {rsi:.1f}")

            if rsi < RSI_THRESHOLD and len(owned_meme) < MAX_POS and free_usdt >= AMOUNT_USDT:
                price = ex.fetch_ticker(sym)['last']
                qty = AMOUNT_USDT / price
                print(f"ACHAT SPOT {sym} RSI {rsi:.1f}")
                ex.create_market_buy_order(sym, qty)
                owned_meme.append(coin)
                achats.append(f"{sym} RSI {rsi:.1f}")
                time.sleep(1)
        except Exception as e:
            erreurs.append(f"{sym}: {e}")

    msg = f"🚀 Chasseur Meme du jour - {len(owned_meme)}/{MAX_POS} (memes uniquement)\n"
    msg += f"Spot memes: {owned_meme}\n"
    msg += f"Spot total: {all_owned}\n"
    msg += f"Solde SPOT: {free_usdt:.2f} USDT\n\n"
    msg += f"{'✅ Achats: '+', '.join(achats) if achats else 'Aucun achat (RSI > 35)'}\n\n"
    msg += "📊 Scan:\n" + "\n".join(scans)

    if erreurs and "100202" in str(erreurs):
        msg += "\n\n👉 100202 = transfere USDT Futures -> Spot"

    tg(msg)

except Exception as e:
    print(f"Erreur: {e}")
    tg(f"⚠️ Erreur chasseur meme: {e}")
