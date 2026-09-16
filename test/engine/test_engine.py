import json
import random
from pathlib import Path

import cocotb
from cocotb.triggers import Timer
from tools.witness_isa import HALT, DRIVE, EXPECT, WAIT, JMP, encode, execute, uart_program
from tools.protocol_lab import Drive, Expect, PulsePeer, run


class Harness:
    def __init__(self, dut):
        self.d = dut

    async def edge(self):
        await Timer(10, unit='ns')
        self.d.clk.value = 1
        await Timer(10, unit='ns')
        self.d.clk.value = 0

    async def reset(self):
        for name in ('clk', 'rst_n', 'load_valid', 'load_addr', 'load_word', 'start', 'abort', 'pins_in'):
            getattr(self.d, name).value = 0
        await self.edge()
        await self.edge()
        assert int(self.d.pins_oe.value) == 0
        assert int(self.d.done.value) == 0
        self.d.rst_n.value = 1
        await self.edge()

    async def load(self, words):
        for addr, word in enumerate(words):
            if word is None:
                continue
            assert int(self.d.load_ready.value) == 1
            self.d.load_addr.value = addr
            self.d.load_word.value = word
            self.d.load_valid.value = 1
            await self.edge()
        self.d.load_valid.value = 0

    async def start(self):
        self.d.start.value = 1
        await self.edge()
        self.d.start.value = 0
        assert int(self.d.running.value) == 1
        assert int(self.d.done.value) == 0

    def record(self):
        return {name: int(getattr(self.d, 'witness_' + name).value)
                for name in ('pc', 'cycle', 'word', 'observed', 'samples')} | {
                    'status': int(self.d.status.value),
                    'time_wrapped': int(self.d.time_wrapped.value)}

    async def compare(self, expected, peer=None):
        actual_trace = []
        for row in expected['trace']:
            assert int(self.d.running.value) == 1, row
            assert int(self.d.load_ready.value) == 0
            actual = dict(cycle=row['cycle'], value=int(self.d.pins_out.value),
                          enable=int(self.d.pins_oe.value))
            actual['observed'] = (peer(row['cycle'], actual['value'], actual['enable'])
                                  if peer else row['observed'])
            assert actual == row, (actual, row)
            actual_trace.append(actual)
            self.d.pins_in.value = actual['observed']
            await self.edge()
        assert int(self.d.running.value) == 0
        assert int(self.d.done.value) == 1
        assert int(self.d.pins_oe.value) == 0
        assert int(self.d.pins_out.value) == expected['final_value']
        record = self.record()
        assert record == {key: expected[key] for key in record}, (record, expected)
        self.d.pins_in.value = 255
        await self.edge()
        assert self.record() == record, 'first terminal record must be sticky'
        return dict(trace=actual_trace, witness=record)


@cocotb.test()
async def loaded_programs_and_original_model(dut):
    h = Harness(dut)
    await h.reset()
    for width in range(1, 9):
        for minimum in (1, 4):
            words = [encode(DRIVE, width, 0, 1), encode(DRIVE, 1, 0, 0),
                     encode(EXPECT, 3, 2, 2), encode(HALT)]
            expected = execute(words, PulsePeer(minimum))
            original = run([Drive(0, 1, width), Drive(0, 0, 1), Expect(2, 2, 3)],
                           PulsePeer(minimum))
            # Existing high-level semantics are independent of binary decoding.
            prefix = expected['trace'][:len(original['trace'])]
            assert prefix == [{k: r[k] for k in ('cycle', 'value', 'enable', 'observed')}
                              for r in original['trace']]
            assert expected['status'] == (1 if original['status'] == 'timeout' else 0)
            await h.load(words)
            await h.start()
            actual = await h.compare(expected, PulsePeer(minimum))
            if width == 1 and minimum == 4:
                saved_words, saved_result = words, actual
    out = Path(__file__).resolve().parents[2] / 'work' / 'rtl-witness.json'
    out.parent.mkdir(exist_ok=True)
    record = dict(schema=1, isa='ADR-0004-v1',
                  fixture={'kind': 'synthetic-pulse-peer', 'minimum_width': 4},
                  words=[f'{w:010x}' for w in saved_words], result=saved_result)
    out.write_text(json.dumps(record, indent=2) + '\n')
    # Deserialize the actual artifact, reload it, and replay against a fresh peer.
    exported = json.loads(out.read_text())
    replay_words = [int(word, 16) for word in exported['words']]
    minimum = exported['fixture']['minimum_width']
    await h.load(replay_words)
    await h.start()
    replayed = await h.compare(execute(replay_words, PulsePeer(minimum)), PulsePeer(minimum))
    assert replayed == exported['result']
    record['replay_matched'] = True
    out.write_text(json.dumps(record, indent=2) + '\n')


