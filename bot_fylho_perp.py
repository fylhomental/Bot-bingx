import ccxt, os, pandas as pd, time
print("=== FYLHO V2.6 RECYCLAGE 20USDT ===")
API_KEY=os.getenv('BINGX_API_KEY')
SECRET=os.getenv('BINGX_SECRET_KEY')
ex=ccxt.bingx({'apiKey':API_KEY,'secret':SECRET,'options':{'defaultType':'swap'},'enableRateLimit':True})
try: ex.set_position_mode(False)
except: pass
mkts=ex.load_markets()

bal=ex.fetch_balance()
free=bal.get('USDT',{}).get('free',0)
print(f"Solde Futures: {free:.2f} USDT")

positions=ex.fetch_positions()
open_pos=[p for p in positions if float(p.get('contracts',0))>0]
print(f"Positions ouvertes: {len(open_pos)}")
for p in open_pos:
    pnl=float(p.get('unrealizedPnl',0) or 0)
    print(f" - {p['symbol']} {p['side']} {p['contracts']} PnL {pnl:.2f}")

MAX_POS=2
TRADE_USDT=5

def get_rsi(sym):
    try:
        o=ex.fetch_ohlcv(sym,'1h',limit=100)
        df=pd.DataFrame(o,columns=['t','o','h','l','c','v'])
        d=df['c'].diff()
        g=d.where(d>0,0).rolling(14).mean()
        l=-d.where(d<0,0).rolling(14).mean()
        r=100-(100/(1+g/l))
        return float(r.iloc[-1])
    except: return 50

need_recycle = len(open_pos) >= MAX_POS
if need_recycle:
    print(f"MODE RECYCLAGE ACTIF - on va fermer la plus vieille