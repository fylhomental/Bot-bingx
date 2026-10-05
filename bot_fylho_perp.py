import ccxt, os, json, requests, time
from datetime import datetime

SYMBOLS = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","XRP/USDT"]
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
            with open(MEM_FILE) as f: return json.load(f)
        except: return {}
    return {}

def save_mem(m):
    with open(MEM_FILE, "w") as f: json.dump(m, f)

def get_rsi(exchange, symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=100)
        closes = [c[4] for c in ohlcv]
        gains, losses = [], []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            if diff > 0: gains.append(diff); losses.append(0)
            else: gains.append(0); losses.append(abs(diff))
        if len(gains) < RSI_PERIOD: return 50
        avg_gain = sum(gains[-RSI_PERIOD:]) / RSI_PERIOD
        avg_loss = sum(losses[-RSI_PERIOD:]) / RSI_PERIOD
        if avg_loss == 0: return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1+rs))
    except: return 50

# --- MAIN ---
exchange = ccxt.bitget({
    'apiKey': os.getenv('BITGET_API_KEY'),
    'secret': os.getenv('BITGET_SECRET'),
    'password': os.getenv('BITGET_PASSPHRASE'),
    'options': {'defaultType': 'swap'}
})

mem = load_mem()
print(f"[{datetime.now()}] START SL={SL_PCT}% BE={BE_PCT}% TRAIL={TRAILING_PCT}%")

for sym in SYMBOLS:
    try:
        rsi = get_rsi(exchange, sym)
        print(f"{sym} RSI={rsi:.1f}")
        if rsi < RSI_SEUIL and sym not in mem:
            print(f"BUY {sym}")
            # logique d'achat ici
            mem[sym] = {"entry": time.time(), "rsi": rsi}
            send_tg(f"BUY {sym} RSI {rsi:.1f} SL {SL_PCT}%")
    except Exception as e:
        print(f"ERR {sym}: {e}")

save_mem(mem)
print("DONE")
