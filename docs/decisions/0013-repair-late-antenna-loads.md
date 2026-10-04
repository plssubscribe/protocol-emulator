# ADR 0013: Repair electrical loads after detailed-route antenna protection

Date: 2026-10-04. Status: accepted for the fourth physical characterization.
Supersedes ADR 0012's jumper-only choice.

The third candidate cleared fanout/slew/capacitance but left eight antenna nets
and twelve violating pins. The second candidate protected every antenna net,
but diode loads added during detailed routing exceeded four data-buffer fanout
limits. Neither candidate is accepted.

Restore normal detailed-route antenna repair, including diodes. Use LibreLane's
native plugin discovery to register `WitnessClassic`, a subclass of the pinned
Classic flow. After its original detailed routing, insert two bounded passes of
post-global-route design repair and detailed rerouting. The design repair sees
existing diode loads, legalizes new buffers and regenerates routing guides; the
rerouter retains antenna repair. This is a characterization strategy, not a
convergence guarantee. Final extracted electrical and antenna metrics must be zero.

Keep every original Classic step, configuration variable and gating rule. Give
added steps their own IDs and explicit enable gates. The project-root plugin is
visible to native Python discovery in both the host and mounted Docker working
directory; no tool package or PDK files are patched for this flow change.
Local validation checks plugin discovery, complete preservation of the original
step sequence, configuration and gates, and the inserted step order. It does not
run OpenROAD or establish physical correctness.

Retain clock grouping and weak NOR4 exclusion. Do not change RTL, library limits,
PDK revision, clock period, footprint, pins, reset or instruction timing. Run full
implementation, strict final acceptance, precheck and gate simulation on the same
candidate. Preserve earlier failures; their incomplete downstream checks do not
validate this geometry.
