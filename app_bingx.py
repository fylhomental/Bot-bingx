import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Bot BingX", layout="wide")
st.title("Bot BingX - Signal + Telegram")

BINGX_API_KEY = st.secrets.get("BINGX_API_KEY", "")
BINGX_API_SECRET = st.secrets.get("BINGX_API_SECRET", "")
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        st.warning("Telegram non configuré")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

symbol = st.sidebar.selectbox("Paire", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
timeframe = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m", "1h"])

if st.sidebar.button("Tester Telegram"):
    send_telegram(f"Test Bot {symbol} OK")
    st.success("Message envoye!")

exchange = ccxt.bingx()
st.metric(symbol, f"{ticker['last']}")
st.metric(symbol, f"{ticker['last']}")

ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','vol'])
df['rsi'] = ta.rsi(df['close'], length=14)
last_rsi = df['rsi'].iloc[-1]

fig = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
st.plotly_chart(fig, use_container_width=True)

if last_rsi < 30:
    st.success(f"ACHAT RSI {last_rsi:.2f}")
    send_telegram(f"ACHAT {symbol} RSI {last_rsi:.2f}")
elif last_rsi > 70:
    st.error(f"VENTE RSI {last_rsi:.2f}")
    send_telegram(f"VENTE {symbol} RSI {last_rsi:.2f}")
else:
    st.info(f"Neutre RSI {last_rsi:.2f}")