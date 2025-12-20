import os
import sys
import math
import random
import bisect  # REQUIRED for fast pixel searching
import colorsys
from typing import List, Tuple, Generator, Dict, Union
from dataclasses import dataclass

from PIL import Image, ImageEnhance, ImageDraw

# --- CONFIGURATION ---
DEFAULT_BLOCK_SIZE = 1      # 1 is too slow. 10-15 is high detail.
ANIMATION_STEPS = 1        # Frames in the animation
FINAL_BLEND_STRENGTH = 1  # 85% Pennywise, 15% Original Texture
ENABLE_SHIMMER = True        # Visual glowing effect

@dataclass
class PixelTile:
    image: Image.Image
    avg_color: Tuple[int, int, int]
    luminance: float
    coord: Tuple[int, int]

class PennywiseMosaicEngine:
    def __init__(self, input_source: Union[str, Image.Image], ref_source: Union[str, Image.Image]):
        self.block_size = DEFAULT_BLOCK_SIZE
        self.tiles: List[PixelTile] = []
        self.tile_luminances: List[float] = [] # separate list for binary search
        self.grid_map: List[Dict] = []

        # Load Input
        if isinstance(input_source, str):
            if not os.path.exists(input_source):
                raise FileNotFoundError(f"Input image not found: {input_source}")
            self.img_in = Image.open(input_source).convert('RGB')
        else:
            self.img_in = input_source.convert('RGB')

        # --- Performance Fix: Dynamic Block Size ---
        # For large images, 1x1 blocks cause memory crashes (millions of objects).
        # We scale block size to keep total blocks manageable (~20k).
        total_pixels = self.img_in.width * self.img_in.height
        target_blocks = 50000
        if total_pixels > target_blocks:
            calc_size = int(math.sqrt(total_pixels / target_blocks))
            self.block_size = max(self.block_size, calc_size)

        # Load Reference (Pennywise)
        if isinstance(ref_source, str):
            if not os.path.exists(ref_source):
                raise FileNotFoundError(f"Reference image not found: {ref_source}")
            self.img_ref = Image.open(ref_source).convert('RGB')
        else:
            self.img_ref = ref_source.convert('RGB')

        # Force Reference to fit Input dimensions exactly
        self.img_ref = self.img_ref.resize(self.img_in.size, Image.Resampling.LANCZOS)

    def _calculate_luminance(self, color: Tuple[int, int, int]) -> float:
        r, g, b = color
        return 0.299 * r + 0.587 * g + 0.114 * b

    def _get_avg_color(self, img_chunk: Image.Image) -> Tuple[int, int, int]:
        return img_chunk.resize((1, 1)).getpixel((0, 0)) # type: ignore

    def prepare_data(self):
        """Analyzes both images to create the 'Palette' and the 'Blueprint'."""
        # Consume the generator if called directly
        for _ in self.prepare_data_steps(): pass

    def prepare_data_steps(self):
        yield "Phase 1/3: Scanning Input Pixels..."
        w, h = self.img_in.size

        # 1. CREATE PALETTE: Slice input image into tiles
        self.tiles = []
        
        # Visualization: Create a "dimmed" version to highlight the scan line
        vis_base = ImageEnhance.Brightness(self.img_in).enhance(0.3)
        
        for y in range(0, h, self.block_size):
            # Visual: Yield a scan line effect every few rows
            if y % (self.block_size * 2) == 0:
                frame = vis_base.copy()
                # Paste the "original" brightness up to the current line to show progress
                frame.paste(self.img_in.crop((0, 0, w, y)), (0, 0))
                # Draw the scan line
                draw = ImageDraw.Draw(frame)
                draw.rectangle([0, y, w, y + self.block_size], outline="#00ff00", width=2)
                yield frame

            for x in range(0, w, self.block_size):
                box = (x, y, min(w, x + self.block_size), min(h, y + self.block_size))
                tile_img = self.img_in.crop(box)
                avg_col = self._get_avg_color(tile_img)
                lum = self._calculate_luminance(avg_col)

                self.tiles.append(PixelTile(
                    image=tile_img,
                    avg_color=avg_col,
                    luminance=lum,
                    coord=(x, y)
                ))

        # Sort tiles by luminance so we can search them instantly
        self.tiles.sort(key=lambda t: t.luminance)
        # Create a separate list of just float values for bisect function
        self.tile_luminances = [t.luminance for t in self.tiles]

        yield "Phase 2/3: Identifying Target Pixels (Decryption)..."
        # 2. CREATE BLUEPRINT: Map out the target image
        cx, cy = w // 2, h // 2
        
        # Visualization: Start with "Digital Noise" (Black)
        vis_target = Image.new('RGB', (w, h), (10, 10, 10))
        
        # Generate all coordinates first
        coords = []
        for y in range(0, h, self.block_size):
            for x in range(0, w, self.block_size):
                coords.append((x, y))
        
        # Shuffle coordinates to create a "Random Decryption" effect
        # This makes it look like the AI is solving the image non-linearly
        random.shuffle(coords)
        
        total_coords = len(coords)
        yield_interval = max(1, total_coords // 60) # Approx 60 frames for this phase

        for i, (x, y) in enumerate(coords):
            box = (x, y, min(w, x + self.block_size), min(h, y + self.block_size))
            
            target_region = self.img_ref.crop(box)
            target_color = self._get_avg_color(target_region)
            target_lum = self._calculate_luminance(target_color)
            
            # Calculate Hue for Spectral Sort
            r, g, b = target_color
            h_val, s_val, v_val = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)

            # Update visualization
            vis_target.paste(target_region, box)

            dx, dy = x - cx, y - cy
            dist = math.sqrt(dx*dx + dy*dy)
            
            self.grid_map.append({
                'box': box,
                'target_color': target_color,
                'target_lum': target_lum,
                'dist': dist,
                'hue': h_val
            })
            
            # Yield frame
            if i % yield_interval == 0:
                yield vis_target.copy()
        
        # Final look at the identified target
        yield vis_target

        yield "Phase 3/3: Optimizing Grid (Spectral Sort)..."
        # Sort grid by Hue (Red=0.0 -> Green -> Blue -> Purple=~0.8)
        self.grid_map.sort(key=lambda item: item['hue'])

    def generate_frames(self) -> Generator[Union[Image.Image, str], None, None]:
        if not self.grid_map:
            yield from self.prepare_data_steps()

        w, h = self.img_in.size
        canvas = self.img_in.copy()

        total_blocks = len(self.grid_map)
        blocks_per_step = math.ceil(total_blocks / ANIMATION_STEPS)

        processed_count = 0

        for step in range(ANIMATION_STEPS + 10):
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

                # --- THE "IDENTIFY PIXEL" LOGIC ---
                # 1. Find the index in our sorted tiles that closely matches the target brightness
                idx = bisect.bisect_left(self.tile_luminances, target_lum)
                
                # 2. Keep index within bounds
                idx = max(0, min(len(self.tiles) - 1, idx))
                
                # 3. Add randomness so we don't pick the exact same tile for every black pixel
                # (Scans nearby neighbors in the sorted list)
                idx = max(0, min(len(self.tiles) - 1, idx + random.randint(-5, 5)))
                
                # 4. Grab the "identified" best matching tile
                best_tile = self.tiles[idx].image

                # Resize if necessary (for edge cases)
                bw, bh = box[2]-box[0], box[3]-box[1]
                if best_tile.size != (bw, bh):
                    best_tile = best_tile.resize((bw, bh))

                # Tint the matched tile to the target color
                color_overlay = Image.new('RGB', best_tile.size, target_color)
                final_tile = Image.blend(best_tile, color_overlay, FINAL_BLEND_STRENGTH)
                
                # Paste onto canvas
                canvas.paste(final_tile, box)

            # Generate visual output for this frame
            if ENABLE_SHIMMER and current_batch:
                display_frame = canvas.copy()
                # Calculate active region bounds
                min_x = min(b['box'][0] for b in current_batch)
                max_x = max(b['box'][2] for b in current_batch)
                min_y = min(b['box'][1] for b in current_batch)
                max_y = max(b['box'][3] for b in current_batch)

                try:
                    # Apply glow to the active processing area
                    active_region = display_frame.crop((min_x, min_y, max_x, max_y))
                    enhancer = ImageEnhance.Brightness(active_region)
                    bright_region = enhancer.enhance(1.4)
                    display_frame.paste(bright_region, (min_x, min_y))
                except:
                    pass
                yield display_frame
            else:
                yield canvas

            processed_count = end_idx
        yield canvas

