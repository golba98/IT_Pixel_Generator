# Image to JPEG Converter (with GUI)

Simple utility to convert any image to a JPEG file named "picture it.jpeg" in the same folder as the input.
Simple utility to convert any image to a JPEG file named "it.jpeg".

Behavior (mosaic/tile):
- The program will take your uploaded image and replace its pixels by tiling the pixels
	from a reference `it.jpeg`. The result is saved as `it.jpeg` in the project (script) folder.
- The input image's directory is not stored; only the output `it.jpeg` is written to the script folder.

Requirements
- Python 3.8+
- Pillow (listed in `requirements.txt`)

Install

```powershell
# from project folder
C:/Users/jorda/OneDrive/Desktop/3-Python/Programs/2-Personal/11-IT pixels/.venv/Scripts/python.exe -m pip install -r requirements.txt
```

Run GUI

```powershell
C:/Users/jorda/OneDrive/Desktop/3-Python/Programs/2-Personal/11-IT pixels/.venv/Scripts/python.exe gui_converter.py
```

Run CLI

```powershell
C:/Users/jorda/OneDrive/Desktop/3-Python/Programs/2-Personal/11-IT pixels/.venv/Scripts/python.exe image_converter.py <path-to-image>

Notes
- The converted file will be saved as `it.jpeg` in the same directory as the input image.
```
