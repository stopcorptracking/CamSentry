# CamSentry 🎥

A lightweight, terminal-first surveillance and motion detection tool built for Linux / Kali.

## Features
- **MOG2 Background Subtraction**: Filters out minor lighting shifts and shadow artifacts.
- **Dual Alert Channels**: Dispatch snapshots to **Telegram**, **Discord**, or both simultaneously.
- **Asynchronous Delivery**: Alerts are processed in worker threads to prevent dropped video frames.
- **Configurable CLI**: Flags for sensitivity, buffer time, channel selection, and headless execution.

## Installation

```bash
sudo apt update && sudo apt install python3-opencv python3-numpy python3-requests python3-dotenv git -y
