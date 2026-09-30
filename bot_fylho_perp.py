import os,ccxt,requests
import pandas as pd

A=os.getenv('BINGX_API_KEY')
S=os.getenv('BINGX_SECRET_KEY')
T=os.getenv('TELEGRAM_BOT_TOKEN')
C=os.getenv('TELEGRAM_CHAT_ID')

SYMBOL='BTC/USDT:USDT'
TF='5m'
LEV=10
RISK=0.15
SL=0.03
TP=0.06

def tg(m):
 try:
  u=f"https://api.telegram.org/bot{T}/sendMessage"
  requests.post(u,data={"chat_id":C,"text":m},timeout=10)
 except: pass

def rsi(s,p=14):
 d=s.diff()
 g=d.clip(lower=0).ewm(alpha=1/p).mean()
 l=(-d.clip(upper=0)).ewm(alpha=1/p).mean()
 return 100-100/(1+g/l)

ex=ccxt.bingx({'apiKey':A,'secret':S,'options':{'defaultType':'swap'}})
ex.set_leverage(LEV,SYMBOL)

bal=ex.fetch_balance()
usdt=float(bal['USDT']['free']or 0)

ohlcv=ex.fetch_ohlcv(SYMBOL,TF,limit=100)
df=pd.DataFrame(ohlcv,columns=['t','o','h','l','c','v'])
df['ema20']=df['c'].ewm(span=20).mean()
df['ema50']=df['c'].ewm(span=50).mean()
df['rsi']=rsi(df['c'])
df['sma']=df['c'].rolling(20).mean()
df['std']=df['c'].rolling(20).std()
df['up']=df['sma']+2*df['std']
df['low']=df['sma']-2*df['std']

last=df.iloc[-1]
price=last['c']

long_c=last['rsi']<40 and last['c']<last['low'] and last['ema20']>last['ema50']
short_c=last['rsi']>60 and last['c']>last['up'] and last['ema20']<last['ema50']

pos=ex.fetch_positions([SYMBOL])
has=float(pos[0]['contracts'])>0 if pos else False

msg=f"SCAN {SYMBOL} {price:.1f} RSI:{last['rsi']:.1f} {usdt:.2f}$"
print(msg)

if not has:
 amt=(usdt*RISK*LEV)/price
 amt=ex.amount_to_precision(SYMBOL,amt)
 if long_c:
  ex.create_market_buy_order(SYMBOL,amt)
  tg(f"🚀 LONG x{LEV} {SYMBOL} {price} SL{SL*100}% TP{TP*100}%")
 elif short_c:
  ex.create_market_sell_order(SYMBOL,amt)
  tg(f"🔻 SHORT x{LEV} {SYMBOL} {price} SL{SL*100}% TP{TP*100}%")
 else:
  tg(msg+" No signal")
else:
 print("Pos open")