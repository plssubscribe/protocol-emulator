# ADR 0008: Bounded timed input capture

Date: 2026-09-13. Status: accepted for implementation and verification.
Extends ADR 0004 and ADR 0005; all existing legal instructions, commands, timings,
reset semantics and physical assignments remain unchanged.

Add opcode 5 SAMPLE: duration 1..65535, A=input pin index 0..7, B=0,
reserved bits zero. Hold outputs for exactly duration cycles and append the selected
synchronized input bit at the edge ending the final cycle. No early completion.
The next instruction begins immediately under the existing no-fetch-bubble contract.

A 32-bit capture register shifts left and appends each bit at bit 0. A six-bit count
starts at zero. Thus an MSB-first eight-bit transfer occupies bits 7:0 in natural
byte order; LSB-first serial data is reversed by host software. Accepted START and
reset clear data/count. Idle writes, HALT, EXPECT timeout and abort preserve them;
abort/reset take precedence over a same-edge sample. The 33rd SAMPLE waits its
specified duration then terminates with status 5, preserves all first 32 bits,
records that SAMPLE's PC/word/observed input/duration, and releases outputs. No
rolling overwrite, backpressure, implicit pause or automatic draining.

SNAPSHOT (80) now also freezes page 3 on the same edge as existing pages. Command
83, payload zero, returns {reserved[1:0]=0, count[5:0], data[31:0]}. It is
non-destructive, initially zero, and stable across subsequent runs until SNAPSHOT
or reset. Existing response revision 1 and pages remain compatible; new software
must explicitly opt into page 3 and handles rejection by older hardware. The host
API exposes `snapshot(capture=True)`; its default preserves existing callers.

This bounded run buffer provides useful unknown-byte reception without committing
to FIFO servicing, streaming, or larger memory. It costs 38 core state bits plus
40 snapshot bits and decode/control logic, to be measured by synthesis. Generic
counts do not establish mapped area or timing. Memory depth, 20 ns clock target,
CMOS5L, 8x4 allocation and Tiny Tapeout ports are unchanged.

Acceptance: model/RTL agreement across all input selections and timed samples;
32/33-bit boundary, abort/reset precedence, run clearing and sticky results;
atomic page readback across another run; unknown SPI responses in all four modes;
full legacy regression, generic synthesis/netlist checks and bounded safety checks.
SPI sampling still checks a settled level after synchronization, not raw pad-edge
capture. Multi-byte programs and continuous host-drained RX remain future work.
