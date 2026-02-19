# PressReady

A standalone PDF imposition tool built with Python, PyQt6, and PyMuPDF.

## Features

- **N-Up Imposition**: 2-Up and 4-Up layouts on A3/A4 sheets
- **Booklet Mode**: Saddle-stitch booklet generation with auto-padding
- **WYSIWYG Preview**: Fast image-based preview for verification
- **Vector Export**: High-quality PDF export using vector placement (no rasterization)

## Requirements

- Python 3.10+
- PyQt6
- PyMuPDF (fitz)

## Installation

```bash
# Navigate to project
cd "D:\Vibe Coding\PressReady"

# Install dependencies
pip install PyQt6 PyMuPDF pytest pytest-qt

# Or install as editable package
pip install -e ".[dev]"
```

## Running the App

```bash
python -m pressready
```

## Running Tests

```bash
pytest
```

## Project Structure

```
PressReady/
├── pressready/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── impose.py        # Imposition logic (N-Up, Booklet)
│   │   └── utils.py         # Unit conversions, page range parsing
│   ├── ui/
│   │   ├── __init__.py
│   │   └── main_window.py   # PyQt6 main window
│   └── tools/
│       ├── __init__.py
│       ├── impose_nup_demo.py
│       └── pdf_info.py      # PDF info script
├── tests/
│   ├── __init__.py
│   ├── test_utils.py
│   └── test_impose.py
├── samples/                  # Sample PDFs for testing
├── pyproject.toml
└── README.md
```

## Usage Examples

### Command Line Demo (N-Up)

```bash
python -m pressready.tools.impose_nup_demo input.pdf output_imposed.pdf
```

### PDF Info Check

```bash
python -m pressready.tools.pdf_info sample.pdf
```

## Development Stages

- [x] Stage 0: Setup - Repo skeleton, dependencies, placeholder app
- [x] Stage 1: Engine - N-Up imposition (2-Up/4-Up) with vector placement
- [x] Stage 2: UI + Previews - PyQt6 UI with source/sheet preview
- [x] Stage 3: Export - Background export with progress
- [x] Stage 4: Booklet - Saddle-stitch booklet mode
- [x] Stage 5: Marks - Crop marks, registration marks, page labels

## Current Version

**v0.6.0** - All core stages complete. See `ProjectContext.md` for detailed status.
