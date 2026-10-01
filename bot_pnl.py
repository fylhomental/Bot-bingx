import os, requests, ccxt
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT = os.getenv("TELEGRAM_CHAT_ID", "").strip()
API_KEY = os.getenv("BINGX_API_KEY", "").strip()

# on cherche le secret sous tous les noms possibles
SECRET = os.getenv("BINGX_SECRET_KEY", "") or os.getenv("BINGX_SECRET", "") or os.getenv("BINGX_API_SECRET", "")
SECRET = SECRET.strip()

print("TOKEN ok" if TOKEN else "TOKEN missing")
print("CHAT ok" if CHAT else "CHAT missing")
print("API_KEY ok" if API_KEY else "API_KEY missing")
print(f"SECRET length = {len(SECRET)}")

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT, "text": msg}, timeout=15)
    print(f"TELEGRAM {r.status_code} {r.text[:400]}")

try:
    if not SECRET:
        raise Exception("BingX SECRET is empty - check GitHub Secrets names")

    ex = ccxt.bingx({'apiKey': API_KEY, 'secret': SECRET, 'options': {'defaultType': 'swap'}})
    positions = ex.fetch_positions()
    total = 0
    lines = []
    for p in positions:
        if float(p.get('contracts',0)) == 0:
            continue
        pnl = float(p.get('unrealizedPnl',0) or 0)
        total += pnl
        lines.append(f"{p['symbol']}: {pnl:.2f}$")

    bal = ex.fetch_balance()
    usdt = bal.get('USDT',{}).get('total',0) if isinstance(bal, dict) else 0

    msg = f"Daily P&L {datetime.now().strftime('%d/%m %H:%M')}\nBalance: {usdt:.2f} USDT\nPNL: {total:.2f}$\n\n" + ("\n".join(lines[:15]) if lines else "Aucune position")
    send(msg)

except Exception as e:
    import traceback
    traceback.print_exc()
    send(f"Erreur: {e}")
