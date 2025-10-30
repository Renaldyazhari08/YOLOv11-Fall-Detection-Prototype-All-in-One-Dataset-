# Fall Detection App (YOLOv11) - Desktop (Windows)

This project is a simple desktop application (Tkinter) for detecting human falls using YOLOv11-style models (ultralytics API). It supports:
- Live webcam inference (with snapshot and auto-notify to Telegram)
- Upload image for inference (saves annotated image and sends to Telegram)
- Upload video for inference (saves annotated video and sends to Telegram)
- Settings saved in `settings.json` (model selection, output folder, confidence threshold, Telegram token/chat_id)

## Setup (Windows)
1. Create a virtual environment (recommended):
   ```powershell
   python -m venv venv
   .\\venv\\Scripts\\activate
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Put your `.pt` models inside the `models/` folder. Default model name is `yolov11n_aio_lr0001_50.pt`.

4. Edit settings via GUI (Pengaturan) or open `settings.json` to fill `telegram_token` and `telegram_chat_id`.

5. Run the app:
   ```powershell
   python main.py
   ```

## Build to .exe (PyInstaller)
1. Install PyInstaller:
   ```powershell
   pip install pyinstaller
   ```

2. Build:
   ```powershell
   pyinstaller --onefile --noconsole main.py
   ```

Note: before building, test app in Python environment. Also ensure models and `settings.json` are in the same folder as the executable or adjust paths accordingly.
