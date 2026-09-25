import os
import requests

print("--- DEBUT TEST ---")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print(f"Token present: {bool(TELEGRAM_TOKEN)}")
print(f"Chat ID present: {bool(TELEGRAM_CHAT_ID)}")
print(f"Chat ID value: {TELEGRAM_CHAT_ID}")

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
        print(f"Telegram response: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Erreur Telegram: {e}")

# TEST 1 - Simple
send_telegram("✅ TEST 1: Si tu reçois ça, Telegram marche !")

# TEST 2 - Le format BOTH
send_telegram("✅ SPOT: Achat 0.000123 BTC (~20$)\n🚀 FUTURES x3: Long 0.000369 BTC (~20$)")

print("--- FIN TEST ---")