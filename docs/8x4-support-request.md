# Draft upstream support request: CMOS5L 8x4 floorplan

Historical draft. Resolved by the organizer response supplied on 2026-09-16:
use 6x4 now; see ADR 0009. Do not send this superseded request.

The protocol-emulator competition template requests `tiles: "8x4"` with
`pdk: ihp-sg13cmos5l`, but the action's selected support-tools revision rejects
that size before synthesis.

Rechecked 2026-09-14:

- `TinyTapeout/tt-gds-action@ihp-cmos5l` resolves to
  `45187a61556e197732a236b3f56acd2c800b9e0e`.
- Its selected `htfab/tt-support-tools@cmos` resolves to
  `da63c9927411e3aca350977d653d24bbf5bca972`.
- `tech/ihp-sg13cmos5l/tile_sizes.yaml` has no `8x4` entry.
- `tech/ihp-sg13cmos5l/def/tt_block_8x4_pgvdd.def` is absent.
- Metadata validation reports `Invalid value for 'tiles' in 'project' section: 8x4`.

Could you point us to the accepted CMOS5L 8x4 size/DEF package and the matching
support-tools/action revisions? We are retaining the required 8x4 metadata and
have not substituted a Sky130 floorplan or reduced the competition footprint.

Minimal configuration:

```yaml
project:
  tiles: "8x4"
```

```yaml
- uses: TinyTapeout/tt-gds-action@ihp-cmos5l
  with:
    pdk: ihp-sg13cmos5l
```

The missing support package is independent of the RTL. A separate historical
UART-only 8x2 preview passed, but does not resolve the competition-size issue.
Current integrated RTL has been mapped locally to the pinned CMOS5L standard-cell
library; full implementation awaits the supported footprint.

References:

- https://blog.janestreet.com/protocol-emulator-asic-competition/
- https://github.com/htfab/tt-support-tools/blob/da63c9927411e3aca350977d653d24bbf5bca972/tech/ihp-sg13cmos5l/tile_sizes.yaml
- https://github.com/htfab/tt-support-tools/tree/da63c9927411e3aca350977d653d24bbf5bca972/tech/ihp-sg13cmos5l/def
