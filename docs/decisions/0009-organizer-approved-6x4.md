# ADR 0009: Adopt the organizer-approved CMOS5L 6x4 footprint

Date: 2026-09-16. Status: accepted.

The user provided Anish Singhani's reply confirming that 8x4 support is not yet
available and recommending 6x4 development. The official competition page, checked
2026-09-16, now explicitly requires 6x4 and describes 8x4 as a possible future
expansion. This supersedes the footprint requirement in ADR 0001 and subsequent
ADRs that preserved 8x4. Historical build records remain historical.

Set canonical `info.yaml` to 6x4. Use the existing CMOS5L 6x4 size and DEF from the
pinned support package. Keep the 20 ns/50 MHz target, CMOS5L process revision,
Tiny Tapeout pin assignment, reset, program depth and instruction timing unchanged.
Do not assume 8x4 will become available or rely on its extra area.

Run the complete current integrated design through the physical workflow. Reuse
the previously verified pinned-action installer repair for the duplicate process
checkout; it preserves the standalone process revision. Pin support-tools and the
GDS/precheck/gate-test action consistently. Keep the historical 8x2 preview manual
only. Do not publish a chip viewer as part of this characterization run.

Record source commit and which physical checks ran. Existing library mapping and
functional simulation establish neither fit nor timing closure. Investigate any
area, congestion, timing or physical-rule failures before altering architecture.

Source: https://blog.janestreet.com/protocol-emulator-asic-competition/
Organizer email was supplied by the user in this task on 2026-09-16.
