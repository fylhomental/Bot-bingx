import ccxt, os, json, requests
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
        try: return json.loads(open(MEM_FILE).read())
        except: return {}
    return {}
def save_mem(m): open(MEM_FILE, "w").write(json.dumps(m))

def rsi_calc(closes, period=14):
    if len(closes) < period + 1: return 50
    gains, losses = 0, 0
    for i in range(1, period+1):
        diff = closes[-i] - closes[-i-1]
        if diff > 0: gains += diff
        else: losses -= diff
    if losses == 0: return 100
    rs = gains / losses
    return 100 - (100 / (1 + rs))

def cancel_sl_tp(ex, sym_fut):
    try:
        orders = ex.fetch_open_orders(sym_fut)
        for o in orders:
            if o['type'] in ['stop', 'stopMarket', 'takeProfitMarket', 'takeProfit']:
                ex.cancel_order(o['id'], sym_fut)
    except: pass

def place_sl_tp(ex, sym_fut, qty, sl_price, tp_price):
    cancel_sl_tp(ex, sym_fut)
    # SL
    try:
        ex.create_order(sym_fut, 'STOP_MARKET', 'sell', qty, None, params={'stopPrice': sl_price, 'positionSide': 'LONG'})
    except:
        try:
            ex.create_order(sym_fut, 'stopMarket', 'sell', qty, None, params={'stopPrice': sl_price})
        except Exception as e:
            send_tg(f"⚠️ SL fail {sym_fut}: {e}")
    # TP
    try:
        ex.create_order(sym_fut, 'TAKE_PROFIT_MARKET', 'sell', qty, None, params={'stopPrice': tp_price, 'positionSide': 'LONG'})
    except:
        try:
            ex.create_order(sym_fut, 'takeProfitMarket', 'sell', qty, None, params={'stopPrice': tp_price})
        except:
            try:
                ex.create_order(sym_fut, 'limit', 'sell', qty, tp_price)
            except Exception as e:
                send_tg(f"⚠️ TP fail {sym_fut}: {e}")

ex_fut = ccxt.bingx({'apiKey': os.getenv("BINGX_API_KEY"), 'secret': os.getenv("BINGX_SECRET_KEY"), 'options': {'defaultType': 'swap'}})
ex_spot = ccxt.bingx({'apiKey': os.getenv("BINGX_API_KEY"), 'secret': os.getenv("BINGX_SECRET_KEY"), 'options': {'defaultType': 'spot'}})

memory = load_mem()

for sym in SYMBOLS:
    try:
        sym_fut = sym.replace("/USDT", "/USDT:USDT")
        ohlcv = ex_spot.fetch_ohlcv(sym, '15m', limit=100)
        closes = [c[4] for c in ohlcv]
        price = closes[-1]
        rsi = rsi_calc(closes, RSI_PERIOD)

        if sym in memory:
            entry = memory[sym]['entry']
            high = max(memory[sym].get('high', entry), price)
            memory[sym]['high'] = high
            profit_pct = (price - entry) / entry * 100
            qty = memory[sym]['qty']

            # BE +2% -> remonte SL sur BingX
            if profit_pct >= BE_PCT and not memory[sym].get('be_done'):
                place_sl_tp(ex_fut, sym_fut, qty, entry, memory[sym]['tp'])
                memory[sym]['sl'] = entry
                memory[sym]['be_done'] = True
                save_mem(memory)
                send_tg(f"🔒 BE AUTO {sym} SL -> {entry:.5f}")

            # Trailing -5% depuis high
            if profit_pct > 0 and (high - price) / high * 100 >= TRAILING_PCT:
                try:
                    pos = ex_fut.fetch_positions([sym_fut])
                    for p in pos:
                        if p['symbol'] == sym_fut and float(p['contracts']) > 0:
                            ex_fut.create_market_sell_order(sym_fut, float(p['contracts']))
                            send_tg(f"💰 TRAILING CLOSE {sym} {profit_pct:.2f}%")
                    if sym in memory:
                        del memory[sym]
                        save_mem(memory)
                except Exception as e:
                    send_tg(f"❌ Err CLOSE {sym}: {e}")
                continue

            # SL -8%
            if profit_pct <= -SL_PCT:
                try:
                    pos = ex_fut.fetch_positions([sym_fut])
                    for p in pos:
                        if p['symbol'] == sym_fut and float(p['contracts']) > 0:
                            ex_fut.create_market_sell_order(sym_fut, float(p['contracts']))
                            send_tg(f"🛑 SL -8% {sym} {profit_pct:.2f}%")
                    del memory[sym]
                    save_mem(memory)
                except: pass
                continue

        if rsi < RSI_SEUIL and sym not in memory:
            try: ex_fut.set_leverage(LEVERAGE, sym_fut, params={'side': 'BOTH'})
            except:
                try:
                    ex_fut.set_leverage(LEVERAGE, sym_fut, params={'side': 'LONG'})
                    ex_fut.set_leverage(LEVERAGE, sym_fut, params={'side': 'SHORT'})
                except: pass

            qty = (AMOUNT_USDT * LEVERAGE) / price
            sl_price = price * (1 - SL_PCT / 100)
            tp_price = price * (1 + TRAILING_PCT / 100)

            ex_fut.create_market_buy_order(sym_fut, qty)
            place_sl_tp(ex_fut, sym_fut, qty, sl_price, tp_price)

            memory[sym] = {'entry': price, 'high': price, 'sl': sl_price, 'tp': tp_price, 'be_done': False, 'qty': qty}
            save_mem(memory)
            send_tg(f"🚀 LONG {sym} x{LEVERAGE} {price:.5f} RSI {rsi:.1f} SL {sl_price:.5f} TP {tp_price:.5f}")

    except Exception as e:
        send_tg(f"❌ {sym}: {e}")
        continue

print(f"V2 OK {datetime.utcnow()}")
