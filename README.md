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
  - **Border**: perimeter frame layout for collar/sleeve-style badge accents.
- Configurable page size, badge size, spacing, copies per badge, mirroring, and panel selection, with invalid form values safely normalized.
- User uploads for additional SVG/PNG/JPG badge artwork stored under the Flask `instance/uploads/` folder.
- Optional mirroring for sublimation transfer workflows.
- Browser preview plus PDF download.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app tshirt_templates.app run --debug
```

Open <http://127.0.0.1:5000>.

## Testing

```bash
python -m py_compile tshirt_templates/*.py
python -m ruff check .
python -m pytest
```

The pytest suite includes dependency-light unit coverage for layout and badge discovery. Flask route integration tests are also included and run automatically when the runtime dependencies from `requirements.txt` are installed.

## Notes

- The app caches the GitHub badge listing in memory for 10-minute windows to avoid repeated API calls; use the refresh button to clear that cache and fetch the latest repository `HEAD` immediately.
- If GitHub cannot be reached, a built-in demo badge is shown so the UI and PDF flow remain usable.
- SVG rendering in PDFs is handled with `svglib` and `reportlab`.
