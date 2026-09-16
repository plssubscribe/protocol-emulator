# Protocol emulator ASIC

A learn-by-building entry for Jane Street’s Protocol Emulator ASIC Competition.
Current milestone: Protocol Witness integrated into the Tiny Tapeout top, with an
SPI program loader, registered protocol outputs and atomic failure readback. The
original UART diagnostic remains available. Verified in simulation, not on hardware.

## Entry direction: Protocol Witness

A protocol emulator that helps find and reproduce timing-dependent device bugs.
The proposed workflow is: program a conversation, sweep a timing parameter,
capture the first failed response expectation, and save a replayable case.
See [ADR 0003](docs/decisions/0003-reproducible-protocol-failures.md) for scope,
prior art and acceptance gates. [ADR 0004](docs/decisions/0004-loadable-witness-core.md)
specifies the core ISA and exact clock contract.
[ADR 0005](docs/decisions/0005-spi-host-transport.md) defines the physical pin
assignments and framed SPI host transport.

Run the first **software-only** experiment with Python 3 and Make:

```sh
make lab
```

It compares correct and deliberately faulty synthetic request/acknowledge devices
at pulse widths 1..8, finds failures at widths 1..3, saves the smallest case to
`work/protocol-witness.json`, and checks exact model replay. This is an executable
timing proposal, not RTL, I2C support, a real device test or physical evidence.

## Runnable hardware milestone

After activating the environment below:

```sh
make engine       # load programs, compare RTL cycles, save and replay a failure
make mutations    # prove the tests catch four selected deliberate RTL defects
```

The 32-word core executes DRIVE, EXPECT, WAIT, JMP, SAMPLE and HALT. It generates all 256
UART byte values in tests without using the fixed UART peripheral. A timed EXPECT
captures the first missed response's instruction, PC, cycle, input and sample count,
then releases output enables. Outputs are registered, with no fetch bubbles.
`work/rtl-witness.json` contains a real RTL simulation trace and a reloaded/replayed
failure case against the deliberately faulty synthetic peer.

The Tiny Tapeout top now connects the loader/readback to SPI on ui[0:2] and uo[1].
A CRC-valid unlock packet enables the host; the eight uio pins carry programmable
protocol signals. `make integration` exercises only public pins: load, run, timeout,
readback, abort, input synchronization, malformed packets and atomic snapshots.
The protocol input adapter adds the documented two-register synchronization path.
The SPI host link does not itself count as an emulated SPI protocol demonstration.

`tools/witness_host.py` provides the packet codec and asynchronous host API; supply
an adapter's 64-bit SPI transaction callback. The test uses a simulated pin driver.
No physical adapter or board capture has been tested. See the
[integrated evidence report](docs/integrated-witness-evidence.md) in `docs/`.

Optional generic synthesis and netlist simulation:

```sh
uv pip install --python .venv/bin/python -r test/synthesis-requirements.txt
make synth-check
make formal       # bounded core safety checks plus timeout reachability
make synth-top-check  # integrated generic netlist, public-pin regression
make host-mutations   # four packet/snapshot protection defects must be detected
```

This checks the synthesized generic netlist and records cell counts under
`work/synthesis/`. It does not map CMOS5L cells or prove timing closure.

CMOS5L library mapping is now available with `make cmos5l-map-check`:
8,463 mapped standard cells, 0.164 mm² summed cell area. The organizer-approved
6x4 footprint is now selected (ADR 0009); mapped area does not establish timing or fit.
See [mapping evidence](docs/cmos5l-mapping-evidence.md).

## I2C clock-stretching demonstration

```sh
make i2c-demo
python scripts/render-i2c-witness.py
```

The loaded firmware stretches SCL, checks an address byte and generates ACK on a
resolved open-drain bus. A separately written controller and bus decoder verify
START/address/ACK/STOP. The correct controller passes all 49 tested hold durations;
a deliberately broken controller first fails at 20 cycles in the accelerated
fixture. A nominal 100 kHz case independently shows a lost first address bit.
The saved program, bus trace and host-read witness replay exactly.

![Actual sampled boundary waveform](docs/images/i2c-stretch-boundary.svg)

