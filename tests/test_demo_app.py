import unittest
from demo_app.retry_policy import retry_delay


class RetryTests(unittest.TestCase):
    def test_initial_delays(self):
        self.assertEqual(retry_delay(0), 1)
        self.assertEqual(retry_delay(3), 8)

    def test_invalid_attempts(self):
        for value in (-1, 21, True, "2"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                retry_delay(value)
