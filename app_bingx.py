import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="Bot BingX FYL", layout="wide")
st.title("🚀 Bot BingX FYL - V5")
st.write("Connecté à OKX - mêmes prix que BingX")

def get_data(symbol="BTC/USDT", interval="15m", limit=200):
    # OKX format: BTC-USDT
    instId = symbol.replace("/", "-")
    # Convertit 15m -> 15m, 1h -> 1H, 4h -> 4H, 1d -> 1D
    bar_map = {"15m":"15m", "1h":"1H", "4h":"4H", "1d":"1D"}
    bar = bar_map.get(interval, "15m")
    url = f"https://www.okx.com/api/v5/market/candles?instId={instId}&bar={bar}&limit={limit}"
    headers = {"User-Agent":"Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    data = r.json()
    if data.get("code") != "0":
        st.error(f"OKX Error: {data}")
        return None
    # OKX renvoie [ts, open, high, low, close, vol, volCcy...]
    rows = data["data"][::-1]  # inverser pour avoir du plus ancien au plus récent
    df = pd.DataFrame(rows, columns=['timestamp','open','high','low','close','vol','volCcy','volCcyQuote','confirm'])
    df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
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

st.sidebar.header("Paramètres")
symbol = st.sidebar.selectbox("Paire", ["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT","PEPE/USDT"])
timeframe = st.sidebar.selectbox("Timeframe", ["15m","1h","4h","1d"])
rsi_period = st.sidebar.slider("Période RSI", 7, 21, 14)

if st.sidebar.button("🔍 Analyser"):
    with st.spinner("Chargement OKX..."):
        df = get_data(symbol, timeframe)
        if df is not None and len(df) > 20:
            df['RSI'] = rsi(df['close'], rsi_period)
            df['EMA20'] = df['close'].ewm(span=20).mean()
            df['EMA50'] = df['close'].ewm(span=50).mean()
            df = df.dropna()
            
            last_rsi = df['RSI'].iloc[-1]
            last_price = df['close'].iloc[-1]
            
            if last_rsi < 30:
                st.success(f"💚 SIGNAL ACHAT - RSI {last_rsi:.2f} - Survente !")
                st.balloons()
            elif last_rsi > 70:
                st.error(f"❤️ SIGNAL VENTE - RSI {last_rsi:.2f} - Surachat !")
            else:
                st.warning(f"🟡 NEUTRE - RSI {last_rsi:.2f}")

            c1, c2 = st.columns(2)
            c1.metric(f"Prix {symbol}", f"${last_price:.4f}")
            c2.metric(f"RSI ({rsi_period})", f"{last_rsi:.2f}")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], name="Prix", line=dict(color='#00ff88')))
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA20'], name="EMA20"))
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA50'], name="EMA50"))
            fig.update_layout(height=500, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df.tail(10))
else:
    st.info("👈 Clique sur Analyser à gauche pour voir le signal")