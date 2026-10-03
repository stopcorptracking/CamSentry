# CamSentry 🎥

A lightweight, terminal-first surveillance and motion detection tool built for Linux / Kali.

## Features
- Background subtraction with shadow filtering (MOG2).
- Automatic MP4 video recording upon motion trigger.
- Asynchronous Telegram photo alerts with rate-limiting cooldowns.
- CLI flags for sensitivity, post-motion buffer, and headless operation.

## Setup & Usage

```bash
# Install dependencies
sudo apt update && sudo apt install python3-opencv python3-numpy python3-requests python3-dotenv git -y

# Configure credentials
cp .env.example .env
nano .env

# Run standard
python3 cam_sentry.py

# Run headless (ideal for background monitoring)
python3 cam_sentry.py --headless
