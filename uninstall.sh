#!/usr/bin/env bash
set -euo pipefail

systemctl --user disable --now ps5-steam-big-picture.service 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/ps5-steam-big-picture.service"
rm -f "$HOME/.local/bin/ps5-steam-big-picture-monitor"
systemctl --user daemon-reload

echo "Removed ps5-steam-big-picture.service and its monitor script"
