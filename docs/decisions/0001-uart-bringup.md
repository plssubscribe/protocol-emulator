# ADR 0001: Establish UART pin bring-up before the programmable engine

Date: 2026-09-12. Status: accepted for milestone 1.

Use the official Tiny Tapeout CMOS5L Verilog branch, retaining its physical-flow
configuration and Apache-2.0 license. Request 8x4 tiles as directed by the competition.
The top name `tt_um_protocol_emulator` is provisional until a submission identity exists.

Use one 50 MHz clock, matching the inherited 20 ns timing constraint. This is a
target to verify through place and route, not a proven maximum operating frequency.
UART uses 8N1 with a 434-cycle integer divisor: 115207.37 baud, +0.0064% from 115200.
No derived clocks: counters run from the input clock. This keeps timing constraints simple.

Separate the reusable byte transmitter from the Tiny Tapeout wrapper. A transfer
is accepted on a rising edge when valid and ready are both high. Data is latched
then; requests while busy are not accepted. The sender must retain a request until
ready. Reset is synchronous active-low and aborts an in-flight byte on the next
clock edge. The receiver may see a broken frame during reset.

For initial observation, transmit constant 0x55 continuously on uo_out[0]. Return
to idle high for one additional clock between frames. Zero unused outputs and
hold all uio output enables low. Ignore ena following the template's selection
semantics; it is not an application pause input. No asynchronous external inputs
are consumed by this milestone.

Consequence: this is a diagnostic stepping stone, not the competition architecture.
The next engine must reproduce UART using programmed pin/timing instructions;
we will retain an independent wire-level oracle. Instruction set, host transport,
program memory technology, depth, buffering and electrical interfaces remain open.
Do not add fixed SPI/I2C peripherals as a substitute for programmability.
