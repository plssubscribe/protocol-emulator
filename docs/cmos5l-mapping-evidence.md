# CMOS5L mapping checkpoint — 2026-09-14

The integrated capture design now maps to **8,463 standard cells**, with a summed
Liberty cell area of **163,546.803 µm² (0.163547 mm²)**. This replaces a generic
cell-count guess with a measurement using the pinned process library. It does not
establish the required die size, placement utilization, routed area or timing.

## Reproduce

Activate `.venv` with `test/synthesis-requirements.txt` installed, then run:

```sh
make cmos5l-map        # download pinned library/models; map and check all cells
make cmos5l-map-check  # map, then three selected public-pin simulation groups
```

`scripts/map-cmos5l.py` uses process revision
`ae7613984daf3ac2b14897321399df497278068f`, the same standalone process revision as
the historical UART preview. It selects the typical 1.20 V / 25 °C standard-cell
library, matching the pinned process configuration's default supply. The process
synthesis-exclusion list is applied to both sequential and combinational mapping;
no excluded or unmapped logic cells are permitted in the result. Yosys's hierarchy
scope metadata is removed before checking the mapped cell inventory.

The flattened design is mapped using YoWASP Yosys 0.69, `dfflibmap` and ABC.
The 20 ns project target is retained in project configuration but is **not applied
as a timing constraint in this area-characterization command**. No input/output
loads, wire RC, placement, clock-tree insertion or timing repair are modeled.
Do not interpret ABC library mapping as static timing analysis or timing closure.

The outputs live under `work/cmos5l-mapping/`: library and model sources,
`map.ys`, `yosys.log`, `mapped.v`, `mapped.json`, and a hash-bearing `summary.json`.
The sum excludes physical-only filler/decap/tap cells, routing, and subsequently
inserted buffers. It is not a final chip-area prediction.

## Functional mapped-netlist checks

All three selected public-pin groups passed using the pinned PDK Verilog models:
loading/execution/witness readback, capture overflow/reset, and unknown SPI response
capture in all four modes. The run simulated 5.60744 ms. All twelve recorded SPI
capture results match the earlier RTL results exactly; four additional exchanges
check frozen snapshot behavior. This is selected functional coverage, not the full
regression or post-route signoff.

Icarus 13.0 warned that edge-sensitive `ifnone` timing paths in the upstream cell
models are unsupported. No SDF was applied and timing was not verified. The
[machine-readable evidence](evidence/cmos5l-mapping-2026-09-14.json) records source
and library/model hashes, cell counts, test names, and the current support blocker.

A [draft upstream request](8x4-support-request.md) is prepared locally; it has not
been sent. The test runner's multi-test regex quoting was also repaired, including
the existing `capture-demo` target. No RTL changed.

## Required 8x4 flow remains blocked

On 2026-09-14, upstream references still resolve to:

- `TinyTapeout/tt-gds-action`, `ihp-cmos5l`:
  `45187a61556e197732a236b3f56acd2c800b9e0e`.
- `htfab/tt-support-tools`, `cmos`:
  `da63c9927411e3aca350977d653d24bbf5bca972`.

That support revision still lacks both the required CMOS5L 8x4 size entry and
`tt_block_8x4_pgvdd.def`. See the upstream
[tile table](https://github.com/htfab/tt-support-tools/blob/da63c9927411e3aca350977d653d24bbf5bca972/tech/ihp-sg13cmos5l/tile_sizes.yaml)
and [floorplan directory](https://github.com/htfab/tt-support-tools/tree/da63c9927411e3aca350977d653d24bbf5bca972/tech/ihp-sg13cmos5l/def).
The canonical 8x4 project metadata, PDK, pin map and clock target are unchanged.
No fabricated floorplan or smaller competition footprint was substituted.

The next dependency is an accepted CMOS5L 8x4 support package. Then run the real
implementation flow on these current sources and review mapped timing, placement,
routing, DRC/LVS, Tiny Tapeout precheck and post-route gate simulation. The older
8x2 UART layout is not evidence for this integrated design. No upstream message,
repository push, remote build dispatch or publication was performed in this checkpoint.
