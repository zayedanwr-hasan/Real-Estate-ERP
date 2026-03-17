import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
import ttkbootstrap as ttk

from db_connection import get_connection


class ManualJournalScreen:
    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.separator_color = "#2c3e50"
        self.bg_color = "#f4f7f6"

        self._ledger_column_cache = {}
        self.current_voucher_id = None
        self.current_line_index = None
        self.journal_lines = []
        self.account_data = {}
        self.property_data = {}
        self.vendor_data = {}
        self.project_data = {}

        self.voucher_types = ["Journal", "Adjustment", "Opening"]

        self.voucher_id_var = tk.StringVar(value="تلقائي")
        self.voucher_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.voucher_type_var = tk.StringVar(value="Journal")

        self.line_account_var = tk.StringVar()
        self.line_debit_var = tk.StringVar(value="0.00")
        self.line_credit_var = tk.StringVar(value="0.00")
        self.line_property_var = tk.StringVar()
        self.line_vendor_var = tk.StringVar()
        self.line_project_var = tk.StringVar()

        self.total_debit_var = tk.StringVar(value="0.00")
        self.total_credit_var = tk.StringVar(value="0.00")
        self.difference_var = tk.StringVar(value="0.00")
        self.amount_words_var = tk.StringVar(value="فقط صفر")
        self.balance_status_var = tk.StringVar(value="القيد غير متوازن")

        self._setup_styles()
        self._build_layout()
        self._bind_shortcuts()
        self._load_initial_data()
        self._reset_and_new(initial=True)

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("App.Journal.Root.TFrame", background=self.bg_color)
        style.configure("App.Journal.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("App.Journal.Header.TFrame", background=self.primary_color)
        style.configure("App.Journal.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 20, "bold"))
        style.configure("App.Journal.Content.TFrame", background="white")
        style.configure("App.Journal.FieldLabel.TLabel", background=self.sidebar_color, foreground=self.text_color, font=("Segoe UI", 13, "bold"), anchor="center", padding=9)
        style.configure("App.Journal.Field.TEntry", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 14, "bold"))
        style.configure("App.Journal.Field.TCombobox", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 13, "bold"))
        style.configure("App.Journal.SectionTitle.TLabel", background="white", foreground=self.primary_color, font=("Segoe UI", 13, "bold"))
        style.configure("App.Journal.Status.TLabel", background="white", foreground=self.sidebar_color, font=("Segoe UI", 12, "bold"))
        style.configure("App.Journal.Total.TFrame", background="#f8f9fa", bordercolor="#d8e1e8", borderwidth=1, relief="solid")
        style.configure("App.Journal.TotalAmount.TLabel", background="#f8f9fa", foreground="#c0392b", font=("Segoe UI", 22, "bold"))
        style.configure("App.Journal.TotalWords.TLabel", background="#f8f9fa", foreground=self.sidebar_color, font=("Segoe UI", 13, "bold"))

        style.configure("App.Journal.Primary.TButton", background="#2980b9", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Journal.Success.TButton", background="#27ae60", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Journal.Warning.TButton", background="#f1c40f", foreground="#2c3e50", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Journal.Danger.TButton", background="#e74c3c", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Journal.Info.TButton", background="#8e44ad", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Journal.Exit.TButton", background="#e67e22", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))

        for btn_style in (
            "App.Journal.Primary.TButton",
            "App.Journal.Success.TButton",
            "App.Journal.Warning.TButton",
            "App.Journal.Danger.TButton",
            "App.Journal.Info.TButton",
            "App.Journal.Exit.TButton",
        ):
            style.map(
                btn_style,
                background=[("active", self.accent_color), ("pressed", self.accent_color)],
                foreground=[("active", "white"), ("pressed", "white")],
            )

        style.configure(
            "App.Journal.Treeview",
            rowheight=30,
            font=("Segoe UI", 11),
            background="white",
            fieldbackground="white",
            foreground=self.primary_color,
        )
        style.configure(
            "App.Journal.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background=self.primary_color,
            foreground="white",
        )
        style.map("App.Journal.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "white")])
        style.map(
            "App.Journal.Treeview.Heading",
            background=[("active", self.primary_color), ("pressed", self.primary_color)],
            foreground=[("active", "white"), ("pressed", "white")],
        )
        style.configure("App.Journal.Vertical.TScrollbar", background=self.sidebar_color, troughcolor=self.bg_color, arrowcolor=self.primary_color)
        style.configure("App.Journal.Horizontal.TScrollbar", background=self.sidebar_color, troughcolor=self.bg_color, arrowcolor=self.primary_color)

    def _build_layout(self):
        self.frame = ttk.Frame(self.master, style="App.Journal.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.main_card = ttk.Frame(self.frame, style="App.Journal.Card.TFrame")
        self.main_card.pack(fill="both", expand=True, padx=14, pady=14)
        self.main_card.grid_rowconfigure(1, weight=1)
        self.main_card.grid_columnconfigure(0, weight=1)

        self._build_header_buttons()
        self._build_content()

    def _build_header_buttons(self):
        header = ttk.Frame(self.main_card, style="App.Journal.Header.TFrame", height=68)
        header.pack(fill="x", side="top")

        ttk.Label(header, text="قيد يومية - Al-Sofi ERP", style="App.Journal.Header.TLabel").pack(side="right", padx=30, pady=15)

        btn_group = ttk.Frame(header, style="App.Journal.Header.TFrame")
        btn_group.pack(side="left", padx=20)

        self.btn_new = ttk.Button(btn_group, text="جديد", style="App.Journal.Primary.TButton", width=9, command=self._reset_and_new)
        self.btn_new.pack(side="left", padx=5)
        self.btn_save = ttk.Button(btn_group, text="حفظ", style="App.Journal.Success.TButton", width=9, command=self._save_journal)
        self.btn_save.pack(side="left", padx=5)
        self.btn_update = ttk.Button(btn_group, text="تعديل", style="App.Journal.Warning.TButton", width=9, command=self._update_journal)
        self.btn_update.pack(side="left", padx=5)
        self.btn_delete = ttk.Button(btn_group, text="حذف", style="App.Journal.Danger.TButton", width=9, command=self._delete_journal)
        self.btn_delete.pack(side="left", padx=5)
        self.btn_search = ttk.Button(btn_group, text="بحث", style="App.Journal.Info.TButton", width=9, command=self._search_journal)
        self.btn_search.pack(side="left", padx=5)
        self.btn_exit = ttk.Button(btn_group, text="خروج", style="App.Journal.Exit.TButton", width=9, command=self._exit_screen)
        self.btn_exit.pack(side="left", padx=5)

    def _build_content(self):
        self.content = ttk.Frame(self.main_card, style="App.Journal.Content.TFrame", padding=(24, 18))
        self.content.pack(fill="both", expand=True)
        self.content.grid_rowconfigure(2, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self._build_voucher_header_card()
        self._build_entry_line_card()
        self._build_ledger_grid()
        self._build_footer()

    def _build_voucher_header_card(self):
        card = ttk.Frame(self.content, style="App.Journal.Card.TFrame", padding=16)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        for col in range(4):
            card.grid_columnconfigure(col, weight=1)

        ttk.Label(card, text="بيانات القيد", style="App.Journal.SectionTitle.TLabel").grid(row=0, column=3, sticky="e", pady=(0, 10))

        self.ent_id = self._create_field(card, "رقم القيد :", 1, 3, textvariable=self.voucher_id_var, state="readonly")
        self.ent_date = self._create_field(card, "التاريخ :", 1, 2, textvariable=self.voucher_date_var)
        self.combo_vtype = self._create_field(card, "نوع القيد :", 1, 1, widget_type="combo", textvariable=self.voucher_type_var, values=self.voucher_types, state="readonly")
        self.combo_vtype.set("Journal")

        desc_container = ttk.Frame(card, style="App.Journal.Content.TFrame")
        desc_container.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        desc_container.grid_columnconfigure(0, weight=1)
        ttk.Label(desc_container, text="الوصف العام :", style="App.Journal.FieldLabel.TLabel", width=20).grid(row=0, column=1, sticky="ns")
        self.txt_general_desc = tk.Text(desc_container, font=("Segoe UI", 12, "bold"), bd=1, relief="solid", height=3, wrap="word")
        self.txt_general_desc.grid(row=0, column=0, sticky="ew", padx=(0, 15))

    def _build_entry_line_card(self):
        card = ttk.Frame(self.content, style="App.Journal.Card.TFrame", padding=16)
        card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        for col in range(4):
            card.grid_columnconfigure(col, weight=1)

        ttk.Label(card, text="سطر القيد الذكي", style="App.Journal.SectionTitle.TLabel").grid(row=0, column=3, sticky="e", pady=(0, 10))

        self.combo_account = self._create_field(card, "الحساب :", 1, 3, widget_type="combo", textvariable=self.line_account_var, state="readonly")
        self.combo_account.bind("<<ComboboxSelected>>", self._on_account_selected)
        self.ent_debit = self._create_field(card, "مدين :", 1, 2, textvariable=self.line_debit_var)
        self.ent_credit = self._create_field(card, "دائن :", 1, 1, textvariable=self.line_credit_var)

        detail_container = ttk.Frame(card, style="App.Journal.Content.TFrame")
        detail_container.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(8, 8))
        detail_container.grid_columnconfigure(0, weight=1)
        ttk.Label(detail_container, text="تفصيل السطر :", style="App.Journal.FieldLabel.TLabel", width=20).grid(row=0, column=1, sticky="ns")
        self.txt_line_detail = tk.Text(detail_container, font=("Segoe UI", 12, "bold"), bd=1, relief="solid", height=2, wrap="word")
        self.txt_line_detail.grid(row=0, column=0, sticky="ew", padx=(0, 15))

        dims = ttk.Frame(card, style="App.Journal.Content.TFrame")
        dims.grid(row=4, column=0, columnspan=4, sticky="ew")
        for col in range(3):
            dims.grid_columnconfigure(col, weight=1)

        self.property_label = ttk.Label(dims, text="العقار :", style="App.Journal.FieldLabel.TLabel")
        self.property_label.grid(row=0, column=2, sticky="ew", padx=(10, 0))
        self.combo_property = ttk.Combobox(dims, style="App.Journal.Field.TCombobox", textvariable=self.line_property_var, state="readonly", justify="right")
        self.combo_property.grid(row=1, column=2, sticky="ew", padx=(10, 0), pady=(4, 0))
        self.combo_property.bind("<<ComboboxSelected>>", self._on_property_selected)

        self.vendor_label = ttk.Label(dims, text="الوارث / المالك :", style="App.Journal.FieldLabel.TLabel")
        self.vendor_label.grid(row=0, column=1, sticky="ew", padx=(10, 10))
        self.combo_vendor = ttk.Combobox(dims, style="App.Journal.Field.TCombobox", textvariable=self.line_vendor_var, state="readonly", justify="right")
        self.combo_vendor.grid(row=1, column=1, sticky="ew", padx=(10, 10), pady=(4, 0))

        self.project_label = ttk.Label(dims, text="المشروع :", style="App.Journal.FieldLabel.TLabel")
        self.project_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.combo_project = ttk.Combobox(dims, style="App.Journal.Field.TCombobox", textvariable=self.line_project_var, state="readonly", justify="right")
        self.combo_project.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(4, 0))

        line_btns = ttk.Frame(card, style="App.Journal.Content.TFrame")
        line_btns.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(14, 0))
        line_btns.grid_columnconfigure(0, weight=1)
        line_btns.grid_columnconfigure(1, weight=1)
        line_btns.grid_columnconfigure(2, weight=1)
        line_btns.grid_columnconfigure(3, weight=1)

        self.btn_add_line = ttk.Button(line_btns, text="إضافة سطر", style="App.Journal.Primary.TButton", command=self._add_or_update_line)
        self.btn_add_line.grid(row=0, column=3, sticky="ew", padx=(0, 8))
        self.btn_edit_line = ttk.Button(line_btns, text="تحميل السطر المحدد", style="App.Journal.Warning.TButton", command=self._load_selected_line)
        self.btn_edit_line.grid(row=0, column=2, sticky="ew", padx=8)
        self.btn_delete_line = ttk.Button(line_btns, text="حذف السطر المحدد", style="App.Journal.Danger.TButton", command=self._delete_selected_line)
        self.btn_delete_line.grid(row=0, column=1, sticky="ew", padx=8)
        self.btn_clear_line = ttk.Button(line_btns, text="مسح السطر", style="App.Journal.Info.TButton", command=self._clear_line_editor)
        self.btn_clear_line.grid(row=0, column=0, sticky="ew", padx=(8, 0))

    def _build_ledger_grid(self):
        card = ttk.Frame(self.content, style="App.Journal.Card.TFrame", padding=16)
        card.grid(row=2, column=0, sticky="nsew", pady=(0, 12))
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        ttk.Label(card, text="خطوط القيد", style="App.Journal.SectionTitle.TLabel").grid(row=0, column=0, sticky="e", pady=(0, 10))

        table_wrap = ttk.Frame(card, style="App.Journal.Content.TFrame")
        table_wrap.grid(row=1, column=0, sticky="nsew")
        table_wrap.grid_rowconfigure(0, weight=1)
        table_wrap.grid_columnconfigure(0, weight=1)

        columns = ("code", "name", "debit", "credit", "detail", "property", "vendor", "project")
        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings", style="App.Journal.Treeview")
        headings = {
            "code": "كود الحساب",
            "name": "اسم الحساب",
            "debit": "مدين",
            "credit": "دائن",
            "detail": "البيان",
            "property": "العقار",
            "vendor": "الوارث",
            "project": "المشروع",
        }
        widths = {
            "code": 110,
            "name": 210,
            "debit": 110,
            "credit": 110,
            "detail": 220,
            "property": 150,
            "vendor": 150,
            "project": 150,
        }
        for col in columns:
            self.tree.heading(col, text=headings[col], anchor="center")
            self.tree.column(col, anchor="center", width=widths[col], stretch=True)

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", style="App.Journal.Vertical.TScrollbar", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_wrap, orient="horizontal", style="App.Journal.Horizontal.TScrollbar", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        self.tree.tag_configure("odd", background="#ffffff")
        self.tree.tag_configure("even", background="#f0f3f5")
        self.tree.tag_configure("empty", foreground=self.sidebar_color)
        self.tree.bind("<Double-1>", lambda _e: self._load_selected_line())

    def _build_footer(self):
        footer = ttk.Frame(self.content, style="App.Journal.Total.TFrame", padding=16)
        footer.grid(row=3, column=0, sticky="ew")
        for col in range(4):
            footer.grid_columnconfigure(col, weight=1)

        ttk.Label(footer, text="إجمالي المدين", style="App.Journal.Status.TLabel").grid(row=0, column=3, sticky="e")
        ttk.Label(footer, textvariable=self.total_debit_var, style="App.Journal.TotalAmount.TLabel").grid(row=1, column=3, sticky="e")

        ttk.Label(footer, text="إجمالي الدائن", style="App.Journal.Status.TLabel").grid(row=0, column=2, sticky="e")
        ttk.Label(footer, textvariable=self.total_credit_var, style="App.Journal.TotalAmount.TLabel").grid(row=1, column=2, sticky="e")

        ttk.Label(footer, text="الفرق", style="App.Journal.Status.TLabel").grid(row=0, column=1, sticky="e")
        ttk.Label(footer, textvariable=self.difference_var, style="App.Journal.TotalAmount.TLabel").grid(row=1, column=1, sticky="e")

        ttk.Label(footer, textvariable=self.balance_status_var, style="App.Journal.Status.TLabel").grid(row=0, column=0, sticky="e")
        ttk.Label(footer, textvariable=self.amount_words_var, style="App.Journal.TotalWords.TLabel", anchor="e", justify="right").grid(row=1, column=0, sticky="e")

    def _create_field(self, parent, label_text, row, column, widget_type="entry", **kwargs):
        container = ttk.Frame(parent, style="App.Journal.Content.TFrame")
        container.grid(row=row, column=column, sticky="ew", padx=6, pady=6)
        container.grid_columnconfigure(0, weight=1)

        if widget_type == "entry":
            field = ttk.Entry(container, style="App.Journal.Field.TEntry", justify="right", **kwargs)
        else:
            field = ttk.Combobox(container, style="App.Journal.Field.TCombobox", justify="right", **kwargs)

        field.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Label(container, text=label_text, style="App.Journal.FieldLabel.TLabel", width=18).grid(row=0, column=1, sticky="ns")
        return field

    def _bind_shortcuts(self):
        self.frame.bind_all("<Control-s>", lambda _e: self._save_journal())
        self.frame.bind_all("<Control-S>", lambda _e: self._save_journal())

    def _load_initial_data(self):
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT TRIM(account_code), account_name, COALESCE(account_type, ''), COALESCE(nature, '')
                FROM finance.accounts
                ORDER BY account_code
                """
            )
            account_rows = cur.fetchall()
            self.account_data = {
                f"{r[0]} - {r[1]}": {
                    "code": str(r[0]).strip(),
                    "name": r[1] or "",
                    "type": r[2] or "",
                    "nature": r[3] or "",
                }
                for r in account_rows
            }
            self.combo_account["values"] = list(self.account_data.keys())

            cur.execute("SELECT id, property_name, COALESCE(project_id, 0) FROM finance.properties ORDER BY property_name")
            property_rows = cur.fetchall()
            self.property_data = {
                f"{r[0]} - {r[1]}": {"id": r[0], "name": r[1], "project_id": r[2] or None}
                for r in property_rows
            }
            self.combo_property["values"] = list(self.property_data.keys())

            cur.execute("SELECT id, vendor_name FROM finance.vendors ORDER BY vendor_name")
            vendor_rows = cur.fetchall()
            self.vendor_data = {f"{r[0]} - {r[1]}": {"id": r[0], "name": r[1]} for r in vendor_rows}
            self.combo_vendor["values"] = list(self.vendor_data.keys())

            cur.execute("SELECT id, project_name FROM finance.projects ORDER BY project_name")
            project_rows = cur.fetchall()
            self.project_data = {f"{r[0]} - {r[1]}": {"id": r[0], "name": r[1]} for r in project_rows}
            self.combo_project["values"] = list(self.project_data.keys())
        except Exception as e:
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _ledger_has_column(self, cursor, column_name):
        if column_name in self._ledger_column_cache:
            return self._ledger_column_cache[column_name]
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'finance'
                  AND table_name = 'ledger'
                  AND column_name = %s
            )
            """,
            (column_name,),
        )
        exists = bool(cursor.fetchone()[0])
        self._ledger_column_cache[column_name] = exists
        return exists

    def _get_next_voucher_id(self):
        conn = get_connection()
        if not conn:
            return "تلقائي"
        try:
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM finance.vouchers")
            return str(cur.fetchone()[0])
        except Exception:
            return "تلقائي"
        finally:
            conn.close()

    def _reset_and_new(self, initial=False):
        self.current_voucher_id = None
        self.voucher_id_var.set(self._get_next_voucher_id())
        self.voucher_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.voucher_type_var.set("Journal")
        self.txt_general_desc.delete("1.0", tk.END)
        self.journal_lines = []
        self.current_line_index = None
        self._clear_line_editor()
        self._render_lines()
        self._set_header_button_states()
        if not initial:
            self.ent_date.focus_set()

    def _clear_line_editor(self):
        self.current_line_index = None
        self.line_account_var.set("")
        self.line_debit_var.set("0.00")
        self.line_credit_var.set("0.00")
        self.line_property_var.set("")
        self.line_vendor_var.set("")
        self.line_project_var.set("")
        self.txt_line_detail.delete("1.0", tk.END)
        self.btn_add_line.configure(text="إضافة سطر")
        self._update_dimension_visibility()

    def _update_dimension_visibility(self, show_property=False, show_vendor=False, show_project=False):
        widgets = [
            (self.property_label, self.combo_property, show_property),
            (self.vendor_label, self.combo_vendor, show_vendor),
            (self.project_label, self.combo_project, show_project),
        ]
        for label, combo, visible in widgets:
            if visible:
                label.grid()
                combo.grid()
            else:
                label.grid_remove()
                combo.grid_remove()
                combo.set("")

    def _infer_dimension_rule(self, account_code, account_name):
        name = (account_name or "").lower()
        code = str(account_code or "").strip()

        show_property = False
        show_vendor = False
        show_project = False

        if code == "2101" or any(k in name for k in ["owner", "vendor", "warith", "وارث", "مالك"]):
            show_property = True
            show_vendor = True
        elif any(k in name for k in ["land", "development", "under development", "عقار", "أرض", "تطوير"]):
            show_property = True
        elif any(k in name for k in ["project", "مشروع"]):
            show_project = True

        return show_property, show_vendor, show_project

    def _on_account_selected(self, _event=None):
        account_text = self.line_account_var.get().strip()
        account_info = self.account_data.get(account_text)
        if not account_info:
            self._update_dimension_visibility()
            return
        self._update_dimension_visibility(*self._infer_dimension_rule(account_info["code"], account_info["name"]))

    def _on_property_selected(self, _event=None):
        property_info = self.property_data.get(self.line_property_var.get().strip())
        if not property_info:
            return
        project_id = property_info.get("project_id")
        if not project_id:
            return
        for text, info in self.project_data.items():
            if info["id"] == project_id:
                self.line_project_var.set(text)
                break

    def _parse_amount(self, value, field_name):
        text = (value or "").strip()
        if not text:
            return 0.0
        try:
            return float(text)
        except ValueError:
            raise ValueError(f"{field_name} يجب أن يكون رقمًا صحيحًا")

    def _build_line_payload(self):
        account_text = self.line_account_var.get().strip()
        if not account_text:
            raise ValueError("اختر الحساب أولاً")
        account = self.account_data.get(account_text)
        if not account:
            raise ValueError("الحساب المختار غير صالح")

        debit = self._parse_amount(self.line_debit_var.get(), "المدين")
        credit = self._parse_amount(self.line_credit_var.get(), "الدائن")
        if debit <= 0 and credit <= 0:
            raise ValueError("أدخل مبلغًا في المدين أو الدائن")
        if debit > 0 and credit > 0:
            raise ValueError("لا يمكن إدخال مدين ودائن في نفس السطر")

        detail = self.txt_line_detail.get("1.0", tk.END).strip()

        property_text = self.line_property_var.get().strip()
        vendor_text = self.line_vendor_var.get().strip()
        project_text = self.line_project_var.get().strip()

        property_info = self.property_data.get(property_text)
        vendor_info = self.vendor_data.get(vendor_text)
        project_info = self.project_data.get(project_text)

        if property_info and not project_info and property_info.get("project_id"):
            for proj_text, proj in self.project_data.items():
                if proj["id"] == property_info["project_id"]:
                    project_info = proj
                    project_text = proj_text
                    break

        return {
            "account_code": account["code"],
            "account_name": account["name"],
            "debit": debit,
            "credit": credit,
            "detail": detail,
            "property_id": property_info["id"] if property_info else None,
            "property_name": property_info["name"] if property_info else "",
            "vendor_id": vendor_info["id"] if vendor_info else None,
            "vendor_name": vendor_info["name"] if vendor_info else "",
            "project_id": project_info["id"] if project_info else None,
            "project_name": project_info["name"] if project_info else "",
        }

    def _add_or_update_line(self):
        try:
            line = self._build_line_payload()
        except Exception as e:
            return messagebox.showwarning("تنبيه", str(e))

        if self.current_line_index is None:
            self.journal_lines.append(line)
        else:
            self.journal_lines[self.current_line_index] = line

        self._render_lines()
        self._clear_line_editor()

    def _render_lines(self):
        self.tree.delete(*self.tree.get_children())
        if not self.journal_lines:
            self.tree.insert("", "end", values=("", "No Data Available", "", "", "", "", "", ""), tags=("empty",))
        else:
            for idx, line in enumerate(self.journal_lines):
                tag = "even" if idx % 2 == 0 else "odd"
                self.tree.insert(
                    "",
                    "end",
                    iid=str(idx),
                    values=(
                        line["account_code"],
                        line["account_name"],
                        f"{line['debit']:,.2f}",
                        f"{line['credit']:,.2f}",
                        line["detail"],
                        line["property_name"],
                        line["vendor_name"],
                        line["project_name"],
                    ),
                    tags=(tag,),
                )
        self._update_totals()

    def _load_selected_line(self):
        selected = self.tree.selection()
        if not selected:
            return messagebox.showwarning("تنبيه", "اختر سطرًا من الجدول أولاً")
        iid = selected[0]
        if not iid.isdigit():
            return
        index = int(iid)
        if not (0 <= index < len(self.journal_lines)):
            return

        line = self.journal_lines[index]
        self.current_line_index = index
        self.line_account_var.set(f"{line['account_code']} - {line['account_name']}")
        self.line_debit_var.set(f"{line['debit']:.2f}")
        self.line_credit_var.set(f"{line['credit']:.2f}")
        self.line_property_var.set(self._find_combo_text(self.property_data, line.get("property_id")))
        self.line_vendor_var.set(self._find_combo_text(self.vendor_data, line.get("vendor_id")))
        self.line_project_var.set(self._find_combo_text(self.project_data, line.get("project_id")))
        self.txt_line_detail.delete("1.0", tk.END)
        self.txt_line_detail.insert("1.0", line.get("detail", ""))
        self._on_account_selected()
        self.btn_add_line.configure(text="تحديث السطر")

    def _delete_selected_line(self):
        selected = self.tree.selection()
        if not selected:
            return messagebox.showwarning("تنبيه", "اختر سطرًا من الجدول أولاً")
        iid = selected[0]
        if not iid.isdigit():
            return
        index = int(iid)
        if not (0 <= index < len(self.journal_lines)):
            return
        if not messagebox.askyesno("تأكيد", "هل تريد حذف السطر المحدد؟"):
            return
        del self.journal_lines[index]
        self._clear_line_editor()
        self._render_lines()

    def _update_totals(self):
        total_debit = sum(line["debit"] for line in self.journal_lines)
        total_credit = sum(line["credit"] for line in self.journal_lines)
        difference = round(total_debit - total_credit, 2)

        self.total_debit_var.set(f"{total_debit:,.2f}")
        self.total_credit_var.set(f"{total_credit:,.2f}")
        self.difference_var.set(f"{difference:,.2f}")
        self.amount_words_var.set(self._amount_to_words(total_debit if total_debit > 0 else 0))

        if self.journal_lines and abs(difference) < 0.005:
            self.balance_status_var.set("القيد متوازن")
            self.btn_save.configure(state="normal")
            self.btn_update.configure(state="normal" if self.current_voucher_id else "disabled")
        else:
            self.balance_status_var.set("القيد غير متوازن")
            self.btn_save.configure(state="disabled")
            self.btn_update.configure(state="disabled" if not self.current_voucher_id else "disabled")

    def _set_header_button_states(self):
        self.btn_save.configure(state="disabled")
        self.btn_update.configure(state="normal" if self.current_voucher_id else "disabled")
        self.btn_delete.configure(state="normal" if self.current_voucher_id else "disabled")

    def _find_combo_text(self, data_map, record_id):
        if not record_id:
            return ""
        for text, payload in data_map.items():
            if payload["id"] == record_id:
                return text
        return ""

    def _validate_before_save(self):
        if not self.journal_lines:
            raise ValueError("أضف سطر قيد واحد على الأقل")
        if abs(sum(l["debit"] for l in self.journal_lines) - sum(l["credit"] for l in self.journal_lines)) >= 0.005:
            raise ValueError("القيد غير متوازن")
        if not self.voucher_date_var.get().strip():
            raise ValueError("أدخل تاريخ القيد")
        if not self.voucher_type_var.get().strip():
            raise ValueError("اختر نوع القيد")

    def _insert_ledger_line(self, cur, voucher_id, line):
        columns = ["voucher_id", "account_code", "debit", "credit", "property_id", "vendor_id"]
        values = [voucher_id, line["account_code"], line["debit"] or 0, line["credit"] or 0, line["property_id"], line["vendor_id"]]

        if self._ledger_has_column(cur, "project_id"):
            columns.append("project_id")
            values.append(line["project_id"])
        if self._ledger_has_column(cur, "description"):
            columns.append("description")
            values.append(line["detail"])

        sql = f"INSERT INTO finance.ledger ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(values))})"
        cur.execute(sql, tuple(values))

    def _save_journal(self):
        try:
            self._validate_before_save()
        except Exception as e:
            return messagebox.showwarning("تنبيه", str(e))

        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO finance.vouchers (v_type, v_date, description) VALUES (%s, %s, %s) RETURNING id",
                (self.voucher_type_var.get().strip(), self.voucher_date_var.get().strip(), self.txt_general_desc.get("1.0", tk.END).strip()),
            )
            voucher_id = cur.fetchone()[0]
            for line in self.journal_lines:
                self._insert_ledger_line(cur, voucher_id, line)
            conn.commit()
            self.current_voucher_id = voucher_id
            self.voucher_id_var.set(str(voucher_id))
            messagebox.showinfo("نجاح", "تم حفظ القيد بنجاح")
            self._set_header_button_states()
            self._update_totals()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _update_journal(self):
        if not self.current_voucher_id:
            return messagebox.showwarning("تنبيه", "ابحث عن قيد محفوظ أولاً")
        try:
            self._validate_before_save()
        except Exception as e:
            return messagebox.showwarning("تنبيه", str(e))

        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE finance.vouchers SET v_type=%s, v_date=%s, description=%s WHERE id=%s",
                (self.voucher_type_var.get().strip(), self.voucher_date_var.get().strip(), self.txt_general_desc.get("1.0", tk.END).strip(), self.current_voucher_id),
            )
            cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (self.current_voucher_id,))
            for line in self.journal_lines:
                self._insert_ledger_line(cur, self.current_voucher_id, line)
            conn.commit()
            messagebox.showinfo("نجاح", "تم تعديل القيد بنجاح")
            self._set_header_button_states()
            self._update_totals()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _delete_journal(self):
        if not self.current_voucher_id:
            if self.journal_lines and messagebox.askyesno("تأكيد", "هل تريد مسح القيد الحالي غير المحفوظ؟"):
                self._reset_and_new()
            return
        if not messagebox.askyesno("تأكيد", "هل تريد حذف القيد المحدد؟"):
            return

        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (self.current_voucher_id,))
            cur.execute("DELETE FROM finance.vouchers WHERE id=%s", (self.current_voucher_id,))
            conn.commit()
            messagebox.showinfo("نجاح", "تم حذف القيد")
            self._reset_and_new()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _fetch_journal_lines(self, cur, voucher_id):
        has_project = self._ledger_has_column(cur, "project_id")
        has_desc = self._ledger_has_column(cur, "description")

        project_select = "COALESCE(l.project_id, p.project_id, 0) AS project_id" if has_project else "COALESCE(p.project_id, 0) AS project_id"
        project_join = "LEFT JOIN finance.projects pr ON pr.id = COALESCE(l.project_id, p.project_id)" if has_project else "LEFT JOIN finance.projects pr ON pr.id = p.project_id"
        detail_select = "COALESCE(l.description, '') AS detail" if has_desc else "'' AS detail"

        query = f"""
            SELECT l.id,
                   TRIM(l.account_code) AS account_code,
                   COALESCE(a.account_name, '') AS account_name,
                   COALESCE(l.debit, 0) AS debit,
                   COALESCE(l.credit, 0) AS credit,
                   {detail_select},
                   COALESCE(l.property_id, 0) AS property_id,
                   COALESCE(p.property_name, '') AS property_name,
                   COALESCE(l.vendor_id, 0) AS vendor_id,
                   COALESCE(v.vendor_name, '') AS vendor_name,
                   {project_select},
                   COALESCE(pr.project_name, '') AS project_name
            FROM finance.ledger l
            LEFT JOIN finance.accounts a ON TRIM(a.account_code) = TRIM(l.account_code)
            LEFT JOIN finance.properties p ON p.id = l.property_id
            LEFT JOIN finance.vendors v ON v.id = l.vendor_id
            {project_join}
            WHERE l.voucher_id = %s
            ORDER BY l.id
        """
        cur.execute(query, (voucher_id,))
        rows = cur.fetchall()
        result = []
        for row in rows:
            result.append(
                {
                    "ledger_id": row[0],
                    "account_code": row[1],
                    "account_name": row[2],
                    "debit": float(row[3] or 0),
                    "credit": float(row[4] or 0),
                    "detail": row[5] or "",
                    "property_id": row[6] or None,
                    "property_name": row[7] or "",
                    "vendor_id": row[8] or None,
                    "vendor_name": row[9] or "",
                    "project_id": row[10] or None,
                    "project_name": row[11] or "",
                }
            )
        return result

    def _search_journal(self):
        voucher_id = simpledialog.askstring("بحث", "أدخل رقم القيد:", parent=self.master)
        if not voucher_id:
            return
        if not voucher_id.isdigit():
            return messagebox.showwarning("تنبيه", "رقم القيد يجب أن يكون رقمًا")

        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, v_date, v_type, COALESCE(description, '') FROM finance.vouchers WHERE id=%s", (voucher_id,))
            header = cur.fetchone()
            if not header:
                return messagebox.showinfo("بحث", "لم يتم العثور على القيد")

            self.current_voucher_id = int(header[0])
            self.voucher_id_var.set(str(header[0]))
            self.voucher_date_var.set(str(header[1]))
            self.voucher_type_var.set(header[2] or "Journal")
            self.txt_general_desc.delete("1.0", tk.END)
            self.txt_general_desc.insert("1.0", header[3] or "")

            self.journal_lines = self._fetch_journal_lines(cur, header[0])
            self.current_line_index = None
            self._clear_line_editor()
            self._render_lines()
            self._set_header_button_states()
        except Exception as e:
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _exit_screen(self):
        try:
            self.frame.destroy()
        except Exception:
            self.master.destroy()

    def _amount_to_words(self, value):
        number = int(abs(float(value or 0)))
        if number == 0:
            return "فقط صفر"
        words = self._int_to_arabic_words(number)
        return f"فقط {words}"

    def _int_to_arabic_words(self, n):
        units = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"]
        teens = ["عشرة", "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر", "ستة عشر", "سبعة عشر", "ثمانية عشر", "تسعة عشر"]
        tens = ["", "", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"]
        hundreds = ["", "مئة", "مئتان", "ثلاثمئة", "أربعمئة", "خمسمئة", "ستمئة", "سبعمئة", "ثمانمئة", "تسعمئة"]

        def under_1000(x):
            parts = []
            h = x // 100
            r = x % 100
            if h:
                parts.append(hundreds[h])
            if 10 <= r <= 19:
                parts.append(teens[r - 10])
            else:
                t = r // 10
                u = r % 10
                if u:
                    parts.append(units[u])
                if t:
                    parts.append(tens[t])
            return " و ".join(parts)

        chunks = []
        millions = n // 1000000
        thousands = (n % 1000000) // 1000
        rest = n % 1000

        if millions:
            chunks.append(f"{under_1000(millions)} مليون")
        if thousands:
            chunks.append(f"{under_1000(thousands)} ألف")
        if rest:
            chunks.append(under_1000(rest))
        return " و ".join([c for c in chunks if c])


if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    root.title("Manual Journal Screen")
    root.geometry("1350x900")
    app = ManualJournalScreen(root)
    root.mainloop()

