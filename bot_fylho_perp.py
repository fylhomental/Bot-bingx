import ccxt, os, time
import pandas as pd

API_KEY = os.getenv("BINGX_API_KEY")
API_SECRET = os.getenv("BINGX_SECRET_KEY")

LEV = 20
AMOUNT_USDT = 36.70
TP_ROE = 30.0
SL_ROE = 15.0

SYMBOLS = ["BTC/USDT:USDT","ETH/USDT:USDT","SOL/USDT:USDT","INJ/USDT:USDT","TAO/USDT:USDT"]

def get_rsi(sym, ex):
    try:
        ohlcv = ex.fetch_ohlcv(sym, '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        delta = df['c'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    except:
        return 50

ex = ccxt.bingx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'options': {'defaultType': 'swap'}
})

print(f"CHASSEUR PERP {LEV}x TP {TP_ROE}% SL {SL_ROE}%")

try:
    positions = ex.fetch_positions()
    open_syms = []

    for p in positions:
        if float(p.get('contracts', 0)) == 0:
            continue
        
        sym = p['symbol']
        # On ne gere que les SYMBOLS voulus
        if sym not in SYMBOLS:
            continue
            
        open_syms.append(sym)
        entry = float(p['entryPrice'])
        side = p['side']
        qty = float(p['contracts'])

        # Fix doublon : si TP/SL deja la, on skip
        try:
            orders = ex.fetch_open_orders(sym)
            if len(orders) >= 2:
                print(f"TP/SL deja pose {sym}, skip")
                continue
        except:
            pass

        tp_price = entry * (1 + TP_ROE/100/LEV) if side == 'long' else entry * (1 - TP_ROE/100/LEV)
        sl_price = entry * (1 - SL_ROE/100/LEV) if side == 'long' else entry * (1 + SL_ROE/100/LEV)

        try:
            if side == 'long':
                ex.create_order(sym, 'limit', 'sell', qty, tp_price, {'reduceOnly': True})
                ex.create_order(sym, 'stop', 'sell', qty, sl_price, {'stopPrice': sl_price, 'reduceOnly': True})
            else:
                ex.create_order(sym, 'limit', 'buy', qty, tp_price, {'reduceOnly': True})
                ex.create_order(sym, 'stop', 'buy', qty, sl_price, {'stopPrice': sl_price, 'reduceOnly': True})
            print(f"TP/SL POSE {sym} TP {tp_price:.4f} SL {sl_price:.4f}")
        except Exception as e:
            print(f"Erreur TP/SL {sym}: {e}")

    print(f"Positions ouvertes: {open_syms}")

    for sym in SYMBOLS:
        if sym in open_syms:
            continue
        try:
            rsi = get_rsi(sym, ex)
            print(f"{sym} RSI {rsi:.1f}")
            if rsi < 35:
                ex.set_leverage(LEV, sym)
                try:
                    ex.set_margin_mode('ISOLATED', sym)
                except:
                    pass
                price = ex.fetch_ticker(sym)['last']
                qty = AMOUNT_USDT * LEV / price
                ex.create_market_buy_order(sym, qty)
                print(f"ACHAT {sym} {qty} a {price}")
                time.sleep(2)
                
                tp_price = price * (1 + TP_ROE/100/LEV)
                sl_price = price * (1 - SL_ROE/100/LEV)
                ex.create_order(sym, 'limit', 'sell', qty, tp_price, {'reduceOnly': True})
                ex.create_order(sym, 'stop', 'sell', qty, sl_price, {'stopPrice': sl_price, 'reduceOnly': True})
                print(f"TP/SL POSE apres achat {sym}")
        except Exception as e:
            print(f"Err {sym}: {e}")

except Exception as e:
    print(f"Erreur globale: {e}")