# --- Helper for GUI ---
def mosaic_tile_generator(img_in: Image.Image, img_ref: Image.Image, steps=100):
    engine = PennywiseMosaicEngine(img_in, img_ref)
    global ANIMATION_STEPS
    ANIMATION_STEPS = steps
    return engine.generate_frames()

# --- CLI Function with GIF Support ---
def convert_to_jpeg(input_path: str, output_name: str = "transformation_process.gif"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ref_path = os.path.join(base_dir, 'it.jpeg')

    if not os.path.exists(ref_path):
        print(f"Error: Reference image 'it.jpeg' not found in {base_dir}")
        return

    print("Initializing Engine (Analyzing Pixels)...")
    engine = PennywiseMosaicEngine(input_path, ref_path)

    print("Generating Animation Frames...")
    gen = engine.generate_frames()
    
    frames = []
    for frame in gen:
        # We make a copy of each frame to store in the animation list
        frames.append(frame.copy())
        print(".", end="", flush=True)

    print(f"\nCollected {len(frames)} frames. Saving Animation...")
    
    output_path = os.path.join(os.path.dirname(input_path) or '.', output_name)
    
    if frames:
        # Save as an animated GIF so you can see the process
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            optimize=False,
            duration=40,  # Speed of animation
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
        # NOTE: Saving as .gif to show the full process
        result = convert_to_jpeg(input_file, output_name="pennywise_transform.gif")
        if result:
            print(f"Done! Full process saved to: {result['output_path']}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()