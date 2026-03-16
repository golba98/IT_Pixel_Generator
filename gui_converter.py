import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from image_converter import mosaic_tile_engine


class ImageConverterGUI(tk.Tk):
    def __init__(self, initial_path=None):
        super().__init__()

        self.title("IT Pixel Generator")
        self.geometry("1100x850")
        self.minsize(900, 700)

        self.input_path = initial_path
        self.ref_path = os.path.join(os.path.dirname(__file__) or '.', 'it.jpeg')
        self.transformation_gen = None
        self.preview_image_tk = None
        self.final_result_img = None

        self._setup_styles()
        self._build_ui()

        if self.input_path and os.path.exists(self.input_path):
            self.path_var.set(self.input_path)
            self._load_and_show_preview(self.input_path)
        
        if os.path.exists(self.ref_path):
            self.ref_var.set(self.ref_path)

    def _setup_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except:
            pass

        bg_color = "#2b2b2b"
        fg_color = "#ffffff"
        accent_color = "#d62828"

        self.configure(bg=bg_color)

        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Helvetica", 10))
        style.configure("TLabelframe", background=bg_color, foreground=fg_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=accent_color, font=("Helvetica", 10, "bold"))
        style.configure("TButton", background="#404040", foreground=fg_color, font=("Helvetica", 10, "bold"), borderwidth=1)
        style.map("TButton", background=[('active', accent_color), ('disabled', '#333333')])

        style.configure("TEntry", fieldbackground="#404040", foreground=fg_color)

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # File Selection Area
        files_frame = ttk.LabelFrame(main_frame, text=" File Selection ", padding=10)
        files_frame.pack(fill=tk.X, pady=(0, 15))

        # Input row
        input_row = ttk.Frame(files_frame)
        input_row.pack(fill=tk.X, pady=2)
        ttk.Label(input_row, text="Input Image:", width=15).pack(side=tk.LEFT)
        self.path_var = tk.StringVar()
        ttk.Entry(input_row, textvariable=self.path_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(input_row, text="Browse...", command=self._browse_input).pack(side=tk.LEFT)

        # Reference row
        ref_row = ttk.Frame(files_frame)
        ref_row.pack(fill=tk.X, pady=2)
        ttk.Label(ref_row, text="Ref Image:", width=15).pack(side=tk.LEFT)
        self.ref_var = tk.StringVar()
        ttk.Entry(ref_row, textvariable=self.ref_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(ref_row, text="Browse...", command=self._browse_ref).pack(side=tk.LEFT)

        # Settings Area
        settings_frame = ttk.LabelFrame(main_frame, text=" Transformation Settings ", padding=10)
        settings_frame.pack(fill=tk.X, pady=(0, 15))

        # Sliders
        sliders_row = ttk.Frame(settings_frame)
        sliders_row.pack(fill=tk.X)

        # Block Size
        block_frame = ttk.Frame(sliders_row)
        block_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        ttk.Label(block_frame, text="Block Size (px):").pack(side=tk.TOP, anchor=tk.W)
        self.block_size_var = tk.IntVar(value=1)
        tk.Scale(block_frame, from_=1, to=20, orient=tk.HORIZONTAL, variable=self.block_size_var, 
                 bg="#2b2b2b", fg="white", highlightthickness=0, troughcolor="#404040").pack(fill=tk.X)

        # Animation Steps
        anim_frame = ttk.Frame(sliders_row)
        anim_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        ttk.Label(anim_frame, text="Animation Speed:").pack(side=tk.TOP, anchor=tk.W)
        self.anim_steps_var = tk.IntVar(value=120)
        tk.Scale(anim_frame, from_=10, to=400, orient=tk.HORIZONTAL, variable=self.anim_steps_var,
                 bg="#2b2b2b", fg="white", highlightthickness=0, troughcolor="#404040").pack(fill=tk.X)

        # Blend Strength
        blend_frame = ttk.Frame(sliders_row)
        blend_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        ttk.Label(blend_frame, text="Color Blend:").pack(side=tk.TOP, anchor=tk.W)
        self.blend_var = tk.DoubleVar(value=0.85)
        tk.Scale(blend_frame, from_=0.0, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, variable=self.blend_var,
                 bg="#2b2b2b", fg="white", highlightthickness=0, troughcolor="#404040").pack(fill=tk.X)

        # Action Buttons
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill=tk.X, pady=(0, 10))

        self.btn_transform = ttk.Button(actions_frame, text="START TRANSFORMATION", command=self._start_transformation)
        self.btn_transform.pack(side=tk.LEFT, padx=(0, 10), ipadx=20, ipady=5)

        self.btn_save = ttk.Button(actions_frame, text="SAVE RESULT", command=self._save_result, state=tk.DISABLED)
        self.btn_save.pack(side=tk.LEFT, padx=(0, 10), ipadx=10, ipady=5)

        # Preview Canvas
        self.canvas_container = tk.Frame(main_frame, bg="#111111", bd=2, relief=tk.SUNKEN)
        self.canvas_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_container, bg="#111111", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Status Bar
        status_container = ttk.Frame(main_frame)
        status_container.pack(fill=tk.X, pady=(10, 0))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_container, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, side=tk.TOP, pady=(0, 5))

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(status_container, textvariable=self.status_var, font=("Consolas", 9)).pack(side=tk.LEFT)

        self.time_var = tk.StringVar(value="")
        ttk.Label(status_container, textvariable=self.time_var, font=("Consolas", 9)).pack(side=tk.RIGHT)

    def _browse_input(self):
        path = filedialog.askopenfilename(title="Select Input Image", 
                                          filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp"), ("All", "*.*")])
        if path:
            self.path_var.set(path)
            self.input_path = path
            self._load_and_show_preview(path)

    def _browse_ref(self):
        path = filedialog.askopenfilename(title="Select Reference Image", 
                                          filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp"), ("All", "*.*")])
        if path:
            self.ref_var.set(path)
            self.ref_path = path

    def _load_and_show_preview(self, path):
        try:
            img = Image.open(path)
            self._display_on_canvas(img)
            self.status_var.set(f"Loaded: {os.path.basename(path)} ({img.width}x{img.height})")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{e}")

    def _display_on_canvas(self, img):
        self.canvas.update_idletasks()
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw < 10: cw, ch = 800, 600

        w, h = img.size
        ratio = min(cw / w, ch / h)
        new_w, new_h = int(w * ratio), int(h * ratio)

        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.preview_image_tk = ImageTk.PhotoImage(img_resized)
        self.canvas.delete("all")
        self.canvas.create_image(cw // 2, ch // 2, image=self.preview_image_tk, anchor=tk.CENTER)

    def _start_transformation(self):
        if not self.path_var.get() or not os.path.exists(self.path_var.get()):
            messagebox.showwarning("Warning", "Please select a valid input image.")
            return
        
        ref = self.ref_var.get()
        if not ref or not os.path.exists(ref):
            messagebox.showwarning("Warning", "Please select a valid reference image.")
            return

        try:
            self.btn_transform.config(state=tk.DISABLED)
            self.btn_save.config(state=tk.DISABLED)
            self.status_var.set("Initializing engine...")
            
            img_in = Image.open(self.path_var.get())
            img_ref = Image.open(ref)

            engine = mosaic_tile_engine(
                img_in, 
                img_ref, 
                steps=self.anim_steps_var.get(),
                block_size=self.block_size_var.get(),
                blend_strength=self.blend_var.get()
            )

            self.total_steps = engine.get_total_steps_estimate()
            self.transformation_gen = engine.generate_frames()

            self.start_time = time.time()
            self.last_frame_time = time.time()
            self.frame_times = []
            self.frame_count = 0
            self.progress_var.set(0)
            
            self._animate_next_frame()

        except Exception as e:
            self.btn_transform.config(state=tk.NORMAL)
            messagebox.showerror("Engine Error", str(e))

    def _animate_next_frame(self):
        if not self.transformation_gen: return

        try:
            frame = next(self.transformation_gen)
            if isinstance(frame, str):
                self.status_var.set(frame)
                self.after(1, self._animate_next_frame)
                return

            self.frame_count += 1
            self.final_result_img = frame # Store the current frame as potential result

            # Update Progress & ETA
            progress = (self.frame_count / self.total_steps) * 100
            self.progress_var.set(min(progress, 100))

            now = time.time()
            self.frame_times.append(now - self.last_frame_time)
            self.last_frame_time = now
            if len(self.frame_times) > 20: self.frame_times.pop(0)

            avg = sum(self.frame_times) / len(self.frame_times)
            eta = (self.total_steps - self.frame_count) * avg
            self.time_var.set(f"ETA: {eta:.1f}s")

            self._display_on_canvas(frame)
            self.after(5, self._animate_next_frame)

        except StopIteration:
            self.status_var.set("Complete!")
            self.progress_var.set(100)
            self.time_var.set("Done")
            self.btn_transform.config(state=tk.NORMAL)
            self.btn_save.config(state=tk.NORMAL)
            self.transformation_gen = None
        except Exception as e:
            messagebox.showerror("Animation Error", str(e))
            self.btn_transform.config(state=tk.NORMAL)

    def _save_result(self):
        if not self.final_result_img: return
        
        path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")],
            initialfile="mosaic_result.jpg"
        )
        if path:
            try:
                self.final_result_img.save(path, quality=95)
                messagebox.showinfo("Success", f"Image saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))


def main():
    app = ImageConverterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()