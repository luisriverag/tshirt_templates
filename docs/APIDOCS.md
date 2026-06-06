# API and MCP Planning Documentation

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
| `GET` | `/api/v1/health` | JSON | Basic service health. |
| `GET` | `/api/v1/options` | JSON | Supported option values and defaults. |
| `GET` | `/api/v1/badges` | JSON | Available badges with optional refresh/order/logo query flags. |
| `POST` | `/api/v1/uploads` | JSON | Saves multipart badge artwork uploads and returns created badge records. |
| `PUT` | `/api/v1/uploads/<filename>` | JSON | Replaces a saved uploaded badge artwork file by storage filename. |
| `DELETE` | `/api/v1/uploads/<filename>` | JSON | Deletes a saved uploaded badge artwork file by storage filename. |
| `POST` | `/api/v1/layouts/preview` | JSON | Computes layouts from badge IDs and options. |
| `POST` | `/api/v1/pdfs` | PDF | Generates PDF bytes from badge IDs, options, and optional manual placements. |
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
  "include_logo": false,
  "logo_size": "5.0",
  "copies": 1,
  "order": "selected",
  "sides": ["front", "back"],
  "mirror": true,
  "include_print_marks": false,
  "front_text": "Ada",
  "back_text": "MakeSpace Madrid",
  "text_font": "ubuntu"
}
```

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

### `GET /api/v1/options`

Returns supported option values and defaults.

Response should include:

- Page sizes.
- Orientations.
- Layout modes.
- Units.
- Text fonts.
- Badge size presets.
- Spacing presets.
- Copy range.
- Order modes.
- Default option object, including `front_text`, `back_text`, and `text_font`.

### `GET /api/v1/badges`

Returns the available badge catalog.

Query parameters:

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `refresh` | boolean | `false` | If true, clears cache before listing. |
| `source` | string | `all` | Future filter: `upstream`, `upload`, `fallback`, or `all`. |
| `order` | string | `alphabetical` | Catalog display order. |

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
    "include_logo": false,
    "logo_size": "5.0",
    "copies": 1,
    "order": "selected",
    "sides": ["front", "back"],
    "mirror": true,
    "include_print_marks": false,
    "front_text": "Ada",
    "back_text": "MakeSpace Madrid",
    "text_font": "ubuntu"
  },
  "manual_placements": []
}
```

`front_text` and `back_text` are optional short labels rendered on the matching panel. `text_font` accepts the values returned by `/api/v1/options` and defaults to `ubuntu`.

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

Generates a PDF from the same JSON layout request shape used by `/api/v1/layouts/preview`. The endpoint applies badge ordering, copies, optional logo placement, optional panel text, manual placement overrides, and mirror settings, then returns `application/pdf` bytes directly.

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
    "include_logo": false,
    "logo_size": "5.0",
    "copies": 1,
    "order": "selected",
    "sides": ["front", "back"],
    "mirror": true,
    "include_print_marks": false,
    "front_text": "Ada",
    "back_text": "MakeSpace Madrid",
    "text_font": "ubuntu"
  },
  "manual_placements": []
}
```

Response:

```text
Content-Type: application/pdf
Content-Disposition: attachment; filename=tshirt-badge-template.pdf
```

Job-based generation remains a future option if templates become multi-page or asset-heavy.

### `POST /api/v1/templates`

Future endpoint for persisting named templates.

Potential fields:

- `name`
- `badge_ids`
- `options`
- `manual_placements`
- `created_at`
- `updated_at`

## CLI Automation

The CLI can generate PDFs from the same JSON request shape accepted by `POST /api/v1/pdfs`:

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
    "allowed_values": ["grid", "rows"]
  }
}
```

Suggested status codes:

- `400` for invalid input.
- `404` for unknown badge/template IDs.
- `413` for upload payload too large.
- `415` for unsupported media type.
- `422` for valid JSON that cannot produce a layout.
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

The server exposes badge catalog and layout option resources, template preview tools, PDF generation tools, uploaded asset management tools, validation helpers, and layout-related prompt suggestions.

### MCP Resources

`resources/list` currently returns the two implemented JSON resources. `resources/read` returns one `contents` entry with `mimeType: application/json` and serialized `text`. `resources/templates/list` is supported and currently returns an empty `resourceTemplates` array for clients that call it during capability discovery.

| Resource URI | Status | Description |
| --- | --- | --- |
| `tshirt://options` | Implemented | Current supported options and defaults, matching `/api/v1/options`. |
| `tshirt://badges` | Implemented | Alphabetically ordered available badge catalog. |
| `tshirt://layouts/{id}` | Future | Persisted or temporary computed layout. |
| `tshirt://templates/{id}` | Future | Saved template configuration. |
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
  "order": "alphabetical"
}
```

Outputs a badge list. Optional `include_logo: true` appends the reserved MakeSpace logo badge.

#### `get_options`

Inputs: `{}`

Outputs the same supported options/defaults payload as `/api/v1/options`, plus a text content item for clients that display tool-call summaries.

#### `compute_layout`

Inputs:

```json
{
  "badge_ids": [],
  "options": {},
  "manual_placements": []
}
```

Outputs page dimensions, normalized options, panel layouts, and placements in `structuredContent`, plus a text content item.

#### `render_pdf`

Inputs:

```json
{
  "badge_ids": [],
  "options": {},
  "manual_placements": []
}
```

Outputs `mime_type`, `filename`, `byte_length`, base64-encoded PDF bytes in `pdf_base64`, and a `resource` object with `uri`, `mimeType`, and `blob`. The tool result also includes text and resource content items for clients that prefer MCP content blocks.

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

### MCP Error Behavior

Unknown resources, unknown tools, invalid prompts, invalid methods, and invalid base64 uploads return JSON-RPC error objects. Invalid upload arguments use code `-32602` to match JSON-RPC invalid params. The Flask endpoint returns these JSON-RPC errors with HTTP 200 for broad client compatibility.

### MCP Security Considerations

- Uploaded artwork should be size-limited and extension-validated.
- PDF rendering should avoid unrestricted external URL fetches when possible.
- MCP tools that write files should use an explicit output directory.
- Any future authenticated deployment should scope uploads/templates per user.
- Exposed MCP resources should not leak local filesystem paths unless explicitly requested in a trusted development context.

### Compatibility Methods

The endpoint supports `initialize`, `ping`, `notifications/initialized`, `tools/list`, `tools/call`, `resources/list`, `resources/read`, `resources/templates/list`, `prompts/list`, and `prompts/get`. Initialize advertises `tools`, `resources`, and `prompts` capabilities with list-change notifications disabled.

### MCP Open Questions

- Should MCP be served by the Flask app or a separate process?
- Should MCP call internal Python functions directly or go through `/api/v1`?
- Should generated PDFs continue to be returned as base64 JSON, or should future MCP clients receive resource references or files?
- Should upstream badge refresh be available to MCP clients by default?
- What retention policy should apply to generated PDFs and temporary layouts?
