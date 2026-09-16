"""Fixed-byte SPI controller firmware and an independent edge-driven target."""
from tools.witness_isa import DRIVE, EXPECT, HALT, SAMPLE, encode


def controller_program(tx, expected_rx, mode=0, half=8):
    if any(type(x) is not int or not 0 <= x <= 255 for x in (tx, expected_rx)):
        raise ValueError('bytes must be integers in 0..255')
    if mode not in range(4) or type(half) is not int or not 4 <= half <= 65535:
        raise ValueError('mode 0..3 and half period 4..65535 required')
    idle, phase = mode >> 1, mode & 1
    def drive(clock, bit, count, cs=0):
        return encode(DRIVE, count, clock | bit << 1 | cs << 2, 7)
    words = [drive(idle, tx >> 7, half, 1), drive(idle, tx >> 7, half)]
    for bit in range(7, -1, -1):
        data = (tx >> bit) & 1
        check = encode(EXPECT, 1, ((expected_rx >> bit) & 1) << 3, 8)
        if phase:
            words += [drive(1-idle, data, half), drive(idle, data, half-1), check]
        else:
            following = (tx >> max(0, bit-1)) & 1
            words += [drive(1-idle, data, half-1), check, drive(idle, following, half)]
    words += [drive(idle, 0, half, 1), encode(HALT)]
    return words


class Target:
    """Samples MOSI and shifts MISO from line edges, without reading firmware."""
    def __init__(self, response, mode):
        self.response, self.idle, self.phase = response, mode >> 1, mode & 1
        self.previous = 4 | self.idle
        self.miso = 0
        self.bits = []
        self.edges = []
        self.selected = False
        self.complete = False

    def observe(self, lines, cycle):
        old = self.previous
        self.previous = lines
        if lines & 4:
            if self.selected:
                self.complete = True
            self.selected = False
            return 0
        if old & 4:
            self.selected = True
            self.miso = (self.response >> 7) & 1 if not self.phase else 0
            return self.miso
        if (old ^ lines) & 1:
            leading = (lines & 1) != self.idle
            sample = leading != bool(self.phase)
            self.edges.append(dict(cycle=cycle, clock=lines & 1, sample=sample))
            if sample:
                self.bits.append((lines >> 1) & 1)
            elif len(self.bits) < 8:
                self.miso = (self.response >> (7-len(self.bits))) & 1
        return self.miso


def capture_program(tx, mode=0, half=8):
    """Same wire timing as the known-response program, but accept unknown MISO."""
    return [encode(SAMPLE, 1, 3) if word >> 36 == EXPECT else word
            for word in controller_program(tx, 0, mode, half)]
