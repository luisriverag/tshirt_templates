# API and MCP Planning Documentation

## Current API Surface

The app now has the original browser form routes plus an initial JSON API and MCP JSON-RPC endpoint:

| Method | Path | Current Type | Notes |
| --- | --- | --- | --- |
| `GET` | `/` | HTML | Generator form. |
| `POST` | `/refresh` | Redirect | Clears the badge discovery cache. |
| `GET` | `/uploads/<filename>` | File | Serves uploaded artwork. |
| `POST` | `/preview` | HTML | Renders SVG preview from submitted form data. |
| `POST` | `/pdf` | PDF | Returns generated PDF bytes. |
| `GET` | `/api/v1/health` | JSON | Basic service health. |
| `GET` | `/api/v1/options` | JSON | Supported option values and defaults. |
| `GET` | `/api/v1/badges` | JSON | Available badges with optional refresh/order/logo query flags. |
| `POST` | `/api/v1/layouts/preview` | JSON | Computes layouts from badge IDs and options. |
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
  "mirror": true
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
- Badge size presets.
- Spacing presets.
- Copy range.
- Order modes.
- Default option object.

### `GET /api/v1/badges`

Returns the available badge catalog.

Query parameters:

| Parameter | Type | Default | Notes |
| --- | --- | --- | --- |
| `refresh` | boolean | `false` | If true, clears cache before listing. |
| `source` | string | `all` | Future filter: `upstream`, `upload`, `fallback`, or `all`. |
| `order` | string | `alphabetical` | Catalog display order. |

### `POST /api/v1/uploads`

Not implemented yet. It should accept multipart artwork uploads and return created badge records.

Future considerations:

- Enforce maximum file count per request.
- Return image dimensions when possible.
- Support deletion or replacement of uploaded assets.

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
    "sides": ["front", "back"]
  },
  "manual_placements": []
}
```

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

Generates a PDF from a JSON layout request.

Possible response strategies:

1. Return `application/pdf` bytes directly.
2. Return JSON with a temporary download URL.
3. Return a job ID for asynchronous generation.

Direct bytes are simplest for v1. Job-based generation is better if future templates become multi-page or asset-heavy.

### `POST /api/v1/templates`

Future endpoint for persisting named templates.

Potential fields:

- `name`
- `badge_ids`
- `options`
- `manual_placements`
- `created_at`
- `updated_at`

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

- Add `POST /api/v1/uploads` for API-driven artwork upload.
- Add `POST /api/v1/pdfs` for API-driven PDF rendering.
- Add API-specific validation error objects instead of silently normalizing every invalid value.
- Decide whether the MakeSpace logo is modeled as a reserved badge, separate element, or template decoration in JSON responses.
- Decide whether PDF generation should be synchronous or job-based.
- Decide how uploaded files are authenticated and cleaned up.

## Model Context Protocol (MCP) Implementation

Initial MCP support is implemented at `/mcp` using JSON-RPC-style messages. This section also tracks pending features for future automation and IDE integrations.

### MCP Server Goals

The MCP endpoint lets IDEs, agents, and design tools inspect and generate t-shirt template layouts without manually driving the browser.

The server should expose:

- Badge catalog resources.
- Layout option resources.
- Template preview tools.
- PDF generation tools.
- Uploaded asset management tools.

### Proposed MCP Resources

| Resource URI | Description |
| --- | --- |
| `tshirt://options` | Current supported options and defaults. |
| `tshirt://badges` | Available badge catalog. |
| `tshirt://layouts/{id}` | Persisted or temporary computed layout. |
| `tshirt://templates/{id}` | Saved template configuration. |
| `tshirt://uploads` | Uploaded artwork metadata. |

### Implemented MCP Tools

#### `list_badges`

Inputs:

```json
{
  "refresh": false,
  "order": "alphabetical"
}
```

Outputs a badge list.

#### `compute_layout`

Inputs:

```json
{
  "badge_ids": [],
  "options": {},
  "manual_placements": []
}
```

Outputs page dimensions, panel layouts, placements, and warnings.

#### `render_pdf`

Not implemented yet. Planned inputs:

```json
{
  "badge_ids": [],
  "options": {},
  "manual_placements": []
}
```

It should output either PDF bytes as an MCP blob or a local file/resource reference.

#### `upload_badge_artwork`

Not implemented yet. Planned inputs:

```json
{
  "filename": "custom.svg",
  "content_base64": "..."
}
```

It should output the created badge record.

#### `validate_template`

Not implemented yet. It should input a template request and return normalized options, errors, warnings, and estimated placement density.

### MCP Prompts

Potential prompts:

- `design_tshirt_template`: Ask an agent to choose badges/layout options for a described shirt concept.
- `optimize_cut_sheet`: Ask an agent to reduce wasted transfer paper while respecting badge sizes.
- `explain_layout`: Ask an agent to describe why a placement mode was chosen.

### MCP Security Considerations

- Uploaded artwork should be size-limited and extension-validated.
- PDF rendering should avoid unrestricted external URL fetches when possible.
- MCP tools that write files should use an explicit output directory.
- Any future authenticated deployment should scope uploads/templates per user.
- Exposed MCP resources should not leak local filesystem paths unless explicitly requested in a trusted development context.

### MCP Open Questions

- Should MCP be served by the Flask app or a separate process?
- Should MCP call internal Python functions directly or go through `/api/v1`?
- How should generated PDFs be returned: bytes, local file handles, or URLs?
- Should upstream badge refresh be available to MCP clients by default?
- What retention policy should apply to generated PDFs and temporary layouts?
