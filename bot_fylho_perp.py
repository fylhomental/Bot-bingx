import ccxt
import os
import json
import time
import pandas as pd

API_KEY = os.getenv("BINGX_API_KEY")
API_SECRET = os.getenv("BINGX_SECRET_KEY")
AMOUNT = 5
LEV = 10
TP_PCT = 3.0 # = +30% PnL en x10
SL_PCT = 1.5 # = -15% PnL en x10
MEM_FILE = "bot_perp_memory.json"

# Matières premières forcées même si pas dans Top volume
COMMODITIES = ["GOLD/USDT:USDT", "XAU/USDT:USDT", "SILVER/USDT:USDT", "XAG/USDT:USDT", "OIL/USDT:USDT", "USOIL/USDT:USDT", "UKOIL/USDT:USDT", "NATGAS/USDT:USDT"]

def get_rsi(symbol, exchange):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    except:
        return 50

exchange = ccxt.bingx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'swap'}
})

memory = json.load(open(MEM_FILE)) if os.path.exists(MEM_FILE) else {}

exchange.load_markets()
tickers = exchange.fetch_tickers()

usdt_markets = []
for sym, t in tickers.items():
    if '/USDT' in sym and t.get('quoteVolume') is not None:
        usdt_markets.append((sym, t['quoteVolume']))

usdt_markets.sort(key=lambda x: x[1], reverse=True)
TOP_LIST = [x[0] for x in usdt_markets[:120]]

# Ajout forcé des matières premières
for c in COMMODITIES:
    if c in exchange.markets and c not in TOP_LIST:
        TOP_LIST.append(c)

print(f"=== FYLHO PERP UNIVERSAL x10 + SL/TP AUTO ===")
print(f"Scanning {len(TOP_LIST)} marchés avec matières premières: {COMMODITIES}")

all_rsi = []
for sym in TOP_LIST:
    rsi = get_rsi(sym, exchange)
    print(f"{sym} RSI {rsi:.1f}")
    all_rsi.append((sym, rsi))
    time.sleep(0.12)

all_rsi.sort(key=lambda x: x[1])
longs = [x for x in all_rsi if x[1] < 40][:3]
shorts = [x for x in all_rsi if x[1] > 60][:3]

print(f"LONG signal: {longs}")
print(f"SHORT signal: {shorts}")

# OPEN LONG avec SL/TP AUTO
for sym, rsi in longs:
    if sym not in memory:
        try:
            try:
                exchange.set_leverage(LEV, sym)
            except:
                pass
            exchange.create_market_buy_order(sym, AMOUNT)
            price = exchange.fetch_ticker(sym)['last']
            tp_price = price * (1 + TP_PCT / 100)
            sl_price = price * (1 - SL_PCT / 100)
            try:
                exchange.create_order(sym, 'TAKE_PROFIT_MARKET', 'sell', AMOUNT, None, {'stopPrice': tp_price, 'closePosition': True})
                exchange.create_order(sym, 'STOP_MARKET', 'sell', AMOUNT, None, {'stopPrice': sl_price, 'closePosition': True})
                print(f"TP/SL posé LONG {sym} TP {tp_price:.4f} SL {sl_price:.4f}")
            except Exception as e:
                print(f"Erreur pose TP/SL LONG {sym}: {e}")
            memory[sym] = {"side": "long", "entry": price}
            print(f"OPEN LONG {sym} RSI {rsi:.1f} @ {price}")
        except Exception as e:
            print(f"Err LONG {sym}: {e}")

# OPEN SHORT avec SL/TP AUTO
for sym, rsi in shorts:
    if sym not in memory:
        try:
            try:
                exchange.set_leverage(LEV, sym)
            except:
                pass
            exchange.create_market_sell_order(sym, AMOUNT)
            price = exchange.fetch_ticker(sym)['last']
            tp_price = price * (1 - TP_PCT / 100)
            sl_price = price * (1 + SL_PCT / 100)
            try:
                exchange.create_order(sym, 'TAKE_PROFIT_MARKET', 'buy', AMOUNT, None, {'stopPrice': tp_price, 'closePosition': True})
                exchange.create_order(sym, 'STOP_MARKET', 'buy', AMOUNT, None, {'stopPrice': sl_price, 'closePosition': True})
                print(f"TP/SL posé SHORT {sym} TP {tp_price:.4f} SL {sl_price:.4f}")
            except Exception as e:
                print(f"Erreur pose TP/SL SHORT {sym}: {e}")
            memory[sym] = {"side": "short", "entry": price}
            print(f"OPEN SHORT {sym} RSI {rsi:.1f} @ {price}")
        except Exception as e:
            print(f"Err SHORT {sym}: {e}")

with open(MEM_FILE, 'w') as f:
    json.dump(memory, f, indent=2)

print("=== FIN SCAN ===")
