import json
import tempfile
import unittest
from pathlib import Path
from agent import DemoError
from budget import reservation, reserve_request


def request():
    return {"model": "gpt-6.1-terra", "service_tier": "default", "max_output_tokens": 900, "input": "synthetic"}


class BudgetTests(unittest.TestCase):
    def test_request_reservation_is_conservative(self):
        self.assertGreater(reservation(request()), 29000)

    def test_unknown_model_rejected(self):
        payload = request()
        payload["model"] = "unreviewed-model"
        with self.assertRaises(DemoError):
            reservation(payload)

    def test_large_payload_rejected(self):
        payload = request()
        payload["input"] = "x" * 50001
        with self.assertRaises(DemoError):
            reservation(payload)

    def test_cumulative_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = Path(folder) / "budget.json"
            ledger.write_text(json.dumps({"reserved_microdollars": 990000, "requests": 10}))
            with self.assertRaises(DemoError):
                reserve_request(request(), ledger)

    def test_metadata_only_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = Path(folder) / "budget.json"
            reserve_request(request(), ledger)
            self.assertNotIn("synthetic", ledger.read_text())
            self.assertEqual(json.loads(ledger.read_text())["requests"], 1)

    def test_invalid_ledger_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = Path(folder) / "budget.json"
            ledger.write_text("broken")
            with self.assertRaises(DemoError):
                reserve_request(request(), ledger)
