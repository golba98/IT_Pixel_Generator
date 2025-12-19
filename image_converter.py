"""
Image to JPEG Converter
Converts any image format to JPEG and saves it as 'picture it.jpeg'
"""

from PIL import Image
import sys
import os


def convert_to_jpeg(input_path, output_name="picture it.jpeg"):
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
