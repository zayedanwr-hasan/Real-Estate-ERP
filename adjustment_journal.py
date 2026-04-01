import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog

import ttkbootstrap as ttk
from ttkbootstrap.constants import END

from app_constants import SYSTEM_NAME
from combobox_helper import bind_searchable_combobox, set_combobox_values
from db_connection import get_connection, get_db_error_message


class JournalVoucherScreen:
    FIXED_VOUCHER_TYPE = "JV"

    def __init__(self, master):
        self.master = master

        self.bg_color = "#1e272e"
        self.header_color = "#00d2d3"
        self.text_color = "#ffffff"
        self.panel_color = "#27343c"
        self.field_bg = "#f7f9fa"

        self.current_voucher_id = None
        self.selected_line_iid = None
        self.entry_lines = []
        self._schema_cache = {}

        self.account_display_to_code = {}
        self.account_code_to_name = {}
        self.account_code_to_display = {}

        self.vendor_display_to_id = {}
        self.vendor_id_to_display = {}

        self.voucher_id_var = tk.StringVar(value="Auto")
        self.reference_no_var = tk.StringVar(value="10001")
        self.voucher_type_var = tk.StringVar(value=self.FIXED_VOUCHER_TYPE)
        self.voucher_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.currency_var = tk.StringVar(value="YER")
        self.exchange_rate_var = tk.StringVar(value="1.00")
        self.general_desc_var = tk.StringVar()

        self.customer_chk_var = tk.BooleanVar(value=False)
        self.vendor_chk_var = tk.BooleanVar(value=False)
        self.customer_var = tk.StringVar()
        self.vendor_var = tk.StringVar()

        self.line_account_code_var = tk.StringVar()
        self.line_account_name_var = tk.StringVar()
        self.line_debit_var = tk.StringVar(value="0.00")
        self.line_credit_var = tk.StringVar(value="0.00")
        self.line_branch_var = tk.StringVar(value="Main")
        self.line_desc_var = tk.StringVar()

        self.total_debit_var = tk.StringVar(value="0.00")
        self.total_credit_var = tk.StringVar(value="0.00")
        self.balance_status_var = tk.StringVar(value="Not Balanced")

        self._setup_styles()
        self._build_layout()
        self._bind_events()
        self._load_master_data()
        self._reset_and_new(initial=True)

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("JV.Root.TFrame", background=self.bg_color)
        style.configure("JV.Card.TFrame", background=self.panel_color, borderwidth=1, relief="solid", bordercolor="#223039")
        style.configure("JV.Toolbar.TFrame", background=self.bg_color)
        style.configure("JV.HeaderBand.TFrame", background=self.header_color)
        style.configure("JV.HeaderBand.TLabel", background=self.header_color, foreground="#102027", font=("Segoe UI", 16, "bold"))

        style.configure("JV.Section.TLabelframe", background=self.panel_color, foreground=self.text_color)
        style.configure("JV.Section.TLabelframe.Label", background=self.panel_color, foreground=self.header_color, font=("Segoe UI", 10, "bold"))

        style.configure("JV.Label.TLabel", background=self.panel_color, foreground=self.text_color, font=("Segoe UI", 10, "bold"))
        style.configure("JV.Field.TEntry", fieldbackground=self.field_bg, foreground="#1b1b1b", font=("Segoe UI", 10, "bold"))
        style.configure("JV.Field.TCombobox", fieldbackground=self.field_bg, foreground="#1b1b1b", font=("Segoe UI", 10, "bold"))
        style.configure("JV.Check.TCheckbutton", background=self.panel_color, foreground=self.text_color, font=("Segoe UI", 10, "bold"))

        style.configure("JV.Toolbar.TButton", font=("Segoe UI", 10, "bold"), padding=(10, 8), borderwidth=0)
        style.map(
            "JV.Toolbar.TButton",
            background=[("!disabled", self.header_color), ("active", "#00b4b5"), ("pressed", "#00a5a6")],
            foreground=[("!disabled", "#102027"), ("active", "#0d1b1e")],
        )
        style.configure("JV.Line.TButton", font=("Segoe UI", 10, "bold"), padding=(8, 6), borderwidth=0)
        style.map(
            "JV.Line.TButton",
            background=[("!disabled", self.header_color), ("active", "#00b4b5")],
            foreground=[("!disabled", "#102027")],
        )

        style.configure("JV.Tree.TFrame", background=self.panel_color)
        style.configure("JV.Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#1b1b1b", rowheight=30, font=("Segoe UI", 10))
        style.configure("JV.Treeview.Heading", background=self.header_color, foreground="#102027", font=("Segoe UI", 10, "bold"))
        style.map("JV.Treeview", background=[("selected", "#87e6e7")], foreground=[("selected", "#0f1f24")])

        style.configure("JV.StatusGood.TLabel", background=self.panel_color, foreground="#2ecc71", font=("Segoe UI", 11, "bold"))
        style.configure("JV.StatusBad.TLabel", background=self.panel_color, foreground="#ff6b6b", font=("Segoe UI", 11, "bold"))

    def _build_layout(self):
        self.frame = ttk.Frame(self.master, style="JV.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.main_card = ttk.Frame(self.frame, style="JV.Card.TFrame", padding=8)
        self.main_card.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._build_top_toolbar()

        self.content = ttk.Frame(self.main_card, style="JV.Card.TFrame")
        self.content.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(3, weight=1)

        self._build_header_grid()
        self._build_general_description_row()
        self._build_line_editor_row()
        self._build_data_grid()
        self._build_footer_totals()

    def _build_top_toolbar(self):
        bar = ttk.Frame(self.main_card, style="JV.HeaderBand.TFrame")
        bar.pack(fill="x")

        title = ttk.Label(bar, text=f"Journal Voucher - {SYSTEM_NAME}", style="JV.HeaderBand.TLabel")
        title.pack(side="right", padx=12, pady=8)

        left = ttk.Frame(bar, style="JV.HeaderBand.TFrame")
        left.pack(side="left", padx=8, pady=4)

        actions = [
            ("NEW [+]", self._reset_and_new),
            ("SAVE [S]", self._save_voucher),
            ("UPDATE [U]", self._update_voucher),
            ("DELETE [D]", self._delete_voucher),
            ("SEARCH [?]", self._search_voucher),
            ("PRINT [P]", self._print_voucher),
        ]
        for txt, cmd in actions:
            ttk.Button(left, text=txt, style="JV.Toolbar.TButton", command=cmd, width=11).pack(side="left", padx=2)

    def _build_header_grid(self):
        header = ttk.Labelframe(self.content, text="Header", style="JV.Section.TLabelframe", padding=8)
        header.grid(row=0, column=0, sticky="nsew", padx=4, pady=(2, 4))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)

        assoc = ttk.Frame(header, style="JV.Card.TFrame")
        assoc.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        assoc.grid_columnconfigure(1, weight=1)

        meta = ttk.Frame(header, style="JV.Card.TFrame")
        meta.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        meta.grid_columnconfigure(1, weight=1)

        # Left column: association area like the sketch.
        ttk.Checkbutton(
            assoc,
            text="Customer Selection",
            variable=self.customer_chk_var,
            style="JV.Check.TCheckbutton",
            command=self._on_customer_toggle,
        ).grid(row=0, column=0, sticky="e", padx=(0, 6), pady=3)
        self.combo_customer = ttk.Combobox(assoc, textvariable=self.customer_var, style="JV.Field.TCombobox", state="disabled", justify="right")
        self.combo_customer.grid(row=0, column=1, sticky="ew", pady=3)
        bind_searchable_combobox(self.combo_customer)
        ttk.Button(assoc, text="Select", style="JV.Line.TButton", width=8, command=self._pick_customer).grid(row=0, column=2, padx=(6, 0), pady=3)

        ttk.Checkbutton(
            assoc,
            text="Vendor Selection",
            variable=self.vendor_chk_var,
            style="JV.Check.TCheckbutton",
            command=self._on_vendor_toggle,
        ).grid(row=1, column=0, sticky="e", padx=(0, 6), pady=3)
        self.combo_vendor = ttk.Combobox(assoc, textvariable=self.vendor_var, style="JV.Field.TCombobox", state="disabled", justify="right")
        self.combo_vendor.grid(row=1, column=1, sticky="ew", pady=3)
        bind_searchable_combobox(self.combo_vendor)
        ttk.Button(assoc, text="Select", style="JV.Line.TButton", width=8, command=self._pick_vendor).grid(row=1, column=2, padx=(6, 0), pady=3)

        # Right column: main header parameters.
        self._meta_field(meta, 0, "Voucher Type", self.voucher_type_var, readonly=True)
        self._meta_field(meta, 1, "Voucher ID", self.voucher_id_var, readonly=True)
        self._meta_date(meta, 2, "Date", self.voucher_date_var)
        self._meta_field(meta, 3, "Currency", self.currency_var)
        self._meta_field(meta, 4, "Exchange Rate", self.exchange_rate_var)
        self._meta_field(meta, 5, "Reference No", self.reference_no_var, readonly=True)

    def _build_general_description_row(self):
        row = ttk.Labelframe(self.content, text="البيان العام", style="JV.Section.TLabelframe", padding=8)
        row.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        row.grid_columnconfigure(0, weight=1)
        self.ent_general_desc = ttk.Entry(row, textvariable=self.general_desc_var, style="JV.Field.TEntry", justify="right")
        self.ent_general_desc.grid(row=0, column=0, sticky="ew")

    def _build_line_editor_row(self):
        row = ttk.Labelframe(self.content, text="Line Entry Editor", style="JV.Section.TLabelframe", padding=8)
        row.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
        for col in range(7):
            row.grid_columnconfigure(col, weight=1)

        labels = ["Account Code", "Account Name", "Debit", "Credit", "Branch", "Line Description", "Action"]
        for idx, txt in enumerate(labels):
            ttk.Label(row, text=txt, style="JV.Label.TLabel").grid(row=0, column=idx, sticky="ew", padx=2, pady=(0, 3))

        self.combo_line_account_code = ttk.Combobox(row, textvariable=self.line_account_code_var, style="JV.Field.TCombobox", justify="right", state="normal")
        self.combo_line_account_code.grid(row=1, column=0, sticky="ew", padx=2)
        bind_searchable_combobox(self.combo_line_account_code)

        self.ent_line_account_name = ttk.Entry(row, textvariable=self.line_account_name_var, style="JV.Field.TEntry", justify="right", state="readonly")
        self.ent_line_account_name.grid(row=1, column=1, sticky="ew", padx=2)

        self.ent_line_debit = ttk.Entry(row, textvariable=self.line_debit_var, style="JV.Field.TEntry", justify="right")
        self.ent_line_debit.grid(row=1, column=2, sticky="ew", padx=2)

        self.ent_line_credit = ttk.Entry(row, textvariable=self.line_credit_var, style="JV.Field.TEntry", justify="right")
        self.ent_line_credit.grid(row=1, column=3, sticky="ew", padx=2)

        self.combo_branch = ttk.Combobox(
            row,
            textvariable=self.line_branch_var,
            style="JV.Field.TCombobox",
            justify="right",
            values=("Main", "Branch A", "Branch B"),
            state="normal",
        )
        self.combo_branch.grid(row=1, column=4, sticky="ew", padx=2)

        self.ent_line_desc = ttk.Entry(row, textvariable=self.line_desc_var, style="JV.Field.TEntry", justify="right")
        self.ent_line_desc.grid(row=1, column=5, sticky="ew", padx=2)

        ttk.Button(row, text="Confirm Line", style="JV.Line.TButton", command=self._add_or_update_line).grid(row=1, column=6, sticky="ew", padx=2)

    def _build_data_grid(self):
        box = ttk.Frame(self.content, style="JV.Tree.TFrame")
        box.grid(row=3, column=0, sticky="nsew", padx=4, pady=4)
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(0, weight=1)

        cols = ("account_code", "account_name", "debit", "credit", "branch", "line_description")
        self.tree = ttk.Treeview(box, columns=cols, show="headings", style="JV.Treeview", selectmode="browse")

        self.tree.heading("account_code", text="Account Code", anchor="e")
        self.tree.heading("account_name", text="Account Name", anchor="e")
        self.tree.heading("debit", text="Debit", anchor="e")
        self.tree.heading("credit", text="Credit", anchor="e")
        self.tree.heading("branch", text="Branch", anchor="e")
        self.tree.heading("line_description", text="Line Description", anchor="e")

        self.tree.column("account_code", width=130, anchor="e", stretch=False)
        self.tree.column("account_name", width=220, anchor="e", stretch=True)
        self.tree.column("debit", width=120, anchor="e", stretch=False)
        self.tree.column("credit", width=120, anchor="e", stretch=False)
        self.tree.column("branch", width=140, anchor="e", stretch=False)
        self.tree.column("line_description", width=300, anchor="e", stretch=True)

        yscroll = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

        self.tree.tag_configure("odd", background="#f6fcfc")
        self.tree.tag_configure("even", background="#ebf9f9")

    def _build_footer_totals(self):
        foot = ttk.Frame(self.content, style="JV.Card.TFrame")
        foot.grid(row=4, column=0, sticky="ew", padx=4, pady=(2, 4))
        foot.grid_columnconfigure(0, weight=1)

        right = ttk.Frame(foot, style="JV.Card.TFrame")
        right.grid(row=0, column=0, sticky="e")

        ttk.Label(right, text="إجمالي المدين", style="JV.Label.TLabel").grid(row=0, column=0, sticky="e", padx=6, pady=2)
        self.ent_total_debit = ttk.Entry(right, textvariable=self.total_debit_var, style="JV.Field.TEntry", justify="right", state="readonly", width=18)
        self.ent_total_debit.grid(row=0, column=1, sticky="e", padx=6, pady=2)

        ttk.Label(right, text="إجمالي الدائن", style="JV.Label.TLabel").grid(row=1, column=0, sticky="e", padx=6, pady=2)
        self.ent_total_credit = ttk.Entry(right, textvariable=self.total_credit_var, style="JV.Field.TEntry", justify="right", state="readonly", width=18)
        self.ent_total_credit.grid(row=1, column=1, sticky="e", padx=6, pady=2)

        self.lbl_balance_status = ttk.Label(right, textvariable=self.balance_status_var, style="JV.StatusBad.TLabel")
        self.lbl_balance_status.grid(row=2, column=0, columnspan=2, sticky="e", padx=6, pady=(2, 0))

    def _meta_field(self, parent, row, label, var_obj, readonly=False):
        ttk.Label(parent, text=label, style="JV.Label.TLabel").grid(row=row, column=0, sticky="e", padx=(0, 6), pady=2)
        state = "readonly" if readonly else "normal"
        ent = ttk.Entry(parent, textvariable=var_obj, style="JV.Field.TEntry", justify="right", state=state)
        ent.grid(row=row, column=1, sticky="ew", pady=2)
        return ent

    def _meta_date(self, parent, row, label, var_obj):
        ttk.Label(parent, text=label, style="JV.Label.TLabel").grid(row=row, column=0, sticky="e", padx=(0, 6), pady=2)
        date_class = getattr(ttk, "DateEntry", None)
        if date_class:
            widget = date_class(parent, bootstyle="info", dateformat="%Y-%m-%d")
            widget.entry.configure(justify="right", font=("Segoe UI", 10, "bold"))
            widget.grid(row=row, column=1, sticky="ew", pady=2)
            self.ent_date = widget
        else:
            widget = ttk.Entry(parent, textvariable=var_obj, style="JV.Field.TEntry", justify="right")
            widget.grid(row=row, column=1, sticky="ew", pady=2)
            self.ent_date = widget

    def _bind_events(self):
        self.combo_line_account_code.bind("<<ComboboxSelected>>", self._on_account_selected)
        self.combo_line_account_code.bind("<FocusOut>", self._on_account_selected)
        self.ent_line_debit.bind("<Return>", self._confirm_line_enter)
        self.ent_line_credit.bind("<Return>", self._confirm_line_enter)
        self.ent_line_desc.bind("<Return>", self._confirm_line_enter)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_selected)
        self.tree.bind("<Double-1>", self._on_tree_selected)
        self.tree.bind("<Delete>", lambda _e: self._delete_selected_line())

        self.frame.bind_all("<Control-s>", lambda _e: self._save_voucher())
        self.frame.bind_all("<Control-S>", lambda _e: self._save_voucher())

    def _confirm_line_enter(self, _event=None):
        self._add_or_update_line()
        return "break"

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
        valid = [str(v) for v in values if str(v).strip()]
        if not valid:
            messagebox.showinfo("Info", "No values available")
            return None

        win = tk.Toplevel(self.master)
        win.title(title)
        win.geometry("500x420")
        win.transient(self.master)
        win.grab_set()

        search_var = tk.StringVar()
        ttk.Entry(win, textvariable=search_var, justify="right").pack(fill="x", padx=10, pady=(10, 6))

        tree = ttk.Treeview(win, columns=("value",), show="headings", selectmode="browse")
        tree.heading("value", text="Select")
        tree.column("value", width=460, anchor="e")
        tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        picked = {"value": None}

        def refill(*_):
            q = search_var.get().strip().lower()
            tree.delete(*tree.get_children())
            for item in valid:
                if not q or q in item.lower():
                    tree.insert("", tk.END, values=(item,))

        def choose(_event=None):
            sel = tree.selection()
            if not sel:
                return
            picked["value"] = tree.item(sel[0])["values"][0]
            win.destroy()

        ttk.Button(win, text="Apply", style="JV.Line.TButton", command=choose).pack(pady=(0, 8))
        search_var.trace_add("write", refill)
        tree.bind("<Double-1>", choose)
        refill()
        win.wait_window()
        return picked["value"]

    def _pick_customer(self):
        val = self._open_picker("Select Customer", self.combo_customer.cget("values"))
        if val:
            self.customer_var.set(str(val))
            self.customer_chk_var.set(True)
            self._on_customer_toggle()

    def _pick_vendor(self):
        val = self._open_picker("Select Vendor", self.combo_vendor.cget("values"))
        if val:
            self.vendor_var.set(str(val))
            self.vendor_chk_var.set(True)
            self._on_vendor_toggle()

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

    def _parse_amount(self, raw, field):
        text = (raw or "").replace(",", "").strip()
        if not text:
            return 0.0
        try:
            val = float(text)
        except ValueError:
            raise ValueError(f"{field} must be numeric")
        if val < 0:
            raise ValueError(f"{field} cannot be negative")
        return val

    def _fmt(self, val):
        try:
            return f"{float(val):,.2f}"
        except Exception:
            return "0.00"

    def _load_master_data(self):
        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()

            cur.execute("SELECT TRIM(account_code), account_name FROM finance.accounts ORDER BY account_code")
            account_codes = []
            self.account_display_to_code.clear()
            self.account_code_to_name.clear()
            self.account_code_to_display.clear()
            for code, name in cur.fetchall() or []:
                code_txt = str(code or "").strip()
                name_txt = str(name or "").strip()
                if not code_txt:
                    continue
                account_codes.append(code_txt)
                self.account_code_to_name[code_txt] = name_txt
                disp = f"{code_txt} - {name_txt}"
                self.account_display_to_code[disp] = code_txt
                self.account_code_to_display[code_txt] = disp
            set_combobox_values(self.combo_line_account_code, account_codes)

            cur.execute("SELECT id, vendor_name FROM finance.vendors ORDER BY vendor_name")
            vendors = []
            self.vendor_display_to_id.clear()
            self.vendor_id_to_display.clear()
            for vid, vname in cur.fetchall() or []:
                if vid is None:
                    continue
                disp = f"{int(vid)} - {str(vname or '').strip()}"
                vendors.append(disp)
                self.vendor_display_to_id[disp] = int(vid)
                self.vendor_id_to_display[int(vid)] = disp
            set_combobox_values(self.combo_customer, vendors)
            set_combobox_values(self.combo_vendor, vendors)

        except Exception as exc:
            messagebox.showerror("DB Error", get_db_error_message(exc, "Failed to load master data"))
        finally:
            conn.close()

    def _next_reference_no(self, cur):
        if not self._column_exists(cur, "vouchers", "reference_no"):
            return "10001"
        cur.execute("SELECT COALESCE(MAX(reference_no::BIGINT), 10000) + 1 FROM finance.vouchers")
        row = cur.fetchone()
        return str(row[0]) if row and row[0] is not None else "10001"

    def _fetch_next_ids(self):
        conn = get_connection()
        if not conn:
            return "Auto", "10001"
        try:
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM finance.vouchers")
            row = cur.fetchone()
            next_id = str(row[0]) if row and row[0] is not None else "Auto"
            next_ref = self._next_reference_no(cur)
            return next_id, next_ref
        except Exception:
            return "Auto", "10001"
        finally:
            conn.close()

    def _reset_line_editor(self):
        self.selected_line_iid = None
        self.line_account_code_var.set("")
        self.line_account_name_var.set("")
        self.line_debit_var.set("0.00")
        self.line_credit_var.set("0.00")
        self.line_branch_var.set("Main")
        self.line_desc_var.set("")
        self.tree.selection_remove(self.tree.selection())

    def _reset_and_new(self, initial=False):
        self.current_voucher_id = None
        self.voucher_type_var.set(self.FIXED_VOUCHER_TYPE)
        self.voucher_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self._set_date_value(self.voucher_date_var.get())
        self.currency_var.set("YER")
        self.exchange_rate_var.set("1.00")
        self.general_desc_var.set("")

        self.customer_chk_var.set(False)
        self.vendor_chk_var.set(False)
        self.customer_var.set("")
        self.vendor_var.set("")
        self._on_customer_toggle()
        self._on_vendor_toggle()

        self.entry_lines.clear()
        self._refresh_tree()
        self._reset_line_editor()

        next_id, next_ref = self._fetch_next_ids()
        self.voucher_id_var.set(next_id)
        self.reference_no_var.set(next_ref)

        if not initial:
            self.combo_line_account_code.focus_set()

    def _on_account_selected(self, _event=None):
        code = self.line_account_code_var.get().strip()
        if code in self.account_code_to_name:
            self.line_account_name_var.set(self.account_code_to_name[code])
        else:
            self.line_account_name_var.set("")

    def _line_from_editor(self):
        code = self.line_account_code_var.get().strip()
        if not code:
            raise ValueError("Account code is required")
        if code not in self.account_code_to_name:
            raise ValueError("Account code is not valid")

        debit = self._parse_amount(self.line_debit_var.get(), "Debit")
        credit = self._parse_amount(self.line_credit_var.get(), "Credit")

        if debit > 0 and credit > 0:
            raise ValueError("Enter either debit or credit, not both")
        if debit <= 0 and credit <= 0:
            raise ValueError("Enter debit or credit amount")

        return {
            "account_code": code,
            "account_name": self.account_code_to_name.get(code, ""),
            "debit": debit,
            "credit": credit,
            "branch": self.line_branch_var.get().strip() or "Main",
            "line_description": self.line_desc_var.get().strip(),
        }

    def _add_or_update_line(self):
        try:
            line = self._line_from_editor()
        except Exception as exc:
            messagebox.showwarning("Validation", str(exc))
            return

        if self.selected_line_iid:
            for idx, old in enumerate(self.entry_lines):
                if old.get("_iid") == self.selected_line_iid:
                    line["_iid"] = self.selected_line_iid
                    self.entry_lines[idx] = line
                    break
        else:
            iid = f"line_{len(self.entry_lines)+1}_{datetime.now().timestamp()}"
            line["_iid"] = iid
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
        self.line_account_code_var.set(line.get("account_code", ""))
        self.line_account_name_var.set(line.get("account_name", ""))
        self.line_debit_var.set(self._fmt(line.get("debit", 0)))
        self.line_credit_var.set(self._fmt(line.get("credit", 0)))
        self.line_branch_var.set(line.get("branch", "Main"))
        self.line_desc_var.set(line.get("line_description", ""))

    def _delete_selected_line(self):
        sel = self.tree.selection()
        iid = self.selected_line_iid or (sel[0] if sel else None)
        if not iid:
            messagebox.showwarning("Validation", "Select a line first")
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
                    line.get("branch", ""),
                    line.get("line_description", ""),
                ),
                tags=(tag,),
            )
            line["_iid"] = iid

        self._refresh_totals()

    def _refresh_totals(self):
        total_debit = round(sum(float(x.get("debit", 0) or 0) for x in self.entry_lines), 2)
        total_credit = round(sum(float(x.get("credit", 0) or 0) for x in self.entry_lines), 2)
        self.total_debit_var.set(self._fmt(total_debit))
        self.total_credit_var.set(self._fmt(total_credit))

        if self.entry_lines and abs(total_debit - total_credit) < 0.005:
            self.balance_status_var.set("Balance Status: Balanced")
            self.lbl_balance_status.configure(style="JV.StatusGood.TLabel")
        else:
            self.balance_status_var.set("Balance Status: Not Balanced")
            self.lbl_balance_status.configure(style="JV.StatusBad.TLabel")

    def _resolve_vendor_id(self):
        if self.vendor_chk_var.get():
            return self.vendor_display_to_id.get(self.vendor_var.get().strip())
        if self.customer_chk_var.get():
            return self.vendor_display_to_id.get(self.customer_var.get().strip())
        return None

    def _validate_before_save(self):
        if not self.entry_lines:
            raise ValueError("Add at least one line")

        total_debit = round(sum(float(x.get("debit", 0) or 0) for x in self.entry_lines), 2)
        total_credit = round(sum(float(x.get("credit", 0) or 0) for x in self.entry_lines), 2)

        if abs(total_debit - total_credit) >= 0.005:
            raise ValueError("Total Debit must equal Total Credit before saving")

        self._parse_amount(self.exchange_rate_var.get(), "Exchange Rate")

    def _upsert_voucher_header(self, cur, is_update):
        v_date = self._get_date_value() or datetime.now().strftime("%Y-%m-%d")
        ref_no = self.reference_no_var.get().strip()
        currency = self.currency_var.get().strip()
        ex_rate = self._parse_amount(self.exchange_rate_var.get(), "Exchange Rate")
        desc = self.general_desc_var.get().strip()

        has_ref = self._column_exists(cur, "vouchers", "reference_no")
        has_currency = self._column_exists(cur, "vouchers", "currency")
        has_ex_rate = self._column_exists(cur, "vouchers", "exchange_rate")

        if is_update:
            if not self.current_voucher_id:
                raise ValueError("No voucher loaded for update")

            cols = ["v_type=%s", "v_date=%s", "description=%s"]
            vals = [self.FIXED_VOUCHER_TYPE, v_date, desc]
            if has_ref:
                cols.append("reference_no=%s")
                vals.append(ref_no)
            if has_currency:
                cols.append("currency=%s")
                vals.append(currency)
            if has_ex_rate:
                cols.append("exchange_rate=%s")
                vals.append(ex_rate)

            vals.append(self.current_voucher_id)
            cur.execute(f"UPDATE finance.vouchers SET {', '.join(cols)} WHERE id=%s", tuple(vals))
            return self.current_voucher_id

        cols = ["v_type", "v_date", "description"]
        vals = [self.FIXED_VOUCHER_TYPE, v_date, desc]
        if has_ref:
            cols.append("reference_no")
            vals.append(ref_no)
        if has_currency:
            cols.append("currency")
            vals.append(currency)
        if has_ex_rate:
            cols.append("exchange_rate")
            vals.append(ex_rate)

        cur.execute(
            f"INSERT INTO finance.vouchers ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(vals))}) RETURNING id",
            tuple(vals),
        )
        return int(cur.fetchone()[0])

    def _detect_ledger_branch_column(self, cur):
        for col in ("branch", "branch_name", "branch_code"):
            if self._column_exists(cur, "ledger", col):
                return col
        return None

    def _save_ledger_lines(self, cur, voucher_id):
        cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (voucher_id,))

        vendor_id = self._resolve_vendor_id()
        posting_date = self._get_date_value() or datetime.now().strftime("%Y-%m-%d")

        has_line_desc = self._column_exists(cur, "ledger", "line_description")
        has_desc = self._column_exists(cur, "ledger", "description")
        has_posting_date = self._column_exists(cur, "ledger", "posting_date")
        has_vendor = self._column_exists(cur, "ledger", "vendor_id")
        has_property = self._column_exists(cur, "ledger", "property_id")
        branch_col = self._detect_ledger_branch_column(cur)

        for line in self.entry_lines:
            cols = ["voucher_id", "account_code", "debit", "credit"]
            vals = [voucher_id, line["account_code"], line["debit"], line["credit"]]

            if has_vendor:
                cols.append("vendor_id")
                vals.append(vendor_id)
            if has_property:
                cols.append("property_id")
                vals.append(None)
            if branch_col:
                cols.append(branch_col)
                vals.append(line.get("branch", ""))
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
            messagebox.showinfo("Saved", "Journal Voucher saved successfully")
        except Exception as exc:
            conn.rollback()
            messagebox.showerror("DB Error", get_db_error_message(exc, "Failed to save Journal Voucher"))
        finally:
            conn.close()

    def _update_voucher(self):
        current = self.voucher_id_var.get().strip()
        if current.isdigit() and not self.current_voucher_id:
            self.current_voucher_id = int(current)

        if not self.current_voucher_id:
            ask = simpledialog.askstring("Update", "Enter Voucher ID:", parent=self.master)
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
            messagebox.showinfo("Updated", "Journal Voucher updated successfully")
        except Exception as exc:
            conn.rollback()
            messagebox.showerror("DB Error", get_db_error_message(exc, "Failed to update Journal Voucher"))
        finally:
            conn.close()

    def _delete_voucher(self):
        current = self.voucher_id_var.get().strip()
        voucher_id = int(current) if current.isdigit() else None
        if voucher_id is None:
            ask = simpledialog.askstring("Delete", "Enter Voucher ID:", parent=self.master)
            if not ask or not ask.isdigit():
                return
            voucher_id = int(ask)

        if not messagebox.askyesno("Confirm", "Delete this Journal Voucher?"):
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (voucher_id,))
            cur.execute("DELETE FROM finance.vouchers WHERE id=%s AND v_type=%s", (voucher_id, self.FIXED_VOUCHER_TYPE))
            conn.commit()
            messagebox.showinfo("Deleted", "Journal Voucher deleted")
            self._reset_and_new()
        except Exception as exc:
            conn.rollback()
            messagebox.showerror("DB Error", get_db_error_message(exc, "Failed to delete Journal Voucher"))
        finally:
            conn.close()

    def _search_voucher(self):
        ask = simpledialog.askstring("Search", "Enter Voucher ID:", parent=self.master)
        if not ask:
            return
        if not ask.isdigit():
            messagebox.showwarning("Validation", "Voucher ID must be numeric")
            return
        self._load_voucher_by_id(int(ask))

    def _load_voucher_by_id(self, voucher_id):
        conn = get_connection()
        if not conn:
            return False

        try:
            cur = conn.cursor()

            has_ref = self._column_exists(cur, "vouchers", "reference_no")
            has_currency = self._column_exists(cur, "vouchers", "currency")
            has_ex_rate = self._column_exists(cur, "vouchers", "exchange_rate")

            ref_expr = "COALESCE(reference_no::text, '')" if has_ref else "''"
            cur_expr = "COALESCE(currency, 'YER')" if has_currency else "'YER'"
            ex_expr = "COALESCE(exchange_rate, 1)" if has_ex_rate else "1"

            cur.execute(
                f"""
                SELECT id, {ref_expr} AS reference_no, v_date, COALESCE(description, ''), {cur_expr} AS currency, {ex_expr} AS exchange_rate
                FROM finance.vouchers
                WHERE id=%s AND v_type=%s
                """,
                (voucher_id, self.FIXED_VOUCHER_TYPE),
            )
            header = cur.fetchone()
            if not header:
                messagebox.showinfo("Search", "Voucher not found")
                return False

            has_line_desc = self._column_exists(cur, "ledger", "line_description")
            has_desc = self._column_exists(cur, "ledger", "description")
            branch_col = self._detect_ledger_branch_column(cur)
            branch_expr = branch_col if branch_col else "''"

            desc_expr = "COALESCE(line_description, '')" if has_line_desc else ("COALESCE(description, '')" if has_desc else "''")

            cur.execute(
                f"""
                SELECT account_code, COALESCE(debit, 0), COALESCE(credit, 0), {branch_expr} AS branch, {desc_expr} AS line_desc,
                       vendor_id
                FROM finance.ledger
                WHERE voucher_id=%s
                ORDER BY id
                """,
                (voucher_id,),
            )
            rows = cur.fetchall() or []

            self.current_voucher_id = int(header[0])
            self.voucher_id_var.set(str(header[0]))
            self.reference_no_var.set(str(header[1] or ""))
            self._set_date_value(str(header[2]))
            self.currency_var.set(str(header[4] or "YER"))
            self.exchange_rate_var.set(self._fmt(header[5] or 1))
            self.general_desc_var.set(header[3] or "")

            self.entry_lines.clear()
            first_vendor = None
            for idx, (acc_code, debit, credit, branch, line_desc, vendor_id) in enumerate(rows, start=1):
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
                        "branch": str(branch or "Main"),
                        "line_description": str(line_desc or ""),
                    }
                )
                if first_vendor is None and vendor_id is not None:
                    first_vendor = int(vendor_id)

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
                self._on_vendor_toggle()
                self._on_customer_toggle()

            self._refresh_tree()
            self._reset_line_editor()
            return True

        except Exception as exc:
            messagebox.showerror("DB Error", get_db_error_message(exc, "Failed to load Journal Voucher"))
            return False
        finally:
            conn.close()

    def _print_voucher(self):
        voucher_id = self.voucher_id_var.get().strip()
        if not voucher_id.isdigit():
            messagebox.showwarning("Validation", "Save the voucher first")
            return
        messagebox.showinfo("Print", f"Journal Voucher {voucher_id} is prepared for printing")


SettlementEntryScreen = JournalVoucherScreen
AdjustmentJournalEntryScreen = JournalVoucherScreen


if __name__ == "__main__":
    root = ttk.Window(themename="darkly")
    root.title("Journal Voucher")
    root.geometry("1400x900")
    JournalVoucherScreen(root)
    root.mainloop()
