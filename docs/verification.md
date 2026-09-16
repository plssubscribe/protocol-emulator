# Verification strategy

Verification starts at observable behavior, then adds implementation and physical checks.
Tests must fail on incorrect pin levels, timing or handshakes, not merely run a waveform.

## Milestone 1 checks

`make test` runs:

- Unit simulation: all 256 bytes at divisors 1, 2, 3 and 434; idle high,
  ready behavior, latched input data, and requests while busy. Every clock of every
  start, data and stop bit is compared with an independently constructed frame.
- Pin integration: four complete 0x55 frames at 50 MHz, exact bit duration and
  frame spacing; reset abort at each of ten bit positions; fresh start after reset;
  unused outputs and output enables; deterministic random activity on ignored inputs.
- The integration test only uses top-level pins so the inherited GDS workflow can
  rerun it on the synthesized gate netlist (`make -C test GATES=yes`).

Local RTL results are recorded in the roadmap. CI runs unit and integration checks.
The GDS workflow separately runs the template linter, synthesis/place-and-route,
precheck and gate-level simulation. Inspect reports for timing violations, area,
DRC and LVS results; a green RTL test does not substitute for those reports.
The inherited physical flow contains upstream checking defaults: verify current
shuttle signoff requirements before claiming tapeout readiness.

## Next milestones

For the programmable engine, write an instruction-level Python reference model
before adding randomized programs. Compare cycle-stamped pin output and output-enable
traces. Include instruction timing, wrap/jumps, stalls, reset, FIFO overflow/underflow,
program loading, and illegal opcodes. Add bounded formal properties where helpful
(e.g. no writes outside instruction memory, deterministic reset and safe output enables).

SPI tests need a modeled peer for supported clock modes; I2C needs a resolved bus
with pull-ups, open-drain output enables, ACK/NACK and clock stretching. Future
asynchronous inputs need synchronization and an explicit latency contract.

After the first programmable slice, run synthesis and full place-and-route early.
Record cells/area, worst setup/hold slack and tool versions for each release candidate.
If an FPGA is available, replay the same observable cases through actual pins before
fabrication. Physical UART milestone acceptance requires a captured hardware trace;
simulation alone is marked as simulation complete.

## Protocol Witness software specification

`make model` checks six software timing/experiment cases; it also runs under
`make test`. `make lab` executes the finite pulse-width sweep and verifies that
the saved witness reproduces every software cycle. Covered: first/last/late
matching samples, exact drive holds, masks, timeout capture and release, invalid
operands, execution budget and the deliberately faulty peer's width boundary.
These are specification checks, not independent RTL verification. The peer is
a synthetic fixture; no I2C device or physical behavior is being validated.

## Standalone Witness RTL and generic netlist

`make engine` runs six groups against `witness_core`: a 16-case closed-loop pulse
sweep plus exported-file replay; 21 first/last/late deadline cases and 160 seeded
random programs; an independent all-byte UART wire oracle plus divisor 434;
loader/start contention, blocked live writes, reset/abort and illegal/uninitialized
execution; 65,535-cycle duration, PC wrap and backward jump; and output stability
between edges. The original DRIVE/EXPECT model also checks the toy experiment's
prefix, independently of the binary ISA interpreter. Inputs are already synchronized.

`make mutations` first reruns the unmodified baseline, then compiles four separately
modified source copies under `work/mutations/`. It requires actual AssertionError
results, not compiler/tool failures. Selected mutants: missed last EXPECT sample,
ignored input mask, inverted output enables and accepted live memory writes.
All four are detected. This is a targeted suite, not a quantified universal score.

`make synth-check` runs Yosys generic synthesis and structural `check -assert`, then
reruns all six core groups on the generated netlist. This is zero-delay generic
netlist simulation, not PDK cell simulation or post-layout timing. At this standalone milestone, the inherited
TT gate workflow still exercised only M1; the later integration below updates the top. CI is configured to run the new
checks and retain evidence; the updated workflow has not yet run remotely.

Remaining gaps: pin synchronization/metastability, physical host loading, actual
I2C/SPI peers, timestamp rollover across 2^32 cycles, target-library synthesis,
static timing and physical signoff. No FPGA or fabricated-device tests ran.

## Bounded formal safety

`make formal` uses the actual core with `test/formal/witness_safety.v` and Yosys SAT.
It checks six public-interface properties for 12 sequential steps, assuming an
initial synchronous reset and otherwise arbitrary defined inputs and initial state.
Properties cover idle output release, done/running exclusion, reset, abort, sticky
terminal records and load/start priority. A separate 8-step satisfiability check
requires a timeout to be reachable; it guards against a wholly inert/reset-only
harness. This is bounded model checking, not an inductive or complete ISA proof.
It does not establish CDC, timing, electrical safety or correctness after the bound.

## Integrated host transport (2026-09-13)

`make integration` now includes three host test groups plus the original UART pin
contract. Tests only access public TT pins. They check locked-write rejection,
CRC-checked unlock/loading, address 31, all 40 payload bits, two distinct pulse
programs with timeout readback,
program-generated UART on uio[0], bad CRC, 63/65-clock frames, busy write/start
rejection, abort, reset/invalidation, nominal input synchronization and atomic
snapshot pages across a later run. Host half-periods of 4, 5 and 7 system clocks
are exercised. This is digital simulation, not metastability or external board timing.

`make synth-top-check` synthesizes all integrated modules and reruns the four pin
test groups on the resulting generic netlist. Hierarchical cell counts include
instances recursively, not just cells in the wrapper. This is still not PDK mapping.

`make host-mutations` first passes the original integrated baseline, then checks
four selected defects: ignored CRC, ignored frame length, writes while locked and
non-atomic snapshot readback. A first version of the locked-write test checked only
terminal status; mutation exposed that a later uninitialized-slot fault could hide
the write. The strengthened test requires PC 0, cycle 0, empty word and no drive.
This is a concrete example of tests improving in response to mutation evidence.

## I2C address probe and stretching (2026-09-13)

`make test` now includes `test_i2c.py`: 49 integer hold durations against both
controller variants, two nominal-100-kHz cases, and exact saved-word/trace/witness
replay through public pins. The digital open-drain resolver rejects high drive
and unrelated-pin enables. An independent state machine produces the address
probe; a line decoder checks the completed bus clocks and ACK/STOP. Model unit
tests include a hand-constructed bus transaction and the wait-behavior mutation.

`make i2c-netlist` runs only the explicit five-duration subset (0,19,20,24,48),
nominal cases and replay against a hash-matched generic netlist. `make synth-top-check`
uses that same I2C subset alongside the complete existing UART/host pin tests.
The full I2C sweep is RTL-only. See `i2c-stretch-evidence.md` for exact findings,
time origins, coverage limits and the distinction between compressed and missing
clock pulses. No electrical timing or complete I2C compliance claim follows.


## SAMPLE extension

See [capture evidence](capture-evidence.md) and ADR 0008. Full RTL regression and
new capture lifecycle, unknown SPI response, overflow and atomic readback tests
must pass. Capture must preserve first 32 bits, report the 33rd sample as status 5,
clear only on accepted start/reset, and obey the existing input synchronizer.
Record synthesis and bounded proof results separately from physical signoff.
