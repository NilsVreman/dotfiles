#!/bin/bash

killall waybar
pkill waybar
sleep 0.2

CONFIG_DIR=$(realpath ~/.config/waybar)

waybar -c "$CONFIG_DIR/config.jsonc" -s "$CONFIG_DIR/style.css" &
