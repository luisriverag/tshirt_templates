# API and MCP Planning Documentation

## Running the Unified App/API/MCP Server

Run the browser app, JSON API, and MCP endpoint together with the CLI helper:

```bash
python -m tshirt_templates.cli serve --debug
```

That command starts one Flask development server. The browser UI is available at `/`, the JSON API is available under `/api/v1`, and the MCP JSON-RPC endpoint is available at `/mcp`. Host and port can be customized with `--host` and `--port`; for example, `python -m tshirt_templates.cli serve --host 0.0.0.0 --port 8080`. MCP does not require a specific reserved port; compatibility comes from giving each MCP client a reachable `http://HOST:PORT/mcp` URL. Choose a predictable port only to simplify client configuration, container publishing, firewall rules, or avoiding conflicts with another local service.

The equivalent Flask command is still supported:

```bash
flask --app tshirt_templates.app run --debug
```

## Current API Surface

The app now has the original browser form routes plus an initial JSON API and MCP JSON-RPC endpoint:

| Method | Path | Current Type | Notes |
| --- | --- | --- | --- |
| `GET` | `/` | HTML | Generator form. |
| `POST` | `/refresh` | Redirect | Clears the badge discovery cache. |
| `GET` | `/uploads/<filename>` | File | Serves uploaded artwork. |
| `POST` | `/uploads/delete` | Redirect | Deletes a saved upload from the browser picker. |
| `POST` | `/uploads/replace` | Redirect | Replaces a saved upload from the browser picker. |
| `POST` | `/preview` | HTML | Renders SVG preview from submitted form data. |
| `POST` | `/pdf` | PDF | Returns generated PDF bytes. |
| `GET` | `/calibration.pdf` | PDF | Returns a calibration page with rulers and mirror guidance. |
| `GET` | `/api/v1` | JSON | API discovery metadata, endpoint map, repository documentation path, and MCP connection hints. |
| `GET` | `/api/v1/health` | JSON | Basic service health. |
| `GET` | `/api/v1/ready` | JSON | Readiness check for container or process supervisors. |
| `GET` | `/api/v1/options` | JSON | Supported option values and defaults. |
| `GET` | `/api/v1/badges` | JSON | Available badges with optional refresh/order/logo query flags. |
| `POST` | `/api/v1/uploads` | JSON | Saves multipart badge artwork uploads and returns created badge records. |
| `PUT` | `/api/v1/uploads/<filename>` | JSON | Replaces a saved uploaded badge artwork file by storage filename. |
| `DELETE` | `/api/v1/uploads/<filename>` | JSON | Deletes a saved uploaded badge artwork file by storage filename. |
| `POST` | `/api/v1/layouts/preview` | JSON | Computes layouts from badge IDs and options. |
| `POST` | `/api/v1/pdfs` | PDF | Generates PDF bytes from badge IDs, options, and optional manual placements. |
| `GET` | `/api/v1/templates` | JSON | Lists saved local JSON template files. |
| `POST` | `/api/v1/templates` | JSON | Saves or replaces a named local JSON template file. |
| `GET` | `/api/v1/templates/<name>` | JSON | Reads a saved local JSON template file. |
| `DELETE` | `/api/v1/templates/<name>` | JSON | Deletes a saved local JSON template file. |
| `GET` | `/mcp` | JSON | MCP server metadata. |
| `POST` | `/mcp` | JSON-RPC | Initial MCP methods for initialize, tools/resources listing, and tool calls. |

Browser routes remain the stable user-facing surface. API and MCP endpoints are intentionally marked as initial implementations and may evolve before a formal release.

## Proposed Versioning

Use `/api/v1` for JSON and binary API endpoints.

Design goals:

- Stable request/response schemas.
- Explicit units and page options.
- Reusable layout computation without requiring browser HTML forms.
- Machine-readable errors.
- Compatibility with future MCP tools.

## Proposed Data Types

### Badge

```json
{
  "id": "electronics/example.svg",
  "name": "Example",
  "path": "electronics/example.svg",
  "raw_url": "https://raw.githubusercontent.com/.../example.svg",
  "extension": ".svg",
  "source": "upstream"
}
```

`source` should be one of:

