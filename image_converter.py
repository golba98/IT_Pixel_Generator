import argparse
import bisect
import colorsys
import math
import os
import random
import sys
from dataclasses import dataclass
from typing import Dict, Generator, List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageEnhance


DEFAULT_BLOCK_SIZE = 1
DEFAULT_ANIMATION_STEPS = 120
DEFAULT_GIF_FPS = 25
DEFAULT_FRAME_SAMPLE = 1
FINAL_BLEND_STRENGTH = 1.0
ENABLE_SHIMMER = True
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REFERENCE_IMAGE = os.path.join(PROJECT_DIR, "it.jpeg")


@dataclass(frozen=True)
class PixelTile:
    avg_color: Tuple[int, int, int]
    luminance: float
    coord: Tuple[int, int]
    size: Tuple[int, int]


GridBlock = Dict[str, Union[Tuple[int, int, int, int], Tuple[int, int, int], float]]


class PennywiseMosaicEngine:
    def __init__(
        self,
        input_source: Union[str, Image.Image],
        ref_source: Union[str, Image.Image],
        animation_steps: int = DEFAULT_ANIMATION_STEPS,
        block_size: int = DEFAULT_BLOCK_SIZE,
        blend_strength: float = FINAL_BLEND_STRENGTH,
    ):
        self.block_size = max(1, int(block_size))
        self.blend_strength = max(0.0, min(1.0, float(blend_strength)))
        self.animation_steps = max(1, int(animation_steps))
        self.tiles: List[PixelTile] = []
        self.tile_luminances: List[float] = []
        self.grid_map: List[GridBlock] = []

        self.img_in = self._load_rgb_image(input_source, "Input")
        self._scale_block_size_for_large_images()
        self.img_ref = self._load_rgb_image(ref_source, "Reference").resize(
            self.img_in.size,
            Image.Resampling.LANCZOS,
        )

    @staticmethod
    def _load_rgb_image(source: Union[str, Image.Image], label: str) -> Image.Image:
        if isinstance(source, str):
            if not os.path.exists(source):
                raise FileNotFoundError(f"{label} image not found: {source}")
            with Image.open(source) as image:
                return image.convert("RGB")

        return source.convert("RGB")

    def _scale_block_size_for_large_images(self) -> None:
        total_pixels = self.img_in.width * self.img_in.height
        target_blocks = 60_000_000

        if self.block_size == 1 and total_pixels > target_blocks:
            calculated_size = int(math.sqrt(total_pixels / target_blocks))
            self.block_size = max(self.block_size, calculated_size)

    def get_total_steps_estimate(self) -> int:
        """Estimate yielded frames and status updates for GUI progress."""
        _, height = self.img_in.size
        scan_interval = max(self.block_size, height // 15)
        scan_frames = math.ceil(height / scan_interval)
        status_updates = 2
        shimmer_padding_frames = 10
        final_frame = 1
        return scan_frames + status_updates + self.animation_steps + shimmer_padding_frames + final_frame

    @staticmethod
    def _calculate_luminance(color: Tuple[int, int, int]) -> float:
        red, green, blue = color
        return 0.299 * red + 0.587 * green + 0.114 * blue

    @staticmethod
    def _get_avg_color(img_chunk: Image.Image) -> Tuple[int, int, int]:
        return img_chunk.resize((1, 1)).getpixel((0, 0))

    def prepare_data(self) -> None:
        for _ in self.prepare_data_steps():
            pass

    def prepare_data_steps(self) -> Generator[Union[Image.Image, str], None, None]:
        yield "Phase 1/3: Scanning Input Pixels..."
        width, height = self.img_in.size

        self.tiles = []
        self.tile_luminances = []
        self.grid_map = []

        dimmed_input = ImageEnhance.Brightness(self.img_in).enhance(0.3)
        scan_interval = max(self.block_size, height // 15)

        for y_coord in range(0, height, self.block_size):
            if y_coord % scan_interval < self.block_size:
                frame = dimmed_input.copy()
                frame.paste(self.img_in.crop((0, 0, width, y_coord)), (0, 0))
                draw = ImageDraw.Draw(frame)
                draw.rectangle(
                    [0, y_coord, width, y_coord + self.block_size],
                    outline="#00ff00",
                    width=2,
                )
                yield frame

            for x_coord in range(0, width, self.block_size):
                box = (
                    x_coord,
                    y_coord,
                    min(width, x_coord + self.block_size),
                    min(height, y_coord + self.block_size),
                )
                tile_img = self.img_in.crop(box)
                avg_color = self._get_avg_color(tile_img)

                self.tiles.append(
                    PixelTile(
                        avg_color=avg_color,
                        luminance=self._calculate_luminance(avg_color),
                        coord=(x_coord, y_coord),
                        size=(box[2] - box[0], box[3] - box[1]),
                    )
                )

        self.tiles.sort(key=lambda tile: tile.luminance)
        self.tile_luminances = [tile.luminance for tile in self.tiles]

        yield "Phase 2/3: Processing Target Geometry..."

        for y_coord in range(0, height, self.block_size):
            for x_coord in range(0, width, self.block_size):
                box = (
                    x_coord,
                    y_coord,
                    min(width, x_coord + self.block_size),
                    min(height, y_coord + self.block_size),
                )

                target_region = self.img_ref.crop(box)
                target_color = self._get_avg_color(target_region)
                target_lum = self._calculate_luminance(target_color)
                red, green, blue = target_color
                hue, _, _ = colorsys.rgb_to_hsv(red / 255.0, green / 255.0, blue / 255.0)

                self.grid_map.append(
                    {
                        "box": box,
                        "target_color": target_color,
                        "target_lum": target_lum,
                        "hue": hue,
                    }
                )

        yield "Phase 3/3: Optimizing Grid (Spectral Sort)..."
        self.grid_map.sort(key=lambda item: item["hue"])

    def _get_tile_image(self, tile: PixelTile, target_size: Tuple[int, int]) -> Image.Image:
        x_coord, y_coord = tile.coord
        tile_width, tile_height = tile.size
        tile_img = self.img_in.crop(
            (x_coord, y_coord, x_coord + tile_width, y_coord + tile_height)
        )

        if tile_img.size != target_size:
            tile_img = tile_img.resize(target_size)

        return tile_img

    def generate_frames(self) -> Generator[Union[Image.Image, str], None, None]:
        if not self.grid_map:
            yield from self.prepare_data_steps()

        canvas = self.img_in.copy()
        total_blocks = len(self.grid_map)

        if total_blocks == 0:
            yield canvas
            return

        blocks_per_step = max(1, math.ceil(total_blocks / self.animation_steps))
        jitter_range = max(1, len(self.tiles) // 200)
        processed_count = 0

        for _ in range(self.animation_steps + 10):
            start_idx = processed_count
            end_idx = min(processed_count + blocks_per_step, total_blocks)

            if start_idx >= total_blocks:
                yield canvas
                continue

            current_batch = self.grid_map[start_idx:end_idx]

            for block in current_batch:
                box = block["box"]
                target_lum = block["target_lum"]
                target_color = block["target_color"]

                if not isinstance(box, tuple) or not isinstance(target_color, tuple):
                    continue

                idx = bisect.bisect_left(self.tile_luminances, float(target_lum))
                idx = max(0, min(len(self.tiles) - 1, idx))
                jittered_idx = idx + random.randint(-jitter_range, jitter_range)
                idx = max(0, min(len(self.tiles) - 1, jittered_idx))

                block_width = box[2] - box[0]
                block_height = box[3] - box[1]
                best_tile = self._get_tile_image(self.tiles[idx], (block_width, block_height))

                color_overlay = Image.new("RGB", best_tile.size, target_color)
                final_tile = Image.blend(best_tile, color_overlay, self.blend_strength)
                canvas.paste(final_tile, box)

            if ENABLE_SHIMMER and current_batch:
                yield self._apply_shimmer_frame(canvas, current_batch)
            else:
                yield canvas

            processed_count = end_idx

        yield canvas

    @staticmethod
    def _apply_shimmer_frame(canvas: Image.Image, current_batch: List[GridBlock]) -> Image.Image:
        boxes = [block["box"] for block in current_batch if isinstance(block["box"], tuple)]

        if not boxes:
            return canvas

        min_x = min(box[0] for box in boxes)
        max_x = max(box[2] for box in boxes)
        min_y = min(box[1] for box in boxes)
        max_y = max(box[3] for box in boxes)

        shimmer_region = canvas.crop((min_x, min_y, max_x, max_y))
        bright_region = ImageEnhance.Brightness(shimmer_region).enhance(1.4)
        shimmer_frame = canvas.copy()
        shimmer_frame.paste(bright_region, (min_x, min_y))
        return shimmer_frame


def mosaic_tile_engine(
    img_in: Image.Image,
    img_ref: Image.Image,
    steps: int = DEFAULT_ANIMATION_STEPS,
    block_size: int = DEFAULT_BLOCK_SIZE,
    blend_strength: float = FINAL_BLEND_STRENGTH,
) -> PennywiseMosaicEngine:
    return PennywiseMosaicEngine(
        img_in,
        img_ref,
        animation_steps=steps,
        block_size=block_size,
        blend_strength=blend_strength,
    )


def convert_to_jpeg(
    input_path: str,
    output_name: str = "transformation_process.gif",
    ref_path: Optional[str] = None,
    block_size: int = DEFAULT_BLOCK_SIZE,
    steps: int = DEFAULT_ANIMATION_STEPS,
    blend_strength: float = FINAL_BLEND_STRENGTH,
    fps: int = DEFAULT_GIF_FPS,
    frame_sample: int = DEFAULT_FRAME_SAMPLE,
) -> Optional[Dict[str, str]]:
    reference_path = ref_path or DEFAULT_REFERENCE_IMAGE

    if not os.path.exists(reference_path):
        print(f"Error: Reference image not found: {reference_path}")
        return None

    print("Initializing engine...")
    engine = PennywiseMosaicEngine(
        input_path,
        reference_path,
        animation_steps=steps,
        block_size=block_size,
        blend_strength=blend_strength,
    )

    print("Generating animation frames...")
    frames = []
    image_frame_index = 0

    for frame in engine.generate_frames():
        if isinstance(frame, str):
            print(f"\n{frame}")
            continue

        if frame_sample > 1 and image_frame_index % frame_sample != 0:
            image_frame_index += 1
            continue

        frames.append(frame.copy())
        image_frame_index += 1
        print(".", end="", flush=True)

    print(f"\nCollected {len(frames)} frames. Saving animation...")
    output_path = os.path.join(os.path.dirname(input_path) or ".", output_name)

    if not frames:
        return None

    duration_ms = max(1, int(1000 / max(1, fps)))
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        optimize=False,
        duration=duration_ms,
        loop=0,
    )
    return {"output_path": output_path}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an IT PiXELS mosaic animation GIF.")
    parser.add_argument("input", help="Path to the input image.")
    parser.add_argument("-o", "--output", default="it_pixels_transform.gif", help="Output GIF filename.")
    parser.add_argument(
        "-r",
        "--reference",
        default=None,
        help="Reference image path. Defaults to it.jpeg in the project root.",
    )
    parser.add_argument("-b", "--block-size", type=int, default=DEFAULT_BLOCK_SIZE)
    parser.add_argument("-s", "--steps", type=int, default=DEFAULT_ANIMATION_STEPS)
    parser.add_argument("--blend", type=float, default=FINAL_BLEND_STRENGTH)
    parser.add_argument("--fps", type=int, default=DEFAULT_GIF_FPS)
    parser.add_argument(
        "--frame-sample",
        type=int,
        default=DEFAULT_FRAME_SAMPLE,
        help="Keep every Nth image frame to reduce memory usage.",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}")
        sys.exit(1)

    try:
        result = convert_to_jpeg(
            args.input,
            output_name=args.output,
            ref_path=args.reference,
            block_size=args.block_size,
            steps=args.steps,
            blend_strength=args.blend,
            fps=args.fps,
            frame_sample=max(1, args.frame_sample),
        )
    except OSError as exc:
        print(f"Image processing failed: {exc}")
        sys.exit(1)

    if result:
        print(f"Done. Full process saved to: {result['output_path']}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
