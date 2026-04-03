import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog

import ttkbootstrap as ttk

from app_constants import SYSTEM_NAME
from combobox_helper import bind_searchable_combobox, set_combobox_values
from db_connection import get_connection, get_db_error_message


class SettlementEntryScreen:
    VOUCHER_TYPE = "قيد تسوية"

    def __init__(self, master):
        self.master = master

        # System colors with settlement identity accent.
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.bg_color = "#f4f7f6"
        self.card_color = "#ffffff"
        self.accent_color = "#e67e22"
        self.text_light = "#ecf0f1"

        self.current_voucher_id = None
        self.selected_line_iid = None
        self.entry_lines = []
        self._schema_cache = {}

        self.account_display_to_code = {}
        self.account_code_to_name = {}
        self.account_code_to_display = {}

        self.vendor_display_to_id = {}
        self.vendor_id_to_display = {}

        self.property_display_to_id = {}
        self.property_id_to_display = {}

        self.voucher_id_var = tk.StringVar(value="تلقائي")
        self.reference_no_var = tk.StringVar(value="10001")
        self.voucher_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.currency_var = tk.StringVar(value="ريال يمني")
        self.exchange_rate_var = tk.StringVar(value="1.00")
        self.general_desc_var = tk.StringVar()

        self.customer_chk_var = tk.BooleanVar(value=False)
        self.vendor_chk_var = tk.BooleanVar(value=False)
        self.customer_var = tk.StringVar()
        self.vendor_var = tk.StringVar()
        self.property_var = tk.StringVar()

        self.line_account_var = tk.StringVar()
        self.line_account_code_var = tk.StringVar()
        self.line_account_name_var = tk.StringVar()
        self.line_debit_var = tk.StringVar(value="")
        self.line_credit_var = tk.StringVar(value="")
        self.line_desc_var = tk.StringVar()

        self.total_debit_var = tk.StringVar(value="0.00")
        self.total_credit_var = tk.StringVar(value="0.00")
        self.diff_var = tk.StringVar(value="0.00")
        self.status_var = tk.StringVar(value="غير متوازن")

        self._setup_styles()
        self._build_layout()
        self._bind_events()
        self._load_master_data()
        self._reset_and_new(initial=True)

    # -----------------------------
    # UI
    # -----------------------------
    def _setup_styles(self):
        style = ttk.Style()

        style.configure("Settlement.Root.TFrame", background=self.bg_color)
        style.configure("Settlement.Card.TFrame", background=self.card_color, bordercolor="#d9e2ec", borderwidth=1, relief="solid")
        style.configure("Settlement.Header.TFrame", background=self.primary_color)
        style.configure("Settlement.Header.TLabel", background=self.primary_color, foreground=self.text_light, font=("Segoe UI", 17, "bold"))

        style.configure("Settlement.Content.TFrame", background=self.card_color)
        style.configure("Settlement.Section.TLabelframe", background=self.card_color, bordercolor="#d9e2ec", borderwidth=1, relief="solid")
        style.configure("Settlement.Section.TLabelframe.Label", background=self.card_color, foreground=self.primary_color, font=("Segoe UI", 10, "bold"))

        style.configure(
            "Settlement.FieldLabel.TLabel",
            background=self.sidebar_color,
            foreground=self.text_light,
            font=("Segoe UI", 10, "bold"),
            anchor="center",
            padding=6,
        )
        style.configure("Settlement.Field.TEntry", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 10, "bold"))
        style.configure("Settlement.Field.TCombobox", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 10, "bold"))
        style.configure("Settlement.Check.TCheckbutton", background=self.card_color, foreground=self.primary_color, font=("Segoe UI", 10, "bold"))

        style.configure("Settlement.Primary.TButton", background="#2980b9", foreground="white", borderwidth=0, font=("Segoe UI", 10, "bold"), padding=(10, 6))
        style.configure("Settlement.Success.TButton", background="#27ae60", foreground="white", borderwidth=0, font=("Segoe UI", 10, "bold"), padding=(10, 6))
        style.configure("Settlement.Warning.TButton", background="#f1c40f", foreground="#2c3e50", borderwidth=0, font=("Segoe UI", 10, "bold"), padding=(10, 6))
        style.configure("Settlement.Danger.TButton", background="#e74c3c", foreground="white", borderwidth=0, font=("Segoe UI", 10, "bold"), padding=(10, 6))
        style.configure("Settlement.Info.TButton", background="#8e44ad", foreground="white", borderwidth=0, font=("Segoe UI", 10, "bold"), padding=(10, 6))
        style.configure("Settlement.History.TButton", background="#16a085", foreground="white", borderwidth=0, font=("Segoe UI", 10, "bold"), padding=(10, 6))
        style.configure("Settlement.Orange.TButton", background=self.accent_color, foreground="white", borderwidth=0, font=("Segoe UI", 10, "bold"), padding=(10, 6))

        for btn_style in (
            "Settlement.Primary.TButton",
            "Settlement.Success.TButton",
            "Settlement.Warning.TButton",
            "Settlement.Danger.TButton",
            "Settlement.Info.TButton",
            "Settlement.History.TButton",
            "Settlement.Orange.TButton",
        ):
            style.map(btn_style, background=[("active", self.accent_color), ("pressed", self.accent_color)], foreground=[("active", "white")])

        style.configure(
            "Settlement.Treeview",
            background="white",
            fieldbackground="white",
            foreground=self.primary_color,
            rowheight=30,
            font=("Segoe UI", 10, "bold"),
        )
        style.configure("Settlement.Treeview.Heading", background=self.primary_color, foreground="white", font=("Segoe UI", 10, "bold"))
        style.map("Settlement.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "white")])

        style.configure("Settlement.FooterOk.TLabel", background=self.card_color, foreground="#27ae60", font=("Segoe UI", 11, "bold"))
        style.configure("Settlement.FooterBad.TLabel", background=self.card_color, foreground="#e74c3c", font=("Segoe UI", 11, "bold"))

    def _build_layout(self):
        self.frame = ttk.Frame(self.master, style="Settlement.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.main_card = ttk.Frame(self.frame, style="Settlement.Card.TFrame")
        self.main_card.pack(fill="both", expand=True, padx=12, pady=12)

        self._build_top_toolbar()

        self.content = ttk.Frame(self.main_card, style="Settlement.Content.TFrame", padding=(14, 10))
        self.content.pack(fill="both", expand=True)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(3, weight=1)

        self._build_header_section()
        self._build_general_description()
        self._build_line_editor()
        self._build_table()
        self._build_footer()

    def _build_top_toolbar(self):
        header = ttk.Frame(self.main_card, style="Settlement.Header.TFrame", height=66)
        header.pack(fill="x", side="top")

        ttk.Label(header, text=f"قيد تسوية - {SYSTEM_NAME}", style="Settlement.Header.TLabel").pack(side="right", padx=26, pady=14)

        btn_group = ttk.Frame(header, style="Settlement.Header.TFrame")
        btn_group.pack(side="left", padx=16)

        buttons = [
            ("جديد", "Settlement.Primary.TButton", self._reset_and_new),
            ("حفظ", "Settlement.Success.TButton", self._save_voucher),
            ("تعديل", "Settlement.Warning.TButton", self._update_voucher),
            ("حذف", "Settlement.Danger.TButton", self._delete_voucher),
            ("بحث", "Settlement.Primary.TButton", self._search_voucher),
            ("السجل", "Settlement.History.TButton", self._show_history),
            ("طباعة", "Settlement.Info.TButton", self._print_voucher),
        ]
        for txt, style_name, cmd in buttons:
            ttk.Button(btn_group, text=txt, style=style_name, width=8, command=cmd).pack(side="left", padx=4)

    def _compact_field(self, parent, label_text, widget_type="entry", label_width=13, **kwargs):
        box = ttk.Frame(parent, style="Settlement.Content.TFrame")
        box.pack(side="right", fill="x", expand=True, padx=(8, 0), pady=3)

        if widget_type == "entry":
            field = ttk.Entry(box, style="Settlement.Field.TEntry", justify="right", **kwargs)
        else:
            field = ttk.Combobox(box, style="Settlement.Field.TCombobox", justify="right", **kwargs)

        field.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Label(box, text=label_text, style="Settlement.FieldLabel.TLabel", width=label_width).pack(side="right")
        return field

    def _build_header_section(self):
        wrap = ttk.Labelframe(self.content, text=" بيانات القيد ", style="Settlement.Section.TLabelframe", padding=8)
        wrap.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        right = ttk.Frame(wrap, style="Settlement.Content.TFrame")
        right.pack(side="right", fill="both", expand=True, padx=(6, 0))
        left = ttk.Frame(wrap, style="Settlement.Content.TFrame")
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        r1 = ttk.Frame(right, style="Settlement.Content.TFrame")
        r1.pack(fill="x")
        self.ent_voucher_id = self._compact_field(r1, "رقم القيد :", textvariable=self.voucher_id_var, state="readonly")
        self.ent_ref = self._compact_field(r1, "رقم المرجع :", textvariable=self.reference_no_var, state="readonly")
        self.ent_date = self._create_date_field(r1, "التاريخ :")

        r2 = ttk.Frame(right, style="Settlement.Content.TFrame")
        r2.pack(fill="x")
        self.combo_currency = self._compact_field(
            r2,
            "العملة :",
            widget_type="combo",
            textvariable=self.currency_var,
            state="readonly",
            values=("ريال يمني", "ريال سعودي", "دولار"),
        )
        self.ent_exchange = self._compact_field(r2, "سعر الصرف :", textvariable=self.exchange_rate_var)

        l1 = ttk.Frame(left, style="Settlement.Content.TFrame")
        l1.pack(fill="x")
        ttk.Checkbutton(
            l1,
            text="تحديد عميل",
            variable=self.customer_chk_var,
            style="Settlement.Check.TCheckbutton",
            command=self._on_customer_toggle,
        ).pack(side="right", padx=(8, 4))
        self.combo_customer = ttk.Combobox(l1, textvariable=self.customer_var, style="Settlement.Field.TCombobox", justify="right", state="disabled")
        self.combo_customer.pack(side="right", fill="x", expand=True, padx=(0, 8))
        bind_searchable_combobox(self.combo_customer)
        ttk.Button(l1, text="اختيار", style="Settlement.Orange.TButton", width=8, command=self._pick_customer).pack(side="right")

        l2 = ttk.Frame(left, style="Settlement.Content.TFrame")
        l2.pack(fill="x")
        ttk.Checkbutton(
            l2,
            text="تحديد مورد",
            variable=self.vendor_chk_var,
            style="Settlement.Check.TCheckbutton",
            command=self._on_vendor_toggle,
        ).pack(side="right", padx=(8, 4))
        self.combo_vendor = ttk.Combobox(l2, textvariable=self.vendor_var, style="Settlement.Field.TCombobox", justify="right", state="disabled")
        self.combo_vendor.pack(side="right", fill="x", expand=True, padx=(0, 8))
        bind_searchable_combobox(self.combo_vendor)
        ttk.Button(l2, text="اختيار", style="Settlement.Orange.TButton", width=8, command=self._pick_vendor).pack(side="right")

        l3 = ttk.Frame(left, style="Settlement.Content.TFrame")
        l3.pack(fill="x")
        self.combo_property = self._compact_field(
            l3,
            "العقار (اختياري) :",
            widget_type="combo",
            textvariable=self.property_var,
            state="readonly",
        )
        bind_searchable_combobox(self.combo_property)

    def _build_general_description(self):
        box = ttk.Labelframe(self.content, text=" البيان العام ", style="Settlement.Section.TLabelframe", padding=8)
        box.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        box.grid_columnconfigure(0, weight=1)
        self.ent_general_desc = ttk.Entry(box, textvariable=self.general_desc_var, style="Settlement.Field.TEntry", justify="right")
        self.ent_general_desc.grid(row=0, column=0, sticky="ew")

    def _build_line_editor(self):
        editor = ttk.Labelframe(self.content, text=" إدخال الحركة ", style="Settlement.Section.TLabelframe", padding=8)
        editor.grid(row=2, column=0, sticky="ew", pady=(0, 6))

        for i in range(6):
            editor.grid_columnconfigure(i, weight=1)

        labels = ["الحساب", "كود الحساب", "اسم الحساب", "مدين", "دائن", "الوصف"]
        for idx, txt in enumerate(labels):
            ttk.Label(editor, text=txt, style="Settlement.FieldLabel.TLabel").grid(row=0, column=idx, sticky="ew", padx=2, pady=(0, 4))

        self.combo_line_account = ttk.Combobox(
            editor,
            textvariable=self.line_account_var,
            style="Settlement.Field.TCombobox",
            justify="right",
            state="normal",
        )
        self.combo_line_account.grid(row=1, column=0, sticky="ew", padx=2)
        bind_searchable_combobox(self.combo_line_account)

        self.ent_line_code = ttk.Entry(
            editor,
            textvariable=self.line_account_code_var,
            style="Settlement.Field.TEntry",
            justify="right",
            state="readonly",
        )
        self.ent_line_code.grid(row=1, column=1, sticky="ew", padx=2)

        self.ent_line_name = ttk.Entry(
            editor,
            textvariable=self.line_account_name_var,
            style="Settlement.Field.TEntry",
            justify="right",
            state="readonly",
        )
        self.ent_line_name.grid(row=1, column=2, sticky="ew", padx=2)

        self.ent_line_debit = ttk.Entry(editor, textvariable=self.line_debit_var, style="Settlement.Field.TEntry", justify="right")
        self.ent_line_debit.grid(row=1, column=3, sticky="ew", padx=2)

        self.ent_line_credit = ttk.Entry(editor, textvariable=self.line_credit_var, style="Settlement.Field.TEntry", justify="right")
        self.ent_line_credit.grid(row=1, column=4, sticky="ew", padx=2)

        self.ent_line_desc = ttk.Entry(editor, textvariable=self.line_desc_var, style="Settlement.Field.TEntry", justify="right")
        self.ent_line_desc.grid(row=1, column=5, sticky="ew", padx=2)

    def _build_table(self):
        box = ttk.Frame(self.content, style="Settlement.Content.TFrame")
        box.grid(row=3, column=0, sticky="nsew")
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(0, weight=1)

        cols = ("account_code", "account_name", "debit", "credit", "description")
        self.tree = ttk.Treeview(box, columns=cols, show="headings", style="Settlement.Treeview", selectmode="browse")

        self.tree.heading("account_code", text="Account Code", anchor="e")
        self.tree.heading("account_name", text="Account Name", anchor="e")
        self.tree.heading("debit", text="Debit", anchor="e")
        self.tree.heading("credit", text="Credit", anchor="e")
        self.tree.heading("description", text="Description", anchor="e")

        self.tree.column("account_code", width=130, anchor="e", stretch=False)
        self.tree.column("account_name", width=260, anchor="e", stretch=True)
        self.tree.column("debit", width=140, anchor="e", stretch=False)
        self.tree.column("credit", width=140, anchor="e", stretch=False)
        self.tree.column("description", width=380, anchor="e", stretch=True)

        yscroll = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

        self.tree.tag_configure("odd", background="#fdf6ef")
        self.tree.tag_configure("even", background="#fffaf4")

    def _build_footer(self):
        foot = ttk.Frame(self.content, style="Settlement.Content.TFrame")
        foot.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        foot.grid_columnconfigure(0, weight=1)

        right = ttk.Frame(foot, style="Settlement.Content.TFrame")
        right.grid(row=0, column=0, sticky="e")

        ttk.Label(right, text="إجمالي المدين", style="Settlement.FieldLabel.TLabel", width=16).grid(row=0, column=0, sticky="e", padx=6, pady=2)
        ttk.Entry(right, textvariable=self.total_debit_var, style="Settlement.Field.TEntry", justify="right", state="readonly", width=20).grid(row=0, column=1, sticky="e", padx=6, pady=2)

        ttk.Label(right, text="إجمالي الدائن", style="Settlement.FieldLabel.TLabel", width=16).grid(row=1, column=0, sticky="e", padx=6, pady=2)
        ttk.Entry(right, textvariable=self.total_credit_var, style="Settlement.Field.TEntry", justify="right", state="readonly", width=20).grid(row=1, column=1, sticky="e", padx=6, pady=2)

        ttk.Label(right, text="الفرق", style="Settlement.FieldLabel.TLabel", width=16).grid(row=2, column=0, sticky="e", padx=6, pady=2)
        ttk.Entry(right, textvariable=self.diff_var, style="Settlement.Field.TEntry", justify="right", state="readonly", width=20).grid(row=2, column=1, sticky="e", padx=6, pady=2)

        ttk.Label(right, text="الحالة", style="Settlement.FieldLabel.TLabel", width=16).grid(row=3, column=0, sticky="e", padx=6, pady=2)
        self.lbl_status = ttk.Label(right, textvariable=self.status_var, style="Settlement.FooterBad.TLabel")
        self.lbl_status.grid(row=3, column=1, sticky="e", padx=6, pady=2)

    def _create_date_field(self, parent, label_text):
        box = ttk.Frame(parent, style="Settlement.Content.TFrame")
        box.pack(side="right", fill="x", expand=True, padx=(8, 0), pady=3)

        date_class = getattr(ttk, "DateEntry", None)
        if date_class:
            widget = date_class(box, bootstyle="primary", dateformat="%Y-%m-%d")
            widget.entry.configure(justify="right", font=("Segoe UI", 10, "bold"))
        else:
            widget = ttk.Entry(box, textvariable=self.voucher_date_var, style="Settlement.Field.TEntry", justify="right")

        widget.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Label(box, text=label_text, style="Settlement.FieldLabel.TLabel", width=13).pack(side="right")
        return widget

    # -----------------------------
    # Bindings and helper logic
    # -----------------------------
    def _bind_events(self):
        self.combo_line_account.bind("<<ComboboxSelected>>", self._on_line_account_selected)
        self.combo_line_account.bind("<FocusOut>", self._on_line_account_selected)

        for widget in (self.combo_line_account, self.ent_line_debit, self.ent_line_credit, self.ent_line_desc):
            widget.bind("<Return>", self._on_enter_add_line)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_selected)
        self.tree.bind("<Double-1>", self._on_tree_selected)
        self.tree.bind("<Delete>", lambda _e: self._delete_selected_line())

        self.frame.bind_all("<Delete>", self._on_delete_hotkey)
        self.frame.bind_all("<Control-s>", lambda _e: self._save_voucher())
        self.frame.bind_all("<Control-S>", lambda _e: self._save_voucher())

    def _on_delete_hotkey(self, _event=None):
        if self.tree.focus_displayof() is not None:
            self._delete_selected_line()

    def _fmt(self, value):
        try:
            return f"{float(value):,.2f}"
        except Exception:
            return "0.00"

    def _parse_amount(self, raw, field_name):
        txt = (raw or "").replace(",", "").strip()
        if not txt:
            return 0.0
        try:
            val = float(txt)
        except ValueError as exc:
            raise ValueError(f"{field_name} يجب أن يكون رقم") from exc
        if val < 0:
            raise ValueError(f"{field_name} لا يمكن أن يكون سالب")
        return val

    def _column_exists(self, cur, table_name, column_name):
        key = f"{table_name}.{column_name}"
        if key in self._schema_cache:
            return self._schema_cache[key]

        cur.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema='finance' AND table_name=%s AND column_name=%s
            """,
            (table_name, column_name),
        )
        exists = cur.fetchone() is not None
        self._schema_cache[key] = exists
        return exists

    def _table_exists(self, cur, table_name):
        cur.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema='finance' AND table_name=%s
            """,
            (table_name,),
        )
        return cur.fetchone() is not None

    def _get_date_value(self):
        if hasattr(self.ent_date, "entry"):
            return self.ent_date.entry.get().strip()
        return self.voucher_date_var.get().strip()

    def _set_date_value(self, value):
        if hasattr(self.ent_date, "entry"):
            self.ent_date.entry.delete(0, tk.END)
            self.ent_date.entry.insert(0, value)
        else:
            self.voucher_date_var.set(value)

    # -----------------------------
    # Data loading
    # -----------------------------
    def _load_master_data(self):
        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()

            # Accounting rule: all accounts are allowed.
            cur.execute("SELECT TRIM(account_code), COALESCE(account_name, '') FROM finance.accounts ORDER BY account_code")
            account_display = []
            self.account_display_to_code.clear()
            self.account_code_to_name.clear()
            self.account_code_to_display.clear()

            for code, name in cur.fetchall() or []:
                code_txt = str(code or "").strip()
                name_txt = str(name or "").strip()
                if not code_txt:
                    continue
                disp = f"{code_txt} - {name_txt}" if name_txt else code_txt
                account_display.append(disp)
                self.account_display_to_code[disp] = code_txt
                self.account_code_to_name[code_txt] = name_txt
                self.account_code_to_display[code_txt] = disp

            set_combobox_values(self.combo_line_account, account_display)

            cur.execute("SELECT id, COALESCE(vendor_name, '') FROM finance.vendors ORDER BY vendor_name")
            vendor_values = []
            self.vendor_display_to_id.clear()
            self.vendor_id_to_display.clear()
            for vid, vname in cur.fetchall() or []:
                if vid is None:
                    continue
                disp = f"{int(vid)} - {str(vname).strip()}"
                vendor_values.append(disp)
                self.vendor_display_to_id[disp] = int(vid)
                self.vendor_id_to_display[int(vid)] = disp

            set_combobox_values(self.combo_customer, vendor_values)
            set_combobox_values(self.combo_vendor, vendor_values)

            self._load_properties(cur)

        except Exception as exc:
            messagebox.showerror("DB Error", get_db_error_message(exc, "تعذر تحميل البيانات الأساسية"))
        finally:
            conn.close()

    def _load_properties(self, cur):
        self.property_display_to_id.clear()
        self.property_id_to_display.clear()

        if not self._table_exists(cur, "properties"):
            set_combobox_values(self.combo_property, [])
            self.combo_property.configure(state="disabled")
            return

        if self._column_exists(cur, "properties", "id"):
            id_col = "id"
        elif self._column_exists(cur, "properties", "property_id"):
            id_col = "property_id"
        else:
            set_combobox_values(self.combo_property, [])
            self.combo_property.configure(state="disabled")
            return

        name_candidates = ["property_name", "name", "property_no", "code"]
        name_col = None
        for c in name_candidates:
            if self._column_exists(cur, "properties", c):
                name_col = c
                break

        if name_col is None:
            sql = f"SELECT {id_col}::text, {id_col}::text FROM finance.properties ORDER BY {id_col}"
        else:
            sql = f"SELECT {id_col}, COALESCE({name_col}::text, '') FROM finance.properties ORDER BY {id_col}"

        cur.execute(sql)
        values = []
        for pid, pname in cur.fetchall() or []:
            if pid is None:
                continue
            pid_int = int(pid)
            display = f"{pid_int} - {str(pname or '').strip()}" if str(pname or "").strip() else str(pid_int)
            values.append(display)
            self.property_display_to_id[display] = pid_int
            self.property_id_to_display[pid_int] = display

        set_combobox_values(self.combo_property, values)
        self.combo_property.configure(state="readonly")

    # -----------------------------
    # Header behavior
    # -----------------------------
    def _on_customer_toggle(self):
        if self.customer_chk_var.get():
            self.vendor_chk_var.set(False)
            self.combo_customer.configure(state="normal")
            self.combo_vendor.configure(state="disabled")
            self.vendor_var.set("")
        else:
            self.combo_customer.configure(state="disabled")
            self.customer_var.set("")

    def _on_vendor_toggle(self):
        if self.vendor_chk_var.get():
            self.customer_chk_var.set(False)
            self.combo_vendor.configure(state="normal")
            self.combo_customer.configure(state="disabled")
            self.customer_var.set("")
        else:
            self.combo_vendor.configure(state="disabled")
            self.vendor_var.set("")

    def _open_picker(self, title, values):
        candidates = [str(v) for v in values if str(v).strip()]
        if not candidates:
            messagebox.showinfo("Info", "لا توجد بيانات متاحة")
            return None

        win = tk.Toplevel(self.master)
        win.title(title)
        win.geometry("520x430")
        win.transient(self.master)
        win.grab_set()

        search_var = tk.StringVar()
        ttk.Entry(win, textvariable=search_var, justify="right").pack(fill="x", padx=10, pady=(10, 6))

        tree = ttk.Treeview(win, columns=("value",), show="headings", selectmode="browse")
        tree.heading("value", text="اختر")
        tree.column("value", width=480, anchor="e")
        tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        picked = {"value": None}

        def refill(*_):
            q = search_var.get().strip().lower()
            tree.delete(*tree.get_children())
            for item in candidates:
                if not q or q in item.lower():
                    tree.insert("", tk.END, values=(item,))

        def choose(_event=None):
            sel = tree.selection()
            if not sel:
                return
            picked["value"] = tree.item(sel[0])["values"][0]
            win.destroy()

        ttk.Button(win, text="اختيار", style="Settlement.Orange.TButton", command=choose).pack(pady=(0, 8))
        search_var.trace_add("write", refill)
        tree.bind("<Double-1>", choose)
        refill()

        win.wait_window()
        return picked["value"]

    def _pick_customer(self):
        value = self._open_picker("اختيار عميل", self.combo_customer.cget("values"))
        if value:
            self.customer_var.set(str(value))
            self.customer_chk_var.set(True)
            self._on_customer_toggle()

    def _pick_vendor(self):
        value = self._open_picker("اختيار مورد", self.combo_vendor.cget("values"))
        if value:
            self.vendor_var.set(str(value))
            self.vendor_chk_var.set(True)
            self._on_vendor_toggle()

    # -----------------------------
    # Line editor + table
    # -----------------------------
    def _on_line_account_selected(self, _event=None):
        raw = self.line_account_var.get().strip()
        code = self.account_display_to_code.get(raw)
        if not code:
            code = raw.split("-")[0].strip() if raw else ""

        if code in self.account_code_to_name:
            self.line_account_code_var.set(code)
            self.line_account_name_var.set(self.account_code_to_name.get(code, ""))
            disp = self.account_code_to_display.get(code)
            if disp:
                self.line_account_var.set(disp)
        else:
            self.line_account_code_var.set("")
            self.line_account_name_var.set("")

    def _line_from_editor(self):
        self._on_line_account_selected()

        code = self.line_account_code_var.get().strip()
        if not code:
            raise ValueError("يجب اختيار الحساب")
        if code not in self.account_code_to_name:
            raise ValueError("الحساب غير موجود")

        debit = self._parse_amount(self.line_debit_var.get(), "المدين")
        credit = self._parse_amount(self.line_credit_var.get(), "الدائن")

        if debit > 0 and credit > 0:
            raise ValueError("لا يمكن إدخال مدين ودائن معًا في نفس السطر")
        if debit <= 0 and credit <= 0:
            raise ValueError("يجب إدخال مدين أو دائن")

        return {
            "account_code": code,
            "account_name": self.account_code_to_name.get(code, ""),
            "debit": debit,
            "credit": credit,
            "line_description": self.line_desc_var.get().strip(),
        }

    def _on_enter_add_line(self, _event=None):
        self._add_or_update_line()
        return "break"

    def _add_or_update_line(self):
        try:
            line = self._line_from_editor()
        except Exception as exc:
            messagebox.showwarning("Validation", str(exc))
            return

        if self.selected_line_iid:
            for idx, old_line in enumerate(self.entry_lines):
                if old_line.get("_iid") == self.selected_line_iid:
                    line["_iid"] = self.selected_line_iid
                    self.entry_lines[idx] = line
                    break
        else:
            line["_iid"] = f"line_{len(self.entry_lines) + 1}_{datetime.now().timestamp()}"
            self.entry_lines.append(line)

        self._refresh_tree()
        self._reset_line_editor()

    def _on_tree_selected(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return

        iid = sel[0]
        line = next((x for x in self.entry_lines if x.get("_iid") == iid), None)
        if not line:
            return

        self.selected_line_iid = iid
        code = line.get("account_code", "")
        self.line_account_var.set(self.account_code_to_display.get(code, code))
        self.line_account_code_var.set(code)
        self.line_account_name_var.set(line.get("account_name", ""))

        self.line_debit_var.set(self._fmt(line.get("debit", 0)) if float(line.get("debit", 0) or 0) > 0 else "")
        self.line_credit_var.set(self._fmt(line.get("credit", 0)) if float(line.get("credit", 0) or 0) > 0 else "")
        self.line_desc_var.set(line.get("line_description", ""))

    def _delete_selected_line(self):
        sel = self.tree.selection()
        iid = self.selected_line_iid or (sel[0] if sel else None)
        if not iid:
            return

        self.entry_lines = [x for x in self.entry_lines if x.get("_iid") != iid]
        self._refresh_tree()
        self._reset_line_editor()

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for idx, line in enumerate(self.entry_lines, start=1):
            tag = "even" if idx % 2 == 0 else "odd"
            iid = line.get("_iid", str(idx))
            self.tree.insert(
                "",
                tk.END,
                iid=iid,
                values=(
                    line.get("account_code", ""),
                    line.get("account_name", ""),
                    self._fmt(line.get("debit", 0)),
                    self._fmt(line.get("credit", 0)),
                    line.get("line_description", ""),
                ),
                tags=(tag,),
            )
            line["_iid"] = iid

        self._refresh_totals()

    def _refresh_totals(self):
        total_debit = round(sum(float(x.get("debit", 0) or 0) for x in self.entry_lines), 2)
        total_credit = round(sum(float(x.get("credit", 0) or 0) for x in self.entry_lines), 2)
        diff = round(total_debit - total_credit, 2)

        self.total_debit_var.set(self._fmt(total_debit))
        self.total_credit_var.set(self._fmt(total_credit))
        self.diff_var.set(self._fmt(diff))

        if self.entry_lines and abs(diff) < 0.005:
            self.status_var.set("متوازن")
            self.lbl_status.configure(style="Settlement.FooterOk.TLabel")
        else:
            self.status_var.set("غير متوازن")
            self.lbl_status.configure(style="Settlement.FooterBad.TLabel")

    def _reset_line_editor(self):
        self.selected_line_iid = None
        self.line_account_var.set("")
        self.line_account_code_var.set("")
        self.line_account_name_var.set("")
        self.line_debit_var.set("")
        self.line_credit_var.set("")
        self.line_desc_var.set("")
        self.tree.selection_remove(self.tree.selection())
        self.combo_line_account.focus_set()

    # -----------------------------
    # Save/update/delete/search/history
    # -----------------------------
    def _next_reference_no(self, cur):
        if not self._column_exists(cur, "vouchers", "reference_no"):
            return "10001"
        cur.execute("SELECT COALESCE(MAX(reference_no::BIGINT), 10000) + 1 FROM finance.vouchers")
        row = cur.fetchone()
        return str(row[0]) if row and row[0] is not None else "10001"

    def _fetch_next_ids(self):
        conn = get_connection()
        if not conn:
            return "تلقائي", "10001"

        try:
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM finance.vouchers")
            row = cur.fetchone()
            next_id = str(row[0]) if row and row[0] is not None else "تلقائي"
            next_ref = self._next_reference_no(cur)
            return next_id, next_ref
        except Exception:
            return "تلقائي", "10001"
        finally:
            conn.close()

    def _resolve_vendor_id(self):
        if self.vendor_chk_var.get():
            return self.vendor_display_to_id.get(self.vendor_var.get().strip())
        if self.customer_chk_var.get():
            return self.vendor_display_to_id.get(self.customer_var.get().strip())
        return None

    def _resolve_property_id(self):
        return self.property_display_to_id.get(self.property_var.get().strip())

    def _validate_before_save(self):
        if not self.entry_lines:
            raise ValueError("يجب إدخال سطر واحد على الأقل")

        total_debit = round(sum(float(x.get("debit", 0) or 0) for x in self.entry_lines), 2)
        total_credit = round(sum(float(x.get("credit", 0) or 0) for x in self.entry_lines), 2)

        if abs(total_debit - total_credit) >= 0.005:
            raise ValueError("القيد غير متوازن (يجب أن يتساوى المدين والدائن)")

        self._parse_amount(self.exchange_rate_var.get(), "سعر الصرف")

    def _upsert_voucher_header(self, cur, is_update):
        v_date = self._get_date_value() or datetime.now().strftime("%Y-%m-%d")
        ref_no = self.reference_no_var.get().strip() or "10001"
        currency = self.currency_var.get().strip() or "ريال يمني"
        exchange_rate = self._parse_amount(self.exchange_rate_var.get(), "سعر الصرف")
        description = self.general_desc_var.get().strip()

        has_ref = self._column_exists(cur, "vouchers", "reference_no")
        has_currency = self._column_exists(cur, "vouchers", "currency")
        has_exchange = self._column_exists(cur, "vouchers", "exchange_rate")

        if is_update:
            if not self.current_voucher_id:
                raise ValueError("لا يوجد قيد محمل للتعديل")

            parts = ["v_type=%s", "v_date=%s", "description=%s"]
            vals = [self.VOUCHER_TYPE, v_date, description]

            if has_ref:
                parts.append("reference_no=%s")
                vals.append(ref_no)
            if has_currency:
                parts.append("currency=%s")
                vals.append(currency)
            if has_exchange:
                parts.append("exchange_rate=%s")
                vals.append(exchange_rate)

            vals.append(self.current_voucher_id)
            cur.execute(f"UPDATE finance.vouchers SET {', '.join(parts)} WHERE id=%s", tuple(vals))
            return int(self.current_voucher_id)

        cols = ["v_type", "v_date", "description"]
        vals = [self.VOUCHER_TYPE, v_date, description]

        if has_ref:
            cols.append("reference_no")
            vals.append(ref_no)
        if has_currency:
            cols.append("currency")
            vals.append(currency)
        if has_exchange:
            cols.append("exchange_rate")
            vals.append(exchange_rate)

        cur.execute(
            f"INSERT INTO finance.vouchers ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(vals))}) RETURNING id",
            tuple(vals),
        )
        return int(cur.fetchone()[0])

    def _save_ledger_lines(self, cur, voucher_id):
        cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (voucher_id,))

        vendor_id = self._resolve_vendor_id()
        property_id = self._resolve_property_id()

        has_vendor = self._column_exists(cur, "ledger", "vendor_id")
        has_property = self._column_exists(cur, "ledger", "property_id")
        has_line_desc = self._column_exists(cur, "ledger", "line_description")
        has_desc = self._column_exists(cur, "ledger", "description")
        has_posting_date = self._column_exists(cur, "ledger", "posting_date")

        posting_date = self._get_date_value() or datetime.now().strftime("%Y-%m-%d")

        for line in self.entry_lines:
            cols = ["voucher_id", "account_code", "debit", "credit"]
            vals = [voucher_id, line["account_code"], line["debit"], line["credit"]]

            if has_vendor:
                cols.append("vendor_id")
                vals.append(vendor_id)
            if has_property:
                cols.append("property_id")
                vals.append(property_id)
            if has_line_desc:
                cols.append("line_description")
                vals.append(line.get("line_description", ""))
            elif has_desc:
                cols.append("description")
                vals.append(line.get("line_description", ""))
            if has_posting_date:
                cols.append("posting_date")
                vals.append(posting_date)

            cur.execute(
                f"INSERT INTO finance.ledger ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(vals))})",
                tuple(vals),
            )

    def _save_voucher(self):
        try:
            self._validate_before_save()
        except Exception as exc:
            messagebox.showwarning("Validation", str(exc))
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            voucher_id = self._upsert_voucher_header(cur, is_update=False)
            self._save_ledger_lines(cur, voucher_id)
            conn.commit()

            self.current_voucher_id = voucher_id
            self.voucher_id_var.set(str(voucher_id))
            messagebox.showinfo("Saved", "تم حفظ قيد التسوية بنجاح")
        except Exception as exc:
            conn.rollback()
            messagebox.showerror("DB Error", get_db_error_message(exc, "تعذر حفظ قيد التسوية"))
        finally:
            conn.close()

    def _update_voucher(self):
        current = self.voucher_id_var.get().strip()
        if current.isdigit() and not self.current_voucher_id:
            self.current_voucher_id = int(current)

        if not self.current_voucher_id:
            ask = simpledialog.askstring("تعديل", "أدخل رقم القيد:", parent=self.master)
            if not ask or not ask.isdigit():
                return
            if not self._load_voucher_by_id(int(ask)):
                return

        try:
            self._validate_before_save()
        except Exception as exc:
            messagebox.showwarning("Validation", str(exc))
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            voucher_id = self._upsert_voucher_header(cur, is_update=True)
            self._save_ledger_lines(cur, voucher_id)
            conn.commit()
            messagebox.showinfo("Updated", "تم تعديل قيد التسوية بنجاح")
        except Exception as exc:
            conn.rollback()
            messagebox.showerror("DB Error", get_db_error_message(exc, "تعذر تعديل قيد التسوية"))
        finally:
            conn.close()

    def _delete_voucher(self):
        current = self.voucher_id_var.get().strip()
        voucher_id = int(current) if current.isdigit() else None

        if voucher_id is None:
            ask = simpledialog.askstring("حذف", "أدخل رقم القيد:", parent=self.master)
            if not ask or not ask.isdigit():
                return
            voucher_id = int(ask)

        if not messagebox.askyesno("تأكيد", "هل تريد حذف قيد التسوية؟"):
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (voucher_id,))
            cur.execute("DELETE FROM finance.vouchers WHERE id=%s AND v_type=%s", (voucher_id, self.VOUCHER_TYPE))
            conn.commit()
            messagebox.showinfo("Deleted", "تم حذف قيد التسوية")
            self._reset_and_new()
        except Exception as exc:
            conn.rollback()
            messagebox.showerror("DB Error", get_db_error_message(exc, "تعذر حذف قيد التسوية"))
        finally:
            conn.close()

    def _search_voucher(self):
        ask = simpledialog.askstring("بحث", "أدخل رقم القيد:", parent=self.master)
        if not ask:
            return
        if not ask.isdigit():
            messagebox.showwarning("Validation", "رقم القيد يجب أن يكون رقمًا")
            return
        self._load_voucher_by_id(int(ask))

    def _show_history(self):
        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()

            has_ref = self._column_exists(cur, "vouchers", "reference_no")
            ref_expr = "COALESCE(v.reference_no::text, '')" if has_ref else "''"

            cur.execute(
                f"""
                SELECT
                    v.id,
                    {ref_expr} AS ref_no,
                    v.v_date,
                    COALESCE(v.description, '') AS description,
                    COALESCE(SUM(l.debit), 0) AS total_debit,
                    COALESCE(SUM(l.credit), 0) AS total_credit
                FROM finance.vouchers v
                LEFT JOIN finance.ledger l ON l.voucher_id = v.id
                WHERE v.v_type=%s
                GROUP BY v.id, ref_no, v.v_date, v.description
                ORDER BY v.v_date DESC, v.id DESC
                """,
                (self.VOUCHER_TYPE,),
            )
            rows = cur.fetchall() or []

        except Exception as exc:
            messagebox.showerror("DB Error", get_db_error_message(exc, "تعذر تحميل السجل"))
            conn.close()
            return
        finally:
            try:
                conn.close()
            except Exception:
                pass

        win = tk.Toplevel(self.master)
        win.title("سجل قيود التسوية")
        win.geometry("980x520")
        win.transient(self.master)
        win.grab_set()

        cols = ("id", "reference", "date", "desc", "debit", "credit")
        tree = ttk.Treeview(win, columns=cols, show="headings", style="Settlement.Treeview", selectmode="browse")

        tree.heading("id", text="رقم القيد", anchor="e")
        tree.heading("reference", text="المرجع", anchor="e")
        tree.heading("date", text="التاريخ", anchor="e")
        tree.heading("desc", text="البيان", anchor="e")
        tree.heading("debit", text="إجمالي المدين", anchor="e")
        tree.heading("credit", text="إجمالي الدائن", anchor="e")

        tree.column("id", width=90, anchor="e", stretch=False)
        tree.column("reference", width=120, anchor="e", stretch=False)
        tree.column("date", width=120, anchor="e", stretch=False)
        tree.column("desc", width=360, anchor="e", stretch=True)
        tree.column("debit", width=130, anchor="e", stretch=False)
        tree.column("credit", width=130, anchor="e", stretch=False)

        yscroll = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=yscroll.set)

        tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        yscroll.pack(side="left", fill="y", padx=(0, 10), pady=10)

        for idx, row in enumerate(rows, start=1):
            tag = "even" if idx % 2 == 0 else "odd"
            tree.insert(
                "",
                tk.END,
                values=(row[0], row[1], str(row[2]), row[3], self._fmt(row[4]), self._fmt(row[5])),
                tags=(tag,),
            )

        def open_selected(_event=None):
            sel = tree.selection()
            if not sel:
                return
            voucher_id = tree.item(sel[0])["values"][0]
            if str(voucher_id).isdigit() and self._load_voucher_by_id(int(voucher_id)):
                win.destroy()

        tree.bind("<Double-1>", open_selected)

        bottom = ttk.Frame(win)
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(bottom, text="فتح", style="Settlement.Orange.TButton", command=open_selected).pack(side="right")

    def _load_voucher_by_id(self, voucher_id):
        conn = get_connection()
        if not conn:
            return False

        try:
            cur = conn.cursor()

            has_ref = self._column_exists(cur, "vouchers", "reference_no")
            has_currency = self._column_exists(cur, "vouchers", "currency")
            has_exchange = self._column_exists(cur, "vouchers", "exchange_rate")

            ref_expr = "COALESCE(reference_no::text, '')" if has_ref else "''"
            currency_expr = "COALESCE(currency, 'ريال يمني')" if has_currency else "'ريال يمني'"
            exchange_expr = "COALESCE(exchange_rate, 1)" if has_exchange else "1"

            cur.execute(
                f"""
                SELECT id, {ref_expr} AS reference_no, v_date, COALESCE(description, ''), {currency_expr}, {exchange_expr}
                FROM finance.vouchers
                WHERE id=%s AND v_type=%s
                """,
                (voucher_id, self.VOUCHER_TYPE),
            )
            header = cur.fetchone()
            if not header:
                messagebox.showinfo("بحث", "القيد غير موجود")
                return False

            has_line_desc = self._column_exists(cur, "ledger", "line_description")
            has_desc = self._column_exists(cur, "ledger", "description")
            has_vendor = self._column_exists(cur, "ledger", "vendor_id")
            has_property = self._column_exists(cur, "ledger", "property_id")

            if has_line_desc:
                desc_expr = "COALESCE(line_description, '')"
            elif has_desc:
                desc_expr = "COALESCE(description, '')"
            else:
                desc_expr = "''"

            vendor_expr = "vendor_id" if has_vendor else "NULL"
            property_expr = "property_id" if has_property else "NULL"

            cur.execute(
                f"""
                SELECT account_code, COALESCE(debit, 0), COALESCE(credit, 0), {desc_expr} AS line_desc, {vendor_expr}, {property_expr}
                FROM finance.ledger
                WHERE voucher_id=%s
                ORDER BY id
                """,
                (voucher_id,),
            )
            lines = cur.fetchall() or []

            self.current_voucher_id = int(header[0])
            self.voucher_id_var.set(str(header[0]))
            self.reference_no_var.set(str(header[1] or ""))
            self._set_date_value(str(header[2]))
            self.currency_var.set(str(header[4] or "ريال يمني"))
            self.exchange_rate_var.set(self._fmt(header[5] or 1))
            self.general_desc_var.set(str(header[3] or ""))

            self.entry_lines.clear()
            first_vendor = None
            first_property = None
            for idx, (acc_code, debit, credit, line_desc, vendor_id, property_id) in enumerate(lines, start=1):
                code = str(acc_code or "").strip()
                if not code:
                    continue
                self.entry_lines.append(
                    {
                        "_iid": f"load_{idx}",
                        "account_code": code,
                        "account_name": self.account_code_to_name.get(code, ""),
                        "debit": float(debit or 0),
                        "credit": float(credit or 0),
                        "line_description": str(line_desc or ""),
                    }
                )
                if first_vendor is None and vendor_id is not None:
                    first_vendor = int(vendor_id)
                if first_property is None and property_id is not None:
                    first_property = int(property_id)

            if first_vendor is not None:
                self.vendor_chk_var.set(True)
                self.customer_chk_var.set(False)
                self.vendor_var.set(self.vendor_id_to_display.get(first_vendor, ""))
                self.customer_var.set("")
                self._on_vendor_toggle()
            else:
                self.vendor_chk_var.set(False)
                self.customer_chk_var.set(False)
                self.vendor_var.set("")
                self.customer_var.set("")
                self._on_customer_toggle()
                self._on_vendor_toggle()

            if first_property is not None:
                self.property_var.set(self.property_id_to_display.get(first_property, str(first_property)))
            else:
                self.property_var.set("")

            self._refresh_tree()
            self._reset_line_editor()
            return True

        except Exception as exc:
            messagebox.showerror("DB Error", get_db_error_message(exc, "تعذر تحميل قيد التسوية"))
            return False
        finally:
            conn.close()

    def _print_voucher(self):
        voucher_id = self.voucher_id_var.get().strip()
        if not voucher_id.isdigit():
            messagebox.showwarning("Validation", "يجب حفظ القيد قبل الطباعة")
            return
        messagebox.showinfo("طباعة", f"تم تجهيز قيد التسوية رقم {voucher_id} للطباعة")

    def _reset_and_new(self, initial=False):
        self.current_voucher_id = None

        self.voucher_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self._set_date_value(self.voucher_date_var.get())
        self.currency_var.set("ريال يمني")
        self.exchange_rate_var.set("1.00")
        self.general_desc_var.set("")

        self.customer_chk_var.set(False)
        self.vendor_chk_var.set(False)
        self.customer_var.set("")
        self.vendor_var.set("")
        self.property_var.set("")
        self._on_customer_toggle()
        self._on_vendor_toggle()

        self.entry_lines.clear()
        self._refresh_tree()
        self._reset_line_editor()

        next_id, next_ref = self._fetch_next_ids()
        self.voucher_id_var.set(next_id)
        self.reference_no_var.set(next_ref)

        if not initial:
            self.combo_line_account.focus_set()


# Backward-compatible aliases for existing imports.
JournalVoucherScreen = SettlementEntryScreen
AdjustmentJournalEntryScreen = SettlementEntryScreen


if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    root.title("Settlement Entry")
    root.geometry("1420x900")
    SettlementEntryScreen(root)
    root.mainloop()
