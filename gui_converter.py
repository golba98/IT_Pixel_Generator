import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from image_converter import mosaic_tile_generator


class ImageConverterGUI(tk.Tk):
    def __init__(self, initial_path=None):
        super().__init__()

        self.title("IT Pixel Generator")
        self.geometry("1000x800")
        self.minsize(800, 600)

        self.input_path = initial_path
        self.transformation_gen = None
        self.preview_image_tk = None

        self._setup_styles()
        self._build_ui()

        if self.input_path and os.path.exists(self.input_path):
            self.path_var.set(self.input_path)
            self._load_and_show_preview(self.input_path)

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
        style.configure("TButton", background="#404040", foreground=fg_color, font=("Helvetica", 10, "bold"), borderwidth=1)
        style.map("TButton", background=[('active', accent_color), ('disabled', '#333333')])

        style.configure("TEntry", fieldbackground="#404040", foreground=fg_color)

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 15))

        lbl_file = ttk.Label(control_frame, text="Input Image:")
        lbl_file.pack(side=tk.LEFT, padx=(0, 10))

        self.path_var = tk.StringVar()
        entry_path = ttk.Entry(control_frame, textvariable=self.path_var)
        entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        btn_browse = ttk.Button(control_frame, text="Browse...", command=self._browse_file)
        btn_browse.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_transform = ttk.Button(control_frame, text="TRANSFORM", command=self._start_transformation)
        self.btn_transform.pack(side=tk.LEFT, ipadx=10)

        self.canvas_container = tk.Frame(main_frame, bg="#111111", bd=2, relief=tk.SUNKEN)
        self.canvas_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_container, bg="#111111", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, side=tk.TOP, pady=(0, 5))

        self.status_var = tk.StringVar(value="Select an image to begin.")
        lbl_status = ttk.Label(status_frame, textvariable=self.status_var, font=("Consolas", 9))
        lbl_status.pack(side=tk.LEFT)

        self.time_var = tk.StringVar(value="")
        lbl_time = ttk.Label(status_frame, textvariable=self.time_var, font=("Consolas", 9))
        lbl_time.pack(side=tk.RIGHT)

    def _browse_file(self):
        file_types = [
            ("Images", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff"),
            ("All Files", "*.*")
        ]
        path = filedialog.askopenfilename(title="Select Photo", filetypes=file_types)
        if path:
            self.path_var.set(path)
            self.input_path = path
            self._load_and_show_preview(path)

    def _load_and_show_preview(self, path):
        try:
            img = Image.open(path)
            self._display_on_canvas(img)
            self.status_var.set(f"Loaded: {os.path.basename(path)} | Size: {img.size}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{e}")

    def _display_on_canvas(self, img):
        self.canvas.update_idletasks()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()

        if cw < 10:
            cw = 800
        if ch < 10:
            ch = 600

        w, h = img.size
        ratio = min(cw / w, ch / h)
        new_w, new_h = int(w * ratio), int(h * ratio)

        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        self.preview_image_tk = ImageTk.PhotoImage(img_resized)

        self.canvas.delete("all")
        self.canvas.create_image(cw // 2, ch // 2, image=self.preview_image_tk, anchor=tk.CENTER)

    def _start_transformation(self):
        if not self.input_path:
            messagebox.showwarning("Warning", "Please select an image first.")
            return

        ref_path = os.path.join(os.path.dirname(__file__) or '.', 'it.jpeg')
        if not os.path.exists(ref_path):
            messagebox.showerror("Error", "Reference image 'it.jpeg' is missing from the script folder.")
            return

        try:
            self.btn_transform.config(state=tk.DISABLED, text="Running...")
            self.status_var.set("Initializing pixel engine...")

            img_in = Image.open(self.input_path)
            img_ref = Image.open(ref_path)

            self.anim_steps = 120
            self.total_steps = 205 
            self.transformation_gen = mosaic_tile_generator(img_in, img_ref, steps=self.anim_steps)

            self.start_time = time.time()
            self.last_frame_time = time.time()
            self.frame_times = []
            self.frame_count = 0
            self.progress_var.set(0)
            self.time_var.set("Estimating time...")

            self._animate_next_frame()

        except Exception as e:
            self.btn_transform.config(state=tk.NORMAL, text="TRANSFORM")
            messagebox.showerror("Error", f"Transformation failed:\n{e}")

    def _animate_next_frame(self):
        if not self.transformation_gen:
            return

        try:
            frame = next(self.transformation_gen)

            if isinstance(frame, str):
                self.status_var.set(frame)
                self.update_idletasks()
                self.after(1, self._animate_next_frame)
                return

            self.frame_count += 1

            progress = (self.frame_count / self.total_steps) * 100
            self.progress_var.set(min(progress, 100))

            current_time = time.time()
            frame_duration = current_time - self.last_frame_time
            self.last_frame_time = current_time

            self.frame_times.append(frame_duration)
            if len(self.frame_times) > 30:
                self.frame_times.pop(0)

            if self.frame_times:
                avg_time = sum(self.frame_times) / len(self.frame_times)
                remaining_frames = max(0, self.total_steps - self.frame_count)
                time_left = remaining_frames * avg_time
                self.time_var.set(f"Time Left: {time_left:.1f}s")

            self._display_on_canvas(frame)

            self.after(10, self._animate_next_frame)

        except StopIteration:
            self.status_var.set("Transformation Complete! (Visual Only)")
            self.progress_var.set(100)
            self.time_var.set("Done!")
            self.btn_transform.config(state=tk.NORMAL, text="TRANSFORM")
            self.transformation_gen = None

        except Exception as e:
            print(f"Animation loop error: {e}")
            self.transformation_gen = None
            self.btn_transform.config(state=tk.NORMAL, text="TRANSFORM")


def main():
    app = ImageConverterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()