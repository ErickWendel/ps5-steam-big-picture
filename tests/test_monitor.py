import importlib.machinery
import importlib.util
import pathlib
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = pathlib.Path(__file__).parents[1] / "ps5-steam-big-picture-monitor"
LOADER = importlib.machinery.SourceFileLoader("monitor", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
monitor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = monitor
LOADER.exec_module(monitor)


class GameDetectionTests(unittest.TestCase):
    def make_process(self, root, pid, comm, argv):
        process = pathlib.Path(root, str(pid))
        process.mkdir()
        (process / "comm").write_text(comm + "\n")
        (process / "cmdline").write_bytes(
            b"".join(arg.encode() + b"\0" for arg in argv)
        )

    def test_detects_steam_reaper_for_non_steam_shortcut(self):
        with tempfile.TemporaryDirectory() as root:
            self.make_process(root, 10, "steam", ["steam"])
            self.make_process(
                root,
                11,
                "reaper",
                [
                    "/steam/ubuntu12_32/reaper",
                    "SteamLaunch",
                    "AppId=3581472424",
                    "--",
                    "/home/user/.local/bin/omarchy-pcsx2",
                ],
            )
            self.assertTrue(monitor.steam_game_running(root))

    def test_ignores_unrelated_reaper_processes(self):
        with tempfile.TemporaryDirectory() as root:
            self.make_process(root, 10, "steam", ["steam"])
            self.make_process(root, 12, "reaper", ["reaper", "--help"])
            self.assertFalse(monitor.steam_game_running(root))


class PcsxDetectionTests(unittest.TestCase):
    def make_process(self, root, pid, argv):
        process = pathlib.Path(root, str(pid))
        process.mkdir()
        (process / "cmdline").write_bytes(
            b"".join(arg.encode() + b"\0" for arg in argv)
        )

    def test_detects_pcsx2_appimage(self):
        with tempfile.TemporaryDirectory() as root:
            self.make_process(root, 10, ["/home/u/Applications/pcsx2-Qt.AppImage", "-batch"])
            self.assertTrue(monitor.pcsx2_running(root))

    def test_ignores_paths_that_only_mention_pcsx2_in_arguments(self):
        with tempfile.TemporaryDirectory() as root:
            self.make_process(root, 11, ["/usr/bin/bash", "-c", "pgrep pcsx2"])
            self.assertFalse(monitor.pcsx2_running(root))


class ButtonTests(unittest.TestCase):
    def press(self, game=False, pcsx2=False, last_launch=0.0, now=5.0):
        with mock.patch.object(monitor.time, "monotonic", return_value=now), \
             mock.patch.object(monitor, "steam_game_running", return_value=game), \
             mock.patch.object(monitor, "pcsx2_running", return_value=pcsx2), \
             mock.patch.object(monitor, "open_pcsx2_menu") as menu, \
             mock.patch.object(monitor.subprocess, "run") as run, \
             mock.patch.object(monitor, "launch_big_picture") as launch:
            result = monitor.handle_ps_button(last_launch)
        self.menu = menu
        return result, run, launch

    def test_button_is_debounced(self):
        result, run, launch = self.press(last_launch=4.5)
        self.assertEqual(result, 4.5)
        launch.assert_not_called()
        run.assert_not_called()

    def test_button_without_game_opens_big_picture(self):
        result, run, launch = self.press()
        self.assertEqual(result, 5.0)
        launch.assert_called_once_with()
        run.assert_not_called()

    def test_button_during_game_is_ignored(self):
        # Steam handles Guide itself; acting on the same press conflicts
        # with its overlay and UI mode transitions.
        result, run, launch = self.press(game=True)
        self.assertEqual(result, 5.0)
        launch.assert_not_called()
        run.assert_not_called()
        self.menu.assert_not_called()

    def test_button_during_pcsx2_opens_its_pause_menu(self):
        result, run, launch = self.press(game=True, pcsx2=True)
        self.assertEqual(result, 5.0)
        self.menu.assert_called_once_with()
        launch.assert_not_called()

    def test_pcsx2_menu_is_escape(self):
        completed = mock.Mock(returncode=0)
        with mock.patch.object(
            monitor.subprocess, "run", return_value=completed
        ) as run, mock.patch.object(monitor, "log"):
            self.assertTrue(monitor.open_pcsx2_menu())
        self.assertEqual(run.call_args.args[0], ["wtype", "-k", "Escape"])

    def test_big_picture_request_never_touches_windows(self):
        with mock.patch.object(monitor.subprocess, "run") as run, \
             mock.patch.object(monitor, "log"):
            monitor.launch_big_picture()
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0][-2:], ["steam", "steam://open/bigpicture"])


if __name__ == "__main__":
    unittest.main()
