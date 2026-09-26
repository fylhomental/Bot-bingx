import os, ccxt, requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINGX_API_KEY = os.getenv("BINGX_API_KEY")
BINGX_SECRET = os.getenv("BINGX_SECRET")

SYMBOL = "BTC/USDT:USDT"
AMOUNT = 10
LEVERAGE = 5
TP = 2.0
SL = 1.5
RSI_SEUIL = 30

def send_tg(msg):
    print(msg)
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        print(f"TG {r.status_code}")
    except Exception as e:
        print(f"TG ERROR {e}")

def get_rsi():
    ex = ccxt.bingx({'enableRateLimit': True})
    candles = ex.fetch_ohlcv("BTC/USDT", '1h', limit=100)
    closes = [c[4] for c in candles]
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff > 0: gains.append(diff)
        else: losses.append(abs(diff))
    avg_gain = sum(gains[-14:]) / 14 if len(gains)>=14 else 1
    avg_loss = sum(losses[-14:]) / 14 if len(losses)>=14 else 1
    rs = avg_gain / (avg_loss + 0.0001)
    rsi = 100 - (100 / (1+rs))
    price = closes[-1]
    return price, rsi

try:
    price, rsi = get_rsi()
    send_tg(f"🤖 CHECK BingX Futures x5 - BTC ${price:.2f} RSI {rsi:.1f}")

    if rsi < RSI_SEUIL:
        ex = ccxt.bingx({
            'apiKey': BINGX_API_KEY,
            'secret': BINGX_SECRET,
            'options': {'defaultType': 'swap'}
        })
        ex.set_leverage(LEVERAGE, SYMBOL)
        ex.set_margin_mode('ISOLATED', SYMBOL)
        qty = (AMOUNT * LEVERAGE) / price
        send_tg(f"🚀 SIGNAL ACHAT RSI {rsi:.1f} < 30 -> LONG x5 {qty:.6f} BTC | TP +{TP}% SL -{SL}%")
        # ex.create_market_buy_order(SYMBOL, qty) # A decommenter quand tu veux trader en reel
    else:
        send_tg(f"⏸️ Pas d'achat - RSI {rsi:.1f} > 30 - Bot en surveillance")

except Exception as e:
    send_tg(f"❌ ERREUR BOT: {e}")
    print(f"ERROR: {e}")