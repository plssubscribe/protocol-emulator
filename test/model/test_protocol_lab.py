import unittest
from tools.protocol_lab import Drive, Expect, run, experiment, replay


class TimingContract(unittest.TestCase):
    def test_deadline_inclusive(self):
        for arrival in range(5):
            result = run([Expect(1, 1, 3)], lambda c, v, e: int(c >= arrival))
            self.assertEqual(result['status'], 'pass' if arrival < 3 else 'timeout')
            self.assertEqual(result['cycles'], min(arrival + 1, 3))

    def test_drive_duration_and_mask(self):
        result = run([Drive(5, 7, 2), Drive(0, 0, 1), Expect(2, 2, 1)],
                     lambda c, v, e: 255)
        self.assertEqual([(r['value'], r['enable']) for r in result['trace']],
                         [(5, 7), (5, 7), (0, 0), (0, 0)])
        self.assertEqual(result['status'], 'pass')

    def test_first_failure_stops_and_releases(self):
        result = run([Drive(0, 1, 1), Expect(2, 2, 2), Drive(255, 255, 1)],
                     lambda c, v, e: 0)
        self.assertEqual(result['failure'], dict(pc=1, cycle=2, mask=2,
                         expected=2, observed=0, samples=2))
        self.assertEqual(result['cycles'], 3)
        self.assertEqual(result['final_output']['enable'], 0)

    def test_budget_is_not_a_peer_failure(self):
        result = run([Drive(0, 1, 4)], lambda c, v, e: 0, budget=2)
        self.assertEqual(result['status'], 'budget_exhausted')
        self.assertEqual(len(result['trace']), 2)
        self.assertEqual(result['final_output']['enable'], 0)

    def test_invalid_program(self):
        for op in [Drive(0, 1, 0), Drive(256, 0, 1), Expect(0, 0, 1),
                   Expect(1, 2, 3), Expect(1, 1, 65536)]:
            with self.assertRaises(ValueError):
                run([op], lambda c, v, e: 0)

    def test_experiment_boundary_and_replay(self):
        record = experiment()
        self.assertEqual([c['width'] for c in record['cases'] if c['faulty'] == 'timeout'],
                         [1, 2, 3])
        self.assertEqual(record['smallest_failing_width_in_sweep'], 1)
        self.assertEqual(replay(record), record['result'])


if __name__ == '__main__':
    unittest.main()
