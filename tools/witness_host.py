"""ADR 0005 transport codec and serialized async host API.

Supply an async transfer(bytes)->bytes function implementing one 64-clock SPI
transaction. This module has no adapter-specific dependencies.
"""


def crc8(data):
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ (0x07 if crc & 0x80 else 0)) & 255
    return crc


def packet(command, payload=0):
    if type(command) is not int or not 0 <= command <= 255:
        raise ValueError('command must be a byte')
    if type(payload) is not int or not 0 <= payload < 1 << 40:
        raise ValueError('payload must fit 40 bits')
    body = bytes([0xa7, command]) + payload.to_bytes(5, 'big')
    return body + bytes([crc8(body)])


def decode_reply(raw):
    if len(raw) != 8 or raw[0] != 0x5a or crc8(raw[:7]) != raw[7]:
        raise ValueError('invalid reply length, magic or CRC')
    return raw[1], int.from_bytes(raw[2:7], 'big')


class HostError(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(f'Host command rejected, code {code}')


class WitnessHost:
    """One command at a time; the second transfer retrieves the pipelined reply."""
    def __init__(self, transfer):
        self.transfer = transfer

    async def request(self, command, payload=0):
        await self.transfer(packet(command, payload))
        code, data = decode_reply(await self.transfer(packet(0)))
        if code:
            raise HostError(code)
        return data

    async def unlock(self):
        revision = await self.request(1, int.from_bytes(b'WITNS', 'big'))
        if revision != 1:
            raise ValueError('unsupported host transport revision')

    async def write(self, address, word):
        if type(address) is not int or not 0 <= address < 32:
            raise ValueError('instruction address must be 0..31')
        await self.request(0x20 | address, word)

    async def program(self, words):
        if not 1 <= len(words) <= 32:
            raise ValueError('program must contain 1..32 words')
        for address, word in enumerate(words):
            await self.write(address, word)

    async def start(self):
        await self.request(0x40)

    async def abort(self):
        await self.request(0x60)

    async def snapshot(self, capture=False):
        page0 = await self.request(0x80)
        page1 = await self.request(0x81)
        page2 = await self.request(0x82)
        flags = page0 >> 32
        result = dict(unlocked=bool(flags & 128), host_error=bool(flags & 64),
                    time_wrapped=bool(flags & 32), running=bool(flags & 16),
                    done=bool(flags & 8), status=flags & 7, cycle=page0 & 0xffffffff,
                    pc=page1 >> 32, observed=(page1 >> 24) & 255,
                    samples=(page1 >> 8) & 65535, word=page2)

        if capture:
            page3 = await self.request(0x83)
            result.update(capture_count=page3 >> 32, capture_data=page3 & 0xffffffff)
        return result
