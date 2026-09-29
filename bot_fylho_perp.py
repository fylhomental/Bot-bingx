import ccxt, os, json, time
import pandas as pd

API_KEY = os.getenv("BINGX_API_KEY")
API_SECRET = os.getenv("BINGX_SECRET_KEY")
AMOUNT = 5
LEV = 5
TRAIL = 3.0
SL_PCT = 5.0 # -5% Stop Loss
TP_PCT = 10.0 # +10% Take Profit
MEM_FILE = "bot_perp_memory.json"

def get_rsi(symbol, exchange):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain/loss
        rsi = 100 - (100/(1+rs))
        return float(rsi.iloc[-1])
    except:
        return 50

exchange = ccxt.bingx({
    'apiKey': API_KEY, 'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

print(f"=== FYLHOMENTAL PERP V2 SL:{SL_PCT}% TP:{TP_PCT}% ===")
exchange.load_markets()
tickers = exchange.fetch_tickers()

usdt_markets = []
for sym, t in tickers.items():
    if '/USDT' in sym and t.get('quoteVolume'):
        usdt_markets.append((sym, t['quoteVolume']))
usdt_markets.sort(key=lambda x: x[1], reverse=True)
TOP_100 = [x[0] for x in usdt_markets[:100]]

all_rsi = []
for sym in TOP_100:
    rsi = get_rsi(sym, exchange)
    all_rsi.append((sym, rsi))
    time.sleep(0.1)

all_rsi.sort(key=lambda x: x[1])
longs = [x for x in all_rsi if x[1] < 35][:5]
shorts = [x for x in all_rsi if x[1] > 70][:5]

memory = json.load(open(MEM_FILE)) if os.path.exists(MEM_FILE) else {}

def place_sl_tp(symbol, side, entry_price, amount):
    try:
        if side == "long":
            sl_price = entry_price * (1 - SL_PCT/100)
            tp_price = entry_price * (1 + TP_PCT/100)
            # SL
            exchange.create_order(symbol, 'STOP_MARKET', 'sell', amount, None, {'stopPrice': sl_price})
            # TP
            exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', 'sell', amount, None, {'stopPrice': tp_price})
        else:
            sl_price = entry_price * (1 + SL_PCT/100)
            tp_price = entry_price * (1 - TP_PCT/100)
            exchange.create_order(symbol, 'STOP_MARKET', 'buy', amount, None, {'stopPrice': sl_price})
            exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', 'buy', amount, None, {'stopPrice': tp_price})
        print(f"SL/TP placé {symbol} SL:{sl_price} TP:{tp_price}")
    except Exception as e:
        print(f"Erreur SL/TP {symbol}: {e}")

for sym, rsi in longs:
    if sym not in memory:
        try:
            try: exchange.set_leverage(LEV, sym)
            except: pass
            exchange.create_market_buy_order(sym, AMOUNT)
            price = exchange.fetch_ticker(sym)['last']
            place_sl_tp(sym, "long", price, AMOUNT)
            memory[sym] = {"side":"long","entry":price,"high":price,"low":price}
            print(f"OPEN LONG {sym} RSI {rsi:.1f} @ {price}")
        except Exception as e:
            print(f"Err LONG {sym}: {e}")

for sym, rsi in shorts:
    if sym not in memory:
        try:
            try: exchange.set_leverage(LEV, sym)
            except: pass
            exchange.create_market_sell_order(sym, AMOUNT)
            price = exchange.fetch_ticker(sym)['last']
            place_sl_tp(sym, "short", price, AMOUNT)
            memory[sym] = {"side":"short","entry":price,"high":price,"low":price}
            print(f"OPEN SHORT {sym} RSI {rsi:.1f} @ {price}")
        except Exception as e:
            print(f"Err SHORT {sym}: {e}")

# Trailing de sécurité en plus du SL/TP
for sym in list(memory.keys()):
    try:
        price = exchange.fetch_ticker(sym)['last']
        p = memory[sym]
        if p['side'] == 'long':
            if price > p['high']: p['high'] = price
            if ((price - p['high'])/p['high']*100) <= -TRAIL:
                exchange.create_market_sell_order(sym, AMOUNT)
                print(f"CLOSE TRAIL LONG {sym}")
                del memory[sym]
        else:
            if price < p['low']: p['low'] = price
            if ((price - p['low'])/p['low']*100) >= TRAIL:
                exchange.create_market_buy_order(sym, AMOUNT)
                print(f"CLOSE TRAIL SHORT {sym}")
                del memory[sym]
    except: pass

with open(MEM_FILE, 'w') as f:
    json.dump(memory, f, indent=2)