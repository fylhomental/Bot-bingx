import os, ccxt, requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINGX_API_KEY = os.getenv("BINGX_API_KEY")
BINGX_SECRET = os.getenv("BINGX_SECRET")

SYMBOL = "BTC/USDT"
AMOUNT_USDT = 10 # 10$ SPOT
RSI_SEUIL = 30
TP_PCT = 2.0

def send_tg(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except: pass
    print(msg)

def get_rsi():
    ex = ccxt.bingx({'enableRateLimit': True})
    candles = ex.fetch_ohlcv("BTC/USDT", '1h', limit=100)
    closes = [c[4] for c in candles]
    price = closes[-1]
    gains = []; losses = []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        (gains if d>0 else losses).append(abs(d))
    avg_g = sum(gains[-14:])/14 if len(gains)>=14 else 1
    avg_l = sum(losses[-14:])/14 if len(losses)>=14 else 1
    rs = avg_g / (avg_l + 0.0001)
    rsi = 100 - (100 / (1+rs))
    return price, rsi

try:
    price, rsi = get_rsi()
    send_tg(f"💰 SPOT CHECK - BTC ${price:.2f} RSI {rsi:.1f}")

    if rsi < RSI_SEUIL:
        ex = ccxt.bingx({
            'apiKey': BINGX_API_KEY,
            'secret': BINGX_SECRET,
            'options': {'defaultType': 'spot'}
        })
        qty = AMOUNT_USDT / price
        send_tg(f"🚀 ACHAT SPOT REEL {AMOUNT_USDT}$ de BTC - RSI {rsi:.1f}")

        order = ex.create_market_buy_order(SYMBOL, qty)
        tp_price = price * (1 + TP_PCT/100)
        ex.create_limit_sell_order(SYMBOL, qty, tp_price)
        send_tg(f"✅ SPOT acheté + Ordre de vente placé à ${tp_price:.1f} (+{TP_PCT}%)")
    else:
        send_tg(f"⏸️ SPOT Surveillance - RSI {rsi:.1f} > 30 - Pas d'achat")

except Exception as e:
    send_tg(f"❌ SPOT ERREUR: {e}")
