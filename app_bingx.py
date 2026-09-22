import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Bot BingX FYL", layout="wide")
st.title("🚀 Bot BingX FYL - V6")
st.write("Connecté en direct à BingX API")

def get_bingx_data(symbol="BTC-USDT", interval="15m", limit=200):
    # API publique BingX - pas besoin de clé pour les prix
    # Docs: https://bingx-api.github.io/docs/#/spot/market/get%20klines
    url = "https://open-api.bingx.com/openApi/spot/v1/market/kline"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    headers = {"User-Agent":"Mozilla/5.0"}
    r = requests.get(url, params=params, headers=headers, timeout=15)
    j = r.json()
    if j.get("code")!= 0:
        st.error(f"BingX Error: {j}")
        return None

    # j["data"] = [[open, high, low, close, volume, time],...]
    data = j["data"]
    # Parfois BingX renvoie du plus récent au plus ancien, on inverse
    # On vérifie l'ordre avec le timestamp
    if data[0][5] > data[-1][5]:
        data = data[::-1]

    df = pd.DataFrame(data, columns=['open','high','low','close','volume','timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    return df

def rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

st.sidebar.header("Paramètres BingX")
symbol = st.sidebar.selectbox("Paire", ["BTC-USDT","ETH-USDT","SOL-USDT","BNB-USDT","PEPE-USDT"])
timeframe = st.sidebar.selectbox("Timeframe", ["15m","1h","4h","1d"])
rsi_period = st.sidebar.slider("Période RSI", 7, 21, 14)

if st.sidebar.button("🔍 Analyser BingX"):
    with st.spinner(f"Chargement BingX {symbol}..."):
        df = get_bingx_data(symbol, timeframe)
        if df is not None and len(df) > 20:
            df['RSI'] = rsi(df['close'], rsi_period)
            df['EMA20'] = df['close'].ewm(span=20).mean()
            df['EMA50'] = df['close'].ewm(span=50).mean()
            df = df.dropna()

            last_rsi = df['RSI'].iloc[-1]
            last_price = df['close'].iloc[-1]

            if last_rsi < 30:
                st.success(f"💚 ACHAT sur BingX - RSI {last_rsi:.2f}")
                st.balloons()
            elif last_rsi > 70:
                st.error(f"❤️ VENTE sur BingX - RSI {last_rsi:.2f}")
            else:
                st.warning(f"🟡 NEUTRE sur BingX - RSI {last_rsi:.2f}")

            c1, c2, c3 = st.columns(3)
            c1.metric(f"Prix {symbol}", f"${last_price:.4f}")
            c2.metric(f"RSI ({rsi_period})", f"{last_rsi:.2f}")
            c3.metric("Source", "BingX.com")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], name="Prix BingX", line=dict(color='#ffcc00', width=2)))
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA20'], name="EMA20"))
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA50'], name="EMA50"))
            fig.update_layout(height=500, template="plotly_dark", title=f"{symbol} - Données BingX")
            st.plotly_chart(fig, use_container_width=True)

            st.caption(f"Dernière bougie: {df['timestamp'].iloc[-1]}")
else:
    st.info("👈 Clique sur Analyser BingX")
    st.write("Cette version utilise directement l'API de BingX, plus de détour par Binance ou OKX.")