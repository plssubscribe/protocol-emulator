## How it works

Milestone 1 of a programmable protocol emulator. After reset, output 0 repeatedly
transmits ASCII U (0x55) in UART 8N1 format. At a 50 MHz input clock each bit is
434 clock cycles (115207.37 baud). Data is least-significant bit first. The line
idles high, with one extra clock of idle after each stop bit. Other outputs are zero;
all bidirectional pins have their output enables disabled.

## How to test

Run `make test` from the repository with Icarus Verilog and the Python environment
active. Inspect `test/tb.fst` for start-low, eight alternating data bits and stop-high.

For future board bring-up, select the design, supply a 50 MHz clock and hold rst_n
low for at least three rising edges before releasing it. Connect output 0 to a
logic analyzer or a voltage-compatible USB UART adapter's RX input, with common
ground. Decode as 115200 baud, 8 data bits, no parity, one stop bit; expect repeated U.
A bit should measure about 8.68 microseconds. No hardware capture has been performed.

## External hardware

For physical testing: a compatible Tiny Tapeout dev board or FPGA mapping, and
logic analyzer or UART adapter. Confirm the actual board's I/O voltage before
connection; use logic-level UART, not an RS-232 voltage interface.
