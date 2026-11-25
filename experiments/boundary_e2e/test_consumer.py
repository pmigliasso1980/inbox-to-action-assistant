import unittest

from experiments.boundary_e2e.consumer import schedule


class ConsumerTests(unittest.TestCase):
    def test_adds_wire_seconds_to_clock(self):
        self.assertEqual(schedule({"delay_seconds": 300}, 1000),
                         {"due_at_epoch_seconds": 1300})

    def test_rejects_negative_wire_delay(self):
        with self.assertRaises(ValueError):
            schedule({"delay_seconds": -1}, 1000)
