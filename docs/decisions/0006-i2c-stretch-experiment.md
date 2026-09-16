# ADR 0006: I2C address-probe failure experiment without new RTL

Date: 2026-09-13. Status: accepted for firmware and verification milestone.

## Decision and scope

Use the existing 32-word ISA to implement a programmable I2C target that validates
one configured address/RW byte, stretches the first SCL-low phase, and acknowledges
that byte. Pair it with an independently written digital controller fixture and a
separate line-transition decoder. All program loading and witness readback use the
public SPI host pins. The controller is project-authored with a deliberate defect;
this is not a bug discovered in third-party hardware or a general I2C IP core.

No RTL, ISA, physical pin assignment, reset, PDK, footprint or clock target changes.
SCL and SDA use uio[0] and uio[1] respectively as a firmware assignment within the
already-programmable protocol bus. Values driven by the program are always zero;
enables pull a line low, and disabled drivers release it. The testbench resolves
both participants with ideal pull-ups and feeds the actual bus back through the
existing two-register input synchronizers. Assert that no unrelated pin or high
push-pull value is driven.

## Firmware and independent observations

The 32 words are: observe START, wait for first SCL low, hold SCL low for a selected
duration (zero disables injection), release SCL, then for each of eight bits wait
for SCL high, check the expected SDA value with a one-sample EXPECT, and wait for
SCL low. Pull SDA low for ACK, wait for its clock rise/fall, then HALT/release. All
EXPECT waits other than bit checks have a 4,096-cycle program deadline. This is an
experiment timeout, not a claimed I2C specification maximum. Program startup waits
long enough for the SPI START acknowledgement to finish before the peer begins.

The controller fixture emits START, eight address bits, an ACK clock and STOP. Its
correct version waits for resolved SCL high before counting the high period. Its
fault-injected version counts that period even while another device holds SCL low.
It does not inspect emulator instructions or internal signals. A separate decoder
observes only resolved bus transitions, checking the byte, ACK and STOP. Its scope
is this address-only transaction, including the controller's final STOP setup
edge; it is not a general multi-byte or repeated-START decoder.

## Experiment and replay

Sweep every integer duration 0..48 with low/high periods of 12 cycles. This is an
accelerated digital regression, not a compliant 2 MHz I2C operating claim. Require
the correct peer to decode A0 (address 50, write), ACK and STOP for every duration;
require both peers to pass without stretching. Report the first failing duration
only within this finite sweep and this fixture timing/phase/address.

Also run correct and faulty peers at low=260, high=240 cycles and stretch=800.
At the unchanged 50 MHz target these nominal periods give 100 kHz. Ideal pull-ups
omit rise/fall time, so this is still not an electrical compliance test. Save the
program, parameters, resolved line trace and host-read witness, reload the saved
words and replay against a fresh peer. Compare trace and witness exactly.

This consumes the entire current instruction store. It is useful evidence for
memory/ISA planning, not a reason to silently increase memory depth. Data payloads,
read responses, general RX capture, repeated START, arbitration and stuck-bus
recovery remain separate milestones. An address probe is not a complete I2C stack.

## Specification basis

NXP UM10204 Rev. 7.0, sections 3.1.1, 3.1.9 and 3.1.10: open-drain resolution,
holding SCL low to pause a transfer, and the seven-bit address plus R/W bit.
Clock-stretch handling is optional when no attached target can stretch; the
fault is evaluated in a configuration that explicitly requires stretching support.
Source checked 2026-09-13: https://www.nxp.com/docs/en/user-guide/UM10204.pdf

No new physical checks are implied. Reuse the unchanged source's generic netlist
for representative replay, and keep full RTL sweep results separate from any
smoke subset used on that netlist.
