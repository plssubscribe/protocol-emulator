"""Only public Tiny Tapeout pins; also usable on its synthesized netlist."""
import json
from pathlib import Path

import cocotb
from cocotb.triggers import Timer
from tools.witness_host import WitnessHost, HostError, packet, crc8, decode_reply
from tools.witness_isa import DRIVE, EXPECT, HALT, JMP, encode, execute, uart_program


class Pins:
    def __init__(self, dut, half=4):
        self.d = dut
        self.half = half
        self.controls = 4
        self.runs = []
        self.current = None

    async def cycles(self, count):
        for _ in range(count):
            self.d.clk.value = 0
            self.d.ui_in.value = self.controls
            await Timer(10, unit='ns')
            self.d.clk.value = 1
            await Timer(10, unit='ns')
            status = int(self.d.uo_out.value)
            assert status & 0xe0 == 0
            if status & 4:
                if self.current is None:
                    self.current = []
                self.current.append((int(self.d.uio_out.value), int(self.d.uio_oe.value)))
            elif self.current is not None:
                self.runs.append(self.current)
                self.current = None

    async def reset(self):
        self.controls = 4
        self.d.ena.value = 1
        self.d.uio_in.value = 0
        self.d.rst_n.value = 0
        await self.cycles(4)
        assert int(self.d.uio_oe.value) == 0
        assert int(self.d.uio_out.value) == 0
        assert int(self.d.uo_out.value) & 0xfe == 0
        self.d.rst_n.value = 1
        await self.cycles(4)
        self.runs.clear()
        self.current = None

    async def transfer(self, data, bits=64):
        assert len(data) == 8
        value = int.from_bytes(data, 'big')
        self.controls = 0
        await self.cycles(4)
        received = 0
        for bit in range(bits):
            mosi = (value >> (63-bit)) & 1 if bit < 64 else 0
            self.controls = mosi << 1
            await self.cycles(self.half)
            received = (received << 1) | ((int(self.d.uo_out.value) >> 1) & 1)
            self.controls |= 1
            await self.cycles(self.half)
        self.controls = 0
        await self.cycles(4)
        self.controls = 4
        await self.cycles(4)
        return received.to_bytes((bits+7)//8, 'big')


@cocotb.test()
async def host_load_execute_and_witness(dut):
    pins = Pins(dut)
    await pins.reset()
    host = WitnessHost(pins.transfer)
    assert crc8(b'123456789') == 0xf4
    # A complete valid WRITE is inert while locked.
    await pins.transfer(packet(0x20, encode(DRIVE, 8, 255, 255)))
    assert int(dut.uio_oe.value) == 0
    assert int(dut.uo_out.value) & 0xfe == 0
    await host.unlock()
    await host.start()
    locked_write_check = await host.snapshot()
    assert locked_write_check['status'] == 3
    assert locked_write_check['pc'] == 0 and locked_write_check['cycle'] == 0
    assert locked_write_check['word'] == 0 and pins.runs[-1] == [(0, 0)]
    # A later uninitialized-slot fault must not hide a forbidden initial WRITE.
    # Exercise every address bit and every payload bit through the serial link.
    await host.write(0, encode(JMP, b=31))
    await host.write(31, encode(EXPECT, 2, 0x80, 0x80))
    await host.start()
    boundary = await host.snapshot()
    assert boundary['pc'] == 31 and boundary['cycle'] == 2 and boundary['status'] == 1
    assert boundary['word'] == encode(EXPECT, 2, 0x80, 0x80)
    await host.write(0, (1 << 40) - 1)
    await host.start()
    illegal = await host.snapshot()
    assert illegal['status'] == 2 and illegal['word'] == (1 << 40) - 1
    assert pins.runs[-1] == [(0, 0)]
    snapshots = []
    for width in (1, 9):
        words = [encode(DRIVE, width, 0x35, 0x81), encode(DRIVE, 1, 0, 0),
                 encode(EXPECT, 3, 2, 2), encode(HALT)]
        await host.program(words)
        await host.start()
        record = await host.snapshot()
        expected = execute(words)
        assert pins.runs[-1] == [(r['value'], r['enable']) for r in expected['trace']]
        for name in ('status', 'pc', 'cycle', 'word', 'observed', 'samples'):
            assert record[name] == expected[name], (record, expected)
        assert record['done'] and not record['running'] and not record['host_error']
        snapshots.append(record)
    # Program-generated UART is observed through protocol pin 0, distinct from
    # the always-running diagnostic UART on dedicated output 0.
    await host.program(uart_program(0xa6, 3))
    await host.start()
    levels = pins.runs[-1]
    frame = 1 << 9 | 0xa6 << 1
    assert levels == [((frame >> (cycle//3)) & 1, 1) for cycle in range(30)] + [(1, 0)]
    record = await host.snapshot()
    assert record['done'] and record['status'] == 0
    path = Path(__file__).resolve().parents[1] / 'work' / 'pin-host-witness.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(dict(transport='ADR-0005-v1', scope='public-pin RTL simulation',
                    timeout_snapshots=snapshots, programmed_uart='A6, divisor 3: passed'), indent=2)+'\n')


@cocotb.test()
async def host_corrupt_frames_busy_abort_and_reset(dut):
    pins = Pins(dut, half=5)
    await pins.reset()
    host = WitnessHost(pins.transfer)
    await host.unlock()
    await host.program([encode(DRIVE, 65535, 0x56, 0xff), encode(HALT)])
    corrupt = bytearray(packet(0x20, encode(DRIVE, 1, 255, 255)))
    corrupt[-1] ^= 1
    for data, bits, error in [(bytes(corrupt), 64, 1), (packet(0x40), 63, 2),
                              (packet(0x40), 65, 2)]:
        await pins.transfer(data, bits=bits)
        code, _ = decode_reply(await pins.transfer(packet(0)))
        assert code == error
        assert int(dut.uo_out.value) & 4 == 0  # no unexpected START
        assert int(dut.uio_oe.value) == 0
    await host.start()
    assert int(dut.uio_out.value) == 0x56  # corrupt WRITE never committed
    for command, payload in [(0x20, encode(DRIVE, 1, 0xff, 0xff)), (0x40, 0)]:
        try:
            await host.request(command, payload)
        except HostError as error:
            assert error.code == 3
        else:
            assert False, 'busy command was accepted'
    await host.abort()
    record = await host.snapshot()
    assert record['status'] == 4 and record['done'] and record['host_error']
    assert int(dut.uio_oe.value) == 0
    await host.start()
    assert int(dut.uio_out.value) == 0x56  # busy WRITE also left memory intact
    await pins.reset()
    assert int(dut.uio_oe.value) == 0
    await host.unlock()
    await host.start()
    record = await host.snapshot()
    assert record['status'] == 3 and record['done'] and not record['host_error']


@cocotb.test()
async def host_synchronized_response_and_atomic_snapshot(dut):
    pins = Pins(dut, half=7)
    await pins.reset()
    host = WitnessHost(pins.transfer)
    await host.unlock()
    # Leave EXPECT running while the host START acknowledgement is transferred.
    words = [encode(EXPECT, 65535, 0x80, 0x80), encode(HALT)]
    await host.program(words)
    await host.start()
    assert int(dut.uo_out.value) & 4
    dut.uio_in.value = 0x80
    await pins.cycles(1)
    assert int(dut.uo_out.value) & 4
    await pins.cycles(1)
    assert int(dut.uo_out.value) & 4
    await pins.cycles(1)  # core consumes the second-stage sample, enters HALT
    assert int(dut.uo_out.value) & 4
    await pins.cycles(1)  # HALT retires
    assert int(dut.uo_out.value) & 8
    passed = await host.snapshot()
    assert passed['status'] == 0 and passed['observed'] == 0x80
    dut.uio_in.value = 0
    await host.program([encode(EXPECT, 3, 2, 2), encode(HALT)])
    await host.start()
    page0 = await host.request(0x80)
    assert page0 & 0xffffffff == 2
    # Change the live witness before reading the remaining snapshot pages.
    await host.program([encode(EXPECT, 5, 4, 4), encode(HALT)])
    await host.start()
    page1 = await host.request(0x81)
    page2 = await host.request(0x82)
    assert (page1 >> 8) & 65535 == 3
    assert page2 == encode(EXPECT, 3, 2, 2)
    newest = await host.snapshot()
    assert newest['samples'] == 5 and newest['word'] == encode(EXPECT, 5, 4, 4)


@cocotb.test()
async def capture_overflow_readback_and_reset(dut):
    from tools.witness_isa import SAMPLE
    pins = Pins(dut)
    await pins.reset()
    host = WitnessHost(pins.transfer)
    await host.unlock()
    assert await host.request(0x83) == 0
    dut.uio_in.value = 0x80
    await host.program([encode(SAMPLE, 1, 7), encode(JMP, b=0)])
    await host.start()
    result = await host.snapshot(capture=True)
    assert result['status'] == 5 and result['pc'] == 0 and result['cycle'] == 64
    assert result['samples'] == 1 and result['word'] == encode(SAMPLE, 1, 7)
    assert result['capture_count'] == 32 and result['capture_data'] == 0xffffffff
    assert int(dut.uio_oe.value) == 0
    await host.program([encode(SAMPLE, 1, 0), encode(HALT)])
    await host.start()
    assert await host.request(0x83) == (32 << 32 | 0xffffffff)
    result = await host.snapshot(capture=True)
    assert result['status'] == 0 and result['capture_count'] == 1 and result['capture_data'] == 0
    await pins.reset()
    await host.unlock()
    assert await host.request(0x83) == 0
