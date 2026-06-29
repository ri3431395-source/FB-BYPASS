#!/bin/bash
apt-get update
apt-get install -y ffmpeg exiftool
pip install -r requirements.txt
python telegram_bypass_bot.py
chmod +x start.sh
