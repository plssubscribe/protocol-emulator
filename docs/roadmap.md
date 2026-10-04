# Project state and milestones

Updated: 2026-10-04.

## M1 — UART pin bring-up

Implemented: official CMOS5L project; 8x4 allocation; repeat-0x55 UART TX on output 0;
reusable transmitter; unit and pin tests; CI wiring; ADR 0001.
Verification: local `make test` PASS on 2026-09-12 with Icarus 13.0 and cocotb
2.0.1 in the Python 3.11 environment. All 256 bytes passed at divisors 1, 2, 3,
and 434 (1,024 unit cases); the top-level pin regression passed over 869.34 us
of simulated time. Waveform: `test/tb.fst`. M1 simulation acceptance is complete.
GitHub RTL CI passed. GDS workflow was attempted but stopped before synthesis:
the inherited CMOS5L support package rejects 8x4 and lacks its floorplan. Author
metadata has been filled in. See [physical-build evidence](physical-build.md).
The separate 8x2 preview now passes gate simulation and physical checks listed
below; these have not passed for 8x4. Physical pin capture has not run.
No FPGA or board availability assumed.

Done criteria: automated RTL checks pass and the expected waveform is available.
Hardware follow-up: capture 115200 8N1 U characters at the output pin on an FPGA
or fabricated device. Track that evidence separately from simulated success.

## M1.5 — Reproducible-failure software experiment

Implemented 2026-09-12: ADR 0003 selects protocol failure reproduction as the entry
focus. `make lab` sweeps a synthetic request/acknowledge peer, saves the smallest
failing pulse width within 1..8, and replays its full software trace. Six model
checks pass, including inclusive deadline and first-failure output release.
No new RTL, physical checks or actual device captures are included in this milestone.
The generic model is a proposal; binary ISA and input synchronization remain open.

## M2 — First programmable waveform

Implemented standalone RTL, 2026-09-12: ADR 0004 defines a 32 x 40-bit loadable
instruction store with DRIVE / EXPECT / WAIT / JMP / HALT. Registered output value
and enables update without fetch bubbles; the active instruction is latched to
avoid a second memory read path. Two loaded waveforms and all 256 programmed UART
bytes pass; a 0x55 frame uses the production divisor 434. The M1 top is unchanged.

`make test` passes six model checks, the original 1,024 UART unit cases and pin
regression, and six core test groups. The core suite includes 160 seeded randomized
programs, 21 response-deadline cases, loader races, reset/abort, maximum duration,
invalid encodings/slots, PC wrap and registered outputs. The same six core groups
pass on the generic synthesized netlist (`make synth-check`).

Generic synthesis: 5,151 Boolean/sequential cells, including 1,528 flip-flops;
1,280 flip-flops are instruction storage. This is neither CMOS5L mapped area nor a
timing result. See [the evidence record](witness-evidence.md).

M2 logical acceptance is now complete at the public pins: ADR 0005 integrates an
SPI loader and two different loaded waveforms in the Tiny Tapeout wrapper. The
original repeating UART remains intact. Physical area/timing acceptance remains
open, and program depth is provisional pending CMOS5L mapping.

## M2.5 — Bounded observation and failure witness

Implemented in the standalone core: inclusive EXPECT deadline, first terminal
record, safe release, persistent program/restart, invalid-program detection, and
explicit abort. The software toy sweep now runs through RTL. The test serializes
a failure, reads it back, reloads its words, and matches every replayed cycle.
`make mutations` confirms four selected broken implementations are detected by
assertions. This is targeted mutation evidence, not complete fault coverage.
`make formal` checks six safety properties to 12 steps with a separate reachable
timeout check; it is not an unbounded functional proof.

Implemented 2026-09-13: CRC-framed SPI loading, explicit unlock, synchronized
protocol inputs, atomic witness pages and host-side readback API. Four public-pin
test groups (including the original UART) pass both RTL and generic netlist
simulation. Four additional host mutations are detected. Integrated generic
synthesis has 6,769 cells, including 1,888 flip-flops; these are not PDK area/timing.
See [integrated evidence](integrated-witness-evidence.md).

Resolved-bus address-probe coverage is now implemented below; full protocol
transactions and real hardware replay remain. The 32-bit timestamp
wrap flag has not been exercised across a full 2^32-cycle simulation. The I2C controller is a project-authored fault fixture, not third-party hardware.

## M3 — Data and inputs

Implemented 2026-09-13: ADR 0008 adds timed SAMPLE, a 32-bit bounded run buffer,
explicit overflow status 5, and atomic host snapshot page 3. The same SPI firmware
can receive unknown bytes in all four clock modes. See [capture evidence](capture-evidence.md).

