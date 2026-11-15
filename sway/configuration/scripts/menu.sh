#!/bin/sh
# Resolve through the deployed Sway directory symlink; never use global helper
# configuration, which belongs to the existing Hyprland session.
set -eu
config=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
case "${1:-}" in
    launcher)
        exec wofi --conf "$config/wofi/config" --style "$config/styles/wofi.css" \
            --color "$config/wofi/colors" --show drun
        ;;
    power)
        # Only logout is offered until lock-before-suspend is implemented/tested.
        exec wlogout --layout "$config/wlogout/layout" --css "$config/styles/wlogout.css" \
            --buttons-per-row 1
        ;;
    *)
        echo "Usage: menu.sh launcher|power" >&2
        exit 2
        ;;
esac
