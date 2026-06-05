# Technical Specifications

## Scope

This application is a Flask-based generator for printable t-shirt sublimation badge templates. It discovers badge artwork, lets users choose layout options, renders an SVG preview, and exports a print-ready PDF.

## Runtime Stack

- **Language:** Python 3.
- **Web framework:** Flask.
- **PDF rendering:** ReportLab.
- **SVG to PDF rendering:** svglib with ReportLab graphics.
- **Raster image rendering:** Pillow-backed ReportLab image readers.
- **HTTP client:** requests for upstream badge discovery and PDF asset fetching.
- **Frontend:** Server-rendered Jinja templates, plain CSS, inline browser JavaScript for dynamic controls and manual preview placement.

## Application Entry Points

- `tshirt_templates/app.py` exposes `create_app()` and module-level `app`.
- `templates/index.html` renders the generator form.
- `templates/preview.html` renders the SVG preview and manual placement form.
- `static/styles.css` defines the MakeSpace-inspired black/yellow monospace UI theme and global styling.

## HTTP Routes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Render the template generator form with available badges and default options. |
| `POST` | `/refresh` | Clear the in-process upstream badge cache, then redirect to `/`. |
| `GET` | `/uploads/<filename>` | Serve locally uploaded badge artwork from the configured upload folder. |
| `POST` | `/preview` | Parse form options, save any uploads, compute layouts, apply optional manual placement fields, and render an SVG preview. |
| `POST` | `/pdf` | Parse form options, save uploads, compute/apply layouts, and return a generated PDF download. |
| `GET` | `/api/v1/health` | Return service health as JSON. |
| `GET` | `/api/v1/options` | Return option values and defaults as JSON. |
| `GET` | `/api/v1/badges` | Return available badges as JSON. |
| `POST` | `/api/v1/layouts/preview` | Compute layouts from a JSON request. |
| `GET` | `/mcp` | Return MCP endpoint metadata. |
| `POST` | `/mcp` | Handle initial MCP JSON-RPC methods and tool calls. |

## Badge Sources

### Upstream Repository

Badge discovery reads the recursive tree for `makespacemadrid/open-badges` from GitHub. Supported upstream extensions are:

- `.svg`
- `.png`
- `.jpg`
- `.jpeg`

Discovered upstream badges are normalized into `Badge` records containing:

- `id`: stable selection key, currently the repository path.
- `name`: human-readable title derived from the file name.
- `path`: source repository path.
- `raw_url`: direct raw asset URL.
- `extension`: lowercase file extension.
- `local_path`: `None` for upstream assets.

### Cache Behavior

Badge discovery is cached in process for ten-minute buckets. The refresh route clears the cache explicitly so the next request fetches the current upstream tree.

### Fallback Badge

If upstream discovery fails or returns no supported images, a built-in demo SVG badge is used so the UI and PDF workflows remain available.

### User Uploads

Uploaded badge artwork is saved under Flask's configured upload folder, which defaults to `instance/uploads`. Uploads are accepted for SVG, PNG, JPG, and JPEG images. Uploaded badges use `upload:` IDs and local file paths for PDF rendering.

## Layout Model

### Units

The PDF/layout engine stores geometry in PDF points. UI-facing size and spacing options can be selected in centimeters or inches. Parsed values are converted to inches, then to points at 72 points per inch for layout calculations.

Manual preview coordinates are displayed in the selected UI unit and converted back to PDF points before PDF rendering. The optional MakeSpace Madrid logo uses the same selected unit for its size presets.

### Page Sizes

Supported page sizes are:

| Key | Size |
| --- | --- |
| `a4` | A4, default |
| `a3` | A3 |
| `letter` | US Letter |

Both portrait and landscape orientations are supported. Landscape swaps the long and short page sides.

### Panels

Users may select front, back, or both panels. If both panels are selected, the content area is split into two side-by-side panel rectangles with a fixed gap. If no valid side is submitted, the application defaults to both front and back at option-parse time.

