import os, ccxt, requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINGX_API_KEY = os.getenv("BINGX_API_KEY")
BINGX_SECRET = os.getenv("BINGX_SECRET")

# MEME COINS TOP BingX
MEME_COINS = ["DOGE/USDT", "PEPE/USDT", "BONK/USDT", "WIF/USDT", "SHIB/USDT"]
AMOUNT_USDT = 2 # 2$ par meme
RSI_SEUIL = 25 # Plus bas que BTC car memes chutent plus fort
TP_PCT = 10.0 # On vise +10%
SL_PCT = 7.0 # On coupe à -7%

def send_tg(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except: pass
    print(msg)

def get_rsi_price(symbol):
    ex = ccxt.bingx({'enableRateLimit': True})
    candles = ex.fetch_ohlcv(symbol, '15m', limit=100)
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

for SYMBOL in MEME_COINS:
    try:
        price, rsi = get_rsi_price(SYMBOL)
        if rsi < RSI_SEUIL:
            ex = ccxt.bingx({
                'apiKey': BINGX_API_KEY,
                'secret': BINGX_SECRET,
                'options': {'defaultType': 'spot'}
            })
            qty = AMOUNT_USDT / price
            send_tg(f"🐸 MEME BUY {SYMBOL} ${price} RSI {rsi:.1f} - {AMOUNT_USDT}$")

            order = ex.create_market_buy_order(SYMBOL, qty)
            send_tg(f"✅ MEME REEL ACHETE {SYMBOL} - TP +{TP_PCT}% | SL -{SL_PCT}%")
        else:
            print(f"{SYMBOL} RSI {rsi:.1f} - pas d'achat")
    except Exception as e:
        send_tg(f"❌ MEME ERREUR {SYMBOL}: {e}")
