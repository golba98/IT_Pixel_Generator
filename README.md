# 11-IT PiXELS

11-IT PiXELS is a small Python image-mosaic tool. It transforms an input image by rebuilding it from tiles sampled from a reference image, with a Tkinter GUI for live preview and a CLI helper for generating an animated GIF.

## Features

- Live GUI preview of the mosaic transformation.
- Configurable block size, animation speed, and color blend strength.
- Save the final GUI result as JPEG or PNG.
- CLI GIF export for the full transformation process.
- Automatic block-size scaling for very large images.
- Default reference image support through the tracked `it.jpeg` asset.

## Tech Stack

- Python 3.8+
- Tkinter for the desktop GUI
- Pillow for image loading, processing, and export

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Tkinter is usually bundled with Python. If it is missing on Linux, install your distribution's Tkinter package, such as `python3-tk` on Debian or Ubuntu.

## Run The Project

Start the GUI:

```bash
python gui_converter.py
```

On Windows, you can also run:

```bat
run_gui.bat
```

Generate an animated GIF from the CLI:

```bash
python image_converter.py path/to/input-image.png
```

Useful CLI options:

```bash
python image_converter.py path/to/input-image.png --output output.gif --reference it.jpeg --steps 120 --block-size 1 --blend 0.85
```

## Tests And Validation

There is no automated test suite yet. For a basic validation pass, run:

```bash
python -m compileall -q gui_converter.py image_converter.py
```

If you install development tools, these checks are also recommended:

```bash
python -m ruff check .
python -m black --check .
python -m pytest
```

## Project Structure

```text
.
├── gui_converter.py      # Tkinter GUI
├── image_converter.py    # Mosaic engine and CLI GIF export
├── it.jpeg               # Default reference image
├── requirements.txt      # Runtime Python dependencies
├── run_gui.bat           # Windows launcher
└── README.md
```

## Environment Variables

No environment variables are required.

## Notes And Limitations

- Large images can be slow and memory-intensive, especially with a block size of `1`.
- CLI GIF export stores frames in memory before saving, so use `--frame-sample` for very large outputs.
- The default `it.jpeg` reference image is included in the repository. Confirm that you have the right to publish or redistribute it before making the repository public.
- Generated images, local virtual environments, caches, logs, and local database files should stay uncommitted.

## License

MIT. See [LICENSE](LICENSE).
