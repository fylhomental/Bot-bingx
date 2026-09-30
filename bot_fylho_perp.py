import os, ccxt, requests, time
API_KEY=os.getenv('BINGX_API_KEY')
SECRET=os.getenv('BINGX_SECRET_KEY')
TG_TOKEN=os.getenv('TELEGRAM_BOT_TOKEN')
TG_CHAT=os.getenv('TELEGRAM_CHAT_ID')
TRADE_USDT=7
MAX_POS=4
LEVERAGE=5

def tg(msg):
    if not TG_TOKEN or not TG_CHAT: return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id":TG_CHAT,"text":msg}, timeout=10)
    except: pass

print("=== FYLHO V2.8 32USDT 4x7 + TG ===")
ex=ccxt.bingx({'apiKey':API_KEY,'secret':SECRET,'options':{'defaultType':'swap'},'enableRateLimit':True})
try: ex.load_markets()
except: pass

# 1. Solde
bal=ex.fetch_balance()
total=float(bal['USDT']['total'] or 0)
free=float(bal['USDT']['free'] or 0)
print(f"Solde Futures Total: {total:.2f} USDT (libre {free:.2f})")

# 2. Positions actuelles
positions=ex.fetch_positions()
open_syms=[]
pnl_txt=""
for p in positions:
    if float(p.get('contracts',0) or 0)!=0:
        sym=p['symbol'].split('/')[0].split(':')[0]
        side=p['side']
        pnl=float(p.get('unrealizedPnl',0) or 0)
        open_syms.append(sym)
        pnl_txt+=f"{sym} {side} {pnl:+.2f}$\n"
print(f"Positions ouvertes: {len(open_syms)} {open_syms}")

# 3. Trading
COINS=["BTC/USDT:USDT","ETH/USDT:USDT","SOL/USDT:USDT","AVAX/USDT:USDT","NEAR/USDT:USDT","ZEC/USDT:USDT"]
if len(open_syms)>=MAX_POS:
    print("MAX POS atteint")
else:
    for pair in COINS:
        coin=pair.split('/')[0]
        if coin in open_syms: continue
        if len(open_syms)>=MAX_POS: break
        try:
            ohlcv=ex.fetch_ohlcv(pair,'1h',limit=100)
            closes=[c[4] for c in ohlcv]
            # RSI 14
            gains=0;losses=0
            for i in range(1,15):
                diff=closes[-i]-closes[-i-1]
                if diff>0: gains+=diff
                else: losses-=diff
            if losses==0: rsi=100
            else:
                rs=gains/losses
                rsi=100-(100/(1+rs))

            side=None
            if rsi<35: side='buy'
            elif rsi>65: side='sell'

            if side:
                price=closes[-1]
                amount=TRADE_USDT/price
                # leverage
                try: ex.set_leverage(LEVERAGE, pair)
                except: pass
                # TP 10% SL 5%
                tp_price = price*1.10 if side=='buy' else price*0.90
                sl_price = price*0.95 if side=='buy' else price*1.05
                ex.create_order(pair,'market',side,amount,None,{'takeProfit':tp_price,'stopLoss':sl_price})
                msg=f"{'🟢 LONG' if side=='buy' else '🔴 SHORT'} {coin} 7$ x{LEVERAGE} RSI {rsi:.1f}\nSolde: {total:.2f}$"
                print(f"OPEN {msg}")
                tg(f"🚀 {msg}\nTP +10% / SL -5% auto")
                open_syms.append(coin)
                time.sleep(1)
        except Exception as e:
            print(f"Err {coin}: {e}")

# 4. Rapport final + TG
final=f"💼 FYLHO V2.8\nSolde: {total:.2f}$ (libre {free:.2f}$)\nPositions: {len(open_syms)}/4\n{pnl_txt}"
print("FIN RUN")
tg(final)