import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Tuple

import ttkbootstrap as tb

from combobox_helper import bind_searchable_combobox, set_combobox_values
from reporting import ReportManager, ReportPreviewWindow


class ReportsScreen:
    def __init__(self, master):
        self.master = master

        self.primary_color = "#2C3E50"
        self.soft_bg = "#E3E7EB"
        self.card_bg = "#f0f0f0"
        self.text_color = "#1F2D3D"

        self.base_font = ("Segoe UI", 11)
        self.bold_font = ("Segoe UI", 11, "bold")

        self._report_manager = ReportManager()
        self._report_preview_window = None

        self._account_values: List[str] = []
        self._property_values: List[str] = []
        self._fund_values: List[str] = []

        self._build_ui()
        self._load_picker_values()
        self._apply_filter_visibility()

    def _build_ui(self):
        self.frame = tk.Frame(self.master, bg=self.soft_bg)
        self.frame.pack(fill="both", expand=True)

        card = tk.Frame(
            self.frame,
            bg=self.card_bg,
            width=550,
            height=350,
            highlightthickness=1,
            highlightbackground="#C9D0D8",
            bd=0,
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        content = tk.Frame(card, bg=self.card_bg)
        content.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(content, text="معايير التقرير", bg=self.card_bg, fg=self.primary_color, font=("Segoe UI", 14, "bold"), anchor="e").pack(fill="x", pady=(0, 10))

        self.report_var = tk.StringVar(value="كشف حساب تفصيلي")
        self.account_var = tk.StringVar(value="")
        self.property_var = tk.StringVar(value="")
        self.fund_var = tk.StringVar(value="")
        self.date_from_var = tk.StringVar(value=date.today().replace(day=1).strftime("%Y-%m-%d"))
        self.date_to_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.status_var = tk.StringVar(value="مرحلة")

        self.filters_panel = tk.Frame(content, bg=self.card_bg)
        self.filters_panel.pack(fill="x")

        # Report type row
        report_row = tk.Frame(self.filters_panel, bg=self.card_bg)
        report_row.pack(fill="x", pady=4)
        tk.Label(report_row, text="نوع التقرير", bg=self.card_bg, fg=self.text_color, font=self.bold_font, anchor="e", width=12).pack(side="right", padx=(10, 0))
        self.report_combo = ttk.Combobox(report_row, justify="right", textvariable=self.report_var, font=self.base_font)
        self.report_combo.pack(side="right", fill="x", expand=True)
        set_combobox_values(self.report_combo, self._report_manager.get_available_report_types())
        bind_searchable_combobox(self.report_combo)
        self.report_combo.bind("<<ComboboxSelected>>", lambda _e: self._apply_filter_visibility())

        # Dynamic rows
        self.row_account = tk.Frame(self.filters_panel, bg=self.card_bg)
        tk.Label(self.row_account, text="الحساب", bg=self.card_bg, fg=self.text_color, font=self.bold_font, anchor="e", width=12).pack(side="right", padx=(10, 0))
        self.account_combo = ttk.Combobox(self.row_account, justify="right", textvariable=self.account_var, font=self.base_font)
        self.account_combo.pack(side="right", fill="x", expand=True)
        bind_searchable_combobox(self.account_combo)

        self.row_property = tk.Frame(self.filters_panel, bg=self.card_bg)
        tk.Label(self.row_property, text="العقار", bg=self.card_bg, fg=self.text_color, font=self.bold_font, anchor="e", width=12).pack(side="right", padx=(10, 0))
        self.property_combo = ttk.Combobox(self.row_property, justify="right", textvariable=self.property_var, font=self.base_font)
        self.property_combo.pack(side="right", fill="x", expand=True)
        bind_searchable_combobox(self.property_combo)

        self.row_fund = tk.Frame(self.filters_panel, bg=self.card_bg)
        tk.Label(self.row_fund, text="الصندوق", bg=self.card_bg, fg=self.text_color, font=self.bold_font, anchor="e", width=12).pack(side="right", padx=(10, 0))
        self.fund_combo = ttk.Combobox(self.row_fund, justify="right", textvariable=self.fund_var, font=self.base_font)
        self.fund_combo.pack(side="right", fill="x", expand=True)
        bind_searchable_combobox(self.fund_combo)

        self.row_status = tk.Frame(self.filters_panel, bg=self.card_bg)
        tk.Label(self.row_status, text="الحالة", bg=self.card_bg, fg=self.text_color, font=self.bold_font, anchor="e", width=12).pack(side="right", padx=(10, 0))
        status_combo = ttk.Combobox(self.row_status, state="readonly", justify="right", textvariable=self.status_var, font=self.base_font)
        status_combo.pack(side="right", fill="x", expand=True)
        set_combobox_values(status_combo, ["مرحلة", "غير مرحلة"])

        self.row_dates = tk.Frame(self.filters_panel, bg=self.card_bg)
        tk.Label(self.row_dates, text="الفترة", bg=self.card_bg, fg=self.text_color, font=self.bold_font, anchor="e", width=12).pack(side="right", padx=(10, 0))
        dates_inputs = tk.Frame(self.row_dates, bg=self.card_bg)
        dates_inputs.pack(side="right", fill="x", expand=True)
        ttk.Entry(dates_inputs, justify="center", textvariable=self.date_to_var, font=self.base_font, width=12).pack(side="right")
        tk.Label(dates_inputs, text="إلى", bg=self.card_bg, fg=self.text_color, font=self.bold_font).pack(side="right", padx=4)
        ttk.Entry(dates_inputs, justify="center", textvariable=self.date_from_var, font=self.base_font, width=12).pack(side="right")
        tk.Label(dates_inputs, text="من", bg=self.card_bg, fg=self.text_color, font=self.bold_font).pack(side="right", padx=4)

        action_row = tk.Frame(content, bg=self.card_bg)
        action_row.pack(side="bottom", fill="x", pady=(12, 0))
        actions_left = tk.Frame(action_row, bg=self.card_bg)
        actions_left.pack(side="left", anchor="w")
        tb.Button(actions_left, text="عرض التقرير", bootstyle="primary", command=lambda: self._open_preview("view")).pack(side="left", padx=(0, 6))
        tb.Button(actions_left, text="طباعة", bootstyle="secondary", command=lambda: self._open_preview("print")).pack(side="left")

    def _safe_extract_token(self, value: str) -> Tuple[str, str]:
        text = (value or "").strip()
        if not text:
            return "", ""
        if " - " in text:
            code, _ = text.split(" - ", 1)
            return code.strip(), text
        return text, text

    def _load_picker_values(self):
        try:
            self._account_values = self._report_manager.fetch_accounts_for_picker()
        except Exception:
            self._account_values = []
        set_combobox_values(self.account_combo, self._account_values)

        try:
            self._property_values = self._report_manager.fetch_properties_for_picker()
        except Exception:
            self._property_values = []
        set_combobox_values(self.property_combo, self._property_values)

        try:
            self._fund_values = self._report_manager.fetch_funds_for_picker()
        except Exception:
            self._fund_values = []
        set_combobox_values(self.fund_combo, self._fund_values)

    def _required_filters(self) -> List[str]:
        config = self._report_manager.get_report_config(self.report_var.get().strip())
        return list(config.get("required_filters", []))

    def _apply_filter_visibility(self):
        for row in (self.row_account, self.row_property, self.row_fund, self.row_dates, self.row_status):
            row.pack_forget()

        required = set(self._required_filters())

        if "account_code" in required:
            self.row_account.pack(fill="x", pady=4)
        if "property_id" in required:
            self.row_property.pack(fill="x", pady=4)
        if "fund_code" in required:
            self.row_fund.pack(fill="x", pady=4)
        if "date_from" in required or "date_to" in required:
            self.row_dates.pack(fill="x", pady=4)
        if "posted_status" in required:
            self.row_status.pack(fill="x", pady=4)

    def _validate_dates_if_needed(self, required: set[str]) -> Dict[str, str] | None:
        data: Dict[str, str] = {}
        if "date_from" not in required and "date_to" not in required:
            return data

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

        data["date_from"] = date_from
        data["date_to"] = date_to
        return data

    def _collect_filters(self) -> Dict[str, Any] | None:
        required = set(self._required_filters())
        filters: Dict[str, Any] = {}

        date_data = self._validate_dates_if_needed(required)
        if date_data is None:
            return None
        filters.update(date_data or {})

        if "account_code" in required:
            account_code, account_label = self._safe_extract_token(self.account_var.get())
            if not account_code:
                messagebox.showwarning("تنبيه", "يرجى اختيار حساب صحيح من القائمة")
                return None
            filters["account_code"] = account_code
            filters["account_label"] = account_label

        if "property_id" in required:
            property_id, property_label = self._safe_extract_token(self.property_var.get())
            if not property_id:
                messagebox.showwarning("تنبيه", "يرجى اختيار عقار صحيح من القائمة")
                return None
            filters["property_id"] = property_id
            filters["property_label"] = property_label

        if "fund_code" in required:
            fund_code, fund_label = self._safe_extract_token(self.fund_var.get())
            if not fund_code:
                messagebox.showwarning("تنبيه", "يرجى اختيار صندوق صحيح من القائمة")
                return None
            filters["fund_code"] = fund_code
            filters["fund_label"] = fund_label

        if "posted_status" in required:
            filters["posted_status"] = self.status_var.get().strip() or "مرحلة"

        return filters

    def _open_preview(self, action: str):
        report_type = self.report_var.get().strip()
        if not report_type:
            messagebox.showwarning("تنبيه", "يرجى اختيار نوع التقرير")
            return

        filters = self._collect_filters()
        if filters is None:
            return

        if self._report_preview_window is not None and self._report_preview_window.winfo_exists():
            try:
                self._report_preview_window.destroy()
            except Exception:
                pass
            self._report_preview_window = None

        try:
            result = self._report_manager.generate_report(
                report_type=report_type,
                filters=filters,
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
        requested = (report_name or "").strip()
        available = self._report_manager.get_available_report_types()

        # Keep compatibility with older dashboard label.
        if requested == "أرصدة الموردين/عقار":
            requested = "أرصدة الموردين"

        if requested in available:
            self.report_var.set(requested)
            self._apply_filter_visibility()
            return

        messagebox.showinfo("تنبيه", "التقرير المحدد غير متاح حالياً ضمن محرك التقارير الجديد")


def open_report(master, report_name):
    screen = ReportsScreen(master)
    if report_name:
        screen.open_report(report_name)
    return screen

