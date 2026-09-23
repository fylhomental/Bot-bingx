import requests, os

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send(msg):
    if not TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def get_rsi(symbol="BTCUSDT", interval="1h", period=14):
    # Prix de Binance
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
    data = requests.get(url).json()
    closes = [float(x[4]) for x in data]

    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

try:
    rsi = get_rsi("BTCUSDT", "1h", 14)
    msg = ""

    if rsi < 30:
        msg = f"🚨 *CRASH* BTC RSI 1h: {rsi}"
    elif rsi < 35:
        msg = f"💚 *ACHAT* BTC RSI 1h: {rsi}"
    elif rsi > 65:
        msg = f"🔴 *VENTE* BTC RSI 1h: {rsi}"

    if msg:
        send(msg)
        print(msg)
    else:
        print(f"RAS RSI {rsi} - pas d'envoi")

except Exception as e:
    print(f"Erreur: {e}")