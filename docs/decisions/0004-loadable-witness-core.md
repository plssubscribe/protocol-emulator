# ADR 0004: Loadable timing and witness core, revision 1

Date: 2026-09-12. Status: accepted for standalone RTL milestone.

## Scope and hardware boundary

Implement `witness_core` as a separately tested synthesizable core. Keep the M1
Tiny Tapeout top and pin map unchanged until a physical host transport is designed.
The core has a synchronous internal load port, not a board-ready host connection.
Inputs are already synchronized to `clk`; the future pad adapter must provide and
specify synchronization latency. There are no derived clocks. Reset is synchronous
active-low, aborts execution and invalidates all instruction slots. Memory contents
need not reset because an invalid slot cannot execute or drive outputs.

Use 32 x 40-bit flip-flop-backed words with asynchronous read as an initial
measurement point. This is deliberately provisional, not a size justified by PDK
area. No SRAM macro or PDK change is implied. Read timing and mux area need synthesis
and subsequent physical evaluation before integration.

## Loader and lifecycle

On a rising edge with `load_valid && load_ready`, atomically write `load_word` at
`load_addr` and mark that slot valid. `load_ready` is true only when idle, reset is
released and abort is low. Loading has priority over start; a concurrent start is
ignored. Start is accepted while idle with no load or abort; PC and timestamp reset
to zero and the previous witness clears. Program persists across runs, not reset.
Loads and starts while running are ignored. Abort during execution stops at the
next rising edge, releases output enables and records status 4. Reset dominates all.

A program must contain an explicit HALT or jump. PC increments modulo 32; wrapping
is intentional and can be used as a loop. Invalid slots fault. A looping program
has no implicit watchdog; host abort is available. The first terminal record remains
stable until the next accepted start or reset, including during idle memory writes.

## Instruction word

Bits 39:36 opcode; 35:32 reserved zero; 31:16 duration; 15:8 A; 7:0 B.

| Opcode | Name | Operands |
| --- | --- | --- |
| 0 | HALT | all lower bits zero |
| 1 | DRIVE | duration 1..65535, A=value, B=enable |
| 2 | EXPECT | duration 1..65535, A=expected, B=nonzero mask; A & ~B = 0 |
| 3 | WAIT | duration 1..65535, A=B=0; retain output state |
| 4 | JMP | duration=A=0, B=target 0..31 |

Other encodings fault. Programmer tools reject invalid fields before emission; RTL
also checks words because the loader is not trusted to validate them.

## Clock contract

An accepted start launches cycle 0 immediately after that rising edge. DRIVE output
value and enable are registered on the edge launching the instruction; a peer's synchronous input is sampled at the rising edge ending that cycle.
Each DRIVE/WAIT consumes exactly duration cycles; EXPECT consumes 1..duration
samples, matching on its final sample before timeout takes precedence. Consecutive
instructions have no fetch bubbles. JMP consumes one cycle retaining outputs. HALT
and malformed/uninitialized words release enables on entry and retire in one cycle.
On timeout, enables release at the boundary after the final mismatching sample.

This preserves ADR 0003 DRIVE/EXPECT timing. Explicit HALT adds one released-output
cycle to the RTL run versus the implicit end of the software list. The new binary
model specifies WAIT/JMP, execution faults, wrap and terminal status as well.

A combinational successor read prepares registered outputs and latches the active
instruction without adding a fetch bubble. Keeping the active word in a register
avoids a second instruction-memory read mux. Both output value and enable change only on rising edges. The extra read
mux/decode path must meet the unchanged 20 ns target; generic synthesis cannot
establish that. An initial unregistered implementation was superseded during this
milestone, before external pin integration.

## Witness and safety

`done` is sticky after any termination; `status`: 0 HALT, 1 timeout, 2 illegal word,
3 invalid slot, 4 abort. Capture terminal PC, 32-bit zero-based cycle timestamp,
current word, observed input byte and samples consumed in the current instruction.
Abort records zero samples. Timestamp wraps modulo 2^32 with a sticky `time_wrapped`
flag (cleared on start/reset); consumers must not interpret it as unbounded time.
All output enables are zero when idle, on HALT or invalid instruction. DRIVE can
request push-pull behavior; open-drain programs must set output value zero and toggle
enables. The core alone provides no analog voltage compatibility or contention
protection. Terminal record registers are internal readback signals, not serialized
host readback yet.

## Acceptance

Cycle comparisons with a separately written binary interpreter; randomized loaded
programs; original semantic-model agreement for DRIVE/EXPECT; independent UART
wire oracle; inclusive deadline, loader races, reset, abort, illegal/uninitialized
instructions, maximum duration and looping tests. The synthetic timing sweep must
run through RTL and export a replayable witness. Mutation checks must demonstrate
that broken deadlines/output enables are detected. Report generic synthesis as
such; it cannot establish CMOS5L area or 50 MHz timing closure.

## Verification follow-through

The standalone RTL now has six simulation groups, four targeted mutation checks,
and six bounded public-interface safety properties. The formal harness assumes
one initial reset and checks 12 steps; timeout reachability is checked separately.
Generic synthesis and zero-delay netlist simulation pass. The evidence report
records exact scope and generic counts; none substitutes for CMOS5L mapping.
