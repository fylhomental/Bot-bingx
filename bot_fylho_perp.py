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
def tg(m):
 try:
  a="https://api.telegram.org/bot"
  b="/sendMessage"
  u=a+T+b
  d={"chat_id":C,"text":m}
  requests.post(u,data=d,timeout=10)
 except: pass
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
 ex.set_leverage(LEV,SYM)
