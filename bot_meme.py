import os
import ccxt
import time
import requests
import pandas as pd

AMOUNT_USDT = 5
MAX_POS = 20
RSI_THRESHOLD = 35

MEMES = [
    "DOGE/USDT", "SHIB/USDT", "PEPE/USDT", "BONK/USDT",
    "WIF/USDT", "FLOKI/USDT", "ORDI/USDT", "BOME/USDT",
    "POPCAT/USDT", "MOG/USDT", "BRETT/USDT", "MEME/USDT",
    "TURBO/USDT", "LADYS/USDT"
]

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")
API_KEY = os.getenv("BINGX_API_KEY")
SECRET = os.getenv("BINGX_SECRET") or os.getenv("BINGX_SECRET_KEY") or os.getenv("BINGX_API_SECRET")

def tg(msg):
    try:
        if not TOKEN or not CHAT:
            return
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      json={"chat_id": CHAT, "text": msg}, timeout=15)
    except:
        pass

def get_rsi(closes, period=14):
    delta = closes.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

print(f"CHASSEUR SPOT SECURISE {AMOUNT_USDT}$ max {MAX_POS} coins")

try:
    ex = ccxt.bingx({'apiKey': API_KEY,'secret': SECRET,'enableRateLimit': True})
    bal = ex.fetch_balance()
    spot_bal = bal.get('USDT', {}).get('free', 0) if isinstance(bal.get('USDT'), dict) else 0
    print(f"Solde SPOT USDT: {spot_bal}")

    owned = []
    try:
        for k,v in bal.items():
            if isinstance(v, dict) and v.get('total',0) > 0 and k!= 'USDT':
                if k not in ['info','free','used','total']:
                    owned.append(k)
    except:
        owned = []

    print(f"Deja en Spot: {owned} ({len(owned)}/{MAX_POS})")

    briefing_lines = []
    achats = []
    erreurs = []

    for sym in MEMES:
        try:
            coin = sym.split('/')[0]
            if coin in owned:
                briefing_lines.append(f"{sym} deja possede")
                continue
            candles = ex.fetch_ohlcv(sym, '1d', limit=50)
            closes = pd.DataFrame(candles, columns=['t','o','h','l','c','v'])['c']
            rsi = get_rsi(closes)
            briefing_lines.append(f"{sym} RSI {rsi:.1f}")
            print(f"{sym} RSI {rsi:.1f}")

            if rsi < RSI_THRESHOLD:
                try:
                    price = ex.fetch_ticker(sym)['last']
                    qty = AMOUNT_USDT / price
                    print(f"ACHAT SPOT {sym} RSI {rsi:.1f}")
                    ex.create_market_buy_order(sym, qty)
                    owned.append(coin)
                    achats.append(f"{sym} @ RSI {rsi:.1f}")
                    time.sleep(1)
                    if len(owned) >= MAX_POS:
                        break
                except Exception as e:
                    print(f"Err {sym}: {e}")
                    erreurs.append(f"{sym}: {e}")
        except Exception as e:
            print(f"Err {sym}: {e}")

    msg = f"🚀 Chasseur Meme du jour - {len(owned)}/{MAX_POS}\n"
    msg += f"Spot: {owned}\nSolde SPOT: {spot_bal:.2f} USDT\n\n"
    if achats:
        msg += "✅ Achats:\n" + "\n".join(achats) + "\n\n"
    else:
        msg += "Aucun achat (RSI > 35)\n\n"
    msg += "📊 Scan:\n" + "\n".join(briefing_lines[:12]) + "\n"
    if erreurs:
        msg += "\n⚠️ " + "\n".join(erreurs[:3])
        if "100202" in str(erreurs):
            msg += "\n👉 Transfere USDT Futures -> Spot"
    tg(msg)

except Exception as e:
    print(f"Erreur globale spot: {e}")
    tg(f"⚠️ Erreur chasseur meme: {e}")
