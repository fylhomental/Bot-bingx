import os, ccxt, requests, time
TOKEN=os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID=os.getenv("TELEGRAM_CHAT_ID")
BINGX_API_KEY=os.getenv("BINGX_API_KEY")
BINGX_SECRET=os.getenv("BINGX_SECRET")
SYMBOLS=["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","XRP/USDT"]
AMOUNT_USDT=10
RSI_SEUIL=30
TP_PCT=3.0

def send_tg(msg):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except: pass
    print(msg)

def get_rsi_price(s):
    ex=ccxt.bingx({'enableRateLimit': True})
    candles=ex.fetch_ohlcv(s,'1h',limit=100)
    closes=[c[4] for c in candles]
    price=closes[-1]
    gains=[];losses=[]
    for i in range(1,len(closes)):
        d=closes[i]-closes[i-1]
        gains.append(d) if d>0 else losses.append(abs(d))
    avg_g=sum(gains[-14:])/14 if len(gains)>=14 else 1
    avg_l=sum(losses[-14:])/14 if len(losses)>=14 else 1
    rsi=100-(100/(1+avg_g/(avg_l+0.0001)))
    return price,rsi

ex_spot=ccxt.bingx({'apiKey':BINGX_API_KEY,'secret':BINGX_SECRET,'options':{'defaultType':'spot'}})
for sym in SYMBOLS:
    try:
        price,rsi=get_rsi_price(sym)
        if rsi<RSI_SEUIL:
            qty=AMOUNT_USDT/price
            ex_spot.create_market_buy_order(sym,qty)
            tp=price*(1+TP_PCT/100)
            try: ex_spot.create_order(sym,'limit','sell',qty,tp)
            except: pass
            send_tg(f"💸 SPOT REEL {sym} {AMOUNT_USDT}$ RSI {rsi:.1f}\nTP +{TP_PCT}% ${tp:.2f} ✅")
        else:
            send_tg(f"💰 {sym} RSI {rsi:.1f} - Attente")
        time.sleep(2)
    except Exception as e:
        send_tg(f"❌ {sym} SPOT: {e}")