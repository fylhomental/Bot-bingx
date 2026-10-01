import os, requests, ccxt, traceback
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")
API_KEY = os.getenv("BINGX_API_KEY")
SECRET = os.getenv("BINGX_SECRET_KEY") or os.getenv("BINGX_SECRET")

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        print(f"TELEGRAM OK: {msg[:100]}")
    except Exception as e:
        print(f"TELEGRAM ERR: {e}")

print(f"START PNL {datetime.now()}")
if not TOKEN or not CHAT:
    print("TOKEN/CHAT manquant")
    exit(1)

try:
    ex = ccxt.bingx({'apiKey': API_KEY, 'secret': SECRET, 'options': {'defaultType': 'swap'}})
    positions = ex.fetch_positions()
    total_pnl = 0
    lines = []
    for p in positions:
        if float(p.get('contracts', 0)) == 0: continue
        sym = p['symbol']
        pnl = float(p.get('unrealizedPnl', 0))
        roe = float(p.get('percentage', 0))
        total_pnl += pnl
        lines.append(f"{sym}: {pnl:.2f}$ ({roe:.1f}%)")

    bal = ex.fetch_balance()
    usdt = bal.get('USDT', {}).get('total', 0)

    msg = f"📊 *Daily P&L {datetime.now().strftime('%d/%m %H:%M')}*\n\n"
    msg += f"Balance: {usdt:.2f} USDT\n"
    msg += f"PNL total: {total_pnl:.2f}$\n\n"
    if lines:
        msg += "\n".join(lines[:15])
    else:
        msg += "Aucune position ouverte"

    send(msg)

except Exception as e:
    print(traceback.format_exc())
    send(f"⚠️ Erreur bot_pnl.py:\n{e}")
