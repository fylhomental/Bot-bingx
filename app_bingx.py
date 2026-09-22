import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="Bot BingX FYL V7", layout="wide")
st.title("🚀 Bot BingX FYL - V7 Telegram")
st.write("Connecté à BingX + Telegram")

def send_telegram(msg):
    try:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        r = requests.post(url, json={"chat_id": chat_id, "text": msg})
        if r.status_code == 200:
            st.toast("✅ Telegram envoyé!")
        else:
            st.error(f"Telegram erreur: {r.text}")
    except Exception as e:
        st.error(f"Telegram non configuré: {e}")

def get_bingx_data(symbol="BTC-USDT", interval="15m", limit=200):
    url = "https://open-api.bingx.com/openApi/spot/v1/market/kline"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    r = requests.get(url, params=params, timeout=15)
    j = r.json()
    data = j.get("data", [])
    df = pd.DataFrame(data)
    df = df.iloc[:, :6]
    df.columns = ['open','high','low','close','volume','timestamp']
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        if df['timestamp'].iloc[-1].year < 2020:
            raise ValueError
    except:
        freq_map = {"15m":"15min","1h":"1H","4h":"4H","1d":"1D"}
        df['timestamp'] = pd.date_range(end=datetime.now(), periods=len(df), freq=freq_map.get(interval, "15min"))
    for c in ['close','open','high','low']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def rsi(series, p=14):
    d=series.diff(); g=(d.where(d>0,0)).ewm(alpha=1/p).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/p).mean(); return 100-(100/(1+g/l))

st.sidebar.header("BingX V7")
symbol = st.sidebar.selectbox("Paire", ["BTC-USDT","ETH-USDT","SOL-USDT"])
timeframe = st.sidebar.selectbox("TF", ["15m","1h","4h","1d"])

if st.sidebar.button("🔍 Analyser + Alerter"):
    df = get_bingx_data(symbol, timeframe)
    df['RSI']=rsi(df['close']); df['EMA20']=df['close'].ewm(span=20).mean(); df['EMA50']=df['close'].ewm(span=50).mean(); df=df.dropna()
    last_rsi=df['RSI'].iloc[-1]; last_price=df['close'].iloc[-1]

    if last_rsi < 35:
        msg = f"💚 ACHAT {symbol} - ${last_price:.2f} - RSI {last_rsi:.2f} - {timeframe}"
        st.success(msg); send_telegram(msg); st.balloons()
    elif last_rsi > 65:
        msg = f"❤️ VENTE {symbol} - ${last_price:.2f} - RSI {last_rsi:.2f} - {timeframe}"
        st.error(msg); send_telegram(msg)
    else:
        st.warning(f"🟡 NEUTRE {symbol} - RSI {last_rsi:.2f}")

    c1,c2=st.columns(2); c1.metric(symbol, f"${last_price:.2f}"); c2.metric("RSI", f"{last_rsi:.2f}")
    fig=go.Figure(); fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], name="BingX", line=dict(color='#ffcc00'))); fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA20'], name="EMA20")); fig.add_trace(go.Scatter(x=df['timestamp'], y=df['EMA50'], name="EMA50")); fig.update_layout(height=500, template="plotly_dark"); st.plotly_chart(fig, use_container_width=True)

if st.sidebar.button("📱 Test Telegram"):
    send_telegram("✅ Test OK - Bot BingX FYL V7 connecté! rfkay5")