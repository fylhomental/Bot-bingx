import os, ccxt, requests, datetime
import pandas as pd
import ta

# --- Secrets GitHub ---
TG_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN','').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID','').strip()
BINGX_KEY = os.getenv('BINGX_API_KEY','').strip()
BINGX_SEC = os.getenv('BINGX_SECRET','').strip() or os.getenv('BINGX_API_SECRET','').strip()

def send_tg(msg):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=15)
    except Exception as e:
        print(f"TG Error {e}")

try:
    if not BINGX_KEY or not BINGX_SEC:
        raise Exception("Clés BingX manquantes dans Secrets")

    # Connexion BingX corrigée (plus d'erreur Signature 100001)
    ex = ccxt.bingx({
        'apiKey': BINGX_KEY,
        'secret': BINGX_SEC,
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })
    
    ex.load_markets()
    symbol = 'BTC/USDT'
    
    # Récupère prix + RSI 15m
    ohlcv = ex.fetch_ohlcv(symbol, '15m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
    price = float(df['c'].iloc[-1])
    rsi = float(ta.momentum.RSIIndicator(df['c']).rsi().iloc[-1])
    
    now = datetime.datetime.now().strftime("%d/%m %H:%M")
    print(f"BTC {price} RSI {rsi}")

    # LOGIQUE
    if rsi < 30:
        send_tg(f"💚 SIGNAL ACHAT {symbol}\nPrix: ${price:.2f}\nRSI 15m: {rsi:.2f}\nHeure: {now}\n\nBot prêt à acheter. Dis-moi si tu veux que j'active l'ordre réel.")
    else: