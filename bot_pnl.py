SECRET = os.getenv("BINGX_SECRET_KEY") or os.getenv("BINGX_SECRET") or os.getenv("BINGX_API_SECRET")
print(f"SECRET len={len(SECRET) if SECRET else 0}")import os, requests, ccxt, traceback
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN").strip()
CHAT = os.getenv("TELEGRAM_CHAT_ID").strip()
API_KEY = os.getenv("BINGX_API_KEY")
SECRET = os.getenv("BINGX_SECRET_KEY") or os.getenv("BINGX_SECRET")

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"}, timeout=15)
    print(f"TELEGRAM {r.status_code}: {r.text[:300]}")

try:
    ex = ccxt.bingx({'apiKey': API_KEY, 'secret': SECRET, 'options': {'defaultType': 'swap'}})
    positions = ex.fetch_positions()
    total_pnl = 0
    lines = []
    for p in positions:
        if float(p.get('contracts',0))==0: continue
        pnl = float(p.get('unrealizedPnl',0) or 0)
        total_pnl+=pnl
        lines.append(f"{p['symbol']}: {pnl:.2f}$")
    bal = ex.fetch_balance()
    usdt = bal.get('USDT',{}).get('total',0)
    
    msg = f"📊 *Daily P&L {datetime.now().strftime('%d/%m %H:%M')}*\n\nBalance: {usdt:.2f} USDT\nPNL: {total_pnl:.2f}$\n\n" + ("\n".join(lines[:15]) if lines else "Aucune position")
    send(msg)
except Exception as e:
    print(traceback.format_exc())
    send(f"⚠️ Erreur: {e}")