- `upstream`
- `upload`
- `fallback`

### LayoutOptions

```json
{
  "page_size": "a4",
  "orientation": "portrait",
  "mode": "grid",
  "unit": "cm",
  "badge_size": "3.5",
  "spacing": "0.5",
  "page_margin": "1.25",
  "panel_gap": "0.85",
  "include_logo": false,
  "logo_sides": [],
  "logo_size": "5.0",
  "front_logo_size": "5.0",
  "back_logo_size": "5.0",
  "copies": 1,
  "order": "selected",
  "sides": ["front", "back"],
  "mirror": true,
  "include_print_marks": false,
  "include_cut_lines": false,
  "include_curve_effect": false,
  "curve_device": "custom",
  "curve_diameter": "8.0",
  "front_text": "Ada",
  "back_text": "MakeSpace Madrid",
  "text_font": "ubuntu"
}
```

`mode` accepts `grid`, `rows`, `diagonal`, `scatter`, `circle`, `spiral`, `wave`, `border`, `m-pixels`, and `m-pixels-no-shrink`. Use `m-pixels-no-shrink` when badge size must remain fixed and dense M layouts should move overflow badges around the M instead of reducing artwork size.

### Placement

```json
{
  "badge_id": "electronics/example.svg",
  "x": 4.25,
  "y": 6.5,
  "width": 3.5,
  "height": 3.5,
  "rotation": 0,
  "unit": "cm"
}
```

For JSON APIs, coordinates should be represented in the requested unit by default. A debug or advanced response may also include `points` values for precise PDF internals.

### PanelLayout

```json
{
  "side": "front",
  "x": 1.27,
  "y": 1.27,
  "width": 18.46,
  "height": 27.2,
  "unit": "cm",
  "placements": []
}
```

## Implemented `/api/v1` Endpoints

### `GET /api/v1/health`

Returns basic application status.

Response:

```json
{
  "status": "ok",
  "service": "tshirt_templates"
}
```

### `GET /api/v1/ready`

Returns readiness status for process supervisors. The endpoint verifies that the configured upload folder can be created and is a directory. It returns `200 OK` with `status: "ready"` when checks pass and `503 Service Unavailable` with `status: "not_ready"` when a required local dependency is unavailable.

Response:

```json
{
  "status": "ready",
  "service": "tshirt_templates",
  "checks": {
    "upload_folder": "ok"
  }
}
```

### `GET /api/v1/options`

Returns supported option values and defaults.

Response should include:

- Page sizes.
- Orientations.
- Layout modes.
- `layout_mode_details`, including labels/descriptions for each mode. The `m-pixels-no-shrink` entry documents that it preserves badge size and uses fallbacks in this order: one line above the M, lines above and below, square frame, then double-square frame.
- Units.
- Text fonts.
- Curve device presets and preset diameters.
- Badge size presets.
- Spacing presets.
- Copy range.
- Order modes.
- Default option object, including `front_text`, `back_text`, and `text_font`.

Example layout-mode metadata excerpt:

```json
{
  "layout_modes": {
    "m-pixels": "M pixel shape",
    "m-pixels-no-shrink": "M pixel shape (no shrink)"
  },
  "layout_mode_details": {
    "m-pixels-no-shrink": {
      "label": "M pixel shape (no shrink)",
      "description": "Badges fill a fixed-size pixel-art capital M without reducing badge size; overflow falls back to one line above, lines above and below, a square frame, then a double-square frame.",
      "fallbacks": [
        "line-above",
        "lines-above-and-below",
        "square-frame",
        "double-square-frame"
      ],
      "shrinks_badges": false
    }
  }
}
```

### `GET /api/v1/badges`

Returns the available badge catalog.

Query parameters:

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `refresh` | boolean | `false` | If true, clears cache before listing. |
| `source` | string | `all` | Future filter: `upstream`, `upload`, `fallback`, or `all`. |
| `order` | string | `alphabetical` | Catalog display order. |
| `logo_sides` | string or repeated string | none | Preferred way to append the reserved MakeSpace logo badge when one or more values are `front` or `back`. Accepts repeated query values or comma-separated sides. |
| `include_logo` | boolean | `false` | Legacy compatibility flag that also appends the reserved MakeSpace logo badge. Prefer `logo_sides`. |

