import requests
import csv
import time
import threading
import os
from flask import Flask
from keep_alive import keep_alive  # Sunucuyu canlı tutan dosya

# Telegram bilgileri
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# %1 fark için eşik (0.01)
THRESHOLD = 0.01

# Coin bilgilerini tutan CSV dosyası
COIN_LIST_FILE = "coin_list.csv"


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, data=payload)
        if r.status_code != 200:
            print(f"Telegram mesaj gönderilemedi: {r.text}")
    except Exception as e:
        print(f"Telegram mesaj gönderme hatası: {e}")


def read_coin_list():
    coins = []
    try:
        with open(COIN_LIST_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            for row in reader:
                if len(row) >= 3:
                    coins.append({
                        "name": row[0],
                        "symbol": row[1],
                        "ticker_id": row[2]
                    })
    except FileNotFoundError:
        print("coin_list.csv bulunamadı!")
    return coins


def get_jupiter_prices(symbol):
    url = f"https://lite-api.jup.ag/price/v2?ids={symbol}&showExtraInfo=true"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        price_data = data['data'][symbol]['extraInfo']['quotedPrice']
        buy_price = float(price_data['buyPrice'])
        sell_price = float(price_data['sellPrice'])
        return buy_price, sell_price
    except Exception as e:
        print(f"Jupiter API hatası: {e}")
        return None, None


def get_kraken_prices(pair):
    url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        result = data['result']
        first_key = list(result.keys())[0]
        bid_price = float(result[first_key]['a'][0])
        ask_price = float(result[first_key]['b'][0])
        return bid_price, ask_price
    except Exception as e:
        print(f"Kraken API hatası: {e}")
        return None, None


def check_prices_and_notify():
    coins = read_coin_list()
    for coin in coins:
        jupiter_bid, jupiter_ask = get_jupiter_prices(coin['symbol'])
        kraken_bid, kraken_ask = get_kraken_prices(coin['ticker_id'])

        if None in [jupiter_bid, jupiter_ask, kraken_bid, kraken_ask]:
            continue

        diff1 = (kraken_ask - jupiter_bid) / jupiter_bid
        diff2 = (jupiter_ask - kraken_bid) / kraken_bid

        messages = []

        if diff1 > THRESHOLD:
            messages.append(
                f"*{coin['name']}*:\nJupiter Bid: {jupiter_bid:.6f}\nKraken Ask: {kraken_ask:.6f}\nFark: %{diff1*100:.3f} (Kraken ask > Jupiter bid)"
            )

        if diff2 > THRESHOLD:
            messages.append(
                f"*{coin['name']}*:\nJupiter Ask: {jupiter_ask:.6f}\nKraken Bid: {kraken_bid:.6f}\nFark: %{diff2*100:.3f} (Jupiter ask > Kraken bid)"
            )

        if messages:
            final_message = "\n\n".join(messages)
            print("Bildirim gönderiliyor:\n", final_message)
            send_telegram_message(final_message)


def periodic_check():
    while True:
        check_prices_and_notify()
        print("Kontrol tamamlandı, 10 saniye bekleniyor...\n")
        time.sleep(10)


# KEEP ALIVE'ı başlat ve arka planda botu çalıştır
if __name__ == "__main__":
    keep_alive()
    threading.Thread(target=periodic_check, daemon=True).start()
