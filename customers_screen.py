import tkinter as tk
from tkinter import messagebox, ttk

import ttkbootstrap as tb

from app_constants import CUSTOMER_CONTROL_ACCOUNT_CODE
from db_connection import get_connection, get_db_error_message


class CustomersScreen:
    STATUS_ACTIVE = "فعال"
    STATUS_INACTIVE = "غير فعال"

    def __init__(self, master):
        self.master = master

        # Match global system palette
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        # Softer, non-white surfaces for a richer system look.
        self.card_color = "#e8eef3"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.bg_color = "#dde6ee"

        self.selected_customer_id = None
        self.has_address_column = False
        self.has_is_active_column = False
        self.has_control_account_column = False

        self._setup_styles()
        self._build_layout()
        self._refresh_schema_flags()
        self._load_rows()
        self._new_customer()

    def _setup_styles(self):
        style = tb.Style()
        style.configure("Cust.Root.TFrame", background=self.bg_color)
        style.configure(
            "Cust.Card.TFrame",
            background=self.card_color,
            bordercolor="#d1d8e0",
            borderwidth=1,
            relief="solid",
        )
        style.configure("Cust.Header.TFrame", background=self.primary_color)
        style.configure("Cust.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 18, "bold"))
        style.configure(
            "Cust.Label.TLabel",
            background=self.sidebar_color,
            foreground=self.text_color,
            font=("Segoe UI", 11, "bold"),
            anchor="e",
            padding=6,
        )
        style.configure("Cust.Entry.TEntry", font=("Segoe UI", 11, "bold"), foreground=self.primary_color)
        style.configure("Cust.Combo.TCombobox", font=("Segoe UI", 11, "bold"), foreground=self.primary_color)

        style.configure("Cust.New.TButton", background="#2980b9", foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(10, 6))
        style.configure("Cust.Del.TButton", background="#e74c3c", foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(10, 6))
        style.configure("Cust.Edit.TButton", background="#f1c40f", foreground="#1b1b1b", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(10, 6))
        style.configure("Cust.Save.TButton", background="#27ae60", foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(10, 6))
        style.configure("Cust.Refresh.TButton", background="#16a085", foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(8, 5))

        style.configure(
            "Cust.Treeview",
            rowheight=34,
            font=("Segoe UI", 10),
            background="#f7fafc",
            fieldbackground="#f7fafc",
            foreground=self.primary_color,
            borderwidth=0,
        )
        style.configure(
            "Cust.Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background=self.primary_color,
            foreground="white",
            relief="flat",
        )
        style.map("Cust.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "white")])

    def _build_layout(self):
        self.frame = tb.Frame(self.master, style="Cust.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=0)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_rowconfigure(0, weight=0)
        self.frame.grid_rowconfigure(1, weight=1)

        self.card = tb.Frame(self.frame, style="Cust.Card.TFrame", padding=0)
        self.card.grid(row=0, column=1, sticky="n", padx=20, pady=(20, 12))
        # Larger centered card width.
        self.card.grid_columnconfigure(0, weight=1, minsize=860)

        header = tb.Frame(self.card, style="Cust.Header.TFrame", padding=(20, 14))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        tb.Label(header, text="ترميز العملاء", style="Cust.Header.TLabel", anchor="e").grid(row=0, column=0, sticky="e")

        form_wrap = tb.Frame(self.card, style="Cust.Card.TFrame", padding=(30, 24, 30, 14))
        form_wrap.grid(row=1, column=0, sticky="ew")
        form_wrap.grid_columnconfigure(0, weight=1)

        self.ent_code = self._create_field_row(form_wrap, 0, "كود العميل", field_type="entry", readonly=True)
        self.ent_name = self._create_field_row(form_wrap, 1, "الاسم الكلي", field_type="entry")
        self.ent_phone = self._create_field_row(form_wrap, 2, "رقم الهاتف", field_type="entry")
        self.ent_address = self._create_field_row(form_wrap, 3, "العنوان", field_type="entry")
        self.combo_status = self._create_field_row(
            form_wrap,
            4,
            "الحالة",
            field_type="combo",
            values=(self.STATUS_ACTIVE, self.STATUS_INACTIVE),
            state="readonly",
        )

        buttons_wrap = tb.Frame(self.card, style="Cust.Card.TFrame", padding=(16, 6, 16, 14))
        buttons_wrap.grid(row=2, column=0, sticky="ew")
        for idx in range(4):
            buttons_wrap.grid_columnconfigure(idx, weight=1)

        tb.Button(buttons_wrap, text="جديد", style="Cust.New.TButton", command=self._new_customer).grid(row=0, column=3, padx=4, sticky="ew")
        tb.Button(buttons_wrap, text="حذف", style="Cust.Del.TButton", command=self._delete).grid(row=0, column=2, padx=4, sticky="ew")
        tb.Button(buttons_wrap, text="تعديل", style="Cust.Edit.TButton", command=self._edit).grid(row=0, column=1, padx=4, sticky="ew")
        tb.Button(buttons_wrap, text="حفظ", style="Cust.Save.TButton", command=self._save).grid(row=0, column=0, padx=4, sticky="ew")

        table_wrap = tb.Frame(self.frame, style="Cust.Card.TFrame", padding=(12, 10, 12, 12))
        table_wrap.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=24, pady=(0, 16))
        table_wrap.grid_columnconfigure(0, weight=1)
        table_wrap.grid_rowconfigure(1, weight=1)

        actions_bar = tb.Frame(table_wrap, style="Cust.Card.TFrame")
        actions_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        actions_bar.grid_columnconfigure(0, weight=1)
        tb.Button(actions_bar, text="تحديث", style="Cust.Refresh.TButton", command=self._load_rows).grid(row=0, column=0, sticky="e")

        cols = ("id", "code", "name", "phone", "address", "status")
        self.tree = ttk.Treeview(table_wrap, columns=cols, show="headings", style="Cust.Treeview")
        for col, title, width in (
            ("id", "ID", 70),
            ("code", "كود العميل", 110),
            ("name", "الاسم الكلي", 240),
            ("phone", "رقم الهاتف", 150),
            ("address", "العنوان", 260),
            ("status", "الحالة", 90),
        ):
            self.tree.heading(col, text=title, anchor="e")
            self.tree.column(col, width=width, anchor="e")

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        y_scroll.grid(row=1, column=1, sticky="ns")

        # Striped rows for a modern table layout.
        self.tree.tag_configure("odd", background="#f7fafc")
        self.tree.tag_configure("even", background="#edf3f8")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self._bind_enter_navigation()

    def _create_field_row(self, parent, row, label_text, field_type="entry", readonly=False, values=None, state="normal"):
        row_wrap = tb.Frame(parent, style="Cust.Card.TFrame")
        row_wrap.grid(row=row, column=0, sticky="ew", pady=12)
        row_wrap.grid_columnconfigure(0, weight=1)

        ttk.Label(row_wrap, text=label_text, style="Cust.Label.TLabel", width=14).grid(row=0, column=1, sticky="e", padx=(0, 5))

        if field_type == "combo":
            widget = ttk.Combobox(
                row_wrap,
                values=values or (),
                state=state,
                justify="right",
                style="Cust.Combo.TCombobox",
                font=("Segoe UI", 11, "bold"),
            )
            if values:
                widget.set(values[0])
        else:
            widget = ttk.Entry(row_wrap, justify="right", style="Cust.Entry.TEntry", font=("Segoe UI", 11, "bold"))
            if readonly:
                widget.configure(state="readonly")

        widget.grid(row=0, column=0, sticky="ew")
        return widget

    def _bind_enter_navigation(self):
        order = [self.ent_name, self.ent_phone, self.ent_address, self.combo_status]

        for idx, widget in enumerate(order):
            def go_next(_event, i=idx):
                if i == len(order) - 1:
                    self._save()
                else:
                    order[i + 1].focus_set()
                return "break"

            widget.bind("<Return>", go_next)

    def _refresh_schema_flags(self):
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    self.has_address_column = self._table_has_column(cur, "customers", "address")
                    self.has_is_active_column = self._table_has_column(cur, "customers", "is_active")
                    self.has_control_account_column = self._table_has_column(cur, "customers", "control_account")
        except Exception:
            self.has_address_column = False
            self.has_is_active_column = False
            self.has_control_account_column = False
        finally:
            conn.close()

    def _table_has_column(self, cur, table, column):
        cur.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'finance' AND table_name = %s AND column_name = %s
            """,
            (table, column),
        )
        return cur.fetchone() is not None

    def _status_to_bool(self, status_text):
        return status_text != self.STATUS_INACTIVE

    def _bool_to_status(self, is_active):
        return self.STATUS_ACTIVE if bool(is_active) else self.STATUS_INACTIVE

    def _set_readonly_entry(self, entry, value):
        was_readonly = str(entry.cget("state")) == "readonly"
        if was_readonly:
            entry.configure(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, value)
        if was_readonly:
            entry.configure(state="readonly")

    def _fetch_next_customer_code(self):
        conn = get_connection()
        if not conn:
            return ""
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT COALESCE(
                            MAX(CASE WHEN customer_code ~ '^[0-9]+$' THEN customer_code::BIGINT END),
                            COALESCE(MAX(id), 0)
                        ) + 1
                        FROM finance.customers
                        """
                    )
                    row = cur.fetchone()
                    return str(row[0]) if row and row[0] is not None else "1"
        except Exception:
            return ""
        finally:
            conn.close()

    def _new_customer(self):
        self.selected_customer_id = None
        self._set_readonly_entry(self.ent_code, self._fetch_next_customer_code())
        self.ent_name.delete(0, tk.END)
        self.ent_phone.delete(0, tk.END)
        self.ent_address.delete(0, tk.END)
        self.combo_status.set(self.STATUS_ACTIVE)
        self.ent_name.focus_set()

    def _validate_inputs(self):
        name = self.ent_name.get().strip()
        if not name:
            messagebox.showwarning("تنبيه", "يرجى إدخال الاسم الكلي")
            self.ent_name.focus_set()
            return None

        return {
            "customer_code": self.ent_code.get().strip() or None,
            "customer_name": name,
            "phone": self.ent_phone.get().strip() or None,
            "address": self.ent_address.get().strip() or None,
            "is_active": self._status_to_bool(self.combo_status.get().strip() or self.STATUS_ACTIVE),
        }

    def _load_rows(self):
        self.tree.delete(*self.tree.get_children())

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    address_expr = "COALESCE(address, '')" if self.has_address_column else "''"
                    status_expr = "COALESCE(is_active, true)" if self.has_is_active_column else "true"

                    cur.execute(
                        f"""
                        SELECT
                            id,
                            COALESCE(customer_code, ''),
                            customer_name,
                            COALESCE(phone, ''),
                            {address_expr} AS address,
                            {status_expr} AS is_active
                        FROM finance.customers
                        ORDER BY id DESC
                        """
                    )
                    rows = cur.fetchall() or []

            for idx, row in enumerate(rows):
                customer_id, code, name, phone, address, is_active = row
                tag = "even" if idx % 2 == 0 else "odd"
                self.tree.insert(
                    "",
                    tk.END,
                    iid=str(customer_id),
                    values=(
                        customer_id,
                        code,
                        name,
                        phone,
                        address,
                        self._bool_to_status(is_active),
                    ),
                    tags=(tag,),
                )
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل العملاء"))

        finally:
            conn.close()

    def _on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return

        data = self.tree.item(selected[0], "values")
        if not data:
            return

        self.selected_customer_id = int(data[0])
        self._set_readonly_entry(self.ent_code, str(data[1] or ""))

        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, data[2] or "")

        self.ent_phone.delete(0, tk.END)
        self.ent_phone.insert(0, data[3] or "")

        self.ent_address.delete(0, tk.END)
        self.ent_address.insert(0, data[4] or "")

        self.combo_status.set(data[5] or self.STATUS_ACTIVE)

    def _save(self):
        payload = self._validate_inputs()
        if not payload:
            return

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    values = [payload["customer_code"], payload["customer_name"], payload["phone"]]
                    extra_columns = []
                    extra_placeholders = []

                    if self.has_address_column:
                        extra_columns.append("address")
                        extra_placeholders.append("%s")
                        values.append(payload["address"])

                    if self.has_is_active_column:
                        extra_columns.append("is_active")
                        extra_placeholders.append("%s")
                        values.append(payload["is_active"])

                    if self.has_control_account_column:
                        extra_columns.append("control_account")
                        extra_placeholders.append("%s")
                        values.append(CUSTOMER_CONTROL_ACCOUNT_CODE)

                    extra_cols_sql = ""
                    if extra_columns:
                        extra_cols_sql = ",\n                            " + ",\n                            ".join(extra_columns)

                    extra_vals_sql = ""
                    if extra_placeholders:
                        extra_vals_sql = ", " + ", ".join(extra_placeholders)

                    sql = f"""
                        INSERT INTO finance.customers (
                            customer_code,
                            customer_name,
                            phone{extra_cols_sql}
                        )
                        VALUES (%s, %s, %s{extra_vals_sql})
                        RETURNING id
                    """

                    cur.execute(sql, tuple(values))
                    inserted_id = cur.fetchone()[0]

            self._load_rows()
            self._select_tree_row(inserted_id)
            messagebox.showinfo("نجاح", "تم حفظ العميل")
            self._new_customer()

        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ العميل"))

        finally:
            conn.close()

    def _edit(self):
        if not self.selected_customer_id:
            messagebox.showwarning("تنبيه", "اختر عميلاً للتعديل")
            return

        payload = self._validate_inputs()
        if not payload:
            return

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    set_parts = ["customer_code=%s", "customer_name=%s", "phone=%s"]
                    values = [payload["customer_code"], payload["customer_name"], payload["phone"]]

                    if self.has_address_column:
                        set_parts.append("address=%s")
                        values.append(payload["address"])

                    if self.has_is_active_column:
                        set_parts.append("is_active=%s")
                        values.append(payload["is_active"])

                    if self.has_control_account_column:
                        set_parts.append("control_account=%s")
                        values.append(CUSTOMER_CONTROL_ACCOUNT_CODE)

                    values.append(self.selected_customer_id)

                    cur.execute(
                        f"UPDATE finance.customers SET {', '.join(set_parts)} WHERE id=%s",
                        tuple(values),
                    )

            self._load_rows()
            self._select_tree_row(self.selected_customer_id)
            messagebox.showinfo("نجاح", "تم تعديل العميل")

        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل العميل"))

        finally:
            conn.close()

    def _delete(self):
        if not self.selected_customer_id:
            messagebox.showwarning("تنبيه", "اختر عميلاً للحذف")
            return

        if not messagebox.askyesno("تأكيد", "هل تريد حذف العميل المحدد؟"):
            return

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM finance.customers WHERE id=%s", (self.selected_customer_id,))

            self._load_rows()
            self._new_customer()
            messagebox.showinfo("نجاح", "تم حذف العميل")

        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حذف العميل"))

        finally:
            conn.close()

    def _select_tree_row(self, row_id):
        iid = str(row_id)
        if not self.tree.exists(iid):
            return
        self.tree.selection_set(iid)
        self.tree.focus(iid)
        self.tree.see(iid)
        self._on_select()
