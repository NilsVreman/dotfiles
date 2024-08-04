#!/bin/bash -eu

HYPRLAND_CONF_DIR="$HOME/.config/hypr/config"
MONITORS_CONF_DIR="$HYPRLAND_CONF_DIR/monitors"
CURRENT_LINK="$HYPRLAND_CONF_DIR/monitors_current.conf"

FILES=($(ls "$MONITORS_CONF_DIR"/*.conf | sort))

# Find index of current monitor configuration
CURRENT_IDX=-1
for i in "${!FILES[@]}"; do
  if [[ "$(readlink -f "$CURRENT_LINK")" == "$(readlink -f "${FILES[$i]}")" ]]; then
    CURRENT_IDX=$i
    break
  fi
done

# Get next index
NEXT_INDEX=$(((CURRENT_IDX + 1) % ${#FILES[@]}))

echo "Switching from: $(basename "${FILES[$CURRENT_IDX]}")"
# Link that file to the $CURRENT_LINK
ln -sf "${FILES[$NEXT_INDEX]}" "$CURRENT_LINK"

echo "Switched to: $(basename "${FILES[$NEXT_INDEX]}")"

hyprctl reload
