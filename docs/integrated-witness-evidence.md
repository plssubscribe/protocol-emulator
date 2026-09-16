# Protocol Witness: integrated loader and failure readback

Date: 2026-09-13. Scope: public Tiny Tapeout pins, RTL and generic netlist simulation.
[ADR 0005](decisions/0005-spi-host-transport.md) defines the new pin contract.
[Machine-readable evidence](evidence/integrated-witness-2026-09-13.json) records
source hashes, cell counts and test/mutation results.

## The demonstration now crosses the real chip interface

The test sends SPI packets through ui[0:2], receives replies on uo[1], and observes
programmed signals on uio. It never writes internal instruction memory or inspects
internal state. It checks instruction address 31 and complete 40-bit payload readback, then loads
two programs with different output pulse widths, runs
them, and reads their timeout records through the same host link. Another loaded
program emits UART byte A6 on uio[0], independently of the diagnostic UART on uo[0].

Failure records for pulse widths 1 and 9 report EXPECT at PC 2, cycles 4 and 12,
observed input 0, three samples. `work/pin-host-witness.json` contains decoded host
readback. These missing-response fixtures are intentionally synthetic, not actual
bugs discovered in an I2C controller. The next flagship demonstration should use
an independently implemented real protocol peer.

The standalone pulse sweep and file-replay tests from the prior milestone remain.
This integrated milestone demonstrates program loading and readback through pins;
it does not yet claim replay on an FPGA or fabricated device.

## Protection and observability

The interface requires an explicit unlock packet. Every command has a framed CRC;
truncated, overlong or corrupted packets do not write memory or start execution.
Loading/starting while busy returns an error. Reset clears the program and returns
the chip to the original diagnostic state. ABORT releases protocol output enables.

A snapshot command captures all witness fields together. Reads of later pages use
that snapshot even if a subsequent program changes the live record. Protocol input
synchronization has a documented nominal latency, checked through public pins.
SPI communication errors and protocol timeouts have separate status indicators.

## Checks and costs

| Check | Result |
| --- | --- |
| Original UART pin contract, including random input activity | PASS |
| Public-pin host loading, programmed waveforms and failure readback | PASS |
| Corrupted/short/long frames, busy rejection, abort/reset | PASS |
| Input synchronization and snapshot consistency | PASS |
| Same four groups on integrated generic netlist | PASS |
| Four selected host mutation checks | All detected |
| Standalone core tests, four core mutations and bounded formal checks | PASS; same core properties and mutation scope as the prior milestone |
| Integrated generic synthesis/structural check | PASS |
| Generic cell count, including all instantiated modules | 6,769 |
| Flip-flops within that count | 1,888 |

The locked-write mutant initially survived a weak test: an unauthorized DRIVE could
run and then fault on the next unloaded slot, matching the expected fault status.
The improved test also requires PC 0, cycle 0, an empty word and no driven waveform.
Its success demonstrates specific protection, not a universal verification score.

Tools: Icarus 13.0, cocotb 2.0.1, YoWASP Yosys 0.69 (`9f75ca1f9`). Generic cells
are not CMOS5L area or transistor counts; netlist simulation is zero-delay. CI is
configured for these checks but has not run remotely for the current changes.

## Reproduce

With the README environment active:

```sh
make test
make host-mutations
make synth-top-check
```

The last command needs the optional synthesis requirements. The portable host API
in `tools/witness_host.py` accepts an async 64-bit SPI transaction callback. Tests
supply a simulated pin driver. No particular USB adapter or board has been validated.

Remaining gates: actual protocol peers and data-path features, adapter/hardware
capture, program-memory sizing from real firmware, CMOS5L mapping and 8x4 physical
implementation, CDC/timing constraints and signoff. No new physical checks ran.
The old 8x2 UART layout does not represent this integrated design.
