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
        style.configure("Sub.Ref.Root.TFrame", background=self.bg_color)
        style.configure("Sub.Ref.Header.TFrame", background=self.primary_color)
        style.configure("Sub.Ref.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 18, "bold"))
        style.configure("Sub.Ref.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("Sub.Ref.FieldLabel.TLabel", background="white", foreground=self.primary_color, font=("Segoe UI", 11, "bold"), anchor="e")

        style.configure("Sub.Ref.Treeview", rowheight=30, font=("Segoe UI", 10), background="white", fieldbackground="white", foreground=self.primary_color)
        style.configure("Sub.Ref.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.primary_color, foreground="white")
        style.map("Sub.Ref.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "white")])

        style.configure("Sub.Ref.Primary.TButton", background="#2980b9", foreground="white", borderwidth=0, font=("Segoe UI", 10, "bold"), padding=(10, 5))
        style.configure("Sub.Ref.Success.TButton", background="#27ae60", foreground="white", borderwidth=0, font=("Segoe UI", 10, "bold"), padding=(10, 5))
        style.configure("Sub.Ref.Warning.TButton", background="#f1c40f", foreground="#2c3e50", borderwidth=0, font=("Segoe UI", 10, "bold"), padding=(10, 5))
        style.configure("Sub.Ref.Danger.TButton", background="#e74c3c", foreground="white", borderwidth=0, font=("Segoe UI", 10, "bold"), padding=(10, 5))
        style.configure("Sub.Ref.Info.TButton", background="#8e44ad", foreground="white", borderwidth=0, font=("Segoe UI", 10, "bold"), padding=(10, 5))

        for btn_style in (
            "Sub.Ref.Primary.TButton",
            "Sub.Ref.Success.TButton",
            "Sub.Ref.Warning.TButton",
            "Sub.Ref.Danger.TButton",
            "Sub.Ref.Info.TButton",
        ):
            style.map(btn_style, background=[("active", self.accent_color), ("pressed", self.accent_color)], foreground=[("active", "white"), ("pressed", "white")])

    def _build_layout(self):
        self.frame = tb.Frame(self.master, style="Sub.Ref.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        header = tb.Frame(self.frame, style="Sub.Ref.Header.TFrame", padding=10)
        header.pack(fill="x")
        tb.Label(header, text="إدارة الأراضي والموردين", style="Sub.Ref.Header.TLabel").pack(side="right")

        actions = tb.Frame(header, style="Sub.Ref.Header.TFrame")
        actions.pack(side="left")
        for title, action, style_name in (
            ("جديد", self._action_new, "Sub.Ref.Primary.TButton"),
            ("حفظ", self._action_save, "Sub.Ref.Success.TButton"),
            ("تعديل", self._action_edit, "Sub.Ref.Warning.TButton"),
            ("حذف", self._action_delete, "Sub.Ref.Danger.TButton"),
            ("بحث", self._action_search, "Sub.Ref.Info.TButton"),
        ):
            tb.Button(actions, text=title, style=style_name, command=action).pack(side="left", padx=3)

        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_properties = tb.Frame(self.notebook, style="Sub.Ref.Root.TFrame", padding=10)
        self.tab_vendors = tb.Frame(self.notebook, style="Sub.Ref.Root.TFrame", padding=10)
        self.notebook.add(self.tab_properties, text="الأراضي")
        self.notebook.add(self.tab_vendors, text="الموردون")

        self._build_properties_tab()
        self._build_vendors_tab()

    def _make_labeled_entry(self, parent, label_text, row, readonly=False):
        ttk.Label(parent, text=label_text, style="Sub.Ref.FieldLabel.TLabel", anchor="e").grid(row=row, column=0, sticky="e", pady=(8, 4))
        entry = ttk.Entry(parent, justify="right", font=("Segoe UI", 11, "bold"))
        entry.grid(row=row + 1, column=0, sticky="ew")
        if readonly:
            entry.configure(state="readonly")
        return entry

    def _build_properties_tab(self):
        self.tab_properties.columnconfigure(0, weight=2)
        self.tab_properties.columnconfigure(1, weight=1)
        self.tab_properties.rowconfigure(0, weight=1)

        table_card = tb.Frame(self.tab_properties, style="Sub.Ref.Card.TFrame", padding=8)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        form_card = tb.Frame(self.tab_properties, style="Sub.Ref.Card.TFrame", padding=8)
        form_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        form_card.columnconfigure(0, weight=1)

        self.property_tree = ttk.Treeview(table_card, columns=("id", "name", "price", "account"), show="headings", style="Sub.Ref.Treeview")
        for c, t, w in (("id", "ID", 60), ("name", "اسم الأرض", 220), ("price", "سعر الشراء", 120), ("account", "كود الحساب", 120)):
            self.property_tree.heading(c, text=t, anchor="e")
            self.property_tree.column(c, width=w, anchor="e")
        self.property_tree.pack(fill="both", expand=True)
        self.property_tree.bind("<<TreeviewSelect>>", self._on_property_select)

        self.p_name = self._make_labeled_entry(form_card, "اسم الأرض", 0)
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

        table_card = tb.Frame(self.tab_vendors, style="Sub.Ref.Card.TFrame", padding=8)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        form_card = tb.Frame(self.tab_vendors, style="Sub.Ref.Card.TFrame", padding=8)
        form_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        form_card.columnconfigure(0, weight=1)

        self.vendor_tree = ttk.Treeview(table_card, columns=("id", "name", "group", "property", "account"), show="headings", style="Sub.Ref.Treeview")
        for c, t, w in (("id", "ID", 60), ("name", "اسم المورد", 180), ("group", "المجموعة", 170), ("property", "الأرض", 170), ("account", "كود الحساب", 120)):
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

        ttk.Label(form_card, text="الأرض", anchor="e").grid(row=5, column=0, sticky="e", pady=(8, 4))
        self.v_property_combo = ttk.Combobox(form_card, state="readonly", justify="right")
        self.v_property_combo.grid(row=6, column=0, sticky="ew")
        bind_searchable_combobox(self.v_property_combo)

        self.v_account_code = self._make_labeled_entry(form_card, "كود الحساب", 8, readonly=True)

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
                    cur.execute("SELECT account_code, account_name FROM finance.accounts WHERE account_level='تحليلي' AND is_active=true AND (parent_code='1111' OR account_code LIKE '1111%') ORDER BY account_code")
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
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل خيارات الأرض والحساب"))
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
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل الأراضي"))
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
        code = self.p_account_code.get().strip()
        try:
            price = float((self.p_price.get().strip() or "0").replace(",", ""))
        except ValueError:
            messagebox.showwarning("تنبيه", "سعر الشراء يجب أن يكون رقمًا")
            return

        if not name or not code:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم الأرض واختيار الحساب")
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO finance.properties (property_name, purchase_price, total_cost, status, account_code) VALUES (%s, %s, %s, %s, %s)", (name, price, price, "نشط", code))
            messagebox.showinfo("نجاح", "تم حفظ الأرض")
            self._action_new()
            self._refresh_all_data()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ الأرض"))
        finally:
            conn.close()

    def _save_vendor(self):
        name = self.v_name.get().strip()
        group_id = self.group_display_to_id.get(self.v_group_combo.get().strip())
        property_id = self.property_display_to_id.get(self.v_property_combo.get().strip())

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
            messagebox.showinfo("نجاح", "تم تعديل الأرض")
            self._refresh_all_data()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل الأرض"))
        finally:
            conn.close()

    def _edit_vendor(self):
        if not self.selected_vendor_id:
            messagebox.showwarning("تنبيه", "اختر مورداً للتعديل")
            return

        name = self.v_name.get().strip()
        group_id = self.group_display_to_id.get(self.v_group_combo.get().strip())
        property_id = self.property_display_to_id.get(self.v_property_combo.get().strip())

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE finance.vendors SET vendor_name=%s, group_id=%s, property_id=%s WHERE id=%s", (name, group_id, property_id, self.selected_vendor_id))
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
        if not messagebox.askyesno("تأكيد", "هل تريد حذف الأرض المحددة؟"):
            return

        self._delete_by_id("finance.properties", self.selected_property_id, "فشل حذف الأرض")
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
