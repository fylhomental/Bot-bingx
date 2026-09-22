import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Bot BingX - FYL", layout="wide")
st.title("🚀 Bot BingX - Analyse RSI + EMA")

def get_data(symbol="BTC/USDT", timeframe="1h", limit=200):
    exchange = ccxt.bingx()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

st.sidebar.header("Paramètres")
symbol = st.sidebar.selectbox("Paire", ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT"])
timeframe = st.sidebar.selectbox("Timeframe", ["15m","1h","4h","1d"])
rsi_period = st.sidebar.slider("Période RSI", 7, 21, 14)

if st.sidebar.button("Analyser"):
    with st.spinner("Chargement..."):
        df = get_data(symbol, timeframe)
        df['RSI'] = rsi(df['close'], rsi_period)
        df['EMA20'] = df['close'].ewm(span=20).mean()
        df['EMA50'] = df['close'].ewm(span=50).mean()
        last_rsi = df['RSI'].iloc[-1]
        signal = "NEUTRE"
        if last_rsi < 30: signal = "ACHAT 💚"
        elif last_rsi > 70: signal = "VENTE ❤️"
        st.metric(f"RSI {symbol}", f"{last_rsi:.2f}", signal)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], name="Prix"))
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA20'], name="EMA20"))
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA50'], name="EMA50"))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.tail(10))
else:
    st.info("Choisis tes paramètres à gauche et clique sur Analyser")
