import os, requests, ccxt
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT = os.getenv("TELEGRAM_CHAT_ID", "").strip()
API_KEY = os.getenv("BINGX_API_KEY", "").strip()
SECRET = (os.getenv("BINGX_SECRET_KEY", "") or os.getenv("BINGX_SECRET", "") or os.getenv("BINGX_API_SECRET", "")).strip()

def clean_sym(s):
    s = s.split("/")[0].split(":")[0]
    return "NCFX" if "NCFX" in s else s

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT, "text": msg}, timeout=15)

ex = ccxt.bingx({'apiKey': API_KEY, 'secret': SECRET, 'options': {'defaultType': 'swap'}})
positions = ex.fetch_positions()
bal = ex.fetch_balance()
usdt = bal.get('USDT',{}).get('total',0) or 0

total=0
lines=[]
for p in positions:
    if float(p.get('contracts',0))==0: continue
    pnl = float(p.get('unrealizedPnl',0) or 0)
    total+=pnl
    entry = float(p.get('entryPrice',0) or 0)
    mark = float(p.get('markPrice',0) or p.get('lastPrice',0) or entry)
    side = p.get('side','long')
    # vrai % de variation de prix
    price_pct = ((mark-entry)/entry*100) if entry else 0
    if side=='short': price_pct = -price_pct
    lev = p.get('leverage', '') or ''

    emoji = "🟢" if pnl>=0 else "🔴"
    sign = "+" if pnl>=0 else ""
    signp = "+" if price_pct>=0 else ""
    sym = clean_sym(p['symbol'])
    lev_txt = f" x{int(lev)}" if lev else ""
    lines.append(f"{emoji} {sym}{lev_txt}: {sign}{pnl:.2f}$ ({signp}{price_pct:.2f}%)\n └ {entry:.2f} → {mark:.2f}")

sign_total = "+" if total>=0 else ""
pct_total = (total/usdt*100) if usdt else 0

msg = f"📊 Daily P&L {datetime.now().strftime('%d/%m %H:%M')}\nBalance: {usdt:.2f} USDT | UPNL: {sign_total}{total:.2f}$ ({sign_total}{pct_total:.2f}%)\n\n" + "\n\n".join(lines)
send(msg)
print(msg)
