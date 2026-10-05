import ccxt, os, json, requests, time
from datetime import datetime

SYMBOLS = ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","XRP/USDT"]
LEVERAGE = 5
AMOUNT_USDT = 10
RSI_SEUIL = 35
RSI_PERIOD = 14
SL_PCT = 8.0
TRAILING_PCT = 3.5
BE_PCT = 1.5

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

# --- CONNEXION BINGX ---
exchange = ccxt.bingx({
    'apiKey': os.getenv('BINGX_API_KEY') or os.getenv('BITGET_API_KEY'),
    'secret': os.getenv('BINGX_SECRET') or os.getenv('BITGET_SECRET'),
    'options': {'defaultType': 'swap'}
})

mem = load_mem()
print(f"[{datetime.now()}] BINGX START SL={SL_PCT}% BE={BE_PCT}% TRAIL={TRAILING_PCT}%")

# 1. GESTION POSITIONS (SL / BE / TRAILING)
try:
    positions = exchange.fetch_positions()
    for pos in positions:
        sym = pos['symbol']
        if pos['contracts'] and float(pos['contracts']) > 0:
            entry = float(pos['entryPrice'] or 0)
            mark = float(pos['markPrice'] or 0)
            if entry==0: continue
            pnl_pct = (mark - entry) / entry * 100

            if sym not in mem: mem[sym] = {}
            highest = mem[sym].get('highest', entry)
            if mark > highest: highest = mark
            mem[sym]['highest'] = highest

            print(f"{sym} PnL={pnl_pct:.2f}% High={highest}")

            if pnl_pct <= -SL_PCT:
                print(f"SL HIT {sym}")
                exchange.create_market_order(sym, 'sell', pos['contracts'])
                send_tg(f"🔴 SL -8% {sym}")
                if sym in mem: del mem[sym]
            elif pnl_pct >= BE_PCT:
                drop = (highest - mark) / highest * 100
                if drop >= TRAILING_PCT:
                    print(f"TRAILING TP HIT {sym}")
                    exchange.create_market_order(sym, 'sell', pos['contracts'])
                    send_tg(f"🟢 TP Trailing {sym} +{pnl_pct:.2f}%")
                    if sym in mem: del mem[sym]
except Exception as e:
    print(f"ERR pos: {e}")

# 2. ENTREES RSI
for sym in SYMBOLS:
    try:
        rsi = get_rsi(exchange, sym)
        print(f"{sym} RSI={rsi:.1f}")
        has_pos = False
        try:
            for p in exchange.fetch_positions():
                if p['symbol']==sym and p['contracts'] and float(p['contracts'])>0:
                    has_pos=True
        except: pass
        if rsi < RSI_SEUIL and not has_pos:
            print(f"BUY {sym} RSI {rsi}")
            price = exchange.fetch_ticker(sym)['last']
            qty = (AMOUNT_USDT * LEVERAGE) / price
            try: exchange.set_leverage(LEVERAGE, sym)
            except: pass
            exchange.create_market_order(sym, 'buy', qty)
            mem[sym] = {"entry": price, "highest": price, "rsi": rsi}
            send_tg(f"🟡 BUY {sym} RSI {rsi:.1f}")
    except Exception as e:
        print(f"ERR {sym}: {e}")

save_mem(mem)
print("DONE")
