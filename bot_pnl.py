import os, requests, traceback
from datetime import datetime

TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
CHAT = (os.getenv("TELEGRAM_CHAT_ID") or "").strip()
print(f"TOKEN len={len(TOKEN)} starts={TOKEN[:10]}")
print(f"CHAT raw='{CHAT}' len={len(CHAT)}")

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT, "text": msg}, timeout=15)
    print(f"TELEGRAM status={r.status_code} response={r.text[:500]}")
    return r

# test 1 - message simple sans erreur bingx
send(f"TEST BOT {datetime.now()} - si tu lis ça, Telegram OK")

# ensuite ton code BingX normal...
