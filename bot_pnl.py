import os, ccxt, requests
TOKEN=os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID=os.getenv("TELEGRAM_CHAT_ID")
BINGX_API_KEY=os.getenv("BINGX_API_KEY")
BINGX_SECRET=os.getenv("BINGX_SECRET")

def send_tg(msg):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})

try:
    ex_spot=ccxt.bingx({'apiKey':BINGX_API_KEY,'secret':BINGX_SECRET,'options':{'defaultType':'spot'}})
    ex_fut=ccxt.bingx({'apiKey':BINGX_API_KEY,'secret':BINGX_SECRET,'options':{'defaultType':'swap'}})
    
    bal_spot=ex_spot.fetch_balance()
    usdt_spot=bal_spot.get('USDT',{}).get('free',0)

    bal_fut=ex_fut.fetch_balance()
    usdt_fut=bal_fut.get('USDT',{}).get('free',0) if 'USDT' in bal_fut else 0

    positions=ex_fut.fetch_positions()
    msg="📊 *BRIEFING 8H - TOP 5 BOT*\n\n"
    msg+=f"💰 Spot USDT libre: {usdt_spot:.2f}$\n"
    msg+=f"💰 Futures USDT libre: {usdt_fut:.2f}$\n\n"
    
    pnl_total=0
    open_pos=0
    for p in positions:
        if float(p.get('contracts',0))>0:
            open_pos+=1
            pnl=float(p.get('unrealizedPnl',0))
            pnl_total+=pnl
            sym=p['symbol']
            msg+=f"📈 {sym} : {pnl:.2f}$ PnL\n"
    
    if open_pos==0:
        msg+="😴 Aucune position ouverte - En attente de DIP\n"
    else:
        msg+=f"\n🔥 PnL Total ouvert: {pnl_total:.2f}$ sur {open_pos} pos\n"
    
    msg+="\n🤖 Bot actif - Prochain check dans 1h"
    send_tg(msg)
except Exception as e:
    send_tg(f"❌ Erreur P&L: {e}")
