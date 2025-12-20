# Image → Pennywise Mosaic (GUI + CLI)

This project visually transforms an input image by replacing regions with tiles sampled from a reference image (default: it.jpeg). The process is shown live in a GUI with progress and an ETA; a CLI helper can generate an animated GIF of the full transformation.

Features
- Live GUI preview that shows the transformation frame-by-frame.
- Progress bar and rolling-average ETA during the transformation.
- Automatic block-size scaling to avoid memory issues on very large images.
- CLI helper to produce an animated GIF of the full process.

Requirements
- Python 3.8+
- See `requirements.txt` for exact pins (Pillow is required)
- `tkinter` (usually bundled with Python; install via your OS package manager if missing)

Quick install
```powershell
# from the project folder (activate your venv first if used)
python -m pip install -r requirements.txt
```

Run the GUI
```powershell
python gui_converter.py
```

Run the CLI (generate animated GIF)
```powershell
python image_converter.py C:\path\to\your\image.png
```

Usage notes
- Place a reference image named `it.jpeg` in the project root to use the default tile source. The GUI allows selecting a different reference if needed.
- The GUI does not save files by default; use the CLI helper `convert_to_jpeg` (called by `image_converter.py`) to produce an animated GIF of the entire transformation.
- For very large input images, the engine increases the tile block size automatically to keep memory usage reasonable. This keeps the process stable but reduces per-pixel detail.

How the visual transform works (brief)
- Phase 1: Fast scan of the input to sample tiles and build a palette.
- Phase 2: Blueprinting of the target image (mapping target regions to colors/hues).
- Phase 3: Sorted placement (by hue/spectral order) with optional shimmer for the active processing area.
- The GUI shows intermediate frames from the engine; a rolling-average of recent frame timings is used to compute the ETA.

Troubleshooting
- If the program fails on very large images, ensure you are running inside a virtual environment and have enough system memory; the engine will try to scale block size but very-large images may still be slow.
- If `tkinter` is not found, install it for your OS (e.g., `sudo apt install python3-tk` on Debian/Ubuntu).

Contributing
- Feel free to open issues or PRs to add features such as an explicit save button in the GUI or different sorting/visualization modes.

License
- MIT (adjust as needed)

Files of interest
- `image_converter.py` — core engine that yields frames and performs the transformation
- `gui_converter.py` — Tkinter GUI that consumes the engine frames and displays progress/ETA
# Image to JPEG Converter (with GUI)
# Image → picture it.jpeg (GUI + visual mosaic)

This small tool visually transforms any input image by replacing its pixels with tiles sampled from a reference `it.jpeg`. The transformation is shown live in a window — nothing is written to your disk by default.

Features
- Visual, step-by-step "redesign" animation that tiles the reference image's pixels across the input.
- GUI-first: run the GUI and watch the transform on the canvas (no automatic file saving).
- CLI will open the GUI (optionally pre-selecting an image path).

Requirements
- Python 3.8+
- Pillow (PIL) — included in `requirements.txt`
- `tkinter` (standard on most Python installs; if missing, install your platform's tkinter package)

Quick install

```powershell
# from the project folder (activate your venv first if used)
python -m pip install -r requirements.txt
```

Run the GUI

```powershell
# start the GUI (opens file picker)
python gui_converter.py
```

Open the GUI with a preselected image (optional)

```powershell
python image_converter.py C:\path\to\your\image.png
```

How it works
- Select an input image in the GUI and click **Transform**.
- The app tiles pixels from the reference `it.jpeg` across your image using a randomized block animation so you can watch the image be "redesigned".
- If `it.jpeg` is missing from the project folder, the GUI will let you choose a different reference image.

Notes
- No output file is created by the transformation in the GUI — it is purely visual. If you want to save the final result, you can export it manually from the code or add a save option.
- The repository contains `it.jpeg` which is used as the default tile reference.

License
- MIT 

