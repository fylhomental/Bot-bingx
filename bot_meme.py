import os, ccxt, requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BINGX_API_KEY = os.getenv("BINGX_API_KEY")
BINGX_SECRET = os.getenv("BINGX_SECRET")

MEME_COINS = ["DOGE/USDT", "PEPE/USDT", "BONK/USDT", "WIF/USDT", "SHIB/USDT"]
AMOUNT_USDT = 1.5 # On baisse à 1.5$ pour éviter le manque de solde
RSI_SEUIL = 35
TP_PCT = 10.0
SL_PCT = 7.0

def send_tg(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except: pass
    print(msg)

def get_rsi(symbol):
    ex = ccxt.bingx({'enableRateLimit': True})
    candles = ex.fetch_ohlcv(symbol, '1h', limit=100) # 1h plus fiable
    closes = [c[4] for c in candles]
    # RSI classique 14
    deltas = [closes[i]-closes[i-1] for i in range(1,len(closes))]
    gains = [d if d>0 else 0 for d in deltas]
    losses = [-d if d<0 else 0 for d in deltas]
    avg_gain = sum(gains[-14:])/14
    avg_loss = sum(losses[-14:])/14
    if avg_loss == 0: return closes[-1], 100
    rs = avg_gain / avg_loss
    rsi = 100 - (100/(1+rs))
    return closes[-1], rsi

for SYMBOL in MEME_COINS:
    try:
        price, rsi = get_rsi(SYMBOL)
        if rsi < RSI_SEUIL:
            ex = ccxt.bingx({'apiKey': BINGX_API_KEY,'secret': BINGX_SECRET,'options': {'defaultType': 'spot'}})
            bal = ex.fetch_balance()
            usdt_free = bal['USDT']['free']
            if usdt_free < AMOUNT_USDT:
                send_tg(f"⚠️ {SYMBOL} RSI {rsi:.1f} mais solde insuffisant: {usdt_free:.2f}$ dispo")
                continue
            qty = AMOUNT_USDT / price
            send_tg(f"🐸 MEME BUY {SYMBOL} ${price} RSI {rsi:.1f} - {AMOUNT_USDT}$")
            ex.create_market_buy_order(SYMBOL, qty)
            send_tg(f"✅ MEME REEL ACHETE {SYMBOL} - TP +{TP_PCT}% | SL -{SL_PCT}%")
        else:
            print(f"{SYMBOL} RSI {rsi:.1f} - Attente")
    except Exception as e:
        send_tg(f"❌ MEME ERREUR {SYMBOL}: {e}")