import os, ccxt, requests, datetime
import pandas as pd
import ta

TG_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BINGX_KEY = os.getenv('BINGX_API_KEY')
BINGX_SECRET = os.getenv('BINGX_SECRET')

def send_tg(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=15)
        print(f"TG {r.status_code} - {msg[:50]}")
        return r.status_code
    except Exception as e:
        print(f"TG ERREUR {e}")
        return 0

now = datetime.datetime.now().strftime("%d/%m %H:%M")

try:
    ex = ccxt.bingx({'apiKey': BINGX_KEY, 'secret': BINGX_SECRET, 'enableRateLimit': True})
    ex.load_markets()
    bal = ex.fetch_balance()
    usdt = bal['total'].get('USDT', 0)
    ohlcv = ex.fetch_ohlcv('BTC/USDT', '15m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
    rsi = ta.momentum.RSIIndicator(df['c']).rsi().iloc[-1]
    price = df['c'].iloc[-1]
    print(f"OK Token:{bool(TG_TOKEN)} Chat:{CHAT_ID} USDT:{usdt} RSI:{rsi:.2f}")

    if rsi < 30:
        send_tg(f"💚 ACHAT BTC-USDT ${price:.2f} RSI {rsi:.2f} 15m {now} USDT:{usdt:.2f}")
    else:
        send_tg(f"✅ Check {now} - Bot OK\nBTC: ${price:.2f} | RSI: {rsi:.2f}\nEn attente RSI<30 | USDT:{usdt:.2f}$")

except Exception as e:
    print(f"ERREUR GLOBALE: {e}")
    send_tg(f"❌ ERREUR {now} {e}")