### `POST /api/v1/uploads`

Accepts multipart artwork uploads using the `uploads` field and returns created badge records. Supported file extensions match the browser uploader: SVG, PNG, JPG, and JPEG. Empty, unsupported, oversized, malformed SVG, and unreadable raster files are ignored; if no files are saved, the endpoint returns a structured `invalid_upload` error. Valid uploads may include non-fatal dimension warnings when dimensions are missing, very small, or very large.

Request:

```text
Content-Type: multipart/form-data
uploads=@team-badge.svg
uploads=@sponsor.png
```

Response (`201 Created`):

```json
{
  "badges": [
    {
      "id": "upload:uuid-team-badge.svg",
      "name": "Team Badge",
      "path": "uploaded/uuid-team-badge.svg",
      "raw_url": "/uploads/uuid-team-badge.svg",
      "extension": ".svg",
      "source": "upload"
    }
  ],
  "warnings": []
}
```

### `PUT /api/v1/uploads/{filename}`

Replaces a saved uploaded badge artwork file in place by storage filename. Submit one multipart file under `upload` (or `replacement_upload` for parity with the browser form). The storage filename stays unchanged so existing `upload:` badge IDs continue to work. Empty, oversized, malformed SVG, and unreadable raster replacements are rejected; valid replacements may include non-fatal dimension warnings.

Request:

```text
Content-Type: multipart/form-data
upload=@updated-team-badge.svg
```

Response (`200 OK`):

```json
{
  "badge": {
    "id": "upload:uuid-team-badge.svg",
    "name": "Team Badge",
    "path": "uploaded/uuid-team-badge.svg",
    "raw_url": "/uploads/uuid-team-badge.svg",
    "extension": ".svg",
    "source": "upload"
  },
  "warnings": []
}
```

### `DELETE /api/v1/uploads/{filename}`

Deletes a saved uploaded badge artwork file by storage filename, for example `uuid-team-badge.svg`. Clients should pass the filename portion of an `upload:` badge ID without the `upload:` prefix. The endpoint rejects path traversal and unsupported extensions, and returns a structured `upload_not_found` error when no matching saved upload exists.

Response (`200 OK`):

```json
{
  "deleted": "uuid-team-badge.svg"
}
```

Future considerations:

- Enforce maximum file count per request.
- Return image dimensions when possible.

### `POST /api/v1/layouts/preview`

Computes layouts without generating a PDF.

Request:

```json
{
  "badge_ids": ["demo-badge.svg"],
  "options": {
    "page_size": "a4",
    "orientation": "portrait",
    "mode": "grid",
    "unit": "cm",
    "badge_size": "3.5",
    "spacing": "0.5",
    "page_margin": "1.25",
    "panel_gap": "0.85",
    "logo_sides": [],
    "logo_size": "5.0",
    "front_logo_size": "5.0",
    "back_logo_size": "5.0",
    "copies": 1,
    "order": "selected",
    "sides": ["front", "back"],
    "mirror": true,
    "include_print_marks": false,
    "include_cut_lines": false,
    "front_text": "Ada",
    "back_text": "MakeSpace Madrid",
    "text_font": "ubuntu"
  },
  "manual_placements": []
}
```

`page_margin` controls the outer content inset, and `panel_gap` controls the space between front/back panels when both are selected. Both use the selected `unit`. `logo_sides` controls MakeSpace logo placement: use `["front"]`, `["back"]`, or `["front", "back"]` to include the logo on those panels; omit it or send an empty array for no logo. The legacy `include_logo: true` option is still accepted and defaults to both logo sides when `logo_sides` is absent. `front_text` and `back_text` are optional short labels rendered on the matching panel. `text_font` accepts the values returned by `/api/v1/options` and defaults to `ubuntu`. `include_curve_effect` adds a cylindrical mug/canteen adapter effect in generated PDFs. `curve_device` may be `custom`, `mug`, `skinny-tumbler`, or `canteen`; `/api/v1/options` returns both `curve_device_options` labels and `curve_device_diameters` preset values. Presets provide a starting diameter, and `curve_diameter` may override it with the exact outside device/heater-adapter diameter in the selected `unit`.

