import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import END

from db_connection import get_connection, get_db_error_message
from combobox_helper import bind_searchable_combobox, set_combobox_values
from app_constants import SYSTEM_NAME


class AdjustmentJournalEntryScreen:
    FIXED_VOUCHER_TYPE = "قيد"

    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.bg_color = "#f4f7f6"

        self._ledger_column_cache = {}
        self._voucher_column_cache = {}

        self.current_voucher_id = None
        self.selected_line_iid = None
        self.entry_lines = []

        self.account_data = {}
        self.property_data = {}
        self.vendor_data = {}

        self.voucher_id_var = tk.StringVar(value="تلقائي")
        self.voucher_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

        self.line_account_var = tk.StringVar()
        self.line_desc_var = tk.StringVar()
        self.line_debit_var = tk.StringVar(value="0.00")
        self.line_credit_var = tk.StringVar(value="0.00")
        self.line_property_var = tk.StringVar()
        self.line_vendor_var = tk.StringVar()

        self.total_debit_var = tk.StringVar(value="0.00")
        self.total_credit_var = tk.StringVar(value="0.00")
        self.difference_var = tk.StringVar(value="0.00")
        self.balance_status_var = tk.StringVar(value="غير متوازن")

        self._setup_styles()
        self._build_layout()
        self._bind_events()
        self._load_initial_data()
        self._reset_and_new(initial=True)

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("Adj.Root.TFrame", background=self.bg_color)
        style.configure("Adj.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("Adj.Header.TFrame", background=self.primary_color)
        style.configure("Adj.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 18, "bold"))
        style.configure("Adj.Content.TFrame", background="white")
        style.configure("Adj.FieldLabel.TLabel", background=self.sidebar_color, foreground=self.text_color, font=("Segoe UI", 11, "bold"), anchor="center", padding=8)
        style.configure("Adj.Field.TEntry", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 11, "bold"))
        style.configure("Adj.Field.TCombobox", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 11, "bold"))
        style.configure("Adj.SectionTitle.TLabel", background="white", foreground=self.primary_color, font=("Segoe UI", 13, "bold"))
        style.configure("Adj.StatusTitle.TLabel", background="white", foreground=self.sidebar_color, font=("Segoe UI", 11, "bold"))
        style.configure("Adj.StatusValue.TLabel", background="white", foreground=self.primary_color, font=("Segoe UI", 18, "bold"))
        style.configure("Adj.Total.TFrame", background="#f8f9fa", bordercolor="#d8e1e8", borderwidth=1, relief="solid")

        # Grid-like table look with clearer header and selected-row contrast.
        style.configure(
            "Adj.Treeview",
            rowheight=34,
            font=("Segoe UI", 10),
            background="#ffffff",
            fieldbackground="#ffffff",
            bordercolor="#cfd8dc",
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Adj.Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#e9eff3",
            foreground="#1f2d3a",
            relief="solid",
            borderwidth=1,
        )
        style.map(
            "Adj.Treeview",
            background=[("selected", "#1abc9c")],
            foreground=[("selected", "white")],
        )
        style.map(
            "Adj.Treeview.Heading",
            background=[("active", "#dbe5ec")],
        )

        style.configure("Adj.Primary.TButton", background="#2980b9", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("Adj.Success.TButton", background="#27ae60", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("Adj.Warning.TButton", background="#f1c40f", foreground="#2c3e50", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("Adj.Danger.TButton", background="#e74c3c", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("Adj.Info.TButton", background="#8e44ad", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("Adj.Exit.TButton", background="#e67e22", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("Adj.Line.TButton", font=("Segoe UI", 10, "bold"), padding=(8, 5))

        for btn_style in (
            "Adj.Primary.TButton",
            "Adj.Success.TButton",
            "Adj.Warning.TButton",
            "Adj.Danger.TButton",
            "Adj.Info.TButton",
            "Adj.Exit.TButton",
            "Adj.Line.TButton",
        ):
            style.map(
                btn_style,
                background=[("active", self.accent_color), ("pressed", self.accent_color)],
                foreground=[("active", "white"), ("pressed", "white")],
            )

    def _build_layout(self):
        self.frame = ttk.Frame(self.master, style="Adj.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        main_card = ttk.Frame(self.frame, style="Adj.Card.TFrame")
        main_card.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        self._build_header_buttons(main_card)

        self.content = ttk.Frame(main_card, style="Adj.Content.TFrame", padding=(22, 16))
        self.content.pack(fill=tk.BOTH, expand=True)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)

        self._build_voucher_info_card()
        self._build_line_entry_card()
        self._build_table_card()
        self._build_totals_status_card()

    def _build_header_buttons(self, parent):
        header = ttk.Frame(parent, style="Adj.Header.TFrame", height=68)
        header.pack(fill="x", side="top")

        ttk.Label(header, text=f"قيد تسوية احترافي - {SYSTEM_NAME}", style="Adj.Header.TLabel").pack(side="right", padx=30, pady=15)

        btn_group = ttk.Frame(header, style="Adj.Header.TFrame")
        btn_group.pack(side="left", padx=20)

        self.btn_new = ttk.Button(btn_group, text="جديد", style="Adj.Primary.TButton", width=9, command=self._reset_and_new)
        self.btn_new.pack(side="left", padx=5)
        self.btn_save = ttk.Button(btn_group, text="حفظ", style="Adj.Success.TButton", width=9, command=self._save_voucher)
        self.btn_save.pack(side="left", padx=5)
        self.btn_update = ttk.Button(btn_group, text="تعديل", style="Adj.Warning.TButton", width=9, command=self._update_voucher)
        self.btn_update.pack(side="left", padx=5)
        self.btn_delete = ttk.Button(btn_group, text="حذف", style="Adj.Danger.TButton", width=9, command=self._delete_voucher)
        self.btn_delete.pack(side="left", padx=5)
        self.btn_search = ttk.Button(btn_group, text="بحث", style="Adj.Info.TButton", width=9, command=self._search_voucher)
        self.btn_search.pack(side="left", padx=5)
        self.btn_exit = ttk.Button(btn_group, text="خروج", style="Adj.Exit.TButton", width=9, command=self._exit_screen)
        self.btn_exit.pack(side="left", padx=5)

    def _build_voucher_info_card(self):
        card = ttk.Frame(self.content, style="Adj.Card.TFrame", padding=16)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for col in range(3):
            card.grid_columnconfigure(col, weight=1)

        ttk.Label(card, text="بيانات السند", style="Adj.SectionTitle.TLabel").grid(row=0, column=2, sticky="e", pady=(0, 8))

        self.ent_voucher_id = self._create_field(card, "رقم السند :", 1, 2, textvariable=self.voucher_id_var, state="readonly")
        self.ent_voucher_date = self._create_field(card, "التاريخ :", 1, 1, textvariable=self.voucher_date_var)

        type_box = ttk.Frame(card, style="Adj.Content.TFrame")
        type_box.grid(row=1, column=0, sticky="ew", padx=6, pady=6)
        type_box.grid_columnconfigure(0, weight=1)

        self.ent_voucher_type = ttk.Entry(type_box, style="Adj.Field.TEntry", justify="right", state="readonly")
        self.ent_voucher_type.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ttk.Label(type_box, text="نوع القيد :", style="Adj.FieldLabel.TLabel", width=16).grid(row=0, column=1, sticky="ns")

        self.ent_voucher_type.configure(state="normal")
        self.ent_voucher_type.delete(0, END)
        self.ent_voucher_type.insert(0, self.FIXED_VOUCHER_TYPE)
        self.ent_voucher_type.configure(state="readonly")

        desc_box = ttk.Frame(card, style="Adj.Content.TFrame")
        desc_box.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        desc_box.grid_columnconfigure(0, weight=1)

        ttk.Label(desc_box, text="الوصف العام :", style="Adj.FieldLabel.TLabel", width=16).grid(row=0, column=1, sticky="ns")
        self.txt_general_desc = tk.Text(desc_box, font=("Segoe UI", 11, "bold"), bd=1, relief="solid", height=3, wrap="word")
        self.txt_general_desc.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    def _build_line_entry_card(self):
        card = ttk.Frame(self.content, style="Adj.Card.TFrame", padding=16)
        card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        for col in range(4):
            card.grid_columnconfigure(col, weight=1)

        ttk.Label(card, text="إدخال سطر القيد", style="Adj.SectionTitle.TLabel").grid(row=0, column=3, sticky="e", pady=(0, 8))

        self.combo_line_account = self._create_field(card, "الحساب :", 1, 3, widget_type="combo", textvariable=self.line_account_var)
        self.ent_line_desc = self._create_field(card, "الوصف :", 1, 2, textvariable=self.line_desc_var)
        self.ent_line_debit = self._create_field(card, "مدين :", 1, 1, textvariable=self.line_debit_var)
        self.ent_line_credit = self._create_field(card, "دائن :", 1, 0, textvariable=self.line_credit_var)

        self.combo_line_property = self._create_field(card, "العقار :", 2, 3, widget_type="combo", textvariable=self.line_property_var)
        self.combo_line_vendor = self._create_field(card, "المورد / الوارث :", 2, 2, widget_type="combo", textvariable=self.line_vendor_var)

        line_btns = ttk.Frame(card, style="Adj.Content.TFrame")
        line_btns.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        line_btns.grid_columnconfigure(0, weight=1)
        line_btns.grid_columnconfigure(1, weight=1)

        left_btns = ttk.Frame(line_btns, style="Adj.Content.TFrame")
        left_btns.grid(row=0, column=0, sticky="w")

        right_btns = ttk.Frame(line_btns, style="Adj.Content.TFrame")
        right_btns.grid(row=0, column=1, sticky="e")

        self.btn_add_line = ttk.Button(left_btns, text="+ Add", style="Adj.Line.TButton", command=self._add_line_from_form)
        self.btn_add_line.pack(side="left", padx=4)
        self.btn_update_line = ttk.Button(left_btns, text="✎ Edit", style="Adj.Line.TButton", command=self._update_selected_line, state="disabled")
        self.btn_update_line.pack(side="left", padx=4)
        self.btn_delete_line = ttk.Button(left_btns, text="- Delete", style="Adj.Line.TButton", command=self._delete_selected_line, state="disabled")
        self.btn_delete_line.pack(side="left", padx=4)

        self.btn_clear_line = ttk.Button(right_btns, text="↺ Clear", style="Adj.Line.TButton", command=self._clear_line_form)
        self.btn_clear_line.pack(side="right", padx=4)

        ttk.Label(card, text="اختصار: Enter = Add Line", style="Adj.StatusTitle.TLabel").grid(row=3, column=3, sticky="e", pady=(10, 0))

    def _build_table_card(self):
        card = ttk.Frame(self.content, style="Adj.Card.TFrame", padding=14)
        card.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        ttk.Label(card, text="جدول القيد (Invoice Style)", style="Adj.SectionTitle.TLabel").grid(row=0, column=0, sticky="e", pady=(0, 8))

        cols = ("account", "description", "debit", "credit", "property", "vendor")
        self.tree = ttk.Treeview(card, columns=cols, show="headings", style="Adj.Treeview", selectmode="browse")

        headers = {
            "account": "الحساب",
            "description": "الوصف",
            "debit": "مدين",
            "credit": "دائن",
            "property": "العقار",
            "vendor": "المورد/الوارث",
        }
        widths = {"account": 300, "description": 260, "debit": 120, "credit": 120, "property": 220, "vendor": 220}

        for c in cols:
            self.tree.heading(c, text=headers[c], anchor="e")
            self.tree.column(c, width=widths[c], anchor="e", stretch=True)

        self.tree.grid(row=1, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        yscroll.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.tag_configure("odd", background="#ffffff")
        self.tree.tag_configure("even", background="#f5f9fc")

    def _apply_tree_striping(self):
        for idx, iid in enumerate(self.tree.get_children()):
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.item(iid, tags=(tag,))

    def _build_totals_status_card(self):
        card = ttk.Frame(self.content, style="Adj.Total.TFrame", padding=16)
        card.grid(row=3, column=0, sticky="ew")
        for col in range(4):
            card.grid_columnconfigure(col, weight=1)

        ttk.Label(card, text="إجمالي المدين", style="Adj.StatusTitle.TLabel").grid(row=0, column=3, sticky="e")
        ttk.Label(card, textvariable=self.total_debit_var, style="Adj.StatusValue.TLabel").grid(row=1, column=3, sticky="e")

        ttk.Label(card, text="إجمالي الدائن", style="Adj.StatusTitle.TLabel").grid(row=0, column=2, sticky="e")
        ttk.Label(card, textvariable=self.total_credit_var, style="Adj.StatusValue.TLabel").grid(row=1, column=2, sticky="e")

        ttk.Label(card, text="الفرق", style="Adj.StatusTitle.TLabel").grid(row=0, column=1, sticky="e")
        ttk.Label(card, textvariable=self.difference_var, style="Adj.StatusValue.TLabel").grid(row=1, column=1, sticky="e")

        ttk.Label(card, text="الحالة", style="Adj.StatusTitle.TLabel").grid(row=0, column=0, sticky="e")
        self.lbl_status = ttk.Label(card, textvariable=self.balance_status_var, style="Adj.SectionTitle.TLabel")
        self.lbl_status.grid(row=1, column=0, sticky="e")

    def _create_field(self, parent, label_text, row, column, widget_type="entry", **kwargs):
        box = ttk.Frame(parent, style="Adj.Content.TFrame")
        box.grid(row=row, column=column, sticky="ew", padx=6, pady=6)
        box.grid_columnconfigure(0, weight=1)

        if widget_type == "entry":
            field = ttk.Entry(box, style="Adj.Field.TEntry", justify="right", **kwargs)
        else:
            field = ttk.Combobox(box, style="Adj.Field.TCombobox", justify="right", **kwargs)

        field.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ttk.Label(box, text=label_text, style="Adj.FieldLabel.TLabel", width=16).grid(row=0, column=1, sticky="ns")
        return field


    def _bind_events(self):
        self.frame.bind_all("<Control-s>", lambda _e: self._save_voucher())
        self.frame.bind_all("<Control-S>", lambda _e: self._save_voucher())

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<Delete>", lambda _e: self._delete_selected_line())
        self.frame.bind_all("<Delete>", self._on_delete_key)

        for w in (
            self.combo_line_account,
            self.ent_line_desc,
            self.ent_line_debit,
            self.ent_line_credit,
            self.combo_line_property,
            self.combo_line_vendor,
        ):
            w.bind("<Return>", self._handle_enter_key)

        bind_searchable_combobox(self.combo_line_account)
        bind_searchable_combobox(self.combo_line_property)
        bind_searchable_combobox(self.combo_line_vendor)

    def _on_tree_double_click(self, _event=None):
        # Reuse existing selection-to-form behavior on double click.
        self._on_tree_select()

    def _on_delete_key(self, _event=None):
        if self.selected_line_iid:
            self._delete_selected_line()

    def _handle_enter_key(self, _event=None):
        if self.selected_line_iid:
            self._update_selected_line()
        else:
            self._add_line_from_form()
        return "break"

    def _load_initial_data(self):
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            try:
                cur.execute("SELECT id, TRIM(account_code), account_name FROM finance.accounts ORDER BY account_code")
                self.account_data = {
                    f"{r[1]} - {r[2]}": {"id": r[0], "code": str(r[1]).strip(), "name": r[2] or ""}
                    for r in cur.fetchall()
                }
            except Exception:
                cur.execute("SELECT TRIM(account_code), account_name FROM finance.accounts ORDER BY account_code")
                self.account_data = {
                    f"{r[0]} - {r[1]}": {"id": None, "code": str(r[0]).strip(), "name": r[1] or ""}
                    for r in cur.fetchall()
                }

            cur.execute("SELECT id, property_name FROM finance.properties ORDER BY property_name")
            self.property_data = {f"{r[0]} - {r[1]}": {"id": r[0], "name": r[1]} for r in cur.fetchall()}

            cur.execute("SELECT id, vendor_name FROM finance.vendors ORDER BY vendor_name")
            self.vendor_data = {f"{r[0]} - {r[1]}": {"id": r[0], "name": r[1]} for r in cur.fetchall()}

            set_combobox_values(self.combo_line_account, self.account_data.keys())
            set_combobox_values(self.combo_line_property, self.property_data.keys())
            set_combobox_values(self.combo_line_vendor, self.vendor_data.keys())
        except Exception as e:
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _schema_has_column(self, cur, table_name, column_name):
        cache = self._ledger_column_cache if table_name == "ledger" else self._voucher_column_cache
        key = f"{table_name}.{column_name}"
        if key in cache:
            return cache[key]

        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema='finance' AND table_name=%s AND column_name=%s
            )
            """,
            (table_name, column_name),
        )
        exists = bool(cur.fetchone()[0])
        cache[key] = exists
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

    def _parse_amount(self, value, label):
        text = (value or "").strip().replace(",", "")
        if not text:
            return 0.0
        try:
            amount = float(text)
        except ValueError:
            raise ValueError(f"{label} يجب أن يكون رقمًا")
        if amount < 0:
            raise ValueError(f"{label} لا يمكن أن يكون سالبًا")
        return amount

    def _resolve_dimension(self, data_map, text):
        payload = data_map.get((text or "").strip())
        if payload:
            return payload["id"], payload["name"]
        return None, ""

    def _build_line_from_form(self):
        account_text = self.line_account_var.get().strip()
        if not account_text:
            raise ValueError("اختر الحساب")

        account = self.account_data.get(account_text)
        if not account:
            raise ValueError("الحساب غير صالح")

        debit = self._parse_amount(self.line_debit_var.get(), "المدين")
        credit = self._parse_amount(self.line_credit_var.get(), "الدائن")

        if debit <= 0 and credit <= 0:
            raise ValueError("يجب إدخال قيمة مدين أو دائن")
        if debit > 0 and credit > 0:
            raise ValueError("السطر يجب أن يحتوي على طرف واحد فقط: مدين أو دائن")

        prop_text = self.line_property_var.get().strip()
        ven_text = self.line_vendor_var.get().strip()

        prop_id, prop_name = self._resolve_dimension(self.property_data, prop_text)
        ven_id, ven_name = self._resolve_dimension(self.vendor_data, ven_text)

        return {
            "account_id": account.get("id"),
            "account_code": account["code"],
            "account_name": account["name"],
            "account_text": account_text,
            "description": self.line_desc_var.get().strip(),
            "debit": debit,
            "credit": credit,
            "property_id": prop_id,
            "property_name": prop_name,
            "property_text": prop_text,
            "vendor_id": ven_id,
            "vendor_name": ven_name,
            "vendor_text": ven_text,
        }

    def _format_line_values(self, line):
        return (
            line["account_text"],
            line["description"],
            f"{line['debit']:,.2f}",
            f"{line['credit']:,.2f}",
            line["property_text"],
            line["vendor_text"],
        )

    def _clear_line_form(self):
        self.selected_line_iid = None
        self.line_account_var.set("")
        self.line_desc_var.set("")
        self.line_debit_var.set("0.00")
        self.line_credit_var.set("0.00")
        self.line_property_var.set("")
        self.line_vendor_var.set("")

        self.tree.selection_remove(self.tree.selection())
        self.btn_update_line.configure(state="disabled")
        self.btn_delete_line.configure(state="disabled")

    def _add_line_from_form(self):
        try:
            line = self._build_line_from_form()
        except Exception as e:
            return messagebox.showwarning("تنبيه", str(e))

        iid = self.tree.insert("", "end", values=self._format_line_values(line))
        line["_iid"] = iid
        self.entry_lines.append(line)

        self._apply_tree_striping()
        self._refresh_totals_status()
        self._clear_line_form()
        self.combo_line_account.focus_set()

    def _on_tree_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return

        iid = selected[0]
        line = next((x for x in self.entry_lines if x.get("_iid") == iid), None)
        if not line:
            return

        self.selected_line_iid = iid
        self.line_account_var.set(line["account_text"])
        self.line_desc_var.set(line["description"])
        self.line_debit_var.set(f"{line['debit']:.2f}")
        self.line_credit_var.set(f"{line['credit']:.2f}")
        self.line_property_var.set(line["property_text"])
        self.line_vendor_var.set(line["vendor_text"])

        self.btn_update_line.configure(state="normal")
        self.btn_delete_line.configure(state="normal")

    def _update_selected_line(self):
        if not self.selected_line_iid:
            return messagebox.showwarning("تنبيه", "اختر سطرًا للتعديل")

        try:
            new_line = self._build_line_from_form()
        except Exception as e:
            return messagebox.showwarning("تنبيه", str(e))

        for i, old in enumerate(self.entry_lines):
            if old.get("_iid") == self.selected_line_iid:
                new_line["_iid"] = self.selected_line_iid
                self.entry_lines[i] = new_line
                self.tree.item(self.selected_line_iid, values=self._format_line_values(new_line))
                break

        self._apply_tree_striping()
        self._refresh_totals_status()
        self._clear_line_form()

    def _delete_selected_line(self):
        if not self.selected_line_iid:
            return messagebox.showwarning("تنبيه", "اختر سطرًا للحذف")

        self.entry_lines = [x for x in self.entry_lines if x.get("_iid") != self.selected_line_iid]
        self.tree.delete(self.selected_line_iid)
        self._apply_tree_striping()
        self._refresh_totals_status()
        self._clear_line_form()

    def _refresh_totals_status(self):
        total_debit = sum(x["debit"] for x in self.entry_lines)
        total_credit = sum(x["credit"] for x in self.entry_lines)
        diff = round(total_debit - total_credit, 2)

        self.total_debit_var.set(f"{total_debit:,.2f}")
        self.total_credit_var.set(f"{total_credit:,.2f}")
        self.difference_var.set(f"{diff:,.2f}")

        balanced = len(self.entry_lines) > 0 and total_debit > 0 and total_credit > 0 and abs(diff) < 0.005
        if balanced:
            self.balance_status_var.set("متوازن")
            self.lbl_status.configure(foreground="#27ae60")
        else:
            self.balance_status_var.set("غير متوازن")
            self.lbl_status.configure(foreground="#c0392b")

        self.btn_save.configure(state="normal" if balanced else "disabled")
        self.btn_update.configure(state="normal" if balanced and self.current_voucher_id else "disabled")

    def _set_header_button_states(self):
        self.btn_delete.configure(state="normal" if self.current_voucher_id else "disabled")
        self.btn_update.configure(state="normal" if self.current_voucher_id else "disabled")

    def _validate_voucher_before_persist(self):
        if not self.voucher_date_var.get().strip():
            raise ValueError("أدخل التاريخ")
        if not self.entry_lines:
            raise ValueError("أضف سطرًا واحدًا على الأقل")

        total_debit = sum(x["debit"] for x in self.entry_lines)
        total_credit = sum(x["credit"] for x in self.entry_lines)

        if total_debit <= 0 or total_credit <= 0:
            raise ValueError("القيد يجب أن يحتوي على مدين ودائن")
        if abs(total_debit - total_credit) >= 0.005:
            raise ValueError("القيد غير متوازن")

        for ln in self.entry_lines:
            if (ln["debit"] > 0 and ln["credit"] > 0) or (ln["debit"] <= 0 and ln["credit"] <= 0):
                raise ValueError("يوجد سطر غير صحيح: يجب أن يكون مدين أو دائن فقط")

    def _insert_voucher_header(self, cur):
        v_date = self.voucher_date_var.get().strip()
        desc = self.txt_general_desc.get("1.0", END).strip()

        cur.execute(
            "INSERT INTO finance.vouchers (v_type, v_date, description) VALUES (%s, %s, %s) RETURNING id",
            (self.FIXED_VOUCHER_TYPE, v_date, desc),
        )
        return cur.fetchone()[0]

    def _insert_ledger_line(self, cur, voucher_id, line):
        columns = ["voucher_id", "debit", "credit", "property_id", "vendor_id"]
        values = [voucher_id, line["debit"], line["credit"], line["property_id"], line["vendor_id"]]

        if self._schema_has_column(cur, "ledger", "account_id") and line.get("account_id") is not None:
            columns.append("account_id")
            values.append(line["account_id"])
        else:
            columns.append("account_code")
            values.append(line["account_code"])

        if self._schema_has_column(cur, "ledger", "description"):
            columns.append("description")
            values.append(line["description"])

        sql = f"INSERT INTO finance.ledger ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(values))})"
        cur.execute(sql, tuple(values))

    def _reset_and_new(self, initial=False):
        self.current_voucher_id = None
        self.voucher_id_var.set(self._get_next_voucher_id())
        self.voucher_date_var.set(datetime.now().strftime("%Y-%m-%d"))

        self.txt_general_desc.delete("1.0", END)

        self.entry_lines.clear()
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        self._clear_line_form()
        self._refresh_totals_status()
        self._set_header_button_states()

        if not initial:
            self.ent_voucher_date.focus_set()

    def _save_voucher(self):
        try:
            self._validate_voucher_before_persist()
        except Exception as e:
            return messagebox.showwarning("تنبيه", str(e))

        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            voucher_id = self._insert_voucher_header(cur)
            for line in self.entry_lines:
                self._insert_ledger_line(cur, voucher_id, line)
            conn.commit()

            self.current_voucher_id = int(voucher_id)
            self.voucher_id_var.set(str(voucher_id))
            self._set_header_button_states()
            self._refresh_totals_status()
            messagebox.showinfo("نجاح", "تم حفظ قيد التسوية بنجاح")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", get_db_error_message(e, "تعذر حفظ قيد التسوية"))
        finally:
            conn.close()

    def _update_voucher(self):
        if not self.current_voucher_id:
            return messagebox.showwarning("تنبيه", "ابحث عن سند محفوظ أولاً")

        try:
            self._validate_voucher_before_persist()
        except Exception as e:
            return messagebox.showwarning("تنبيه", str(e))

        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            v_date = self.voucher_date_var.get().strip()
            desc = self.txt_general_desc.get("1.0", END).strip()

            cur.execute(
                "UPDATE finance.vouchers SET v_type=%s, v_date=%s, description=%s WHERE id=%s",
                (self.FIXED_VOUCHER_TYPE, v_date, desc, self.current_voucher_id),
            )

            cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (self.current_voucher_id,))
            for line in self.entry_lines:
                self._insert_ledger_line(cur, self.current_voucher_id, line)

            conn.commit()
            self._set_header_button_states()
            self._refresh_totals_status()
            messagebox.showinfo("نجاح", "تم تعديل قيد التسوية بنجاح")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", get_db_error_message(e, "تعذر تعديل قيد التسوية"))
        finally:
            conn.close()

    def _delete_voucher(self):
        if not self.current_voucher_id:
            if messagebox.askyesno("تأكيد", "هل تريد مسح البيانات الحالية؟"):
                self._reset_and_new()
            return

        if not messagebox.askyesno("تأكيد", "هل تريد حذف السند المحدد؟"):
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (self.current_voucher_id,))

            if self._schema_has_column(cur, "vouchers", "id"):
                cur.execute("DELETE FROM finance.vouchers WHERE id=%s", (self.current_voucher_id,))
            else:
                cur.execute("DELETE FROM finance.vouchers WHERE id=%s", (self.current_voucher_id,))

            conn.commit()
            messagebox.showinfo("نجاح", "تم حذف السند")
            self._reset_and_new()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", get_db_error_message(e, "تعذر حذف قيد التسوية"))
        finally:
            conn.close()

    def _fetch_ledger_lines(self, cur, voucher_id):
        has_desc = self._schema_has_column(cur, "ledger", "description")
        has_account_id = self._schema_has_column(cur, "ledger", "account_id")

        account_join = "LEFT JOIN finance.accounts a ON a.id = l.account_id" if has_account_id else "LEFT JOIN finance.accounts a ON TRIM(a.account_code) = TRIM(l.account_code)"
        account_code_select = "TRIM(COALESCE(a.account_code::text, l.account_code::text, ''))" if has_account_id else "TRIM(COALESCE(l.account_code::text, ''))"
        detail_select = "COALESCE(l.description, '') AS detail" if has_desc else "'' AS detail"

        query = f"""
            SELECT l.id,
                   {account_code_select} AS account_code,
                   COALESCE(a.account_name, '') AS account_name,
                   COALESCE(a.id, NULL) AS account_id,
                   COALESCE(l.debit, 0) AS debit,
                   COALESCE(l.credit, 0) AS credit,
                   {detail_select},
                   COALESCE(l.property_id, 0) AS property_id,
                   COALESCE(p.property_name, '') AS property_name,
                   COALESCE(l.vendor_id, 0) AS vendor_id,
                   COALESCE(v.vendor_name, '') AS vendor_name
            FROM finance.ledger l
            {account_join}
            LEFT JOIN finance.properties p ON p.id = l.property_id
            LEFT JOIN finance.vendors v ON v.id = l.vendor_id
            WHERE l.voucher_id = %s
            ORDER BY l.id
        """
        cur.execute(query, (voucher_id,))

        lines = []
        for r in cur.fetchall():
            lines.append(
                {
                    "account_id": r[3],
                    "account_code": str(r[1] or "").strip(),
                    "account_name": r[2] or "",
                    "description": r[6] or "",
                    "debit": float(r[4] or 0),
                    "credit": float(r[5] or 0),
                    "property_id": r[7] or None,
                    "vendor_id": r[9] or None,
                }
            )
        return lines

    def _find_account_text(self, account_id, account_code):
        if account_id is not None:
            for text, payload in self.account_data.items():
                if payload.get("id") == account_id:
                    return text
        code = str(account_code or "").strip()
        for text, payload in self.account_data.items():
            if payload.get("code") == code:
                return text
        return ""

    def _find_combo_text(self, data_map, record_id):
        if not record_id:
            return ""
        for text, payload in data_map.items():
            if payload["id"] == record_id:
                return text
        return ""

    def _load_lines_to_ui(self, lines):
        self.entry_lines.clear()
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        for raw in lines:
            acc_text = self._find_account_text(raw.get("account_id"), raw.get("account_code"))
            prop_text = self._find_combo_text(self.property_data, raw.get("property_id"))
            ven_text = self._find_combo_text(self.vendor_data, raw.get("vendor_id"))

            acc_payload = self.account_data.get(acc_text, {"id": raw.get("account_id"), "code": raw.get("account_code", ""), "name": raw.get("account_name", "")})

            line = {
                "account_id": acc_payload.get("id"),
                "account_code": acc_payload.get("code") or raw.get("account_code", ""),
                "account_name": acc_payload.get("name") or raw.get("account_name", ""),
                "account_text": acc_text,
                "description": raw.get("description", ""),
                "debit": float(raw.get("debit", 0) or 0),
                "credit": float(raw.get("credit", 0) or 0),
                "property_id": raw.get("property_id"),
                "property_name": "",
                "property_text": prop_text,
                "vendor_id": raw.get("vendor_id"),
                "vendor_name": "",
                "vendor_text": ven_text,
            }

            iid = self.tree.insert("", "end", values=self._format_line_values(line))
            line["_iid"] = iid
            self.entry_lines.append(line)

        self._apply_tree_striping()
        self._clear_line_form()
        self._refresh_totals_status()

    def _search_voucher(self):
        voucher_id = simpledialog.askstring("بحث", "أدخل رقم السند:", parent=self.master)
        if not voucher_id:
            return
        if not voucher_id.isdigit():
            return messagebox.showwarning("تنبيه", "رقم السند يجب أن يكون رقمًا")

        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            cur.execute("SELECT id, v_date, COALESCE(description, '') FROM finance.vouchers WHERE id=%s", (voucher_id,))

            header = cur.fetchone()
            if not header:
                return messagebox.showinfo("بحث", "لم يتم العثور على السند")

            self.current_voucher_id = int(header[0])
            self.voucher_id_var.set(str(header[0]))
            self.voucher_date_var.set(str(header[1]))

            self.txt_general_desc.delete("1.0", END)
            self.txt_general_desc.insert("1.0", header[2] or "")

            lines = self._fetch_ledger_lines(cur, header[0])
            self._load_lines_to_ui(lines)

            self._set_header_button_states()
            self._refresh_totals_status()
        except Exception as e:
            messagebox.showerror("خطأ", get_db_error_message(e, "تعذر جلب القيد"))
        finally:
            conn.close()

    def _exit_screen(self):
        try:
            self.frame.destroy()
        except Exception:
            self.master.destroy()


if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    root.title("Adjustment Journal Entry")
    root.geometry("1380x920")
    AdjustmentJournalEntryScreen(root)
    root.mainloop()

