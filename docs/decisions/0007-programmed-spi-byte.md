# ADR 0007: Programmed SPI controller byte with known-response checks

Date: 2026-09-13. Status: accepted for firmware and simulation.

Use 28 existing instructions to transmit one MSB-first byte and check one configured
response byte in each CPOL/CPHA mode. Firmware assigns uio[0:3] to SCLK, MOSI,
CS_N and MISO respectively; only the first three are driven. These are assignments
within the existing programmable bus, with no physical pin-map or RTL change.
The independent host SPI transport continues to load programs and read witnesses.

Each bit uses two DRIVE instructions and one one-cycle EXPECT. The EXPECT occupies
the last cycle of the sampling half-period; it checks a stable response level after
the existing input synchronization delay. It does not capture arbitrary received
data and is not an edge-triggered SPI receiver. Half-periods below four system
cycles are rejected by the compiler. This digital minimum is not a characterized
board speed or an electrical setup/hold guarantee.

An edge-driven target fixture knows only the mode, response and actual protocol
lines. It samples MOSI on the mode's sample edges and shifts MISO on the other edges.
Tests check eight transmitted bits, sixteen clock transitions, uniform half-periods,
normal completion, and first-failure readback for an inverted fourth response bit.
Reload serialized words and compare the entire trace and witness using a fresh peer.
This deliberately corrupted byte is a response-integrity demonstration, not yet
the SPI timing-defect experiment requested by ADR 0003.

No new data path, multi-byte transaction, target-mode firmware, analog model or
third-party interoperability claim. PDK, clock target, reset, ISA timing and 8x4
allocation remain unchanged. Physical checks remain separate.
