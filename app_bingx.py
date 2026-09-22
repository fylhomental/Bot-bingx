import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="Bot BingX FYL", layout="wide")
st.title("🚀 Bot BingX FYL - V3")
st.write("Version stable sans ccxt")

def get_data(symbol="BTCUSDT", interval="15m", limit=200):
    # On enlève le / de BTC/USDT -> BTCUSDT
    symbol = symbol.replace("/", "")
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    r = requests.get(url, timeout=10)
    data = r.json()
    df = pd.DataFrame(data, columns=['timestamp','open','high','low','close','volume','close_time','qav','trades','taker_base','taker_quote','ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
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
rsi_period = st.sidebar.slider("RSI", 7, 21, 14)

if st.sidebar.button("🔍 Analyser"):
    with st.spinner("Chargement Binance..."):
        try:
            df = get_data(symbol, timeframe)
            df['RSI'] = rsi(df['close'], rsi_period)
            df['EMA20'] = df['close'].ewm(span=20).mean()
            df['EMA50'] = df['close'].ewm(span=50).mean()
            
            last_rsi = df['RSI'].iloc[-1]
            last_price = df['close'].iloc[-1]
            
            if last_rsi < 30:
                st.success(f"💚 ACHAT - RSI {last_rsi:.2f} - Survente")
            elif last_rsi > 70:
                st.error(f"❤️ VENTE - RSI {last_rsi:.2f} - Surachat")
            else:
                st.warning(f"🟡 NEUTRE - RSI {last_rsi:.2f}")

            c1, c2 = st.columns(2)
            c1.metric(f"Prix {symbol}", f"${last_price}")
            c2.metric("RSI", f"{last_rsi:.2f}")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], name="Prix"))
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA20'], name="EMA20"))
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA50'], name="EMA50"))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df.tail(10))
        except Exception as e:
            st.error(f"Erreur API: {e}")
else:
    st.info("👈 Clique sur Analyser à gauche")