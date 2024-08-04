#!/bin/bash

is_mute() {
  if [ "$(pamixer --default-source --get-mute)" == "true" ]; then
    return 0 # true
  else
    return 1 # false
  fi
}

toggle_mic() {
  if is_mute; then
    pamixer -u --default-source u # unmute
  else
    pamixer --default-source -m # mute
  fi
}

inc_mic_volume() {
  if is_mute; then
    pamixer -u --default-source u
  fi
  pamixer --default-source -i 5
}

dec_mic_volume() {
  if is_mute; then
    pamixer -u --default-source u
  fi
  pamixer --default-source -d 5
}

# Execute accordingly
if [[ "$1" == "--inc" ]]; then
  inc_mic_volume
elif [[ "$1" == "--dec" ]]; then
  dec_mic_volume
elif [[ "$1" == "--toggle" ]]; then
  toggle_mic
fi
