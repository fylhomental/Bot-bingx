import os,ccxt,requests
import pandas as pd
A=os.getenv('BINGX_API_KEY')
S=os.getenv('BINGX_SECRET_KEY')
T=os.getenv('TELEGRAM_BOT_TOKEN')
C=os.getenv('TELEGRAM_CHAT_ID')
SYMS=['BTC/USDT:USDT','ETH/USDT:USDT','SOL/USDT:USDT']
TF='5m'
LEV=10
RISK=0.15
SL=0.03
TP=0.06
def tg(m):
 try:
  u=f"https://api.telegram.org/bot{T}/sendMessage"
  d={"chat_id":C,"text":m}
  requests.post(u,data=d,timeout=10)
 except:
  pass
def rsi(s,p=14):
 d=s.diff()
 g=d.clip(lower=0).ewm(alpha=1/p).mean()
 l=(-d.clip(upper=0)).ewm(alpha=1/p).mean()
 return 100-100/(1+g/l)
ex=ccxt.bingx({'apiKey':A,'secret':S,'options':{'defaultType':'swap'}})
bal=ex.fetch_balance()
usdt=float(bal['USDT']['free']or 0)
tg(f"SCAN START {usdt:.2f}$")
for SYM in SYMS:
 ohlcv=ex.fetch_ohlcv(SYM,TF,limit=100)
 df=pd.DataFrame(ohlcv,columns=['t','o','h','l','c','v'])
 df['e20']=df['c'].ewm(span=20).mean()
 df['e50']=df['c'].ewm(span=50).mean()
 df['r']=rsi(df['c'])
 df['sma']=df['c'].rolling(20).mean()
 df['std']=df['c'].rolling(20).std()
 df['up']=df['sma']+2*df['std']
 df['low']=df['sma']-2*df['std']
 last=df.iloc[-1]
 price=last['c']
 long_c=last['r']<40 and last['c']<last['low']
 short_c=last['r']>60 and last['c']>last['up']
 pos=ex.fetch_positions([SYM])
 has=float(pos[0]['contracts'])>0 if pos else False
 msg=f"{SYM} {price:.2f} RSI:{last['r']:.1f}"
 print(msg)
 if has:
  continue
 amt=(usdt*RISK*LEV)/price
 amt=ex.amount_to_precision(SYM,amt)
 if long_c:
  ex.create_market_buy_order(SYM,amt)
  sl=price*(1-SL)
  tp=price*(1+TP)
  try:
   ex.create_order(SYM,"limit","sell",amt,tp)
   ex.create_order(SYM,"STOP_MARKET","sell",amt,None,{"stopPrice":sl})
  except:
   pass
  tg(f"LONG x{LEV} {SYM} {price} SL:{sl:.1f} TP:{tp:.1f}")
  break
 if short_c:
  ex.create_market_sell_order(SYM,amt)
  sl=price*(1+SL)
  tp=price*(1-TP)
  try:
   ex.create_order(SYM,"limit","buy",amt,tp)
   ex.create_order(SYM,"STOP_MARKET","buy",amt,None,{"stopPrice":sl})
  except:
   pass
  tg(f"SHORT x{LEV} {SYM} {price} SL:{sl:.1f} TP:{tp:.1f}")
  break
else:
 tg("No signal "+msg)
