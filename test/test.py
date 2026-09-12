"""Black-box pin checks; the same test runs against RTL and the gate netlist."""
import random
import cocotb
from cocotb.triggers import Timer

DIV = 434

async def tick(dut):
    dut.clk.value = 0
    await Timer(10, unit="ns")
    dut.clk.value = 1
    await Timer(10, unit="ns")
    assert int(dut.uio_oe.value) == 0
    assert int(dut.uio_out.value) == 0
    assert int(dut.uo_out.value) & 0xFE == 0
    return int(dut.uo_out.value) & 1

async def reset(dut):
    dut.rst_n.value = 0
    for _ in range(3):
        assert await tick(dut) == 1
    dut.rst_n.value = 1

@cocotb.test()
async def uart_pin_contract(dut):
    dut.clk.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    await reset(dut)
    rng = random.Random(20260912)
    for _ in range(4):
        # Exact start/data/stop levels, checked on every clock, LSB first.
        for expected in [0] + [(0x55 >> i) & 1 for i in range(8)] + [1]:
            for _ in range(DIV):
                dut.ui_in.value = rng.randrange(256)
                dut.uio_in.value = rng.randrange(256)
                assert await tick(dut) == expected
        assert await tick(dut) == 1  # one extra idle clock between frames
    # Abort in each bit position, then demand a fresh complete start bit.
    for bit in range(10):
        await reset(dut)
        for _ in range(bit * DIV + DIV // 2):
            await tick(dut)
        await reset(dut)
        for _ in range(DIV):
            assert await tick(dut) == 0
