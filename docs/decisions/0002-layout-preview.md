# ADR 0002: Build a separate 8x2 CMOS5L layout preview

Date: 2026-09-12. Status: accepted for visualization and early physical feedback.

The user requested a chip layout image after the competition 8x4 build failed.
The selected upstream CMOS5L support package has no 8x4 floorplan. It does have
an 8x2 floorplan. Build the existing UART on that supported footprint in a separate
`layout-preview.yaml` workflow, explicitly labeled as preview only.

The workflow changes the tile value only in its temporary runner checkout.
Committed `info.yaml` and the competition GDS workflow retain 8x4. CMOS5L,
20 ns clock, RTL, logical pin assignments, reset and instruction behavior stay
unchanged. The physical footprint is different, so its results cannot validate
8x4 integration or submission readiness. ADR 0001 still governs the final design.

Pin the preview's GDS action and support-tools revisions for traceability. Run
upstream precheck and gate simulation when a GDS artifact is available. Publish
the actual GDS render, never an illustrative substitute for physical results.
Record which checks ran and any failures separately from the image.

This preview is a runnable learning milestone: it exposes mapped cells, routing
and early timing results while competition floorplan support remains unresolved.
It is not a reduction of the competition's requested tile allocation.
