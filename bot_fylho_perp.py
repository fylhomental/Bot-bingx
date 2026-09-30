import os,ccxt,requests
A=os.getenv('BINGX_API_KEY')
S=os.getenv('BINGX_SECRET_KEY')
T=os.getenv('TELEGRAM_BOT_TOKEN')
C=os.getenv('TELEGRAM_CHAT_ID')
def tg(m):
 a="https://api.telegram.org/bot"
 b="/sendMessage"
 u=a+T+b
 d={"chat_id":C,"text":m}
 r=requests.post(u,data=d)
 print(r.text[:300])
ex=ccxt.bingx({'apiKey':A,'secret':S,'options':{'defaultType':'swap'}})
b=ex.fetch_balance()
tot=float(b['USDT']['total']or 0)
tg(f"TEST OK {tot}$")
print("FIN")
