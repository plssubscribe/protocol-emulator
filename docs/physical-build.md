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