@cocotb.test()
async def inclusive_deadlines_and_random_programs(dut):
    h = Harness(dut)
    for deadline in (1, 2, 3, 7):
        for arrival in range(deadline + 2):
            await h.reset()
            words = [encode(EXPECT, deadline, 2, 2), encode(HALT)]
            expected = execute(words, lambda c, v, e: 0x82 if c >= arrival else 0x80)
            assert expected['status'] == (0 if arrival < deadline else 1)
            if arrival >= deadline:
                assert expected['cycle'] == deadline - 1
                assert expected['samples'] == deadline
            await h.load(words)
            await h.start()
            await h.compare(expected)
    rng = random.Random(0x5717)
    for case in range(160):
        await h.reset()
        words = []
        length = rng.randrange(2, 31)
        for pc in range(length):
            op = rng.choice((DRIVE, WAIT, EXPECT, JMP))
            count = rng.randrange(1, 10)
            if op == DRIVE:
                words.append(encode(op, count, rng.randrange(256), rng.randrange(256)))
            elif op == EXPECT:
                mask = rng.randrange(1, 256)
                words.append(encode(op, count, rng.randrange(256) & mask, mask))
            elif op == JMP:
                words.append(encode(op, b=rng.randrange(pc+1, length+1)))
            else:
                words.append(encode(op, count))
        words.append(encode(HALT))
        samples = [rng.randrange(256) for _ in range(400)]
        expected = execute(words, lambda c, v, e: samples[c])
        await h.load(words)
        await h.start()
        await h.compare(expected)


