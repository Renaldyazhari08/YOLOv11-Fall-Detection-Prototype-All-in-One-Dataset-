import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "model_name": "yolov11n_aio_lr0001_50.pt",
    "output_dir": "outputs",
    "confidence_threshold": 0.5,
    "wait_time": 5,
    "notify_cooldown" : 10,
    "telegram_token": "8366790973:AAEwwWUCWYsvD5g6uHVp-V13P7V6Ovbr3A0",
    "telegram_chat_id": "1447214258"
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            # ensure keys
            for k,v in DEFAULT_SETTINGS.items():
                if k not in data:
                    data[k] = v
            return data
        except Exception:
            return DEFAULT_SETTINGS.copy()
    else:
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def ensure_folders(settings):
    # create outputs and models folder if not exist
    os.makedirs(settings.get("output_dir", "outputs"), exist_ok=True)
    os.makedirs("models", exist_ok=True)

def get_model_list(models_folder="models"):
    if not os.path.exists(models_folder):
        return []
    files = [f for f in os.listdir(models_folder) if f.lower().endswith(".pt")]
    return files
