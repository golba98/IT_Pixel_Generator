import os
import sys
import math
import random
import bisect
import colorsys
from typing import List, Tuple, Generator, Dict, Union
from dataclasses import dataclass

from PIL import Image, ImageEnhance, ImageDraw

DEFAULT_BLOCK_SIZE = 1
DEFAULT_ANIMATION_STEPS = 1
FINAL_BLEND_STRENGTH = 1
ENABLE_SHIMMER = True


@dataclass
class PixelTile:
    avg_color: Tuple[int, int, int]
    luminance: float
    coord: Tuple[int, int]
    size: Tuple[int, int]


class PennywiseMosaicEngine:
    def __init__(
        self,
        input_source: Union[str, Image.Image],
        ref_source: Union[str, Image.Image],
        animation_steps: int = DEFAULT_ANIMATION_STEPS,
        block_size: int = DEFAULT_BLOCK_SIZE,
        blend_strength: float = FINAL_BLEND_STRENGTH
    ):
        self.block_size = max(1, int(block_size))
        self.blend_strength = max(0.0, min(1.0, float(blend_strength)))
        self.animation_steps = max(1, int(animation_steps))
        self.tiles: List[PixelTile] = []
        self.tile_luminances: List[float] = []
        self.grid_map: List[Dict] = []

        if isinstance(input_source, str):
            if not os.path.exists(input_source):
                raise FileNotFoundError(f"Input image not found: {input_source}")
            self.img_in = Image.open(input_source).convert('RGB')
        else:
            self.img_in = input_source.convert('RGB')

        total_pixels = self.img_in.width * self.img_in.height
        # Only auto-scale if block_size is 1 (default) and image is massive
        if self.block_size == 1:
            target_blocks = 60000000
            if total_pixels > target_blocks:
                calc_size = int(math.sqrt(total_pixels / target_blocks))
                self.block_size = max(self.block_size, calc_size)

        if isinstance(ref_source, str):
            if not os.path.exists(ref_source):
                raise FileNotFoundError(f"Reference image not found: {ref_source}")
            self.img_ref = Image.open(ref_source).convert('RGB')
        else:
            self.img_ref = ref_source.convert('RGB')

        self.img_ref = self.img_ref.resize(self.img_in.size, Image.Resampling.LANCZOS)

    def get_total_steps_estimate(self) -> int:
        """Calculate total yielded frames: Scan frames + Animation steps + Final frame."""
        w, h = self.img_in.size
        # Scan phase yields every 'scan_interval' rows
        scan_interval = max(self.block_size, h // 15)
        scan_frames = math.ceil(h / scan_interval)
        # Phase 2 & 3 yields text strings (2 steps)
        # Animation phase yields 'animation_steps' + 10 padding steps + final canvas
        return scan_frames + 2 + self.animation_steps + 10 + 1

    def _calculate_luminance(self, color: Tuple[int, int, int]) -> float:
        r, g, b = color
        return 0.299 * r + 0.587 * g + 0.114 * b

    def _get_avg_color(self, img_chunk: Image.Image) -> Tuple[int, int, int]:
        return img_chunk.resize((1, 1)).getpixel((0, 0))

    def prepare_data(self):
        for _ in self.prepare_data_steps():
            pass

    def prepare_data_steps(self):
        yield "Phase 1/3: Scanning Input Pixels..."
        w, h = self.img_in.size

        self.tiles = []

        vis_base = ImageEnhance.Brightness(self.img_in).enhance(0.3)

        scan_interval = max(self.block_size, h // 15)

        for y in range(0, h, self.block_size):
            if y % scan_interval < self.block_size:
                frame = vis_base.copy()
                frame.paste(self.img_in.crop((0, 0, w, y)), (0, 0))
                draw = ImageDraw.Draw(frame)
                draw.rectangle([0, y, w, y + self.block_size], outline="#00ff00", width=2)
                yield frame

            for x in range(0, w, self.block_size):
                box = (x, y, min(w, x + self.block_size), min(h, y + self.block_size))
                tile_img = self.img_in.crop(box)
                avg_col = self._get_avg_color(tile_img)
                lum = self._calculate_luminance(avg_col)

                self.tiles.append(PixelTile(
                    avg_color=avg_col,
                    luminance=lum,
                    coord=(x, y),
                    size=(box[2] - box[0], box[3] - box[1])
                ))

        self.tiles.sort(key=lambda t: t.luminance)
        self.tile_luminances = [t.luminance for t in self.tiles]

        yield "Phase 2/3: Processing Target Geometry..."
        cx, cy = w // 2, h // 2

        for y in range(0, h, self.block_size):
            for x in range(0, w, self.block_size):
                box = (x, y, min(w, x + self.block_size), min(h, y + self.block_size))

                target_region = self.img_ref.crop(box)
                target_color = self._get_avg_color(target_region)
                target_lum = self._calculate_luminance(target_color)

                r, g, b = target_color
                h_val, s_val, v_val = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)

                dx, dy = x - cx, y - cy
                dist = math.sqrt(dx*dx + dy*dy)

                self.grid_map.append({
                    'box': box,
                    'target_color': target_color,
                    'target_lum': target_lum,
                    'dist': dist,
                    'hue': h_val
                })

        yield "Phase 3/3: Optimizing Grid (Spectral Sort)..."
        self.grid_map.sort(key=lambda item: item['hue'])

    def _get_tile_image(self, tile: PixelTile, target_size: Tuple[int, int]) -> Image.Image:
        tx, ty = tile.coord
        tw, th = tile.size
        tile_img = self.img_in.crop((tx, ty, tx + tw, ty + th))
        if tile_img.size != target_size:
            tile_img = tile_img.resize(target_size)
        return tile_img

    def generate_frames(self) -> Generator[Union[Image.Image, str], None, None]:
        if not self.grid_map:
            yield from self.prepare_data_steps()

        w, h = self.img_in.size
        canvas = self.img_in.copy()

        total_blocks = len(self.grid_map)
        blocks_per_step = math.ceil(total_blocks / self.animation_steps)
        jitter_range = max(1, len(self.tiles) // 200)

        processed_count = 0

        for step in range(self.animation_steps + 10):
            start_idx = processed_count
            end_idx = min(processed_count + blocks_per_step, total_blocks)

            if start_idx >= total_blocks:
                yield canvas
                continue

            current_batch = self.grid_map[start_idx:end_idx]

            for block in current_batch:
                box = block['box']
                target_lum = block['target_lum']
                target_color = block['target_color']

                idx = bisect.bisect_left(self.tile_luminances, target_lum)
                idx = max(0, min(len(self.tiles) - 1, idx))
                idx = max(0, min(len(self.tiles) - 1, idx + random.randint(-jitter_range, jitter_range)))

                bw, bh = box[2]-box[0], box[3]-box[1]
                best_tile = self._get_tile_image(self.tiles[idx], (bw, bh))

                color_overlay = Image.new('RGB', best_tile.size, target_color)
                final_tile = Image.blend(best_tile, color_overlay, self.blend_strength)

                canvas.paste(final_tile, box)

            if ENABLE_SHIMMER and current_batch:
                min_x = min(b['box'][0] for b in current_batch)
                max_x = max(b['box'][2] for b in current_batch)
                min_y = min(b['box'][1] for b in current_batch)
                max_y = max(b['box'][3] for b in current_batch)

                try:
                    shimmer_region = canvas.crop((min_x, min_y, max_x, max_y))
                    enhancer = ImageEnhance.Brightness(shimmer_region)
                    bright_region = enhancer.enhance(1.4)
                    canvas.paste(bright_region, (min_x, min_y))
                    yield canvas
                    canvas.paste(shimmer_region, (min_x, min_y))
                except Exception:
                    yield canvas
            else:
                yield canvas

            processed_count = end_idx
        yield canvas


def mosaic_tile_engine(img_in: Image.Image, img_ref: Image.Image, steps=100, block_size=1, blend_strength=1.0):
    return PennywiseMosaicEngine(img_in, img_ref, animation_steps=steps, block_size=block_size, blend_strength=blend_strength)


def convert_to_jpeg(input_path: str, output_name: str = "transformation_process.gif"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ref_path = os.path.join(base_dir, "it.jpeg")

    if not os.path.exists(ref_path):
        print(f"Error: Reference image 'it.jpeg' not found in {base_dir}")
        return

    print("Initializing Engine (Analyzing Pixels)...")
    engine = PennywiseMosaicEngine(input_path, ref_path)

    print("Generating Animation Frames...")
    gen = engine.generate_frames()
    
    frames = []
    for frame in gen:
        frames.append(frame.copy())
        print(".", end="", flush=True)

    print(f"\nCollected {len(frames)} frames. Saving Animation...")
    
    output_path = os.path.join(os.path.dirname(input_path) or '.', output_name)
    
    if frames:
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            optimize=False,
            duration=40,
            loop=0
        )
        return {'output_path': output_path}
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python image_converter.py <path_to_image>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found.")
        sys.exit(1)

    try:
        result = convert_to_jpeg(input_file, output_name="pennywise_transform.gif")
        if result:
            print(f"Done! Full process saved to: {result['output_path']}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
