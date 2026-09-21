# PS5 controller → Steam Big Picture

This project starts Steam Big Picture when you press the PS button on a Sony
PS5 DualSense controller that is already connected to the current graphical
Linux session.

It uses a user-level `systemd` service and Linux input events, so it does not
install a system-wide udev rule or run Steam as root.

This monitor is intentional: Steam's native Linux Gamepad UI can destroy its
Big Picture window when a game closes. The service detects the overlay ending,
reopens Big Picture through Steam's native URI, and restores Hyprland
fullscreen. It does not replace Steam Input while a game is running.

## Install

From this directory:

```bash
./install.sh
```

The installer places:

- `ps5-steam-big-picture-monitor` in `~/.local/bin/`
- `ps5-steam-big-picture.service` in `~/.config/systemd/user/`

Then it enables and starts the service immediately.

For Omarchy's idle/sleep prevention, copy the rule from
`hyprland-snippet.lua` into `~/.config/hypr/hyprland.lua`, then run:

```bash
hyprctl reload
hyprctl configerrors
```

## Test and inspect

Check the service:

```bash
systemctl --user status ps5-steam-big-picture.service
journalctl --user -u ps5-steam-big-picture.service -f
```

Start the service, connect the controller, and press the PS button. Steam
should open its gamepad UI. The monitor watches Linux input events directly, so
it works even when the controller was connected before the service started.
Steam's `steam://open/bigpicture` request is forwarded to the existing Steam
client when one is already running, avoiding a second Steam instance. While a game is
running, the monitor leaves the PS button to Steam's native in-game overlay
instead of sending a competing Big Picture request. The launcher runs in a
separate transient user unit so Steam and its games are not children of the
controller-monitor service. If Steam replaces Big Picture with a hidden desktop
window after a Gamescope-wrapped game exits, the monitor requests Gamepad UI
again after the in-game overlay closes. Wired and Bluetooth DualSense
controllers are recognized by their Linux input device name.

To verify the controller identity manually while it is connected:

```bash
udevadm info --export-db | grep -i -C 4 -E 'DualSense|Wireless Controller|054c'
```

## Steam overlay on Hyprland

For Proton/XWayland games whose Steam overlay opens but does not reliably
receive controller input, run the game itself inside Gamescope. Install the
`gamescope` package and set the game's Steam launch options to:

```text
gamescope -f -W 3440 -H 1440 -- %command%
```

Adjust the width and height for the display. Wrapping the game gives Steam's
overlay and Steam Input a dedicated XWayland compositor; wrapping an already
running Steam client does not, because Steam only forwards the request to the
existing process.

## Uninstall

```bash
./uninstall.sh
```

This stops/disables the service and removes only the files installed by this
project. It does not remove Steam or unrelated user configuration.

## Files

- `ps5-steam-big-picture-monitor`: DualSense input monitor and Steam launcher
- `ps5-steam-big-picture.service`: user service definition
- `hyprland-snippet.lua`: Omarchy fullscreen idle-inhibit rule
- `install.sh`: reproducible installation step
- `uninstall.sh`: clean removal step
