import tkinter as tk
from tkinter import messagebox, ttk

import ttkbootstrap as tb

from combobox_helper import bind_searchable_combobox, set_combobox_values
from db_connection import get_connection, get_db_error_message


class PropertyScreen:
    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.bg_color = "#f4f7f6"

        self.account_display_map = {}

        self._setup_styles()

        self.frame = tb.Frame(master, style="App.Property.Root.TFrame", padding=12)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.main_card = tb.Frame(self.frame, style="App.Property.Card.TFrame", padding=14)
        self.main_card.pack(fill="both", expand=True)

        self.arabic_font = ("Segoe UI", 12, "bold")

        self.form_row = tb.Frame(self.main_card, style="App.Property.Card.TFrame")
        self.form_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        for col in (0, 2, 4):
            self.form_row.columnconfigure(col, weight=1)

        self.label_name = tb.Label(self.form_row, text="اسم العقار", style="App.Property.FieldLabel.TLabel", anchor="e")
        self.label_name.grid(row=0, column=1, sticky="e", padx=8, pady=8)
        self.entry_name = tb.Entry(self.form_row, font=self.arabic_font, justify="right", style="App.Property.Field.TEntry")
        self.entry_name.grid(row=0, column=0, padx=8, pady=8, sticky="ew")

        self.label_price = tb.Label(self.form_row, text="سعر الشراء", style="App.Property.FieldLabel.TLabel", anchor="e")
        self.label_price.grid(row=0, column=3, sticky="e", padx=8, pady=8)
        self.entry_price = tb.Entry(self.form_row, font=self.arabic_font, justify="right", style="App.Property.Field.TEntry")
        self.entry_price.grid(row=0, column=2, padx=8, pady=8, sticky="ew")

        self.label_account = tb.Label(self.form_row, text="حساب العقار", style="App.Property.FieldLabel.TLabel", anchor="e")
        self.label_account.grid(row=0, column=5, sticky="e", padx=8, pady=8)
        self.combo_account = ttk.Combobox(self.form_row, justify="right", font=self.arabic_font, state="readonly")
        self.combo_account.grid(row=0, column=4, padx=8, pady=8, sticky="ew")
        bind_searchable_combobox(self.combo_account)

        self.account_code_var = tk.StringVar(value="")
        self.label_account_code = tb.Label(self.form_row, text="كود الحساب", style="App.Property.FieldLabel.TLabel", anchor="e")
        self.label_account_code.grid(row=1, column=1, sticky="e", padx=8, pady=8)
        self.entry_account_code = tb.Entry(
            self.form_row,
            font=self.arabic_font,
            justify="right",
            style="App.Property.Field.TEntry",
            textvariable=self.account_code_var,
            state="readonly",
        )
        self.entry_account_code.grid(row=1, column=0, padx=8, pady=8, sticky="ew")

        self.combo_account.bind("<<ComboboxSelected>>", self._on_account_selected)

        self.save_button = tb.Button(self.main_card, text="حفظ", style="App.Property.Action.TButton", command=self.save_property)
        self.save_button.grid(row=1, column=0, columnspan=2, pady=(0, 12), sticky="e")

        columns = ("id", "property_name", "purchase_price", "total_cost", "account_code", "status")
        table_wrap = tb.Frame(self.main_card, style="App.Property.Card.TFrame")
        table_wrap.grid(row=2, column=0, columnspan=2, sticky="nsew")
        table_wrap.rowconfigure(0, weight=1)
        table_wrap.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=12, style="App.Property.Treeview")
        self.tree.heading("id", text="ID", anchor="e")
        self.tree.heading("property_name", text="اسم العقار", anchor="e")
        self.tree.heading("purchase_price", text="سعر الشراء", anchor="e")
        self.tree.heading("total_cost", text="التكلفة الكلية", anchor="e")
        self.tree.heading("account_code", text="كود الحساب", anchor="e")
        self.tree.heading("status", text="الحالة", anchor="e")
        self.tree.column("id", anchor="e", width=60)
        self.tree.column("property_name", anchor="e", width=210)
        self.tree.column("purchase_price", anchor="e", width=130)
        self.tree.column("total_cost", anchor="e", width=130)
        self.tree.column("account_code", anchor="e", width=120)
        self.tree.column("status", anchor="e", width=100)

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", style="App.Property.Vertical.TScrollbar", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_wrap, orient="horizontal", style="App.Property.Horizontal.TScrollbar", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        self.tree.tag_configure("odd", background="#ffffff")
        self.tree.tag_configure("even", background="#f0f3f5")

        self.main_card.grid_rowconfigure(2, weight=1)
        self.main_card.grid_columnconfigure(0, weight=1)
        self.main_card.grid_columnconfigure(1, weight=1)

        self.refresh_account_choices()
        self.refresh_data()

    def _setup_styles(self):
        style = tb.Style()
        style.configure("App.Property.Root.TFrame", background=self.bg_color)
        style.configure("App.Property.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("App.Property.FieldLabel.TLabel", background="white", foreground=self.primary_color, font=("Segoe UI", 12, "bold"))
        style.configure("App.Property.Field.TEntry", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 12, "bold"))
        style.configure("App.Property.Action.TButton", background="#27ae60", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.map("App.Property.Action.TButton", background=[("active", self.accent_color), ("pressed", self.accent_color)], foreground=[("active", "white"), ("pressed", "white")])
        style.configure("App.Property.Treeview", rowheight=30, font=("Segoe UI", 10), background="white", fieldbackground="white", foreground=self.primary_color)
        style.configure("App.Property.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.primary_color, foreground="white")
        style.map("App.Property.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "white")])
        style.map("App.Property.Treeview.Heading", background=[("active", self.primary_color), ("pressed", self.primary_color)], foreground=[("active", "white"), ("pressed", "white")])
        style.configure("App.Property.Vertical.TScrollbar", background=self.sidebar_color, troughcolor=self.bg_color, arrowcolor=self.primary_color)
        style.configure("App.Property.Horizontal.TScrollbar", background=self.sidebar_color, troughcolor=self.bg_color, arrowcolor=self.primary_color)

    def _on_account_selected(self, _event=None):
        display = self.combo_account.get().strip()
        self.account_code_var.set(self.account_display_map.get(display, ""))

    def refresh_account_choices(self):
        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT account_code, account_name
                        FROM finance.accounts
                        WHERE is_active = true
                          AND account_level = 'تحليلي'
                          AND (parent_code = '1111' OR account_code LIKE '1111%')
                        ORDER BY account_code
                        """
                    )
                    rows = cur.fetchall() or []

            displays = []
            self.account_display_map = {}
            for code, name in rows:
                code_text = (str(code or "")).strip()
                name_text = (name or "").strip()
                if not code_text:
                    continue
                display = f"{code_text} - {name_text}" if name_text else code_text
                displays.append(display)
                self.account_display_map[display] = code_text

            set_combobox_values(self.combo_account, displays)
            if displays and not self.combo_account.get().strip():
                self.combo_account.set(displays[0])
                self._on_account_selected()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل حسابات العقارات"))
        finally:
            conn.close()

    def save_property(self):
        name = self.entry_name.get().strip()
        price = self.entry_price.get().strip()
        account_code = self.account_code_var.get().strip()

        if not name or not price or not account_code:
            messagebox.showerror("خطأ", "يرجى إدخال اسم العقار وسعر الشراء واختيار الحساب")
            return

        try:
            price_val = float(price.replace(",", ""))
        except ValueError:
            messagebox.showerror("خطأ", "سعر الشراء يجب أن يكون رقمًا")
            return

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO finance.properties (property_name, purchase_price, total_cost, status, account_code)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (name, price_val, price_val, "نشط", account_code),
                    )
            messagebox.showinfo("تم الحفظ", "تم إضافة العقار بنجاح")
            self.entry_name.delete(0, tk.END)
            self.entry_price.delete(0, tk.END)
            self.refresh_data()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ العقار"))
        finally:
            conn.close()

    def refresh_data(self):
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, property_name, purchase_price, total_cost, account_code, status
                        FROM finance.properties
                        ORDER BY id DESC
                        """
                    )
                    rows = cur.fetchall() or []

            for idx, row in enumerate(rows):
                tag = "even" if idx % 2 == 0 else "odd"
                safe_row = tuple("" if value is None else value for value in row)
                self.tree.insert("", tk.END, values=safe_row, tags=(tag,))
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل بيانات العقارات"))
        finally:
            conn.close()
