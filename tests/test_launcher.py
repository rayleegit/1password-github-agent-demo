"""Recording-pause behavior with dummy values and no subprocess/network calls."""

import contextlib
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts import run_secure


class LauncherTests(unittest.TestCase):
    def run_launch(self, mode, pause, cancel=False):
        events = []
        output = io.StringIO()
        def hidden(prompt):
            events.append("hidden")
            return "DUMMY-KEY-CANARY"
        def answer(prompt):
            if prompt.startswith("Type SYNTHETIC"):
                events.append("consent")
                return "SYNTHETIC"
            events.append("pause")
            if cancel:
                raise KeyboardInterrupt
            return ""
        def launch(command, **kwargs):
            events.append("launch")
            self.assertNotIn("DUMMY-KEY-CANARY", str(command))
            self.assertNotIn("--pause-before-run", command)
            return SimpleNamespace(returncode=0)
        argv = ["run_secure.py", "--mode", mode]
        if pause:
            argv.append("--pause-before-run")
        with patch("sys.argv", argv), patch("sys.stdin.isatty", return_value=True), patch.object(run_secure.Path, "exists", return_value=True), patch.object(run_secure.getpass, "getpass", side_effect=hidden), patch("builtins.input", side_effect=answer), patch.object(run_secure.subprocess, "run", side_effect=launch), contextlib.redirect_stdout(output):
            if cancel:
                with self.assertRaises(KeyboardInterrupt):
                    run_secure.main()
            else:
                self.assertEqual(run_secure.main(), 0)
        self.assertNotIn("DUMMY-KEY-CANARY", output.getvalue())
        return events

    def test_live_pause_is_after_both_secrets_and_before_launch(self):
        self.assertEqual(self.run_launch("live", True), ["hidden", "consent", "hidden", "pause", "launch"])

    def test_smoke_pause_needs_no_model_key(self):
        self.assertEqual(self.run_launch("smoke", True), ["hidden", "pause", "launch"])

    def test_default_flow_is_unchanged(self):
        self.assertEqual(self.run_launch("smoke", False), ["hidden", "launch"])

    def test_cancel_does_not_launch_or_spend(self):
        self.assertNotIn("launch", self.run_launch("live", True, cancel=True))


if __name__ == "__main__":
    unittest.main()
