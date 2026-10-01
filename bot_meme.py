import ccxt, os, json, time
import pandas as pd

API_KEY = os.getenv("BINGX_API_KEY")
API_SECRET = os.getenv("BINGX_SECRET_KEY")
AMOUNT_USDT = 5
MAX_POS = 20

MEMES = ["DOGE/USDT","SHIB/USDT","PEPE/USDT","BONK/USDT","WIF/USDT","FLOKI/USDT","ORDI/USDT","BOME/USDT","POPCAT/USDT","MOG/USDT","BRETT/USDT","MEME/USDT","TURBO/USDT","LADYS/USDT"]

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
    'options': {'defaultType': 'spot'}
})

print(f"CHASSEUR SPOT SECURISE {AMOUNT_USDT}$ max {MAX_POS} coins")

# 1. Vrai solde SPOT = securité anti-doublon
try:
    bal = ex.fetch_balance()
    owned = []
    for coin in [s.split('/')[0] for s in MEMES]:
        if bal.get(coin, {}).get('total', 0) > 0.0001:
            owned.append(coin)
    print(f"Deja en Spot: {owned} ({len(owned)}/{MAX_POS})")

    if len(owned) >= MAX_POS:
        print("MAX SPOT atteint, stop")
        exit()

    for sym in MEMES:
        coin = sym.split('/')[0]
        if coin in owned:
            print(f"{sym} deja possede, skip")
            continue

        rsi = get_rsi(sym, ex)
        print(f"{sym} RSI {rsi:.1f}")

        if rsi < 35:
            try:
                price = ex.fetch_ticker(sym)['last']
                qty = AMOUNT_USDT / price
                print(f"ACHAT SPOT {sym} RSI {rsi:.1f} qty {qty}")
                ex.create_market_buy_order(sym, qty)
                owned.append(coin)
                time.sleep(1)
                if len(owned) >= MAX_POS:
                    break
            except Exception as e:
                print(f"Err {sym}: {e}")

except Exception as e:
    print(f"Erreur globale spot: {import requests, os
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")

def tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
        json={"chat_id": CHAT, "text": msg}, timeout=10)
    except: pass

# À la toute fin de ton script, après la boucle
resume = f"🚀 Chasseur Meme - {len(deja_en_spot) if 'deja_en_spot' in locals() else 1}/20 coins\n"
resume += f"Spot actuel: {deja_en_spot if 'deja_en_spot' in locals() else ['ORDI']}\n\n"
resume += f"Scan du jour:\n"
# tu peux mettre tes variables
resume += f"Meilleur RSI bas: POPCAT 34.0 - tentative achat {'OK' if 'Err' not in open('/tmp/log').read() else 'ECHEC solde SPOT'}\n"
resume += f"⚠️ Action requise: Transférer USDT Futures -> Spot"

tg(resume)
