# ADR 0010: Repair clock loading and routed transitions

Date: 2026-10-04. Status: accepted for physical characterization; results pending.

The baseline integrated 6x4 build has positive setup/hold slack and passing
geometry checks, but final STA reports four slow-corner slew violations on one
nor4 output net and 131 fanout violations on clock-tree leaf buffers. All leaf
violations use library limit 8, with loads 11..18. Preserve that evidence.

Set `CTS_SINK_CLUSTERING_SIZE` to 6, leaving room below the library limit for
clock-tree balancing loads. Enable `RUN_POST_GRT_DESIGN_REPAIR` with a 20% slew
repair margin so cell resizing/buffering uses global-route parasitics. Enable
`RUN_POST_GRT_RESIZER_TIMING` to restore setup/hold after those electrical repairs.
These are implementation settings, not changes to functional architecture.
No electrical limit is relaxed. No RTL, clock period, PDK, floorplan, physical
pin assignment, reset, instruction timing or memory depth changes.

The upstream installer follows the parent PDK dev branch. Pin its checkout to
`0dedf265f0cad6ef81aeb64b9ddd17eef88c0460`, already recorded in the baseline,
so characterization does not silently change the parent process checkout.
Standalone CMOS5L remains `ae7613984daf3ac2b14897321399df497278068f`.

Add a separate CI acceptance job requiring final reported setup/hold slack to
be nonnegative and setup/hold, slew, capacitance, fanout, route/Magic DRC, LVS and
antenna violation counts to be present and zero. Missing or incomplete metrics
fail. Keep precheck and gate simulation as separate required results; none is
inferred from these metrics. Do not waive a remaining violation to turn CI green.

Reviewed source: LibreLane 3.0.0rc1 tag, commit
`e73adbd885e0a33efe131f4ea40f4f93efeb4247`, `steps/openroad.py`,
`scripts/openroad/cts.tcl`, `repair_design_postgrt.tcl`, `flows/classic.py`.
The new settings exist in that pinned version. Post-GRT repairs are experimental
and may extend runtime; inspect the completed artifacts before claiming cleanup.
