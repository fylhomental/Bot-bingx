import os, ccxt, json, time, requests

TOKEN=os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID=os.getenv("TELEGRAM_CHAT_ID")
BINGX_API_KEY=os.getenv("BINGX_API_KEY")
BINGX_SECRET=os.getenv("BINGX_SECRET")

SYMBOLS=["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","XRP/USDT","DOGE/USDT"]
AMOUNT_USDT=5
LEVERAGE=5
RSI_SEUIL=35
TRAILING_PCT=5.0 # il laisse grimper 5%
SL_PCT=8.0 # coupe à -8% max
BE_TRIGGER=2.0 # si +2%, met le stop à 0

MEM_FILE="bot_fylho_perp_memory.json"

def send_tg(msg):
    try: requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id":CHAT_ID,"text":msg})
    except: pass
    print(msg)

def load_mem():
    if os.path.exists(MEM_FILE):
        try: return json.load(open(MEM_FILE))
        except: return {}
    return {}

def save_mem(m):
    json.dump(m, open(MEM_FILE,"w"))

def get_rsi_price(s):
    ex=ccxt.bingx({'enableRateLimit': True})
    candles=ex.fetch_ohlcv(s,'1h',limit=100)
    closes=[c[4] for c in candles]
    price=closes[-1]
    gains=[];losses=[]
    for i in range(1,len(closes)):
        d=closes[i]-closes[i-1]
        gains.append(d if d>0 else 0)
        losses.append(-d if d<0 else 0)
    avg_g=sum(gains[-14:])/14 if len(gains)>=14 else 0.01
    avg_l=sum(losses[-14:])/14 if len(losses)>=14 else 0.01
    rsi=100-(100/(1+avg_g/(avg_l+0.0001)))
    return price,rsi

ex_fut=ccxt.bingx({'apiKey':BINGX_API_KEY,'secret':BINGX_SECRET})
memory=load_mem()

# GAGE DE PROTECTION : nettoie memory si plus de position sur BingX
try:
    positions=ex_fut.fetch_positions()
    open_syms=[p['symbol'] for p in positions if float(p.get('contracts',0))>0]
    for sym in list(memory.keys()):
        if sym+":USDT" not in open_syms and sym not in open_syms:
            del memory[sym]
    save_mem(memory)
except: pass

for sym in SYMBOLS:
    try:
        price,rsi=get_rsi_price(sym)
        sym_fut=sym+":USDT"
                # TRAILING pour les positions existantes
        if sym in memory:
            entry=memory[sym]['entry']
            high=max(memory[sym].get('high',entry), price)
            memory[sym]['high']=high
            if price >= entry*(1+BE_TRIGGER/100) and not memory[sym].get('be_done'):
                memory[sym]['sl']=entry
                memory[sym]['be_done']=True
                send_tg(f"🔒 {sym} BE à {entry:.4f}")
            if price < high*(1-TRAILING_PCT/100) or price < memory[sym].get('sl', entry*(1-SL_PCT/100)):
                qty=(AMOUNT_USDT*LEVERAGE)/price
                ex_fut.create_market_sell_order(sym_fut, qty)
                send_tg(f"💰 CLOSE {sym} {((price/entry-1)*100):.2f}%")
                del memory[sym]
                save_mem(memory)
                continue
            save_mem(memory)

                if rsi<RSI_SEUIL and sym not in memory:
            try:
                ex_fut.set_leverage(LEVERAGE, sym_fut, params={'side': 'BOTH'})
            except:
                try:
                    ex_fut.set_leverage(LEVERAGE, sym_fut, params={'side': 'LONG'})
                    ex_fut.set_leverage(LEVERAGE, sym_fut, params={'side': 'SHORT'})
                except:
                    pass
            qty=(AMOUNT_USDT*LEVERAGE)/price
            ex_fut.create_market_buy_order(sym_fut, qty)
            memory[sym]={'entry':price,'high':price,'sl':price*(1-SL_PCT/100),'be_done':False}
            save_mem(memory)
            send_tg(f"🚀 LONG REEL {sym} x{LEVERAGE} entry {price:.4f} RSI {rsi:.1f}")
        else:
            if sym not in memory:
                send_tg(f"⏳ {sym} RSI {rsi:.1f}")
        time.sleep(2)
    except Exception as e:
        send_tg(f"❌ {sym} FUTURES: {e}")
