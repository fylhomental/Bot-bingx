import os, ccxt, requests, datetime
import pandas as pd
import ta

TG_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN','').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID','').strip()
BINGX_KEY = os.getenv('BINGX_API_KEY','').strip()
BINGX_SEC = os.getenv('BINGX_SECRET','').strip()

def send_tg(msg):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=15)
    except:
        pass

try:
    ex = ccxt.bingx({'apiKey': BINGX_KEY, 'secret': BINGX_SEC, 'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
    ex.load_markets()
    ohlcv = ex.fetch_ohlcv('BTC/USDT', '15m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
    price = float(df['c'].iloc[-1])
    rsi = float(ta.momentum.RSIIndicator(df['c']).rsi().iloc[-1])
    now = datetime.datetime.now().strftime("%d/%m %H:%M")
    send_tg(f"Bot OK {now} BTC ${price:.2f} RSI {rsi:.2f} En attente RSI < 30")
except Exception as e:
    send_tg(f"ERREUR Bot {e}")
    raise e