import os, ccxt, requests
A=os. getenv ('BINGX_API_KEY')
S=os.getenv('BINGX_SECRET_KEY')
C=os. getenv ('TELEGRAM_CHAT_ID')
def tg(m) :
b="/ sendMessage"
u=a+T+b
d={"chat_id" :C, "text":m}
r=requests. post (u, data=d)
print (r.text: 200])
b=ex.fetch_balance()
tg (f"TEST OK {tot}$")
print("FIN")