@cocotb.test()
async def programmed_uart_independent_wire_oracle(dut):
    h = Harness(dut)
    await h.reset()
    for byte in range(256):
        words = uart_program(byte, divisor=3)
        await h.load(words)
        await h.start()
        # Independently construct an entire frame as a bit-packed wire value.
        frame = (1 << 9) | (byte << 1)
        for cycle in range(30):
            assert int(dut.pins_out.value) == ((frame >> (cycle // 3)) & 1)
            assert int(dut.pins_oe.value) == 1
            await h.edge()
        assert int(dut.pins_oe.value) == 0  # HALT releases immediately on entry
        await h.edge()
        assert h.record()['status'] == 0
    await h.load(uart_program(0x55))
    await h.start()
    await h.compare(execute(uart_program(0x55)))


@cocotb.test()
async def loader_reset_abort_and_faults(dut):
    h = Harness(dut)
    await h.reset()
    await h.start()
    await h.compare(execute([]))
    for bad in [15 << 36, 1 << 32, 1, DRIVE << 36, encode(DRIVE, 1) | (1 << 32),
                EXPECT << 36 | 1 << 16, EXPECT << 36 | 1 << 16 | 0x0201,
                WAIT << 36 | 1 << 16 | 1, JMP << 36 | 32]:
        await h.load([bad])
        await h.start()
        await h.compare(execute([bad]))
    # Load wins over simultaneous start.
    dut.load_addr.value = 0
    dut.load_word.value = encode(DRIVE, 4, 0x55, 0xff)
    dut.load_valid.value = 1
    dut.start.value = 1
    await h.edge()
    assert int(dut.running.value) == 0
    dut.load_valid.value = 0
    dut.start.value = 0
    await h.load([encode(DRIVE, 4, 0x55, 0xff), encode(HALT)])
    await h.start()
    # A hostile write/start during a run cannot alter its program or restart it.
    dut.load_valid.value = 1
    dut.load_addr.value = 1
    dut.load_word.value = 15 << 36
    dut.start.value = 1
    await h.edge()
    dut.load_valid.value = 0
    dut.start.value = 0
    expected = execute([encode(DRIVE, 4, 0x55, 0xff), encode(HALT)])
    expected['trace'] = expected['trace'][1:]
    await h.compare(expected)
    # Program survives a run and idle writes do not erase its witness.
    record = h.record()
    await h.load([encode(DRIVE, 4, 0x55, 0xff)])
    assert h.record() == record
    await h.start()
    await h.edge()
    dut.abort.value = 1
    dut.pins_in.value = 0xa5
    await h.edge()
    assert int(dut.pins_oe.value) == 0
    assert h.record() == dict(pc=0, cycle=1, word=encode(DRIVE, 4, 0x55, 0xff),
                             observed=0xa5, samples=0, status=4, time_wrapped=0)
    dut.abort.value = 0
    await h.start()
    dut.rst_n.value = 0
    await h.edge()
    assert int(dut.pins_oe.value) == 0
    assert int(dut.done.value) == 0
    dut.rst_n.value = 1
    await h.start()
    await h.compare(execute([]))  # reset invalidated the program


@cocotb.test()
async def maximum_duration_and_pc_wrap(dut):
    h = Harness(dut)
    await h.reset()
    words = [encode(DRIVE, 65535, 0xa5, 0x5a), encode(HALT)]
    await h.load(words)
    await h.start()
    for cycle in range(65535):
        assert int(dut.pins_oe.value) == 0x5a
        assert int(dut.pins_out.value) == 0xa5
        await h.edge()
    assert int(dut.pins_oe.value) == 0
    await h.edge()
    assert h.record()['cycle'] == 65535
    assert h.record()['status'] == 0
    # Wrap 31 -> 0, then stop the second pass with a changed sampled input.
    words = [encode(EXPECT, 1, 1, 1)] + [encode(WAIT, 1)] * 31
    expected = execute(words, lambda c, v, e: int(c == 0))
    assert expected['cycle'] == 32 and expected['pc'] == 0
    await h.load(words)
    await h.start()
    await h.compare(expected)
    # Backward JMP consumes one cycle; abort is the explicit loop escape.
    await h.load([encode(DRIVE, 2, 3, 3), encode(JMP, b=0)])
    await h.start()
    for _ in range(10):
        assert int(dut.pins_out.value) == 3
        assert int(dut.pins_oe.value) == 3
        await h.edge()
    dut.abort.value = 1
    await h.edge()
    assert h.record()['cycle'] == 10
    assert h.record()['pc'] == 0
    assert h.record()['status'] == 4


@cocotb.test()
async def outputs_are_registered(dut):
    h = Harness(dut)
    await h.reset()
    await h.load([encode(DRIVE, 2, 0x96, 0x69), encode(HALT)])
    await h.start()
    before = (int(dut.pins_out.value), int(dut.pins_oe.value))
    assert before == (0x96, 0x69)
    # Changing inputs and control signals away from an edge cannot change outputs.
    for value in range(8):
        dut.pins_in.value = value
        dut.load_addr.value = value
        dut.load_word.value = value
        dut.abort.value = value & 1
        await Timer(1, unit='ns')
        assert (int(dut.pins_out.value), int(dut.pins_oe.value)) == before
    dut.abort.value = 0
    dut.rst_n.value = 0
    await Timer(1, unit='ns')
    assert (int(dut.pins_out.value), int(dut.pins_oe.value)) == before
    await h.edge()
    assert int(dut.pins_oe.value) == 0
    assert int(dut.pins_out.value) == 0


@cocotb.test()
async def timed_capture_capacity_and_lifecycle(dut):
    from tools.witness_isa import SAMPLE
    h = Harness(dut)
    await h.reset()
    rng = random.Random(0xcab)
    # All eight selectors, varied durations and nonconstant inputs: only the
    # final sample may contribute a bit. Compare outputs and terminal witness too.
    for pin in range(8):
        words = [encode(DRIVE, 2, 0xa5, 0x5a)] + [encode(SAMPLE, n, pin) for n in (1, 2, 7, 3, 4, 1, 2, 5)] + [encode(HALT)]
        inputs = [rng.randrange(256) for _ in range(40)]
        expected = execute(words, lambda c,v,e: inputs[c])
        await h.load(words)
        await h.start()
        assert int(dut.capture_count.value) == int(dut.capture_data.value) == 0
        await h.compare(expected)
        assert int(dut.capture_count.value) == expected['capture_count'] == 8
        assert int(dut.capture_data.value) == expected['capture_data']
    # A loop deliberately exhausts capacity; preserve first 32 bits and stop on 33.
    words = [encode(SAMPLE, 2, 7), encode(JMP, b=0)]
    expected = execute(words, lambda c,v,e: (0xd36a195c >> (31-min(c//3,31)) & 1) << 7)
    await h.load(words)
    await h.start()
    await h.compare(expected)
    assert expected['status'] == 5 and expected['capture_count'] == 32
    assert int(dut.capture_data.value) == 0xd36a195c
    assert int(dut.capture_count.value) == 32
    # Idle program writes retain capture; accepted START clears it.
    await h.load([encode(SAMPLE, 1, 0), encode(HALT)])
    assert int(dut.capture_count.value) == 32
    await h.start()
    assert int(dut.capture_count.value) == 0
    dut.pins_in.value = 1
    dut.abort.value = 1
    await h.edge()
    assert int(dut.capture_count.value) == 0 and h.record()['status'] == 4
    dut.abort.value = 0
    await h.start()
    await h.edge()
    assert int(dut.capture_count.value) == 1
    await h.edge()
    assert int(dut.capture_data.value) == 1
    await h.start()
    dut.rst_n.value = 0
    await h.edge()
    assert int(dut.capture_count.value) == int(dut.capture_data.value) == 0
    dut.rst_n.value = 1
    await h.edge()
    for bad in [SAMPLE << 36, SAMPLE << 36 | 1 << 16 | 8 << 8,
                SAMPLE << 36 | 1 << 16 | 1]:
        await h.load([bad])
        await h.start()
        await h.compare(execute([bad]))
        assert int(dut.capture_count.value) == 0
