import importlib.machinery
import importlib.util
import pathlib
import sys
import unittest
from unittest import mock


SCRIPT = pathlib.Path(__file__).parents[1] / "ps5-steam-big-picture-monitor"
LOADER = importlib.machinery.SourceFileLoader("monitor", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
monitor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = monitor
LOADER.exec_module(monitor)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.lifecycle = monitor.BigPictureLifecycle(restore_delay=2.0)

    def observe(self, now, big_picture=False, overlay=False, game=False):
        return self.lifecycle.observe(now, big_picture, overlay, game)

    def test_game_exit_restores_once_then_disarms(self):
        self.observe(0, big_picture=True)
        self.observe(1, overlay=True, game=True)
        self.observe(2, overlay=False, game=False)

        self.assertEqual(self.observe(3.9), monitor.LifecycleAction.NONE)
        self.assertEqual(
            self.observe(4.0), monitor.LifecycleAction.RESTORE_BIG_PICTURE
        )
        self.assertEqual(self.observe(5.0), monitor.LifecycleAction.NONE)
        self.assertEqual(
            self.lifecycle.state, monitor.LifecycleState.RETURN_COMPLETED
        )

    def test_minimize_after_completed_return_does_not_restore(self):
        self.lifecycle.state = monitor.LifecycleState.RETURN_COMPLETED
        self.observe(0, big_picture=True)
        self.assertEqual(
            self.lifecycle.state, monitor.LifecycleState.BIG_PICTURE_ACTIVE
        )

        self.assertEqual(self.observe(1, big_picture=False), monitor.LifecycleAction.NONE)
        self.assertEqual(self.lifecycle.state, monitor.LifecycleState.IDLE)
        self.assertEqual(self.observe(20), monitor.LifecycleAction.NONE)

    def test_close_without_game_does_not_restore(self):
        self.observe(0, big_picture=True)
        self.observe(1, big_picture=False)
        self.assertEqual(self.lifecycle.state, monitor.LifecycleState.IDLE)
        self.assertEqual(self.observe(10), monitor.LifecycleAction.NONE)

    def test_repeated_requests_do_not_create_restore(self):
        self.lifecycle.big_picture_requested()
        self.lifecycle.big_picture_requested()
        self.assertEqual(
            self.lifecycle.state, monitor.LifecycleState.BIG_PICTURE_ACTIVE
        )
        self.assertEqual(self.observe(10, big_picture=True), monitor.LifecycleAction.NONE)

    def test_missing_window_during_game_does_not_cancel_return(self):
        self.observe(0, big_picture=True)
        self.observe(1, game=True)
        self.assertEqual(self.observe(2), monitor.LifecycleAction.NONE)
        self.assertEqual(self.observe(4), monitor.LifecycleAction.RESTORE_BIG_PICTURE)
        self.assertEqual(self.observe(5), monitor.LifecycleAction.NONE)

    def test_waits_for_overlay_when_game_closes_first(self):
        self.observe(0, big_picture=True)
        self.observe(1, overlay=True, game=True)
        self.observe(2, overlay=True, game=False)
        self.assertEqual(self.lifecycle.state, monitor.LifecycleState.GAME_ACTIVE)
        self.observe(3, overlay=False, game=False)
        self.assertEqual(self.observe(4.9), monitor.LifecycleAction.NONE)
        self.assertEqual(self.observe(5), monitor.LifecycleAction.RESTORE_BIG_PICTURE)

    def test_waits_for_game_when_overlay_closes_first(self):
        self.observe(0, big_picture=True)
        self.observe(1, overlay=True, game=True)
        self.observe(2, overlay=False, game=True)
        self.assertEqual(self.lifecycle.state, monitor.LifecycleState.GAME_ACTIVE)
        self.observe(3, overlay=False, game=False)
        self.assertEqual(self.observe(5), monitor.LifecycleAction.RESTORE_BIG_PICTURE)

    def test_process_reappearing_during_delay_restarts_shutdown_wait(self):
        self.observe(0, big_picture=True)
        self.observe(1, overlay=True)
        self.observe(2)
        self.observe(3, game=True)
        self.assertEqual(self.lifecycle.state, monitor.LifecycleState.GAME_ACTIVE)
        self.observe(4)
        self.assertEqual(self.observe(5.9), monitor.LifecycleAction.NONE)
        self.assertEqual(self.observe(6), monitor.LifecycleAction.RESTORE_BIG_PICTURE)

    def test_game_not_launched_from_big_picture_never_arms(self):
        self.observe(0, overlay=True, game=True)
        self.observe(1, overlay=False, game=False)
        self.assertEqual(self.lifecycle.state, monitor.LifecycleState.IDLE)
        self.assertEqual(self.observe(10), monitor.LifecycleAction.NONE)


class FullscreenRestoreTests(unittest.TestCase):
    def test_fullscreens_returned_window_only_once(self):
        client = {
            "address": "0x1234",
            "class": "steam",
            "title": "Steam Big Picture",
            "fullscreen": 0,
        }
        with mock.patch.object(monitor, "visible_steam_window", return_value=client), \
             mock.patch.object(monitor.subprocess, "run") as run, \
             mock.patch.object(monitor, "log"):
            self.assertTrue(monitor.restore_steam_fullscreen())

        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(commands), 2)
        self.assertTrue(all(command[:2] == ["hyprctl", "dispatch"] for command in commands))

    def test_missing_window_times_out_without_dispatch(self):
        clock = mock.Mock(side_effect=[0.0, 0.0, 0.5, 1.0])
        with mock.patch.object(monitor, "visible_steam_window", return_value=None), \
             mock.patch.object(monitor.time, "monotonic", clock), \
             mock.patch.object(monitor.time, "sleep"), \
             mock.patch.object(monitor.subprocess, "run") as run, \
             mock.patch.object(monitor, "log"):
            self.assertFalse(monitor.restore_steam_fullscreen(timeout=1.0))

        run.assert_not_called()


class ButtonTests(unittest.TestCase):
    def test_button_is_debounced(self):
        with mock.patch.object(monitor.time, "monotonic", return_value=1.0), \
             mock.patch.object(monitor, "launch_big_picture") as launch:
            self.assertEqual(monitor.handle_ps_button(0.5), (0.5, False))
        launch.assert_not_called()

    def test_button_during_overlay_is_left_to_steam(self):
        with mock.patch.object(monitor.time, "monotonic", return_value=5.0), \
             mock.patch.object(monitor, "process_is_running", return_value=True), \
             mock.patch.object(monitor, "log"), \
             mock.patch.object(monitor, "launch_big_picture") as launch:
            self.assertEqual(monitor.handle_ps_button(0.0), (5.0, False))
        launch.assert_not_called()

    def test_button_during_gamescope_session_is_left_to_steam(self):
        with mock.patch.object(monitor.time, "monotonic", return_value=5.0), \
             mock.patch.object(
                 monitor,
                 "process_is_running",
                 side_effect=lambda name: name == "gamescope",
             ), \
             mock.patch.object(monitor, "log"), \
             mock.patch.object(monitor, "launch_big_picture") as launch:
            self.assertEqual(monitor.handle_ps_button(0.0), (5.0, False))
        launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
