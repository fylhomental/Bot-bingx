import ccxt, os, json, time
import pandas as pd

# --- CONFIG FYLHOMENTAL ---
API_KEY = os.getenv("BINGX_API_KEY")
API_SECRET = os.getenv("BINGX_SECRET_KEY")
AMOUNT_USDT = 5
TRAILING_PCT = 3.0
MEMORY_FILE = "MEMORY_FILE = "bot_meme_memory.json"

# TOP 50 MEMES - il scannera dedans
TOP_MEMES = [
    "DOGE/USDT","SHIB/USDT","PEPE/USDT","BONK/USDT","WIF/USDT","FLOKI/USDT","MEME/USDT",
    "BABYDOGE/USDT","PEPE2/USDT","BOME/USDT","MEW/USDT","POPCAT/USDT","BRETT/USDT",
    "MOG/USDT","TURBO/USDT","LADYS/USDT","WOJAK/USDT","BEN/USDT","PSYOP/USDT",
    "COQ/USDT","MYRO/USDT","WEN/USDT","PONKE/USDT","SMOG/USDT","SLERF/USDT",
    "BODEN/USDT","TREMP/USDT","MAGA/USDT","PEPECOIN/USDT","KISHU/USDT","SAITAMA/USDT",
    "ELON/USDT","HOGE/USDT","MONA/USDT","DOG/USDT","CAT/USDT","RATS/USDT","SATS/USDT",
    "ORDI/USDT","1000SATS/USDT","BONK/USDT","CORGIAI/USDT","AIDOGE/USDT"
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

# Charge mémoire
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, 'r') as f:
        memory = json.load(f)
else:
    memory = {}

# 1. SCAN DES PLUS BAS
print("Scan TOP memes...")
rsi_list = []
for sym in TOP_MEMES:
    rsi = get_rsi(sym, exchange)
    print(f"{sym} RSI: {rsi:.1f}")
    if rsi < 35:
        rsi_list.append((sym, rsi))
    time.sleep(0.2)

rsi_list.sort(key=lambda x: x[1]) # du plus bas au moins bas
to_buy = rsi_list[:5] # les 5 plus bas

# 2. ACHAT
for sym, rsi in to_buy:
    if sym not in memory: # n'achète pas s'il l'a déjà
        try:
            bal = exchange.fetch_balance()
            usdt_free = bal['free'].get('USDT', 0)
            if usdt_free < AMOUNT_USDT:
                print(f"Solde insuffisant pour {sym}: {usdt_free}$")
                continue
            # achat market
            exchange.create_market_buy_order(sym, AMOUNT_USDT) # achat en USDT
            # on récupère qty achetée
            time.sleep(1)
            bal = exchange.fetch_balance()
            coin = sym.split('/')[0]
            qty = bal['total'].get(coin, 0)
            # on sauvegarde
            ticker = exchange.fetch_ticker(sym)
            price = ticker['last']
            memory[sym] = {"qty": qty, "buy_price": price, "highest": price}
            print(f"ACHAT {sym} RSI {rsi:.1f} au plus bas")
        except Exception as e:
            print(f"Erreur achat {sym}: {e}")

# 3. VENTE AU PLUS HAUT (uniquement ses propres achats)
for sym in list(memory.keys()):
    try:
        ticker = exchange.fetch_ticker(sym)
        price = ticker['last']
        # maj plus haut
        if price > memory[sym]['highest']:
            memory[sym]['highest'] = price

        highest = memory[sym]['highest']
        drop_pct = ((price - highest) / highest) * 100

        if drop_pct <= -TRAILING_PCT:
            coin = sym.split('/')[0]
            qty = memory[sym]['qty']
            exchange.create_market_sell_order(sym, qty)
            print(f"VENTE {sym} au plus haut -3% | Haut: {highest} Actuel: {price}")
            del memory[sym] # supprime de sa mémoire
    except Exception as e:
        print(f"Erreur vente {sym}: {e}")

# Sauvegarde mémoire
with open(MEMORY_FILE, 'w') as f:
    json.dump(memory, f, indent=2)