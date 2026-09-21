#!/usr/bin/env bash
set -euo pipefail

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
bin_dir="$HOME/.local/bin"
unit_dir="$HOME/.config/systemd/user"

install -Dm755 "$project_dir/ps5-steam-big-picture-monitor" \
    "$bin_dir/ps5-steam-big-picture-monitor"
install -Dm644 "$project_dir/ps5-steam-big-picture.service" \
    "$unit_dir/ps5-steam-big-picture.service"

# Remove links made by older releases, which started the monitor before the
# graphical session and left it without DISPLAY/WAYLAND_DISPLAY.
systemctl --user disable --now ps5-steam-big-picture.service 2>/dev/null || true
systemctl --user daemon-reload
systemctl --user enable --now ps5-steam-big-picture.service

echo "Installed and started ps5-steam-big-picture.service"
echo "Inspect with: systemctl --user status ps5-steam-big-picture.service"
