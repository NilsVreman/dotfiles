#!/bin/bash

is_mute() {
  if [ "$(pamixer --get-mute)" == "true" ]; then
    return 0 # true
  else
    return 1 # false
  fi
}

toggle_sound() {
  if is_mute; then
    pamixer -u # Unmute
  else
    pamixer -m # Mute
  fi
}

inc_volume() {
  if is_mute; then
    pamixer -u
  fi
  pamixer -i 5
}

dec_volume() {
  if is_mute; then
    pamixer -u
  fi
  pamixer -d 5
}

# Execute accordingly
if [[ "$1" == "--inc" ]]; then
  inc_volume
elif [[ "$1" == "--dec" ]]; then
  dec_volume
elif [[ "$1" == "--toggle" ]]; then
  toggle_sound
fi
