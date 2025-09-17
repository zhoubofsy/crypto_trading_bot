#!/bin/bash

# 启动bot
python3 okx_bot.py &

# 启动GUI
python3 ./cmd/main_gui.py &