# Project state and milestones

Updated: 2026-09-12.

## M1 — UART pin bring-up

Implemented: official CMOS5L project; 8x4 allocation; repeat-0x55 UART TX on output 0;
reusable transmitter; unit and pin tests; CI wiring; ADR 0001.
Verification: local `make test` PASS on 2026-09-12 with Icarus 13.0 and cocotb
2.0.1 in the Python 3.11 environment. All 256 bytes passed at divisors 1, 2, 3,
and 434 (1,024 unit cases); the top-level pin regression passed over 869.34 us
of simulated time. Waveform: `test/tb.fst`. M1 simulation acceptance is complete.
GDS, gate simulation and physical pin capture have not been run. No FPGA or board availability assumed.

Done criteria: automated RTL checks pass and the expected waveform is available.
Hardware follow-up: capture 115200 8N1 U characters at the output pin on an FPGA
or fabricated device. Track that evidence separately from simulated success.

## M2 — First programmable waveform

Define a minimal cycle-exact SET / WAIT / JMP instruction contract in ADR 0002.
Build a small instruction engine and a matching Python reference model. Initially
use a short boot program to reproduce UART 0x55 at exactly documented timing.
Then provide a host-loadable instruction store before calling the engine programmable
for competition purposes. Select the loading interface and memory depth with area evidence.
Acceptance: two different pin waveforms from different loaded programs without RTL changes;
cycle-by-cycle agreement with the reference model, plus first area/timing reports.

## M3 — Data and inputs

Add conditional pin reads and bounded host TX/RX queues based on protocol needs.
Define synchronization latency, empty/full behavior and program update semantics.
Acceptance: programmable UART transmit and receive with boundary and error tests.

## M4 — Protocol flexibility

Demonstrate SPI and I2C with programs on the same engine, including I2C open-drain
control and clock stretching. Use these to revise the ISA only with documented reasons.

## M5 — Submission candidate

Freeze ISA and interfaces; publish examples, programming tools and measured limits.
Pass current Tiny Tapeout physical checks, gate simulation and timing for 8x4 CMOS5L.
Fill author/identity metadata, recheck competition rules and submit by January 18, 2027.
Stretch protocols follow evidence of area and timing headroom.

## Next session

Inspect the UART waveform, then specify exact SET/WAIT/JMP execution timing.
Keep M1 as a regression baseline while developing the engine. Open decisions:
host connection, clock source available on the test board, program memory size/type,
unique submission name, FPGA availability. None blocks local simulation.
