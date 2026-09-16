import unittest
from tools.i2c_lab import BusDecoder, Controller, target_program, SCL, SDA
from tools.witness_isa import decode, DRIVE


class I2CFixtures(unittest.TestCase):
    def test_known_bus_transaction(self):
        decoder = BusDecoder()
        waveform = [3, 1]  # idle, START
        bits = [1, 0, 1, 0, 0, 0, 0, 0, 0]
        for bit in bits:
            waveform += [bit * SDA, bit * SDA | SCL, bit * SDA]
        waveform += [0, 1, 3]  # STOP setup and STOP
        for bus in waveform:
            decoder.observe(bus)
        self.assertEqual(decoder.starts, 1)
        self.assertEqual(decoder.transfers, [dict(bits=bits, address_byte=0xa0, ack=True)])

    def test_fixture_mutation_changes_wait_behavior(self):
        for faulty in (False, True):
            peer = Controller(ignore_stretch=faulty)
            data_during_stretch = []
            for cycle in range(70):
                stretching = 14 <= cycle < 48
                bus = 3 & ~(peer.pull_low | (SCL if stretching else 0))
                if stretching:
                    data_during_stretch.append(bool(bus & SDA))
                peer.advance(bus)
            self.assertEqual(all(data_during_stretch), not faulty)

    def test_firmware_capacity_and_open_drain(self):
        for width in (0, 1, 48, 800, 65535):
            words = target_program(width)
            self.assertEqual(len(words), 32)
            for word in words:
                op, duration, value, enable = decode(word)
                if op == DRIVE:
                    self.assertEqual(value, 0)
                    self.assertEqual(enable & ~3, 0)
        for width in (-1, 65536, 1.5):
            with self.assertRaises(ValueError):
                target_program(width)
