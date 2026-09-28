import ccxt, os, json, time
import pandas as pd

# --- CONFIG FYLHOMENTAL ---
API_KEY = os.getenv("BINGX_API_KEY")
API_SECRET = os.getenv("BINGX_SECRET_KEY")
AMOUNT_USDT = 5
TRAILING_PCT = 3.0
MEMORY_FILE = "bot_meme_memory.json"

# TOP 50 MEMES
TOP_MEMES = [
    "DOGE/USDT","SHIB/USDT","PEPE/USDT","BONK/USDT","WIF/USDT","FLOKI/USDT","MEME/USDT",
    "BABYDOGE/USDT","BOME/USDT","MEW/USDT","POPCAT/USDT","BRETT/USDT","MOG/USDT",
    "TURBO/USDT","LADYS/USDT","WOJAK/USDT","COQ/USDT","MYRO/USDT","WEN/USDT","PONKE/USDT",
    "BODEN/USDT","TREMP/USDT","MAGA/USDT","PEPECOIN/USDT","HOGE/USDT","MONA/USDT",
    "DOG/USDT","CAT/USDT","RATS/USDT","ORDI/USDT","1000SATS/USDT","CORGIAI/USDT"
]

def get_rsi(symbol, exchange):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    except:
        return 100

exchange = ccxt.bingx({'apiKey': API_KEY, 'secret': API_SECRET, 'enableRateLimit': True})

if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, 'r') as f:
        memory = json.load(f)
else:
    memory = {}

print("Scan TOP memes...")
rsi_list = []
for sym in TOP_MEMES:
    rsi = get_rsi(sym, exchange)
    print(f"{sym} RSI: {rsi:.1f}")
    if rsi < 35:
        rsi_list.append((sym, rsi))
    time.sleep(0.2)

rsi_list.sort(key=lambda x: x[1])
to_buy = rsi_list[:5]

for sym, rsi in to_buy:
    if sym not in memory:
        try:
            bal = exchange.fetch_balance()
            if bal['free'].get('USDT', 0) < AMOUNT_USDT:
                continue
            exchange.create_market_buy_order(sym, AMOUNT_USDT)
            time.sleep(1)
            ticker = exchange.fetch_ticker(sym)
            price = ticker['last']
            coin = sym.split('/')[0]
            qty = exchange.fetch_balance()['total'].get(coin, 0)
            memory[sym] = {"qty": qty, "buy_price": price, "highest": price}
            print(f"ACHAT {sym} RSI {rsi:.1f}")
        except Exception as e:
            print(f"Erreur achat {sym}: {e}")

for sym in list(memory.keys()):
    try:
        price = exchange.fetch_ticker(sym)['last']
        if price > memory[sym]['highest']:
            memory[sym]['highest'] = price
        drop_pct = ((price - memory[sym]['highest']) / memory[sym]['highest']) * 100
        if drop_pct <= -TRAILING_PCT:
            coin = sym.split('/')[0]
            exchange.create_market_sell_order(sym, memory[sym]['qty'])
            print(f"VENTE {sym}")
            del memory[sym]
    except Exception as e:
        print(f"Erreur vente {sym}: {e}")

with open(MEMORY_FILE, 'w') as f:
    json.dump(memory, f, indent=2)