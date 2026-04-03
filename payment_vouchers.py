import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog

import ttkbootstrap as ttk

from app_constants import (
    CUSTOMER_CONTROL_ACCOUNT_CODE,
    SYSTEM_NAME,
    VENDOR_CONTROL_ACCOUNT_CODE,
    VOUCHER_TYPE_PAYMENT,
)
from combobox_helper import bind_searchable_combobox, set_combobox_values
from db_connection import get_connection, get_db_error_message


class PaymentVoucherScreen:
    def __init__(self, master):
        self.master = master

        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.bg_color = "#f4f7f6"

        self.voucher_id_var = tk.StringVar(value="تلقائي")
        self.reference_no_var = tk.StringVar(value="10001")
        self.voucher_type_var = tk.StringVar(value=VOUCHER_TYPE_PAYMENT)
        self.currency_var = tk.StringVar(value="ريال يمني")
        self.fund_var = tk.StringVar(value="الصندوق الرئيسي")

        self.beneficiary_id_var = tk.StringVar()
        self.beneficiary_var = tk.StringVar()

        self.amount_var = tk.StringVar(value="0.00")
        self.amount_words_var = tk.StringVar(value="")
        self.notes_var = tk.StringVar()

        self.account_display_to_code = {}
        self.account_code_to_name = {}
        self.account_code_to_display = {}
        self.fund_display_to_code = {}

        self.beneficiary_display_to_data = {}

        self.ledger_has_vendor_id = False
        self.ledger_has_customer_id = False
        self.ledger_has_property_id = False

        self.line_items = []

        # Optional safety check: block save if selected fund balance is insufficient.
        self.enforce_fund_balance_check = False
        self.field_label_width = 15

        self._setup_styles()

        self.frame = ttk.Frame(master, style="App.Payment.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.main_card = ttk.Frame(self.frame, style="App.Payment.Card.TFrame")
        self.main_card.pack(fill="both", expand=True, padx=12, pady=12)

        self._build_header_buttons()
        self._build_form_content()

        self.load_accounts()
        self.load_beneficiaries()
        self._reset_and_new()

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("App.Payment.Root.TFrame", background=self.bg_color)
        style.configure("App.Payment.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("App.Payment.Header.TFrame", background=self.primary_color)
        style.configure("App.Payment.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 18, "bold"))
        style.configure("App.Payment.Content.TFrame", background="white")
        style.configure(
            "App.Payment.FieldLabel.TLabel",
            background=self.sidebar_color,
            foreground=self.text_color,
            font=("Segoe UI", 11, "bold"),
            anchor="center",
            padding=6,
        )
        # Flat inputs for cleaner look.
        style.configure(
            "App.Payment.Field.TEntry",
            fieldbackground="white",
            foreground=self.primary_color,
            font=("Segoe UI", 11, "bold"),
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "App.Payment.Field.TCombobox",
            fieldbackground="white",
            foreground=self.primary_color,
            font=("Segoe UI", 11, "bold"),
            borderwidth=0,
            relief="flat",
        )
        style.configure("App.Payment.Hint.TLabel", background="white", foreground=self.sidebar_color, font=("Segoe UI", 10, "bold"), anchor="e")

        style.configure("App.Payment.Primary.TButton", background="#2980b9", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Payment.Success.TButton", background="#27ae60", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Payment.Warning.TButton", background="#f1c40f", foreground="#2c3e50", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Payment.Danger.TButton", background="#e74c3c", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Payment.Info.TButton", background="#8e44ad", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Payment.History.TButton", background="#16a085", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))

        for btn_style in (
            "App.Payment.Primary.TButton",
            "App.Payment.Success.TButton",
            "App.Payment.Warning.TButton",
            "App.Payment.Danger.TButton",
            "App.Payment.Info.TButton",
            "App.Payment.History.TButton",
        ):
            style.map(btn_style, background=[("active", self.accent_color), ("pressed", self.accent_color)], foreground=[("active", "white"), ("pressed", "white")])

        style.configure("App.Payment.Treeview", background="white", fieldbackground="white", foreground=self.primary_color, rowheight=32, font=("Segoe UI", 10, "bold"))
        style.configure("App.Payment.Treeview.Heading", background=self.primary_color, foreground="white", font=("Segoe UI", 10, "bold"))
        style.map("App.Payment.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "white")])

    def _build_header_buttons(self):
        header = ttk.Frame(self.main_card, style="App.Payment.Header.TFrame", height=68)
        header.pack(fill="x", side="top")
        ttk.Label(header, text=f"سند صرف - {SYSTEM_NAME}", style="App.Payment.Header.TLabel").pack(side="right", padx=30, pady=15)

        btn_group = ttk.Frame(header, style="App.Payment.Header.TFrame")
        btn_group.pack(side="left", padx=20)

        btn_data = [
            ("جديد", "App.Payment.Primary.TButton", self._reset_and_new),
            ("حفظ", "App.Payment.Success.TButton", lambda: self.save_voucher(is_update=False)),
            ("تعديل", "App.Payment.Warning.TButton", self._update_voucher),
            ("حذف", "App.Payment.Danger.TButton", self._delete_voucher),
            ("بحث", "App.Payment.Primary.TButton", self._search_voucher),
            ("السجلات", "App.Payment.History.TButton", self._show_history),
            ("طباعة", "App.Payment.Info.TButton", self._print_voucher),
        ]
        for txt, style_name, cmd in btn_data:
            ttk.Button(btn_group, text=txt, style=style_name, width=9, command=cmd).pack(side="left", padx=5)

    def _build_form_content(self):
        self.container = ttk.Frame(self.main_card, style="App.Payment.Content.TFrame", padding=(0, 8))
        self.container.pack(fill="both", expand=True)

        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=0)
        self.container.grid_rowconfigure(1, weight=0)
        self.container.grid_rowconfigure(2, weight=0)
        self.container.grid_rowconfigure(3, weight=7)

        self._build_header_section(row=0)
        self._build_beneficiary_section(row=1)
        self._build_amount_notes_section(row=2)
        self._build_lines_table(row=3)

    def _create_compact_field(
        self,
        parent,
        label_text,
        widget_type="entry",
        label_width=None,
        text_height=2,
        compact=False,
        col=0,
        expand=False,
        group_padx=(0, 0),
        pady=10,
        **kwargs,
    ):
        grp = ttk.Frame(parent, style="App.Payment.Content.TFrame")
        grp.grid(row=0, column=col, sticky="ew", padx=group_padx, pady=pady)
        grp.columnconfigure(0, weight=1 if expand else 0)

        if widget_type == "entry":
            field = ttk.Entry(grp, style="App.Payment.Field.TEntry", justify="right", **kwargs)
        elif widget_type == "combo":
            field = ttk.Combobox(grp, style="App.Payment.Field.TCombobox", justify="right", **kwargs)
        else:
            field = tk.Text(grp, font=("Segoe UI", 11, "bold"), bd=0, relief="flat", height=text_height)

        if compact:
            field.grid(row=0, column=0, sticky="e", padx=(0, 5))
        else:
            field.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ttk.Label(
            grp,
            text=label_text,
            style="App.Payment.FieldLabel.TLabel",
            width=label_width or self.field_label_width,
        ).grid(row=0, column=1, sticky="e")
        return field

    def _build_header_section(self, row):
        # Row A: [Voucher No] -> [Date] -> [Currency] -> [Fund]
        row_wrap = ttk.Frame(self.container, style="App.Payment.Content.TFrame")
        row_wrap.grid(row=row, column=0, sticky="ew")
        row_wrap.columnconfigure(0, weight=3, minsize=360)
        row_wrap.columnconfigure(1, weight=1)
        row_wrap.columnconfigure(2, weight=1)
        row_wrap.columnconfigure(3, weight=1)

        self.ent_id = self._create_compact_field(
            row_wrap,
            "رقم السند :",
            textvariable=self.voucher_id_var,
            state="readonly",
            label_width=self.field_label_width,
            compact=True,
            width=12,
            col=3,
            group_padx=(15, 0),
        )
        self.ent_date = self._create_date_field(
            row_wrap,
            "التاريخ :",
            col=2,
            label_width=self.field_label_width,
            group_padx=(15, 0),
        )
        self.combo_currency = self._create_compact_field(
            row_wrap,
            "العملة :",
            widget_type="combo",
            state="readonly",
            textvariable=self.currency_var,
            values=("ريال يمني", "ريال سعودي", "دولار"),
            label_width=self.field_label_width,
            compact=True,
            width=12,
            col=1,
            group_padx=(15, 0),
        )
        self.combo_fund = self._create_compact_field(
            row_wrap,
            "الصندوق :",
            widget_type="combo",
            state="normal",
            textvariable=self.fund_var,
            label_width=self.field_label_width,
            col=0,
            expand=True,
            group_padx=(0, 0),
        )
        bind_searchable_combobox(self.combo_fund)

    def _build_beneficiary_section(self, row):
        # Row B: [Beneficiary ID] -> [Beneficiary Name stretched] -> [Amount] -> [Amount in Letters]
        row_wrap = ttk.Frame(self.container, style="App.Payment.Content.TFrame")
        row_wrap.grid(row=row, column=0, sticky="ew")
        row_wrap.columnconfigure(0, weight=3, minsize=420)
        row_wrap.columnconfigure(1, weight=1)
        row_wrap.columnconfigure(2, weight=3)
        row_wrap.columnconfigure(3, weight=1)

        self.ent_beneficiary_id = self._create_compact_field(
            row_wrap,
            "رقم المستفيد :",
            textvariable=self.beneficiary_id_var,
            state="readonly",
            label_width=self.field_label_width,
            compact=True,
            width=12,
            col=3,
            group_padx=(15, 0),
        )
        self.combo_beneficiary = self._create_compact_field(
            row_wrap,
            "اسم المستفيد :",
            widget_type="combo",
            state="normal",
            textvariable=self.beneficiary_var,
            label_width=self.field_label_width,
            col=2,
            expand=True,
            group_padx=(15, 0),
        )
        bind_searchable_combobox(self.combo_beneficiary)
        self.combo_beneficiary.bind("<<ComboboxSelected>>", self._on_beneficiary_selected)

        self.ent_amount = self._create_compact_field(
            row_wrap,
            "المبلغ :",
            textvariable=self.amount_var,
            label_width=self.field_label_width,
            compact=True,
            width=12,
            col=1,
            group_padx=(15, 0),
        )
        self.ent_amount.bind("<KeyRelease>", self._on_amount_changed)

        self.ent_amount_words = self._create_compact_field(
            row_wrap,
            "المبلغ بالأحرف :",
            textvariable=self.amount_words_var,
            state="readonly",
            label_width=self.field_label_width,
            col=0,
            expand=True,
            group_padx=(0, 0),
        )

    def _build_amount_notes_section(self, row):
        # Row C: [Notes full width]
        row_wrap = ttk.Frame(self.container, style="App.Payment.Content.TFrame")
        row_wrap.grid(row=row, column=0, sticky="ew")
        row_wrap.columnconfigure(0, weight=1)

        self.ent_notes = self._create_compact_field(
            row_wrap,
            "البيان أو الملاحظة :",
            textvariable=self.notes_var,
            label_width=self.field_label_width,
            col=0,
            expand=True,
            group_padx=(0, 0),
        )

    def _create_date_field(self, parent, label_text, col=0, label_width=None, group_padx=(0, 0), pady=10):
        grp = ttk.Frame(parent, style="App.Payment.Content.TFrame")
        grp.grid(row=0, column=col, sticky="ew", padx=group_padx, pady=pady)
        grp.columnconfigure(0, weight=1)

        date_class = getattr(ttk, "DateEntry", None)
        if date_class:
            field = date_class(grp, bootstyle="primary", dateformat="%Y-%m-%d")
            field.entry.configure(justify="right", font=("Segoe UI", 11, "bold"))
        else:
            field = ttk.Entry(grp, style="App.Payment.Field.TEntry", justify="right")

        field.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ttk.Label(
            grp,
            text=label_text,
            style="App.Payment.FieldLabel.TLabel",
            width=label_width or self.field_label_width,
        ).grid(row=0, column=1, sticky="e")
        return field

    def _build_lines_table(self, row):
        table_area = ttk.Frame(self.container, style="App.Payment.Content.TFrame")
        table_area.grid(row=row, column=0, sticky="nsew", pady=(2, 0))
        table_area.grid_rowconfigure(0, weight=1)
        table_area.grid_columnconfigure(0, weight=1)

        cols = ("description", "voucher_type", "voucher_number", "amount", "account_name", "account_code")
        self.lines_tree = ttk.Treeview(table_area, columns=cols, show="headings", style="App.Payment.Treeview", selectmode="browse")
        self.lines_tree.heading("description", text="الوصف")
        self.lines_tree.column("description", width=380, anchor="e")
        self.lines_tree.heading("voucher_type", text="نوع السند")
        self.lines_tree.column("voucher_type", width=110, anchor="center", stretch=False)
        self.lines_tree.heading("voucher_number", text="رقم السند")
        self.lines_tree.column("voucher_number", width=110, anchor="center", stretch=False)
        self.lines_tree.heading("amount", text="المبلغ")
        self.lines_tree.column("amount", width=130, anchor="e", stretch=False)
        self.lines_tree.heading("account_name", text="اسم الحساب")
        self.lines_tree.column("account_name", width=250, anchor="e")
        self.lines_tree.heading("account_code", text="كود الحساب")
        self.lines_tree.column("account_code", width=120, anchor="center", stretch=False)

        y_scroll = ttk.Scrollbar(table_area, orient="vertical", command=self.lines_tree.yview)
        self.lines_tree.configure(yscrollcommand=y_scroll.set)

        self.lines_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")

        self.lines_tree.tag_configure("odd", background="#f8f9fa")
        self.lines_tree.tag_configure("even", background="#ffffff")

    def _table_has_column(self, cur, table, column):
        cur.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_schema='finance' AND table_name=%s AND column_name=%s",
            (table, column),
        )
        return cur.fetchone() is not None

    def _parse_amount(self, raw_value):
        value = (raw_value or "").replace(",", "").strip()
        if not value:
            return 0.0
        return float(value)

    def _fmt_amount(self, value):
        try:
            return f"{float(value):,.2f}"
        except Exception:
            return "0.00"

    def _format_amount_during_typing(self, var_obj):
        raw = var_obj.get().strip()
        if not raw:
            return
        trans = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        raw = raw.translate(trans)
        cleaned = "".join(ch for ch in raw if ch.isdigit() or ch in ".,")
        cleaned = cleaned.replace(",", "")
        if not cleaned:
            var_obj.set("")
            return
        if cleaned.count(".") > 1:
            first, rest = cleaned.split(".", 1)
            cleaned = first + "." + rest.replace(".", "")
        try:
            if "." in cleaned:
                int_part, dec_part = cleaned.split(".", 1)
                int_part = int_part or "0"
                dec_part = "".join(ch for ch in dec_part if ch.isdigit())[:2]
                formatted = f"{int(int_part):,}." + dec_part
            else:
                formatted = f"{int(cleaned):,}"
            var_obj.set(formatted)
        except Exception:
            pass

    def _set_date_value(self, value):
        if hasattr(self.ent_date, "entry"):
            self.ent_date.entry.delete(0, tk.END)
            self.ent_date.entry.insert(0, value)
        else:
            self.ent_date.delete(0, tk.END)
            self.ent_date.insert(0, value)

    def _get_date_value(self):
        if hasattr(self.ent_date, "entry"):
            return self.ent_date.entry.get().strip()
        return self.ent_date.get().strip()

    def _on_amount_changed(self, _event=None):
        self._format_amount_during_typing(self.amount_var)
        self._refresh_amount_words()
        self._sync_preview_line()

    def _refresh_amount_words(self):
        try:
            amount = self._parse_amount(self.amount_var.get())
        except Exception:
            self.amount_words_var.set("")
            return
        if amount <= 0:
            self.amount_words_var.set("")
            return
        self.amount_words_var.set(f"المبلغ بالأحرف: {self._amount_to_words_ar(amount)}")

    def _amount_to_words_ar(self, amount):
        units = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"]
        tens = ["", "عشرة", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"]
        teens = ["عشرة", "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر", "ستة عشر", "سبعة عشر", "ثمانية عشر", "تسعة عشر"]

        integer_part = int(amount)
        fraction_part = int(round((amount - integer_part) * 100))

        if integer_part == 0:
            base = "صفر"
        elif integer_part < 10:
            base = units[integer_part]
        elif integer_part < 20:
            base = teens[integer_part - 10]
        elif integer_part < 100:
            ten = integer_part // 10
            one = integer_part % 10
            base = tens[ten] if one == 0 else f"{units[one]} و {tens[ten]}"
        else:
            base = str(integer_part)

        text = f"{base} ريال"
        if fraction_part > 0:
            text += f" و {fraction_part} فلس"
        return text

    def _sync_preview_line(self):
        ben = self.beneficiary_display_to_data.get(self.combo_beneficiary.get().strip(), {})
        code = str(ben.get("account_code") or ben.get("control_account") or "").strip()
        try:
            amt = self._parse_amount(self.amount_var.get())
        except Exception:
            amt = 0

        self.line_items.clear()
        if code and amt > 0:
            self.line_items.append(
                {
                    "account_code": code,
                    "account_name": self.account_code_to_name.get(code, ben.get("name", "")),
                    "amount": amt,
                    "voucher_number": self.voucher_id_var.get().strip(),
                    "voucher_type": self.voucher_type_var.get().strip(),
                    "description": self.notes_var.get().strip(),
                }
            )
        self._refresh_lines_table()

    def _refresh_lines_table(self):
        self.lines_tree.delete(*self.lines_tree.get_children())
        for idx, line in enumerate(self.line_items, start=1):
            tag = "even" if idx % 2 == 0 else "odd"
            self.lines_tree.insert(
                "",
                tk.END,
                iid=str(idx - 1),
                values=(
                    line.get("description", ""),
                    line.get("voucher_type", ""),
                    line.get("voucher_number", ""),
                    self._fmt_amount(line.get("amount", 0)),
                    line.get("account_name", ""),
                    line.get("account_code", ""),
                ),
                tags=(tag,),
            )

    def _next_reference_no(self, cur):
        cur.execute("SELECT COALESCE(MAX(reference_no::BIGINT), 10000) + 1 FROM finance.vouchers")
        row = cur.fetchone()
        return str(row[0]) if row and row[0] is not None else "10001"

    def _fetch_next_ids(self):
        conn = get_connection()
        if not conn:
            return "تلقائي", "10001"
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM finance.vouchers")
                    vid_row = cur.fetchone()
                    ref_no = self._next_reference_no(cur)
                    next_id = str(vid_row[0]) if vid_row and vid_row[0] is not None else "تلقائي"
                    return next_id, ref_no
        except Exception:
            return "تلقائي", "10001"
        finally:
            conn.close()

    def _reset_and_new(self):
        self.voucher_id_var.set("تلقائي")
        self.reference_no_var.set("10001")
        self.voucher_type_var.set(VOUCHER_TYPE_PAYMENT)
        self.currency_var.set("ريال يمني")

        self.fund_var.set("الصندوق الرئيسي")
        self.beneficiary_var.set("")
        self.beneficiary_id_var.set("")
        self.amount_var.set("0.00")
        self.amount_words_var.set("")
        self.notes_var.set("")

        self._set_date_value(datetime.now().strftime("%Y-%m-%d"))

        self.line_items.clear()
        self._refresh_lines_table()

        next_id, next_ref = self._fetch_next_ids()
        self.voucher_id_var.set(next_id)
        self.reference_no_var.set(next_ref)

        default_fund = self._get_default_fund_display()
        if default_fund:
            self.combo_fund.set(default_fund)

    def load_accounts(self):
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT account_code, account_name
                FROM finance.accounts
                WHERE COALESCE(is_active, true) = true
                  AND (
                    TRIM(account_code) = '1101'
                    OR TRIM(parent_code) = '1101'
                    OR TRIM(account_code) LIKE '1101%'
                  )
                ORDER BY account_code
                """
            )
            rows = cur.fetchall() or []

            fund_values = []
            self.account_display_to_code.clear()
            self.account_code_to_display.clear()
            self.account_code_to_name.clear()
            self.fund_display_to_code.clear()

            main_fund_code = None
            for code, name in rows:
                code_txt = str(code or "").strip()
                name_txt = str(name or "").strip()
                if not code_txt:
                    continue

                display = f"{code_txt} - {name_txt}" if name_txt else code_txt
                fund_values.append(display)
                self.account_display_to_code[display] = code_txt
                self.account_code_to_display[code_txt] = display
                self.account_code_to_name[code_txt] = name_txt
                self.fund_display_to_code[display] = code_txt

                lowered = name_txt.lower()
                if lowered in ("main fund", "الصندوق الرئيسي"):
                    main_fund_code = code_txt

            if main_fund_code:
                self.fund_display_to_code["الصندوق الرئيسي"] = main_fund_code
                fund_values = ["الصندوق الرئيسي"] + [v for v in fund_values if self.account_display_to_code.get(v) != main_fund_code]
            elif fund_values:
                self.fund_display_to_code["الصندوق الرئيسي"] = self.account_display_to_code[fund_values[0]]
                fund_values = ["الصندوق الرئيسي"] + fund_values

            set_combobox_values(self.combo_fund, fund_values)
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل الصناديق"))
        finally:
            conn.close()

    def load_beneficiaries(self):
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            self.beneficiary_display_to_data.clear()
            values = []

            cur.execute(
                """
                SELECT account_code, account_name
                FROM finance.accounts
                WHERE account_level = 'تحليلي'
                  AND COALESCE(is_active, true) = true
                ORDER BY account_code
                """
            )
            for code, name in cur.fetchall() or []:
                code_txt = str(code or "").strip()
                if not code_txt:
                    continue
                name_txt = str(name or "").strip()
                display = f"حساب: {name_txt}" if name_txt else f"حساب: {code_txt}"
                self.beneficiary_display_to_data[display] = {
                    "type": "account",
                    "account_code": code_txt,
                    "name": name_txt,
                    "vendor_id": None,
                    "customer_id": None,
                }
                values.append(display)

            cur.execute(
                """
                SELECT id, customer_name, COALESCE(control_account, %s)
                FROM finance.customers
                ORDER BY customer_name
                """,
                (CUSTOMER_CONTROL_ACCOUNT_CODE,),
            )
            for cid, name, control_code in cur.fetchall() or []:
                if not name:
                    continue
                display = f"عميل: {name}"
                self.beneficiary_display_to_data[display] = {
                    "type": "customer",
                    "account_code": str(control_code or CUSTOMER_CONTROL_ACCOUNT_CODE).strip(),
                    "name": str(name),
                    "vendor_id": None,
                    "customer_id": int(cid),
                }
                values.append(display)

            vendor_control_expr = f"'{VENDOR_CONTROL_ACCOUNT_CODE}'"
            if self._table_has_column(cur, "vendors", "control_account"):
                vendor_control_expr = f"COALESCE(v.control_account, '{VENDOR_CONTROL_ACCOUNT_CODE}')"

            cur.execute(
                f"""
                SELECT v.id, v.vendor_name, {vendor_control_expr}
                FROM finance.vendors v
                ORDER BY v.vendor_name
                """
            )
            for vid, name, control_code in cur.fetchall() or []:
                if not name:
                    continue
                display = f"وارث/مورد: {name}"
                self.beneficiary_display_to_data[display] = {
                    "type": "vendor",
                    "account_code": str(control_code or VENDOR_CONTROL_ACCOUNT_CODE).strip(),
                    "name": str(name),
                    "vendor_id": int(vid),
                    "customer_id": None,
                }
                values.append(display)

            set_combobox_values(self.combo_beneficiary, values)
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل المستفيدين"))
        finally:
            conn.close()

    def _on_beneficiary_selected(self, *_):
        data = self.beneficiary_display_to_data.get(self.combo_beneficiary.get().strip(), {})
        self.beneficiary_id_var.set(str(data.get("account_code") or ""))
        self._sync_preview_line()

    def _resolve_fund_code(self):
        display = self.combo_fund.get().strip()
        if display in self.fund_display_to_code:
            return self.fund_display_to_code.get(display)
        return self.account_display_to_code.get(display)

    def _validate_before_save(self):
        ben_disp = self.combo_beneficiary.get().strip()
        ben = self.beneficiary_display_to_data.get(ben_disp)
        if not ben:
            messagebox.showwarning("تنبيه", "يرجى اختيار اسم المستفيد")
            return None

        fund_code = self._resolve_fund_code()
        if not fund_code:
            messagebox.showwarning("تنبيه", "يرجى اختيار الصندوق")
            return None

        try:
            amount = self._parse_amount(self.amount_var.get())
        except Exception:
            messagebox.showwarning("تنبيه", "المبلغ غير صحيح")
            return None

        if amount <= 0:
            messagebox.showwarning("تنبيه", "المبلغ يجب أن يكون أكبر من صفر")
            return None

        if self.enforce_fund_balance_check:
            available = self._get_fund_available_balance(str(fund_code).strip())
            if available is not None and amount > available:
                messagebox.showwarning("تنبيه", f"رصيد الصندوق غير كاف. المتاح: {self._fmt_amount(available)}")
                return None

        return {
            "beneficiary": ben,
            "fund_code": str(fund_code).strip(),
            "amount": amount,
            "notes": self.notes_var.get().strip(),
        }

    def _get_default_fund_display(self):
        values = list(self.combo_fund["values"] or [])
        if not values:
            return ""

        for value in values:
            txt = str(value).strip().lower()
            if txt == "الصندوق الرئيسي" or "main fund" in txt or "الصندوق الرئيسي" in txt:
                return str(value)

        return str(values[0])

    def _get_fund_available_balance(self, fund_code):
        conn = get_connection()
        if not conn:
            return None
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT COALESCE(SUM(COALESCE(debit, 0) - COALESCE(credit, 0)), 0)
                        FROM finance.ledger
                        WHERE TRIM(account_code) = TRIM(%s)
                        """,
                        (fund_code,),
                    )
                    row = cur.fetchone()
                    return float(row[0] or 0)
        except Exception:
            return None
        finally:
            conn.close()

    def _refresh_ledger_columns(self, cur):
        self.ledger_has_vendor_id = self._table_has_column(cur, "ledger", "vendor_id")
        self.ledger_has_customer_id = self._table_has_column(cur, "ledger", "customer_id")
        self.ledger_has_property_id = self._table_has_column(cur, "ledger", "property_id")

    def _insert_ledger_row(self, cur, *, voucher_id, account_code, debit, credit, line_description, posting_date, vendor_id=None, customer_id=None):
        cols = ["voucher_id", "account_code", "debit", "credit", "line_description", "posting_date"]
        vals = [voucher_id, account_code, debit, credit, line_description, posting_date]

        if self.ledger_has_vendor_id:
            cols.append("vendor_id")
            vals.append(vendor_id)
        if self.ledger_has_customer_id:
            cols.append("customer_id")
            vals.append(customer_id)
        if self.ledger_has_property_id:
            cols.append("property_id")
            vals.append(None)

        placeholders = ", ".join(["%s"] * len(cols))
        cur.execute(f"INSERT INTO finance.ledger ({', '.join(cols)}) VALUES ({placeholders})", tuple(vals))

    def save_voucher(self, is_update=False):
        valid = self._validate_before_save()
        if not valid:
            return

        vid_text = self.voucher_id_var.get().strip()
        ref_no = self.reference_no_var.get().strip()
        notes = valid["notes"]
        date = self._get_date_value() or datetime.now().strftime("%Y-%m-%d")

        conn = None
        try:
            conn = get_connection()
            if not conn:
                return
            cur = conn.cursor()
            self._refresh_ledger_columns(cur)

            if is_update:
                if not vid_text.isdigit():
                    messagebox.showwarning("تنبيه", "رقم السند غير صالح للتعديل")
                    return
                vid = int(vid_text)
                cur.execute(
                    "UPDATE finance.vouchers SET reference_no=%s, v_type=%s, v_date=%s, description=%s WHERE id=%s",
                    (ref_no, VOUCHER_TYPE_PAYMENT, date, notes, vid),
                )
                cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (vid,))
            else:
                cur.execute(
                    "INSERT INTO finance.vouchers (reference_no, v_type, v_date, description) VALUES (%s, %s, %s, %s) RETURNING id",
                    (ref_no, VOUCHER_TYPE_PAYMENT, date, notes),
                )
                vid = cur.fetchone()[0]
                self.voucher_id_var.set(str(vid))

            ben = valid["beneficiary"]
            vendor_id = ben.get("vendor_id")
            customer_id = ben.get("customer_id")
            counterparty_code = str(ben.get("account_code") or "").strip()
            fund_code = valid["fund_code"]
            amount = valid["amount"]

            self._insert_ledger_row(
                cur,
                voucher_id=vid,
                account_code=fund_code,
                vendor_id=vendor_id,
                customer_id=customer_id,
                debit=0,
                credit=amount,
                line_description=notes or "سند صرف",
                posting_date=date,
            )
            self._insert_ledger_row(
                cur,
                voucher_id=vid,
                account_code=counterparty_code,
                vendor_id=vendor_id,
                customer_id=customer_id,
                debit=amount,
                credit=0,
                line_description=notes or "",
                posting_date=date,
            )

            conn.commit()
            self.reference_no_var.set(ref_no)
            self._sync_preview_line()
            messagebox.showinfo("نجاح", "تم حفظ سند الصرف بنجاح")
        except Exception as exc:
            if conn:
                conn.rollback()
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ السند"))
        finally:
            if conn:
                conn.close()

    def _load_voucher_by_id(self, voucher_id):
        conn = get_connection()
        if not conn:
            messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
            return False
        try:
            cur = conn.cursor()
            self._refresh_ledger_columns(cur)
            cur.execute(
                "SELECT id, COALESCE(reference_no, ''), v_date, description FROM finance.vouchers WHERE id=%s AND v_type=%s",
                (voucher_id, VOUCHER_TYPE_PAYMENT),
            )
            row = cur.fetchone()
            if not row:
                messagebox.showinfo("نتيجة البحث", "لم يتم العثور على سند صرف بهذا الرقم")
                return False

            self.voucher_id_var.set(str(row[0]))
            self.reference_no_var.set(str(row[1] or ""))
            self._set_date_value(str(row[2]))
            self.notes_var.set(str(row[3] or ""))

            select_cols = ["account_code", "debit", "credit", "line_description"]
            if self.ledger_has_vendor_id:
                select_cols.append("vendor_id")
            if self.ledger_has_customer_id:
                select_cols.append("customer_id")
            cur.execute(f"SELECT {', '.join(select_cols)} FROM finance.ledger WHERE voucher_id=%s ORDER BY id", (voucher_id,))
            ledger_rows = cur.fetchall() or []

            cash_set = False
            beneficiary_set = False
            amount_set = False

            for row_data in ledger_rows:
                acc_code = str(row_data[0] or "")
                debit = float(row_data[1] or 0)
                credit = float(row_data[2] or 0)
                line_desc = row_data[3] or ""

                idx = 4
                vend_id = row_data[idx] if self.ledger_has_vendor_id else None
                idx += 1 if self.ledger_has_vendor_id else 0
                cust_id = row_data[idx] if self.ledger_has_customer_id else None

                if credit > 0 and debit == 0 and not cash_set:
                    fund_display = self.account_code_to_display.get(acc_code) or acc_code
                    self.combo_fund.set("الصندوق الرئيسي" if self.fund_display_to_code.get("الصندوق الرئيسي") == acc_code else fund_display)
                    cash_set = True
                    continue

                if debit <= 0 and credit <= 0:
                    continue

                amount = debit if debit > 0 else credit
                if not amount_set:
                    self.amount_var.set(self._fmt_amount(amount))
                    self._refresh_amount_words()
                    amount_set = True

                if not beneficiary_set:
                    disp = self._resolve_beneficiary_display(vend_id, cust_id, acc_code)
                    if disp:
                        self.combo_beneficiary.set(disp)
                        self._on_beneficiary_selected()
                        beneficiary_set = True

                if not self.notes_var.get().strip() and line_desc:
                    self.notes_var.set(str(line_desc))

            self._sync_preview_line()
            return True
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل السند"))
            return False
        finally:
            conn.close()

    def _resolve_beneficiary_display(self, vendor_id, customer_id, account_code):
        for disp, data in self.beneficiary_display_to_data.items():
            if customer_id is not None and data.get("type") == "customer" and int(data.get("customer_id", 0) or 0) == int(customer_id):
                return disp
            if vendor_id is not None and data.get("type") == "vendor" and int(data.get("vendor_id", 0) or 0) == int(vendor_id):
                return disp
            if data.get("type") == "account" and str(data.get("account_code") or "") == str(account_code or ""):
                return disp
        return ""

    def _show_history(self):
        history_win = tk.Toplevel(self.master)
        history_win.title("قائمة سندات الصرف")
        history_win.geometry("620x420")
        tree = ttk.Treeview(history_win, columns=("id", "ref", "date", "desc"), show="headings")
        tree.heading("id", text="رقم السند")
        tree.column("id", width=90, anchor="center")
        tree.heading("ref", text="رقم المرجع")
        tree.column("ref", width=100, anchor="center")
        tree.heading("date", text="التاريخ")
        tree.column("date", width=120, anchor="center")
        tree.heading("desc", text="الوصف")
        tree.column("desc", width=280, anchor="e")
        tree.pack(fill="both", expand=True)

        conn = None
        try:
            conn = get_connection()
            if not conn:
                return
            cur = conn.cursor()
            cur.execute(
                "SELECT id, COALESCE(reference_no, ''), v_date, description FROM finance.vouchers WHERE v_type=%s ORDER BY v_date DESC, id DESC",
                (VOUCHER_TYPE_PAYMENT,),
            )
            for vid, ref_no, vdate, vdesc in cur.fetchall():
                tree.insert("", tk.END, values=(vid, ref_no, str(vdate), vdesc))
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل السجلات"))
        finally:
            if conn:
                conn.close()

        def load_from_history(_event):
            sel = tree.selection()
            if not sel:
                return
            vid = tree.item(sel[0])["values"][0]
            history_win.destroy()
            self._load_voucher_by_id(vid)

        tree.bind("<Double-1>", load_from_history)

    def _search_voucher(self):
        vid = simpledialog.askinteger("بحث", "أدخل رقم السند:")
        if vid:
            self._load_voucher_by_id(vid)

    def _request_voucher_id(self, title):
        ask = simpledialog.askstring(title, "أدخل رقم السند:", parent=self.master)
        if ask and ask.isdigit():
            return int(ask)
        return None

    def _update_voucher(self):
        current = self.voucher_id_var.get().strip()
        if current.isdigit():
            self.save_voucher(is_update=True)
            return
        vid = self._request_voucher_id("تعديل سند")
        if vid is None:
            return
        if self._load_voucher_by_id(vid):
            self.save_voucher(is_update=True)

    def _delete_voucher(self):
        current = self.voucher_id_var.get().strip()
        voucher_id = int(current) if current.isdigit() else self._request_voucher_id("حذف سند")
        if voucher_id is None:
            return
        if not messagebox.askyesno("تأكيد", "هل تريد حذف السند المحدد؟"):
            return

        conn = get_connection()
        if not conn:
            messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
            return

        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (voucher_id,))
            cur.execute("DELETE FROM finance.vouchers WHERE id=%s AND v_type=%s", (voucher_id, VOUCHER_TYPE_PAYMENT))
            conn.commit()
            messagebox.showinfo("نجاح", "تم حذف سند الصرف")
            self._reset_and_new()
        except Exception as exc:
            conn.rollback()
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حذف سند"))
        finally:
            conn.close()

    def _print_voucher(self):
        voucher_id = self.voucher_id_var.get().strip()
        if not voucher_id.isdigit():
            messagebox.showwarning("تنبيه", "احفظ السند أولاً قبل الطباعة")
            return
        messagebox.showinfo("طباعة", f"تم تجهيز سند الصرف رقم {voucher_id} للطباعة")
