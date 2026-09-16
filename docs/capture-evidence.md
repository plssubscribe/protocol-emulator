# Bounded input capture evidence

The SAMPLE extension receives unknown data using the existing programmable engine.
A 28-word SPI program now accepts target bytes without encoding their values in
firmware. `make capture-demo` runs the public-pin tests; ADR 0008 defines the exact
sampling, overflow and snapshot contract.

## Verified locally on 2026-09-13

- `make test`: eleven model checks, 1,024 UART unit cases, seven integrated test
  groups and seven core groups passed. A subsequently added public-pin overflow/
  reset group also passed separately (the full run had already loaded its tests).
- Unknown SPI responses: modes 0..3, one loaded program per mode, responses 96,
  00 and FF, plus 35 after freezing the previous snapshot. Sixteen exchanges at
  four-system-cycle half-periods. Each checks eight received bits, eight correct
  MOSI bits and sixteen uniformly spaced clock edges.
- Core capture tests select every input pin, vary sample durations and input levels,
  fill and overflow the 32-bit buffer, retain data across idle writes, clear on
  accepted restart, and check abort/reset precedence and malformed SAMPLE words.
- `make synth-check`: all seven core groups passed on the generic synthesized netlist.
- `make mutations`: all six selected core mutations detected, including wrong
  capture pin and overwriting a full buffer.
- `make host-mutations`: all five selected host mutations detected, including a
  capture page that incorrectly returns live data instead of its frozen snapshot.
- `make formal`: bounded safety checks to 12 steps passed, plus timeout reachability
  by step 8. Capture count, reset clearing, abort retention and sticky completed
  data are included. This is not induction; the 33-sample overflow is simulation
  evidence, beyond this proof depth.

- `make synth-top-check`: all eight integrated groups passed on the generic
  netlist, including unknown SPI reception. I2C uses the documented five-width
  smoke subset plus nominal-speed cases and replay; the RTL sweep remains 49 widths.
  All twelve recorded unknown-byte capture results match RTL exactly, as do the
  known-response SPI results and full failure replay traces.

The [machine-readable evidence](evidence/capture-2026-09-13.json) includes source
hashes, named test groups, synthesis counts, mutation results and capture records.

## Resource measurement

| Generic synthesis | Previous | Capture extension | Difference |
| --- | ---: | ---: | ---: |
| Core cells | 5,151 | 4,904 | -247 |
| Core flip-flops | 1,528 | 1,566 | +38 |
| Integrated cells | 6,769 | 6,856 | +87 |
| Integrated flip-flops | 1,888 | 1,964 | +76 |

The 38-bit capture state is duplicated in the atomic snapshot; the two reserved
snapshot bits optimize to constants. Boolean optimization changes cell mapping,
so the smaller generic core cell count is not evidence that adding capture reduces
physical area. These totals are from YoWASP Yosys 0.69 with the same synthesis
script, not a mapped incremental area estimate.

No new CMOS5L mapping, static timing, place-and-route, DRC, LVS or hardware capture
ran. The required 8x4 physical acceptance remains open. No pin map, clock target,
PDK, instruction-store depth or prior instruction timing changed.

## Limits

The buffer holds 32 bits per run; it cannot be drained during execution. A 33rd
sample terminates explicitly rather than silently overwriting. Sampling observes
the existing synchronized input at the end of its programmed duration. Four-cycle
SPI half-period tests use an ideal digital target and are not an electrical speed
rating. Multi-byte firmware, UART RX framing and continuous queues remain open.
