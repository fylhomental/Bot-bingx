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
    ex = ccxt.bingx({
        'apiKey': BINGX_KEY,
        'secret': BINGX_SEC,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    ex.load_markets()
    symbol = 'BTC/USDT'
    
    # Prix + RSI
    ohlcv = ex.fetch_ohlcv(symbol, '15m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
    price = float(df['c'].iloc[-1])
    rsi = float(ta.momentum.RSIIndicator(df['c']).rsi().iloc[-1])
    now = datetime.datetime.now().strftime("%d/%m %H:%M")

    # --- LOGIQUE ACHAT REEL ---
    if rsi < 30:
        # Montant = 15$ de BTC
        amount_btc = 15 / price
        # Arrondi BingX (0.00001)
        amount_btc = round(amount_btc, 5)
        
        # ORDRE REEL
        order = ex.create_market_buy_order(symbol, amount_btc)
        
        send_tg(f"💚 ACHAT REEL EXECUTE {symbol}\nPrix: ${price:.2f}\nRSI: {rsi:.2f}\nMontant: ${15} ({amount_btc} BTC)\nHeure: {now}\nOrder ID: {order['id']}")
    else:
        send_tg(f"Bot OK {now} BTC ${price:.2f} RSI {rsi:.2f} En attente RSI < 30")

except Exception as e:
    print(f"ERREUR: {e}")
    send_tg(f"❌ ERREUR Bot {e}")
    raise e