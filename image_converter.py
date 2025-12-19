from PIL import Image, ImageChops
import sys
import os
from typing import Optional


def convert_to_jpeg(input_path, output_name="converted.jpeg"):
    img = Image.open(input_path)
    original_format = img.format
    original_size = img.size
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    output_path = os.path.join(os.path.dirname(input_path) or '.', output_name)
    img.save(output_path, 'JPEG', quality=95)
    return {
        'output_path': output_path,
        'original_format': original_format,
        'original_size': original_size,
        'output_size': img.size,
    }


def _tile_reference_over_input(img_input: Image.Image, img_ref: Image.Image) -> Image.Image:
    img_input = img_input.convert('RGB')
    img_ref = img_ref.convert('RGB')
    img_ref = _get_single_tile(img_ref)
    out = img_ref.resize(img_input.size, Image.Resampling.LANCZOS)
    return out


def mosaic_tile_final(img_in: Image.Image, img_ref: Image.Image) -> Image.Image:
    return _tile_reference_over_input(img_in, img_ref)


def _get_single_tile(img: Image.Image) -> Image.Image:
    img = img.convert('RGB')
    w, h = img.size
    tile_w = w
    for x in range(20, w // 2):
        diff = ImageChops.difference(
            img.crop((0, 0, w - x, h)),
            img.crop((x, 0, w, h))
        )
        bbox = diff.getbbox()
        if bbox is None or (bbox[2] - bbox[0] < 10 and bbox[3] - bbox[1] < 10):
            tile_w = x
            break
    tile_h = h
    for y in range(20, h // 2):
        diff = ImageChops.difference(
            img.crop((0, 0, w, h - y)),
            img.crop((0, y, w, h))
        )
        bbox = diff.getbbox()
        if bbox is None or (bbox[2] - bbox[0] < 10 and bbox[3] - bbox[1] < 10):
            tile_h = y
            break
    if tile_w < w or tile_h < h:
        return img.crop((0, 0, tile_w, tile_h))
    return img


def mosaic_tile_generator(img_in: Image.Image, img_ref: Image.Image, steps=100):
    import math
    img_in = img_in.convert('RGB')
    img_ref = _get_single_tile(img_ref.convert('RGB'))
    img_ref = img_ref.resize(img_in.size, Image.Resampling.LANCZOS)
    w, h = img_in.size
    center_x, center_y = w // 2, h // 2
    block_size = 24
    blocks = []
    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            dx = x - center_x
            dy = y - center_y
            distance = math.sqrt(dx*dx + dy*dy)
            angle = math.atan2(dy, dx)
            blocks.append((x, y, distance, angle))
    blocks.sort(key=lambda b: (b[2], b[3]))
    total_blocks = len(blocks)
    blocks_per_step = max(1, int(total_blocks / steps) + 1)
    current_state = img_in.copy()
    for i in range(steps):
        progress = i / steps
        start_idx = i * blocks_per_step
        if start_idx < total_blocks:
            end_idx = min(start_idx + blocks_per_step, total_blocks)
            batch = blocks[start_idx:end_idx]
            for bx, by, _, _ in batch:
                box = (bx, by, min(bx + block_size, w), min(by + block_size, h))
                patch = img_ref.crop(box)
                current_state.paste(patch, box)
        frame = current_state.copy()
        shimmer_intensity = min(0.2, (math.sin(progress * math.pi * 4) + 1) * 0.1)
        if start_idx < total_blocks and end_idx <= total_blocks:
            for bx, by, _, _ in blocks[max(0, start_idx - blocks_per_step*2):end_idx]:
                box = (bx, by, min(bx + block_size, w), min(by + block_size, h))
                for yy in range(box[1], box[3]):
                    for xx in range(box[0], box[2]):
                        if yy >= 0 and yy < h and xx >= 0 and xx < w:
                            dist_to_edge = min(xx - box[0], box[2] - xx, yy - box[1], box[3] - yy)
                            glow = max(0, (3 - dist_to_edge) * 0.15)
                            frame_px = frame.getpixel((xx, yy))
                            new_px = tuple(int(min(255, c + glow * 100)) for c in frame_px)
                            frame.putpixel((xx, yy), new_px)
        if progress < 0.95:
            frame = Image.blend(img_in, frame, progress * 1.05)
        yield frame
    yield img_ref


def mosaic_tile_to_it(input_path: str, ref_path: Optional[str] = None, output_name: str = "converted_image.jpeg"):
    img_in = Image.open(input_path)
    if ref_path is None:
        ref_path = os.path.join(os.path.dirname(__file__) or '.', 'it.jpeg')
    if not os.path.exists(ref_path):
        raise FileNotFoundError(f"Reference file not found: {ref_path}")
    img_ref = Image.open(ref_path)
    out_img = _tile_reference_over_input(img_in, img_ref)
    output_path = os.path.join(os.path.dirname(__file__) or '.', output_name)
    out_img.save(output_path, 'JPEG', quality=95)
    return {
        'output_path': output_path,
        'output_size': out_img.size,
    }


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        from gui_converter import main as gui_main
        gui_main(initial_path=input_path)
    except ImportError:
        if not input_path:
            print("Usage: python image_converter.py <input_image_path>")
            sys.exit(1)
        print("GUI not available. Falling back to CLI...")
        if not os.path.exists(input_path):
            print(f"✗ Error: File '{input_path}' does not exist.")
            sys.exit(1)
        try:
            info = convert_to_jpeg(input_path)
            print(f"✓ Image successfully converted and saved as: {info['output_path']}")
        except Exception as e:
            print(f"✗ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
