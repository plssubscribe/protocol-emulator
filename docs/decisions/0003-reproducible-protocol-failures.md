# ADR 0003: Focus on reproducible protocol failures

Date: 2026-09-12. Status: accepted product direction; timing model is experimental.

## Decision

Build a programmable protocol emulator whose distinguishing workflow is to vary
protocol timing, detect a violated response expectation, and export a reproducible
failure case. Working name: Protocol Witness. This is a product hypothesis, not a
claim of invention or a prediction of competition results.

The competition explicitly values debugging/reverse engineering, unique functionality
and verification methodology. A useful submission should demonstrate a concrete bug
and its reproduction, alongside ordinary UART/SPI/I2C interoperability.

Keep timing and bounded observation on chip; put experiment generation, exhaustive
finite sweeps, case reduction and readable explanations on the host. Prioritize a
first-failure register over a large on-chip trace RAM. A host simulation trace is
not evidence that the future chip can capture every cycle. Target a small shared
engine, not independent fixed protocol blocks. Memory depth, encoding, transport,
register widths and physical feasibility remain open until synthesis evidence.

## First runnable experiment

`make lab` runs a software-only generic DRIVE/EXPECT sequence against two synthetic
request/acknowledge peers. The correct peer accepts low request pulses of any
positive width; an intentionally faulty peer requires four cycles. Sweep widths
1 through 8, report all failing widths, select the smallest failing width in that
finite set, serialize its program, fixture and trace, then reproduce the result.
This is neither I2C nor a real device discovery, and case reduction is only across
this single swept parameter. No arbitrary-program minimizer exists yet.

`tools/protocol_lab.py` specifies candidate behavior:

- Each cycle applies DRIVE output state before sampling already synchronized inputs.
- DRIVE holds value and enable for 1..65535 cycles.
- EXPECT holds outputs and compares masked inputs for 1..65535 samples. A match
  on the first or last sample succeeds; timeout occurs after the last mismatch.
- The next instruction starts on the following cycle; there are no hidden fetch
  cycles in this model. Failure records PC, cycle, mask, expected/observed pins and
  sample count, stops execution and releases enables at the next boundary.
- Program completion also releases enables. Host execution-budget exhaustion is
  distinct from a protocol timeout. The model uses unbounded Python timestamps.

This does not freeze a binary ISA, reset behavior, asynchronous input latency or
external pin assignment. ADR 0001 continues to govern the existing top-level RTL.
A future RTL ADR must specify synchronization, timestamp wrap, loading/arming,
fetch latency and reset/failure output behavior before integration.

## Alternatives and scope

A broad list of accelerated protocols risks shallow verification. A large logic
analyzer risks spending area on trace storage. Autonomous on-chip fuzzing and
reduction make reproducibility and area harder; initially the host does both.
Keep UART, SPI and I2C as mandatory baseline demonstrations. Defer USB/Ethernet
until baseline correctness and area/timing headroom are established.

Prior art includes RP2040 PIO pin waits and programmable timing, and ChipWhisperer
triggered timing perturbations. No novelty claim follows from this limited review.
Our proposed distinction is the integrated protocol-level failure workflow and
its verification evidence in the competition's small ASIC footprint.

## Evidence required to keep this direction

1. Two host-loaded programs produce different cycle-checked waveforms in RTL.
2. Bounded EXPECT passes last-cycle tests and captures the first failure exactly;
   RTL agrees with a model and independent wire-level protocol oracles.
3. Demonstrate an I2C clock-stretch handling bug and a UART or SPI timing bug in
   independently implemented peers, preserving a normal passing baseline.
4. Quantify incremental cells/area and timing for EXPECT/failure capture; reduce
   diagnostic scope if it threatens the basic programmable engine.
5. Report mutation tests (e.g. deadline off-by-one, wrong mask, wrong output enable)
   and which assertions detect them. Formal checks are planned, not completed.
6. Replay on FPGA/real hardware when available, acknowledging synchronization
   uncertainty: exact digital stimulus does not guarantee identical analog behavior.

## Sources checked 2026-09-12

- https://blog.janestreet.com/protocol-emulator-asic-competition/
- https://www.raspberrypi.com/documentation/pico-sdk/hardware.html
- https://chipwhisperer.readthedocs.io/en/latest/scope-api.html

No RTL or physical configuration changes are part of this decision. No synthesis,
place-and-route, timing, DRC, LVS, gate simulation or hardware checks ran for this
software experiment. The existing 8x4 floorplan blocker remains unresolved.
