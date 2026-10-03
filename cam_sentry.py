#!/usr/bin/env python3
import os
import cv2
import sys
import time
import logging
import argparse
import threading
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("CamSentry")


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str, cooldown: int = 60):
        self.token = token
        self.chat_id = chat_id
        self.cooldown = cooldown
        self.last_sent = 0
        self.enabled = bool(token and chat_id)

        if not self.enabled:
            logger.warning("Telegram credentials missing or incomplete. Alerts disabled.")

    def can_send(self) -> bool:
        return self.enabled and (time.time() - self.last_sent >= self.cooldown)

    def send_photo_async(self, file_path: str, caption: str):
        if not self.can_send():
            return
        self.last_sent = time.time()
        threading.Thread(target=self._upload, args=(file_path, caption), daemon=True).start()

    def _upload(self, file_path: str, caption: str):
        url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
        try:
            with open(file_path, "rb") as photo:
                payload = {"chat_id": self.chat_id, "caption": caption}
                files = {"photo": photo}
                res = requests.post(url, data=payload, files=files, timeout=12)
                if res.status_code == 200:
                    logger.info("Telegram alert dispatched successfully.")
                else:
                    logger.error("Telegram API error (%s): %s", res.status_code, res.text)
        except Exception as err:
            logger.error("Network error sending alert: %s", err)


class MotionDetector:
    def __init__(self, history: int = 500, var_threshold: int = 25):
        self.subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history, varThreshold=var_threshold, detectShadows=True
        )

    def analyze(self, frame, min_area: int):
        clean_frame = frame.copy()
        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        fg_mask = self.subtractor.apply(blurred)

        _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_boxes = []
        for c in contours:
            if cv2.contourArea(c) >= min_area:
                motion_boxes.append(cv2.boundingRect(c))

        return len(motion_boxes) > 0, motion_boxes, clean_frame


def run_sentry(args):
    os.makedirs(args.record_dir, exist_ok=True)
    os.makedirs(args.snap_dir, exist_ok=True)

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    notifier = TelegramNotifier(bot_token, chat_id, cooldown=args.cooldown)
    detector = MotionDetector()

    cap = cv2.VideoCapture(args.device)
    if not cap.isOpened():
        logger.critical("Failed to open video capture device /dev/video%d", args.device)
        sys.exit(1)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps > 60:
        fps = 20.0

    logger.info("Initialized camera %d [%dx%d @ %.1f FPS]", args.device, width, height, fps)

    recording = False
    video_writer = None
    last_motion_time = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.error("Camera frame read error.")
                break

            current_time = time.time()
            motion_found, boxes, snapshot = detector.analyze(frame, args.sensitivity)

            if motion_found:
                last_motion_time = current_time

                for (x, y, w, h) in boxes:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                if notifier.can_send():
                    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    snap_path = os.path.join(args.snap_dir, f"alert_{int(current_time)}.jpg")
                    cv2.imwrite(snap_path, snapshot)
                    caption = f"🚨 CamSentry: Motion Detected!\nTimestamp: {timestamp_str}"
                    notifier.send_photo_async(snap_path, caption)

                if not recording:
                    recording = True
                    fname = datetime.now().strftime("motion_%Y%m%d_%H%M%S.mp4")
                    fpath = os.path.join(args.record_dir, fname)
                    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                    video_writer = cv2.VideoWriter(fpath, fourcc, fps, (width, height))
                    logger.info("Recording started: %s", fpath)

            if recording:
                video_writer.write(frame)
                if current_time - last_motion_time > args.post_record:
                    recording = False
                    video_writer.release()
                    video_writer = None
                    logger.info("Motion stopped. Video saved.")

            if not args.headless:
                status = "REC" if recording else "IDLE"
                color = (0, 0, 255) if recording else (255, 0, 0)
                cv2.putText(frame, f"STATUS: {status}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                cv2.imshow("CamSentry Monitor", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("Stopping...")
                    break

    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
    finally:
        if video_writer is not None:
            video_writer.release()
        cap.release()
        cv2.destroyAllWindows()
        logger.info("Shutdown complete.")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Surveillance tool for Linux.")
    parser.add_argument("-d", "--device", type=int, default=0, help="Camera device index")
    parser.add_argument("-s", "--sensitivity", type=int, default=2500, help="Pixel area threshold")
    parser.add_argument("-p", "--post-record", type=int, default=5, help="Post-motion recording seconds")
    parser.add_argument("-c", "--cooldown", type=int, default=60, help="Alert cooldown in seconds")
    parser.add_argument("--record-dir", default="recordings", help="Video output folder")
    parser.add_argument("--snap-dir", default="snapshots", help="Snapshot output folder")
    parser.add_argument("--headless", action="store_true", help="Run without UI window")
    return parser.parse_args()


if __name__ == "__main__":
    run_sentry(parse_arguments())
