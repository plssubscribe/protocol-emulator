"""Public-pin stretch experiment; all programs enter through the SPI host."""
import json
import os
from pathlib import Path

import cocotb
from cocotb.triggers import Timer
from test_host import Pins
from tools.witness_host import WitnessHost
from tools.i2c_lab import Controller, BusDecoder, target_program, SCL, SDA, high_widths, transitions


class I2CPins(Pins):
    def __init__(self, dut):
        super().__init__(dut)
        self.peer = None
        self.decoder = None
        self.trace = []

    async def cycles(self, count):
        for _ in range(count):
            self.d.clk.value = 0
            self.d.ui_in.value = self.controls
            await Timer(1, unit='ns')
            if int(self.d.rst_n.value):
                value, enable = int(self.d.uio_out.value), int(self.d.uio_oe.value)
            else:
                value, enable = 0, 0
            assert enable & ~3 == 0, 'I2C firmware drove an unrelated pin'
            assert value & enable == 0, 'I2C firmware attempted a push-pull high'
            controller_low = self.peer.pull_low if self.peer else 0
            bus = 3 & ~(enable | controller_low)
            self.d.uio_in.value = bus
            if self.peer:
                self.decoder.observe(bus)
                self.trace.append(dict(cycle=len(self.trace), bus=bus,
                                       target_low=enable, controller_low=controller_low))
            await Timer(9, unit='ns')
            self.d.clk.value = 1
            await Timer(10, unit='ns')
            assert int(self.d.uo_out.value) & 0xe0 == 0
            if self.peer:
                self.peer.advance(bus)

    async def experiment(self, host, width, faulty=False, low=12, high=12, rewrite=True):
        self.peer = None
        self.d.uio_in.value = 3
        if rewrite:
            await host.write(2, target_program(width)[2])
        await host.start()
        self.peer = Controller(low=low, high=high, ignore_stretch=faulty)
        self.decoder = BusDecoder()
        self.trace = []
        # Deadline is a bounded emulator timeout, not the I2C specification's limit.
        for _ in range(70000):
            await self.cycles(1)
            if self.peer.done and int(self.d.uo_out.value) & 8:
                break
        else:
            assert False, 'experiment failed to terminate'
        result = dict(stretch=width, faulty=faulty, low=low, high=high,
                      transfers=self.decoder.transfers, starts=self.decoder.starts,
                      peer_ack=self.peer.ack, trace=self.trace[:], high_widths=high_widths(self.trace))
        self.peer = None  # freeze the peer-relative trace before readback clocks
        result['witness'] = await host.snapshot()
        return result


def validate_good(result):
    assert result['witness']['status'] == 0, result['witness']
    assert result['witness']['done'] and result['peer_ack']
    assert result['starts'] == 1
    assert result['transfers'] == [dict(bits=[1, 0, 1, 0, 0, 0, 0, 0, 0],
                                      address_byte=0xa0, ack=True)], result['transfers']


@cocotb.test()
async def i2c_stretch_sweep_and_replay(dut):
    pins = I2CPins(dut)
    await pins.reset()
    host = WitnessHost(pins.transfer)
    await host.unlock()
    words = target_program(0)
    await host.program(words)
    results = []
    # Exhaustive bounded sweep, no monotonic-failure assumption.
    widths = range(49) if not os.environ.get('I2C_SMOKE') else [0, 19, 20, 24, 48]
    first_failure = None
    for width in widths:
        good = await pins.experiment(host, width)
        validate_good(good)
        faulty = await pins.experiment(host, width, faulty=True)
        if width == 0:
            validate_good(faulty)
        if faulty['witness']['status'] != 0:
            assert faulty['witness']['status'] == 1
            assert not (faulty['peer_ack'] and faulty['transfers'] == good['transfers'])
            if first_failure is None:
                first_failure = faulty
        results.append(dict(stretch=width, good_status=good['witness']['status'],
                            faulty_status=faulty['witness']['status']))
    assert first_failure is not None
    # Verify the same failure mechanism at Standard-mode nominal digital periods:
    # 260+240 system cycles = 10 us at the unchanged 50 MHz target.
    standard_good = await pins.experiment(host, 800, low=260, high=240)
    validate_good(standard_good)
    standard_fault = await pins.experiment(host, 800, faulty=True, low=260, high=240)
    assert standard_fault['witness']['status'] == 1
    assert standard_fault['transfers'][0]['bits'][0] == 0
    assert standard_good['transfers'][0]['bits'][0] == 1
    assert standard_fault['transfers'][0]['address_byte'] != 0xa0
    filename = 'i2c-witness-smoke.json' if os.environ.get('I2C_SMOKE') else 'i2c-witness.json'
    output = Path(__file__).resolve().parents[1] / 'work' / filename
    packet = dict(schema=1, scope='I2C address/ACK probe; authored controller with deliberate fault',
                  sweep=results, first_failure=first_failure,
                  words=[f'{word:010x}' for word in target_program(first_failure['stretch'])],
                  standard_mode={name: {**{k: v for k, v in result.items() if k != 'trace'},
                                 'transitions': transitions(result['trace'])}
                                 for name, result in [('good', standard_good), ('faulty', standard_fault)]})
    output.write_text(json.dumps(packet, indent=2)+'\n')
    saved = json.loads(output.read_text())
    await host.program([int(word, 16) for word in saved['words']])
    replay = await pins.experiment(host, saved['first_failure']['stretch'], faulty=True, rewrite=False)
    assert replay == saved['first_failure'], 'saved I2C failure did not exactly replay'
    packet['replay_matched'] = True
    output.write_text(json.dumps(packet, indent=2)+'\n')
    dut._log.info('First checked failure in sweep: stretch=%d, PC=%d, cycle=%d',
                  first_failure['stretch'], first_failure['witness']['pc'],
                  first_failure['witness']['cycle'])
