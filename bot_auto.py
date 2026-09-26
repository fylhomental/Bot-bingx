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
    now = datetime.datetime.now().strftime("%d/%m %H:%M")

    # --- 1. CHECK SI POSITION OUVERTE ---
    try:
        positions = ex.fetch_positions([symbol])
        pos = None
        for p in positions:
            if p['symbol'] == symbol and float(p.get('contracts',0))!= 0:
                pos = p
                break

        if pos:
            entry = float(pos['entryPrice'])
            contracts = float(pos['contracts'])
            pnl = float(pos.get('unrealizedPnl',0))
            pnl_pct = ((ex.fetch_ticker(symbol)['last'] / entry - 1) * 100) if contracts > 0 else 0

            # Si on est déjà en position, on ne rachète pas
            send_tg(f"📈 POSITION OUVERTE {now}\nBTC ${ex.fetch_ticker(symbol)['last']:.2f}\nEntrée: ${entry:.2f}\nPnL: ${pnl:.2f} ({pnl_pct:.2f}%)\nTP: ${entry*1.02:.1f} | SL: ${entry*0.99:.1f}")
            print(f"Position ouverte PnL {pnl_pct}%")
            exit()
    except Exception as e:
        print(f"Check position error: {e}")

    # --- 2. CHECK SI DERNIER TRADE = TP ou SL ---
    try:
        trades = ex.fetch_my_trades(symbol, limit=5)
        if trades:
            last = trades[-1]
            if last['side'] == 'sell':
                price_close = float(last['price'])
                cost = float(last['cost'])
                # On regarde l'ordre précédent (achat)
                if len(trades) >= 2:
                    prev_buy = trades[-2]
                    entry = float(prev_buy['price'])
                    profit = ((price_close / entry - 1) * 100)
                    if profit > 0:
                        # Evite de spammer, on envoie seulement si trade récent < 20min
                        if (datetime.datetime.now().timestamp() - last['timestamp']/1000) < 1200:
                            send_tg(f"✅ TAKE PROFIT TOUCHE! {now}\nVente: ${price_close:.2f} (+{profit:.2f}%)\nProfit: ~${cost*profit/100:.2f}")
                    else:
                        if (datetime.datetime.now().timestamp() - last['timestamp']/1000) < 1200:
                            send_tg(f"🛑 STOP LOSS TOUCHE {now}\nVente: ${price_close:.2f} ({profit:.2f}%)\nPerte: ~${cost*profit/100:.2f}")
    except Exception as e:
        print(f"Check TP/SL error: {e}")

    # --- 3. LOGIQUE RSI / ACHAT ---
    ohlcv = ex.fetch_ohlcv(symbol, '15m', limit=100)
    df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
    price = float(df['c'].iloc[-1])
    rsi = float(ta.momentum.RSIIndicator(df['c']).rsi().iloc[-1])

    if rsi < 30:
        amount_btc = round((10 / price), 5)
        order = ex.create_market_buy_order(symbol, amount_btc)
        tp_price = round(price * 1.02, 1)
        sl_price = round(price * 0.99, 1)

        try:
            ex.create_order(symbol, 'limit', 'sell', amount_btc, tp_price, {'reduceOnly': True})
        except:
            pass
        try:
            ex.create_order(symbol, 'stop_market', 'sell', amount_btc, None, {'stopPrice': sl_price, 'reduceOnly': True})
        except:
            try:
                ex.create_order(symbol, 'stop', 'sell', amount_btc, None, {'stopPrice': sl_price, 'reduceOnly': True})
            except:
                pass

        send_tg(f"💚 ACHAT REEL + TP/SL\n{now} BTC ${price:.2f} RSI {rsi:.2f}\nAchat: {amount_btc} BTC (${10})\nTP: ${tp_price} (+2%) | SL: ${sl_price} (-1%)")
    else:
        send_tg(f"Bot OK {now} BTC ${price:.2f} RSI {rsi:.2f} En attente RSI < 30")

except Exception as e:
    print(f"ERREUR: {e}")
    send_tg(f"❌ ERREUR Bot {e}")
    raise e