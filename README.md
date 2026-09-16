# PS5 controller → Steam Big Picture

This project starts Steam Big Picture when you press the PS button on a Sony
PS5 DualSense controller that is already connected to the current graphical
Linux session.

It uses a user-level `systemd` service and Linux input events, so it does not
install a system-wide udev rule or run Steam as root.

Gamescope must be installed because Steam Big Picture is launched inside it;
on Arch-based systems, install the `gamescope` package.

## Install

From this directory:

```bash
./install.sh
```

The installer places:

- `ps5-steam-big-picture-monitor` in `~/.local/bin/`
- `ps5-steam-big-picture.service` in `~/.config/systemd/user/`

Then it enables and starts the service immediately.

## Test and inspect

Check the service:

```bash
systemctl --user status ps5-steam-big-picture.service
journalctl --user -u ps5-steam-big-picture.service -f
```

Start the service, connect the controller, and press the PS button. Steam
should open its gamepad UI. The monitor watches Linux input events directly, so
it works even when the controller was connected before the service started.
Steam's `-gamepadui` request is forwarded to the existing Steam client when
one is already running, avoiding a second Steam instance. Wired and Bluetooth
DualSense controllers are recognized by their Linux input device name.

To verify the controller identity manually while it is connected:

```bash
udevadm info --export-db | grep -i -C 4 -E 'DualSense|Wireless Controller|054c'
```

## Uninstall

```bash
./uninstall.sh
```

This stops/disables the service and removes only the files installed by this
project. It does not remove Steam or unrelated user configuration.

## Files

- `ps5-steam-big-picture-monitor`: DualSense input monitor and Steam launcher
- `ps5-steam-big-picture.service`: user service definition
- `install.sh`: reproducible installation step
- `uninstall.sh`: clean removal step
