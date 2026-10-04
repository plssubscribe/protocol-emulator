# ADR 0012: Use jumpers for detailed-route antenna repair

Date: 2026-10-04. Status: accepted for the third physical characterization.

The second candidate (`ee460c64fb2cad045c2d366f3e67aa86bb5d7b21`) cleared
all slew violations, with positive setup/hold slack and zero geometry/antenna errors.
Four data-buffer fanout violations remain, with loads 10, 13, 9 and 15 versus
library limit 8. These are not clock-tree violations.

Compare intermediate netlists: nets `net234`, `net248`, `net278`, `net562`
have 6, 6, 5, 6 loads through the post-global-route timing repair. Detailed routing
then adds 4, 7, 4, 9 `sg13cmos5l_antennanp` diode loads respectively. The final
counts exactly match the four reported fanout violations. Earlier design repair
cannot fix loads that have not yet been added.

Enable `DRT_ANTENNA_REPAIR_JUMPER_ONLY`, supported by the pinned LibreLane
3.0.0rc1 and OpenROAD detailed-routing script. Repair antenna geometry using
metal-layer jumpers instead of adding diode loads at this late stage. Retain
the successful six-sink clock grouping, weak NOR4 exclusion and routed repair
passes. Do not alter the library's diode fanout models or waive the warnings.

Antenna checking stays enabled and must report zero violating nets/pins, alongside
zero fanout/slew/capacitance and positive setup/hold. DRC/LVS, precheck and gate
simulation must all pass on this new geometry. A jumper setting alone is not proof
that every antenna violation can be repaired; inspect the actual outcome.

No RTL, PDK revision, electrical limits, clock period, footprint, pin map, reset or
instruction timing changes. Preserve the rejected candidate's reports and cancel
its remaining gate/precheck jobs; they do not validate the next candidate.
