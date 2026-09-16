import unittest
from tools.spi_lab import controller_program
from tools.witness_isa import decode, DRIVE, EXPECT


class SPIProgramTest(unittest.TestCase):
    def test_store_and_timing_budget(self):
        for mode in range(4):
            for half in (4, 8, 65535):
                words = controller_program(0xa6, 0x59, mode, half)
                self.assertEqual(len(words), 28)
                decoded = [decode(w) for w in words]
                self.assertEqual(sum(d[1] for d in decoded), 19*half)
                self.assertEqual(sum(d[0] == EXPECT for d in decoded), 8)
                self.assertTrue(all(d[3] == 7 for d in decoded if d[0] == DRIVE))

    def test_reject_unsupported_timing_and_bytes(self):
        for args in ((256, 0), (0, -1), (0, 0, 4), (0, 0, 0, 3), (0, 0, 0, 65536)):
            with self.assertRaises(ValueError):
                controller_program(*args)
