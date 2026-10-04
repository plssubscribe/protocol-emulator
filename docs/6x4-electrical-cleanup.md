# CMOS5L 6x4 electrical cleanup

Started 2026-10-04. Decision: [ADR 0010](decisions/0010-routed-electrical-cleanup.md).
The [baseline physical evidence](6x4-physical-evidence.md) remains unchanged.

First-attempt source: `689f55a3422bdb1c4a27d1a338fb165d481c59d8` on `codex/physical-6x4`.

- [Physical build, electrical acceptance, gate simulation and precheck](https://github.com/plssubscribe/protocol-emulator/actions/runs/37228616726)
- [RTL and generic-netlist regression](https://github.com/plssubscribe/protocol-emulator/actions/runs/37228616702)
- [Documentation](https://github.com/plssubscribe/protocol-emulator/actions/runs/37228616729)

First attempt: physical implementation and RTL/generic regression passed;
strict acceptance failed on four remaining slew violations. Fanout is now zero.
Area is 235,647 µm² (26.1129% utilization); setup/hold slack is +8.494268 /
+0.124826 ns. [Preserved first-attempt metrics](evidence/electrical-cleanup-attempt-1/summary.json)
and violation pins record the result. No full cleanup pass is claimed.

ADR 0011 adds the weak NOR4 cell to the additive mapping exclusions for the next
attempt. Unfinished checks on the rejected candidate are cancelled; their results
will not be transferred to the replacement.

The implementation caps CTS sink groups at six, enables post-global-routing
electrical repair with a 20% slew margin, and subsequently repairs timing.
The separate acceptance job requires final setup/hold, slew, fanout, capacitance,
route/Magic DRC, LVS and antenna metrics to be present and clean. Existing precheck
and functional gate simulation remain separate requirements.

The acceptance helper was checked against the actual baseline: it rejects both
remaining electrical violation counts. Temporary fixture checks also confirmed
that missing metrics and negative hold slack fail, while a complete clean fixture
passes. This verifies the checker, not the new physical design.

RTL, clock period, footprint, pin map, reset, instruction timing and standalone
process revision are unchanged. The parent PDK checkout is pinned to the baseline's
recorded revision. Do not replace the baseline image or promote a result until
completed artifacts have been reviewed.

## Second attempt

Source: `ee460c64fb2cad045c2d366f3e67aa86bb5d7b21`.

- [Physical build and acceptance](https://github.com/plssubscribe/protocol-emulator/actions/runs/37231460552): GDS passed; strict electrical acceptance failed; unfinished gate/precheck jobs cancelled.
- [RTL and generic regression](https://github.com/plssubscribe/protocol-emulator/actions/runs/37231460578): passed.
- [Documentation](https://github.com/plssubscribe/protocol-emulator/actions/runs/37231460581): passed.

Local `make cmos5l-map-check` passed all three selected mapped-netlist tests:
host execution/witness, capture overflow/readback/reset, and unknown SPI capture.
The mapping contains 8,471 cells, 163,806.6024 µm² summed typical-library area,
and zero `sg13cmos5l_nor4_1` instances. This is mapping and functional behavior
evidence, not routed electrical acceptance. Physical config SHA256:
`f8c9c471cd2c7f3b75cdbd5dcf5c62ada8e2e19653f96320eaffaf75717634dd`.

Second-attempt final reports show zero slew, zero capacitance, four fanout
violations, +9.517722 ns setup and +0.127329 ns hold slack. Standard-cell area
is 235,329 µm² (26.0777% utilization). Geometry and antenna counts are zero.
[Preserved reports](evidence/electrical-cleanup-attempt-2/summary.json) distinguish
this rejected candidate from the baseline and the next attempt.

Intermediate netlist comparison traces all four excess fanout counts to antenna
diodes added during detailed routing. ADR 0012 selects detailed-route jumper-only
antenna repair for the third attempt. Antenna checking and all electrical limits
remain enabled and unchanged.

## Third attempt

Source: `7b09bb09fa5822d88f913d9211230559219c60a0`.

- [Physical build and acceptance](https://github.com/plssubscribe/protocol-emulator/actions/runs/37235422243): GDS passed; strict acceptance failed on antenna violations; unfinished gate/precheck cancelled.
- [RTL and generic regression](https://github.com/plssubscribe/protocol-emulator/actions/runs/37235422231): passed.
- [Documentation](https://github.com/plssubscribe/protocol-emulator/actions/runs/37235422303): passed.

The only new implementation change is detailed-route jumper-only antenna repair.
Final reports show zero slew/fanout/capacitance violations, but eight antenna
nets and twelve pins still violate. Setup/hold slack is +9.532713 / +0.127305 ns;
route/Magic DRC and LVS counts are zero. Area is 235,172 µm² (26.0602%).
[Preserved reports](evidence/electrical-cleanup-attempt-3/summary.json) record this
rejected candidate. ADR 0013 restores diode protection and repairs loads afterward.


## Fourth attempt

Source: `2acd7e5a85cbbf0c5dbb81da7a440fc84d98aeb6`.

- [Physical build and acceptance](https://github.com/plssubscribe/protocol-emulator/actions/runs/37239496072): implementation failed during late rerouting; downstream checks skipped.
- [RTL and generic regression](https://github.com/plssubscribe/protocol-emulator/actions/runs/37239496093): passed.
- [Documentation](https://github.com/plssubscribe/protocol-emulator/actions/runs/37239496063): passed.

Local `python scripts/check-physical-flow.py` passed with LibreLane 3.0.0rc1:
native discovery, all original Classic steps/configuration/gates, unique step IDs
and the intended late-repair order. OpenROAD did not run locally. The late repair found all four fanout violations and inserted six buffers.
However, global routing skipped nets with existing detailed wires. The old wires
then disagreed with the changed connectivity; rerouting failed with DRT-0206.
No final physical result, gate simulation or precheck is claimed. ADR 0014 adds
an explicit signal-route reset before each late repair, preserving the power grid.
