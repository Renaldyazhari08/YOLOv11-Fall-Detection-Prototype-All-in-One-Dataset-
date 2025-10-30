import requests
import json
import os

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def get_chat_id_from_token(token):
    """Mengambil chat_id otomatis setelah user /start bot-nya"""
    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        response = requests.get(url)
        data = response.json()

        if "result" in data and len(data["result"]) > 0:
            chat_id = data["result"][-1]["message"]["chat"]["id"]
            return chat_id
    except Exception as e:
        print(f"Error mengambil chat_id: {e}")
    return None

def ensure_telegram_settings():
    """Pastikan token dan chat_id valid di settings.json"""
    settings = load_settings()

    if not settings.get("telegram_token"):
        token = input("Masukkan Telegram Bot Token: ").strip()
        settings["telegram_token"] = token

    if not settings.get("telegram_chat_id"):
        chat_id = get_chat_id_from_token(settings["telegram_token"])
        if chat_id:
            print(f"chat_id ditemukan otomatis: {chat_id}")
            settings["telegram_chat_id"] = str(chat_id)
        else:
            chat_id = input("Masukkan chat_id Telegram: ").strip()
            settings["telegram_chat_id"] = chat_id

    save_settings(settings)
    return settings
