import os, ccxt, requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINGX_API_KEY = os.getenv("BINGX_API_KEY")
BINGX_SECRET = os.getenv("BINGX_SECRET")

SYMBOL = "BTC/USDT:USDT"
AMOUNT_USDT = 10
LEVERAGE = 5
RSI_SEUIL = 30
TP_PCT = 2.0
SL_PCT = 1.5

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
    gains=[]; losses=[]
    for i in range(1,len(closes)):
        d=closes[i]-closes[i-1]
        if d>0: gains.append(d)
        else: losses.append(abs(d))
    avg_g=sum(gains[-14:])/14 if len(gains)>=14 else 1
    avg_l=sum(losses[-14:])/14 if len(losses)>=14 else 1
    rsi=100-(100/(1+avg_g/(avg_l+0.0001)))
    return price, rsi

try:
    price, rsi = get_rsi()
    send_tg(f"🤖 CHECK FUTURES x{LEVERAGE} REEL - BTC ${price:.2f} RSI {rsi:.1f}")

    if rsi < RSI_SEUIL:
        ex = ccxt.bingx({
            'apiKey': BINGX_API_KEY,
            'secret': BINGX_SECRET,
            'options': {'defaultType': 'swap'}
        })
        ex.set_leverage(LEVERAGE, SYMBOL)
        qty = (AMOUNT_USDT * LEVERAGE) / price

        send_tg(f"🚀 ACHAT REEL LONG x{LEVERAGE} - {AMOUNT_USDT}$ -> Position {AMOUNT_USDT*LEVERAGE}$ - RSI {rsi:.1f}")

        order = ex.create_market_buy_order(SYMBOL, qty)
        send_tg(f"✅ LONG REEL OUVERT: {qty} BTC à ${price:.2f}")

        # TP et SL
        tp_price = price * (1 + TP_PCT/100)
        sl_price = price * (1 - SL_PCT/100)
        try:
            ex.create_order(SYMBOL, 'limit', 'sell', qty, tp_price, {'takeProfit': tp_price})
            ex.create_order(SYMBOL, 'limit', 'sell', qty, sl_price, {'stopLoss': sl_price})
            send_tg(f"🎯 TP +{TP_PCT}% à ${tp_price:.1f} | SL -{SL_PCT}% à ${sl_price:.1f}")
        except Exception as e:
            send_tg(f"⚠️ Position ouverte mais TP/SL manuel à mettre: {e}")

    else:
        send_tg(f"⏸️ Pas d'achat - RSI {rsi:.1f} > 30")

except Exception as e:
    send_tg(f"❌ ERREUR REEL: {e}")