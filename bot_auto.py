import os, ccxt, requests, time

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINGX_API_KEY = os.getenv("BINGX_API_KEY")
BINGX_SECRET = os.getenv("BINGX_SECRET")

SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]
AMOUNT_USDT = 10
LEVERAGE = 5
RSI_SEUIL = 30

def send_tg(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except: pass
    print(msg)

def get_rsi_price(symbol):
    ex = ccxt.bingx({'enableRateLimit': True})
    candles = ex.fetch_ohlcv(symbol, '1h', limit=100)
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
    ex_fut = ccxt.bingx({
        'apiKey': BINGX_API_KEY,
        'secret': BINGX_SECRET,
        'options': {'defaultType': 'swap'}
    })

    for sym in SYMBOLS:
        try:
            price, rsi = get_rsi_price(sym)
            sym_fut = sym + ":USDT"
            send_tg(f"🤖 {sym} FUTURES x{LEVERAGE} - ${price:.2f} RSI {rsi:.1f}")

            if rsi < RSI_SEUIL:
                ex_fut.set_leverage(LEVERAGE, sym_fut)
                qty = (AMOUNT_USDT * LEVERAGE) / price
                order = ex_fut.create_market_buy_order(sym_fut, qty)
                send_tg(f"🚀 ACHAT REEL LONG {sym} x{LEVERAGE} - {AMOUNT_USDT}$ -> Pos {AMOUNT_USDT*LEVERAGE}$ RSI {rsi:.1f} ✅")
            else:
                send_tg(f"⏸️ {sym} - RSI {rsi:.1f} > 30 - Pas d'achat")
            time.sleep(2)
        except Exception as e:
            send_tg(f"❌ Erreur {sym}: {e}")

except Exception as e:
    send_tg(f"❌ ERREUR GLOBALE FUTURES: {e}")