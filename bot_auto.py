import requests, pandas as pd, os
def rsi(s, p=14):
 d=s.diff()
 g=d.where(d>0,0).ewm(alpha=1/p).mean()
 l=(-d.where(d<0,0)).ewm(alpha=1/p).mean()
 return 100-(100/(1+g/l))
T=os.getenv("8838152453:AAEI37Kh-0BEurFlVSnbQEVOalqW21f1ljQ
")
C=os.getenv("1233249921")
def send(m):
 requests.post(f"https://api.telegram.org/bot{T}/sendMessage", json={"chat_id":C,"text":m}, timeout=10)
for sym in ["BTC-USDT","ETH-USDT","SOL-USDT"]:
 try:
  r=requests.get("https://open-api.bingx.com/openApi/spot/v1/market/kline", params={"symbol":sym,"interval":"15m","limit":100}, timeout=15).json().get("data",[])
  if not r: continue
  df=pd.DataFrame(r).iloc[:,:6]
  df.columns=['o','h','l','c','v','t']
  df['c']=pd.to_numeric(df['c'],errors='coerce')
  df['RSI']=rsi(df['c'])
  rs=float(df['RSI'].iloc[-1]); pr=float(df['c'].iloc[-1])
  if rs<35: send(f"ACHAT {sym} {pr:.2f} RSI {rs:.1f}")
  elif rs>65: send(f"VENTE {sym} {pr:.2f} RSI {rs:.1f}")
 except: pass