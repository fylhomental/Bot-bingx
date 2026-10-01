import os, ccxt, requests, pandas as pd, time

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")
API_KEY = os.getenv("BINGX_API_KEY")
SECRET = os.getenv("BINGX_SECRET") or os.getenv("BINGX_SECRET_KEY") or os.getenv("BINGX_API_SECRET")

AMOUNT_USDT = 5
MAX_POS = 20
RSI_THRESHOLD = 35

MEMES = [
    "DOGE/USDT","SHIB/USDT","PEPE/USDT","BONK/USDT","WIF/USDT",
    "FLOKI/USDT","ORDI/USDT","BOME/USDT","POPCAT/USDT","MOG/USDT",
    "BRETT/USDT","MEME/USDT","TURBO/USDT","LADYS/USDT","PENGU/USDT"
]
VRAIS_MEMES_COINS = [s.split('/')[0] for s in MEMES]

def tg(msg):
    try:
        if TOKEN and CHAT:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT, "text": msg}, timeout=15)
    except: pass

def get_rsi(closes, period=14):
    delta = closes.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rsi = 100 - (100 / (1 + gain/loss))
    return float(rsi.iloc[-1])

print(f"CHASSEUR SPOT SECURISE {AMOUNT_USDT}$ max {MAX_POS} coins")

try:
    ex = ccxt.bingx({'apiKey': API_KEY,'secret': SECRET,'enableRateLimit': True})
    bal = ex.fetch_balance()
    free_usdt = bal.get('USDT',{}).get('free',0) if isinstance(bal.get('USDT'), dict) else 0

    all_owned = [k for k,v in bal.items() if isinstance(v, dict) and v.get('total',0)>0 and k not in ['USDT','info','free','used','total']]
    owned_meme = [c for c in all_owned if c in VRAIS_MEMES_COINS]

    print(f"Deja en Spot (memes): {owned_meme} ({len(owned_meme)}/{MAX_POS})")

    scans, achats_detail, erreurs = [], [], []
    total_depense_jour = 0

    for sym in MEMES:
        coin = sym.split('/')[0]
        if coin in owned_meme:
            scans.append(f"{sym} deja possede")
            continue
        try:
            ohlcv = ex.fetch_ohlcv(sym,'1d',limit=50)
            closes = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])['c']
            rsi = get_rsi(closes)
            scans.append(f"{sym} RSI {rsi:.1f}")
            print(f"{sym} RSI {rsi:.1f}")

            if rsi < RSI_THRESHOLD and len(owned_meme) < MAX_POS and free_usdt >= AMOUNT_USDT:
                ticker_price = ex.fetch_ticker(sym)['last']
                qty_est = AMOUNT_USDT / ticker_price

                # ACHAT
                order = ex.create_market_buy_order(sym, qty_est)
                time.sleep(1.5) # laisse le temps au fill

                # On recupere le vrai prix d'execution
                try:
                    order = ex.fetch_order(order['id'], sym)
                    prix_exec = order.get('average') or order.get('price') or ticker_price
                    qty_exec = order.get('filled') or order.get('amount') or qty_est
                    cout = order.get('cost') or (prix_exec * qty_exec)
                except:
                    prix_exec = ticker_price
                    qty_exec = qty_est
                    cout = AMOUNT_USDT

                owned_meme.append(coin)
                free_usdt -= cout
                total_depense_jour += cout

                detail = f"✅ {sym}\n ├ Prix: {prix_exec:.6f}$\n ├ Qté: {qty_exec:.2f} {coin}\n └ Coût: {cout:.2f}$ (RSI {rsi:.1f})"
                achats_detail.append(detail)
                print(detail)

        except Exception as e:
            print(f"Err {sym}: {e}")
            erreurs.append(f"{sym}: {e}")

    # MESSAGE TELEGRAM
    msg = f"🚀 Chasseur Meme du jour - {len(owned_meme)}/{MAX_POS}\n"
    msg += f"Spot memes: {owned_meme}\n"
    msg += f"Solde SPOT restant: {free_usdt:.2f} USDT\n\n"

    if achats_detail:
        msg += f"🛒 ACHATS DU JOUR ({len(achats_detail)}) - Total: {total_depense_jour:.2f}$\n"
        msg += "\n".join(achats_detail) + "\n\n"
    else:
        msg += "Aucun achat (RSI > 35)\n\n"

    msg += "📊 Scan:\n" + "\n".join(scans)

    if erreurs and "100202" in str(erreurs):
        msg += "\n\n👉 100202 = plus de USDT en Spot, transfere Futures -> Spot"

    tg(msg)

except Exception as e:
    print(f"Erreur: {e}")
    tg(f"⚠️ Erreur chasseur meme: {e}")
