import os, ccxt, requests
A=os.getenv('BINGX_API_KEY')
S=os.getenv('BINGX_SECRET_KEY')
T=os.getenv('TELEGRAM_BOT_TOKEN')
C=os.getenv('TELEGRAM_CHAT_ID')
print(f"TOKEN OK? {bool(T)} CHAT={C}")

def tg(m):
 try:
  u=f"https://api.telegram.org/bot{T}/sendMessage"
  r=requests.post(u,data={"chat_id":C,"text":m},timeout=10)
  print(f"TG {r.status_code} {r.text[:300]}")
 except Exception as e:
  print(f"TG ERR {e}")

ex=ccxt.bingx({'apiKey':A,'secret':S,'options':{'defaultType':'swap'}})
ex.load_markets()
b=ex.fetch_balance()
tot=float(b['USDT']['total'] or 0)
fre=float(b['USDT']['free'] or 0)
print(f"Solde: {tot:.2f} libre {fre:.2f}")
pos=ex.fetch_positions()
opens=[p['symbol'].split('/')[0] for p in pos if float(p.get('contracts',0)or 0)!=0]
print(f"POS {opens}")
tg(f"TEST V2.8.1 OK\nSolde {tot:.2f}$\nPOS {opens}")
print("FIN")