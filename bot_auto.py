import os, ccxt, requests, datetime
import pandas as pd
import ta

TG_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN','').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID','').strip()

def send_tg(msg):
    if not TG_TOKEN or not CHAT_ID:
        print("MANQUE TOKEN OU CHAT_ID")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=15)
    print(f"TG {r.status_code} {r.text[:200]}")

try:
    ex = ccxt.bingx({'enableRateLimit': True})
    ohlcv = ex.fetch_ohlcv('BTC/USDT', '15m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
    rsi = ta.momentum.RSIIndicator(df['c']).rsi().iloc[-1]
    price = df['c'].iloc[-1]
    now = datetime.datetime.now().strftime("%d/%m %H:%M")
    send_tg(f"✅ Bot OK {now}\nBTC: ${price:.2f} RSI 15m: {rsi:.2f}\nTelegram est réparé !")
except Exception as e:
    print(f"ERREUR: {e}")
    send_tg(f"❌ ERREUR {e}")
