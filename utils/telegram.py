import requests
from django.conf import settings


def send_telegram_message(chat_id, text):
    if not chat_id:
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print("Telegram error:", e)