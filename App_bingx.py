import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("🤖 BOT BINGX - Mode USDT Fixe")

# --- SECRETS ---
try:
    API_KEY = st.secrets["BINGX_API_KEY"]
    API_SECRET = st.secrets["BINGX_API_SECRET"]
    MODE_REEL = True
except:
    st.warning("Mode DEMO - Mets tes clés dans .streamlit/secrets.toml")
    API_KEY = ""; API_SECRET = ""; MODE_REEL = False

# --- SIDEBAR EN USDT ---
st.sidebar.header("⚙️ Réglages en $")
symbol = st.sidebar.selectbox("Paire", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
leverage = st.sidebar.slider("Levier BingX", 1, 50, 10)
marge = st.sidebar.number_input("Marge engagée par trade (USDT)", 10, 10000, 100)
profit_souhaite = st.sidebar.number_input("Je veux gagner (USDT)", 5, 1000, 50)
perte_max = st.sidebar.number_input("Je veux risquer max (USDT)", 5, 1000, 25)
auto_trading = st.sidebar.checkbox("🟢 ACTIVER AUTO-TRADING", value=False)

# Calcul auto des %
position_valeur = marge * leverage
tp_pct = (profit_souhaite / position_valeur) * 100
sl_pct = (perte_max / position_valeur) * 100

st.sidebar.divider()
st.sidebar.metric("TP en % de prix", f"{tp_pct:.2f}%")
st.sidebar.metric("SL en % de prix", f"{sl_pct:.2f}%")
st.sidebar.caption(f"Position totale: {position_valeur}$ ( {marge}$ x {leverage} )")

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
fig.add_hline(y=long_tp, line_dash="dash", line_color="green", annotation_text=f"TP: +{profit_souhaite}$ ({tp_pct:.2f}%)")
fig.add_hline(y=long_sl, line_dash="dash", line_color="red", annotation_text=f"SL: -{perte_max}$ ({sl_pct:.2f}%)")
fig.add_hline(y=last_price, line_color="blue", annotation_text=f"ENTREE {last_price}")
fig.update_layout(height=550, xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

col1, col2, col3 = st.columns(3)
col1.metric("Prix Actuel", f"{last_price:.2f}$")
col2.metric("Si TP touché", f"+{profit_souhaite}$", f"Sur {marge}$ de marge = +{(profit_souhaite/marge)*100:.1f}%")
col3.metric("Si SL touché", f"-{perte_max}$", f"Sur {marge}$ de marge = -{(perte_max/marge)*100:.1f}%")

signal = "ACHAT" if rsi < 35 else "VENTE" if rsi > 70 else "ATTENTE"

if signal == "ACHAT":
    st.success(f"SIGNAL LONG - RSI {rsi:.1f}")
elif signal == "VENTE":
    st.error(f"SIGNAL SHORT - RSI {rsi:.1f}")
else:
    st.info(f"ATTENTE - RSI {rsi:.1f}")

# --- EXECUTION ---
if auto_trading and signal != "ATTENTE" and MODE_REEL:
    try:
        ex = ccxt.bingx({'apiKey': API_KEY, 'secret': API_SECRET, 'options': {'defaultType': 'swap'}})
        ex.set_leverage(leverage, symbol)
        ex.set_margin_mode('ISOLATED', symbol)
        
        # Qty = Valeur position / prix
        qty = position_valeur / last_price
        qty = ex.amount_to_precision(symbol, qty)

        if signal == "ACHAT":
            ex.create_market_buy_order(symbol, qty)
            ex.create_order(symbol, 'TAKE_PROFIT_MARKET', 'sell', qty, None, {'stopPrice': long_tp})
            ex.create_order(symbol, 'STOP_MARKET', 'sell', qty, None, {'stopPrice': long_sl})
            st.success(f"✅ LONG {qty} {symbol} | Marge {marge}$ x{leverage} | TP +{profit_souhaite}$ | SL -{perte_max}$")
        else:
            ex.create_market_sell_order(symbol, qty)
            ex.create_order(symbol, 'TAKE_PROFIT_MARKET', 'buy', qty, None, {'stopPrice': last_price * (1 - tp_pct/100)})
            ex.create_order(symbol, 'STOP_MARKET', 'buy', qty, None, {'stopPrice': last_price * (1 + sl_pct/100)})
            st.success(f"✅ SHORT {qty} {symbol} | Marge {marge}$ x{leverage} | TP +{profit_souhaite}$ | SL -{perte_max}$")
    except Exception as e:
        st.error(f"Erreur: {e}")
elif auto_trading:
    st.info(f"[DEMO] J'ouvrirais {signal} de {marge}$ x{leverage} = {position_valeur}$ | TP +{profit_souhaite}$ | SL -{perte_max}$")
