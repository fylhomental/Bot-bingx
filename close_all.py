import os, ccxt
API_KEY = os.getenv('BINGX_API_KEY')
SECRET = os.getenv('BINGX_SECRET_KEY')
exchange = ccxt.bingx({'apiKey': API_KEY, 'secret': SECRET, 'options': {'defaultType': 'swap'}})
exchange.load_markets()
poses = [p for p in exchange.fetch_positions() if p.get('contracts') and float(p['contracts'])>0]
print(f"A fermer: {len(poses)}")
for p in poses:
    sym = p['symbol']
    side = 'sell' if p['side']=='long' else 'buy'
    qty = float(p['contracts'])
    try:
        exchange.create_market_order(sym, side, qty)
        print(f"Ferme {sym}")
    except Exception as e:
        print(f"Err {sym} {e}")
print("Tout ferme")