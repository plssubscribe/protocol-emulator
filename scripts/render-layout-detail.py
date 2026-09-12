"""Render a close view directly from the 8x2 preview GDS using KLayout 0.29.12.

Usage: python scripts/render-layout-detail.py INPUT.gds OUTPUT.png
This is a geometry render, not an edited or generated illustration.
"""
import sys
import klayout.db as db
import klayout.lay as lay

view = lay.LayoutView()
view.load_layout(sys.argv[1], 0)
view.max_hier()
if len(sys.argv) > 3:
    view.load_layer_props(sys.argv[3])
view.set_config('background-color', '#101722')
view.set_config('grid-visible', 'false')
view.set_config('text-visible', 'false')
view.save_image_with_options(sys.argv[2], 1800, 900, 0, 2, 0,
                             db.DBox(80, 244, 230, 319), False)
