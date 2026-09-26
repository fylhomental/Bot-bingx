import os, ccxt, requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINGX_API_KEY = os.getenv("BINGX_API_KEY")
BINGX_SECRET = os.getenv("BINGX_SECRET")

SYMBOL = "BTC/USDT"
AMOUNT_USDT = 10
LEVERAGE = 5
RSI_SEUIL = 30

def send_tg(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        pass
    print(msg)

def get_rsi():
    ex = ccxt.bingx({'enableRateLimit': True})
    candles = ex.fetch_ohlcv(SYMBOL, '1h', limit=100)
    closes = [c[4] for c in candles]
    price = closes[-1]
    gains = []
    losses = []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        if d > 0:
            gains.append(d)
        else:
            losses.append(abs(d))
    avg_g = sum(gains[-14:])/14 if len(gains)>=14 else 1
    avg_l = sum(losses[-14:])/14 if len(losses)>=14 else 1
    rs = avg_g / (avg_l + 0.0001)
    rsi = 100 - (100 / (1 + rs))
    return price, rsi

try:
    price, rsi = get_rsi()
    send_tg(f"🤖 CHECK FUTURES x{LEVERAGE} - BTC ${price:.2f} RSI {rsi:.1f}")

    if rsi < RSI_SEUIL:
        ex = ccxt.bingx({
            'apiKey': BINGX_API_KEY,
            'secret': BINGX_SECRET,
            'options': {'defaultType': 'swap'}
        })
        ex.set_leverage(LEVERAGE, SYMBOL)
        qty = (AMOUNT_USDT * LEVERAGE) / price
        send_tg(f"🚀 SIGNAL LONG FUTURES x{LEVERAGE} RSI {rsi:.1f} - {AMOUNT_USDT}$")
        # ex.create_market_buy_order(SYMBOL, qty)
        send_tg(f"✅ SIMULATION Futures - Ordre {qty} BTC (décommente pour réel)")
    else:
        send_tg(f"⏸️ Surveillance Futures RSI {rsi:.1f} > 30")

except Exception as e:
    send_tg(f"❌ ERREUR Futures: {e}")
