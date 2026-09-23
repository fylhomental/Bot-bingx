import requests, os

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send(msg):
    if not TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

# --- TON CODE RSI ICI ---
# Exemple, tu gardes ton calcul rsi
try:
    # Remplace par ton vrai calcul
    rsi = 32 # <--- TA VARIABLE RSI
    msg = ""

    if rsi < 30:
        msg = f"🚨 *CRASH* RSI: {rsi}"
    elif rsi < 35:
        msg = f"💚 *ACHAT* RSI: {rsi}"
    elif rsi > 65:
        msg = f"🔴 *VENTE* RSI: {rsi}"
    
    # Si msg est vide = RAS, on n'envoie RIEN = plus de spam
    if msg:
        send(msg)
        print(msg)
    else:
        print(f"RAS RSI {rsi} - pas d'envoi")

except Exception as e:
    print(f"Erreur: {e}")
