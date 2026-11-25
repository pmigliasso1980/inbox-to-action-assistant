import unittest

from experiments.boundary_e2e.producer import encode_reminder


class ProducerTests(unittest.TestCase):
    def test_emits_integer_delay_field(self):
        packet = encode_reminder(5)
        self.assertEqual(set(packet), {"delay_seconds"})
        self.assertIs(type(packet["delay_seconds"]), int)

    def test_rejects_negative_delay(self):
        with self.assertRaises(ValueError):
            encode_reminder(-1)
