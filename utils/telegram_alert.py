import os
import requests

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/{method}"

def send_telegram_notification(bot_token, chat_id, message, image_path=None, video_path=None):
    """
    Send a text message, and optionally an image or video file, to Telegram
    """
    try:
        # send text
        url = TELEGRAM_API_BASE.format(token=bot_token, method="sendMessage")
        data = {"chat_id": chat_id, "text": message}
        r = requests.post(url, data=data, timeout=10)
        if r.status_code != 200:
            print("Telegram sendMessage failed:", r.text)

        # send image if provided
        if image_path and os.path.exists(image_path):
            url = TELEGRAM_API_BASE.format(token=bot_token, method="sendPhoto")
            with open(image_path, "rb") as ph:
                files = {"photo": ph}
                data = {"chat_id": chat_id, "caption": os.path.basename(image_path)}
                r = requests.post(url, data=data, files=files, timeout=30)
                if r.status_code != 200:
                    print("Telegram sendPhoto failed:", r.text)

        # send video if provided
        if video_path and os.path.exists(video_path):
            url = TELEGRAM_API_BASE.format(token=bot_token, method="sendVideo")
            with open(video_path, "rb") as vid:
                files = {"video": vid}
                data = {"chat_id": chat_id, "caption": os.path.basename(video_path)}
                r = requests.post(url, data=data, files=files, timeout=60)
                if r.status_code != 200:
                    print("Telegram sendVideo failed:", r.text)

    except Exception as e:
        print("Error sending telegram:", e)
