"""
Image to JPEG Converter
Converts any image format to JPEG and saves it as 'picture it.jpeg'
"""

from PIL import Image
import sys
import os
from typing import Optional


def convert_to_jpeg(input_path, output_name="it.jpeg"):
    """
    Convert an image to JPEG format.
    
    Args:
        input_path (str): Path to the input image file
        output_name (str): Name of the output JPEG file
    """
    # Open the image
    img = Image.open(input_path)

    # Save original info before conversions
    original_format = img.format
    original_size = img.size

    # Convert RGBA to RGB if necessary (JPEG doesn't support transparency)
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Save as JPEG
    output_path = os.path.join(os.path.dirname(input_path) or '.', output_name)
    img.save(output_path, 'JPEG', quality=95)

    # Return useful info for callers (GUI or CLI)
    return {
        'output_path': output_path,
        'original_format': original_format,
        'original_size': original_size,
        'output_size': img.size,
    }


def _tile_reference_over_input(img_input: Image.Image, img_ref: Image.Image) -> Image.Image:
    """Create a new image the same size as img_input by tiling pixels from img_ref.

    Each pixel (x,y) in the output is set to the pixel at (x % ref_w, y % ref_h)
    from the reference image. This implements the "mosaic/tile" behavior.
    """
    img_input = img_input.convert('RGB')
    img_ref = img_ref.convert('RGB')
    in_w, in_h = img_input.size
    ref_w, ref_h = img_ref.size

    ref_px = img_ref.load()
    out = Image.new('RGB', (in_w, in_h))
    out_px = out.load()

    for y in range(in_h):
        ry = y % ref_h
        for x in range(in_w):
            rx = x % ref_w
            out_px[x, y] = ref_px[rx, ry]

    return out


def mosaic_tile_to_it(input_path: str, ref_path: Optional[str] = None, output_name: str = "it.jpeg"):
    """Load input and a reference `it.jpeg`, tile the reference's pixels across the
    input image area, and save the result as `output_name` in the script folder.

    This function does NOT persist the input path anywhere.
    """
    # Open input
    img_in = Image.open(input_path)

    # Resolve reference path (default: script folder / it.jpeg)
    if ref_path is None:
        ref_path = os.path.join(os.path.dirname(__file__) or '.', 'it.jpeg')

    if not os.path.exists(ref_path):
        raise FileNotFoundError(f"Reference file not found: {ref_path}")

    img_ref = Image.open(ref_path)

    # Create tiled image
    out_img = _tile_reference_over_input(img_in, img_ref)

    # Save output in script directory (do not save input dir)
    output_path = os.path.join(os.path.dirname(__file__) or '.', output_name)
    out_img.save(output_path, 'JPEG', quality=95)

    return {
        'output_path': output_path,
        'output_size': out_img.size,
    }


def main():
    """Main function to handle command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python image_converter.py <input_image_path>")
        print("\nExample:")
        print("  python image_converter.py myimage.png")
        print("  python image_converter.py photo.webp")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(input_path):
        print(f"✗ Error: File '{input_path}' does not exist.")
        sys.exit(1)
    
    try:
        info = convert_to_jpeg(input_path)
        print(f"✓ Image successfully converted and saved as: {info['output_path']}")
        print(f"  Original format: {info['original_format']}")
        print(f"  Original size: {info['original_size']}")
        print(f"  Output size: {info['output_size']}")
    except FileNotFoundError:
        print(f"✗ Error: File '{input_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error converting image: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
