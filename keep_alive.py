from flask import Flask
from threading import Thread
import os

app = Flask(__name__)


@app.route('/')
def home():
    return "CoinTracker botu çalışıyor."


def run():
    port = int(os.environ.get("PORT", 5000))
    print(f"Flask sunucusu başlatılıyor... Port: {port}")
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    print("keep_alive() fonksiyonu çağrıldı.")
    t = Thread(target=run)
    t.start()
