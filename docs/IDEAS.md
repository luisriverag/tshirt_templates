# Ideas and Potential Improvements

## User Experience

- [x] Add a reset button on the preview screen to discard manual placement edits and return to the automatic layout.
- [x] Add keyboard nudging for selected preview badges with fine/large step sizes.
- [x] Add snap-to-grid controls for manual preview placement.
- [x] Add snap-to-panel-edge controls.
- Add multi-select movement so several badges can be dragged together.
- [x] Add visual collision warnings when badges overlap.
- [x] Add panel zoom controls for detailed manual placement.
- [x] Add a print calibration page with ruler marks and mirror warnings.
- Add a simple onboarding guide explaining sublimation mirroring and cut spacing.

## Layout and Geometry

- [x] Add rotation presets for manual placement.
- Add alignment tools: center horizontally, center vertically, distribute evenly, align left/right/top/bottom.
- Add density-aware layouts that automatically shrink spacing to fit selected badges.
- Add support for multi-page layouts when selected badges do not fit comfortably.
- Add optional cut-line outlines around badges.
- Add automatic margin controls per panel and per page.
- Add custom panel templates for sleeves, pockets, and kids/adult shirt sizes.
- Add support for locking individual badges before re-running automatic layout.

## Badge Management

- [x] Add category filters and search in the badge picker.
- [x] Add bulk select/deselect for the currently filtered badge set.
- [x] Add uploaded badge deletion and replacement.
- [x] Add uploaded image dimension/format validation with user-facing warnings.
- Add thumbnail caching for faster badge picker rendering.
- Add metadata tags for upstream badges when the source repository supports them.

## PDF and Print Output

- [x] Add optional crop marks and registration marks.
- Add configurable DPI/rasterization behavior for raster assets.
- [x] Add PDF metadata showing selected layout options.
- Add a non-mirrored proof PDF alongside the mirrored transfer PDF.
- Add export to SVG/PNG for users who want to edit layouts in design tools.
- Add server-side verification that every asset can be rendered before generating the PDF.

## API and Automation

- [x] Expand the initial `/api/v1` JSON endpoints described in `APIDOCS.md` with uploads and PDF rendering.
- [x] Add a CLI command for generating PDFs from a JSON template file.
- Add saved template files for repeatable local workflows.
- [x] Expand the initial MCP tools with upload handling, validation, and PDF rendering.
- Add webhook or scheduled refresh for upstream badge catalog changes.

## Reliability and Operations

- Add structured logging for badge refreshes, uploads, and PDF generation failures.
- Add health and readiness endpoints for container deployment.
- Add upload cleanup jobs for stale local assets.
- Add cache metrics for upstream badge discovery.
- Add rate limiting for upload and PDF generation routes.
- Add stricter PDF asset fetch timeouts and retry policy controls.

## Testing

- Add browser-based tests for drag-and-drop manual placement.
- Add visual snapshot tests for preview layouts.
- [x] Add PDF smoke tests for generated PDF bytes and metadata.
- [ ] Add PDF smoke tests that inspect page dimensions and placement counts.
- Add property-based tests for placement bounds across option combinations.
- Add tests for future JSON API schemas and MCP tool responses.

## Accessibility

- [x] Add ARIA status messages when preview badges are moved.
- [x] Add keyboard-only manual placement workflows for focused preview badges.
- Improve focus styling and tab order in the badge picker.
- Add high-contrast preview outlines.
- Add text alternatives for generated layout summaries.
