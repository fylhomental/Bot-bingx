import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import requests

st.set_page_config(layout="wide")
st.title("🤖 BOT BINGX - Mode USDT + Telegram")

# --- SECRETS ---
try:
    API_KEY = st.secrets["BINGX_API_KEY"]
    API_SECRET = st.secrets["BINGX_API_SECRET"]
    TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
    MODE_REEL = True
except:
    st.warning("Mode DEMO - Ajoute tes clés dans .streamlit/secrets.toml")
    API_KEY = ""; API_SECRET = ""; TELEGRAM_TOKEN = ""; TELEGRAM_CHAT_ID = ""; MODE_REEL = False

# --- FONCTION TELEGRAM ---
def send_telegram(msg):
    if not TELEGRAM_TOKEN:
        st.info("Telegram non configuré - Ajoute TELEGRAM_TOKEN dans secrets.toml")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)
        st.toast("Message Telegram envoyé ✅")
    except Exception as e:
        st.error(f"Erreur Telegram: {e}")

# --- SIDEBAR ---
st.sidebar.header("⚙️ Réglages en $")
symbol = st.sidebar.selectbox("Paire", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
leverage = st.sidebar.slider("Levier", 1, 50, 10)
marge = st.sidebar.number_input("Marge (USDT)", 10, 10000, 100)
profit_souhaite = st.sidebar.number_input("Je veux gagner (USDT)", 5, 1000, 50)
perte_max = st.sidebar.number_input("Je risque max (USDT)", 5, 1000, 25)
auto_trading = st.sidebar.checkbox("🟢 ACTIVER AUTO-TRADING", value=False)

if st.sidebar.button("📨 Tester Telegram"):
    send_telegram(f"🔔 Test Bot BingX {symbol} - Ton bot Telegram fonctionne !")

position_valeur = marge * leverage
tp_pct = (profit_souhaite / position_valeur) * 100
sl_pct = (perte_max / position_valeur) * 100

@st.cache_data(ttl=30)
def get_data(symbol):
    ex = ccxt.bingx()
    bars = ex.fetch_ohlcv(symbol, "15m", limit=200)
    df = pd.DataFrame(bars, columns=['t','o','h','l','c','v'])
    df['RSI'] = ta.rsi(df['c'], 14)
    df['EMA200'] = ta.ema(df['c'], 200)
    return df

df = get_data(symbol)
last_price = df['c'].iloc[-1]
rsi = df['RSI'].iloc[-1]

# --- GRAPHIQUE ---
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df.index, open=df['o'], high=df['h'], low=df['l'], close=df['c'], name=symbol))
long_tp = last_price * (1 + tp_pct/100)
long_sl = last_price * (1 - sl_pct/100)
fig.add_hline(y=long_tp, line_dash="dash", line_color="green", annotation_text=f"TP +{profit_souhaite}$")
fig.add_hline(y=long_sl, line_dash="dash", line_color="red", annotation_text=f"SL -{perte_max}$")
fig.update_layout(height=550, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

signal = "ACHAT" if rsi < 35 else "VENTE" if rsi > 70 else "ATTENTE"

# --- EXECUTION ---
if auto_trading and signal != "ATTENTE" and MODE_REEL:
    try:
        ex = ccxt.bingx({'apiKey': API_KEY, 'secret': API_SECRET, 'options': {'defaultType': 'swap'}})
        ex.set_leverage(leverage, symbol)
        ex.set_margin_mode('ISOLATED', symbol)
        qty = ex.amount_to_precision(symbol, position_valeur / last_price)

        if signal == "ACHAT":
            ex.create_market_buy_order(symbol, qty)
            ex.create_order(symbol, 'TAKE_PROFIT_MARKET', 'sell', qty, None, {'stopPrice': long_tp})
            ex.create_order(symbol, 'STOP_MARKET', 'sell', qty, None, {'stopPrice': long_sl})
            
            msg = f"✅ *BINGX LONG {symbol}*\nEntrée: {last_price}\nMarge: {marge}$ x{leverage} = {position_valeur}$\n🎯 TP: +{profit_souhaite}$ ({long_tp:.2f}$)\n🛑 SL: -{perte_max}$ ({long_sl:.2f}$)\nRSI: {rsi:.1f}"
            send_telegram(msg)
            st.success("Ordre LONG placé + Telegram envoyé")

        else:
            ex.create_market_sell_order(symbol, qty)
            ex.create_order(symbol, 'TAKE_PROFIT_MARKET', 'buy', qty, None, {'stopPrice': last_price * (1 - tp_pct/100)})
            ex.create_order(symbol, 'STOP_MARKET', 'buy', qty, None, {'stopPrice': last_price * (1 + sl_pct/100)})
            
            msg = f"✅ *BINGX SHORT {symbol}*\nEntrée: {last_price}\nMarge: {marge}$ x{leverage}\n🎯 TP: +{profit_souhaite}$\n🛑 SL: -{perte_max}$\nRSI: {rsi:.1f}"
            send_telegram(msg)
            st.success("Ordre SHORT placé + Telegram envoyé")

    except Exception as e:
        st.error(f"Erreur: {e}")
        send_telegram(f"❌ Erreur Bot BingX: {e}")

elif auto_trading:
    st.info(f"[DEMO] {signal} - J'enverrais un message Telegram avec +{profit_souhaite}$ / -{perte_max}$")
