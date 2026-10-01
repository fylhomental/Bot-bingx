import os, requests, ccxt
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT = os.getenv("TELEGRAM_CHAT_ID", "").strip()
API_KEY = os.getenv("BINGX_API_KEY", "").strip()
SECRET = (os.getenv("BINGX_SECRET_KEY", "") or os.getenv("BINGX_SECRET", "") or os.getenv("BINGX_API_SECRET", "")).strip()

def clean_sym(s):
    # NCFXEUR2GBP/USDT:USDT -> NCFX
    s = s.split("/")[0].split(":")[0]
    if "NCFX" in s: return "NCFX"
    return s

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT, "text": msg}, timeout=15)

try:
    ex = ccxt.bingx({'apiKey': API_KEY, 'secret': SECRET, 'options': {'defaultType': 'swap'}})
    positions = ex.fetch_positions()
    total = 0
    lines = []
    for p in positions:
        if float(p.get('contracts',0)) == 0: continue
        pnl = float(p.get('unrealizedPnl',0) or 0)
        total += pnl
        emoji = "🟢" if pnl >= 0 else "🔴"
        sign = "+" if pnl >= 0 else ""
        sym = clean_sym(p['symbol'])
        lines.append(f"{emoji} {sym}: {sign}{pnl:.2f}$")

    bal = ex.fetch_balance()
    usdt = bal.get('USDT',{}).get('total',0) if isinstance(bal, dict) else 0

    sign_total = "+" if total >= 0 else ""
    msg = f"📊 Daily P&L {datetime.now().strftime('%d/%m %H:%M')}\nBalance: {usdt:.2f} USDT | UPNL: {sign_total}{total:.2f}$\n\n" + ("\n".join(lines) if lines else "Aucune position ouverte")

    # petite alerte
    if total < -5:
        msg += "\n\n⚠️ Attention PNL < -5$!"

    send(msg)
    print("OK sent")

except Exception as e:
    import traceback
    traceback.print_exc()
    send(f"⚠️ Erreur bot: {e}")
