# UART verification

From the repository root, activate `.venv` and run `make test`.
`make unit` uses Icarus alone; `make integration` also needs cocotb.
The pin-level test writes `test/tb.fst` and `test/results.xml`.
See `../docs/verification.md` for coverage and remaining physical checks.

For the inherited gate simulation workflow, the GDS action supplies
`gate_level_netlist.v` and the CMOS5L PDK; it then runs `make GATES=yes` here.

## Standalone programmable core

`make engine` from the root runs `engine/test_engine.py`. `make mutations` compiles
isolated defective copies and checks that selected assertions fail. The ordinary
`make test` includes the software model, UART baseline and programmable-core tests.

Optional `make synth-check` requires `synthesis-requirements.txt`. It synthesizes
the core with Yosys and reruns the same public-port suite on a generic netlist.
This is separate from the inherited Tiny Tapeout PDK gate simulation above.

## Integrated public-pin host

`test_host.py` uses `tools/witness_host.py` with a simulated SPI pin driver. The
ordinary `make integration` runs it alongside the original UART pin test.
`make host-mutations` checks deliberate host protection defects.
`make synth-top-check` repeats the full public-pin suite on the integrated generic
netlist, separately from the standalone-core and PDK gate simulations.

## I2C demonstration

`make i2c-demo` runs the full 0..48 hold sweep against correct/faulty address-probe
controllers, nominal-100-kHz cases and saved-file replay. `make test` includes it.
`make i2c-netlist` reuses a current integrated generic netlist for the documented
smoke subset. `I2C_SMOKE=1` selects that subset explicitly; it is not the full sweep.
Artifacts: `work/i2c-witness.json` and `work/i2c-witness-smoke.json`.

## Emulated SPI

`make spi-demo` from the repository root runs `test_spi.py`: 12 passing exchanges
(three byte pairs in four clock modes), four corrupted responses, and four exact
replays from serialized words. Checks use public pins and a separate edge-driven
SPI target. `work/spi-witness.json` retains line traces and host-read failures.
The eight-cycle half-period leaves time for synchronized response checking.
This is known-response verification, not general RX storage or physical SPI timing
signoff. See ADR 0007 for firmware assignment and scope.


## Bounded capture

`make capture-demo` runs public-pin unknown SPI response reception and 32-bit
buffer overflow/readback/reset checks. Each clock mode reuses a loaded program
against 96, 00, FF and 35 responses; the last response also tests snapshot stability.
The core suite adds final-cycle sampling across all eight pins, full-buffer fault,
restart clearing, abort/reset precedence and illegal SAMPLE words. Two targeted
mutations select the wrong pin or overwrite a full buffer and must be caught.
