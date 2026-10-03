<div align="center">

# 📹 CamSentry

**Lightweight, headless-ready Linux motion surveillance & automated triage engine.**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Kali-blueviolet?style=flat&logo=linux&logoColor=white)](https://www.kali.org/)
[![OpenCV](https://img.shields.io/badge/Engine-OpenCV%20MOG2-5C3EE8?style=flat&logo=opencv&logoColor=white)](https://opencv.org/)
[![Alerts](https://img.shields.io/badge/Alerts-Telegram%20%7C%20Discord-0088cc?style=flat&logo=telegram&logoColor=white)](https://telegram.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat)](LICENSE)

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#credential-setup">Credential Setup</a> •
  <a href="#cli-reference">CLI Reference</a> •
  <a href="#preventing-sleep">System Tuning</a>
</p>

</div>

---

## ⚡ Key Features

* **Advanced Background Subtraction**: Employs OpenCV's `MOG2` algorithm with shadow elimination ($T=200$) to ignore ambient flicker, shifting clouds, and screen reflections.
* **Dual-Channel Asynchronous Dispatch**: Fires immediate alert snapshots over **Telegram Bot API** and/or **Discord Webhooks** inside non-blocking daemon threads to guarantee zero dropped frames in the video pipeline.
* **Sliding Motion Buffer**: Keeps recording for a configurable duration after movement halts, preventing broken/fragmented video clips during brief pauses.
* **Headless First**: Designed to operate cleanly over SSH sessions or low-power background daemons via the `--headless` flag.
* **Environment-Isolated Secrets**: Automatically ingests variables via `.env` without risk of credential leakage in source control.

---

## 🏗️ Architecture

```text
               ┌────────────────┐
               │  Webcam Feed   │ (/dev/video0)
               └───────┬────────┘
                       │ Frame Capture
                       ▼
       ┌───────────────────────────────┐
       │     Gaussian Blur (11x11)     │
       └───────────────┬───────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │   MOG2 Background Isolator    │ ──> Eliminates Shadows (127 gray)
       └───────────────┬───────────────┘
                       │ Binary Mask Dilations
                       ▼
            [ Motion Area > Threshold? ]
                   /          \
                YES            NO ──> Stream Idle
                /
     ┌─────────┴───────────────┐
     │                         │
     ▼                         ▼
┌──────────────┐      ┌─────────────────────────┐
│ Video Writer │      │  Background Thread      │
│  (MP4V File) │      ├─────────────────────────┤
│              │      │ Telegram API  (Async)   │
│ Buffer: +5s  │      │ Discord Hooks (Async)   │
└──────────────┘      └─────────────────────────┘
🚀 Quick Start1. Install DependenciesOn Debian/Kali Linux systems:Bashsudo apt update && sudo apt install -y \
    python3-opencv \
    python3-numpy \
    python3-requests \
    python3-dotenv \
    git
2. Clone & Setup WorkspaceBashgit clone [https://github.com/](https://github.com/)<your-username>/cam-sentry.git
cd cam-sentry
cp .env.example .env
3. LaunchBash# Standard interactive mode (with OpenCV GUI window)
python3 cam_sentry.py

# Headless mode for background execution
python3 cam_sentry.py --headless
🔑 Credential SetupAdd your keys to .env using any text editor:Ini, TOML# --- Telegram Alerts (Optional) ---
TELEGRAM_BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
TELEGRAM_CHAT_ID="987654321"

# --- Discord Alerts (Optional) ---
DISCORD_WEBHOOK_URL="[https://discord.com/api/webhooks/1234567890/abcdef](https://discord.com/api/webhooks/1234567890/abcdef)..."
Obtaining CredentialsMessage @BotFather on Telegram and run /newbot.Copy the generated HTTP API Token into TELEGRAM_BOT_TOKEN.Open your new bot in Telegram and click Start (or send any text message).Run this command in your terminal to fetch your numeric chat_id:Bashcurl -s "[https://api.telegram.org/bot](https://api.telegram.org/bot)<YOUR_BOT_TOKEN>/getUpdates" | grep -o '"chat":{"id":[0-9\-]*'
Paste that number into TELEGRAM_CHAT_ID.Navigate to your Discord Server $\rightarrow$ Select Channel $\rightarrow$ Edit Channel (⚙️).Select Integrations $\rightarrow$ Webhooks $\rightarrow$ New Webhook.Click Copy Webhook URL and assign it to DISCORD_WEBHOOK_URL.🛠️ CLI ReferenceCustomize behavior on the fly using command-line arguments:Bashpython3 cam_sentry.py [OPTIONS]
FlagArgumentDefaultDescription-d, --deviceINT0V4L2 camera index (/dev/videoX).-s, --sensitivityINT2500Minimum bounding contour pixel area to trigger motion.-p, --post-recordINT5Seconds to continue recording after movement ends.-c, --cooldownINT60Minimum delay (seconds) between successive alert posts.-n, --notifyCHOICEallDelivery target: all, telegram, or discord.--record-dirPATHrecordingsDirectory destination for output .mp4 video files.--snap-dirPATHsnapshotsDirectory destination for alert .jpg captures.--headlessNoneFalseDisables X11/Wayland display rendering (no window popup).Example RecipesBash# High-sensitivity surveillance routed strictly to Discord
python3 cam_sentry.py --sensitivity 1200 --notify discord --headless

# Guard with an extended 10-second post-motion buffer and 3-minute alert cooldown
python3 cam_sentry.py --post-record 10 --cooldown 180 --headless
💤 System Tuning (Prevent Idle Sleep)Laptops running Kali or standard Linux distros will suspend background tasks when idle. Use either of these techniques to keep the system awake:Option A: Transient Inhibit Wrapper (Recommended)Launch the script with systemd-inhibit to suspend power-saving locks only while CamSentry is executing:Bashsystemd-inhibit --what=idle:sleep python3 cam_sentry.py --headless
Option B: System-Wide Suspension LockTo permanently lock down sleep timers across the entire host OS:Bashsudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
(To reverse later: replace mask with unmask).🔒 Security Best PracticesNever push .env to public repositories. Ensure .gitignore remains configured to ignore media folders (recordings/, snapshots/) and credential files.Test camera permissions prior to daemonizing:Bashsudo usermod -aG video $USER
📄 LicenseThis project is distributed under the MIT License. See LICENSE for details. EOF
