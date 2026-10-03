import ccxt, os, json, requests, time
from datetime import datetime

SYMBOLS = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","XRP/USDT","DOGE/USDT"]
LEVERAGE = 5
AMOUNT_USDT = 10
RSI_SEUIL = 35
RSI_PERIOD = 14
SL_PCT = 8.0
TRAILING_PCT = 5.0
BE_PCT = 2.0

MEM_FILE = "bot_fylho_perp_memory.json"

def send_tg(msg):
    try:
        token = os.getenv("TELEGRAM_TOKEN")
        chat = os.getenv("TELEGRAM_CHAT_ID")
        if token and chat:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat, "text": msg}, timeout=10)
    except: pass

def load_mem():
    if os.path.exists(MEM_FILE):
        try:
            return json.loads(open(MEM_FILE).read())
        except: return {}
    return {}

def save_mem(m):
    open(MEM_FILE, "w").write(json.dumps(m))

def rsi_calc(closes, period=14):
    if len(closes) < period + 1:
        return 50
    gains, losses = 0, 0
    for i in range(1, period+1):
        diff = closes[-i] - closes[-i-1]
        if diff > 0: gains += diff
        else: losses -= diff
    if losses == 0: return 100
    rs = gains / losses
    return 100 - (100 / (1 + rs))

# Connexions
ex_fut = ccxt.bingx({
    'apiKey': os.getenv("BINGX_API_KEY"),
    'secret': os.getenv("BINGX_SECRET_KEY"),
    'options': {'defaultType': 'swap'}
})
ex_spot = ccxt.bingx({
    'apiKey': os.getenv("BINGX_API_KEY"),
    'secret': os.getenv("BINGX_SECRET_KEY"),
    'options': {'defaultType': 'spot'}
})

memory = load_mem()

for sym in SYMBOLS:
    try:
        sym_fut = sym.replace("/USDT", "/USDT:USDT")
        # Prix et RSI en spot pour le signal
        ohlcv = ex_spot.fetch_ohlcv(sym, '15m', limit=100)
        closes = [c[4] for c in ohlcv]
        price = closes[-1]
        rsi = rsi_calc(closes, RSI_PERIOD)

        # Gestion position existante
        if sym in memory:
            entry = memory[sym]['entry']
            high = max(memory[sym].get('high', entry), price)
            memory[sym]['high'] = high
            profit_pct = (price - entry) / entry * 100

            # BE à +2%
            if profit_pct >= BE_PCT and not memory[sym].get('be_done'):
                try:
                    memory[sym]['sl'] = entry
                    memory[sym]['be_done'] = True
                    save_mem(memory)
                    send_tg(f"🔒 BE {sym} SL remonté à {entry:.5f}")
                except: pass

            # Trailing TP - si baisse de 5% depuis le high
            if profit_pct > 0 and (high - price) / high * 100 >= TRAILING_PCT:
                try:
                    bal = ex_fut.fetch_positions([sym_fut])
                    qty_to_close = 0
                    for p in bal:
                        if p['symbol'] == sym_fut and p['contracts'] > 0:
                            qty_to_close = p['contracts']
                    if qty_to_close > 0:
                        ex_fut.create_market_sell_order(sym_fut, qty_to_close)
                        send_tg(f"💰 CLOSE LONG {sym} {profit_pct:.2f}% RSI {rsi:.1f} - Trailing {TRAILING_PCT}%")
                        del memory[sym]
                        save_mem(memory)
                except Exception as e:
                    send_tg(f"❌ Erreur CLOSE {sym}: {e}")
                continue

            # SL dur -8%
            if profit_pct <= -SL_PCT:
                try:
                    bal = ex_fut.fetch_positions([sym_fut])
                    qty_to_close = 0
                    for p in bal:
                        if p['symbol'] == sym_fut and p['contracts'] > 0:
                            qty_to_close = p['contracts']
                    if qty_to_close > 0:
                        ex_fut.create_market_sell_order(sym_fut, qty_to_close)
                        send_tg(f"🛑 SL -{SL_PCT}% {sym} {profit_pct:.2f}%")
                        del memory[sym]
                        save_mem(memory)
                except Exception as e:
                    send_tg(f"❌ Erreur SL {sym}: {e}")
                continue

        # Ouverture
        if rsi < RSI_SEUIL and sym not in memory:
            try:
                ex_fut.set_leverage(LEVERAGE, sym_fut, params={'side': 'BOTH'})
            except:
                try:
                    ex_fut.set_leverage(LEVERAGE, sym_fut, params={'side': 'LONG'})
                    ex_fut.set_leverage(LEVERAGE, sym_fut, params={'side': 'SHORT'})
                except: pass

            qty = (AMOUNT_USDT * LEVERAGE) / price
            sl_price = price * (1 - SL_PCT / 100)
            tp_price = price * (1 + TRAILING_PCT / 100)

            ex_fut.create_market_buy_order(sym_fut, qty)

            # SL REEL
            try:
                ex_fut.create_order(sym_fut, 'stopMarket', 'sell', qty, None, params={'stopPrice': sl_price})
            except Exception as e:
                send_tg(f"⚠️ SL non posé {sym}: {e}")

            # TP REEL
            try:
                ex_fut.create_order(sym_fut, 'takeProfitMarket', 'sell', qty, None, params={'stopPrice': tp_price})
            except:
                try:
                    ex_fut.create_order(sym_fut, 'limit', 'sell', qty, tp_price)
                except Exception as e:
                    send_tg(f"⚠️ TP non posé {sym}: {e}")

            memory[sym] = {'entry': price, 'high': price, 'sl': sl_price, 'tp': tp_price, 'be_done': False, 'qty': qty}
            save_mem(memory)
            send_tg(f"🚀 LONG {sym} x{LEVERAGE} entry {price:.5f} RSI {rsi:.1f} | SL {sl_price:.5f} (-{SL_PCT}%) TP {tp_price:.5f} (+{TRAILING_PCT}%)")

    except Exception as e:
        send_tg(f"❌ Erreur globale {sym}: {e}")
        continue

print(f"FYLHO PERP UNIVERSAL - {datetime.utcnow()} - Memory: {memory}")
