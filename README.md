# PS5 controller → Steam Big Picture

This project starts Steam Big Picture when you press the PS button on a Sony
PS5 DualSense controller that is already connected to the current graphical
Linux session.

It uses a user-level `systemd` service and Linux input events, so it does not
install a system-wide udev rule or run Steam as root.

This monitor is intentional: Steam's native Linux Gamepad UI leaves its Big
Picture window floating and windowed when a game closes, and can destroy it
entirely. The service recognizes a game by the `reaper SteamLaunch AppId=...`
process Steam starts for every launch, including non-Steam shortcuts such as
PCSX2 (Gamescope and `gameoverlayui` are also honored when present). When a
game started from Big Picture exits, it returns to Big Picture exactly once:
the existing Gamepad UI window is refocused and fullscreened, and Steam's
native URI is used only when that window is gone. Re-sending
`steam://open/bigpicture` to a live Gamepad UI, during or after a game, makes
Steam switch back to desktop mode a few seconds after the game exits, so the
monitor never does that. The return is disarmed before Steam is contacted, so
a missing window cannot create a reopen loop and a later manual minimize or
close remains respected. It does not replace Steam Input while a game is
running.

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
running, the monitor translates the PS button to Steam's `Shift+Tab` overlay
shortcut. This preserves the Guide-button menu when Steam Input is disabled so
PCSX2 can receive the physical controllers directly, without sending a
competing Big Picture request. The launcher runs in a
separate transient user unit so Steam and its games are not children of the
controller-monitor service. If Steam replaces Big Picture with a hidden desktop
window after a game exits, the monitor requests Gamepad UI again after the game
and in-game overlay close. It waits for Steam's actual
Big Picture/Gamepad UI window instead of accidentally fullscreening the desktop
client while Gamepad UI is still loading. Wired and Bluetooth DualSense
controllers are recognized by their Linux input device name.

Run the deterministic lifecycle tests with:

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
