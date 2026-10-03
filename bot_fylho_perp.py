import ccxt, os, json, time
import pandas as pd

API_KEY = os.getenv("BINGX_API_KEY")
API_SECRET = os.getenv("BINGX_SECRET_KEY")
AMOUNT = 5
LEV = 3 # baissé de 5 à 3 pour payer moins de funding
TRAIL = 5.0 # 3% -> 5% pour laisser respirer
STOP_LOSS = 8.0 # nouveau: coupe sec à -8%
MEM_FILE ="bot_fylho_perp_memory.json"
MIN_VOL = 1000000 # ignore les merdes illiquides

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

print("=== FYLHOMENTAL PERP V2 - TRAIL 5% + SL 8% ===")
exchange.load_markets()
tickers = exchange.fetch_tickers()

usdt_markets = []
for sym, t in tickers.items():
    if '/USDT' in sym and t.get('quoteVolume', 0) > MIN_VOL:
        usdt_markets.append((sym, t['quoteVolume']))

usdt_markets.sort(key=lambda x: x[1], reverse=True)
TOP_100 = [x[0] for x in usdt_markets[:100]]

print(f"Scanning {len(TOP_100)} marchés filtrés >1M vol")

all_rsi = []
for sym in TOP_100:
    rsi = get_rsi(sym, exchange)
    all_rsi.append((sym, rsi))
    time.sleep(0.12)

all_rsi.sort(key=lambda x: x[1])
longs = [x for x in all_rsi if x[1] < 32][:4] # plus strict
shorts = [x for x in all_rsi if x[1] > 68][:4]

memory = json.load(open(MEM_FILE)) if os.path.exists(MEM_FILE) else {}

# OUVERTURE
for sym, rsi in longs + shorts:
    if sym not in memory:
        try:
            side = "long" if (sym,rsi) in longs else "short"
            try: exchange.set_leverage(LEV, sym)
            except: pass
            if side == "long":
                exchange.create_market_buy_order(sym, AMOUNT)
            else:
                exchange.create_market_sell_order(sym, AMOUNT)
            price = exchange.fetch_ticker(sym)['last']
            memory[sym] = {"side":side,"entry":price,"high":price,"low":price}
            print(f"OPEN {side.upper()} {sym} RSI {rsi:.1f}")
        except Exception as e:
            print(f"Err {sym}: {e}")

# GESTION + TRAILING + STOP LOSS DUR
for sym in list(memory.keys()):
    try:
        price = exchange.fetch_ticker(sym)['last']
        p = memory[sym]
        entry = p['entry']

        # Calcul PnL %
        pnl = ((price - entry)/entry*100) if p['side']=="long" else ((entry - price)/entry*100)
        pnl = pnl * LEV # PnL avec levier

        # 1. STOP LOSS DUR -8%
        if pnl <= -STOP_LOSS:
            if p['side']=="long":
                exchange.create_market_sell_order(sym, AMOUNT)
            else:
                exchange.create_market_buy_order(sym, AMOUNT)
            print(f"STOP LOSS {sym} {pnl:.2f}%")
            del memory[sym]
            continue

        # 2. TRAILING 5%
        if p['side'] == 'long':
            if price > p['high']: p['high'] = price
            if ((price - p['high'])/p['high']*100) <= -TRAIL:
                exchange.create_market_sell_order(sym, AMOUNT)
                print(f"CLOSE LONG TRAIL {sym} {pnl:.2f}%")
                del memory[sym]
        else:
            if price < p['low']: p['low'] = price
            if ((price - p['low'])/p['low']*100) >= TRAIL:
                exchange.create_market_buy_order(sym, AMOUNT)
                print(f"CLOSE SHORT TRAIL {sym} {pnl:.2f}%")
                del memory[sym]
    except Exception as e:
        print(f"Gestion err {sym}: {e}")
        # Si position plus sur BingX mais encore dans JSON -> nettoie
        try:
            pos = exchange.fetch_positions([sym])
            if not pos or float(pos[0]['contracts'])==0:
                del memory[sym]
                print(f"CLEAN {sym} plus en position")
        except: pass

with open(MEM_FILE, 'w') as f:
    json.dump(memory, f, indent=2)
