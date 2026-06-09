# Ideas and Potential Improvements

This backlog only tracks work that is not already available in the current app. Implemented items have been moved into `README.md`, `docs/SPECS.md`, or `docs/APIDOCS.md`.

## Layout and Geometry

- Add support for multi-page layouts when selected badges do not fit comfortably.
- Add custom panel templates for sleeves, pockets, and kids/adult shirt sizes.
- Add support for locking individual badges before re-running automatic layout.

## Badge Management

- Add thumbnail caching for faster badge picker rendering.
- Add metadata tags for upstream badges when the source repository supports them.

## PDF and Print Output

- Add configurable DPI/rasterization behavior for raster assets.
- Add a non-mirrored proof PDF alongside the mirrored transfer PDF.
- Add export to SVG/PNG for users who want to edit layouts in design tools.
- Add a dedicated print-preview mode that shows guides in the browser without including them in final PDFs.
- Add per-export toggles for curve guides, registration marks, and badge cut-line outlines.
- Add a preflight summary that warns about low-resolution, missing, or transparency-heavy artwork before PDF export.
- Add a compact PDF export option that deduplicates repeated badge artwork across pages.

## API and Automation

- Add webhook or scheduled refresh for upstream badge catalog changes.

## Reliability and Operations

- Add structured logging for badge refreshes, uploads, and PDF generation failures.
- Add upload cleanup jobs for stale local assets.
- Add cache metrics for upstream badge discovery.
- Add rate limiting for upload and PDF generation routes.
- Add stricter PDF asset fetch timeouts and retry policy controls.

## Testing

- Add browser-based tests for drag-and-drop manual placement.
- Add visual snapshot tests for preview layouts.
- Add property-based tests for placement bounds across option combinations.

