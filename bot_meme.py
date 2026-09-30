import ccxt
import os
import json
import time
import pandas as pd

API_KEY = os.getenv("BINGX_API_KEY")
API_SECRET = os.getenv("BINGX_SECRET_KEY")
AMOUNT_USDT = 5
TP_PCT = 30.0  # +30% en SPOT
SL_PCT = 15.0  # -15% en SPOT
MEM_FILE = "bot_meme_memory.json"

MEMES = ["DOGE/USDT","SHIB/USDT","PEPE/USDT","BONK/USDT","WIF/USDT","FLOKI/USDT","MEME/USDT","BABYDOGE/USDT","BOME/USDT","MEW/USDT","POPCAT/USDT","BRETT/USDT","MOG/USDT","TURBO/USDT","LADYS/USDT","WOJAK/USDT","COQ/USDT","MYRO/USDT","WEN/USDT","PONKE/USDT"]

def get_rsi(symbol, exchange):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    except:
        return 50

exchange = ccxt.bingx({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
   