Still open: conditional pin reads and bounded host TX/RX queues based on protocol needs.
Define synchronization latency, empty/full behavior and program update semantics.
Acceptance: programmable UART transmit and receive with boundary and error tests.
Demonstrate and replay a timing failure against an independently implemented peer.

## M4 — Protocol flexibility

Demonstrate SPI and I2C with programs on the same engine, including I2C open-drain
control and clock stretching. Use these to revise the ISA only with documented reasons.
Flagship demo: sweep clock stretching against a faulty controller model, identify
a failure boundary, and replay the captured program; also show a correct controller
passing. This requires a real resolved-bus protocol model, not the M1.5 toy peer.

### I2C address-probe milestone — implemented 2026-09-13

ADR 0006 adds a 32-word target program and resolved open-drain bus experiment,
using the existing SPI loader and witness readback. No RTL changes. The controller
and line decoder are separate from the instruction interpreter. Correct peers pass
all durations 0..48; faulty peers pass 0..19 and fail 20..48 in the accelerated
12/12-cycle fixture. The first failing hold leaves a one-cycle high pulse. At
nominal 100 kHz (260/240 cycles), an 800-cycle hold causes the faulty controller to
lose the first address bit; the correct controller decodes A0 and receives ACK.
The saved failure replays exactly. See [evidence](i2c-stretch-evidence.md).

This fills all 32 instruction slots. The result is an address/RW-byte check and ACK,
not a complete I2C stack. Next protocol work must add useful data handling and
reduce firmware footprint based on measured program needs. Preserve the current
ISA behavior when extending it.

### SPI byte milestone — implemented 2026-09-13

ADR 0007 adds a 28-word controller program for all four clock modes, a separate
edge-driven target fixture, and public-pin response-corruption replay. The program
uses the existing engine, distinct from the host loader. This is fixed-byte TX and
known-response checking. ADR 0008 extends it to unknown-byte capture; multi-byte
traffic remains open.
Verification results are recorded in `spi-evidence.md`.

### CMOS5L mapping checkpoint — 2026-09-14

Current integrated RTL maps to the pinned typical 1.20 V library: 8,463 standard
cells, 163,546.803 µm² summed cell area. No excluded or generic cells remain.
This is pre-placement library mapping, without a timing constraint applied by
that command. Required 8x4 size/DEF support is still absent at current upstream
revisions. See [mapping evidence](cmos5l-mapping-evidence.md).

### Organizer-approved 6x4 build — 2026-09-16

ADR 0009 supersedes the original 8x4 requirement: both the organizer response and
updated public rules specify 6x4 now. Canonical metadata uses the supported CMOS5L
6x4 floorplan. The full integrated capture design passed GDS, all nine prechecks
and all eight gate-level functional test groups in run 35086370645. Artifact review
on 2026-10-04 confirms 25.4554% core utilization, +8.846 ns setup and +0.130 ns
hold slack at the unchanged 20 ns target; routed/Magic DRC, LVS and antenna counts
are zero. **Four slow-corner slew and 131 clock-tree leaf fanout violations remain.**
See [physical evidence](6x4-physical-evidence.md); this is a physical checkpoint,
not complete signoff or hardware validation.

## M5 — Submission candidate

Freeze ISA and interfaces; publish examples, programming tools and measured limits.
Pass current Tiny Tapeout physical checks, gate simulation and timing for the currently approved 6x4 CMOS5L footprint.
Fill author/identity metadata, recheck competition rules and submit by January 18, 2027.
Stretch protocols follow evidence of area and timing headroom.

## Next session

1. Resolve the four slew violations on the nor4-driven reset/control path and
   the 131 clock-tree leaf fanout violations. Rerun the full physical and gate
   checks without relaxing limits, then review constraints and skipped checks.
   Preserve the committed baseline evidence before memory/ISA expansion.
2. Implement the SPI adapter callback on available host/FPGA hardware and capture
   an actual loaded waveform. Document external signal timing and voltage mapping;
   neither has hardware evidence yet.
3. Use the bounded SAMPLE path for UART RX framing/error tests, then extend I2C
   to payload read/write and SPI to multi-byte traffic. Validate against independent
   maintained IP or hardware when available. Unknown SPI byte reception is implemented.
4. Revisit 32-word depth and host-drained queues using measured program sizes and
   mapped area. Preserve the accepted instruction timing and overflow contracts.

Open decisions: physical host adapter, clock source on the test board, memory size/type,
unique submission name and FPGA availability. None blocks standalone simulation.

## Layout visualization follow-up

ADR 0002 adds a separate CMOS5L 8x2 preview workflow for a real UART layout
image and early physical feedback. The current competition baseline is 6x4 under ADR 0009;
preview results do not establish 8x4 physical acceptance. GDS, precheck and gate
simulation passed in run 34686808569. The real [layout image](images/uart-cmos5l-8x2-preview.png)
and timing/check details are recorded in [physical-build.md](physical-build.md).
