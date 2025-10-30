import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from utils.settings_manager import load_settings, save_settings, ensure_folders, get_model_list
from utils.detection import infer_image, infer_video, run_webcam_inference
from utils.telegram_alert import send_telegram_notification
from utils.telegram_utils import ensure_telegram_settings

settings = load_settings()

# Ensure folders exist
ensure_folders(settings)

APP_TITLE = "YOLOv11 Fall Detection Prototype"
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

def refresh_model_dropdown(combo):
    combo['values'] = get_model_list(os.path.join(ROOT_DIR, "models"))
    # set current if exists
    try:
        combo.set(os.path.basename(settings.get("model_name", "")))
    except Exception:
        pass

def open_settings_window():
    win = tk.Toplevel(root)
    win.title("Pengaturan")
    win.geometry("400x500")

    tk.Label(win, text="Folder Output:").pack(anchor="w", padx=10, pady=(10,0))
    out_frame = tk.Frame(win)
    out_frame.pack(fill="x", padx=10, pady=5)
    out_entry = tk.Entry(out_frame)
    out_entry.insert(0, settings.get("output_dir", "outputs"))
    out_entry.pack(side="left", fill="x", expand=True)
    def browse_out():
        p = filedialog.askdirectory(title="Pilih folder output")
        if p:
            out_entry.delete(0, tk.END); out_entry.insert(0, p)
    tk.Button(out_frame, text="Browse", command=browse_out).pack(side="right")

    tk.Label(win, text="Pilih Model (models/):").pack(anchor="w", padx=10, pady=(10,0))
    model_combo = ttk.Combobox(win, state="readonly")
    model_combo.pack(fill="x", padx=10, pady=5)
    refresh_model_dropdown(model_combo)

    tk.Label(win, text="Threshold Confidence (0.0 - 1.0):").pack(anchor="w", padx=10, pady=(10,0))
    thr_entry = tk.Entry(win)
    thr_entry.insert(0, str(settings.get("confidence_threshold", 0.5)))
    thr_entry.pack(fill="x", padx=10, pady=5)

    tk.Label(win, text="Waktu Detektsi (Detik):").pack(anchor="w", padx=10, pady=(10,0))
    wait_entry = tk.Entry(win)
    wait_entry.insert(0, str(settings.get("wait_time", 5)))
    wait_entry.pack(fill="x", padx=10, pady=5)

    tk.Label(win, text="CoolDown Notifikasi (Detik):").pack(anchor="w", padx=10, pady=(10,0))
    cool_entry = tk.Entry(win)
    cool_entry.insert(0, str(settings.get("notify_cooldown", 10)))
    cool_entry.pack(fill="x", padx=10, pady=5)

    tk.Label(win, text="Telegram Bot Token:").pack(anchor="w", padx=10, pady=(10,0))
    token_entry = tk.Entry(win)
    token_entry.insert(0, settings.get("telegram_token", ""))
    token_entry.pack(fill="x", padx=10, pady=5)

    tk.Label(win, text="Telegram Chat ID:").pack(anchor="w", padx=10, pady=(10,0))
    chat_entry = tk.Entry(win)
    chat_entry.insert(0, settings.get("telegram_chat_id", ""))
    chat_entry.pack(fill="x", padx=10, pady=5)

    def save_and_close():
        out = out_entry.get().strip() or "outputs"
        model_name = model_combo.get().strip()
        thr = thr_entry.get().strip()
        wait = wait_entry.get().strip()
        cool = cool_entry.get().strip()
        try:
            thr = float(thr)
            wait = float(wait)
            if not (0.0 <= thr <= 1.0):
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Masukkan threshold antara 0.0 hingga 1.0")
            return
        settings["output_dir"] = out
        settings["model_name"] = model_name
        settings["telegram_token"] = token_entry.get().strip()
        settings["telegram_chat_id"] = chat_entry.get().strip()
        settings["confidence_threshold"] = thr
        settings["wait_time"] = wait
        settings["notify_cooldown"] = cool
        save_settings(settings)
        ensure_folders(settings)
        refresh_model_dropdown(model_combo)
        messagebox.showinfo("Simpan", "Pengaturan tersimpan.")
        win.destroy()

    tk.Button(win, text="Simpan", command=save_and_close).pack(pady=10)

def choose_image_and_infer():
    file_path = filedialog.askopenfilename(title="Pilih gambar untuk inferensi",
                                           filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
    if not file_path:
        return

    def worker():
        try:
            out_path = infer_image(file_path, settings)
            # send to telegram if token present
            if settings.get("telegram_token") and settings.get("telegram_chat_id"):
                send_telegram_notification(settings["telegram_token"],
                                           settings["telegram_chat_id"],
                                           f"Deteksi gambar selesai: {os.path.basename(out_path)}",
                                           image_path=out_path)
            messagebox.showinfo("Selesai", f"File hasil disimpan di:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal inferensi gambar:\n{e}")

    threading.Thread(target=worker, daemon=True).start()

def choose_video_and_infer():
    file_path = filedialog.askopenfilename(title="Pilih video untuk inferensi",
                                           filetypes=[("Video files", "*.mp4 *.avi *.mov")])
    if not file_path:
        return

    def worker():
        try:
            out_path = infer_video(file_path, settings)
            # send to telegram if token present
            if settings.get("telegram_token") and settings.get("telegram_chat_id"):
                send_telegram_notification(settings["telegram_token"],
                                           settings["telegram_chat_id"],
                                           f"Deteksi video selesai: {os.path.basename(out_path)}",
                                           video_path=out_path)
            messagebox.showinfo("Selesai", f"File hasil disimpan di:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal inferensi video:\n{e}")

    threading.Thread(target=worker, daemon=True).start()

def start_live_webcam():
    def worker():
        try:
            run_webcam_inference(settings)
        except Exception as e:
            messagebox.showerror("Error", f"Error saat webcam:\n{e}")

    threading.Thread(target=worker, daemon=True).start()

# --- GUI ---
root = tk.Tk()
root.title(APP_TITLE)
root.geometry("600x320")

tk.Label(root, text=APP_TITLE, font=("Arial", 14, "bold")).pack(pady=10)

tk.Button(root, bg="lightgray", text="Live Webcam Inference", width=60, command=start_live_webcam).pack(pady=6)
tk.Button(root, bg="lightgray", text="Upload Foto Inference", width=60, command=choose_image_and_infer).pack(pady=6)
tk.Button(root, bg="lightgray", text="Upload Video Inference", width=60, command=choose_video_and_infer).pack(pady=6)
tk.Button(root, bg="lightgray", text="Settings", width=60, command=open_settings_window).pack(pady=6)

tk.Label(root, text="Information:", font=("Arial", 10, "bold")).pack(pady=(12,0))
info_text = tk.Label(root, text=f"Default Model: {settings.get('model_name') or 'yolov11n_aio_lr0001_50.pt'}\nOutput: {settings.get('output_dir')}")
info_text.pack()

root.mainloop()
