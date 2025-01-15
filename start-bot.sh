#!/bin/bash

while true; do
    python3 bot.py
    sleep 1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Перезапуск бота..."
done
