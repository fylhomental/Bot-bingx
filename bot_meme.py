import os, ccxt, time

BINGX_API_KEY=os.getenv("BINGX_API_KEY")
BINGX_SECRET=os.getenv("BINGX_SECRET")
SYMBOLS=["DOGE/USDT","SHIB/USDT","PEPE/USDT","BONK/USDT","WIF/USDT"]
AMOUNT_USDT=5
TRAILING_PCT=3.0 # VEND si -3% depuis le plus haut

ex=ccxt.bingx({'apiKey':BINGX_API_KEY,'secret':BINGX_SECRET,'enableRateLimit':True})

def get_rsi_price(s):
    candles=ex.fetch_ohlcv(s,'1h',limit=100)
    closes=[c[4] for c in candles]
    price=closes[-1]
    gains=[];losses=[]
    for i in range(1,len(closes)):
        d=closes[i]-closes[i-1]
        gains.append(d if d>0 else 0)
        losses.append(-d if d<0 else 0)
    avg_g=sum(gains[-14:])/14
    avg_l=sum(losses[-14:])/14
    rsi=100-(100/(1+avg_g/(avg_l+0.0001)))
    return price,rsi

for sym in SYMBOLS:
    try:
        price,rsi=get_rsi_price(sym)
        print(f"{sym} RSI {rsi:.1f}")
        bal=ex.fetch_balance()
        coin=sym.split('/')[0]
        qty=bal.get(coin,{}).get('free',0)

        # SI ON A DEJA LA COIN -> MODE VENTE AU PLUS HAUT
        if qty>0:
            # On récupère le plus haut depuis l'achat (on le simule avec le prix actuel max du jour)
            # Pour du vrai trailing, on stocke highest en fichier
            # Version simple : si prix actuel est en profit, on met un SL trailing
            # On vend si prix < plus haut des dernières 24h - 3%
            ohlc=ex.fetch_ohlcv(sym,'1h',limit=24)
            highest=max([c[2] for c in ohlc]) # plus haut des 24h
            if price < highest * (1-TRAILING_PCT/100) and price > 0:
                ex.create_market_sell_order(sym,qty)
                print(f"VENDU {sym} AU TOP: {price} (top était {highest})")
        else:
            # MODE ACHAT
            if rsi < 35:
                q=AMOUNT_USDT/price
                ex.create_market_buy_order(sym,q)
                print(f"ACHAT {sym} RSI {rsi:.1f}")
    except Exception as e:
        print(f"ERR {sym} {e}")