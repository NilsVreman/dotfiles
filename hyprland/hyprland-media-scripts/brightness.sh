#!/bin/bash

inc_brightness() {
  brightnessctl set 10%+
}

dec_brightness() {
  brightnessctl set 10%-
}

# Execute accordingly
if [[ "$1" == "--inc" ]]; then
  inc_brightness
elif [[ "$1" == "--dec" ]]; then
  dec_brightness
fi
