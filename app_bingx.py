import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Bot BingX FYL", layout="wide")
st.title("🚀 Bot BingX FYL - V6.2")
st.write("Connecté en direct à BingX API")

def get_bingx_data(symbol="BTC-USDT", interval="15m", limit=200):
    url = "https://open-api.bingx.com/openApi/spot/v1/market/kline"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=15)
    j = r.json()
    if j.get("code")!= 0:
        st.error(f"BingX Error: {j}")
        return None
    data = j.get("data", [])
    df = pd.DataFrame(data)
    if df.shape[1] >= 6:
        df = df.iloc[:, :6]
        df.columns = ['open','high','low','close','volume','timestamp']
    else:
        return None
    # Si timestamp bug, on recrée les dates nous-même
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        # Si ça donne 1970, c'est bugué -> on recrée
        if df['timestamp'].iloc[-1].year < 2020:
            raise ValueError("timestamp 1970")
    except:
        # On recrée des dates récentes manuellement
        freq_map = {"15m":"15min","1h":"1H","4h":"4H","1d":"1D"}
        freq = freq_map.get(interval, "15min")
        df['timestamp'] = pd.date_range(end=datetime.now(), periods=len(df), freq=freq)

    for c in ['close','open','high','low']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    
    if df.iloc[0]['timestamp'] > df.iloc[-1]['timestamp']:
        df = df.iloc[::-1]
    return df

def rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

st.sidebar.header("Paramètres BingX")
symbol = st.sidebar.selectbox("Paire", ["BTC-USDT","ETH-USDT","SOL-USDT","BNB-USDT"])
timeframe = st.sidebar.selectbox("Timeframe", ["15m","1h","4h","1d"])
rsi_period = st.sidebar.slider("Période RSI", 7, 21, 14)

if st.sidebar.button("🔍 Analyser BingX"):
    df = get_bingx_data(symbol, timeframe)
    if df is not None and len(df) > 20:
        df['RSI'] = rsi(df['close'], rsi_period)
        df['EMA20'] = df['close'].ewm(span=20).mean()
        df['EMA50'] = df['close'].ewm(span=50).mean()
        df = df.dropna()

        last_rsi = df['RSI'].iloc[-1]
        last_price = df['close'].iloc[-1]

        if last_rsi < 30:
            st.success(f"💚 ACHAT BingX - RSI {last_rsi:.2f}")
            st.balloons()
        elif last_rsi > 70:
            st.error(f"❤️ VENTE BingX - RSI {last_rsi:.2f}")
        else:
            st.warning(f"🟡 NEUTRE BingX - RSI {last_rsi:.2f}")

        c1, c2 = st.columns(2)
        c1.metric(f"Prix {symbol}", f"${last_price:.2f}")
        c2.metric("RSI", f"{last_rsi:.2f}")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], name="Prix BingX", line=dict(color='#ffcc00', width=2)))
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA20'], name="EMA20", line=dict(color='red')))
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA50'], name="EMA50", line=dict(color='green')))
        fig.update_layout(height=600, template="plotly_dark", title=f"{symbol} - Live BingX")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.tail(10))
else:
    st.info("👈 Clique sur Analyser BingX")