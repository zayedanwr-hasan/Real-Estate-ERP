import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Tuple

import ttkbootstrap as tb

from combobox_helper import bind_searchable_combobox, set_combobox_values
from db_connection import get_connection, get_db_error_message
from reporting import ReportManager, ReportPreviewWindow


class ReportsScreen:
    def __init__(self, master):
        self.master = master

        self.primary_color = "#2C3E50"
        self.soft_bg = "#F4F7F6"
        self.card_bg = "#FFFFFF"
        self.text_color = "#1F2D3D"

        self.base_font = ("Segoe UI", 11)
        self.bold_font = ("Segoe UI", 11, "bold")
        self.title_font = ("Segoe UI", 20, "bold")

        self._report_manager = ReportManager()
        self._report_preview_window = None

        self.report_to_route = {
            "كشف حساب تفصيلي": "account_statement",
            "أرصدة الموردين/عقار": "legacy",
            "أرصدة العملاء": "legacy",
            "كشف حركة صندوق": "legacy",
            "ملخص حركة الصناديق": "legacy",
            "حالة العقارات (الأراضي)": "legacy",
            "إيرادات ومصروفات عقار": "legacy",
            "طباعة دليل الحسابات": "legacy",
            "ميزان المراجعة": "legacy",
            "دفتر اليومية العامة": "legacy",
        }

        self._account_values: List[str] = []

        self._build_ui()
        self._load_accounts()

    def _build_ui(self):
        self.frame = tk.Frame(self.master, bg=self.soft_bg)
        self.frame.pack(fill="both", expand=True)

        root_card = tk.Frame(self.frame, bg=self.card_bg, highlightthickness=1, highlightbackground="#D6DEE5")
        root_card.pack(fill="both", expand=True, padx=14, pady=14)

        header = tk.Frame(root_card, bg=self.primary_color, height=58)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="شاشة التقارير", bg=self.primary_color, fg="white", font=self.title_font).pack(side="right", padx=20, pady=10)

        body = tk.Frame(root_card, bg=self.soft_bg)
        body.pack(fill="both", expand=True, padx=14, pady=14)

        card = tk.Frame(body, bg=self.card_bg, highlightthickness=1, highlightbackground="#D8E1E8")
        card.pack(fill="x", padx=8, pady=8)

        tk.Label(card, text="معاينة التقارير الاحترافية", bg=self.card_bg, fg=self.primary_color, font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=4, sticky="e", padx=14, pady=(12, 10))

        self.report_var = tk.StringVar(value="كشف حساب تفصيلي")
        self.account_var = tk.StringVar(value="")
        self.date_from_var = tk.StringVar(value=date.today().replace(day=1).strftime("%Y-%m-%d"))
        self.date_to_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.include_unposted_var = tk.BooleanVar(value=False)

        for col in range(4):
            card.grid_columnconfigure(col, weight=1)

        tk.Label(card, text="نوع التقرير", bg=self.card_bg, fg=self.text_color, font=self.bold_font, anchor="e").grid(row=1, column=3, sticky="ew", padx=8, pady=(0, 4))
        tk.Label(card, text="الحساب", bg=self.card_bg, fg=self.text_color, font=self.bold_font, anchor="e").grid(row=1, column=2, sticky="ew", padx=8, pady=(0, 4))
        tk.Label(card, text="من تاريخ", bg=self.card_bg, fg=self.text_color, font=self.bold_font, anchor="e").grid(row=1, column=1, sticky="ew", padx=8, pady=(0, 4))
        tk.Label(card, text="إلى تاريخ", bg=self.card_bg, fg=self.text_color, font=self.bold_font, anchor="e").grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))

        report_combo = ttk.Combobox(card, state="readonly", justify="right", textvariable=self.report_var, font=self.base_font)
        set_combobox_values(report_combo, ["كشف حساب تفصيلي"])
        report_combo.grid(row=2, column=3, sticky="ew", padx=8, pady=(0, 8))

        self.account_combo = ttk.Combobox(card, justify="right", textvariable=self.account_var, font=self.base_font)
        self.account_combo.grid(row=2, column=2, sticky="ew", padx=8, pady=(0, 8))
        bind_searchable_combobox(self.account_combo)

        ttk.Entry(card, justify="center", textvariable=self.date_from_var, font=self.base_font).grid(row=2, column=1, sticky="ew", padx=8, pady=(0, 8))
        ttk.Entry(card, justify="center", textvariable=self.date_to_var, font=self.base_font).grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))

        tk.Checkbutton(
            card,
            text="إدراج غير المرحلة",
            variable=self.include_unposted_var,
            bg=self.card_bg,
            fg=self.text_color,
            activebackground=self.card_bg,
            activeforeground=self.text_color,
            selectcolor=self.card_bg,
            anchor="e",
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=(4, 10))

        action_row = tk.Frame(card, bg=self.card_bg)
        action_row.grid(row=3, column=2, columnspan=2, sticky="e", padx=8, pady=(2, 12))

        tb.Button(action_row, text="عرض التقرير", bootstyle="primary", command=lambda: self._open_preview("view")).pack(side="right", padx=4)
        tb.Button(action_row, text="طباعة", bootstyle="secondary", command=lambda: self._open_preview("print")).pack(side="right", padx=4)

    def _load_accounts(self):
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT account_code, account_name FROM finance.accounts ORDER BY account_code")
                    rows = list(cur.fetchall() or [])
            self._account_values = [f"{row[0]} - {row[1]}" for row in rows]
            set_combobox_values(self.account_combo, self._account_values)
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل الحسابات"))
        finally:
            conn.close()

    @staticmethod
    def _extract_account_token(value: str) -> Tuple[str, str]:
        text = (value or "").strip()
        if not text:
            return "", ""
        if " - " in text:
            code, _ = text.split(" - ", 1)
            return code.strip(), text
        return text, text

    def _collect_filters(self) -> Dict[str, Any] | None:
        date_from = self.date_from_var.get().strip()
        date_to = self.date_to_var.get().strip()

        try:
            from_dt = datetime.strptime(date_from, "%Y-%m-%d").date()
            to_dt = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showwarning("تنبيه", "صيغة التاريخ يجب أن تكون YYYY-MM-DD")
            return None

        if from_dt > to_dt:
            messagebox.showwarning("تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return None

        account_code, account_label = self._extract_account_token(self.account_var.get())
        if not account_code:
            messagebox.showwarning("تنبيه", "يرجى اختيار حساب صحيح من القائمة")
            return None

        return {
            "account_code": account_code,
            "account_label": account_label,
            "date_from": date_from,
            "date_to": date_to,
            "posted_status": "غير مرحلة" if self.include_unposted_var.get() else "مرحلة",
        }

    def _open_preview(self, action: str):
        filters = self._collect_filters()
        if not filters:
            return

        if self._report_preview_window is not None and self._report_preview_window.winfo_exists():
            try:
                self._report_preview_window.destroy()
            except Exception:
                pass
            self._report_preview_window = None

        try:
            self._report_manager.cleanup_temp_files()
            result = self._report_manager.generate_account_statement(
                account_code=filters["account_code"],
                account_label=filters["account_label"],
                date_from=filters["date_from"],
                date_to=filters["date_to"],
                posted_status=filters["posted_status"],
                user_name="المستخدم الحالي",
            )
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc))
            return

        owner = self.master.winfo_toplevel()
        self._report_preview_window = ReportPreviewWindow(owner, self._report_manager, result)
        self._report_preview_window.focus_force()

        if action == "print":
            return

    def open_report(self, report_name):
        route = self.report_to_route.get(report_name)
        if route == "account_statement":
            self.report_var.set("كشف حساب تفصيلي")
            return

        messagebox.showinfo(
            "تنبيه",
            "تم توحيد مسار المعاينة الاحترافية. التقرير المحدد سيبقى قيد الترحيل إلى نفس المسار.",
        )


def open_report(master, report_name):
    screen = ReportsScreen(master)
    if report_name:
        screen.open_report(report_name)
    return screen

