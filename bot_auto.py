import os
import time
import requests
import pandas as pd

# On récupère les secrets de GitHub - ne mets JAMAIS ton token en dur
T = os.getenv("TELEGRAM_TOKEN")
C = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(msg):
    if not T or not C:
        print("Secrets manquants!")
        return
    try:
        url = f"https://api.telegram.org/bot{T}/sendMessage"
        requests.post(url, json={"chat_id": C, "text": msg}, timeout=10)
    except Exception as e:
        print(f"Erreur Telegram: {e}")

def get_klines(symbol):
    url = "https://open-api.bingx.com/openApi/spot/v1/market/kline"
    params = {"symbol": symbol, "interval": "15m", "limit": "100"}
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    if "data" not in data:
        print(f"Erreur BingX {symbol}: {data}")
        return None
    df = pd.DataFrame(data["data"])
    df = df.iloc[:, :6]
    df.columns = ['t','o','h','l','c','v']
    df['c'] = pd.to_numeric(df['c'], errors='coerce')
    return df

def calc_rsi(series, p=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/p, min_periods=p).mean()
    avg_loss = loss.ewm(alpha=1/p, min_periods=p).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

SYMBOLS = ["BTC-USDT", "ETH-USDT", "SOL-USDT"]

for sym in SYMBOLS:
    df = get_klines(sym)
    if df is None:
        continue
    df['rsi'] = calc_rsi(df['c'])
    pr = float(df['c'].iloc[-1])
    rs = float(df['rsi'].iloc[-1])
    
    msg = ""
    if rs < 35:
        msg = f"🟢 ACHAT {sym} {pr:.2f} RSI {rs:.1f}"
    elif rs > 65:
        msg = f"🔴 VENTE {sym} {pr:.2f} RSI {rs:.1f}"
    
    if msg:
        print(msg)
        send_telegram(msg)
    else:
        print(f"{sym} {pr:.2f} RSI {rs:.1f} - rien à faire")

print("Scan terminé")