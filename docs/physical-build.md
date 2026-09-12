# First CMOS5L build attempt

Date: 2026-09-12.

## Workflow inspection

Repository: https://github.com/plssubscribe/protocol-emulator, branch `milestone/uart-tx`.
Initial source commit: `8acd879732614cf8d1f972fe48ba9167ee1ebf79`.

- [RTL test](https://github.com/plssubscribe/protocol-emulator/actions/runs/34685805675): passed.
- [Initial GDS and retry](https://github.com/plssubscribe/protocol-emulator/actions/runs/34685805660): metadata validation failed before physical implementation.
- [Docs](https://github.com/plssubscribe/protocol-emulator/actions/runs/34685805649): failed because author was blank.
- Optional FPGA workflow is not automatically triggered for this branch.

The local GDS workflow matches the current official CMOS5L template. It invokes
`TinyTapeout/tt-gds-action@ihp-cmos5l` with `pdk: ihp-sg13cmos5l`.
The initial run resolved that action to `45187a61556e197732a236b3f56acd2c800b9e0e`.
Its defaults select `htfab/tt-support-tools@cmos` and LibreLane `3.0.0rc1`;
LibreLane installation was skipped, so this is a configured version, not a tool run.
The inspected support-tools branch resolved to `da63c9927411e3aca350977d653d24bbf5bca972`.

## Blocker and repair

The first build reported both `Project author cannot be empty` and
`Invalid value for 'tiles' in 'project' section: 8x4`. The user supplied
`Erik Newsham`, now recorded in `info.yaml`.

The [competition rules](https://blog.janestreet.com/protocol-emulator-asic-competition/)
explicitly require `8x4`. However, the selected support tools' CMOS5L
[tile-size table](https://github.com/htfab/tt-support-tools/blob/da63c9927411e3aca350977d653d24bbf5bca972/tech/ihp-sg13cmos5l/tile_sizes.yaml)
has no 8x4 entry, and its `tech/ihp-sg13cmos5l/def/` directory has no 8x4 floorplan.
`project.py` needs both the size and a corresponding technology floorplan.
Removing validation alone is insufficient. Do not substitute the Sky130 8x4
floorplan or reduce the tile allocation: neither implements the required baseline.

Next action: obtain the upstream CMOS5L 8x4 support package/floorplan, then rerun
`gh workflow run gds.yaml --ref milestone/uart-tx`. No upstream message was sent.
No architecture change was made, so ADR 0001 remains in force.

## What actually ran

Metadata parsing ran; synthesis, placement, routing, timing analysis, DRC, LVS,
Tiny Tapeout precheck and gate-level simulation did not run. No physical area,
slack, manufacturability or tapeout-readiness result is available.
The uploaded initial `GDS_logs` artifact contains source/config files, not a completed layout.

For a beginner: RTL simulation checks the logic's behavior. Synthesis maps it to
library cells; placement and routing turn those cells into physical geometry.
Timing analysis checks signal arrival against the 20 ns clock budget. DRC checks
geometry rules; LVS checks that the layout matches the intended circuit.
Gate simulation reruns behavior against the resulting cell netlist. Each is a
separate evidence gate, and none of the physical gates was reached here.

The inherited `src/config.json` disables in-flow KLayout DRC and XOR checks.
Any later successful run must be read alongside its actual reports and precheck;
a green job alone should not be described as exhaustive signoff.

## Author-fixed run

Commit `25ae1e0` was pushed with the metadata repair and this build record.
[RTL CI](https://github.com/plssubscribe/protocol-emulator/actions/runs/34686128649)
passed again. [GDS](https://github.com/plssubscribe/protocol-emulator/actions/runs/34686128730)
failed solely on the unsupported `8x4` value, confirming the author error is fixed.
Physical implementation and downstream physical checks remain unrun.
[Docs](https://github.com/plssubscribe/protocol-emulator/actions/runs/34686128710)
passed after the author repair as well.

## Separate 8x2 visualization build

ADR 0002 adds a preview on the supported CMOS5L 8x2 floorplan without changing
committed 8x4 metadata. This preview cannot validate the competition footprint.
The first preview run, 34686728104, passed metadata validation but failed in the
upstream PDK installer: its parent repository now already contains the directory
that the installer tries to clone. `scripts/prepare-preview-action.py` repairs
only the ephemeral pinned action checkout, replacing that directory before the
original standalone process clone and pinned checkout. Process revision remains
`ae7613984daf3ac2b14897321399df497278068f`.

The repaired preview run is
https://github.com/plssubscribe/protocol-emulator/actions/runs/34686808569
(source `ccc41360c41e19b219f33c65f56a3647f8a426c9`). All three jobs passed: GDS, gate-level simulation and Tiny Tapeout precheck.

![CMOS5L UART layout preview](images/uart-cmos5l-8x2-preview.png)

The PNG is the unmodified upstream GDS render (17242 × 3138 pixels).
The small active logic patch is near the upper-left. This is an 8x2 physical
preview, not the still-blocked 8x4 competition implementation.

Final report evidence:

| Check / metric | Preview result |
| --- | --- |
| Footprint | 1724.16 × 313.74 µm |
| Functional/buffer cells | 192; 2895.78 µm² |
| Filler/decoupling cells | 41,393 |
| Worst setup slack | +13.475 ns |
| Worst hold slack | +0.119 ns |
| Setup/hold violations | 0 / 0 |
| Routed DRC errors | 0 |
| Magic DRC errors | 0 |
| LVS errors | 0; circuits match uniquely |
| Antenna net/pin violations | 0 / 0 |
| Gate-level pin regression | PASS |
| Tiny Tapeout precheck | All 9 listed checks PASS |

Timing covered the nominal-RC fast, typical and slow library corners at 20 ns.
These are results under the inherited generic SDC constraints, not proof of
board-level timing or 8x4 timing closure. Full in-flow KLayout DRC/XOR were
disabled by upstream configuration; the separate precheck's KLayout CMOS5L DRC,
pin-label and zero-area checks did run and pass. Wire-length threshold checking
was skipped because no threshold was configured. IR-drop analysis warned that
voltage-source locations were unspecified. The linter reported 85 warnings;
retain the logs for review rather than interpreting a green workflow as zero warnings.

LibreLane version: 3.0.0rc1. Parent IHP-Open-PDK revision:
`2bbec755dc67ca3db0261c3d6163e15735d66710`. Standalone CMOS5L revision remains
`ae7613984daf3ac2b14897321399df497278068f`.
Downloaded artifacts and logs are under ignored `work/physical/preview-artifacts/`.
The committed image and this evidence record remain available after Actions
artifacts expire.

A [close view of the UART region](images/uart-cmos5l-8x2-detail.png) was rendered
directly from the final GDS with KLayout 0.29.12 and the pinned process's
`libs.tech/klayout/tech/sg13cmos5l.lyp` layer colors. The reproducible helper is
`scripts/render-layout-detail.py INPUT.gds OUTPUT.png [LAYER_PROPERTIES.lyp]`.
Its view covers x=80..230 µm, y=244..319 µm; no circuit geometry was changed.
