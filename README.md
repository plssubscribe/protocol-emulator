# Protocol emulator ASIC

A learn-by-building entry for Jane Street’s Protocol Emulator ASIC Competition.
Current milestone: UART TX bring-up. The final design must execute programmable
protocols; this fixed UART is the first verification and pin-interface baseline.

## Run it

Tools: Git, Make, Icarus Verilog, Python 3.11 and cocotb 2.0.1.
On macOS install Icarus with `brew install icarus-verilog`; on Ubuntu use
`sudo apt-get install iverilog make`. From this repository:

```sh
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r test/requirements.txt
source .venv/bin/activate
make test
```

If uv is unavailable, use `python3.11 -m venv .venv` followed by
`.venv/bin/pip install -r test/requirements.txt` instead.
`make unit` runs exhaustive byte tests at four bit divisors. `make integration`
runs the real top-level pins at the production divisor. Open `test/tb.fst`
in GTKWave or Surfer to inspect the waveform.

## What it does

With a 50 MHz clock and reset released, `uo_out[0]` repeatedly sends `0x55`
(the character U), using 115200 baud, 8 data bits, no parity, one stop bit (8N1).
Hold active-low reset for at least three rising clock edges before starting.
Every bit lasts 434 clocks; a frame has an additional idle clock after its stop bit.
All other dedicated outputs are zero; bidirectional pins remain inputs.
No external data inputs are used yet.

## Repository map

- `src/`: synthesizable Verilog and inherited CMOS5L physical configuration.
- `test/`: exhaustive transmitter unit test and black-box cocotb pin test.
- `docs/decisions/`: architecture decision records (ADRs).
- `docs/verification.md`: checks and acceptance criteria.
- `docs/roadmap.md`: milestones and current state.
- `docs/info.md`: Tiny Tapeout datasheet and hardware bring-up instructions.
- `info.yaml`: top module, source list, pins, clock, and 8x4 allocation.
- `.github/workflows/`: simulation, CMOS5L GDS, precheck, gate simulation, docs and optional FPGA.
- `work/`: ignored local build products. `.venv/` is ignored too.

## Continuing the project

Start with [the roadmap](docs/roadmap.md). Record each consequential architecture
choice in `docs/decisions/`; preserve prior decisions and explicitly supersede them.
Keep each milestone runnable. Explain new concepts at the change that needs them.

The repository is published at https://github.com/plssubscribe/protocol-emulator
on `milestone/uart-tx`; `template` records upstream. Author metadata is Erik Newsham.
The first GDS attempts stop at metadata validation because the inherited CMOS5L
support tools do not provide the required 8x4 floorplan. A separate supported
8x2 preview now has a real [chip layout image](docs/images/uart-cmos5l-8x2-preview.png),
passing precheck and gate simulation. The competition baseline remains 8x4. See
[the physical-build record](docs/physical-build.md). Before submission, choose a
unique top-module name and complete the physical checks. Configure GitHub Pages
as required by the template viewer. Passing simulation does not establish physical timing or
manufacturability; those remain separate acceptance gates.

## Provenance and constraints

Official [CMOS5L template](https://github.com/TinyTapeout/ttihp-verilog-template/tree/cmos5l),
commit `b86a2a781484bcab7ba522dc5de540086695a430`, retrieved 2026-09-12.
The [competition announcement](https://blog.janestreet.com/protocol-emulator-asic-competition/)
requires an open-source programmable protocol emulator, CMOS5L and 8x4 tiles;
the announced deadline is January 18, 2027. Rules should be rechecked before submission.
The inherited Apache-2.0 license is retained. Template action branch references
remain upstream defaults; record resolved versions when producing a release build.
