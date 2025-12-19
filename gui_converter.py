import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from image_converter import mosaic_tile_final, mosaic_tile_generator


class ImageConverterGUI(tk.Tk):
    def __init__(self, initial_path=None):
        super().__init__()
        self.title("Image → picture it.jpeg")
        self.geometry("800x600")
        self.resizable(True, True)
        self.input_path = initial_path
        self.preview_img = None
        self.transformation_gen = None
        self._build_ui()
        if self.input_path:
            self.path_var.set(self.input_path)
            self._show_preview(self.input_path)
            self.status_var.set(f"Selected: {os.path.basename(self.input_path)}")

    def _build_ui(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)
        controls = ttk.Frame(frm)
        controls.pack(fill=tk.X)
        self.path_var = tk.StringVar()
        entry = ttk.Entry(controls, textvariable=self.path_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        browse_btn = ttk.Button(controls, text="Browse…", command=self.browse_file)
        browse_btn.pack(side=tk.LEFT)
        self.transform_btn = ttk.Button(controls, text="Transform", command=self.start_transformation)
        self.transform_btn.pack(side=tk.LEFT, padx=(8, 0))
        preview_frame = ttk.LabelFrame(frm, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.canvas = tk.Canvas(preview_frame, bg="#222")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.status_var = tk.StringVar(value="Select an image to begin")
        status = ttk.Label(frm, textvariable=self.status_var)
        status.pack(fill=tk.X, pady=(8, 0))

    def browse_file(self):
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
            ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(title="Select image", filetypes=filetypes)
        if not path:
            return
        self.path_var.set(path)
        self.input_path = path
        self._show_preview(path)
        self.status_var.set(f"Selected: {os.path.basename(path)}")

    def _show_preview(self, path_or_img):
        try:
            if isinstance(path_or_img, str):
                img = Image.open(path_or_img)
            else:
                img = path_or_img
            cw = max(200, self.canvas.winfo_width() or 780)
            ch = max(200, self.canvas.winfo_height() or 400)
            display_img = img.copy()
            display_img.thumbnail((cw - 20, ch - 20))
            self.preview_img = ImageTk.PhotoImage(display_img)
            self.canvas.delete("all")
            self.canvas.create_image(cw // 2, ch // 2, image=self.preview_img, anchor=tk.CENTER)
        except Exception as e:
            messagebox.showerror("Preview error", f"Unable to open image:\n{e}")

    def start_transformation(self):
        path = self.path_var.get() or self.input_path
        if not path or not os.path.exists(path):
            messagebox.showwarning("No file", "Please select a valid image file first.")
            return
        ref_path = os.path.join(os.path.dirname(__file__) or '.', 'it.jpeg')
        if not os.path.exists(ref_path):
            if messagebox.askyesno("Reference missing", "Default it.jpeg not found. Select a reference image?"):
                ref_path = filedialog.askopenfilename(title="Select reference image",
                                                 filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.gif"), ("All files", "*.*")])
                if not ref_path:
                    return
            else:
                return
        try:
            img_in = Image.open(path)
            img_ref = Image.open(ref_path)
            self.status_var.set("Transforming...")
            self.transform_btn.config(state=tk.DISABLED)
            self.transformation_gen = mosaic_tile_generator(img_in, img_ref, steps=200)
            self._process_step()
        except Exception as e:
            messagebox.showerror("Error", f"Transformation failed: {e}")
            self.transform_btn.config(state=tk.NORMAL)

    def _process_step(self):
        if self.transformation_gen:
            try:
                next_img = next(self.transformation_gen)
                self._show_preview(next_img)
                self.last_transformed_img = next_img
                self.after(10, self._process_step)
            except StopIteration:
                self.status_var.set("Transformation complete!")
                self.transform_btn.config(state=tk.NORMAL)
                self.transformation_gen = None
            except Exception as e:
                messagebox.showerror("Error", f"Error during transformation: {e}")
                self.transform_btn.config(state=tk.NORMAL)
                self.transformation_gen = None


def main(initial_path=None):
    app = ImageConverterGUI(initial_path=initial_path)
    app.mainloop()


if __name__ == "__main__":
    main()