### Placement Modes

| Mode | Behavior |
| --- | --- |
| `grid` | Centered rows and columns. |
| `rows` | Staggered rows with alternating horizontal offsets. |
| `diagonal` | Badges placed along a diagonal sash. |
| `scatter` | Deterministic pseudo-random positions and rotations. |
| `circle` | Badges arranged around an oval wreath. |
| `spiral` | Badges trail outward from panel center. |
| `wave` | Badges follow a sine-wave ribbon. |
| `border` | Badges wrap around panel edges. |
| `m-pixels` | Badges fill a pixel-art capital M shape, repeating badges if needed. |

### Optional Logo Element

Users can include the MakeSpace Madrid logo as a supplemental layout element. The logo asset is referenced from `makespacemadrid/makespacemadrid.github.io` at `assets/images/logo/makespace-bk.svg`. When enabled, one logo placement is appended to each selected panel and can be adjusted with the same manual placement controls as badge artwork.

### Badge Ordering

Before layout placement, selected badges can be ordered by:

- Selection order.
- Alphabetical badge name/path.
- Category derived from parent path, then badge name/path.

### Copies

Copies per badge are expanded before placement. Valid values are 1 through 24. The limit keeps generated PDFs and preview layouts practical.

### Manual Placement

The preview screen exposes a coordinate/rotation table and draggable SVG elements. Manual fields use this naming convention:

```text
manual_{layout_index}_{placement_index}_x
manual_{layout_index}_{placement_index}_y
manual_{layout_index}_{placement_index}_rotation
```

- `x` and `y` are top-left preview coordinates in the selected unit.
- `rotation` is degrees clockwise as displayed in the preview form.
- Missing manual fields leave the automatic placement unchanged.
- Invalid numeric values fall back to the automatic placement value.

## PDF Rendering

PDF rendering receives the resolved badges, page size, panel layouts, and mirror flag. The renderer:

1. Creates a ReportLab canvas.
2. Mirrors the canvas horizontally when requested for sublimation transfer.
3. Draws dashed panel outlines and panel labels.
4. Draws each badge at its placement center with its rotation.
5. Fetches upstream assets on demand or reads uploaded local files.
6. Renders SVG assets through svglib and raster assets through ReportLab image handling.
7. Draws an error placeholder if an asset cannot be fetched or rendered.

## Validation and Defaults

Option parsing is intentionally defensive. Invalid values are normalized to known defaults:

- Page size: `a4`.
- Orientation: `portrait`.
- Placement mode: `grid`.
- Unit: `cm`.
- Badge size: `3.5 cm`.
- Spacing: `0.5 cm`.
- Logo inclusion: disabled.
- Logo size: `5.0 cm`.
- Copies: clamped to 1–24.
- Order: `selected`.
- Mirror: enabled by default.

Size and spacing use preset selector values instead of arbitrary numbers. Presets are chosen to represent common print/cut sizes, maintain badge legibility, and avoid layouts that are too dense or wasteful.

## API and MCP Serialization

The initial API implementation serializes badges, panel layouts, and placements with both selected display units and raw PDF point values. JSON layout requests also accept optional manual placement overrides addressed by layout and placement indexes. The MCP endpoint reuses the same serializers through `get_options`, `list_badges`, and `compute_layout` tools.

## Testing Strategy

The test suite covers:

- Badge discovery, fallback, upload acceptance, and ordering helpers.
- Option parsing, defaulting, validation, and unit conversion.
- Layout page sizes, orientation, placement bounds, copies, and layout modes.
- Flask route rendering for index, preview, refresh, uploads, and PDF download behavior.
- Manual coordinate conversion into PDF layout placements.

Run:

```bash
pytest -q
python -m compileall tshirt_templates
```

## Current Non-Goals

- Persistent server-side template storage.
- Public JSON API endpoints.
- Multi-page PDF output.
- Authentication or multi-user authorization.
- Real-time collaboration.
- Server-side browser automation for preview screenshots.
