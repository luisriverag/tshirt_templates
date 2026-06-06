# Ideas and Potential Improvements

This backlog only tracks work that is not already available in the current app. Implemented items have been moved into `README.md`, `docs/SPECS.md`, or `docs/APIDOCS.md`.

## User Experience

- Add multi-select movement so several badges can be dragged together.
- Add a simple onboarding guide explaining sublimation mirroring and cut spacing.

## Layout and Geometry

- Add alignment tools: center horizontally, center vertically, distribute evenly, align left/right/top/bottom.
- Add density-aware layouts that automatically shrink spacing to fit selected badges.
- Add support for multi-page layouts when selected badges do not fit comfortably.
- Add automatic margin controls per panel and per page.
- Add custom panel templates for sleeves, pockets, and kids/adult shirt sizes.
- Add support for locking individual badges before re-running automatic layout.

## Badge Management

- Add thumbnail caching for faster badge picker rendering.
- Add metadata tags for upstream badges when the source repository supports them.

## PDF and Print Output

- Add configurable DPI/rasterization behavior for raster assets.
- Add a non-mirrored proof PDF alongside the mirrored transfer PDF.
- Add export to SVG/PNG for users who want to edit layouts in design tools.
- Add server-side verification that every asset can be rendered before generating the PDF.

## API and Automation

- Add saved template files for repeatable local workflows.
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
- Add PDF smoke tests that inspect page dimensions and placement counts.
- Add property-based tests for placement bounds across option combinations.

