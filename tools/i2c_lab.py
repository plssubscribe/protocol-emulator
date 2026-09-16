"""I2C stretch program and independent digital controller/decoder fixtures.

SCL is protocol bit 0, SDA bit 1. Fixtures use open-drain masks, never drive high.
The controller is authored for this project, not an external IP core.
"""
from tools.witness_isa import DRIVE, EXPECT, HALT, encode

SCL, SDA = 1, 2


def target_program(stretch, address_byte=0xa0, deadline=4096):
    if type(stretch) is not int or not 0 <= stretch <= 65535:
        raise ValueError('stretch must be 0..65535 cycles')
    if type(address_byte) is not int or not 0 <= address_byte <= 255:
        raise ValueError('address byte must be a byte')
    words = [encode(EXPECT, deadline, SCL, SCL | SDA),  # START: SDA low, SCL high
             encode(EXPECT, deadline, 0, SCL),
             encode(DRIVE, max(1, stretch), 0, SCL if stretch else 0),
             encode(DRIVE, 1, 0, 0)]
    for bit in range(7, -1, -1):
        words += [encode(EXPECT, deadline, SCL, SCL),
                  encode(EXPECT, 1, SDA if address_byte & (1 << bit) else 0, SDA),
                  encode(EXPECT, deadline, 0, SCL)]
    words += [encode(DRIVE, 1, 0, SDA),  # ACK during the ninth low period
              encode(EXPECT, deadline, SCL, SCL),
              encode(EXPECT, deadline, 0, SCL), encode(HALT)]
    assert len(words) == 32
    return words


class Controller:
    """One address probe: START, address+R/W, ACK sample, STOP.

    The fault ignores physical SCL when timing the high period. No ISA knowledge.
    low/high count bus-model cycles, not emulator instructions.
    """
    def __init__(self, address_byte=0xa0, low=12, high=12, ignore_stretch=False):
        if low < 8 or high < 8:
            raise ValueError('fixture periods must allow the input synchronizers')
        self.byte, self.low, self.high = address_byte, low, high
        self.ignore_stretch = ignore_stretch
        self.phase, self.age, self.bit = 'START', 0, 0
        self.pull_low = SDA
        self.done = False
        self.ack = None

    def begin_low(self):
        self.phase, self.age = 'LOW', 0
        data_low = self.bit < 8 and not (self.byte & (1 << (7-self.bit)))
        self.pull_low = SCL | (SDA if data_low else 0)

    def advance(self, bus):
        if self.done:
            return
        if self.phase == 'START':
            self.age += 1
            if self.age == self.high:
                self.begin_low()
        elif self.phase == 'LOW':
            self.age += 1
            if self.age == self.low:
                self.pull_low &= ~SCL
                self.phase = 'WAIT_HIGH'
        elif self.phase == 'WAIT_HIGH':
            if self.ignore_stretch or bus & SCL:
                if self.bit == 8:
                    self.ack = not bool(bus & SDA)
                self.phase, self.age = 'HIGH', 1
        elif self.phase == 'HIGH':
            self.age += 1
            if self.age == self.high:
                if self.bit == 8:
                    self.phase, self.age, self.pull_low = 'STOP_LOW', 0, SCL | SDA
                else:
                    self.bit += 1
                    self.begin_low()
        elif self.phase == 'STOP_LOW':
            self.age += 1
            if self.age == self.low:
                self.pull_low = SDA
                self.phase = 'STOP_WAIT'
        elif self.phase == 'STOP_WAIT':
            if bus & SCL:
                self.phase, self.age = 'STOP_HIGH', 1
        elif self.phase == 'STOP_HIGH':
            self.age += 1
            if self.age == self.high:
                self.pull_low = 0
                self.phase, self.age = 'STOP_HOLD', 0
        elif self.phase == 'STOP_HOLD':
            self.age += 1
            if self.age == self.high:
                self.done = True


class BusDecoder:
    """Decode only resolved line transitions, without reading controller/core state."""
    def __init__(self):
        self.previous = SCL | SDA
        self.active = False
        self.bits = []
        self.transfers = []
        self.starts = 0
        self.pending = None

    def observe(self, bus):
        scl, sda = bool(bus & SCL), bool(bus & SDA)
        old_scl, old_sda = bool(self.previous & SCL), bool(self.previous & SDA)
        if scl and old_scl and old_sda and not sda:
            self.active = True
            self.bits = []
            self.pending = None
            self.starts += 1
        elif scl and old_scl and not old_sda and sda and self.active:
            bits = self.bits[:]
            byte = sum(bit << (7-i) for i, bit in enumerate(bits[:8])) if len(bits) >= 8 else None
            self.transfers.append(dict(bits=bits, address_byte=byte,
                                       ack=(bits[8] == 0) if len(bits) >= 9 else None))
            self.active = False
        elif scl and not old_scl and self.active:
            self.pending = int(sda)
        elif not scl and old_scl and self.active and self.pending is not None:
            # Commit a complete clock pulse; STOP's final incomplete high phase
            # is setup, not an additional data/ACK clock in this probe fixture.
            self.bits.append(self.pending)
            self.pending = None
        self.previous = bus


def high_widths(trace):
    widths = []
    start = None
    for previous, current in zip(trace, trace[1:]):
        if not previous['bus'] & SCL and current['bus'] & SCL:
            start = current['cycle']
        elif previous['bus'] & SCL and not current['bus'] & SCL and start is not None:
            widths.append(current['cycle'] - start)
            start = None
    return widths


def transitions(trace):
    return [row for i, row in enumerate(trace) if i == 0 or any(
        row[key] != trace[i-1][key] for key in ('bus', 'target_low', 'controller_low'))]
