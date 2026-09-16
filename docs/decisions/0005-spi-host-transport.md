# ADR 0005: Framed SPI host transport and Tiny Tapeout integration

Date: 2026-09-13. Status: accepted for RTL integration, pending physical checks.
Supersedes ADR 0001's unused-input/output assignment only after explicit unlock;
ADR 0004 still defines the instruction timing and core reset semantics.

## Pins and startup

Keep the Tiny Tapeout interface, CMOS5L, 8x4 and 50 MHz/20 ns target. Output 0
continues the original repeating-UART diagnostic, including during host operation.
After reset the host is locked and all other outputs/enables stay zero. Unlock is
a deliberate valid packet, not a boot strap; random input activity remains part of
the UART regression. Reset clears unlock, parser state, program and witness.

| Pin | Use |
| --- | --- |
| ui[0] | Host SPI clock |
| ui[1] | Host MOSI |
| ui[2] | Host CS_N |
| ui[7:3] | Unused |
| uo[0] | Original UART diagnostic |
| uo[1] | Host MISO, zero while locked or CS_N inactive |
| uo[2] | Core running, zero while locked |
| uo[3] | Core done, zero while locked |
| uo[4] | Sticky host packet error, zero while locked |
| uo[7:5] | Zero |
| uio[7:0] | Eight programmable protocol pins |

Protocol pin output value/enables are zero while locked. After unlock they are the
core's registered outputs. Each protocol input has two sampling flip-flops. An
external level stable before edge N reaches the second stage at N+1 and is consumed
by the core at N+2. This is the nominal digital latency, not a metastability bound;
software timing must allow uncertainty around asynchronous edges. No input bypass.

## Host electrical timing

SPI mode 0, MSB first, exactly 64 clock pulses per CS_N assertion. Synchronize
CS_N, clock and MOSI through two flip-flops and detect edges in the system-clock
domain; no derived clock. Hold each SCLK half-period and CS setup/hold/inactive
interval at least four system clocks (80 ns at the target clock). MOSI changes on
falling SCLK and is held through the following rising edge; read MISO on rising
SCLK. Maximum recommended host clock is f_sys/8 (6.25 MHz only if 50 MHz closes).
Reset with host CS_N high and SCLK low. Timing violations are unsupported.

## Request/reply framing

Request: byte 0 = A7; byte 1 = command; bytes 2..6 = 40-bit payload, big endian;
byte 7 = CRC-8 over bytes 0..6, polynomial 07, initial zero, non-reflected, xorout 0.
CRC updates serially as the first 56 request bits arrive. Commit only after CS_N
rises with exactly 64 samples, matching magic and CRC. Short/long/bad frames never
write program memory or start the engine.

Response: byte 0 = 5A; byte 1 = result code; bytes 2..6 = payload; byte 7 = same CRC.
Each transfer returns the response to the **previous** frame, snapshotted on CS_N
falling. Send NOP to retrieve a response. The unlock frame returns zeros because
MISO is locked; its response is available on the next frame.

| Command | Payload/action |
| --- | --- |
| 00 NOP | Payload zero; reply payload 0000000001 (transport revision) |
| 01 UNLOCK | Payload 5749544E53 (ASCII WITNS); enable host/protocol pins |
| 20..3F WRITE | Address = command low five bits; payload = one instruction word |
| 40 START | Payload zero; start PC 0 if idle |
| 60 ABORT | Payload zero; stop if running, otherwise no effect |
| 80 SNAPSHOT | Payload zero; snapshot terminal fields and return page 0 |
| 81 PAGE1 | Payload zero; return previously snapshotted page 1 |
| 82 PAGE2 | Payload zero; return previously snapshotted page 2 |

Only UNLOCK is actionable while locked. Unsupported commands/payloads fail. WRITE
and START while busy fail; there is no queued write/start. A complete accepted
packet produces a one-cycle internal command strobe, consumed by the core on the
following rising edge. ABORT does not stop reception of host packets.

Result codes: 0 success, 1 checksum/magic, 2 frame length, 3 busy, 4 invalid command
or payload. After unlock any error sets a sticky host_error output until reset.
Protocol timeout is separate: it appears in the core status, not host_error.

## Atomic snapshot

SNAPSHOT copies pages 1 and 2 on one system edge and replies with page 0 from that
same edge. The host must check page 0's done flag before treating the other pages
as a completed run. Later core completion/start cannot tear the stored pages.

Page 0: top byte bits 7=unlocked, 6=host_error, 5=time_wrapped, 4=running, 3=done,
2:0=core status; lower 32 bits=terminal cycle.
Page 1: byte 0=zero-extended PC, byte 1=observed pins, bytes 2..3=samples, byte 4=0.
Page 2: complete 40-bit terminal instruction. Pages initially zero after reset.

## Acceptance and limitations

Test only public Tiny Tapeout pins: unlock, load, execute, wait for synchronized
input, capture/read all witness pages, reload different output programs, abort,
reset, busy rejection, bad CRC, truncated/overlong packets and snapshot stability.
Retain the original UART pin regression. Re-run standalone core, mutation and
formal checks; synthesize the integrated top separately before claiming area.
CRC detects many transmission errors, not every possible corruption or intentional
command. No source authentication is intended. No physical host adapter, board
capture or timing/CDC signoff is implied by simulated SPI transactions.
