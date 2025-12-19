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
- MIT (add or change as appropriate for your public repository)

