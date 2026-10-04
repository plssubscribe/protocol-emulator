# CMOS5L 6x4 electrical cleanup

Started 2026-10-04. Decision: [ADR 0010](decisions/0010-routed-electrical-cleanup.md).
The [baseline physical evidence](6x4-physical-evidence.md) remains unchanged.

Source: `689f55a3422bdb1c4a27d1a338fb165d481c59d8` on `codex/physical-6x4`.

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
