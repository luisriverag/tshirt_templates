# Screenshot Artifacts

This repository provides deterministic screenshot renderers for UI changes that need visual review when a browser binary is unavailable in the execution container. Generated PNG files are intentionally ignored and should not be committed.

## Upload notices

Generate the upload-notice screenshot locally with:

```sh
python scripts/render_upload_notice_screenshot.py docs/screenshots/upload-notices.png
```

The generated screenshot shows the upload validation notice panel used when SVG/raster validation succeeds with non-fatal dimension warnings.

## Preview snap controls

Generate the preview snap-controls screenshot locally with:

```sh
python scripts/render_preview_controls_screenshot.py docs/screenshots/preview-snap-controls.png
```

The generated screenshot shows the preview toolbar controls for zoom, snap-to-grid, snap-to-panel-edge placement, and high-contrast preview outlines.


## Alignment tools

Generate the alignment-tools screenshot locally with:

```sh
python scripts/render_alignment_tools_screenshot.py docs/screenshots/alignment-tools.png
```

The generated screenshot shows the manual preview multi-select, alignment, and distribution toolbar used to move or line badges up within each panel.

## Curve controls

Generate the curve-controls screenshot locally with:

```sh
python scripts/render_curve_controls_screenshot.py docs/screenshots/curve-controls.png
```

The generated screenshot shows the mug/canteen curved-adapter device preset, diameter input, and enable checkbox.
