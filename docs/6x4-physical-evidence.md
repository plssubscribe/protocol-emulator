# Integrated CMOS5L 6x4 physical build

Built 2026-09-16; artifacts reviewed 2026-10-04. Footprint decision: ADR 0009.

The complete Protocol Witness design fits the approved 6x4 footprint. GDS,
Tiny Tapeout precheck and post-route functional gate simulation passed. Setup
and hold meet the unchanged 20 ns target at the reported corners. **Electrical
cleanup remains: four max-slew and 131 clock-buffer max-fanout violations.**
A successful workflow is not complete fabrication signoff.

![Actual integrated Protocol Witness layout](images/witness-cmos5l-6x4.png)

This is the unmodified upstream render of the final GDS, 12893 × 7107 pixels.
It includes the programmable core, host SPI, timed input capture and diagnostic UART.
It replaces the UART-only 8x2 preview as the current design's layout evidence.

## Build provenance

The organizer email supplied by the user and the public rules checked on
2026-09-16 approve 6x4 development. Future 8x4 support is not assumed.
Source commit: `56cdac9b58f84fa753991a0e62f1edf62a88b13b`, branch `codex/physical-6x4`.
Pins, reset semantics, instruction timing and the 20 ns/50 MHz target are unchanged.

- [Physical workflow](https://github.com/plssubscribe/protocol-emulator/actions/runs/35086370645): GDS, precheck and gate test passed.
- [RTL/generic regression](https://github.com/plssubscribe/protocol-emulator/actions/runs/35086370662): passed.
- [Documentation workflow](https://github.com/plssubscribe/protocol-emulator/actions/runs/35086370641): passed.

Bounds: `0 0 1289.28 710.64` µm. Floorplan DEF SHA256:
`b46d9a0ee8352160e48dbc8312f092f985629061df736c7f46d58686535a76f4`.
Action revision: `45187a61556e197732a236b3f56acd2c800b9e0e`.
Support-tools revision: `da63c9927411e3aca350977d653d24bbf5bca972`.
Precheck used its default branch, which resolved to this same revision; the workflow
now pins it explicitly. LibreLane: 3.0.0rc1. Parent IHP-Open-PDK revision:
`0dedf265f0cad6ef81aeb64b9ddd17eef88c0460`.
The installer compatibility repair preserves standalone CMOS5L revision
`ae7613984daf3ac2b14897321399df497278068f`.

## Reported results

| Check / metric | Integrated 6x4 result |
| --- | --- |
| Functional/buffer standard cells | 12,773 |
| Summed functional/buffer cell area | 229,714 µm² (0.230 mm²) |
| Core area / standard-cell utilization | 902,417 µm² / 25.4554% |
| Filler/decoupling cells | 59,045 |
| Worst setup / hold slack | +8.846085 ns / +0.129633 ns |
| Setup / hold violations | 0 / 0 |
| Routed / Magic DRC errors | 0 / 0 |
| LVS errors | 0 |
| Antenna net / pin violations | 0 / 0 |
| Maximum capacitance violations | 0 |
| Maximum slew / fanout violations | **4 / 131** |
| Gate-level functional tests | 8 groups passed, 33.80604 ms simulated |
| Tiny Tapeout precheck | All 9 listed checks passed |

Physical cell area includes CTS and repair cells; it is distinct from the earlier
0.164 mm² library-only mapping. Total filled instance area is not functional area.

| Nominal-RC library corner | Setup slack (ns) | Hold slack (ns) | Max slew violations |
| --- | ---: | ---: | ---: |
| Fast, 1.32 V, −40 °C | 12.997927 | 0.129633 | 0 |
| Typical, 1.20 V, 25 °C | 11.442521 | 0.329459 | 0 |
| Slow, 1.08 V, 125 °C | 8.846085 | 0.677555 | 4 |

Final SDC specifies 20 ns, 0.25 ns clock uncertainty and 4 ns input/output delays.
These inherited constraints are not measured external host or board timings.
The final STA reports 107 unannotated drivers per corner, zero after the flow's
filtering. The machine-readable record preserves these counts and converts the
fast corner's nonfinite register-to-register setup metric to null, not a pass.

## Behavior and geometry checks that ran

Gate simulation used Icarus 13 with CMOS5L functional models and the post-route
netlist, without SDF delay annotation. The eight groups cover diagnostic UART,
host load/execute/readback, corrupt frames/abort/reset, synchronized input and
atomic snapshots, capture overflow, the full I2C stretch sweep/replay, SPI all
four modes/replay, and unknown SPI response capture. Timing comes from separate
STA, not from this functional simulation.

Separate precheck passed KLayout pin labels, SG13CMOS5L DRC, zero-area and general
checks, plus pin, boundary, layer, cell-name and analog-pin checks. Routed DRC,
Magic DRC, LVS and antenna checks also ran. In-flow KLayout DRC and Magic/KLayout
XOR remained disabled; equivalence checking was skipped.

## Remaining cleanup and limits

The slow-corner slew violations are four pins on a single net driven by
`_09307_/Y` (`sg13cmos5l_nor4_1`): driver plus `fanout534/A`, `fanout535/A` and
`fanout537/A`. Worst transition is 2.561762 ns against a 2.507400 ns limit.
The net appears in the worst setup path from reset into the core. All 131 fanout
violations are clock-tree leaf buffer outputs, with reported limit 8 and loads
11..18. These are actual final-STA reports, not stale synthesis metrics.

Next physical milestone: repair this output transition and clock-tree leaf
loading, then rerun physical timing, DRC/LVS, precheck and gate simulation without
relaxing the clock target or electrical limits. Do not expand the ISA first.

The wire-length checker lacked a configured threshold. IR-drop analysis warned
that voltage-source locations were unspecified. The linter reported 85 warnings.
No FPGA/board capture, measured external timing, silicon testing or exhaustive
manufacturing signoff has occurred.

## Reproducible evidence

[Committed evidence](evidence/physical-6x4-2026-10-04/summary.json) includes source
and artifact SHA256 hashes, exact metrics, corner results and test groups.
The same directory preserves the final SDC, STA summary, electrical violations,
PDK metadata, gate XML and precheck results beyond Actions artifact retention.
Large GDS/netlist artifacts remain under ignored `work/physical/6x4-artifacts/`
and in the linked Actions run.

```sh
python scripts/summarize-physical.py work/physical/6x4-artifacts work/physical/6x4-summary.json
```

The helper reports missing metrics explicitly and never treats missing checks as passes.
