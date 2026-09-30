import os, ccxt, requests, time
API_KEY=os.getenv('BINGX_API_KEY')
SECRET=os.getenv('BINGX_SECRET_KEY')
TG_TOKEN=os.getenv('TELEGRAM_BOT_TOKEN')
TG_CHAT=os.getenv('TELEGRAM_CHAT_ID')
print(f"DEBUG TG_TOKEN existe: {bool(TG_TOKEN)} len={len(TG_TOKEN) if TG_TOKEN else 0}")
print(f"DEBUG TG_CHAT: {TG_CHAT}")

def tg(msg):
    if not TG_TOKEN or not TG_CHAT:
        print("TG SKIP: token ou chat manquant")
        return
    try:
        url=f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        r=requests.post(url, data={"chat_id":TG_CHAT,"text":msg}, timeout=10)
        print(f"TG RESPONSE: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"TG ERROR: {e}")

print("=== FYLHO V2.8.1 DEBUG ===")
ex=ccxt.bingx({'apiKey':API_KEY,'secret':SECRET,'options':{'defaultType':'swap'},'enableRateLimit':True})
ex.load_markets()
bal=ex.fetch_balance()
total=float(bal['USDT']['total'] or 0)
free=float(bal['USDT']['free'] or 0)
print(f"Solde Futures Total: {total:.2f} USDT (libre {free:.2f})")
positions=ex.fetch_positions()
open_syms=[p['symbol'].split('/')[0].split(':')[0] for p in positions if float(p.get('contracts',0) or 0)!=0]
print(f"Positions ouvertes: {len(open_syms)} {open_syms}")
print("MAX POS atteint" if len(open_syms)>=4 else "FREE SLOT")
tg(f"🔧 TEST DEBUG V2.8.1\nSolde: {total:.2f}$\nPositions: {open_syms}\nSi tu reçois ça, Telegram est OK")
print("FIN RUN")