import os, ccxt, requests, time
TOKEN=os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID=os.getenv("TELEGRAM_CHAT_ID")
BINGX_API_KEY=os.getenv("BINGX_API_KEY")
BINGX_SECRET=os.getenv("BINGX_SECRET")
SYMBOLS=["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","XRP/USDT"]
AMOUNT_USDT=5
LEVERAGE=5
RSI_SEUIL=30
TP_PCT=3.0
SL_PCT=2.0

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

ex_fut=ccxt.bingx({'apiKey':BINGX_API_KEY,'secret':BINGX_SECRET,'options':{'defaultType':'swap'}})
for sym in SYMBOLS:
    try:
        price,rsi=get_rsi_price(sym)
        sym_fut=sym+":USDT"
        if rsi<RSI_SEUIL:
            ex_fut.set_leverage(LEVERAGE,sym_fut)
            qty=(AMOUNT_USDT*LEVERAGE)/price
            ex_fut.create_market_buy_order(sym_fut,qty)
            tp=price*(1+TP_PCT/100)
            sl=price*(1-SL_PCT/100)
            # TP/SL
            try:
                ex_fut.create_order(sym_fut,'limit','sell',qty,tp,{'takeProfit':tp})
                ex_fut.create_order(sym_fut,'limit','sell',qty,sl,{'stopLoss':sl})
            except: pass
            send_tg(f"🚀 LONG REEL {sym} x{LEVERAGE} {AMOUNT_USDT}$ RSI {rsi:.1f}\nTP +{TP_PCT}% ${tp:.2f} | SL -{SL_PCT}% ${sl:.2f} ✅")
        else:
            send_tg(f"🤖 {sym} RSI {rsi:.1f} - Attente")
        time.sleep(2)
    except Exception as e:
        send_tg(f"❌ {sym} FUTURES: {e}")