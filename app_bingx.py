import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="Bot BingX FYL", layout="wide")
st.title("🚀 Bot BingX FYL - V6.1")
st.write("Connecté en direct à BingX API - Fix colonnes")

def get_bingx_data(symbol="BTC-USDT", interval="15m", limit=200):
    url = "https://open-api.bingx.com/openApi/spot/v1/market/kline"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=15)
    j = r.json()
    if j.get("code")!= 0:
        st.error(f"BingX Error: {j}")
        return None

    data = j.get("data", [])
    if not data:
        st.error("BingX vide")
        return None

    # Fix: BingX peut renvoyer 6 ou plus colonnes, on prend dynamiquement
    # Format officiel: [open, high, low, close, volume, timestamp] ou [close, high...]
    # On sécurise
    df = pd.DataFrame(data)
    # Les 2 derniers sont toujours volume et timestamp chez BingX
    # Donc on prend les 6 colonnes dans l'ordre
    if df.shape[1] >= 6:
        df = df.iloc[:, :6]
        df.columns = ['open','high','low','close','volume','timestamp']
    else:
        st.error(f"Format inattendu: {data[0]}")
        return None

    if df.iloc[0]['timestamp'] > df.iloc[-1]['timestamp']:
        df = df.iloc[::-1]

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    for c in ['close','open','high','low']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
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
        c1.metric(f"Prix {symbol} BingX", f"${last_price:.4f}")
        c2.metric("RSI", f"{last_rsi:.2f}")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], name="Prix BingX", line=dict(color='#ffcc00')))
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA20'], name="EMA20"))
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA50'], name="EMA50"))
        fig.update_layout(height=500, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("👈 Clique sur Analyser BingX")