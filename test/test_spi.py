"""Emulated SPI on uio, separate from the host SPI transport."""
import json
from pathlib import Path
import cocotb
from cocotb.triggers import Timer
from test_host import Pins
from tools.spi_lab import Target, controller_program
from tools.witness_host import WitnessHost


class SPIPins(Pins):
    def __init__(self, dut):
        super().__init__(dut)
        self.peer = None
        self.trace = []
        self.tick = 0

    async def cycles(self, count):
        for _ in range(count):
            self.d.clk.value = 0
            self.d.ui_in.value = self.controls
            await Timer(1, unit='ns')
            if int(self.d.rst_n.value):
                value, enable = int(self.d.uio_out.value), int(self.d.uio_oe.value)
            else:
                value = enable = 0
            assert enable & ~7 == 0
            idle = self.peer.idle if self.peer else 0
            lines = (value & enable) | ((4 | idle) & ~enable)
            miso = self.peer.observe(lines, self.tick) if self.peer else 0
            self.d.uio_in.value = lines | miso << 3
            if self.peer and (self.peer.selected or (self.trace and not self.peer.complete)):
                self.trace.append(dict(cycle=self.tick, lines=lines, miso=miso, enable=enable))
            await Timer(9, unit='ns')
            self.d.clk.value = 1
            await Timer(10, unit='ns')
            assert int(self.d.uo_out.value) & 0xe0 == 0
            self.tick += 1


@cocotb.test()
async def spi_four_modes_and_replay(dut):
    pins = SPIPins(dut)
    await pins.reset()
    host = WitnessHost(pins.transfer)
    await host.unlock()
    records = []
    async def run(words, response, mode):
        pins.peer = None
        await host.program(words)
        pins.peer = Target(response, mode)
        pins.trace = []
        pins.tick = 0
        await host.start()
        await pins.cycles(32)
        witness = await host.snapshot()
        assert witness['done'] and not witness['running'] and not witness['host_error']
        assert int(dut.uio_oe.value) == 0
        return dict(mode=mode, response=response, witness=witness,
                    bits=pins.peer.bits, edges=pins.peer.edges, trace=pins.trace)
    for mode in range(4):
        for tx, rx in ((0xa6, 0x59), (0x00, 0xff), (0xff, 0x00)):
            words = controller_program(tx, rx, mode)
            good = await run(words, rx, mode)
            assert good['witness']['status'] == 0, good
            assert good['bits'] == [(tx >> bit) & 1 for bit in range(7, -1, -1)]
            assert len(good['edges']) == 16
            assert all(b['cycle']-a['cycle'] == 8 for a,b in zip(good['edges'], good['edges'][1:]))
            records.append({k:v for k,v in good.items() if k != 'trace'})
        words = controller_program(0xa6, 0x59, mode)
        bad = await run(words, 0x59 ^ 0x10, mode)
        assert bad['witness']['status'] == 1
        assert bad['witness']['pc'] == 2 + 3*3 + (2 if mode & 1 else 1)
        assert bad['witness']['samples'] == 1
        assert bad['witness']['word'] == words[bad['witness']['pc']]
        saved = json.loads(json.dumps(dict(words=words, result=bad)))
        assert await run(saved['words'], saved['result']['response'], mode) == saved['result']
        records.append(dict(failure=saved, replay_matched=True))
    path = Path(__file__).resolve().parents[1] / 'work/spi-witness.json'
    path.write_text(json.dumps(dict(scope='public-pin digital simulation', cases=records), indent=2)+'\n')


@cocotb.test()
async def spi_unknown_response_capture(dut):
    from tools.spi_lab import capture_program
    pins = SPIPins(dut)
    await pins.reset()
    host = WitnessHost(pins.transfer)
    await host.unlock()
    records = []
    for mode in range(4):
        # No response value is given to the firmware compiler. Reuse the loaded
        # words for different target bytes to expose stale/constant capture bugs.
        pins.peer = None
        words = capture_program(0xa6, mode, half=4)
        await host.program(words)
        for response in (0x96, 0x00, 0xff):
            pins.peer = Target(response, mode)
            pins.trace = []
            pins.tick = 0
            await host.start()
            record = await host.snapshot(capture=True)
            assert record['done'] and record['status'] == 0
            assert record['capture_count'] == 8 and record['capture_data'] == response, record
            assert pins.peer.bits == [1,0,1,0,0,1,1,0]
            assert len(pins.peer.edges) == 16
            assert all(b['cycle']-a['cycle'] == 4 for a,b in zip(pins.peer.edges,pins.peer.edges[1:]))
            records.append(dict(mode=mode,response=response,witness=record))
        # Snapshot page must survive a new run with a different input response.
        frozen = await host.request(0x83)
        pins.peer = Target(0x35, mode)
        await host.start()
        assert await host.request(0x83) == frozen
        latest = await host.snapshot(capture=True)
        assert latest['capture_data'] == 0x35 and latest['capture_count'] == 8
    path = Path(__file__).resolve().parents[1] / 'work/spi-capture.json'
    path.write_text(json.dumps(dict(scope='public-pin digital simulation',cases=records),indent=2)+'\n')
