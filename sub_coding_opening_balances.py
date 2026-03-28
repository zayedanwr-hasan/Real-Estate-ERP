import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import ttkbootstrap as tb

from combobox_helper import bind_searchable_combobox, set_combobox_values
from db_connection import get_connection, get_db_error_message


class SubCodingOpeningBalances:
    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.accent_color = "#1abc9c"
        self.bg_color = "#f4f7f6"

        self.selected_property_id = None
        self.selected_vendor_id = None

        self.group_display_to_id = {}
        self.property_display_to_id = {}

        self._setup_styles()
        self._build_layout()
        self._refresh_all_data()

    def _setup_styles(self):
        style = tb.Style()
        style.configure("Sub.Root.TFrame", background=self.bg_color)
        style.configure("Sub.Header.TFrame", background=self.primary_color)
        style.configure("Sub.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 16, "bold"))
        style.configure("Sub.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("Sub.Treeview", rowheight=30, font=("Segoe UI", 10), background="white", fieldbackground="white")
        style.configure("Sub.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.primary_color, foreground="white")
        style.map("Sub.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "white")])

    def _build_layout(self):
        self.frame = tb.Frame(self.master, style="Sub.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        header = tb.Frame(self.frame, style="Sub.Header.TFrame", padding=10)
        header.pack(fill="x")
        tb.Label(header, text="إدارة العقارات والموردين", style="Sub.Header.TLabel").pack(side="right")

        actions = tb.Frame(header, style="Sub.Header.TFrame")
        actions.pack(side="left")
        for title, action in (
            ("جديد", self._action_new),
            ("حفظ", self._action_save),
            ("تعديل", self._action_edit),
            ("حذف", self._action_delete),
            ("بحث", self._action_search),
        ):
            tb.Button(actions, text=title, command=action).pack(side="left", padx=3)

        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_properties = tb.Frame(self.notebook, style="Sub.Root.TFrame", padding=10)
        self.tab_vendors = tb.Frame(self.notebook, style="Sub.Root.TFrame", padding=10)
        self.notebook.add(self.tab_properties, text="العقارات")
        self.notebook.add(self.tab_vendors, text="الموردون")

        self._build_properties_tab()
        self._build_vendors_tab()

    def _build_properties_tab(self):
        self.tab_properties.columnconfigure(0, weight=2)
        self.tab_properties.columnconfigure(1, weight=1)
        self.tab_properties.rowconfigure(0, weight=1)

        table_card = tb.Frame(self.tab_properties, style="Sub.Card.TFrame", padding=8)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        form_card = tb.Frame(self.tab_properties, style="Sub.Card.TFrame", padding=8)
        form_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        form_card.columnconfigure(0, weight=1)

        self.property_tree = ttk.Treeview(table_card, columns=("id", "name", "price", "account"), show="headings", style="Sub.Treeview")
        for c, t, w in (("id", "ID", 60), ("name", "اسم العقار", 220), ("price", "سعر الشراء", 120), ("account", "كود الحساب", 120)):
            self.property_tree.heading(c, text=t, anchor="e")
            self.property_tree.column(c, width=w, anchor="e")
        self.property_tree.pack(fill="both", expand=True)
        self.property_tree.bind("<<TreeviewSelect>>", self._on_property_select)

        self.p_name = self._make_labeled_entry(form_card, "اسم العقار", 0)
        self.p_price = self._make_labeled_entry(form_card, "سعر الشراء", 2)
        self.p_account_code = self._make_labeled_entry(form_card, "كود الحساب", 4, readonly=True)

        ttk.Label(form_card, text="الحساب", anchor="e").grid(row=6, column=0, sticky="e", pady=(8, 4))
        self.p_account_combo = ttk.Combobox(form_card, state="readonly", justify="right")
        self.p_account_combo.grid(row=7, column=0, sticky="ew")
        bind_searchable_combobox(self.p_account_combo)
        self.p_account_combo.bind("<<ComboboxSelected>>", self._on_property_account_selected)

    def _build_vendors_tab(self):
        self.tab_vendors.columnconfigure(0, weight=2)
        self.tab_vendors.columnconfigure(1, weight=1)
        self.tab_vendors.rowconfigure(0, weight=1)

        table_card = tb.Frame(self.tab_vendors, style="Sub.Card.TFrame", padding=8)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        form_card = tb.Frame(self.tab_vendors, style="Sub.Card.TFrame", padding=8)
        form_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        form_card.columnconfigure(0, weight=1)

        self.vendor_tree = ttk.Treeview(table_card, columns=("id", "name", "group", "property", "account"), show="headings", style="Sub.Treeview")
        for c, t, w in (("id", "ID", 60), ("name", "اسم المورد", 180), ("group", "المجموعة", 170), ("property", "العقار", 170), ("account", "كود الحساب", 120)):
            self.vendor_tree.heading(c, text=t, anchor="e")
            self.vendor_tree.column(c, width=w, anchor="e")
        self.vendor_tree.pack(fill="both", expand=True)
        self.vendor_tree.bind("<<TreeviewSelect>>", self._on_vendor_select)

        self.v_name = self._make_labeled_entry(form_card, "اسم المورد", 0)

        ttk.Label(form_card, text="مجموعة المورد", anchor="e").grid(row=2, column=0, sticky="e", pady=(8, 4))
        self.v_group_combo = ttk.Combobox(form_card, state="readonly", justify="right")
        self.v_group_combo.grid(row=3, column=0, sticky="ew")
        bind_searchable_combobox(self.v_group_combo)

        tb.Button(form_card, text="إضافة مجموعة", command=self._open_add_group_dialog).grid(row=4, column=0, sticky="ew", pady=(8, 6))

        ttk.Label(form_card, text="العقار", anchor="e").grid(row=5, column=0, sticky="e", pady=(8, 4))
        self.v_property_combo = ttk.Combobox(form_card, state="readonly", justify="right")
        self.v_property_combo.grid(row=6, column=0, sticky="ew")
        bind_searchable_combobox(self.v_property_combo)

        self.v_account_code = self._make_labeled_entry(form_card, "كود الحساب", 8, readonly=True)

    def _make_labeled_entry(self, parent, label_text, row, readonly=False):
        ttk.Label(parent, text=label_text, anchor="e").grid(row=row, column=0, sticky="e", pady=(8, 4))
        entry = ttk.Entry(parent, justify="right")
        entry.grid(row=row + 1, column=0, sticky="ew")
        if readonly:
            entry.configure(state="readonly")
        return entry

    def _set_entry(self, entry, value):
        was_readonly = str(entry.cget("state")) == "readonly"
        if was_readonly:
            entry.configure(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, value)
        if was_readonly:
            entry.configure(state="readonly")

    def _on_property_account_selected(self, _event=None):
        display = self.p_account_combo.get().strip()
        code = display.split(" - ", 1)[0].strip() if display else ""
        self._set_entry(self.p_account_code, code)

    def _refresh_all_data(self):
        self._load_group_choices()
        self._load_property_choices()
        self._load_property_rows()
        self._load_vendor_rows()

    def _load_group_choices(self):
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, group_name, account_code FROM finance.vendor_groups ORDER BY group_name")
                    rows = cur.fetchall() or []
            values = []
            self.group_display_to_id = {}
            for group_id, group_name, account_code in rows:
                display = f"{str(account_code or '').strip()} - {(group_name or '').strip()}".strip(" -")
                if display:
                    values.append(display)
                    self.group_display_to_id[display] = int(group_id)
            set_combobox_values(self.v_group_combo, values)
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل مجموعات الموردين"))
        finally:
            conn.close()

    def _load_property_choices(self):
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, property_name, account_code FROM finance.properties ORDER BY property_name")
                    property_rows = cur.fetchall() or []
                    cur.execute(
                        """
                        SELECT account_code, account_name
                        FROM finance.accounts
                        WHERE account_level = 'تحليلي'
                          AND is_active = true
                          AND (parent_code = '1111' OR account_code LIKE '1111%')
                        ORDER BY account_code
                        """
                    )
                    account_rows = cur.fetchall() or []

            property_values = []
            self.property_display_to_id = {}
            for property_id, property_name, account_code in property_rows:
                display = f"{str(account_code or '').strip()} - {(property_name or '').strip()}".strip(" -")
                if display:
                    property_values.append(display)
                    self.property_display_to_id[display] = int(property_id)

            account_values = []
            for account_code, account_name in account_rows:
                code = str(account_code or "").strip()
                name = (account_name or "").strip()
                if code:
                    account_values.append(f"{code} - {name}" if name else code)

            set_combobox_values(self.v_property_combo, property_values)
            set_combobox_values(self.p_account_combo, account_values)
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل خيارات العقار والحساب"))
        finally:
            conn.close()

    def _load_property_rows(self):
        self.property_tree.delete(*self.property_tree.get_children())
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, property_name, purchase_price, account_code FROM finance.properties ORDER BY id DESC")
                    rows = cur.fetchall() or []
            for row in rows:
                self.property_tree.insert("", tk.END, iid=str(row[0]), values=tuple("" if value is None else value for value in row))
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل العقارات"))
        finally:
            conn.close()

    def _load_vendor_rows(self):
        self.vendor_tree.delete(*self.vendor_tree.get_children())
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            v.id,
                            v.vendor_name,
                            g.group_name,
                            p.property_name,
                            v.account_code
                        FROM finance.vendors v
                        LEFT JOIN finance.vendor_groups g ON v.group_id = g.id
                        LEFT JOIN finance.properties p ON v.property_id = p.id
                        ORDER BY v.id DESC
                        """
                    )
                    rows = cur.fetchall() or []
            for row in rows:
                self.vendor_tree.insert("", tk.END, iid=str(row[0]), values=tuple("" if value is None else value for value in row))
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل الموردين"))
        finally:
            conn.close()

    def _save_property(self):
        name = self.p_name.get().strip()
        account_code = self.p_account_code.get().strip()
        try:
            purchase_price = float((self.p_price.get().strip() or "0").replace(",", ""))
        except ValueError:
            messagebox.showwarning("تنبيه", "سعر الشراء يجب أن يكون رقماً")
            return

        if not name or not account_code:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم العقار واختيار الحساب")
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
                        (name, purchase_price, purchase_price, "نشط", account_code),
                    )
            messagebox.showinfo("نجاح", "تم حفظ العقار")
            self._action_new()
            self._refresh_all_data()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ العقار"))
        finally:
            conn.close()

    def _save_vendor(self):
        vendor_name = self.v_name.get().strip()
        group_id = self.group_display_to_id.get(self.v_group_combo.get().strip())
        property_id = self.property_display_to_id.get(self.v_property_combo.get().strip())

        if not vendor_name or group_id is None:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم المورد واختيار المجموعة")
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO finance.vendors (vendor_name, group_id, property_id) VALUES (%s, %s, %s)",
                        (vendor_name, group_id, property_id),
                    )
            messagebox.showinfo("نجاح", "تم حفظ المورد")
            self._action_new()
            self._refresh_all_data()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ المورد"))
        finally:
            conn.close()

    def _edit_property(self):
        if not self.selected_property_id:
            messagebox.showwarning("تنبيه", "اختر عقاراً للتعديل")
            return

        name = self.p_name.get().strip()
        account_code = self.p_account_code.get().strip()
        try:
            purchase_price = float((self.p_price.get().strip() or "0").replace(",", ""))
        except ValueError:
            messagebox.showwarning("تنبيه", "سعر الشراء يجب أن يكون رقماً")
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE finance.properties
                        SET property_name=%s, purchase_price=%s, total_cost=%s, account_code=%s
                        WHERE id=%s
                        """,
                        (name, purchase_price, purchase_price, account_code, self.selected_property_id),
                    )
            messagebox.showinfo("نجاح", "تم تعديل العقار")
            self._refresh_all_data()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل العقار"))
        finally:
            conn.close()

    def _edit_vendor(self):
        if not self.selected_vendor_id:
            messagebox.showwarning("تنبيه", "اختر مورداً للتعديل")
            return

        vendor_name = self.v_name.get().strip()
        group_id = self.group_display_to_id.get(self.v_group_combo.get().strip())
        property_id = self.property_display_to_id.get(self.v_property_combo.get().strip())

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE finance.vendors SET vendor_name=%s, group_id=%s, property_id=%s WHERE id=%s",
                        (vendor_name, group_id, property_id, self.selected_vendor_id),
                    )
            messagebox.showinfo("نجاح", "تم تعديل المورد")
            self._refresh_all_data()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل المورد"))
        finally:
            conn.close()

    def _delete_property(self):
        if not self.selected_property_id:
            messagebox.showwarning("تنبيه", "اختر عقاراً للحذف")
            return
        if not messagebox.askyesno("تأكيد", "هل تريد حذف العقار المحدد؟"):
            return
        self._delete_by_id("finance.properties", self.selected_property_id, "فشل حذف العقار")
        self._action_new()
        self._refresh_all_data()

    def _delete_vendor(self):
        if not self.selected_vendor_id:
            messagebox.showwarning("تنبيه", "اختر مورداً للحذف")
            return
        if not messagebox.askyesno("تأكيد", "هل تريد حذف المورد المحدد؟"):
            return
        self._delete_by_id("finance.vendors", self.selected_vendor_id, "فشل حذف المورد")
        self._action_new()
        self._refresh_all_data()

    def _delete_by_id(self, table_name, item_id, error_prefix):
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(f"DELETE FROM {table_name} WHERE id=%s", (item_id,))
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, error_prefix))
        finally:
            conn.close()

    def _on_property_select(self, _event=None):
        selected = self.property_tree.selection()
        if not selected:
            return
        row = self.property_tree.item(selected[0], "values")
        if not row:
            return
        self.selected_property_id = int(row[0])
        self.p_name.delete(0, tk.END)
        self.p_name.insert(0, row[1] or "")
        self.p_price.delete(0, tk.END)
        self.p_price.insert(0, row[2] or "")

        code = (row[3] or "").strip()
        self._set_entry(self.p_account_code, code)
        for value in self.p_account_combo["values"]:
            if str(value).startswith(f"{code} -") or str(value) == code:
                self.p_account_combo.set(value)
                break

    def _on_vendor_select(self, _event=None):
        selected = self.vendor_tree.selection()
        if not selected:
            return
        row = self.vendor_tree.item(selected[0], "values")
        if not row:
            return
        self.selected_vendor_id = int(row[0])

        self.v_name.delete(0, tk.END)
        self.v_name.insert(0, row[1] or "")
        self._set_entry(self.v_account_code, str(row[4] or ""))

        group_name = (row[2] or "").strip()
        for value in self.v_group_combo["values"]:
            if str(value).endswith(f"- {group_name}") or str(value) == group_name:
                self.v_group_combo.set(value)
                break

        property_name = (row[3] or "").strip()
        for value in self.v_property_combo["values"]:
            if str(value).endswith(f"- {property_name}") or str(value) == property_name:
                self.v_property_combo.set(value)
                break

    def _open_add_group_dialog(self):
        group_name = simpledialog.askstring("إضافة مجموعة", "اسم مجموعة الموردين:", parent=self.master)
        group_name = (group_name or "").strip()
        if not group_name:
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO finance.vendor_groups (group_name) VALUES (%s)", (group_name,))
            self._load_group_choices()
            messagebox.showinfo("نجاح", "تمت إضافة المجموعة")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل إضافة مجموعة الموردين"))
        finally:
            conn.close()

    def _action_new(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self.selected_property_id = None
            self.p_name.delete(0, tk.END)
            self.p_price.delete(0, tk.END)
            self.p_account_combo.set("")
            self._set_entry(self.p_account_code, "")
        else:
            self.selected_vendor_id = None
            self.v_name.delete(0, tk.END)
            self.v_group_combo.set("")
            self.v_property_combo.set("")
            self._set_entry(self.v_account_code, "")

    def _action_save(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._save_property()
        else:
            self._save_vendor()

    def _action_edit(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._edit_property()
        else:
            self._edit_vendor()

    def _action_delete(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._delete_property()
        else:
            self._delete_vendor()

    def _action_search(self):
        query = simpledialog.askstring("بحث", "أدخل كلمة البحث:", parent=self.master)
        text = (query or "").strip().lower()
        if not text:
            self._refresh_all_data()
            return

        active_tree = self.property_tree if self.notebook.index(self.notebook.select()) == 0 else self.vendor_tree
        for iid in active_tree.get_children():
            values = active_tree.item(iid, "values")
            if text in " ".join(str(v or "").lower() for v in values):
                active_tree.selection_set(iid)
                active_tree.see(iid)
                active_tree.focus(iid)
                return
        messagebox.showinfo("بحث", "لا توجد نتائج")

    def _build_properties_tab(self):
        self.tab_properties.columnconfigure(0, weight=2)
        self.tab_properties.columnconfigure(1, weight=1)
        self.tab_properties.rowconfigure(0, weight=1)

        table_card = tb.Frame(self.tab_properties, style="App.Sub.Card.TFrame", padding=10)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        table_card.rowconfigure(0, weight=1)
        table_card.columnconfigure(0, weight=1)

        columns = ("id", "property_name", "purchase_price", "account_code")
        self.property_tree = ttk.Treeview(table_card, columns=columns, show="headings", style="App.Sub.Treeview")
        self.property_tree.heading("id", text="ID", anchor="e")
        self.property_tree.heading("property_name", text="اسم العقار", anchor="e")
        self.property_tree.heading("purchase_price", text="سعر الشراء", anchor="e")
        self.property_tree.heading("account_code", text="كود الحساب", anchor="e")
        self.property_tree.column("id", width=60, anchor="e")
        self.property_tree.column("property_name", width=240, anchor="e")
        self.property_tree.column("purchase_price", width=130, anchor="e")
        self.property_tree.column("account_code", width=120, anchor="e")
        self.property_tree.grid(row=0, column=0, sticky="nsew")
        self.property_tree.bind("<<TreeviewSelect>>", self._on_property_select)

        form_card = tb.Frame(self.tab_properties, style="App.Sub.Card.TFrame", padding=10)
        form_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        form_card.columnconfigure(0, weight=1)

        self.p_name = self._make_labeled_entry(form_card, "اسم العقار", 0)
        self.p_price = self._make_labeled_entry(form_card, "سعر الشراء", 2)
        self.p_account_code = self._make_labeled_entry(form_card, "كود الحساب", 4, readonly=True)

        ttk.Label(form_card, text="حساب العقار", style="App.Sub.FieldLabel.TLabel").grid(row=6, column=0, sticky="e", pady=(8, 4))
        self.p_account_combo = ttk.Combobox(form_card, state="readonly", justify="right", font=("Segoe UI", 11, "bold"))
        self.p_account_combo.grid(row=7, column=0, sticky="ew")
        bind_searchable_combobox(self.p_account_combo)
        self.p_account_combo.bind("<<ComboboxSelected>>", self._on_property_account_selected)

    def _build_vendors_tab(self):
        self.tab_vendors.columnconfigure(0, weight=2)
        self.tab_vendors.columnconfigure(1, weight=1)
        self.tab_vendors.rowconfigure(0, weight=1)

        table_card = tb.Frame(self.tab_vendors, style="App.Sub.Card.TFrame", padding=10)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        table_card.rowconfigure(0, weight=1)
        table_card.columnconfigure(0, weight=1)

        columns = ("id", "vendor_name", "group_name", "property_name", "account_code")
        self.vendor_tree = ttk.Treeview(table_card, columns=columns, show="headings", style="App.Sub.Treeview")
        self.vendor_tree.heading("id", text="ID", anchor="e")
        self.vendor_tree.heading("vendor_name", text="اسم المورد", anchor="e")
        self.vendor_tree.heading("group_name", text="المجموعة", anchor="e")
        self.vendor_tree.heading("property_name", text="العقار", anchor="e")
        self.vendor_tree.heading("account_code", text="كود الحساب", anchor="e")
        self.vendor_tree.column("id", width=60, anchor="e")
        self.vendor_tree.column("vendor_name", width=210, anchor="e")
        self.vendor_tree.column("group_name", width=180, anchor="e")
        self.vendor_tree.column("property_name", width=180, anchor="e")
        self.vendor_tree.column("account_code", width=130, anchor="e")
        self.vendor_tree.grid(row=0, column=0, sticky="nsew")
        self.vendor_tree.bind("<<TreeviewSelect>>", self._on_vendor_select)

        form_card = tb.Frame(self.tab_vendors, style="App.Sub.Card.TFrame", padding=10)
        form_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        form_card.columnconfigure(0, weight=1)

        self.v_name = self._make_labeled_entry(form_card, "اسم المورد", 0)

        ttk.Label(form_card, text="مجموعة المورد", style="App.Sub.FieldLabel.TLabel").grid(row=2, column=0, sticky="e", pady=(8, 4))
        self.v_group_combo = ttk.Combobox(form_card, state="readonly", justify="right", font=("Segoe UI", 11, "bold"))
        self.v_group_combo.grid(row=3, column=0, sticky="ew")
        bind_searchable_combobox(self.v_group_combo)

        tb.Button(form_card, text="إضافة مجموعة", style="App.Sub.Primary.TButton", command=self._open_add_group_dialog).grid(row=4, column=0, sticky="ew", pady=(8, 6))

        ttk.Label(form_card, text="العقار", style="App.Sub.FieldLabel.TLabel").grid(row=5, column=0, sticky="e", pady=(8, 4))
        self.v_property_combo = ttk.Combobox(form_card, state="readonly", justify="right", font=("Segoe UI", 11, "bold"))
        self.v_property_combo.grid(row=6, column=0, sticky="ew")
        bind_searchable_combobox(self.v_property_combo)

        self.v_account_code = self._make_labeled_entry(form_card, "كود حساب المورد", 8, readonly=True)

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

    def _refresh_group_choices(self):
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, group_name, account_code
                        FROM finance.vendor_groups
                        ORDER BY group_name
                        """
                    )
                    rows = cur.fetchall() or []

            values = []
            self.group_display_to_id = {}
            for group_id, group_name, account_code in rows:
                safe_name = (group_name or "").strip()
                safe_code = (str(account_code or "")).strip()
                display = f"{safe_code} - {safe_name}" if safe_code else safe_name
                if not display:
                    continue
                values.append(display)
                self.group_display_to_id[display] = int(group_id)

            set_combobox_values(self.v_group_combo, values)
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل مجموعات الموردين"))
        finally:
            conn.close()

    def _refresh_property_choices(self):
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, property_name, account_code
                        FROM finance.properties
                        ORDER BY property_name
                        """
                    )
                    property_rows = cur.fetchall() or []

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
                    account_rows = cur.fetchall() or []

            property_values = []
            self.property_display_to_id = {}
            for property_id, property_name, account_code in property_rows:
                safe_name = (property_name or "").strip()
                safe_code = (str(account_code or "")).strip()
                display = f"{safe_code} - {safe_name}" if safe_code else safe_name
                if not display:
                    continue
                property_values.append(display)
                self.property_display_to_id[display] = int(property_id)

            account_values = []
            for account_code, account_name in account_rows:
                safe_code = (str(account_code or "")).strip()
                safe_name = (account_name or "").strip()
                if not safe_code:
                    continue
                account_values.append(f"{safe_code} - {safe_name}" if safe_name else safe_code)

            set_combobox_values(self.v_property_combo, property_values)
            set_combobox_values(self.p_account_combo, account_values)
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل خيارات العقارات والحسابات"))
        finally:
            conn.close()

    def _refresh_properties_table(self):
        self.property_tree.delete(*self.property_tree.get_children())
        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, property_name, purchase_price, account_code
                        FROM finance.properties
                        ORDER BY id DESC
                        """
                    )
                    rows = cur.fetchall() or []

            if not rows:
                self.property_tree.insert("", tk.END, values=("", "لا توجد بيانات", "", ""))
                return

            for idx, row in enumerate(rows):
                safe = tuple("" if value is None else value for value in row)
                tag = "even" if idx % 2 == 0 else "odd"
                self.property_tree.insert("", tk.END, iid=str(row[0]), values=safe, tags=(tag,))
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل بيانات العقارات"))
        finally:
            conn.close()

    def _refresh_vendors_table(self):
        self.vendor_tree.delete(*self.vendor_tree.get_children())
        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            v.id,
                            v.vendor_name,
                            g.group_name,
                            p.property_name,
                            v.account_code
                        FROM finance.vendors v
                        LEFT JOIN finance.vendor_groups g ON v.group_id = g.id
                        LEFT JOIN finance.properties p ON v.property_id = p.id
                        ORDER BY v.id DESC
                        """
                    )
                    rows = cur.fetchall() or []

            if not rows:
                self.vendor_tree.insert("", tk.END, values=("", "لا توجد بيانات", "", "", ""))
                return

            for idx, row in enumerate(rows):
                safe = tuple("" if value is None else value for value in row)
                tag = "even" if idx % 2 == 0 else "odd"
                self.vendor_tree.insert("", tk.END, iid=str(row[0]), values=safe, tags=(tag,))
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل بيانات الموردين"))
        finally:
            conn.close()

    def _refresh_all_data(self):
        self._refresh_group_choices()
        self._refresh_property_choices()
        self._refresh_properties_table()
        self._refresh_vendors_table()

    def _get_selected_group_id(self):
        display = self.v_group_combo.get().strip()
        if not display:
            return None
        return self.group_display_to_id.get(display)

    def _get_selected_property_id(self):
        display = self.v_property_combo.get().strip()
        if not display:
            return None
        return self.property_display_to_id.get(display)

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

        area_val = area if area else None
        ok = self.execute_query(
            "INSERT INTO finance.properties (property_name, total_cost, purchase_price, location) VALUES (%s, %s, %s, %s)",
            (name, cost_val, area_val, loc),
            error_prefix="فشل حفظ بيانات العقار",
        )
        if not ok:
            return

        messagebox.showinfo("نجاح", "تم حفظ العقار")
        self._clear_plot_form()
        self._refresh_all_data()

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

        selected_account_code = self._get_selected_vendor_account_code()

        def _save_vendor_tx(cur):
            credit_account_code = self._resolve_opening_credit_account_code(cur)
            cur.execute(
                "INSERT INTO finance.vendors (vendor_name, group_name, property_id) VALUES (%s, %s, %s) RETURNING id",
                (name, group, property_id),
            )
            v_id = cur.fetchone()[0]

            if bal > 0:
                if not self._validate_opening_v_type(self.allowed_opening_v_type):
                    raise Exception("قيمة نوع القيد غير صالحة")

                cur.execute(
                    "INSERT INTO finance.vouchers (v_type, v_date, description) VALUES (%s, CURRENT_DATE, %s) RETURNING id",
                    (self.allowed_opening_v_type, f"رصيد أول المدة: {name}"),
                )
                voc_id = cur.fetchone()[0]

                cur.execute(
                    "INSERT INTO finance.ledger (voucher_id, account_code, vendor_id, property_id, debit) VALUES (%s, %s, %s, %s, %s)",
                    (voc_id, selected_account_code, v_id, property_id, bal),
                )
                cur.execute(
                    "INSERT INTO finance.ledger (voucher_id, account_code, credit) VALUES (%s, %s, %s)",
                    (voc_id, credit_account_code, bal),
                )

            return v_id

        saved_vendor_id = self.execute_transaction(_save_vendor_tx, error_prefix="فشل حفظ بيانات الوارث")
        if not saved_vendor_id:
            return

        messagebox.showinfo("نجاح", "تم الحفظ")
        self._clear_vendor_form()
        self._refresh_all_data()

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

        area_val = area if area else None
        ok = self.execute_query(
            "UPDATE finance.properties SET property_name=%s, total_cost=%s, purchase_price=%s, location=%s WHERE id=%s",
            (name, cost_val, area_val, loc, self.selected_plot_id),
            error_prefix="فشل حفظ بيانات العقار",
        )
        if not ok:
            return

        messagebox.showinfo("نجاح", "تم تعديل بيانات العقار")
        self._clear_plot_form()
        self._refresh_all_data()

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

        selected_account_code = self._get_selected_vendor_account_code()

        def _edit_vendor_tx(cur):
            credit_account_code = self._resolve_opening_credit_account_code(cur)
            cur.execute(
                "UPDATE finance.vendors SET vendor_name=%s, group_name=%s, property_id=%s WHERE id=%s",
                (name, group, property_id, self.selected_vendor_id),
            )

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
                    raise Exception("قيمة نوع القيد غير صالحة")

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
                    raise Exception("قيمة نوع القيد غير صالحة")

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
            return True

        ok = self.execute_transaction(_edit_vendor_tx, error_prefix="فشل تعديل بيانات الوارث")
        if not ok:
            return

        messagebox.showinfo("نجاح", "تم تعديل بيانات الوارث")
        self._clear_vendor_form()
        self._refresh_all_data()

    def _delete_plot(self):
        if not self.selected_plot_id:
            return messagebox.showwarning("تنبيه", "اختر عقارًا من الجدول أولاً")
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا العقار؟"):
            return

        linked_row = self.execute_query(
            "SELECT COUNT(*) FROM finance.ledger WHERE property_id=%s",
            (self.selected_plot_id,),
            fetchone=True,
            error_prefix="فشل التحقق من ارتباطات العقار",
        )
        if linked_row is None:
            return

        linked = linked_row[0] if isinstance(linked_row, (tuple, list)) and linked_row else 0
        if linked > 0:
            return messagebox.showwarning("تنبيه", "لا يمكن حذف العقار لوجود قيود محاسبية مرتبطة به")

        ok = self.execute_query(
            "DELETE FROM finance.properties WHERE id=%s",
            (self.selected_plot_id,),
            error_prefix="فشل حذف العقار",
        )
        if not ok:
            return

        messagebox.showinfo("نجاح", "تم حذف العقار")
        self._clear_plot_form()
        self._refresh_all_data()

    def _delete_vendor(self):
        if not self.selected_vendor_id:
            return messagebox.showwarning("تنبيه", "اختر وارثًا من الجدول أولاً")
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا الوارث؟"):
            return

        def _delete_vendor_tx(cur):
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
                return "blocked"

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
            return "deleted"

        result = self.execute_transaction(_delete_vendor_tx, error_prefix="فشل حذف الوارث")
        if result is None:
            return
        if result == "blocked":
            return messagebox.showwarning("تنبيه", "لا يمكن حذف الوارث لوجود قيود حركة مرتبطة به")

        messagebox.showinfo("نجاح", "تم حذف الوارث")
        self._clear_vendor_form()
        self._refresh_all_data()

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

        # --- Refactored implementation and runtime symbol rebind ---

        class _SubCodingOpeningBalancesRefactored:
            def __init__(self, master):
                self.master = master
                self.primary_color = "#2c3e50"
                self.accent_color = "#1abc9c"
                self.bg_color = "#f4f7f6"
                self.selected_property_id = None
                self.selected_vendor_id = None
                self.group_map = {}
                self.property_map = {}

                self._setup_styles()
                self._build_ui()
                self._reload_all()

            def _setup_styles(self):
                style = tb.Style()
                style.configure("Ref.Sub.Root.TFrame", background=self.bg_color)
                style.configure("Ref.Sub.Header.TFrame", background=self.primary_color)
                style.configure("Ref.Sub.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 16, "bold"))
                style.configure("Ref.Sub.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
                style.configure("Ref.Sub.Treeview", rowheight=30, font=("Segoe UI", 10))
                style.configure("Ref.Sub.Treeview.Heading", font=("Segoe UI", 10, "bold"))

            def _build_ui(self):
                self.frame = tb.Frame(self.master, style="Ref.Sub.Root.TFrame")
                self.frame.pack(fill=tk.BOTH, expand=True)

                header = tb.Frame(self.frame, style="Ref.Sub.Header.TFrame", padding=10)
                header.pack(fill="x")
                tb.Label(header, text="إدارة العقارات والموردين", style="Ref.Sub.Header.TLabel").pack(side="right")

                actions = tb.Frame(header, style="Ref.Sub.Header.TFrame")
                actions.pack(side="left")
                for text, command in (("جديد", self._action_new), ("حفظ", self._action_save), ("تعديل", self._action_edit), ("حذف", self._action_delete), ("بحث", self._action_search)):
                    tb.Button(actions, text=text, command=command).pack(side="left", padx=3)

                self.notebook = ttk.Notebook(self.frame)
                self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
                self.tab_properties = tb.Frame(self.notebook, style="Ref.Sub.Root.TFrame", padding=10)
                self.tab_vendors = tb.Frame(self.notebook, style="Ref.Sub.Root.TFrame", padding=10)
                self.notebook.add(self.tab_properties, text="العقارات")
                self.notebook.add(self.tab_vendors, text="الموردون")

                self._build_property_tab()
                self._build_vendor_tab()

            def _build_property_tab(self):
                self.tab_properties.columnconfigure(0, weight=2)
                self.tab_properties.columnconfigure(1, weight=1)
                self.tab_properties.rowconfigure(0, weight=1)

                card_table = tb.Frame(self.tab_properties, style="Ref.Sub.Card.TFrame", padding=8)
                card_table.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
                card_form = tb.Frame(self.tab_properties, style="Ref.Sub.Card.TFrame", padding=8)
                card_form.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
                card_form.columnconfigure(0, weight=1)

                self.property_tree = ttk.Treeview(card_table, columns=("id", "name", "price", "account"), show="headings", style="Ref.Sub.Treeview")
                self.property_tree.heading("id", text="ID", anchor="e")
                self.property_tree.heading("name", text="اسم العقار", anchor="e")
                self.property_tree.heading("price", text="سعر الشراء", anchor="e")
                self.property_tree.heading("account", text="كود الحساب", anchor="e")
                self.property_tree.column("id", width=60, anchor="e")
                self.property_tree.column("name", width=220, anchor="e")
                self.property_tree.column("price", width=120, anchor="e")
                self.property_tree.column("account", width=120, anchor="e")
                self.property_tree.pack(fill="both", expand=True)
                self.property_tree.bind("<<TreeviewSelect>>", self._on_property_select)

                self.p_name = self._labeled_entry(card_form, "اسم العقار", 0)
                self.p_price = self._labeled_entry(card_form, "سعر الشراء", 2)
                self.p_account_code = self._labeled_entry(card_form, "كود الحساب", 4, readonly=True)

                ttk.Label(card_form, text="حساب العقار").grid(row=6, column=0, sticky="e", pady=(8, 3))
                self.p_account_combo = ttk.Combobox(card_form, state="readonly", justify="right")
                self.p_account_combo.grid(row=7, column=0, sticky="ew")
                bind_searchable_combobox(self.p_account_combo)
                self.p_account_combo.bind("<<ComboboxSelected>>", lambda _e: self._set_entry(self.p_account_code, self.p_account_combo.get().split(" - ", 1)[0].strip()))

            def _build_vendor_tab(self):
                self.tab_vendors.columnconfigure(0, weight=2)
                self.tab_vendors.columnconfigure(1, weight=1)
                self.tab_vendors.rowconfigure(0, weight=1)

                card_table = tb.Frame(self.tab_vendors, style="Ref.Sub.Card.TFrame", padding=8)
                card_table.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
                card_form = tb.Frame(self.tab_vendors, style="Ref.Sub.Card.TFrame", padding=8)
                card_form.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
                card_form.columnconfigure(0, weight=1)

                self.vendor_tree = ttk.Treeview(card_table, columns=("id", "name", "group", "property", "account"), show="headings", style="Ref.Sub.Treeview")
                for col, title, w in (("id", "ID", 60), ("name", "اسم المورد", 180), ("group", "المجموعة", 160), ("property", "العقار", 160), ("account", "كود الحساب", 110)):
                    self.vendor_tree.heading(col, text=title, anchor="e")
                    self.vendor_tree.column(col, width=w, anchor="e")
                self.vendor_tree.pack(fill="both", expand=True)
                self.vendor_tree.bind("<<TreeviewSelect>>", self._on_vendor_select)

                self.v_name = self._labeled_entry(card_form, "اسم المورد", 0)

                ttk.Label(card_form, text="مجموعة المورد").grid(row=2, column=0, sticky="e", pady=(8, 3))
                self.v_group_combo = ttk.Combobox(card_form, state="readonly", justify="right")
                self.v_group_combo.grid(row=3, column=0, sticky="ew")
                bind_searchable_combobox(self.v_group_combo)

                tb.Button(card_form, text="إضافة مجموعة", command=self._add_group_dialog).grid(row=4, column=0, sticky="ew", pady=6)

                ttk.Label(card_form, text="العقار").grid(row=5, column=0, sticky="e", pady=(8, 3))
                self.v_property_combo = ttk.Combobox(card_form, state="readonly", justify="right")
                self.v_property_combo.grid(row=6, column=0, sticky="ew")
                bind_searchable_combobox(self.v_property_combo)

                self.v_account_code = self._labeled_entry(card_form, "كود حساب المورد", 8, readonly=True)

            def _labeled_entry(self, parent, text, row, readonly=False):
                ttk.Label(parent, text=text).grid(row=row, column=0, sticky="e", pady=(8, 3))
                entry = ttk.Entry(parent, justify="right")
                entry.grid(row=row + 1, column=0, sticky="ew")
                if readonly:
                    entry.configure(state="readonly")
                return entry

            def _set_entry(self, entry, value):
                state = str(entry.cget("state"))
                if state == "readonly":
                    entry.configure(state="normal")
                entry.delete(0, tk.END)
                entry.insert(0, value)
                if state == "readonly":
                    entry.configure(state="readonly")

            def _reload_all(self):
                self._load_group_choices()
                self._load_property_choices()
                self._load_property_rows()
                self._load_vendor_rows()

            def _load_group_choices(self):
                conn = get_connection()
                if not conn:
                    return
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT id, group_name, account_code FROM finance.vendor_groups ORDER BY group_name")
                            rows = cur.fetchall() or []
                    values = []
                    self.group_map = {}
                    for row in rows:
                        display = f"{(row[2] or '').strip()} - {(row[1] or '').strip()}".strip(" -")
                        if display:
                            values.append(display)
                            self.group_map[display] = int(row[0])
                    set_combobox_values(self.v_group_combo, values)
                except Exception as exc:
                    messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل مجموعات الموردين"))
                finally:
                    conn.close()

            def _load_property_choices(self):
                conn = get_connection()
                if not conn:
                    return
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT id, property_name, account_code FROM finance.properties ORDER BY property_name")
                            p_rows = cur.fetchall() or []
                            cur.execute("SELECT account_code, account_name FROM finance.accounts WHERE account_level='تحليلي' AND is_active=true AND (parent_code='1111' OR account_code LIKE '1111%') ORDER BY account_code")
                            a_rows = cur.fetchall() or []
                    p_values = []
                    self.property_map = {}
                    for row in p_rows:
                        display = f"{(row[2] or '').strip()} - {(row[1] or '').strip()}".strip(" -")
                        if display:
                            p_values.append(display)
                            self.property_map[display] = int(row[0])
                    a_values = [f"{(r[0] or '').strip()} - {(r[1] or '').strip()}".strip(" -") for r in a_rows if (r[0] or '').strip()]
                    set_combobox_values(self.v_property_combo, p_values)
                    set_combobox_values(self.p_account_combo, a_values)
                except Exception as exc:
                    messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل خيارات العقار والحساب"))
                finally:
                    conn.close()

            def _load_property_rows(self):
                self.property_tree.delete(*self.property_tree.get_children())
                conn = get_connection()
                if not conn:
                    return
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT id, property_name, purchase_price, account_code FROM finance.properties ORDER BY id DESC")
                            rows = cur.fetchall() or []
                    for row in rows:
                        self.property_tree.insert("", tk.END, iid=str(row[0]), values=tuple("" if v is None else v for v in row))
                except Exception as exc:
                    messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل العقارات"))
                finally:
                    conn.close()

            def _load_vendor_rows(self):
                self.vendor_tree.delete(*self.vendor_tree.get_children())
                conn = get_connection()
                if not conn:
                    return
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                """
                                SELECT
                                    v.id,
                                    v.vendor_name,
                                    g.group_name,
                                    p.property_name,
                                    v.account_code
                                FROM finance.vendors v
                                LEFT JOIN finance.vendor_groups g ON v.group_id = g.id
                                LEFT JOIN finance.properties p ON v.property_id = p.id
                                ORDER BY v.id DESC
                                """
                            )
                            rows = cur.fetchall() or []
                    for row in rows:
                        self.vendor_tree.insert("", tk.END, iid=str(row[0]), values=tuple("" if v is None else v for v in row))
                except Exception as exc:
                    messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل الموردين"))
                finally:
                    conn.close()

            def _save_property(self):
                name = self.p_name.get().strip()
                code = self.p_account_code.get().strip()
                try:
                    price = float((self.p_price.get().strip() or "0").replace(",", ""))
                except ValueError:
                    messagebox.showwarning("تنبيه", "سعر الشراء يجب أن يكون رقمًا")
                    return
                if not name or not code:
                    messagebox.showwarning("تنبيه", "يرجى إدخال اسم العقار واختيار الحساب")
                    return

                conn = get_connection()
                if not conn:
                    return
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("INSERT INTO finance.properties (property_name, purchase_price, total_cost, status, account_code) VALUES (%s, %s, %s, %s, %s)", (name, price, price, "نشط", code))
                    self._action_new()
                    self._reload_all()
                    messagebox.showinfo("نجاح", "تم حفظ العقار")
                except Exception as exc:
                    messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ العقار"))
                finally:
                    conn.close()

            def _save_vendor(self):
                name = self.v_name.get().strip()
                group_id = self.group_map.get(self.v_group_combo.get().strip())
                property_id = self.property_map.get(self.v_property_combo.get().strip())
                if not name or group_id is None:
                    messagebox.showwarning("تنبيه", "يرجى إدخال اسم المورد واختيار المجموعة")
                    return

                conn = get_connection()
                if not conn:
                    return
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("INSERT INTO finance.vendors (vendor_name, group_id, property_id) VALUES (%s, %s, %s)", (name, group_id, property_id))
                    self._action_new()
                    self._reload_all()
                    messagebox.showinfo("نجاح", "تم حفظ المورد")
                except Exception as exc:
                    messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ المورد"))
                finally:
                    conn.close()

            def _edit_property(self):
                if not self.selected_property_id:
                    messagebox.showwarning("تنبيه", "اختر عقاراً للتعديل")
                    return
                name = self.p_name.get().strip()
                code = self.p_account_code.get().strip()
                try:
                    price = float((self.p_price.get().strip() or "0").replace(",", ""))
                except ValueError:
                    messagebox.showwarning("تنبيه", "سعر الشراء يجب أن يكون رقمًا")
                    return

                conn = get_connection()
                if not conn:
                    return
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("UPDATE finance.properties SET property_name=%s, purchase_price=%s, total_cost=%s, account_code=%s WHERE id=%s", (name, price, price, code, self.selected_property_id))
                    self._reload_all()
                    messagebox.showinfo("نجاح", "تم تعديل العقار")
                except Exception as exc:
                    messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل العقار"))
                finally:
                    conn.close()

            def _edit_vendor(self):
                if not self.selected_vendor_id:
                    messagebox.showwarning("تنبيه", "اختر مورداً للتعديل")
                    return
                name = self.v_name.get().strip()
                group_id = self.group_map.get(self.v_group_combo.get().strip())
                property_id = self.property_map.get(self.v_property_combo.get().strip())

                conn = get_connection()
                if not conn:
                    return
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("UPDATE finance.vendors SET vendor_name=%s, group_id=%s, property_id=%s WHERE id=%s", (name, group_id, property_id, self.selected_vendor_id))
                    self._reload_all()
                    messagebox.showinfo("نجاح", "تم تعديل المورد")
                except Exception as exc:
                    messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل المورد"))
                finally:
                    conn.close()

            def _delete_property(self):
                if not self.selected_property_id:
                    messagebox.showwarning("تنبيه", "اختر عقاراً للحذف")
                    return
                if not messagebox.askyesno("تأكيد", "هل تريد حذف العقار المحدد؟"):
                    return
                conn = get_connection()
                if not conn:
                    return
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("DELETE FROM finance.properties WHERE id=%s", (self.selected_property_id,))
                    self._action_new()
                    self._reload_all()
                except Exception as exc:
                    messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حذف العقار"))
                finally:
                    conn.close()

            def _delete_vendor(self):
                if not self.selected_vendor_id:
                    messagebox.showwarning("تنبيه", "اختر مورداً للحذف")
                    return
                if not messagebox.askyesno("تأكيد", "هل تريد حذف المورد المحدد؟"):
                    return
                conn = get_connection()
                if not conn:
                    return
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("DELETE FROM finance.vendors WHERE id=%s", (self.selected_vendor_id,))
                    self._action_new()
                    self._reload_all()
                except Exception as exc:
                    messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حذف المورد"))
                finally:
                    conn.close()

            def _on_property_select(self, _event=None):
                selected = self.property_tree.selection()
                if not selected:
                    return
                row = self.property_tree.item(selected[0], "values")
                if not row:
                    return
                self.selected_property_id = int(row[0])
                self.p_name.delete(0, tk.END)
                self.p_name.insert(0, row[1] or "")
                self.p_price.delete(0, tk.END)
                self.p_price.insert(0, row[2] or "")
                code = (row[3] or "").strip()
                self._set_entry(self.p_account_code, code)
                for value in self.p_account_combo["values"]:
                    if str(value).startswith(f"{code} -") or str(value) == code:
                        self.p_account_combo.set(value)
                        break

            def _on_vendor_select(self, _event=None):
                selected = self.vendor_tree.selection()
                if not selected:
                    return
                row = self.vendor_tree.item(selected[0], "values")
                if not row:
                    return
                self.selected_vendor_id = int(row[0])
                self.v_name.delete(0, tk.END)
                self.v_name.insert(0, row[1] or "")
                self._set_entry(self.v_account_code, (row[4] or "").strip())

                group_name = (row[2] or "").strip()
                for value in self.v_group_combo["values"]:
                    if str(value).endswith(f"- {group_name}") or str(value) == group_name:
                        self.v_group_combo.set(value)
                        break

                property_name = (row[3] or "").strip()
                for value in self.v_property_combo["values"]:
                    if str(value).endswith(f"- {property_name}") or str(value) == property_name:
                        self.v_property_combo.set(value)
                        break

            def _add_group_dialog(self):
                group_name = simpledialog.askstring("إضافة مجموعة", "اسم مجموعة الموردين:", parent=self.master)
                group_name = (group_name or "").strip()
                if not group_name:
                    return
                conn = get_connection()
                if not conn:
                    return
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute("INSERT INTO finance.vendor_groups (group_name) VALUES (%s)", (group_name,))
                    self._load_group_choices()
                    messagebox.showinfo("نجاح", "تمت إضافة المجموعة")
                except Exception as exc:
                    messagebox.showerror("خطأ", get_db_error_message(exc, "فشل إضافة المجموعة"))
                finally:
                    conn.close()

            def _action_new(self):
                if self.notebook.index(self.notebook.select()) == 0:
                    self.selected_property_id = None
                    self.p_name.delete(0, tk.END)
                    self.p_price.delete(0, tk.END)
                    self.p_account_combo.set("")
                    self._set_entry(self.p_account_code, "")
                else:
                    self.selected_vendor_id = None
                    self.v_name.delete(0, tk.END)
                    self.v_group_combo.set("")
                    self.v_property_combo.set("")
                    self._set_entry(self.v_account_code, "")

            def _action_save(self):
                if self.notebook.index(self.notebook.select()) == 0:
                    self._save_property()
                else:
                    self._save_vendor()

            def _action_edit(self):
                if self.notebook.index(self.notebook.select()) == 0:
                    self._edit_property()
                else:
                    self._edit_vendor()

            def _action_delete(self):
                if self.notebook.index(self.notebook.select()) == 0:
                    self._delete_property()
                else:
                    self._delete_vendor()

            def _action_search(self):
                text = simpledialog.askstring("بحث", "أدخل كلمة البحث:", parent=self.master)
                query = (text or "").strip().lower()
                if not query:
                    self._reload_all()
                    return
                tree = self.property_tree if self.notebook.index(self.notebook.select()) == 0 else self.vendor_tree
                for iid in tree.get_children():
                    values = tree.item(iid, "values")
                    if query in " ".join(str(value or "").lower() for value in values):
                        tree.selection_set(iid)
                        tree.see(iid)
                        tree.focus(iid)
                        return
                messagebox.showinfo("بحث", "لا توجد نتائج")


                SubCodingOpeningBalances = _SubCodingOpeningBalancesRefactored

        # ...existing code...

        from subcoding_opening_balances_refactored import SubCodingOpeningBalances as _RefactoredSubCodingOpeningBalances

        SubCodingOpeningBalances = _RefactoredSubCodingOpeningBalances

