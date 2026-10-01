import os
import ccxt
import time
import requests
import pandas as pd

# === CONFIG ===
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
    except Exception as e:
        print(f"Err TG: {e}")

def get_rsi(closes, period=14):
    delta = closes.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# === START ===
print(f"CHASSEUR SPOT SECURISE {AMOUNT_USDT}$ max {MAX_POS} coins")

try:
    ex = ccxt.bingx({
        'apiKey': API_KEY,
        'secret': SECRET,
        'enableRateLimit': True
    })

    # Balance SPOT
    bal = ex.fetch_balance()
    spot_bal = bal.get('USDT', {}).get('free', 0)
    print(f"Solde SPOT USDT: {spot_bal}")

    # Coins deja en spot
    owned = []
    try:
        # liste depuis balance
        for coin, data in bal.items():
            if coin != 'USDT' and coin != 'info' and coin != 'free' and coin != 'used' and coin != 'total':
                if isinstance(data, dict) and data.get('total', 0) > 0:
                    owned.append(coin)
        # fallback si vide, garde ORDI comme vu sur ton log
        if not owned:
            # on essaie de deviner via fetch
            owned = ['ORDI'] if bal.get('ORDI', {}).get('total',
