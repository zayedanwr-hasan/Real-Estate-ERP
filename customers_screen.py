import tkinter as tk
from tkinter import messagebox, ttk

import ttkbootstrap as tb

from app_constants import ACCOUNT_LEVEL_ANALYTICAL, CUSTOMER_CONTROL_ACCOUNT_CODE
from db_connection import get_connection, get_db_error_message


class CustomersScreen:
    STATUS_ACTIVE = "فعال"
    STATUS_INACTIVE = "غير فعال"

    def __init__(self, master):
        self.master = master

        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#00ffff"
        self.text_color = "#ecf0f1"
        self.bg_color = "#f4f7f6"
        self.card_bg = "#3a4b5c"

        self.selected_customer_id = None
        self.customer_columns = set()
        self.accounts_columns = set()
        self.ledger_columns = set()

        self.field_width_chars = 34

        self._setup_styles()
        self._refresh_schema_flags()
        self._build_layout()
        self.refresh_rows()
        self.action_new()

    def _setup_styles(self):
        style = tb.Style()
        style.configure("Cust.Root.TFrame", background=self.bg_color)
        style.configure("Cust.Card.TFrame", background=self.card_bg, bordercolor=self.accent_color, borderwidth=1, relief="solid")
        style.configure("Cust.Title.TLabel", background=self.card_bg, foreground=self.text_color, font=("Segoe UI", 18, "bold"))
        style.configure("Cust.FieldLabel.TLabel", background=self.card_bg, foreground=self.text_color, font=("Segoe UI", 11, "bold"), anchor="e")
        style.configure(
            "Cust.Field.TEntry",
            font=("Segoe UI", 11),
            foreground=self.primary_color,
            fieldbackground="#f9fbff",
            bordercolor=self.accent_color,
            lightcolor=self.accent_color,
            darkcolor=self.accent_color,
            insertcolor=self.primary_color,
            padding=6,
        )
        style.configure("Cust.Field.TCombobox", font=("Segoe UI", 11), foreground=self.primary_color)

        style.configure("Cust.Treeview", rowheight=30, font=("Segoe UI", 10), background=self.card_bg, fieldbackground=self.card_bg, foreground="white")
        style.configure("Cust.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.sidebar_color, foreground="white")
        style.map("Cust.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "#102130")])

    def _build_layout(self):
        self.frame = tb.Frame(self.master, style="Cust.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        self.card = tb.Frame(self.frame, style="Cust.Card.TFrame", padding=(24, 20, 24, 20))
        self.card.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)
        self.card.grid_columnconfigure(0, weight=1, minsize=1180)
        self.card.grid_rowconfigure(3, weight=1)

        tb.Label(self.card, text="ترميز العملاء", style="Cust.Title.TLabel", anchor="e").grid(row=0, column=0, sticky="e", pady=(0, 12))

        self.form = tb.Frame(self.card, style="Cust.Card.TFrame")
        self.form.grid(row=1, column=0, sticky="ew")
        self.form.grid_columnconfigure(0, weight=1, uniform="custcol")
        self.form.grid_columnconfigure(2, weight=1, uniform="custcol")

        self.ent_name = self._create_labeled_field(self.form, 0, 0, "اسم العميل")
        self.ent_phone = self._create_labeled_field(self.form, 0, 2, "رقم الهاتف")
        self.cmb_control_account = self._create_labeled_field(
            self.form,
            1,
            0,
            "حساب التحكم",
            field_type="combo",
            values=(f"{CUSTOMER_CONTROL_ACCOUNT_CODE} - حساب تحكم العملاء",),
            state="readonly",
        )
        self.account_code_var = tk.StringVar()
        self.ent_account_code = self._create_labeled_field(
            self.form,
            1,
            2,
            "كود الحساب",
            textvariable=self.account_code_var,
        )
        self.cmb_status = self._create_labeled_field(
            self.form,
            2,
            0,
            "الحالة",
            field_type="combo",
            values=(self.STATUS_ACTIVE, self.STATUS_INACTIVE),
            state="readonly",
        )

        self.cmb_control_account.set(f"{CUSTOMER_CONTROL_ACCOUNT_CODE} - حساب تحكم العملاء")
        self.cmb_status.set(self.STATUS_ACTIVE)

        actions = tb.Frame(self.card, style="Cust.Card.TFrame")
        actions.grid(row=2, column=0, sticky="ew", pady=(10, 14))
        actions.grid_columnconfigure(0, weight=1)
        actions_wrap = tb.Frame(actions, style="Cust.Card.TFrame")
        actions_wrap.grid(row=0, column=0)

        button_specs = [
            ("جديد", "primary", self.action_new),
            ("حفظ", "success", self.action_save),
            ("تعديل", "warning", self.action_edit),
            ("حذف", "danger", self.action_delete),
            ("تحديث", "info", self.refresh_rows),
        ]
        for idx, (label, bootstyle, command) in enumerate(button_specs):
            tb.Button(actions_wrap, text=label, bootstyle=bootstyle, command=command, width=12).grid(row=0, column=idx, padx=7)

        table_wrap = tb.Frame(self.card, style="Cust.Card.TFrame")
        table_wrap.grid(row=3, column=0, sticky="nsew")
        table_wrap.grid_columnconfigure(0, weight=1)
        table_wrap.grid_rowconfigure(0, weight=1)

        cols = ("id", "name", "phone", "control_account", "status")
        self.tree = ttk.Treeview(table_wrap, columns=cols, show="headings", style="Cust.Treeview")
        self.tree.heading("id", text="ID", anchor="e")
        self.tree.heading("name", text="اسم العميل", anchor="e")
        self.tree.heading("phone", text="رقم الهاتف", anchor="e")
        self.tree.heading("control_account", text="كود الحساب", anchor="e")
        self.tree.heading("status", text="الحالة", anchor="e")
        self.tree.column("id", width=80, anchor="e")
        self.tree.column("name", width=320, anchor="e")
        self.tree.column("phone", width=220, anchor="e")
        self.tree.column("control_account", width=210, anchor="e")
        self.tree.column("status", width=130, anchor="e")

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self._bind_enter_navigation()

    def _create_labeled_field(self, parent, row, col, label_text, field_type="entry", values=(), state="normal", textvariable=None):
        wrap = tb.Frame(parent, style="Cust.Card.TFrame")
        wrap.grid(row=row, column=col, sticky="ew", padx=10, pady=10)
        wrap.grid_columnconfigure(0, weight=1)

        ttk.Label(wrap, text=label_text, style="Cust.FieldLabel.TLabel", width=14).grid(row=0, column=1, sticky="e", padx=(0, 10))

        if field_type == "combo":
            widget = ttk.Combobox(
                wrap,
                values=values,
                state=state,
                justify="right",
                style="Cust.Field.TCombobox",
                font=("Segoe UI", 11),
                width=self.field_width_chars,
                textvariable=textvariable,
            )
            if values:
                widget.set(values[0])
        else:
            widget = ttk.Entry(
                wrap,
                style="Cust.Field.TEntry",
                justify="right",
                font=("Segoe UI", 11),
                width=self.field_width_chars,
                textvariable=textvariable,
            )
            if state != "normal":
                widget.configure(state=state)

        widget.grid(row=0, column=0, sticky="ew")
        return widget

    def _bind_enter_navigation(self):
        order = [self.ent_name, self.ent_phone, self.ent_account_code, self.cmb_status]
        for idx, widget in enumerate(order):

            def go_next(_event, i=idx):
                if i == len(order) - 1:
                    if self.selected_customer_id:
                        self.action_edit()
                    else:
                        self.action_save()
                else:
                    order[i + 1].focus_set()
                return "break"

            widget.bind("<Return>", go_next)

    def _refresh_schema_flags(self):
        conn = get_connection()
        if not conn:
            self.customer_columns = set()
            self.accounts_columns = set()
            self.ledger_columns = set()
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT table_name, column_name
                        FROM information_schema.columns
                        WHERE table_schema='finance' AND table_name IN ('customers', 'accounts', 'ledger')
                        """
                    )
                    rows = cur.fetchall() or []

            self.customer_columns = {col for table, col in rows if table == "customers"}
            self.accounts_columns = {col for table, col in rows if table == "accounts"}
            self.ledger_columns = {col for table, col in rows if table == "ledger"}
        except Exception:
            self.customer_columns = set()
            self.accounts_columns = set()
            self.ledger_columns = set()
        finally:
            conn.close()

    def _status_to_bool(self, status_text):
        return status_text != self.STATUS_INACTIVE

    def _bool_to_status(self, is_active):
        return self.STATUS_ACTIVE if bool(is_active) else self.STATUS_INACTIVE

    def _next_account_code(self, parent_code):
        conn = get_connection()
        if not conn:
            return f"{parent_code}001"
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT COALESCE(MAX(CAST(SUBSTRING(TRIM(account_code) FROM %s) AS BIGINT)), 0)
                        FROM finance.accounts
                        WHERE TRIM(account_code) LIKE %s
                          AND LENGTH(TRIM(account_code)) >= %s
                          AND SUBSTRING(TRIM(account_code) FROM %s) ~ '^[0-9]+$'
                        """,
                        (len(parent_code) + 1, f"{parent_code}%", len(parent_code) + 1, len(parent_code) + 1),
                    )
                    max_suffix = int((cur.fetchone() or [0])[0] or 0)
            return f"{parent_code}{max_suffix + 1:03d}"
        except Exception:
            return f"{parent_code}001"
        finally:
            conn.close()

    def _name_exists(self, cur, name, ignore_id=None):
        if ignore_id:
            cur.execute("SELECT 1 FROM finance.customers WHERE customer_name=%s AND id<>%s LIMIT 1", (name, ignore_id))
        else:
            cur.execute("SELECT 1 FROM finance.customers WHERE customer_name=%s LIMIT 1", (name,))
        return cur.fetchone() is not None

    def _account_exists(self, cur, code, ignore_code=None):
        if ignore_code:
            cur.execute(
                "SELECT 1 FROM finance.accounts WHERE TRIM(account_code)=TRIM(%s) AND TRIM(account_code)<>TRIM(%s) LIMIT 1",
                (code, ignore_code),
            )
        else:
            cur.execute("SELECT 1 FROM finance.accounts WHERE TRIM(account_code)=TRIM(%s) LIMIT 1", (code,))
        return cur.fetchone() is not None

    def _insert_analytical_account(self, cur, code, name, parent_code):
        cols = ["account_code", "account_name"]
        vals = ["%s", "%s"]
        params = [code, name]

        if "parent_code" in self.accounts_columns:
            cols.append("parent_code")
            vals.append("%s")
            params.append(parent_code)
        if "account_level" in self.accounts_columns:
            cols.append("account_level")
            vals.append("%s")
            params.append(ACCOUNT_LEVEL_ANALYTICAL)
        if "is_active" in self.accounts_columns:
            cols.append("is_active")
            vals.append("%s")
            params.append(True)

        # noinspection SqlResolve
        cur.execute(f"INSERT INTO finance.accounts ({', '.join(cols)}) VALUES ({', '.join(vals)})", tuple(params))

    def action_new(self):
        self.selected_customer_id = None
        self.ent_name.delete(0, tk.END)
        self.ent_phone.delete(0, tk.END)
        self.cmb_control_account.set(f"{CUSTOMER_CONTROL_ACCOUNT_CODE} - حساب تحكم العملاء")
        self.account_code_var.set(self._next_account_code(CUSTOMER_CONTROL_ACCOUNT_CODE))
        self.cmb_status.set(self.STATUS_ACTIVE)
        self.ent_name.focus_set()

    def _parse_form(self):
        name = self.ent_name.get().strip()
        phone = self.ent_phone.get().strip()
        account_code = self.account_code_var.get().strip()
        status = self.cmb_status.get().strip() or self.STATUS_ACTIVE

        if not name:
            messagebox.showwarning("تنبيه", "اسم العميل مطلوب")
            self.ent_name.focus_set()
            return None
        if not account_code or not account_code.isdigit() or not account_code.startswith(CUSTOMER_CONTROL_ACCOUNT_CODE):
            messagebox.showwarning("تنبيه", "كود الحساب غير صحيح")
            self.ent_account_code.focus_set()
            return None

        return {
            "name": name,
            "phone": phone,
            "account_code": account_code,
            "status": status,
            "is_active": self._status_to_bool(status),
        }

    def action_save(self):
        data = self._parse_form()
        if not data:
            return

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    if self._name_exists(cur, data["name"]):
                        messagebox.showwarning("تنبيه", "اسم العميل موجود مسبقاً")
                        return
                    if self._account_exists(cur, data["account_code"]):
                        messagebox.showwarning("تنبيه", "كود الحساب مستخدم مسبقاً")
                        return

                    self._insert_analytical_account(cur, data["account_code"], data["name"], CUSTOMER_CONTROL_ACCOUNT_CODE)

                    cols = ["customer_name"]
                    vals = ["%s"]
                    params = [data["name"]]

                    if "phone" in self.customer_columns:
                        cols.append("phone")
                        vals.append("%s")
                        params.append(data["phone"] or None)
                    if "is_active" in self.customer_columns:
                        cols.append("is_active")
                        vals.append("%s")
                        params.append(data["is_active"])
                    if "control_account" in self.customer_columns:
                        cols.append("control_account")
                        vals.append("%s")
                        params.append(data["account_code"])
                    if "customer_code" in self.customer_columns:
                        cols.append("customer_code")
                        vals.append("%s")
                        params.append(data["account_code"])

                    # noinspection SqlResolve
                    cur.execute(f"INSERT INTO finance.customers ({', '.join(cols)}) VALUES ({', '.join(vals)})", tuple(params))

            messagebox.showinfo("نجاح", "تم حفظ العميل")
            self.refresh_rows()
            self.action_new()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ العميل"))
        finally:
            conn.close()

    def action_edit(self):
        if not self.selected_customer_id:
            messagebox.showwarning("تنبيه", "اختر عميلاً للتعديل")
            return

        data = self._parse_form()
        if not data:
            return

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    if self._name_exists(cur, data["name"], ignore_id=self.selected_customer_id):
                        messagebox.showwarning("تنبيه", "اسم العميل موجود مسبقاً")
                        return

                    old_code = ""
                    if "control_account" in self.customer_columns:
                        cur.execute("SELECT COALESCE(control_account, '') FROM finance.customers WHERE id=%s", (self.selected_customer_id,))
                        old_code = str((cur.fetchone() or [""])[0] or "").strip()

                    if old_code and old_code != data["account_code"] and "account_code" in self.ledger_columns:
                        cur.execute("SELECT 1 FROM finance.ledger WHERE TRIM(account_code)=TRIM(%s) LIMIT 1", (old_code,))
                        if cur.fetchone():
                            messagebox.showwarning("تنبيه", "لا يمكن تغيير كود الحساب لوجود حركات")
                            return

                    if old_code:
                        if self._account_exists(cur, data["account_code"], ignore_code=old_code):
                            messagebox.showwarning("تنبيه", "كود الحساب مستخدم مسبقاً")
                            return
                        cur.execute(
                            """
                            UPDATE finance.accounts
                            SET account_code=%s, account_name=%s
                            WHERE TRIM(account_code)=TRIM(%s)
                            """,
                            (data["account_code"], data["name"], old_code),
                        )
                        if cur.rowcount == 0:
                            self._insert_analytical_account(cur, data["account_code"], data["name"], CUSTOMER_CONTROL_ACCOUNT_CODE)
                    else:
                        if self._account_exists(cur, data["account_code"]):
                            messagebox.showwarning("تنبيه", "كود الحساب مستخدم مسبقاً")
                            return
                        self._insert_analytical_account(cur, data["account_code"], data["name"], CUSTOMER_CONTROL_ACCOUNT_CODE)

                    set_parts = ["customer_name=%s"]
                    params = [data["name"]]
                    if "phone" in self.customer_columns:
                        set_parts.append("phone=%s")
                        params.append(data["phone"] or None)
                    if "is_active" in self.customer_columns:
                        set_parts.append("is_active=%s")
                        params.append(data["is_active"])
                    if "control_account" in self.customer_columns:
                        set_parts.append("control_account=%s")
                        params.append(data["account_code"])
                    if "customer_code" in self.customer_columns:
                        set_parts.append("customer_code=%s")
                        params.append(data["account_code"])

                    params.append(self.selected_customer_id)
                    cur.execute(f"UPDATE finance.customers SET {', '.join(set_parts)} WHERE id=%s", tuple(params))

            messagebox.showinfo("نجاح", "تم تعديل العميل")
            self.refresh_rows()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل العميل"))
        finally:
            conn.close()

    def action_delete(self):
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
                    account_code = ""
                    if "control_account" in self.customer_columns:
                        cur.execute("SELECT COALESCE(control_account, '') FROM finance.customers WHERE id=%s", (self.selected_customer_id,))
                        account_code = str((cur.fetchone() or [""])[0] or "").strip()

                    if account_code and "account_code" in self.ledger_columns:
                        cur.execute("SELECT 1 FROM finance.ledger WHERE TRIM(account_code)=TRIM(%s) LIMIT 1", (account_code,))
                        if cur.fetchone():
                            messagebox.showwarning("تنبيه", "لا يمكن حذف العميل لوجود حركات محاسبية")
                            return

                    cur.execute("DELETE FROM finance.customers WHERE id=%s", (self.selected_customer_id,))
                    if account_code:
                        cur.execute("DELETE FROM finance.accounts WHERE TRIM(account_code)=TRIM(%s)", (account_code,))

            messagebox.showinfo("نجاح", "تم حذف العميل")
            self.refresh_rows()
            self.action_new()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حذف العميل"))
        finally:
            conn.close()

    def _on_tree_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        if not values:
            return

        self.selected_customer_id = int(values[0])
        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, values[1])

        self.ent_phone.delete(0, tk.END)
        self.ent_phone.insert(0, values[2])

        self.account_code_var.set(str(values[3] or "").strip())
        self.cmb_status.set(values[4] or self.STATUS_ACTIVE)

    def refresh_rows(self):
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    phone_expr = "COALESCE(phone, '')" if "phone" in self.customer_columns else "''"
                    account_expr = "COALESCE(control_account, '')" if "control_account" in self.customer_columns else "''"
                    status_expr = "COALESCE(is_active, true)" if "is_active" in self.customer_columns else "true"

                    cur.execute(
                        f"""
                        SELECT id, customer_name, {phone_expr}, {account_expr}, {status_expr}
                        FROM finance.customers
                        ORDER BY id DESC
                        """
                    )
                    rows = cur.fetchall() or []

            for row in rows:
                self.tree.insert("", tk.END, values=(row[0], row[1], row[2], row[3], self._bool_to_status(row[4])))
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل العملاء"))
        finally:
            conn.close()
