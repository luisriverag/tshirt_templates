# T-Shirt Sublimation Template Generator

A Flask web application that builds printable PDF templates for front and back t-shirt sublimation sheets using badge artwork from [`makespacemadrid/open-badges`](https://github.com/makespacemadrid/open-badges).

The app discovers badge image assets from the GitHub repository, lets you select badges, choose automatic placement strategies, preview the generated layout, and export a PDF ready for printing.

## Features

- Fetches SVG/PNG/JPG badge assets from the GitHub repository via the GitHub contents API, with an automatic 10-minute refresh window plus a **Refresh badges from GitHub** action to pick up newly added upstream files immediately.
- Front and back print panels with independent layout generation.
- Automatic placement modes:
  - **Grid**: even rows and columns.
  - **Rows**: staggered horizontal bands.
  - **Diagonal**: sash-style diagonal placement.
  - **Scatter**: deterministic pseudo-random distribution.
  - **Circle wreath**: badges arranged around an oval ring.
  - **Spiral trail**: badges flowing outward from the panel center.
  - **Wave ribbon**: badges following a horizontal sine-wave band.
  - **Border**: perimeter frame layout for collar/sleeve-style badge accents.
  - **M pixel shape**: pixel-art capital M that repeats the selected badges as mosaic pixels.
- Configurable page size (A4 by default), page orientation, centimeter/inch units, badge size presets, spacing presets, copies per badge, mirroring, and panel selection, with invalid form values safely normalized.
- Optional front/back panel text for names or short labels, with Ubuntu as the default font plus Helvetica, Times, Courier, and DejaVu Sans choices.
- User uploads for additional SVG/PNG/JPG badge artwork stored under the Flask `instance/uploads/` folder, with browser and API replacement/deletion for saved uploads and validation notices for questionable image dimensions or invalid artwork.
- Optional mirroring for sublimation transfer workflows plus badge cut-line outlines, crop/registration print marks, and a calibration page with rulers/mirror warnings for alignment.
- Optional MakeSpace Madrid logo element with configurable size.
- Badge picker cards are selected by default, searchable/filterable by category, bulk selectable, and drag-and-droppable before previewing to customize selection-order layouts.
- MakeSpace-inspired black/yellow monospace UI theme plus browser preview with manual drag/coordinate placement adjustments, reset controls, zoom, snap-to-grid, snap-to-panel-edge controls, keyboard nudging, rotation presets, overlap warnings, and PDF download.
- JSON API endpoints for health/options/badges, API uploads, layout previews, and direct PDF generation, plus MCP-compatible tools/resources/prompts and a CLI for agent-driven or repeatable local PDF workflows.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m tshirt_templates.cli serve --debug
```

Open <http://127.0.0.1:5000>. The same server also exposes the JSON API under `/api/v1` and the MCP JSON-RPC endpoint at `/mcp`, so the browser UI, API clients, and MCP clients all run from one app process.

If you prefer Flask's built-in CLI, this equivalent command serves the same UI, API, and MCP routes:

```bash
flask --app tshirt_templates.app run --debug
```

## CLI PDF generation

Generate a PDF from the same JSON request shape used by `/api/v1/pdfs`:

```bash
python -m tshirt_templates.cli generate-pdf template.json tshirt-badge-template.pdf
```

Use `--upload-folder instance/uploads` when the JSON references previously uploaded `upload:` badge IDs.

## Documentation

- [`docs/SPECS.md`](docs/SPECS.md): Technical specifications for the current application.
- [`docs/APIDOCS.md`](docs/APIDOCS.md): Initial API/MCP endpoints and future integration details.
- [`docs/IDEAS.md`](docs/IDEAS.md): Potential product, layout, API, testing, and accessibility improvements.

## Testing

```bash
python -m py_compile tshirt_templates/*.py
python -m ruff check .
python -m pytest
```

The pytest suite includes dependency-light unit coverage for layout, badge discovery, uploads, option parsing, CLI generation, API option payloads, PDF handoff behavior, and MCP resources/tools. Flask route integration tests are also included and run automatically when the runtime dependencies from `requirements.txt` are installed.

## Notes

- The app caches the GitHub badge listing in memory for 10-minute windows to avoid repeated API calls; use the refresh button to clear that cache and fetch the latest repository `HEAD` immediately.
- If GitHub cannot be reached, a built-in demo badge is shown so the UI and PDF flow remain usable.
- SVG rendering in PDFs is handled with `svglib` and `reportlab`.
