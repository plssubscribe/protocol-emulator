"""Assembler and instruction-level oracle for ADRs 0004/0008 (no RTL dependencies)."""
HALT, DRIVE, EXPECT, WAIT, JMP, SAMPLE = range(6)


def encode(opcode, cycles=0, a=0, b=0):
    fields = ((opcode, 15), (cycles, 65535), (a, 255), (b, 255))
    if any(type(v) is not int or not 0 <= v <= limit for v, limit in fields):
        raise ValueError('instruction fields out of range')
    word = opcode << 36 | cycles << 16 | a << 8 | b
    if decode(word) is None:
        raise ValueError('illegal instruction')
    return word


def decode(word):
    if type(word) is not int or not 0 <= word < 1 << 40 or (word >> 32) & 15:
        return None
    op, count, a, b = word >> 36, (word >> 16) & 65535, (word >> 8) & 255, word & 255
    if op == HALT and (count, a, b) == (0, 0, 0):
        return op, count, a, b
    if op == DRIVE and count > 0:
        return op, count, a, b
    if op == EXPECT and count > 0 and b and (a & b) == a:
        return op, count, a, b
    if op == WAIT and count > 0 and a == b == 0:
        return op, count, a, b
    if op == JMP and count == a == 0 and b < 32:
        return op, count, a, b
    if op == SAMPLE and count > 0 and a < 8 and b == 0:
        return op, count, a, b
    return None


def execute(words, peer=lambda c, v, e: 0, budget=10000):
    """Expand whole instructions into sampled cycles; None denotes an unloaded slot."""
    if len(words) > 32:
        raise ValueError('program exceeds 32 words')
    memory = list(words) + [None] * (32 - len(words))
    trace = []
    pc, value, enable = 0, 0, 0
    capture_data, capture_count = 0, 0

    def sample(v, e):
        observed = peer(len(trace), v, e)
        trace.append(dict(cycle=len(trace), value=v, enable=e, observed=observed))
        return observed

    def finish(status, word, observed, samples):
        return dict(trace=trace, status=status, pc=pc, cycle=(len(trace)-1) & 0xffffffff,
                    word=word or 0, observed=observed, samples=samples,
                    time_wrapped=int(len(trace) >= 1 << 32), final_value=value,
                    capture_data=capture_data, capture_count=capture_count)

    while len(trace) < budget:
        word = memory[pc]
        decoded = decode(word)
        if word is None or decoded is None:
            observed = sample(value, 0)
            return finish(3 if word is None else 2, word, observed, 0)
        op, count, a, b = decoded
        if op == HALT:
            observed = sample(value, 0)
            return finish(0, word, observed, 0)
        if op == JMP:
            sample(value, enable)
            pc = b
            continue
        if op == DRIVE:
            value, enable = a, b
        for consumed in range(1, count + 1):
            if len(trace) >= budget:
                raise TimeoutError('oracle budget exhausted; not a protocol timeout')
            observed = sample(value, enable)
            if op == EXPECT and (observed & b) == a:
                break
        else:
            if op == EXPECT:
                return finish(1, word, observed, count)
        if op == SAMPLE:
            if capture_count == 32:
                return finish(5, word, observed, count)
            capture_data = ((capture_data << 1) | ((observed >> a) & 1)) & 0xffffffff
            capture_count += 1
        pc = (pc + 1) % 32
    raise TimeoutError('oracle budget exhausted; not a protocol timeout')


def uart_program(byte, divisor=434):
    """One 8N1 frame, then a released HALT cycle. No dedicated UART peripheral."""
    if not 0 <= byte <= 255:
        raise ValueError('byte out of range')
    levels = [0] + [(byte >> bit) & 1 for bit in range(8)] + [1]
    return [encode(DRIVE, divisor, level, 1) for level in levels] + [encode(HALT)]
