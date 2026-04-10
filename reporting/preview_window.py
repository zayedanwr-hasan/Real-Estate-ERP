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

        self.configure(bg="#E7EBEF")
        self.title(self.context.get("report_title", "Print Preview"))

        self.zoom_value = tk.StringVar(value="150%")
        self.zoom_factor_map = {"100%": 1.0, "125%": 1.25, "150%": 1.5, "200%": 2.0, "300%": 3.0}

        self._images: list[ImageTk.PhotoImage] = []
        self._drawn_items: list[int] = []
        self._redraw_job: str | None = None
        self._recenter_next_draw = True

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
        toolbar = tk.Frame(self, bg="#E2E7EC", highlightthickness=1, highlightbackground="#C7CED7")
        toolbar.pack(side="top", fill="x")

        tk.Button(toolbar, text="Print", command=self._print_pdf, bg="#FFFFFF", fg="#1F2D3D", relief="groove").pack(side="right", padx=4, pady=6)
        tk.Button(toolbar, text="Save as PDF", command=self._save_pdf, bg="#FFFFFF", fg="#1F2D3D", relief="groove").pack(side="right", padx=4, pady=6)
        tk.Button(toolbar, text="Export Excel", command=self._export_excel, bg="#FFFFFF", fg="#1F2D3D", relief="groove").pack(side="right", padx=4, pady=6)

        ttk.Combobox(toolbar, values=list(self.zoom_factor_map.keys()), state="readonly", textvariable=self.zoom_value, width=8, justify="center").pack(side="right", padx=4, pady=6)
        tk.Label(toolbar, text="Zoom", bg="#E2E7EC", fg="#1F2D3D").pack(side="right", padx=(8, 2), pady=6)
        self.zoom_value.trace_add("write", self._on_zoom_changed)

        frame = tk.Frame(self, bg="#D5DCE3")
        frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(frame, bg="#D5DCE3", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        ybar = ttk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        xbar = ttk.Scrollbar(frame, orient="horizontal", command=self.canvas.xview)
        ybar.pack(side="right", fill="y")
        xbar.pack(side="bottom", fill="x")
        self.canvas.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)

    def _on_canvas_configure(self, _event=None):
        self._schedule_redraw()

    def _schedule_redraw(self):
        if self._redraw_job is not None:
            self.after_cancel(self._redraw_job)
        self._redraw_job = self.after(60, self._draw_pdf)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_shift_mousewheel(self, event):
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_zoom_changed(self, _name: str, _index: str, _mode: str):
        self._recenter_next_draw = True
        self._draw_pdf()

    @staticmethod
    def _dim(value: Any) -> int:
        return int(value() if callable(value) else value)

    def _draw_pdf(self):
        self._redraw_job = None
        if not os.path.exists(self.pdf_path):
            messagebox.showerror("خطأ", "ملف التقرير غير موجود")
            return

        for item in self._drawn_items:
            self.canvas.delete(item)
        self._drawn_items.clear()
        self._images.clear()

        zoom = self.zoom_factor_map.get(self.zoom_value.get(), 1.5)
        matrix_scale = zoom

        self.update_idletasks()
        canvas_width = max(self.canvas.winfo_width(), 1)
        canvas_height = max(self.canvas.winfo_height(), 1)
        page_gap = 20

        pages: list[tuple[ImageTk.PhotoImage, int, int]] = []

        with fitz.open(self.pdf_path) as doc:
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(matrix_scale, matrix_scale), alpha=False)
                width = self._dim(pix.width)
                height = self._dim(pix.height)
                image = Image.frombytes("RGB", (width, height), pix.samples)
                photo = ImageTk.PhotoImage(image)
                self._images.append(photo)
                pages.append((photo, width, height))

        if not pages:
            self.canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
            return

        total_height = sum(height for _, _, height in pages) + page_gap * (len(pages) - 1)
        y_pos = max((canvas_height - total_height) // 2, 20)

        content_left = 0
        content_right = canvas_width

        for photo, width, height in pages:
            x_center = canvas_width // 2
            y_center = y_pos + (height // 2)
            left = x_center - (width // 2)
            right = left + width

            border = self.canvas.create_rectangle(
                left - 1,
                y_pos - 1,
                right + 1,
                y_pos + height + 1,
                outline="#AFB8C5",
                fill="#FFFFFF",
            )
            img = self.canvas.create_image(x_center, y_center, image=photo, anchor="center")
            self._drawn_items.extend([border, img])

            content_left = min(content_left, left - 20)
            content_right = max(content_right, right + 20)
            y_pos += height + page_gap

        content_bottom = max(y_pos + 20, canvas_height)
        self.canvas.configure(scrollregion=(content_left, 0, content_right, content_bottom))

        if self._recenter_next_draw:
            scroll_width = content_right - content_left
            scroll_height = content_bottom

            if scroll_width > canvas_width:
                centered_left = ((content_left + content_right) / 2.0) - (canvas_width / 2.0)
                x_fraction = (centered_left - content_left) / max(scroll_width - canvas_width, 1)
                self.canvas.xview_moveto(max(0.0, min(1.0, x_fraction)))
            else:
                self.canvas.xview_moveto(0.0)

            if scroll_height > canvas_height:
                centered_top = max((total_height - canvas_height) / 2.0, 0.0)
                y_fraction = centered_top / max(scroll_height - canvas_height, 1)
                self.canvas.yview_moveto(max(0.0, min(1.0, y_fraction)))
            else:
                self.canvas.yview_moveto(0.0)

            self._recenter_next_draw = False

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
