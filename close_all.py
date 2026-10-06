import os, ccxt
k=os.getenv('BINGX_API_KEY')
s=os.getenv('BINGX_SECRET_KEY')
ex=ccxt.bingx({'apiKey':k,'secret':s,'options':{'defaultType':'swap'}})
ex.load_markets()
ps=[p for p in ex.fetch_positions() if float(p.get('contracts',0))>0]
print(f"A fermer {len(ps)}")
for p in ps:
  sym=p['symbol']
  side='sell' if p['side']=='long' else 'buy'
  qty=float(p['contracts'])
  try:
    ex.create_market_order(sym,side,qty)
    print(f"Ferme {sym}")
  except Exception as e:
    print(f"Err {e}")
print("Tout ferme")
