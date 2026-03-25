import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import ttkbootstrap as tb

from backup_service import create_json_backup, restore_json_backup
from windows_task_scheduler import (
    TASK_NAME,
    create_daily_backup_task,
    delete_daily_backup_task,
    query_task,
    task_exists,
)
from db_connection import get_connection


class SettingsScreen:
    def __init__(self, master, current_user=None):
        self.master = master
        self.current_user = current_user or {}

        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.bg_color = "#f4f7f6"

        self.base_font = ("Segoe UI", 11)
        self.bold_font = ("Segoe UI", 11, "bold")
        self.title_font = ("Segoe UI", 20, "bold")

        self.settings_path = os.path.join(os.path.dirname(__file__), "app_settings.json")
        self.defaults = {
            "company_name": "",
            "currency": "EGP",
            "date_format": "YYYY-MM-DD",
            "theme": "flatly",
            "fiscal_year_start": "01-01",
            "auto_backup": False,
            "backup_path": "",
            "backup_time": "23:00",
        }

        self.vars = {
            "company_name": tk.StringVar(),
            "currency": tk.StringVar(),
            "date_format": tk.StringVar(),
            "theme": tk.StringVar(),
            "fiscal_year_start": tk.StringVar(),
            "auto_backup": tk.BooleanVar(),
            "backup_path": tk.StringVar(),
            "backup_time": tk.StringVar(),
        }

        self._setup_styles()
        self._build_layout()
        self._load_settings_to_form()

    def _setup_styles(self):
        style = tb.Style()
        style.configure("App.Settings.Root.TFrame", background=self.bg_color)
        style.configure("App.Settings.Header.TFrame", background=self.primary_color)
        style.configure(
            "App.Settings.Header.TLabel",
            background=self.primary_color,
            foreground="white",
            font=self.title_font,
        )
        style.configure(
            "App.Settings.Card.TFrame",
            background="white",
            relief="solid",
            borderwidth=1,
            bordercolor="#d1d8e0",
        )
        style.configure(
            "App.Settings.Label.TLabel",
            background="white",
            foreground=self.primary_color,
            font=("Segoe UI", 12, "bold"),
            anchor="e",
        )

    def _build_layout(self):
        self.root = ttk.Frame(self.master, style="App.Settings.Root.TFrame", padding=12)
        self.root.pack(fill="both", expand=True)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, style="App.Settings.Header.TFrame", padding=(14, 10))
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(header, text="شاشة الإعدادات", style="App.Settings.Header.TLabel").pack(side="right")

        card = ttk.Frame(self.root, style="App.Settings.Card.TFrame", padding=16)
        card.grid(row=1, column=0, sticky="nsew")
        for c in range(3):
            card.grid_columnconfigure(c, weight=1)

        self._label(card, "اسم الشركة").grid(row=0, column=2, sticky="e", pady=(0, 4))
        ttk.Entry(card, textvariable=self.vars["company_name"], justify="right", font=self.base_font).grid(
            row=1, column=2, sticky="ew", padx=(8, 0), pady=(0, 10)
        )

        self._label(card, "العملة").grid(row=0, column=1, sticky="e", pady=(0, 4))
        ttk.Entry(card, textvariable=self.vars["currency"], justify="right", font=self.base_font).grid(
            row=1, column=1, sticky="ew", padx=8, pady=(0, 10)
        )

        self._label(card, "بداية السنة المالية (MM-DD)").grid(row=0, column=0, sticky="e", pady=(0, 4))
        ttk.Entry(card, textvariable=self.vars["fiscal_year_start"], justify="center", font=self.base_font).grid(
            row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 10)
        )

        self._label(card, "تنسيق التاريخ").grid(row=2, column=2, sticky="e", pady=(0, 4))
        ttk.Combobox(
            card,
            textvariable=self.vars["date_format"],
            values=["YYYY-MM-DD", "DD-MM-YYYY", "MM/DD/YYYY"],
            state="readonly",
            justify="center",
            font=self.base_font,
        ).grid(row=3, column=2, sticky="ew", padx=(8, 0), pady=(0, 10))

        self._label(card, "المظهر").grid(row=2, column=1, sticky="e", pady=(0, 4))
        ttk.Combobox(
            card,
            textvariable=self.vars["theme"],
            values=["flatly", "litera", "cosmo", "minty", "journal", "sandstone"],
            state="readonly",
            justify="center",
            font=self.base_font,
        ).grid(row=3, column=1, sticky="ew", padx=8, pady=(0, 10))

        tb.Checkbutton(
            card,
            text="تفعيل النسخ الاحتياطي التلقائي",
            variable=self.vars["auto_backup"],
            bootstyle="round-toggle",
        ).grid(row=3, column=0, sticky="e", padx=(0, 8), pady=(0, 10))

        self._label(card, "وقت النسخ التلقائي (HH:MM)").grid(row=4, column=1, sticky="e", pady=(0, 4))
        ttk.Entry(card, textvariable=self.vars["backup_time"], justify="center", font=self.base_font).grid(
            row=5, column=1, sticky="ew", padx=8, pady=(0, 12)
        )

        self._label(card, "مسار النسخ الاحتياطي").grid(row=4, column=2, sticky="e", pady=(0, 4))
        ttk.Entry(card, textvariable=self.vars["backup_path"], justify="left", font=self.base_font).grid(
            row=5, column=0, sticky="ew", pady=(0, 12), padx=(0, 8)
        )
        tb.Button(card, text="اختيار المسار", bootstyle="secondary", command=self._pick_backup_path).grid(
            row=5, column=2, sticky="ew", padx=(8, 0), pady=(0, 12)
        )

        actions = ttk.Frame(card, style="App.Settings.Card.TFrame")
        actions.grid(row=6, column=0, columnspan=3, sticky="ew")
        actions.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        tb.Button(actions, text="نسخ احتياطي الآن", bootstyle="primary", command=self._backup_now).grid(
            row=0, column=6, sticky="ew", padx=4
        )
        tb.Button(actions, text="Restore", bootstyle="secondary", command=self._restore_backup).grid(
            row=0, column=5, sticky="ew", padx=4
        )
        tb.Button(actions, text="جدولة يومية", bootstyle="info", command=self._schedule_backup_task).grid(
            row=0, column=4, sticky="ew", padx=4
        )
        tb.Button(actions, text="إلغاء الجدولة", bootstyle="warning", command=self._remove_backup_task).grid(
            row=0, column=3, sticky="ew", padx=4
        )
        tb.Button(actions, text="حفظ الإعدادات", bootstyle="success", command=self._save_settings).grid(
            row=0, column=2, sticky="ew", padx=4
        )
        tb.Button(actions, text="إعادة الافتراضي", bootstyle="warning", command=self._reset_defaults).grid(
            row=0, column=1, sticky="ew", padx=4
        )
        tb.Button(actions, text="إغلاق", bootstyle="danger", command=self._close).grid(
            row=0, column=0, sticky="ew", padx=4
        )

        self.task_status_label = ttk.Label(actions, text="", style="App.Settings.Label.TLabel")
        self.task_status_label.grid(row=1, column=0, columnspan=7, sticky="e", pady=(8, 0))
        self._refresh_task_status()

    def _label(self, parent, text):
        return ttk.Label(parent, text=text, style="App.Settings.Label.TLabel")

    def _pick_backup_path(self):
        path = filedialog.askdirectory()
        if path:
            self.vars["backup_path"].set(path)

    def _read_settings_file(self):
        if not os.path.exists(self.settings_path):
            return dict(self.defaults)
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            merged = dict(self.defaults)
            merged.update({k: loaded.get(k, v) for k, v in self.defaults.items()})
            return merged
        except Exception:
            return dict(self.defaults)

    def _load_settings_to_form(self):
        settings = self._read_settings_file()
        for key, var in self.vars.items():
            var.set(settings.get(key, self.defaults[key]))

    def _collect_form(self):
        return {
            "company_name": self.vars["company_name"].get().strip(),
            "currency": self.vars["currency"].get().strip(),
            "date_format": self.vars["date_format"].get().strip(),
            "theme": self.vars["theme"].get().strip(),
            "fiscal_year_start": self.vars["fiscal_year_start"].get().strip(),
            "auto_backup": bool(self.vars["auto_backup"].get()),
            "backup_path": self.vars["backup_path"].get().strip(),
            "backup_time": self.vars["backup_time"].get().strip(),
        }

    def _validate_time(self, value: str) -> bool:
        if len(value) != 5 or value[2] != ":":
            return False
        try:
            hh = int(value[:2])
            mm = int(value[3:])
            return 0 <= hh <= 23 and 0 <= mm <= 59
        except ValueError:
            return False

    def _validate_settings(self, payload):
        if not payload["currency"]:
            messagebox.showwarning("تنبيه", "حقل العملة مطلوب")
            return False

        fy = payload["fiscal_year_start"]
        if len(fy) != 5 or fy[2] != "-":
            messagebox.showwarning("تنبيه", "بداية السنة المالية يجب أن تكون بصيغة MM-DD")
            return False

        try:
            month = int(fy[:2])
            day = int(fy[3:])
            if month < 1 or month > 12 or day < 1 or day > 31:
                raise ValueError
        except ValueError:
            messagebox.showwarning("تنبيه", "قيمة بداية السنة المالية غير صحيحة")
            return False

        if payload["auto_backup"] and not payload["backup_path"]:
            messagebox.showwarning("تنبيه", "اختر مسار النسخ الاحتياطي عند تفعيل النسخ التلقائي")
            return False

        if not self._validate_time(payload["backup_time"]):
            messagebox.showwarning("تنبيه", "وقت النسخ التلقائي يجب أن يكون بصيغة HH:MM")
            return False

        return True

    def _is_admin(self):
        return (self.current_user or {}).get("role") == "admin"

    def _save_settings(self):
        if not self._is_admin():
            messagebox.showwarning("تنبيه", "تعديل الإعدادات متاح للمسؤول فقط")
            return

        payload = self._collect_form()
        if not self._validate_settings(payload):
            return

        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("نجاح", "تم حفظ الإعدادات بنجاح")
        except Exception as exc:
            messagebox.showerror("خطأ", f"تعذر حفظ الإعدادات: {exc}")

    def _backup_now(self):
        settings = self._collect_form()
        backup_root = settings.get("backup_path") or os.path.join(os.path.dirname(__file__), "backups")
        try:
            file_path = create_json_backup(
                backup_root=backup_root,
                created_by=(self.current_user or {}).get("username", "system"),
            )
            messagebox.showinfo("نجاح", f"تم إنشاء نسخة احتياطية بنجاح:\n{file_path}")
        except Exception as exc:
            messagebox.showerror("خطأ", f"فشل إنشاء النسخة الاحتياطية: {exc}")

    def _restore_backup(self):
        if not self._is_admin():
            messagebox.showwarning("تنبيه", "الاستعادة متاحة للمسؤول فقط")
            return

        file_path = filedialog.askopenfilename(
            title="اختر ملف النسخة الاحتياطية",
            filetypes=[("JSON Backup", "*.json")],
        )
        if not file_path:
            return

        if not messagebox.askyesno(
            "تأكيد الاستعادة",
            "سيتم استبدال البيانات الحالية بالنسخة المختارة. هل تريد المتابعة؟",
        ):
            return

        try:
            counts = restore_json_backup(file_path)
            summary = "\n".join([f"- {k}: {v}" for k, v in counts.items()])
            messagebox.showinfo("نجاح", f"تمت الاستعادة بنجاح:\n{summary}")
        except Exception as exc:
            messagebox.showerror("خطأ", f"فشل تنفيذ الاستعادة: {exc}")

    def _refresh_task_status(self):
        try:
            if task_exists():
                self.task_status_label.configure(text=f"حالة الجدولة: مفعلة ({TASK_NAME})")
            else:
                self.task_status_label.configure(text="حالة الجدولة: غير مفعلة")
        except Exception as exc:
            self.task_status_label.configure(text=f"تعذر قراءة حالة الجدولة: {exc}")

    def _schedule_backup_task(self):
        if not self._is_admin():
            messagebox.showwarning("تنبيه", "الجدولة متاحة للمسؤول فقط")
            return

        payload = self._collect_form()
        if not self._validate_settings(payload):
            return

        try:
            self._save_settings()
            job_script = os.path.join(os.path.dirname(__file__), "backup_job.py")
            create_daily_backup_task(payload["backup_time"], sys.executable, job_script)
            self._refresh_task_status()
            messagebox.showinfo("نجاح", "تم إنشاء/تحديث جدولة النسخ الاحتياطي اليومية")
        except Exception as exc:
            messagebox.showerror("خطأ", f"فشل إنشاء الجدولة: {exc}")

    def _remove_backup_task(self):
        if not self._is_admin():
            messagebox.showwarning("تنبيه", "إلغاء الجدولة متاح للمسؤول فقط")
            return

        try:
            delete_daily_backup_task()
            self._refresh_task_status()
            messagebox.showinfo("نجاح", "تم إلغاء جدولة النسخ الاحتياطي")
        except Exception as exc:
            messagebox.showerror("خطأ", f"فشل إلغاء الجدولة: {exc}")

    def _test_db_connection(self):
        conn = get_connection()
        if not conn:
            messagebox.showerror("فشل", "تعذر الاتصال بقاعدة البيانات")
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            schedule_info = query_task() if task_exists() else "لا توجد جدولة حالياً"
            messagebox.showinfo("نجاح", f"تم الاتصال بقاعدة البيانات بنجاح\n\n{schedule_info}")
        except Exception as exc:
            messagebox.showerror("فشل", f"فشل اختبار الاتصال: {exc}")
        finally:
            conn.close()

    def _close(self):
        parent = self.master.winfo_toplevel()
        if isinstance(parent, (tk.Tk, tk.Toplevel)):
            self.root.destroy()

