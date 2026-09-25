import os
import requests
import ccxt

print("--- DEBUT BOT BOTH ---")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINGX_API_KEY = os.getenv("BINGX_API_KEY")
BINGX_SECRET = os.getenv("BINGX_SECRET")

print(f"Token: {bool(TELEGRAM_TOKEN)} | ChatID: {TELEGRAM_CHAT_ID} | BingX: {bool(BINGX_API_KEY)}")

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
        print(f"TG {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"Erreur TG: {e}")

# --- CONFIG ---
USE_SPOT = True
USE_FUTURES = True
SPOT_AMOUNT_USDT = 20
FUTURES_AMOUNT_USDT = 20
LEVERAGE = 3
SYMBOL_SPOT = "BTC/USDT"
SYMBOL_FUTURES = "BTC/USDT:USDT"

def get_client(market_type):
    return ccxt.bingx({
        'apiKey': BINGX_API_KEY,
        'secret': BINGX_SECRET,
        'options': {'defaultType': market_type}
    })

# --- STRATEGIE TEST BUY ---
signal = "BUY"

if signal == "BUY":
    try:
        if USE_SPOT:
            ex = get_client('spot')
            price = ex.fetch_ticker(SYMBOL_SPOT)['last']
            qty = SPOT_AMOUNT_USDT / price
            # ex.create_market_buy_order(SYMBOL_SPOT, qty)  # <--- TEST, on ne trade pas encore
            send_telegram(f"✅ SPOT: Achat {qty:.6f} BTC (~{SPOT_AMOUNT_USDT}$) à {price}$")

        if USE_FUTURES:
            ex = get_client('swap')
            # CORRECTION BUG BINGX LEVERAGE
            try:
                ex.set_leverage(LEVERAGE, SYMBOL_FUTURES, params={'marginMode': 'cross'})
            except Exception as e:
                print(f"Leverage warning: {e} - on continue")
            
            price = ex.fetch_ticker(SYMBOL_FUTURES)['last']
            qty = (FUTURES_AMOUNT_USDT * LEVERAGE) / price
            # ex.create_market_buy_order(SYMBOL_FUTURES, qty)  # <--- TEST
            send_telegram(f"🚀 FUTURES x{LEVERAGE}: Long {qty:.6f} BTC (~{FUTURES_AMOUNT_USDT}$) à {price}$")
            
    except Exception as e:
        print(f"ERREUR GLOBALE: {e}")
        send_telegram(f"❌ Erreur bot: {e}")

print("--- FIN BOT ---")