import ccxt, os, json, time
import pandas as pd

API_KEY = os.getenv("BINGX_API_KEY")
API_SECRET = os.getenv("BINGX_SECRET_KEY")
AMOUNT = 5
LEV = 5
TRAIL = 3.0
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

print("=== FYLHOMENTAL PERP UNIVERSAL - SCAN ALL MARKETS ===")
exchange.load_markets()
tickers = exchange.fetch_tickers()

# On prend tous les marchés USDT en PERP, triés par volume
usdt_markets = []
for sym, t in tickers.items():
    if '/USDT' in sym and t.get('quoteVolume') is not None:
        usdt_markets.append((sym, t['quoteVolume']))

usdt_markets.sort(key=lambda x: x[1], reverse=True)
TOP_100 = [x[0] for x in usdt_markets[:100]] # Top 100 plus tradés (crypto + gold + oil + forex)

print(f"Scanning {len(TOP_100)} marchés: {TOP_100[:10]}...")

all_rsi = []
for sym in TOP_100:
    rsi = get_rsi(sym, exchange)
    print(f"{sym} RSI {rsi:.1f}")
    all_rsi.append((sym, rsi))
    time.sleep(0.15)

all_rsi.sort(key=lambda x: x[1])
longs = [x for x in all_rsi if x[1] < 35][:5] # 5 plus survendus
shorts = [x for x in all_rsi if x[1] > 70][:5] # 5 plus surachetés

print(f"LONG: {longs}")
print(f"SHORT: {shorts}")

memory = json.load(open(MEM_FILE)) if os.path.exists(MEM_FILE) else {}

for sym, rsi in longs:
    if sym not in memory:
        try:
            try: exchange.set_leverage(LEV, sym)
            except: pass
            exchange.create_market_buy_order(sym, AMOUNT)
            price = exchange.fetch_ticker(sym)['last']
            memory[sym] = {"side":"long","entry":price,"high":price,"low":price}
            print(f"OPEN LONG {sym} RSI {rsi:.1f}")
        except Exception as e:
            print(f"Err LONG {sym}: {e}")

for sym, rsi in shorts:
    if sym not in memory:
        try:
            try: exchange.set_leverage(LEV, sym)
            except: pass
            exchange.create_market_sell_order(sym, AMOUNT)
            price = exchange.fetch_ticker(sym)['last']
            memory[sym] = {"side":"short","entry":price,"high":price,"low":price}
            print(f"OPEN SHORT {sym} RSI {rsi:.1f}")
        except Exception as e:
            print(f"Err SHORT {sym}: {e}")

# Trailing
for sym in list(memory.keys()):
    try:
        price = exchange.fetch_ticker(sym)['last']
        p = memory[sym]
        if p['side'] == 'long':
            if price > p['high']: p['high'] = price
            if ((price - p['high'])/p['high']*100) <= -TRAIL:
                exchange.create_market_sell_order(sym, AMOUNT)
                print(f"CLOSE LONG {sym}")
                del memory[sym]
        else:
            if price < p['low']: p['low'] = price
            if ((price - p['low'])/p['low']*100) >= TRAIL:
                exchange.create_market_buy_order(sym, AMOUNT)
                print(f"CLOSE SHORT {sym}")
                del memory[sym]
    except: pass

with open(MEM_FILE, 'w') as f:
    json.dump(memory, f, indent=2)