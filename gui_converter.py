"""
Simple Tkinter GUI for image_converter
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from image_converter import convert_to_jpeg


class ImageConverterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image → picture it.jpeg")
        self.geometry("700x500")
        self.resizable(True, True)

        self.input_path = None
        self.preview_img = None

        self._build_ui()

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

        convert_btn = ttk.Button(controls, text="Convert to JPEG", command=self.convert)
        convert_btn.pack(side=tk.LEFT, padx=(8, 0))

        preview_frame = ttk.LabelFrame(frm, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        self.canvas = tk.Canvas(preview_frame, bg="#222", height=360)
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

    def _show_preview(self, path):
        try:
            img = Image.open(path)
            # Resize to fit canvas while preserving aspect
            cw = max(200, self.canvas.winfo_width() or 600)
            ch = max(200, self.canvas.winfo_height() or 360)
            img.thumbnail((cw - 20, ch - 20))
            self.preview_img = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(cw // 2, ch // 2, image=self.preview_img, anchor=tk.CENTER)
        except Exception as e:
            messagebox.showerror("Preview error", f"Unable to open image:\n{e}")

    def convert(self):
        path = self.path_var.get() or self.input_path
        if not path or not os.path.exists(path):
            messagebox.showwarning("No file", "Please select a valid image file first.")
            return

        output_name = "it.jpeg"
        try:
            # Use mosaic/tile behavior: tile the reference `it.jpeg` across the input
            info = None
            from image_converter import mosaic_tile_to_it

            info = mosaic_tile_to_it(path, ref_path=None, output_name=output_name)

            self.status_var.set(f"Saved: {info['output_path']}")
            messagebox.showinfo("Done", f"Saved as:\n{info['output_path']}")
        except FileNotFoundError as e:
            # If reference not found, offer user to pick one
            if messagebox.askyesno("Reference missing", "Default it.jpeg not found. Select a reference image?"):
                ref = filedialog.askopenfilename(title="Select reference image",
                                                 filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.gif"), ("All files", "*.*")])
                if ref:
                    try:
                        info = mosaic_tile_to_it(path, ref_path=ref, output_name=output_name)
                        self.status_var.set(f"Saved: {info['output_path']}")
                        messagebox.showinfo("Done", f"Saved as:\n{info['output_path']}")
                    except Exception as e2:
                        messagebox.showerror("Convert error", f"Failed to convert with selected reference:\n{e2}")
            else:
                messagebox.showwarning("Canceled", "Conversion canceled because reference was not available.")
        except Exception as e:
            messagebox.showerror("Convert error", f"Failed to convert:\n{e}")


def main():
    app = ImageConverterGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
