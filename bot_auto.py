import os
import ccxt
import requests

# --- CONFIG ---
USE_SPOT = True
USE_FUTURES = True
SPOT_AMOUNT_USDT = 20
FUTURES_AMOUNT_USDT = 20
LEVERAGE = 3
SYMBOL_SPOT = "BTC/USDT"
SYMBOL_FUTURES = "BTC/USDT:USDT"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINGX_API_KEY = os.getenv("BINGX_API_KEY")
BINGX_SECRET = os.getenv("BINGX_SECRET")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

def get_client(market_type):
    return ccxt.bingx({
        'apiKey': BINGX_API_KEY,
        'secret': BINGX_SECRET,
        'options': {'defaultType': market_type}
    })

# --- TA STRATEGIE ICI ---
# Pour le test, on met un signal BUY
signal = "BUY"  # Remplace par ta logique RSI/MACD

if signal == "BUY":
    if USE_SPOT:
        ex = get_client('spot')
        price = ex.fetch_ticker(SYMBOL_SPOT)['last']
        qty = SPOT_AMOUNT_USDT / price
        # ex.create_market_buy_order(SYMBOL_SPOT, qty) # <-- décommente pour trader réel
        send_telegram(f"✅ SPOT: Achat {qty:.6f} BTC (~{SPOT_AMOUNT_USDT}$)")

    if USE_FUTURES:
        ex = get_client('swap')
        ex.set_leverage(LEVERAGE, SYMBOL_FUTURES)
        price = ex.fetch_ticker(SYMBOL_FUTURES)['last']
        qty = (FUTURES_AMOUNT_USDT * LEVERAGE) / price
        # ex.create_market_buy_order(SYMBOL_FUTURES, qty) # <-- décommente pour trader réel
        send_telegram(f"🚀 FUTURES x{LEVERAGE}: Long {qty:.6f} BTC (~{FUTURES_AMOUNT_USDT}$)")