Manual placements are optional. Items are addressed by `layout_index` and `placement_index`, with `x`/`y` supplied in the selected unit from the preview top-left coordinate space.

Response:

```json
{
  "page": {
    "width": 21.0,
    "height": 29.7,
    "unit": "cm"
  },
  "badges": [],
  "layouts": []
}
```

### `POST /api/v1/pdfs`

Generates a PDF from the same JSON layout request shape used by `/api/v1/layouts/preview`. The endpoint applies badge ordering, copies, optional logo placement, optional panel text, manual placement overrides, mirror settings, and optional cylindrical curve compensation for mug/canteen heater adapters. Generated template PDFs do not include automatic panel headers or page numbers. Before rendering, the server verifies that every resolved badge asset can be fetched and parsed by the PDF renderer; by default failures return `422 asset_verification_failed` with per-badge details. Set top-level `allow_partial` to `true` to still receive an `application/pdf` response with failed assets drawn as placeholders and the failure details in the `X-Badgeware-Warnings` response header. Browser form PDF downloads always use this partial-render behavior so one broken remote asset does not block the whole PDF.

Request:

```json
{
  "badge_ids": ["demo-badge.svg"],
  "options": {
    "page_size": "a4",
    "orientation": "portrait",
    "mode": "grid",
    "unit": "cm",
    "badge_size": "3.5",
    "spacing": "0.5",
    "page_margin": "1.25",
    "panel_gap": "0.85",
    "logo_sides": [],
    "logo_size": "5.0",
    "front_logo_size": "5.0",
    "back_logo_size": "5.0",
    "copies": 1,
    "order": "selected",
    "sides": ["front", "back"],
    "mirror": true,
    "include_print_marks": false,
    "include_cut_lines": false,
    "front_text": "Ada",
    "back_text": "MakeSpace Madrid",
    "text_font": "ubuntu"
  },
  "manual_placements": [],
  "allow_partial": false
}
```

Response:

```text
Content-Type: application/pdf
Content-Disposition: attachment; filename=tshirt-badge-template.pdf
X-Badgeware-Warnings: {"asset_failures":[...]}
```

`X-Badgeware-Warnings` is only present when partial rendering was used because at least one asset failed verification.

Job-based generation remains a future option if templates become multi-page or asset-heavy.

### `GET /api/v1/templates`

Lists saved local JSON template files from the configured template folder. Each summary includes the template `name`, timestamps, `badge_count`, and normalized `options` snapshot.

Response:

```json
{
  "templates": [
    {
      "name": "team-shirt",
      "created_at": "2026-06-07T00:00:00Z",
      "updated_at": "2026-06-07T00:00:00Z",
      "badge_count": 3,
      "options": {"sides": ["front"], "mode": "grid"}
    }
  ]
}
```

### `POST /api/v1/templates`

Saves or replaces a named local JSON template file for repeatable local workflows. Template names are storage-safe names with letters, numbers, dots, dashes, or underscores. The saved `template` uses the same request shape as `/api/v1/layouts/preview` and `/api/v1/pdfs`: `badge_ids`, `options`, and optional `manual_placements`.

Request:

```json
{
  "name": "team-shirt",
  "template": {
    "badge_ids": ["electronics/example.svg"],
    "options": {"sides": ["front"], "mode": "grid"},
    "manual_placements": []
  }
}
```

Response (`201 Created`):

```json
{
  "name": "team-shirt",
  "created_at": "2026-06-07T00:00:00Z",
  "updated_at": "2026-06-07T00:00:00Z",
  "template": {
    "badge_ids": ["electronics/example.svg"],
    "options": {"sides": ["front"], "mode": "grid"},
    "manual_placements": []
  }
}
```

### `GET /api/v1/templates/{name}`

Reads one saved template by name. A `.json` suffix is optional in the URL. Unknown or invalid names return a structured `template_not_found` error.

### `DELETE /api/v1/templates/{name}`

Deletes one saved template by name and returns `{"deleted": "name"}`.

## CLI Automation

The CLI can start the unified development server for the browser UI, JSON API, and MCP endpoint:

```bash
python -m tshirt_templates.cli serve --debug
```

