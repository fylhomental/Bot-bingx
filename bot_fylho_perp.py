import ccxt, os, pandas as pd, time
print("=== FYLHOMENTAL PERP V2.1 FIX 109400 SL:5% TP:10% ===")

API_KEY = os.getenv('BINGX_API_KEY')
SECRET = os.getenv('BINGX_SECRET_KEY')

exchange = ccxt.bingx({
    'apiKey': API_KEY,
    'secret': SECRET,
    'options': {'defaultType': 'swap'},
    'enableRateLimit': True,
})

# Force One-way mode
try:
    exchange.set_position_mode(False)
    print("Position mode One-way OK")
except Exception as e:
    print(f"Position mode info: {e}")

try:
    markets = exchange.load_markets()
except Exception as e:
    print(f"Err load_markets: {e}")
    exit()

# Config
AMOUNT_USDT = 5
LEVERAGE = 5
RSI_OVERSOLD = 35
RSI_OVERBOUGHT = 70

def get_rsi(symbol_ccxt, timeframe='1h', period=14):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol_ccxt, timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        delta = df['c'].diff()
        gain = delta.where(delta>0,0).rolling(period).mean()
        loss = -delta.where(delta<0,0).rolling(period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    except:
        return 50

# Scan top 100 volume USDT perp
tickers = exchange.fetch_tickers()
usdt_perps = [s for s in markets if '/USDT:USDT' in s]
sorted_by_vol = sorted(usdt_perps, key=lambda s: tickers.get(s, {}).get('quoteVolume',0) or 0, reverse=True)[:100]

print(f"Scanning {len(sorted_by_vol)} perps...")

for symbol_ccxt in sorted_by_vol:
    try:
        market = markets[symbol_ccxt]
        symbol_bingx = market['id']  # ex: LTC-USDT -> format BingX
        rsi = get_rsi(symbol_ccxt)
        # print(f"{symbol_ccxt} RSI {rsi:.1f}")
        
        side = None
        if rsi < RSI_OVERSOLD:
            side = 'LONG'
        elif rsi > RSI_OVERBOUGHT:
            side = 'SHORT'
        
        if not side:
            continue

        print(f"SIGNAL {side} {symbol_ccxt} RSI={rsi:.1f}")

        # set leverage
        try:
            exchange.set_leverage(LEVERAGE, symbol_bingx, params={'side': 'BOTH'})
        except: pass

        # calcul quantité
        ticker = exchange.fetch_ticker(symbol_ccxt)
        price = ticker['last']
        amount_coin = (AMOUNT_USDT * LEVERAGE) / price
        amount_coin = exchange.amount_to_precision(symbol_ccxt, amount_coin)

        order_side = 'buy' if side=='LONG' else 'sell'

        # OUVERTURE avec BOTH obligatoire pour BingX
        order = exchange.create_market_order(symbol_ccxt, order_side, float(amount_coin), params={'positionSide':'BOTH'})
        print(f"OPEN {side} {symbol_ccxt} qty {amount_coin} OK")

        time.sleep(1)

        # SL/TP -5% / +10%
        if side == 'LONG':
            sl_price = price * 0.95
            tp_price = price * 1.10
            sl_side = 'sell'
            tp_side = 'sell'
        else:
            sl_price = price * 1.05
            tp_price = price * 0.90
            sl_side = 'buy'
            tp_side = 'buy'

        sl_price = exchange.price_to_precision(symbol_ccxt, sl_price)
        tp_price = exchange.price_to_precision(symbol_ccxt, tp_price)

        # SL
        try:
            exchange.create_order(symbol_ccxt, 'stop_market', sl_side, float(amount_coin), None, params={'stopPrice': sl_price, 'positionSide':'BOTH', 'type':'STOP_MARKET'})
            print(f"  SL placé {sl_price}")
        except Exception as e:
            print(f"  Err SL {e}")

        # TP
        try:
            exchange.create_order(symbol_ccxt, 'limit', tp_side, float(amount_coin), float(tp_price), params={'positionSide':'BOTH'})
            # ou take_profit_market
            # exchange.create_order(symbol_ccxt, 'take_profit_market', tp_side, float(amount_coin), None, params={'stopPrice': tp_price, 'positionSide':'BOTH'})
            print(f"  TP placé {tp_price}")
        except Exception as e:
            print(f"  Err TP {