This is an address probe, not full I2C read/write support or a third-party bug
report. The controller fixture is project-authored. See
[the experiment evidence](docs/i2c-stretch-evidence.md) and
[ADR 0006](docs/decisions/0006-i2c-stretch-experiment.md) for timings and limits.
No RTL or physical configuration changes were needed for this protocol milestone.

## Programmed SPI exchange

`make spi-demo` loads a 28-word SPI controller program on the same engine and
checks all four CPOL/CPHA modes through uio pins. An independent edge-driven target
returns a configured byte. The regression checks MOSI data and clock spacing,
then flips a response bit and reloads the saved program to reproduce its witness.
The artifact is `work/spi-witness.json`.

The original experiment checks a known response; the capture extension below
also receives unknown bytes. Multi-byte transfers remain open. It is separate from the SPI host loader. See
[ADR 0007](docs/decisions/0007-programmed-spi-byte.md).

## Receive unknown input data

`SAMPLE` appends one selected synchronized input bit after a programmed delay.
The run buffer retains up to 32 bits; a 33rd sample stops with overflow status 5
and preserves the first 32. `await host.snapshot(capture=True)` reads data and
count from the same atomic snapshot as the failure witness.

`tools.spi_lab.capture_program(tx, mode, half)` receives an unknown SPI response
without embedding an expected value. It uses the same 28 words and waveform timing
as the original exchange. Run `make capture-demo` for unknown-byte reception in
all four modes and buffer overflow/readback checks. This is bounded capture;
continuous streaming and host-drained queues are not implemented.
See [ADR 0008](docs/decisions/0008-bounded-input-capture.md).

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
Until the explicit host unlock packet, other dedicated outputs are zero and
bidirectional pins remain inputs. After unlock, host status/readback and programmed
uio signals become active; see [the pin contract](docs/decisions/0005-spi-host-transport.md).

## Repository map

- `src/`: synthesizable Verilog and inherited CMOS5L physical configuration.
- `test/`: exhaustive transmitter unit test and black-box cocotb pin test.
- `docs/decisions/`: architecture decision records (ADRs).
- `docs/verification.md`: checks and acceptance criteria.
- `docs/roadmap.md`: milestones and current state.
- `docs/info.md`: Tiny Tapeout datasheet and hardware bring-up instructions.
- `info.yaml`: top module, source list, pins, clock, and 6x4 allocation.
- `.github/workflows/`: simulation, CMOS5L GDS, precheck, gate simulation, docs and optional FPGA.
- `work/`: ignored local build products. `.venv/` is ignored too.

## Continuing the project

Start with [the roadmap](docs/roadmap.md). Record each consequential architecture
choice in `docs/decisions/`; preserve prior decisions and explicitly supersede them.
Keep each milestone runnable. Explain new concepts at the change that needs them.

The repository is published at https://github.com/plssubscribe/protocol-emulator
on `milestone/uart-tx`; `template` records upstream. Author metadata is Erik Newsham.
The first GDS attempts stopped at metadata validation because the inherited CMOS5L
support tools do not provide the required 8x4 floorplan. A separate supported
8x2 preview now has a real [chip layout image](docs/images/uart-cmos5l-8x2-preview.png),
passing precheck and gate simulation. That image is UART-only and does not include
the new Witness core or host. The competition baseline is now 6x4 following the organizer update (ADR 0009). See
[the physical-build record](docs/physical-build.md). Before submission, choose a
unique top-module name and complete the physical checks. Configure GitHub Pages
as required by the template viewer. Passing simulation does not establish physical timing or
manufacturability; those remain separate acceptance gates.

## Provenance and constraints

Official [CMOS5L template](https://github.com/TinyTapeout/ttihp-verilog-template/tree/cmos5l),
commit `b86a2a781484bcab7ba522dc5de540086695a430`, retrieved 2026-09-12.
The [competition announcement](https://blog.janestreet.com/protocol-emulator-asic-competition/)
now requires an open-source programmable protocol emulator, CMOS5L and 6x4 tiles;
the announced deadline is January 18, 2027. Rules should be rechecked before submission.
The inherited Apache-2.0 license is retained. Template action branch references
remain upstream defaults; record resolved versions when producing a release build.
