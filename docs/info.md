## How it works

Protocol Witness is a programmable timing engine with first-failure capture. After
reset it retains the M1 diagnostic: output 0 repeatedly transmits ASCII U in UART
8N1, 434 clocks per bit at a 50 MHz target, plus one idle clock between frames.
Until an explicit CRC-valid unlock packet, all other outputs/enables are zero.

After unlock, SPI host commands load 32 x 40-bit instruction words, start/abort
execution and read an atomic failure snapshot. The eight uio pins are the protocol
interface. DRIVE, EXPECT, WAIT, JMP and HALT have cycle-exact semantics described
in ADR 0004; ADR 0008 adds timed SAMPLE. EXPECT uses synchronized inputs and records a missed deadline before
releasing output enables. A host packet error is distinct from a protocol timeout.

| Pins | Function |
| --- | --- |
| ui[0], ui[1], ui[2] | SPI SCLK, MOSI, CS_N |
| uo[0] | Original UART diagnostic |
| uo[1] | SPI MISO |
| uo[2], uo[3], uo[4] | Running, done, sticky host error |
| uo[7:5], ui[7:3] | Unused (outputs zero) |
| uio[7:0] | Programmable protocol pins |

SPI mode 0 uses exactly 64 clocks per selected packet. Keep SCLK half-periods and
CS setup/hold/inactive intervals at least four system clocks. SPI input timing and
protocol input synchronization are defined in ADR 0005; no asynchronous bypass
exists. The host API is `tools/witness_host.py`, requiring an adapter transaction
callback. The full packet and reply format is in ADR 0005.

SAMPLE appends a selected synchronized input bit at the end of its duration. Up to
32 bits are retained per run. A 33rd sample stops with status 5 and preserves the
first 32. START/reset clear capture; termination and idle program writes retain it.
SNAPSHOT also freezes capture page 3: command 83 returns count in bits 37:32 and
data in bits 31:0, with top bits 39:38 zero. Use `snapshot(capture=True)` to read it.
The buffer is bounded run storage, not a continuously drained FIFO.

## How to test

Run `make test` from the repository with Icarus Verilog and the Python environment
active. Inspect `test/tb.fst` for diagnostic UART and host/program waveforms.
The public-pin tests load two pulse programs, read failure records, generate a
programmed UART frame on uio[0], and reject malformed/busy host commands.

For future board bring-up, select the design, supply a 50 MHz clock and hold rst_n
low for at least three rising edges before releasing it, with host CS_N high and
SCLK low. Connect output 0 to a
logic analyzer or a voltage-compatible USB UART adapter's RX input, with common
ground. Decode as 115200 baud, 8 data bits, no parity, one stop bit; expect repeated U.
A bit should measure about 8.68 microseconds. No hardware capture has been performed.

## External hardware

For physical testing: a compatible Tiny Tapeout dev board or FPGA mapping, and
logic analyzer or UART adapter. Confirm the actual board's I/O voltage before
connection; use logic-level UART, not an RS-232 voltage interface.
