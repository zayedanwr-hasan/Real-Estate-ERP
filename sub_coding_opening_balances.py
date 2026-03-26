# subcoding_opening_balances.py
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import ttkbootstrap as tb
from db_connection import get_connection, get_db_error_message
from combobox_helper import bind_searchable_combobox, set_combobox_values

class SubCodingOpeningBalances:
    def __init__(self, master):
        self.master = master

        # Enforced by finance.vouchers CHECK constraint.
        self.allowed_opening_v_type = "رصيد افتتاحى"
        self._balance_preview_guard = False

        # Palette
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.bg_color = "#f4f7f6"

        # Action button colors (required per spec)
        self.color_new = "#3498db"
        self.color_save = "#27ae60"
        self.color_edit = "#f1c40f"
        self.color_delete = "#e74c3c"
        self.color_search = "#8e44ad"
        self.color_exit = "#e67e22"

        # Fonts aligned with voucher screens
        self.base_font = ("Segoe UI", 11)
        self.bold_font = ("Segoe UI", 11, "bold")
        self.title_font = ("Segoe UI", 20, "bold")

        # state
        self.selected_plot_id = None
        self.selected_vendor_id = None
        self.plot_rows_cache = []
        self.vendor_rows_cache = []
        self.plot_map = {}
        self.vendor_map = {}

        # Fixed opening account options for vendor balances (aligned with current chart of accounts).
        self.vendor_account_options = [
            ("21", "دائنون-ملاك أراضي"),
            ("2101", "الورثة"),
            ("2102", "المجموعات"),
        ]
        self.vendor_account_code_to_name = {code: name for code, name in self.vendor_account_options}
        self.vendor_account_name_to_code = {name: code for code, name in self.vendor_account_options}
        self.default_vendor_account_code = "2101"

        # Group field options loaded from chart of accounts (2102 and its children).
        self.vendor_group_options = []
        self.vendor_group_display_to_name = {}
        self.vendor_group_name_to_display = {}

        # vars
        self.summary_amount_var = tk.StringVar(value="0.00")
        self.summary_words_var = tk.StringVar(value="فقط صفر")

        # style + layout
        self._setup_styles()
        self._build_layout()
        # initial data load
        self._refresh_all_data()

    def _setup_styles(self):
        self.style = tb.Style(theme="flatly")  # base theme but we customize heavily

        # Root frames and cards
        self.style.configure("App.Root.TFrame", background=self.bg_color)
        self.style.configure("App.Header.TFrame", background=self.primary_color)
        self.style.configure("App.HeaderTitle.TLabel", background=self.primary_color, foreground="white", font=self.title_font, anchor="e")

        self.style.configure("App.Card.TFrame", background="white", relief="solid", borderwidth=1, bordercolor="#d1d8e0")
        self.style.configure("App.CardTitle.TLabel", background="white", foreground=self.primary_color, font=("Segoe UI", 13, "bold"), anchor="e")
        self.style.configure("App.FormLabel.TLabel", background="white", foreground=self.primary_color, font=("Segoe UI", 12, "bold"), anchor="e", justify="right")
        self.style.configure("App.Field.TEntry", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 11))
        self.style.configure("App.Field.TCombobox", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 11))

        # Summary box
        self.style.configure("App.Summary.TFrame", background=self.bg_color, relief="flat")
        self.style.configure("App.SummaryTitle.TLabel", background=self.bg_color, foreground=self.primary_color, font=("Segoe UI", 12, "bold"))
        self.style.configure("App.SummaryAmount.TLabel", background=self.bg_color, foreground=self.color_delete, font=("Segoe UI", 24, "bold"))
        self.style.configure("App.SummaryWords.TLabel", background=self.bg_color, foreground=self.sidebar_color, font=("Segoe UI", 14, "bold"))

        # Buttons styles aligned with voucher screens.
        self.style.configure("App.SubCoding.Primary.TButton", background=self.color_new, foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        self.style.configure("App.SubCoding.Success.TButton", background=self.color_save, foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        self.style.configure("App.SubCoding.Warning.TButton", background=self.color_edit, foreground="#2c3e50", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        self.style.configure("App.SubCoding.Danger.TButton", background=self.color_delete, foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        self.style.configure("App.SubCoding.Info.TButton", background=self.color_search, foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        self.style.configure("App.SubCoding.Exit.TButton", background=self.color_exit, foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))

        for button_style in (
            "App.SubCoding.Primary.TButton",
            "App.SubCoding.Success.TButton",
            "App.SubCoding.Warning.TButton",
            "App.SubCoding.Danger.TButton",
            "App.SubCoding.Info.TButton",
            "App.SubCoding.Exit.TButton",
        ):
            self.style.map(
                button_style,
                background=[("active", self.accent_color), ("pressed", self.accent_color)],
                foreground=[("active", "white"), ("pressed", "white")],
            )

        # Notebook aligned to the same modern ERP styling language.
        self.style.configure("App.SubCoding.TNotebook", background=self.bg_color, borderwidth=0)
        self.style.configure("App.SubCoding.TNotebook.Tab", font=("Segoe UI", 11, "bold"), padding=(14, 8), background=self.sidebar_color, foreground=self.text_color)
        self.style.map(
            "App.SubCoding.TNotebook.Tab",
            background=[("selected", self.accent_color), ("active", self.accent_color)],
            foreground=[("selected", "white"), ("active", "white")],
        )

        # Treeview (table) style
        self.style.configure("App.Treeview", rowheight=30, font=self.base_font, background="white", fieldbackground="white", foreground=self.primary_color)
        self.style.configure("App.Treeview.Heading", font=("Segoe UI", 11, "bold"), background=self.primary_color, foreground="white")
        # selection color (single place)
        self.style.map("App.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "white")])
        self.style.configure("App.Vertical.TScrollbar", troughcolor=self.bg_color, bordercolor=self.sidebar_color, arrowcolor=self.primary_color)

    def _build_layout(self):
        # Support both standalone windows and embedded Frame hosts.
        host_window = self.master.winfo_toplevel() if hasattr(self.master, "winfo_toplevel") else None
        if host_window and host_window is self.master and hasattr(host_window, "title"):
            host_window.title("SubCoding - Opening Balances")

        if isinstance(self.master, (tk.Tk, tk.Toplevel)):
            self.master.configure(bg=self.bg_color)
        elif host_window and host_window is not self.master:
            try:
                host_window.configure(bg=self.bg_color)
            except tk.TclError:
                pass

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        root = ttk.Frame(self.master, style="App.Root.TFrame", padding=12)
        root.grid(sticky="nsew")
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # header
        header = ttk.Frame(root, style="App.Header.TFrame", padding=(12,10))
        header.grid(row=0, column=0, sticky="ew", pady=(0,12))
        header.grid_columnconfigure(1, weight=1)

        actions = ttk.Frame(header, style="App.Header.TFrame")
        actions.grid(row=0, column=0, sticky="w")

        ttk.Button(actions, text="جديد", style="App.SubCoding.Primary.TButton", command=self._action_new).grid(row=0, column=0, padx=(0,8))
        ttk.Button(actions, text="حفظ", style="App.SubCoding.Success.TButton", command=self._action_save).grid(row=0, column=1, padx=8)
        ttk.Button(actions, text="تعديل", style="App.SubCoding.Warning.TButton", command=self._action_edit).grid(row=0, column=2, padx=8)
        ttk.Button(actions, text="حذف", style="App.SubCoding.Danger.TButton", command=self._action_delete).grid(row=0, column=3, padx=8)
        ttk.Button(actions, text="بحث", style="App.SubCoding.Info.TButton", command=self._action_search).grid(row=0, column=4, padx=8)
        ttk.Button(actions, text="خروج", style="App.SubCoding.Exit.TButton", command=self._action_exit).grid(row=0, column=5, padx=(8,0))

        ttk.Label(header, text="شاشة تعريف العقارات والورثة", style="App.HeaderTitle.TLabel").grid(row=0, column=1, sticky="e")

        # Notebook
        notebook_wrapper = ttk.Frame(root, style="App.Root.TFrame", padding=(0, 6, 0, 0))
        notebook_wrapper.grid(row=1, column=0, sticky="nsew")
        notebook_wrapper.grid_rowconfigure(0, weight=1)
        notebook_wrapper.grid_columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(notebook_wrapper, style="App.SubCoding.TNotebook")
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        # tabs
        self.plot_tab = ttk.Frame(self.notebook, style="App.Root.TFrame", padding=12)
        self.vendor_tab = ttk.Frame(self.notebook, style="App.Root.TFrame", padding=12)
        self.plot_tab.grid_rowconfigure(0, weight=1)
        self.plot_tab.grid_columnconfigure(0, weight=1)
        self.vendor_tab.grid_rowconfigure(0, weight=1)
        self.vendor_tab.grid_columnconfigure(0, weight=1)

        self.notebook.add(self.plot_tab, text="تعريف العقارات")
        self.notebook.add(self.vendor_tab, text="الورثة والأرصدة الافتتاحية")

        # build tab interfaces
        self._build_plot_interface()
        self._build_vendor_interface()

    # ---------------------------
    # Plot (properties) UI
    # ---------------------------
    def _build_plot_interface(self):
        container = ttk.Frame(self.plot_tab, style="App.Root.TFrame")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=2)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # table card
        table_card = ttk.Frame(container, style="App.Card.TFrame", padding=12)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        table_card.grid_rowconfigure(1, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        ttk.Label(table_card, text="العقارات المسجلة", style="App.CardTitle.TLabel").grid(row=0, column=0, sticky="e", pady=(0,8))
        cols = ("id", "name", "cost", "area", "loc")
        heads = ["كود", "اسم العقار", "التكلفة", "المساحة", "الموقع"]
        self.plot_tree = self._create_tree(table_card, 1, 0, cols, heads)
        self.plot_tree.bind("<<TreeviewSelect>>", self._on_plot_select)

        # form card
        form_card = ttk.Frame(container, style="App.Card.TFrame", padding=12)
        form_card.grid(row=0, column=1, sticky="nsew", padx=(8,0))
        form_card.grid_columnconfigure(0, weight=1)

        ttk.Label(form_card, text="بيانات العقار", style="App.CardTitle.TLabel").grid(row=0, column=0, sticky="e", pady=(0,8))

        self.p_name = self._create_label_entry(form_card, "اسم العقار:", 1)
        self.p_cost = self._create_label_entry(form_card, "التكلفة:", 3)
        self.p_cost.bind("<FocusOut>", lambda _e: self._format_money_entry(self.p_cost))
        self.p_area = self._create_label_entry(form_card, "المساحة:", 5)
        self.p_loc = self._create_label_entry(form_card, "الموقع:", 7)

        ttk.Button(form_card, text="حفظ العقار", style="App.SubCoding.Success.TButton", command=self._save_plot).grid(
            row=9, column=0, sticky="ew", pady=(12, 0)
        )

    # ---------------------------
    # Vendor UI
    # ---------------------------
    def _build_vendor_interface(self):
        container = ttk.Frame(self.vendor_tab, style="App.Root.TFrame")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=2)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        table_card = ttk.Frame(container, style="App.Card.TFrame", padding=12)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        table_card.grid_rowconfigure(1, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        ttk.Label(table_card, text="الورثة والأرصدة", style="App.CardTitle.TLabel").grid(row=0, column=0, sticky="e", pady=(0,8))
        cols = ("id", "name", "group", "property", "bal")
        heads = ["كود", "الاسم", "المجموعة", "العقار المرتبط", "الرصيد"]
        self.vendor_tree = self._create_tree(table_card, 1, 0, cols, heads)
        self.vendor_tree.bind("<<TreeviewSelect>>", self._on_vendor_select)

        form_card = ttk.Frame(container, style="App.Card.TFrame", padding=12)
        form_card.grid(row=0, column=1, sticky="nsew", padx=(8,0))
        form_card.grid_columnconfigure(0, weight=1)

        ttk.Label(form_card, text="بيانات الوارث", style="App.CardTitle.TLabel").grid(row=0, column=0, sticky="e", pady=(0,8))

        self.v_name = self._create_label_entry(form_card, "اسم الوارث:", 1)

        ttk.Label(form_card, text="المجموعة (اسم الأسرة/المجموعة):", style="App.FormLabel.TLabel").grid(row=3, column=0, sticky="e", pady=(8,2))
        # Keep chart-linked suggestions, but allow typing custom family group names.
        self.v_group_cb = ttk.Combobox(form_card, style="App.Field.TCombobox", state="normal", justify="right", font=("Segoe UI", 12, "bold"))
        self.v_group_cb.grid(row=4, column=0, sticky="ew", pady=(0,8))
        bind_searchable_combobox(self.v_group_cb)

        ttk.Label(form_card, text="الحساب:", style="App.FormLabel.TLabel").grid(row=5, column=0, sticky="e", pady=(8,2))
        self.v_account_cb = ttk.Combobox(form_card, style="App.Field.TCombobox", state="readonly", justify="right", font=("Segoe UI", 12, "bold"))
        self.v_account_cb.grid(row=6, column=0, sticky="ew", pady=(0,8))
        set_combobox_values(self.v_account_cb, [name for _code, name in self.vendor_account_options])
        bind_searchable_combobox(self.v_account_cb)
        self._set_vendor_account_selection(self.default_vendor_account_code)

        ttk.Label(form_card, text="اختر العقار (إلزامي):", style="App.FormLabel.TLabel").grid(row=7, column=0, sticky="e", pady=(8,2))
        self.v_plot_cb = ttk.Combobox(form_card, style="App.Field.TCombobox", state="readonly", justify="right", font=("Segoe UI", 12, "bold"))
        self.v_plot_cb.grid(row=8, column=0, sticky="ew", pady=(0,8))
        bind_searchable_combobox(self.v_plot_cb)

        self.v_balance = self._create_label_entry(form_card, "رصيد افتتاحي (مدين):", 10)
        self.v_balance.insert(0, "0.00")
        self.v_balance.bind("<KeyRelease>", lambda _e: self._update_balance_preview())
        self.v_balance.bind("<FocusOut>", lambda _e: self._update_balance_preview(force_format=True))

        # summary box
        self._build_summary_box(form_card, 12)

        ttk.Button(form_card, text="حفظ الوارث", style="App.SubCoding.Success.TButton", command=self._save_vendor).grid(
            row=14, column=0, sticky="ew", pady=(12, 0)
        )

    def _build_summary_box(self, parent, row):
        summary = ttk.Frame(parent, style="App.Summary.TFrame", padding=10)
        summary.grid(row=row, column=0, sticky="ew", pady=(8,0))
        summary.columnconfigure(0, weight=1)

        ttk.Label(summary, text="ملخص الرصيد", style="App.SummaryTitle.TLabel").grid(row=0, column=0, sticky="e")
        ttk.Label(summary, textvariable=self.summary_amount_var, style="App.SummaryAmount.TLabel").grid(row=1, column=0, sticky="e")
        ttk.Label(summary, textvariable=self.summary_words_var, style="App.SummaryWords.TLabel").grid(row=2, column=0, sticky="e")

    # helper to create label above entry (consistent padding)
    def _create_label_entry(self, parent, txt, row, entry_style="App.Field.TEntry"):
        ttk.Label(parent, text=txt, style="App.FormLabel.TLabel").grid(row=row, column=0, sticky="e", pady=(8,2))
        ent = ttk.Entry(parent, justify="right", font=self.base_font, style=entry_style)
        ent.grid(row=row+1, column=0, sticky="ew", pady=(0,6), ipady=6)
        return ent

    # tree builder
    def _create_tree(self, parent, row, column, cols, heads):
        frame = ttk.Frame(parent, style="App.Card.TFrame")
        frame.grid(row=row, column=column, sticky="nsew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse", style="App.Treeview")
        widths = {
            "id": 80,
            "name": 240,
            "cost": 140,
            "area": 140,
            "loc": 160,
            "group": 140,
            "property": 190,
            "bal": 120,
        }

        for col_name, head in zip(cols, heads):
            tree.heading(col_name, text=head, anchor="center")
            tree.column(col_name, anchor="center", width=widths.get(col_name, 120), stretch=True)

        vsb = ttk.Scrollbar(frame, orient="vertical", style="App.Vertical.TScrollbar", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns", padx=(6,0))

        # row striping tags
        tree.tag_configure("odd", background="white")
        tree.tag_configure("even", background="#f0f3f5")
        tree.tag_configure("empty", foreground=self.sidebar_color)
        return tree

    # ---------------------------
    # Vendor account ComboBox helpers
    # ---------------------------
    def _set_vendor_account_selection(self, account_code):
        code = str(account_code or "").strip()
        account_name = self.vendor_account_code_to_name.get(
            code,
            self.vendor_account_code_to_name.get(self.default_vendor_account_code, ""),
        )
        if hasattr(self, "v_account_cb"):
            self.v_account_cb.set(account_name)

    def _get_selected_vendor_account_code(self):
        selected_name = self.v_account_cb.get().strip() if hasattr(self, "v_account_cb") else ""
        return self.vendor_account_name_to_code.get(selected_name, self.default_vendor_account_code)

    def _set_vendor_group_selection(self, group_text):
        if not hasattr(self, "v_group_cb"):
            return
        text = str(group_text or "").strip()
        if not text:
            self.v_group_cb.set("")
            return
        display = self.vendor_group_name_to_display.get(text, text)
        self.v_group_cb.set(display)

    def _get_selected_vendor_group_name(self):
        text = self.v_group_cb.get().strip() if hasattr(self, "v_group_cb") else ""
        return self.vendor_group_display_to_name.get(text, text)

    def _load_vendor_group_options(self, cur):
        chart_options = []
        try:
            # Prefer explicit group branch (2102) from chart of accounts.
            cur.execute(
                """
                SELECT account_code, account_name
                FROM finance.accounts
                WHERE account_code = '2102' OR parent_code = '2102'
                ORDER BY account_code
                """
            )
            rows = cur.fetchall() or []
            chart_options = [f"{str(code).strip()} - {name}" for code, name in rows if code and name]
        except Exception:
            # Fallback: keep going with saved vendor group names only.
            chart_options = []

        existing_group_names = []
        try:
            # Also keep previously saved family/group names as quick suggestions.
            cur.execute(
                """
                SELECT DISTINCT COALESCE(group_name, '')
                FROM finance.vendors
                WHERE COALESCE(group_name, '') <> ''
                ORDER BY group_name
                """
            )
            existing_group_names = [str(r[0]).strip() for r in (cur.fetchall() or []) if r and str(r[0]).strip()]
        except Exception:
            existing_group_names = []

        options = []
        seen = set()
        for item in chart_options + existing_group_names:
            if item and item not in seen:
                seen.add(item)
                options.append(item)

        self.vendor_group_options = options
        self.vendor_group_display_to_name = {}
        self.vendor_group_name_to_display = {}
        for display in options:
            # Chart option like "2102 - المجموعات" stores only account name.
            name = display.split(" - ", 1)[1].strip() if " - " in display else display
            self.vendor_group_display_to_name[display] = name
            if name not in self.vendor_group_name_to_display:
                self.vendor_group_name_to_display[name] = display

        if hasattr(self, "v_group_cb"):
            set_combobox_values(self.v_group_cb, self.vendor_group_options)
            if self.v_group_cb.get() not in self.v_group_cb["values"]:
                # Keep typed value if user entered custom group name.
                current = self.v_group_cb.get().strip()
                self.v_group_cb.set(current)

    def _resolve_opening_credit_account_code(self, cur):
        preferred_codes = ["3999", "3103", "3101", "3102"]
        cur.execute(
            "SELECT account_code FROM finance.accounts WHERE account_code = ANY(%s)",
            (preferred_codes,),
        )
        existing = {str(r[0]).strip() for r in (cur.fetchall() or []) if r and r[0] is not None}
        for code in preferred_codes:
            if code in existing:
                return code
        raise Exception("تعذر تحديد حساب دائن موازن للرصيد الافتتاحي. أضف أحد الأكواد: 3999 أو 3103 أو 3101 أو 3102 في دليل الحسابات.")

    # ---------------------------
    # Data population & reload
    # ---------------------------
    def _show_empty_state(self, tree, columns_count, text="No Data Available"):
        tree.delete(*tree.get_children())
        empty_values = [text] + ["" for _ in range(columns_count - 1)]
        tree.insert("", "end", iid="__empty__", values=tuple(empty_values), tags=("empty",))
        # make sure selection cleared
        try:
            tree.selection_remove(tree.selection())
        except Exception:
            pass

    def _fill_tree(self, tree, rows, columns_count):
        tree.delete(*tree.get_children())
        if not rows:
            self._show_empty_state(tree, columns_count)
            return
        for index, row in enumerate(rows):
            tag = "even" if index % 2 == 0 else "odd"
            vals = tuple("" if v is None else v for v in row)
            tree.insert("", "end", iid=str(row[0]), values=vals, tags=(tag,))

    # ---------------------------
    # Numeric / voucher validators
    # ---------------------------
    def _normalize_number_text(self, text):
        if text is None:
            return ""
        normalized = str(text).strip()
        if not normalized:
            return ""

        # Support Arabic-Indic digits and Arabic separators.
        trans = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        normalized = normalized.translate(trans)
        normalized = normalized.replace("\u066c", ",").replace("\u066b", ".")
        normalized = normalized.replace(" ", "").replace(",", "")
        return normalized

    def _try_parse_amount(self, text):
        normalized = self._normalize_number_text(text)
        if normalized == "":
            return None
        try:
            return float(normalized)
        except Exception:
            return None

    def _format_amount(self, value):
        try:
            return f"{float(value):,.2f}"
        except Exception:
            return "0.00"

    def _format_money_entry(self, entry_widget):
        raw = entry_widget.get().strip()
        parsed = self._try_parse_amount(raw)
        if parsed is None:
            return
        entry_widget.delete(0, "end")
        entry_widget.insert(0, self._format_amount(parsed))

    def _parse_required_amount(self, text, field_label):
        parsed = self._try_parse_amount(text)
        if parsed is None:
            messagebox.showerror("خطأ", f"{field_label} يجب أن يكون رقمًا صحيحًا")
            return None
        return parsed

    def _validate_opening_v_type(self, v_type):
        # Guard against CHECK constraint failures on finance.vouchers.v_type.
        if v_type != self.allowed_opening_v_type:
            messagebox.showerror(
                "خطأ",
                "قيمة نوع القيد غير مسموحة. يجب أن تكون 'رصيد افتتاحى' فقط لتفادي خطأ CHECK constraint.",
            )
            return False
        return True

    def _refresh_all_data(self):
        conn = get_connection()
        if not conn:
            messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
            return
        try:
            cur = conn.cursor()
            # properties
            cur.execute(
                """
                SELECT id,
                       property_name,
                       COALESCE(total_cost, 0) AS total_cost,
                       COALESCE(purchase_price, 0) AS area_value,
                       COALESCE(location, '') AS location
                FROM finance.properties
                ORDER BY id DESC
                """
            )
            self.plot_rows_cache = cur.fetchall()
            self.plot_map = {int(r[0]): r for r in self.plot_rows_cache}
            plot_display_rows = [
                (
                    r[0],
                    r[1],
                    self._format_amount(r[2] if r[2] is not None else 0),
                    r[3] if r[3] is not None else "",
                    r[4],
                )
                for r in self.plot_rows_cache
            ]
            self._fill_tree(self.plot_tree, plot_display_rows, 5)

            # fill property combobox
            set_combobox_values(self.v_plot_cb, [f"{r[0]} - {r[1]}" for r in self.plot_rows_cache])
            if self.v_plot_cb.get() not in self.v_plot_cb["values"]:
                self.v_plot_cb.set("")

            # load vendor group choices from chart of accounts (do not block data refresh on failure)
            try:
                self._load_vendor_group_options(cur)
            except Exception:
                # Keep vendor data loading even if group suggestions cannot be built.
                if hasattr(self, "v_group_cb"):
                    set_combobox_values(self.v_group_cb, [])

            # vendors + balances (property comes from vendors.property_id, not ledger)
            cur.execute(
                """
                SELECT v.id,
                       v.vendor_name,
                       COALESCE(v.group_name, '') AS group_name,
                       COALESCE(p.property_name, '-') AS property_name,
                       COALESCE((
                           SELECT SUM(COALESCE(l.debit, 0) - COALESCE(l.credit, 0))
                           FROM finance.ledger l
                           WHERE l.vendor_id = v.id
                       ), 0) AS balance,
                       v.property_id,
                       (
                           SELECT l2.account_code
                           FROM finance.ledger l2
                           JOIN finance.vouchers v2 ON v2.id = l2.voucher_id
                           WHERE l2.vendor_id = v.id
                             AND v2.v_type = %s
                             AND COALESCE(l2.debit, 0) > 0
                           ORDER BY l2.id DESC
                           LIMIT 1
                       ) AS opening_account_code
                FROM finance.vendors v
                LEFT JOIN finance.properties p ON p.id = v.property_id
                ORDER BY v.vendor_name
                """,
                (self.allowed_opening_v_type,),
            )
            vendor_rows_raw = cur.fetchall()
            # vendor_rows_cache arranged to match columns shown earlier
            self.vendor_rows_cache = [(r[0], r[1], r[2], r[3], r[4]) for r in vendor_rows_raw]
            # vendor_map holds details used when selecting
            self.vendor_map = {
                int(r[0]): {
                    "id": int(r[0]),
                    "name": r[1],
                    "group": r[2],
                    "property_name": r[3],
                    "balance": r[4],
                    "property_id": r[5],
                    "opening_account_code": r[6] or self.default_vendor_account_code,
                }
                for r in vendor_rows_raw
            }
            vendor_display_rows = [
                (r[0], r[1], r[2], r[3], self._format_amount(r[4] if r[4] is not None else 0))
                for r in self.vendor_rows_cache
            ]
            self._fill_tree(self.vendor_tree, vendor_display_rows, 5)
        except Exception as e:
            messagebox.showerror("خطأ", get_db_error_message(e, "تعذر تحميل البيانات"))
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # ---------------------------
    # CRUD: Save / Edit / Delete
    # ---------------------------
    def _save_plot(self):
        name = self.p_name.get().strip()
        cost = self.p_cost.get().strip()
        area = self.p_area.get().strip()
        loc = self.p_loc.get().strip()

        if not name:
            return messagebox.showwarning("تنبيه", "أدخل اسم العقار")

        cost_val = None
        if cost:
            cost_val = self._parse_required_amount(cost, "التكلفة")
            if cost_val is None:
                return

        # المساحة الآن حقل نصي حر (مثل: متر/لبنة/ك) لذا لا نطبّق عليه تحويل رقمي.
        area_val = area if area else None
        conn = get_connection()
        if not conn:
            return messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO finance.properties (property_name, total_cost, purchase_price, location) VALUES (%s, %s, %s, %s)",
                (name, cost_val, area_val, loc),
            )
            conn.commit()
            messagebox.showinfo("نجاح", "تم حفظ العقار")
            self._clear_plot_form()
            self._refresh_all_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", get_db_error_message(e, "فشل حفظ بيانات العقار"))
        finally:
            conn.close()

    def _get_required_property_id(self):
        plot_info = self.v_plot_cb.get().strip()
        if not plot_info:
            messagebox.showwarning("تنبيه", "يجب اختيار العقار قبل الحفظ")
            return None
        try:
            return int(plot_info.split(" - ")[0])
        except Exception:
            messagebox.showwarning("تنبيه", "قيمة العقار غير صحيحة، اختر عقارًا من القائمة")
            return None

    def _save_vendor(self):
        name = self.v_name.get().strip()
        group = self._get_selected_vendor_group_name()
        bal = self._parse_required_amount(self.v_balance.get().strip() or "0", "الرصيد الافتتاحي")
        if bal is None:
            return

        if not self._validate_opening_v_type(self.allowed_opening_v_type):
            return

        if not name:
            return messagebox.showwarning("تنبيه", "أكمل بيانات الوارث (الاسم)")

        property_id = self._get_required_property_id()
        if property_id is None:
            return

        conn = get_connection()
        if not conn:
            return messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
        cur = conn.cursor()
        try:
            selected_account_code = self._get_selected_vendor_account_code()
            credit_account_code = self._resolve_opening_credit_account_code(cur)
            cur.execute(
                "INSERT INTO finance.vendors (vendor_name, group_name, property_id) VALUES (%s, %s, %s) RETURNING id",
                (name, group, property_id),
            )
            v_id = cur.fetchone()[0]

            if bal > 0:
                # Validate fixed opening voucher type before INSERT to avoid CHECK constraint violations.
                if not self._validate_opening_v_type(self.allowed_opening_v_type):
                    conn.rollback()
                    return

                cur.execute(
                    "INSERT INTO finance.vouchers (v_type, v_date, description) VALUES (%s, CURRENT_DATE, %s) RETURNING id",
                    (self.allowed_opening_v_type, f"رصيد أول المدة: {name}"),
                )
                voc_id = cur.fetchone()[0]

                # debit to vendor (selected account)
                cur.execute(
                    "INSERT INTO finance.ledger (voucher_id, account_code, vendor_id, property_id, debit) VALUES (%s, %s, %s, %s, %s)",
                    (voc_id, selected_account_code, v_id, property_id, bal),
                )
                # balancing credit (account 3999). keep vendor_id NULL for general ledger credit line (depends on your schema)
                cur.execute(
                    "INSERT INTO finance.ledger (voucher_id, account_code, credit) VALUES (%s, %s, %s)",
                    (voc_id, credit_account_code, bal),
                )

            conn.commit()
            messagebox.showinfo("نجاح", "تم الحفظ")
            self._clear_vendor_form()
            self._refresh_all_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", get_db_error_message(e, "فشل حفظ بيانات الوارث"))
        finally:
            conn.close()

    # ---------------------------
    # Actions - wrappers
    # ---------------------------
    def _action_new(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._clear_plot_form()
        else:
            self._clear_vendor_form()

    def _action_save(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._save_plot()
        else:
            self._save_vendor()

    def _action_edit(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._edit_plot()
        else:
            self._edit_vendor()

    def _action_delete(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._delete_plot()
        else:
            self._delete_vendor()

    def _action_search(self):
        query = simpledialog.askstring("بحث", "أدخل كلمة البحث:", parent=self.master)
        if query is None:
            return
        query = query.strip().lower()
        active_tab = self.notebook.index(self.notebook.select())

        if not query:
            self._refresh_all_data()
            return

        if active_tab == 0:
            filtered = [r for r in self.plot_rows_cache if query in str(r[1]).lower() or query in str(r[4] or "").lower()]
            filtered_display = [
                (
                    r[0],
                    r[1],
                    self._format_amount(r[2] if r[2] is not None else 0),
                    r[3] if r[3] is not None else "",
                    r[4],
                )
                for r in filtered
            ]
            self._fill_tree(self.plot_tree, filtered_display, 5)
        else:
            filtered = [r for r in self.vendor_rows_cache if query in str(r[1]).lower() or query in str(r[2] or "").lower() or query in str(r[3] or "").lower()]
            filtered_display = [
                (r[0], r[1], r[2], r[3], self._format_amount(r[4] if r[4] is not None else 0))
                for r in filtered
            ]
            self._fill_tree(self.vendor_tree, filtered_display, 5)

    def _action_exit(self):
        if messagebox.askyesno("تأكيد", "هل تريد إغلاق هذه الشاشة؟"):
            self.master.destroy()

    # ---------------------------
    # Clear forms & selection logic
    # ---------------------------
    def _clear_plot_form(self):
        self.selected_plot_id = None
        self.p_name.delete(0, "end")
        self.p_cost.delete(0, "end")
        self.p_area.delete(0, "end")
        self.p_loc.delete(0, "end")
        try:
            self.plot_tree.selection_remove(self.plot_tree.selection())
        except Exception:
            pass

    def _clear_vendor_form(self):
        self.selected_vendor_id = None
        self.v_name.delete(0, "end")
        if hasattr(self, "v_group_cb"):
            self.v_group_cb.set("")
        self.v_balance.delete(0, "end")
        self.v_balance.insert(0, "0.00")
        self.v_plot_cb.set("")
        self._set_vendor_account_selection(self.default_vendor_account_code)
        self._update_balance_preview()
        try:
            self.vendor_tree.selection_remove(self.vendor_tree.selection())
        except Exception:
            pass

    def _on_plot_select(self, _event=None):
        selected = self.plot_tree.selection()
        if not selected:
            return
        iid = selected[0]
        if iid == "__empty__":
            return
        self.selected_plot_id = int(iid)
        row = self.plot_map.get(self.selected_plot_id)
        if not row:
            return
        # populate
        self.p_name.delete(0, "end"); self.p_name.insert(0, row[1] or "")
        self.p_cost.delete(0, "end"); self.p_cost.insert(0, self._format_amount(row[2] if row[2] is not None else 0))
        self.p_area.delete(0, "end"); self.p_area.insert(0, row[3] if row[3] is not None else "")
        self.p_loc.delete(0, "end"); self.p_loc.insert(0, row[4] or "")

    def _on_vendor_select(self, _event=None):
        selected = self.vendor_tree.selection()
        if not selected:
            return
        iid = selected[0]
        if iid == "__empty__":
            return
        self.selected_vendor_id = int(iid)
        row = self.vendor_map.get(self.selected_vendor_id)
        if not row:
            return
        self.v_name.delete(0, "end"); self.v_name.insert(0, row["name"] or "")
        self._set_vendor_group_selection(row["group"] or "")
        self.v_balance.delete(0, "end"); self.v_balance.insert(0, self._format_amount(row["balance"] or 0))
        # set combobox by vendor.property_id (direct relation in new schema)
        prop_id = row.get("property_id")
        if prop_id:
            prop_match = [v for v in self.v_plot_cb["values"] if v.startswith(f"{prop_id} -")]
            self.v_plot_cb.set(prop_match[0] if prop_match else "")
        else:
            self.v_plot_cb.set("")
        self._set_vendor_account_selection(row.get("opening_account_code"))
        self._update_balance_preview()

    # ---------------------------
    # Edit / Delete implementations
    # ---------------------------
    def _edit_plot(self):
        if not self.selected_plot_id:
            return messagebox.showwarning("تنبيه", "اختر عقارًا من الجدول أولاً")

        name = self.p_name.get().strip()
        cost = self.p_cost.get().strip()
        area = self.p_area.get().strip()
        loc = self.p_loc.get().strip()

        if not name:
            return messagebox.showwarning("تنبيه", "أدخل اسم العقار")

        cost_val = None
        if cost:
            cost_val = self._parse_required_amount(cost, "التكلفة")
            if cost_val is None:
                return

        # المساحة حقل نصي حر.
        area_val = area if area else None
        conn = get_connection()
        if not conn:
            return messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE finance.properties SET property_name=%s, total_cost=%s, purchase_price=%s, location=%s WHERE id=%s",
                (name, cost_val, area_val, loc, self.selected_plot_id),
            )
            conn.commit()
            messagebox.showinfo("نجاح", "تم تعديل بيانات العقار")
            self._clear_plot_form()
            self._refresh_all_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", get_db_error_message(e, "فشل حفظ بيانات العقار"))
        finally:
            conn.close()

    def _edit_vendor(self):
        if not self.selected_vendor_id:
            return messagebox.showwarning("تنبيه", "اختر وارثًا من الجدول أولاً")

        name = self.v_name.get().strip()
        group = self._get_selected_vendor_group_name()
        bal = self._parse_required_amount(self.v_balance.get().strip() or "0", "الرصيد الافتتاحي")
        if bal is None:
            return

        if not self._validate_opening_v_type(self.allowed_opening_v_type):
            return

        if not name:
            return messagebox.showwarning("تنبيه", "أكمل بيانات الوارث (الاسم)")

        property_id = self._get_required_property_id()
        if property_id is None:
            return

        conn = get_connection()
        if not conn:
            return messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
        cur = conn.cursor()
        try:
            selected_account_code = self._get_selected_vendor_account_code()
            credit_account_code = self._resolve_opening_credit_account_code(cur)
            cur.execute(
                "UPDATE finance.vendors SET vendor_name=%s, group_name=%s, property_id=%s WHERE id=%s",
                (name, group, property_id, self.selected_vendor_id),
            )

            # Upsert opening voucher lines: update if exists, otherwise create when bal > 0.
            cur.execute(
                """
                SELECT l.voucher_id
                FROM finance.ledger l
                JOIN finance.vouchers v ON v.id = l.voucher_id
                WHERE l.vendor_id = %s
                  AND v.v_type = %s
                ORDER BY l.id
                LIMIT 1
                """,
                (self.selected_vendor_id, self.allowed_opening_v_type),
            )
            opening_voucher = cur.fetchone()

            if opening_voucher:
                voucher_id = opening_voucher[0]

                if not self._validate_opening_v_type(self.allowed_opening_v_type):
                    conn.rollback()
                    return

                cur.execute(
                    "UPDATE finance.ledger SET account_code=%s, property_id=%s, debit=%s WHERE voucher_id=%s AND vendor_id=%s AND COALESCE(debit, 0) > 0",
                    (selected_account_code, property_id, bal, voucher_id, self.selected_vendor_id),
                )
                if cur.rowcount == 0:
                    raise Exception("تعذر تحديث قيد الرصيد الافتتاحي (سطر المدين غير موجود).")

                cur.execute(
                    "UPDATE finance.ledger SET account_code=%s, credit=%s WHERE voucher_id=%s AND COALESCE(credit, 0) > 0",
                    (credit_account_code, bal, voucher_id),
                )
                if cur.rowcount == 0:
                    raise Exception("تعذر تحديث قيد الرصيد الافتتاحي (سطر الدائن غير موجود).")
            elif bal > 0:
                if not self._validate_opening_v_type(self.allowed_opening_v_type):
                    conn.rollback()
                    return

                cur.execute(
                    "INSERT INTO finance.vouchers (v_type, v_date, description) VALUES (%s, CURRENT_DATE, %s) RETURNING id",
                    (self.allowed_opening_v_type, f"رصيد أول المدة: {name}"),
                )
                voucher_id = cur.fetchone()[0]

                cur.execute(
                    "INSERT INTO finance.ledger (voucher_id, account_code, vendor_id, property_id, debit) VALUES (%s, %s, %s, %s, %s)",
                    (voucher_id, selected_account_code, self.selected_vendor_id, property_id, bal),
                )
                cur.execute(
                    "INSERT INTO finance.ledger (voucher_id, account_code, credit) VALUES (%s, %s, %s)",
                    (voucher_id, credit_account_code, bal),
                )

            conn.commit()
            messagebox.showinfo("نجاح", "تم تعديل بيانات الوارث")
            self._clear_vendor_form()
            self._refresh_all_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", get_db_error_message(e, "فشل تعديل بيانات الوارث"))
        finally:
            conn.close()

    def _delete_plot(self):
        if not self.selected_plot_id:
            return messagebox.showwarning("تنبيه", "اختر عقارًا من الجدول أولاً")
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا العقار؟"):
            return
        conn = get_connection()
        if not conn:
            return messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM finance.ledger WHERE property_id=%s", (self.selected_plot_id,))
            linked = cur.fetchone()[0]
            if linked > 0:
                return messagebox.showwarning("تنبيه", "لا يمكن حذف العقار لوجود قيود محاسبية مرتبطة به")
            cur.execute("DELETE FROM finance.properties WHERE id=%s", (self.selected_plot_id,))
            conn.commit()
            messagebox.showinfo("نجاح", "تم حذف العقار")
            self._clear_plot_form()
            self._refresh_all_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", get_db_error_message(e, "فشل حذف العقار"))
        finally:
            conn.close()

    def _delete_vendor(self):
        if not self.selected_vendor_id:
            return messagebox.showwarning("تنبيه", "اختر وارثًا من الجدول أولاً")
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا الوارث؟"):
            return
        conn = get_connection()
        if not conn:
            return messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM finance.ledger l
                LEFT JOIN finance.vouchers v ON v.id = l.voucher_id
                WHERE l.vendor_id = %s
                  AND COALESCE(v.v_type, '') <> %s
                """,
                (self.selected_vendor_id, self.allowed_opening_v_type),
            )
            has_non_opening_entries = cur.fetchone()[0]
            if has_non_opening_entries > 0:
                return messagebox.showwarning("تنبيه", "لا يمكن حذف الوارث لوجود قيود حركة مرتبطة به")

            cur.execute(
                """
                SELECT DISTINCT l.voucher_id
                FROM finance.ledger l
                JOIN finance.vouchers v ON v.id = l.voucher_id
                WHERE l.vendor_id = %s AND v.v_type = %s
                """,
                (self.selected_vendor_id, self.allowed_opening_v_type),
            )
            opening_vouchers = [r[0] for r in cur.fetchall() if r[0] is not None]

            if opening_vouchers:
                cur.execute("DELETE FROM finance.ledger WHERE voucher_id = ANY(%s)", (opening_vouchers,))
                cur.execute("DELETE FROM finance.vouchers WHERE id = ANY(%s)", (opening_vouchers,))

            cur.execute("DELETE FROM finance.vendors WHERE id=%s", (self.selected_vendor_id,))
            conn.commit()
            messagebox.showinfo("نجاح", "تم حذف الوارث")
            self._clear_vendor_form()
            self._refresh_all_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", get_db_error_message(e, "فشل حذف الوارث"))
        finally:
            conn.close()

    # ---------------------------
    # UX helpers
    # ---------------------------
    def _update_balance_preview(self, force_format=False):
        if self._balance_preview_guard:
            return

        raw_text = self.v_balance.get().strip()
        parsed = self._try_parse_amount(raw_text)

        if parsed is None:
            # Keep UX safe while typing; force 0.00 only when leaving the field.
            parsed = 0.0
            if force_format:
                self._balance_preview_guard = True
                self.v_balance.delete(0, "end")
                self.v_balance.insert(0, self._format_amount(parsed))
                self._balance_preview_guard = False
        elif force_format:
            # Do not reformat during typing; normalize only on focus-out.
            self._balance_preview_guard = True
            self.v_balance.delete(0, "end")
            self.v_balance.insert(0, self._format_amount(parsed))
            self._balance_preview_guard = False

        self.summary_amount_var.set(self._format_amount(parsed))
        self.summary_words_var.set(self._amount_to_words(parsed))

    def _amount_to_words(self, value):
        number = int(abs(value))
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

