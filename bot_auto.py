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
    
    ohlcv = ex.fetch_ohlcv(symbol, '15m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
    price = float(df['c'].iloc[-1])
    rsi = float(ta.momentum.RSIIndicator(df['c']).rsi().iloc[-1])
    now = datetime.datetime.now().strftime("%d/%m %H:%M")

    if rsi < 30:
        amount_btc = round((15 / price), 5)
        
        # 1. ACHAT REEL
        order = ex.create_market_buy_order(symbol, amount_btc)
        
        # 2. CALCUL TP/SL
        tp_price = round(price * 1.02, 1)  # +2%
        sl_price = round(price * 0.99, 1)  # -1%
        
        # 3. ORDRE TAKE PROFIT (vente limit)
        try:
            ex.create_order(symbol, 'limit', 'sell', amount_btc, tp_price, {'reduceOnly': True})
        except Exception as e:
            print(f"TP Error: {e}")
            
        # 4. ORDRE STOP LOSS (vente stop)
        try:
            ex.create_order(symbol, 'stop', 'sell', amount_btc, None, {'stopPrice': sl_price, 'reduceOnly': True})
        except Exception as e:
            # fallback si BingX veut stop_market
            try:
                ex.create_order(symbol, 'stop_market', 'sell', amount_btc, None, {'stopPrice': sl_price, 'reduceOnly': True})
            except Exception as e2:
                print(f"SL Error: {e2}")

        send_tg(f"💚 ACHAT REEL + TP/SL\n{now} BTC ${price:.2f} RSI {rsi:.2f}\nAchat: {amount_btc} BTC (${15})\nTP: ${tp_price} (+2%)\nSL: ${sl_price} (-1%)\nOrder: {order['id']}")
    else:
        send_tg(f"Bot OK {now} BTC ${price:.2f} RSI {rsi:.2f} En attente RSI < 30")

except Exception as e:
    print(f"ERREUR: {e}")
    send_tg(f"❌ ERREUR Bot {e}")
    raise e