import os, ccxt, requests, pandas as pd, time

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")
API_KEY = os.getenv("BINGX_API_KEY")
SECRET = os.getenv("BINGX_SECRET") or os.getenv("BINGX_SECRET_KEY") or os.getenv("BINGX_API_SECRET")

def tg(msg):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"}, timeout=20)

def get_rsi(closes, period=14):
    delta = closes.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])

# --- 1. P&L FUTURES ---
ex = ccxt.bingx({'apiKey': API_KEY,'secret': SECRET,'enableRateLimit': True})
pnl_txt = ""
try:
    bal = ex.fetch_balance()
    # P&L futures - on reprend ta logique
    positions = ex.fetch_positions() if hasattr(ex, 'fetch_positions') else []
    total_pnl = 0
    lines = []
    for p in positions:
        if p.get('contracts',0) != 0:
            symbol = p['symbol']
            entry = p.get('entryPrice',0)
            mark = p.get('markPrice',0)
            pnl = p.get('unrealizedPnl',0)
            total_pnl += pnl or 0
            pct = p.get('percentage',0) or 0
            lines.append(f"{symbol}: {pct:.2f}%")
    pnl_txt = f"📊 *Daily P&L Futures*\nTotal: {total_pnl:.2f}$\n" + "\n".join(lines[:10]) if lines else "📊 *Daily P&L*\nPas de positions futures"
except Exception as e:
    pnl_txt = f"📊 *