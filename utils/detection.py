import os
import time
import cv2
from ultralytics import YOLO
from datetime import datetime
from pathlib import Path
from utils.telegram_alert import send_telegram_notification

def _annotate_frame_with_results(frame, results, model, conf_thresh):
    """
    Draw bounding boxes and labels on frame using results (ultralytics Results)
    Returns annotated frame and a boolean whether 'fall' was detected in frame.
    """
    annotated = frame.copy()
    detected_fall = False
    for r in results:
        # use r.boxes if present (Results object)
        boxes = getattr(r, "boxes", None)
        names = getattr(r, "names", model.names if hasattr(model, "names") else {})
        if boxes is None:
            continue
        for box in boxes:
            try:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
            except Exception:
                # sometimes box.xyxy is list of tensors
                coords = box.xyxy.tolist()[0]
                x1, y1, x2, y2 = map(int, coords)
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            label = names.get(cls, str(cls))
            color = (0,255,0)
            if label == "fall" and conf >= conf_thresh:
                color = (0,0,255)
                detected_fall = True
            cv2.rectangle(annotated, (x1,y1), (x2,y2), color, 2)
            cv2.putText(annotated, f"{label} {conf:.2f}", (x1, max(15,y1-5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return annotated, detected_fall

def infer_image(image_path, settings):
    """
    Infer a single image, save annotated image to output folder, and return output path.
    """
    model_path = os.path.join("models", settings.get("model_name"))
    model = YOLO(model_path)
    conf_thresh = float(settings.get("confidence_threshold", 0.5))
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Gagal membaca gambar. Periksa file.")
    results = model(img)
    annotated, detected_fall = _annotate_frame_with_results(img, results, model, conf_thresh)
    # build output filename
    out_dir = settings.get("output_dir", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    base = Path(image_path).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(out_dir, f"{base}_annotated_{timestamp}.jpg")
    cv2.imwrite(out_path, annotated)
    # if fall detected, log and send snapshot handled by caller
    return out_path

def infer_video(video_path, settings):
    """
    Infer a video file frame-by-frame, save annotated video to output folder, and return output path.
    """
    model_path = os.path.join("models", settings.get("model_name"))
    model = YOLO(model_path)
    conf_thresh = float(settings.get("confidence_threshold", 0.5))

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Gagal membuka file video.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out_dir = settings.get("output_dir", "outputs")
    os.makedirs(out_dir, exist_ok=True)
    base = Path(video_path).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(out_dir, f"{base}_annotated_{timestamp}.mp4")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    fall_frames = 0
    fall_start_time = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame)
        annotated, detected_fall = _annotate_frame_with_results(frame, results, model, conf_thresh)
        writer.write(annotated)

        # simple fall logging per-frame (no telegram here; caller will send file)
        if detected_fall:
            if fall_start_time is None:
                fall_start_time = time.time()
            # we don't send telegram per-frame in video infer; caller will send after done
        else:
            fall_start_time = None

    cap.release()
    writer.release()
    return out_path

def run_webcam_inference(settings):
    """
    Run live webcam inference. Save snapshots when requested and send telegram message
    when 'fall' detected for >=5 consecutive seconds.
    """
    model_path = os.path.join("models", settings.get("model_name"))
    model = YOLO(model_path)
    conf_thresh = float(settings.get("confidence_threshold", 0.5))
    out_dir = settings.get("output_dir", "outputs")
    wait_time = float(settings.get("wait_time", 5))
    notify_cooldown = float(settings.get("notify_cooldown", 10))   # seconds between notifications

    os.makedirs(out_dir, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Tidak dapat membuka webcam.")

    win_name = "Live Webcam Inference - Tekan 'q' untuk keluar | Tekan 's' untuk simpan snapshot"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)

    fall_start = None
    last_notify = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        annotated, detected_fall = _annotate_frame_with_results(frame, results, model, conf_thresh)

        # Check consecutive fall detection time
        if detected_fall:
            if fall_start is None:
                fall_start = time.time()
            else:
                elapsed = time.time() - fall_start
                if elapsed >= wait_time and (time.time() - last_notify) > notify_cooldown:
                    # send telegram alert with snapshot
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    snap_path = os.path.join(out_dir, f"fall_snapshot_{timestamp}.jpg")
                    cv2.imwrite(snap_path, annotated)
                    # send text + image
                    if settings.get("telegram_token") and settings.get("telegram_chat_id"):
                        send_telegram_notification(settings["telegram_token"],
                                                   settings["telegram_chat_id"],
                                                   f"⚠️ Fall detected (live) at {timestamp}",
                                                   image_path=snap_path)
                    last_notify = time.time()
        else:
            fall_start = None

        cv2.imshow(win_name, annotated)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break
        if key == ord("s"):
            # save snapshot manually and send to telegram if configured
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snap_path = os.path.join(out_dir, f"snapshot_{timestamp}.jpg")
            cv2.imwrite(snap_path, annotated)
            if settings.get("telegram_token") and settings.get("telegram_chat_id"):
                send_telegram_notification(settings["telegram_token"],
                                           settings["telegram_chat_id"],
                                           f"Snapshot captured at {timestamp}",
                                           image_path=snap_path)

    cap.release()
    cv2.destroyAllWindows()