"""Executable timing proposal, not the chip ISA or an electrical simulator."""
from dataclasses import asdict, dataclass
import argparse
import json
from pathlib import Path


@dataclass(frozen=True)
class Drive:
    value: int
    enable: int
    cycles: int


@dataclass(frozen=True)
class Expect:
    mask: int
    value: int
    cycles: int


def run(program, peer, budget=10000):
    """Sample peer(cycle, value, enable) once per cycle, after applying DRIVE.

    EXPECT samples on its first cycle and succeeds on the last allowed sample.
    Instructions start on the cycle after their predecessor completes. Failure
    releases all enables at the following boundary. Inputs are already synchronized.
    """
    if budget < 1:
        raise ValueError('budget must be positive')
    for op in program:
        if not isinstance(op, (Drive, Expect)) or not 1 <= op.cycles <= 65535:
            raise ValueError('invalid instruction or duration')
        fields = (op.value, op.enable) if isinstance(op, Drive) else (op.mask, op.value)
        if any(type(v) is not int or not 0 <= v <= 255 for v in fields):
            raise ValueError('pin fields must be bytes')
        if isinstance(op, Expect) and (op.mask == 0 or op.value & ~op.mask):
            raise ValueError('EXPECT requires nonempty mask and masked value')
    trace = []
    cycle = value = enable = 0

    def finish(status, failure=None):
        return dict(status=status, cycles=cycle, failure=failure, trace=trace,
                    final_output=dict(value=value, enable=0))

    for pc, op in enumerate(program):
        if isinstance(op, Drive):
            value, enable = op.value, op.enable
        for age in range(op.cycles):
            if cycle >= budget:
                return finish('budget_exhausted', dict(pc=pc, cycle=cycle))
            observed = peer(cycle, value, enable)
            if type(observed) is not int or not 0 <= observed <= 255:
                raise ValueError('peer sample must be a byte')
            trace.append(dict(cycle=cycle, pc=pc, value=value, enable=enable,
                              observed=observed))
            cycle += 1
            if isinstance(op, Expect) and observed & op.mask == op.value:
                break
        else:
            if isinstance(op, Expect):
                return finish('timeout', dict(pc=pc, cycle=cycle-1, mask=op.mask,
                              expected=op.value, observed=observed,
                              samples=op.cycles))
    return finish('pass')


class PulsePeer:
    """Synthetic device: acknowledge a released pulse if its width was sufficient.

    Correct fixture accepts width >= 1; deliberately faulty fixture requires >= 4.
    This is a toy request/acknowledge protocol, not an I2C implementation.
    """
    def __init__(self, minimum_width):
        self.minimum_width = minimum_width
        self.width = 0
        self.ack = 0

    def __call__(self, cycle, value, enable):
        if enable & 1 and not value & 1:
            self.width += 1
            self.ack = 0
        elif self.width:
            self.ack = 2 if self.width >= self.minimum_width else 0
            self.width = 0
        return self.ack


def pulse_program(width):
    return [Drive(0, 1, width), Drive(0, 0, 1), Expect(2, 2, 3)]


def experiment():
    cases = []
    # Exhaustive finite sweep: no assumption that failures are monotonic.
    for width in range(1, 9):
        program = pulse_program(width)
        good = run(program, PulsePeer(1))
        faulty = run(program, PulsePeer(4))
        assert good['status'] == 'pass'
        cases.append(dict(width=width, correct=good['status'], faulty=faulty['status']))
    failing = [case['width'] for case in cases if case['faulty'] == 'timeout']
    width = min(failing)
    program = pulse_program(width)
    return dict(schema=1, model='synchronized-cycle-proposal-v1',
                fixture=dict(kind='synthetic-pulse-peer', minimum_width=4),
                cases=cases, smallest_failing_width_in_sweep=width,
                program=[dict(op=type(op).__name__, **asdict(op)) for op in program],
                result=run(program, PulsePeer(4)))


def replay(record):
    if (record['schema'] != 1 or record['model'] != 'synchronized-cycle-proposal-v1'
            or record['fixture']['kind'] != 'synthetic-pulse-peer'):
        raise ValueError('unsupported replay format')
    types = {'Drive': Drive, 'Expect': Expect}
    program = [types[item['op']](**{k: v for k, v in item.items() if k != 'op'})
               for item in record['program']]
    return run(program, PulsePeer(record['fixture']['minimum_width']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('work/protocol-witness.json'))
    parser.add_argument('--replay', type=Path)
    args = parser.parse_args()
    if args.replay:
        record = json.loads(args.replay.read_text())
        if replay(record) != record['result']:
            raise SystemExit('Replay mismatch')
        print('Replay matched every cycle and the failure record.')
    else:
        record = experiment()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(record, indent=2) + '\n')
        for case in record['cases']:
            print(f"width={case['width']}: correct={case['correct']}, faulty={case['faulty']}")
        print(f"Smallest failing width in sweep: {record['smallest_failing_width_in_sweep']}")
        print(f'Witness: {args.output}')
