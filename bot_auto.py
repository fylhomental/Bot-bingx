import os, ccxt, requests, datetime
import pandas as pd
import ta

# SECRETS
TG_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BINGX_KEY = os.getenv('BINGX_API_KEY')
BINGX_SECRET = os.getenv('BINGX_SECRET')

def send_tg(msg):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=15)
        print(f"TG {r.status_code}")
        return r.status_code
    except Exception as e:
        print(f"TG ERREUR {e}")
        return 0

# HEURE
now = datetime.datetime.now().strftime("%d/%m %H:%M")

try:
    # CONNEXION BINGX
    exchange = ccxt.bing