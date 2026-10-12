# PS5 controller → Steam Big Picture

This project starts Steam Big Picture when you press the PS button on a Sony
PS5 DualSense controller that is already connected to the current graphical
Linux session.

It uses a user-level `systemd` service and Linux input events, so it does not
install a system-wide udev rule or run Steam as root.

The monitor deliberately does as little as possible:

- **No game running:** the PS button sends `steam://open/bigpicture` once.
  Window placement is left to Steam and Hyprland.
- **A Steam game is running** (detected through the `reaper SteamLaunch
  AppId=...` process Steam starts for every launch, including non-Steam
  shortcuts): the press is left to Steam Input, which opens Steam's own menu.
- **PCSX2 is running:** its shortcuts run with Steam Input disabled so PCSX2
  owns the controllers, and Steam's overlay cannot take controller input in
  PCSX2's Qt/xcb window anyway. The press is forwarded as `Escape`, which
  PCSX2 binds to its controller-navigable pause menu.

Earlier versions also tried to return to Big Picture after a game, focus and
fullscreen Steam's windows, and inject overlay shortcuts. Each of those raced
Steam's own UI mode and focus handling on Hyprland (Big Picture dropping to
desktop mode, games opening behind it, controller input going to a hidden
window), so they were removed. Steam may leave Big Picture when a game closes;
pressing PS again reopens it.

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
client when one is already running, avoiding a second Steam instance. The
launcher runs in a separate transient user unit so Steam and its games are not
children of the controller-monitor service. Wired and Bluetooth DualSense
controllers are recognized by their Linux input device name.

Run the tests with:

```bash
python -m unittest discover -s tests -v
```

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
