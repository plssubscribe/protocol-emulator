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