The CLI can also generate PDFs from the same JSON request shape accepted by `POST /api/v1/pdfs`:

```bash
python -m tshirt_templates.cli generate-pdf template.json tshirt-badge-template.pdf
```

If the template references uploaded `upload:` badge IDs, pass `--upload-folder` with the folder that contains those files.

## Error Format

Use consistent JSON errors:

```json
{
  "error": {
    "code": "invalid_option",
    "message": "Unsupported layout mode.",
    "field": "mode",
    "allowed_values": ["grid", "rows", "diagonal", "scatter", "circle", "spiral", "wave", "border", "m-pixels", "m-pixels-no-shrink"]
  }
}
```

Suggested status codes:

- `400` for invalid input.
- `404` for unknown badge/template IDs.
- `413` for upload payload too large.
- `415` for unsupported media type.
- `422` for valid JSON that cannot produce a layout or references assets that cannot be rendered.
- `500` for unexpected rendering failures.

## Pending API Implementation Tasks

- Add API-specific validation error objects instead of silently normalizing every invalid value.
- Decide whether the MakeSpace logo is modeled as a reserved badge, separate element, or template decoration in JSON responses.
- Decide whether PDF generation should be synchronous or job-based.
- Decide how uploaded files are authenticated and cleaned up.

## Model Context Protocol (MCP) Implementation

MCP support is implemented at `/mcp` using JSON-RPC-style messages. JSON-RPC errors are returned in an `error` object with HTTP 200 so clients that expect JSON-RPC-over-HTTP semantics can still parse the response body. This section also tracks pending features for future automation and IDE integrations.

### MCP Server Goals

The MCP endpoint lets IDEs, agents, and design tools inspect and generate t-shirt template layouts without manually driving the browser.

The server exposes badge catalog and layout option resources, saved template resources, template preview tools, PDF generation tools, uploaded asset management tools, validation helpers, saved-template tools, and layout-related prompt suggestions.

### MCP Resources

`resources/list` currently returns implemented JSON resources for options, badges, and saved templates. `resources/read` returns one `contents` entry with `mimeType: application/json` and serialized `text`. `resources/templates/list` returns badge-catalog and saved-template URI templates so clients can discover supported resource shapes.

| Resource URI | Status | Description |
| --- | --- | --- |
| `tshirt://options` | Implemented | Current supported options and defaults, matching `/api/v1/options`. |
| `tshirt://badges` | Implemented | Alphabetically ordered available badge catalog. |
| `tshirt://badges{?order,logo_sides,include_logo,refresh}` | Implemented | Resource template for client-selected ordering, preferred `logo_sides` logo inclusion, legacy `include_logo`, and cache refresh. |
| `tshirt://templates` | Implemented | Saved local JSON template summaries. |
| `tshirt://templates/{name}` | Implemented | One saved local JSON template by name. |
| `tshirt://layouts/{id}` | Future | Persisted or temporary computed layout. |
| `tshirt://uploads` | Future | Uploaded artwork metadata. |

