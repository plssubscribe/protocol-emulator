# Programmed SPI evidence

Local result on 2026-09-13: PASS, 12 normal exchanges, four corrupted responses
and four exact replays (20 total). Eleven model tests also pass. Icarus 13.0 and
cocotb 2.0.1 simulated 13.44832 ms. See the
[evidence record](evidence/spi-2026-09-13.json) for hashes and witnesses.

The runnable command is `make spi-demo` after activating `.venv`. Firmware uses
28 existing instruction words and no new RTL. The emulated SPI bus is uio[0:3];
the host loader remains on its separate dedicated pins.

The public-pin regression covers modes 0, 1, 2 and 3 with TX/RX pairs A6/59,
00/FF and FF/00 at an eight-system-cycle half-period. Each passing transaction
must have eight correctly sampled MOSI bits, sixteen clock transitions, uniform
eight-cycle transition spacing, HALT completion and released outputs.

For each mode a target returns 49 instead of the expected 59. The fourth response
bit differs. The engine must stop with a one-sample timeout at PC 12 for CPHA=0
or PC 13 for CPHA=1, with the exact EXPECT instruction in the host-read witness.
The serialized words are reloaded and a fresh target must reproduce the full line
trace and witness. The generated artifact is `work/spi-witness.json`.

The target is a project-authored, edge-driven digital fixture. EXPECT checks the
stable MISO level near the end of the sampling half-period after synchronization;
it does not latch arbitrary data precisely at the SPI edge. This is a known-byte
response test, not a discovered third-party defect or a timing-fault experiment.
No analog delays or metastability model are included.

No RTL, PDK, reset, physical pins, 20 ns target or 8x4 allocation changed. No new
synthesis, mapped gate simulation, static timing, place-and-route, DRC, LVS or
hardware capture was run for this milestone. Earlier generic-netlist results do
not establish that this new SPI test passed on a netlist.
