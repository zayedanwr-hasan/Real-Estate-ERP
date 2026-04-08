import os
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict

import fitz
from PIL import Image, ImageTk

from .report_manager import ReportManager


class ReportPreviewWindow(tk.Toplevel):
    def __init__(self, master, manager: ReportManager, report_result: Dict[str, Any]):
        super().__init__(master)
        self.manager = manager
        self.report_result = report_result
        self.pdf_path = report_result["pdf_path"]
        self.context = report_result["context"]

        self.configure(bg="#F4F7F6")
        self.title(self.context.get("report_title", "Print Preview"))

        self.zoom_value = tk.StringVar(value="100%")
        self.zoom_factor_map = {"100%": 1.0, "125%": 1.25, "150%": 1.5}

        self._images: list[ImageTk.PhotoImage] = []
        self._drawn_items: list[int] = []

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._set_window_size()
        self._draw_pdf()

    def _set_window_size(self):
        try:
            self.state("zoomed")
        except Exception:
            width = 1200
            height = 820
            x = max((self.winfo_screenwidth() - width) // 2, 0)
            y = max((self.winfo_screenheight() - height) // 2, 0)
            self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        toolbar = tk.Frame(self, bg="#EDEFF1", highlightthickness=1, highlightbackground="#C7CED7")
        toolbar.pack(side="top", fill="x")

        tk.Button(toolbar, text="Print", command=self._print_pdf, bg="#FFFFFF", fg="#1F2D3D", relief="groove").pack(side="right", padx=4, pady=6)
        tk.Button(toolbar, text="Save as PDF", command=self._save_pdf, bg="#FFFFFF", fg="#1F2D3D", relief="groove").pack(side="right", padx=4, pady=6)
        tk.Button(toolbar, text="Export Excel", command=self._export_excel, bg="#FFFFFF", fg="#1F2D3D", relief="groove").pack(side="right", padx=4, pady=6)

        ttk.Combobox(toolbar, values=list(self.zoom_factor_map.keys()), state="readonly", textvariable=self.zoom_value, width=8, justify="center").pack(side="right", padx=4, pady=6)
        tk.Label(toolbar, text="Zoom", bg="#EDEFF1", fg="#1F2D3D").pack(side="right", padx=(8, 2), pady=6)
        self.zoom_value.trace_add("write", self._on_zoom_changed)

        frame = tk.Frame(self, bg="#DDE3E8")
        frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(frame, bg="#DDE3E8", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        ybar = ttk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        xbar = ttk.Scrollbar(frame, orient="horizontal", command=self.canvas.xview)
        ybar.pack(side="right", fill="y")
        xbar.pack(side="bottom", fill="x")
        self.canvas.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_zoom_changed(self, _name: str, _index: str, _mode: str):
        self._draw_pdf()

    @staticmethod
    def _dim(value: Any) -> int:
        return int(value() if callable(value) else value)

    def _draw_pdf(self):
        if not os.path.exists(self.pdf_path):
            messagebox.showerror("خطأ", "ملف التقرير غير موجود")
            return

        for item in self._drawn_items:
            self.canvas.delete(item)
        self._drawn_items.clear()
        self._images.clear()

        zoom = self.zoom_factor_map.get(self.zoom_value.get(), 1.0)
        matrix_scale = 1.45 * zoom

        y_pos = 20
        max_width = 0

        with fitz.open(self.pdf_path) as doc:
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(matrix_scale, matrix_scale), alpha=False)
                width = self._dim(pix.width)
                height = self._dim(pix.height)
                image = Image.frombytes("RGB", (width, height), pix.samples)
                photo = ImageTk.PhotoImage(image)
                self._images.append(photo)

                x_pos = 30
                border = self.canvas.create_rectangle(
                    x_pos - 1,
                    y_pos - 1,
                    x_pos + width + 1,
                    y_pos + height + 1,
                    outline="#AFB8C5",
                    fill="#FFFFFF",
                )
                img = self.canvas.create_image(x_pos, y_pos, image=photo, anchor="nw")
                self._drawn_items.extend([border, img])

                y_pos += height + 20
                max_width = max(max_width, width + 60)

        self.canvas.configure(scrollregion=(0, 0, max_width, y_pos + 20))

    def _save_pdf(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
        if not file_path:
            return
        try:
            self.manager.save_as_pdf(self.pdf_path, file_path)
            messagebox.showinfo("تم", "تم حفظ PDF بنجاح")
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc))

    def _export_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if not file_path:
            return
        try:
            self.manager.export_excel(self.context.get("rows", []), file_path)
            messagebox.showinfo("تم", "تم تصدير Excel بنجاح")
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc))

    def _print_pdf(self):
        try:
            if os.name == "nt":
                os.startfile(self.pdf_path, "print")
            elif shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", self.pdf_path])
            elif shutil.which("open"):
                subprocess.Popen(["open", self.pdf_path])
            else:
                raise RuntimeError("No PDF opener available")
            messagebox.showinfo("تم", "تم إرسال التقرير للطباعة")
        except Exception as exc:
            messagebox.showerror("خطأ", f"تعذر تنفيذ الطباعة: {exc}")

    def _on_close(self):
        try:
            self.manager.cleanup_temp_files()
        finally:
            self.destroy()