Example resource read:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/read",
  "params": {"uri": "tshirt://options"}
}
```

### MCP Prompts

The endpoint responds to `prompts/list` with prompt suggestions and `prompts/get` with a single text message template:

- `design_tshirt_template`: Ask an agent to choose badges/layout options for a described shirt concept.
- `optimize_cut_sheet`: Ask an agent to reduce wasted transfer paper while respecting badge sizes.
- `explain_layout`: Ask an agent to describe why a placement mode was chosen.

### Implemented MCP Tools

#### `list_badges`

Inputs:

```json
{
  "refresh": false,
  "order": "alphabetical",
  "logo_sides": ["front"]
}
```

Outputs a badge list. Preferred `logo_sides` values of `front` and/or `back` append the reserved MakeSpace logo badge so agents can mirror the browser UI. Legacy `include_logo: true` is still accepted for compatibility.

#### `get_options`

Inputs: `{}`

Outputs the same supported options/defaults payload as `/api/v1/options`, plus a text content item for clients that display tool-call summaries. The payload includes `layout_mode_details`, so MCP clients can discover the `m-pixels-no-shrink` mode and its M-overflow fallback order without scraping browser labels.

#### `compute_layout`

Inputs:

```json
{
  "badge_ids": [],
  "options": {},
  "manual_placements": []
}
```

Outputs page dimensions, normalized options, panel layouts, and placements in `structuredContent`, plus a text content item. The tool schema enumerates the same `options.mode` values as `/api/v1/options`, including `m-pixels-no-shrink` for a fixed badge-size M with overflow fallback frames.

#### `render_pdf`

Inputs:

```json
{
  "badge_ids": [],
  "options": {},
  "manual_placements": [],
  "allow_partial": false
}
```

The tool schema enumerates the same `options.mode` values as `/api/v1/options`, including `m-pixels-no-shrink` for a fixed badge-size M with overflow fallback frames.

Before rendering, MCP checks that every requested badge ID resolved to a renderable placement and every resolved badge asset can be fetched and parsed. By default it returns `render_preflight_failed` for unknown badges or empty layouts and `asset_verification_failed` for broken assets instead of delivering a partial PDF; set `allow_partial` to `true` to receive a PDF with `warnings` and `diagnostics` describing omitted IDs, failed assets drawn as placeholders, layout counts, and placement counts. Generated PDFs omit automatic panel headers and page numbers; only user-supplied panel text is drawn as text.

Outputs `mime_type`, `filename`, `byte_length`, base64-encoded PDF bytes in `pdf_base64`, `warnings`, `diagnostics`, and a `resource` object with `uri`, `mimeType`, and `blob`. The tool result also includes text and resource content items for clients that prefer MCP content blocks.

#### `upload_badge_artwork`

Inputs:

```json
{
  "filename": "custom.svg",
  "content_base64": "..."
}
```

Outputs the created badge record or an MCP invalid-params error when the filename/content is unsupported, empty, over the upload size limit, or not valid base64.

#### `validate_template`

Inputs a template request and returns the normalized layout payload plus warnings such as unknown badge IDs or empty layouts. This tool is useful before calling `render_pdf` when an agent needs to explain or repair a request.

#### Saved template tools

The MCP endpoint also exposes `list_saved_templates`, `save_template`, `get_saved_template`, and `delete_saved_template`. These tools mirror `/api/v1/templates` so IDEs and agents can persist repeatable local JSON workflows without manually writing files. Saved templates use the same `badge_ids`, `options`, and `manual_placements` shape as the layout preview and PDF APIs.

### MCP Error Behavior

Unknown resources, unknown tools, invalid prompts, invalid methods, invalid base64 uploads, and failed PDF asset verification return JSON-RPC error objects. Invalid upload arguments, non-object `params`, and render-preflight failures use code `-32602` to match JSON-RPC invalid params; asset failures include an `error.data.failures` array with per-badge details. Invalid non-object requests use `-32600`. The Flask endpoint returns these JSON-RPC errors with HTTP 200 for broad client compatibility. JSON-RPC batch arrays are accepted and return one response object per request, including per-item errors for invalid batch entries. Tool calls accept MCP-standard `arguments` and a compatibility `input` alias for older or generic JSON-RPC clients.

### MCP Security Considerations

- Uploaded artwork should be size-limited and extension-validated.
- PDF rendering should avoid unrestricted external URL fetches when possible.
- MCP tools that write files should use an explicit output directory.
- Any future authenticated deployment should scope uploads/templates per user.
- Exposed MCP resources should not leak local filesystem paths unless explicitly requested in a trusted development context.

### Compatibility Methods

The endpoint supports `initialize`, `ping`, `notifications/initialized`, `tools/list`, `tools/call`, `resources/list`, `resources/read`, `resources/templates/list`, `prompts/list`, and `prompts/get`. Initialize advertises `tools`, `resources`, and `prompts` capabilities with list-change notifications disabled and echoes the requested protocol version when a client provides one.

### MCP Open Questions

- Should MCP continue calling internal Python functions directly, or should future tools go through `/api/v1` for stricter schema/error parity?
- Should a deployment publish a conventional example port for docs, even though MCP clients only require a reachable endpoint URL?
- Should generated PDFs continue to be returned as base64 JSON, or should future MCP clients receive resource references or files?
- Should upstream badge refresh be available to MCP clients by default?
- What retention policy should apply to generated PDFs and temporary layouts?
