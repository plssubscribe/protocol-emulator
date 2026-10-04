# ADR 0011: Avoid the weak NOR4 mapping that failed routed slew

Date: 2026-10-04. Status: accepted for a second physical characterization.

ADR 0010's build, source `689f55a3422bdb1c4a27d1a338fb165d481c59d8`, eliminated
all 131 fanout violations. Setup/hold remain positive, and route/Magic DRC, LVS
and antenna counts are zero. Four slow-corner slew violations remain on the
same nor4-driven net: worst 3.036714 ns against the unchanged 2.507400 ns limit.
The post-GRT repair log reports zero resized cells and zero inserted buffers;
its estimates did not trigger a repair of the eventual extracted violation.
The stricter acceptance job correctly fails this candidate.

Keep six-sink CTS groups and the routed repair/timing passes. Add precisely
`sg13cmos5l_nor4_1` to `EXTRA_EXCLUDED_CELLS`. This design-specific, additive
exclusion prevents the weak four-input NOR implementation in synthesis and PnR,
allowing the mapper to choose the library's stronger NOR4 or equivalent logic.
The first candidate used 50 instances of this weak cell, so this affects a small
cell class rather than excluding all small gates. Measure actual area and timing
rather than assuming the remapped design is clean.

Do not alter the PDK files or their exclusion lists. LibreLane 3.0.0rc1 explicitly
unions EXTRA_EXCLUDED_CELLS with those lists. Update the local library mapping
helper to honor the same additive exclusions and record its config hash.

No RTL, ISA, clock period, library electrical limit, reset, instruction timing,
physical pin map, program depth or approved footprint changes. Repeat full physical
implementation, strict electrical acceptance, gate simulation and precheck. Retain
first-attempt evidence; checks on its electrically failing design do not validate
the replacement. Cancel unfinished checks on the rejected candidate to avoid
spending compute on a design we will not accept.
