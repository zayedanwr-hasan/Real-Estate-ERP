import tkinter as tk
from tkinter import messagebox, ttk

import ttkbootstrap as tb

from app_constants import ACCOUNT_LEVEL_ANALYTICAL
from db_connection import get_connection, get_db_error_message


class FundCodingScreen:
    STATUS_ACTIVE = "فعال"
    STATUS_INACTIVE = "غير فعال"
    DEFAULT_PARENT_CODE = "1101"

    def __init__(self, master):
        self.master = master

        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#00ffff"
        self.text_color = "#ecf0f1"
        self.bg_color = "#f4f7f6"
        self.card_bg = "#3a4b5c"

        self.selected_account_id = None
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
        style.configure("Fund.Root.TFrame", background=self.bg_color)
        style.configure("Fund.Card.TFrame", background=self.card_bg, bordercolor=self.accent_color, borderwidth=1, relief="solid")
        style.configure("Fund.Title.TLabel", background=self.card_bg, foreground=self.text_color, font=("Segoe UI", 18, "bold"))
        style.configure("Fund.FieldLabel.TLabel", background=self.card_bg, foreground=self.text_color, font=("Segoe UI", 11, "bold"), anchor="e")
        style.configure(
            "Fund.Field.TEntry",
            font=("Segoe UI", 11),
            foreground=self.primary_color,
            fieldbackground="#f9fbff",
            bordercolor=self.accent_color,
            lightcolor=self.accent_color,
            darkcolor=self.accent_color,
            insertcolor=self.primary_color,
            padding=6,
        )
        style.configure("Fund.Field.TCombobox", font=("Segoe UI", 11), foreground=self.primary_color)

        style.configure("Fund.Treeview", rowheight=30, font=("Segoe UI", 10), background=self.card_bg, fieldbackground=self.card_bg, foreground="white")
        style.configure("Fund.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.sidebar_color, foreground="white")
        style.map("Fund.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "#102130")])

    def _build_layout(self):
        self.frame = tb.Frame(self.master, style="Fund.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        self.card = tb.Frame(self.frame, style="Fund.Card.TFrame", padding=(24, 20, 24, 20))
        self.card.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)
        self.card.grid_columnconfigure(0, weight=1, minsize=1180)
        self.card.grid_rowconfigure(3, weight=1)

        tb.Label(self.card, text="ترميز الصناديق", style="Fund.Title.TLabel", anchor="e").grid(row=0, column=0, sticky="e", pady=(0, 12))

        self.form = tb.Frame(self.card, style="Fund.Card.TFrame")
        self.form.grid(row=1, column=0, sticky="ew")
        self.form.grid_columnconfigure(0, weight=1, uniform="fundcol")
        self.form.grid_columnconfigure(2, weight=1, uniform="fundcol")

        self.ent_name = self._create_labeled_field(self.form, 0, 0, "اسم الصندوق")
        self.ent_location = self._create_labeled_field(self.form, 0, 2, "الفرع/الموقع")
        self.cmb_parent = self._create_labeled_field(
            self.form,
            1,
            0,
            "حساب التحكم",
            field_type="combo",
            values=(f"{self.DEFAULT_PARENT_CODE} - الصندوق الرئيسي",),
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

        self.cmb_parent.set(f"{self.DEFAULT_PARENT_CODE} - الصندوق الرئيسي")
        self.cmb_status.set(self.STATUS_ACTIVE)

        actions = tb.Frame(self.card, style="Fund.Card.TFrame")
        actions.grid(row=2, column=0, sticky="ew", pady=(10, 14))
        actions.grid_columnconfigure(0, weight=1)
        actions_wrap = tb.Frame(actions, style="Fund.Card.TFrame")
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

        table_wrap = tb.Frame(self.card, style="Fund.Card.TFrame")
        table_wrap.grid(row=3, column=0, sticky="nsew")
        table_wrap.grid_columnconfigure(0, weight=1)
        table_wrap.grid_rowconfigure(0, weight=1)

        cols = ("id", "code", "name", "location", "parent", "status")
        self.tree = ttk.Treeview(table_wrap, columns=cols, show="headings", style="Fund.Treeview")
        self.tree.heading("id", text="ID", anchor="e")
        self.tree.heading("code", text="كود الحساب", anchor="e")
        self.tree.heading("name", text="اسم الصندوق", anchor="e")
        self.tree.heading("location", text="الفرع/الموقع", anchor="e")
        self.tree.heading("parent", text="حساب التحكم", anchor="e")
        self.tree.heading("status", text="الحالة", anchor="e")
        self.tree.column("id", width=80, anchor="e")
        self.tree.column("code", width=180, anchor="e")
        self.tree.column("name", width=260, anchor="e")
        self.tree.column("location", width=220, anchor="e")
        self.tree.column("parent", width=170, anchor="e")
        self.tree.column("status", width=130, anchor="e")

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self._bind_enter_navigation()

    def _create_labeled_field(self, parent, row, col, label_text, field_type="entry", values=(), state="normal", textvariable=None):
        wrap = tb.Frame(parent, style="Fund.Card.TFrame")
        wrap.grid(row=row, column=col, sticky="ew", padx=10, pady=10)
        wrap.grid_columnconfigure(0, weight=1)

        ttk.Label(wrap, text=label_text, style="Fund.FieldLabel.TLabel", width=14).grid(row=0, column=1, sticky="e", padx=(0, 10))

        if field_type == "combo":
            widget = ttk.Combobox(
                wrap,
                values=values,
                state=state,
                justify="right",
                style="Fund.Field.TCombobox",
                font=("Segoe UI", 11),
                width=self.field_width_chars,
                textvariable=textvariable,
            )
            if values:
                widget.set(values[0])
        else:
            widget = ttk.Entry(
                wrap,
                style="Fund.Field.TEntry",
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
        order = [self.ent_name, self.ent_location, self.ent_account_code, self.cmb_status]
        for idx, widget in enumerate(order):

            def go_next(_event, i=idx):
                if i == len(order) - 1:
                    if self.selected_account_id:
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
                        WHERE table_schema='finance' AND table_name IN ('accounts', 'ledger')
                        """
                    )
                    rows = cur.fetchall() or []
            self.accounts_columns = {col for table, col in rows if table == "accounts"}
            self.ledger_columns = {col for table, col in rows if table == "ledger"}
        except Exception:
            self.accounts_columns = set()
            self.ledger_columns = set()
        finally:
            conn.close()

    def _status_to_bool(self, status_text):
        return status_text != self.STATUS_INACTIVE

    def _bool_to_status(self, is_active):
        return self.STATUS_ACTIVE if bool(is_active) else self.STATUS_INACTIVE

    def _selected_parent_code(self):
        text = self.cmb_parent.get().strip()
        return text.split("-")[0].strip() if text else self.DEFAULT_PARENT_CODE

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

    def _account_exists(self, cur, code, ignore_code=None):
        if ignore_code:
            cur.execute(
                "SELECT 1 FROM finance.accounts WHERE TRIM(account_code)=TRIM(%s) AND TRIM(account_code)<>TRIM(%s) LIMIT 1",
                (code, ignore_code),
            )
        else:
            cur.execute("SELECT 1 FROM finance.accounts WHERE TRIM(account_code)=TRIM(%s) LIMIT 1", (code,))
        return cur.fetchone() is not None

    def action_new(self):
        self.selected_account_id = None
        self.ent_name.delete(0, tk.END)
        self.ent_location.delete(0, tk.END)
        self.cmb_parent.set(f"{self.DEFAULT_PARENT_CODE} - الصندوق الرئيسي")
        self.account_code_var.set(self._next_account_code(self._selected_parent_code()))
        self.cmb_status.set(self.STATUS_ACTIVE)
        self.ent_name.focus_set()

    def _parse_form(self):
        name = self.ent_name.get().strip()
        location = self.ent_location.get().strip()
        account_code = self.account_code_var.get().strip()
        parent_code = self._selected_parent_code()
        status = self.cmb_status.get().strip() or self.STATUS_ACTIVE

        if not name:
            messagebox.showwarning("تنبيه", "اسم الصندوق مطلوب")
            self.ent_name.focus_set()
            return None
        if not account_code or not account_code.isdigit() or not account_code.startswith(parent_code):
            messagebox.showwarning("تنبيه", "كود الحساب غير صحيح")
            self.ent_account_code.focus_set()
            return None

        return {
            "name": name,
            "location": location,
            "account_code": account_code,
            "parent_code": parent_code,
            "is_active": self._status_to_bool(status),
            "status": status,
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
                    if self._account_exists(cur, data["account_code"]):
                        messagebox.showwarning("تنبيه", "كود الحساب مستخدم مسبقاً")
                        return

                    cols = ["account_code", "account_name"]
                    vals = ["%s", "%s"]
                    params = [data["account_code"], data["name"]]

                    if "parent_code" in self.accounts_columns:
                        cols.append("parent_code")
                        vals.append("%s")
                        params.append(data["parent_code"])
                    if "account_level" in self.accounts_columns:
                        cols.append("account_level")
                        vals.append("%s")
                        params.append(ACCOUNT_LEVEL_ANALYTICAL)
                    if "is_active" in self.accounts_columns:
                        cols.append("is_active")
                        vals.append("%s")
                        params.append(data["is_active"])
                    if "description" in self.accounts_columns:
                        cols.append("description")
                        vals.append("%s")
                        params.append(data["location"] or None)

                    # noinspection SqlResolve
                    cur.execute(f"INSERT INTO finance.accounts ({', '.join(cols)}) VALUES ({', '.join(vals)})", tuple(params))

            messagebox.showinfo("نجاح", "تم حفظ الصندوق")
            self.refresh_rows()
            self.action_new()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ الصندوق"))
        finally:
            conn.close()

    def action_edit(self):
        if not self.selected_account_id:
            messagebox.showwarning("تنبيه", "اختر صندوقاً للتعديل")
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
                    cur.execute("SELECT COALESCE(account_code, '') FROM finance.accounts WHERE id=%s", (self.selected_account_id,))
                    old_code = str((cur.fetchone() or [""])[0] or "").strip()

                    if old_code != data["account_code"] and "account_code" in self.ledger_columns:
                        cur.execute("SELECT 1 FROM finance.ledger WHERE TRIM(account_code)=TRIM(%s) LIMIT 1", (old_code,))
                        if cur.fetchone():
                            messagebox.showwarning("تنبيه", "لا يمكن تغيير كود الحساب لوجود حركات")
                            return

                    if self._account_exists(cur, data["account_code"], ignore_code=old_code):
                        messagebox.showwarning("تنبيه", "كود الحساب مستخدم مسبقاً")
                        return

                    set_parts = ["account_code=%s", "account_name=%s"]
                    params = [data["account_code"], data["name"]]
                    if "parent_code" in self.accounts_columns:
                        set_parts.append("parent_code=%s")
                        params.append(data["parent_code"])
                    if "account_level" in self.accounts_columns:
                        set_parts.append("account_level=%s")
                        params.append(ACCOUNT_LEVEL_ANALYTICAL)
                    if "is_active" in self.accounts_columns:
                        set_parts.append("is_active=%s")
                        params.append(data["is_active"])
                    if "description" in self.accounts_columns:
                        set_parts.append("description=%s")
                        params.append(data["location"] or None)

                    params.append(self.selected_account_id)
                    cur.execute(f"UPDATE finance.accounts SET {', '.join(set_parts)} WHERE id=%s", tuple(params))

            messagebox.showinfo("نجاح", "تم تعديل الصندوق")
            self.refresh_rows()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل الصندوق"))
        finally:
            conn.close()

    def action_delete(self):
        if not self.selected_account_id:
            messagebox.showwarning("تنبيه", "اختر صندوقاً للحذف")
            return

        if not messagebox.askyesno("تأكيد", "هل تريد حذف الصندوق المحدد؟"):
            return

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COALESCE(account_code, '') FROM finance.accounts WHERE id=%s", (self.selected_account_id,))
                    code = str((cur.fetchone() or [""])[0] or "").strip()

                    if code and "account_code" in self.ledger_columns:
                        cur.execute("SELECT 1 FROM finance.ledger WHERE TRIM(account_code)=TRIM(%s) LIMIT 1", (code,))
                        if cur.fetchone():
                            messagebox.showwarning("تنبيه", "لا يمكن حذف الصندوق لوجود حركات محاسبية")
                            return

                    cur.execute("DELETE FROM finance.accounts WHERE id=%s", (self.selected_account_id,))

            messagebox.showinfo("نجاح", "تم حذف الصندوق")
            self.refresh_rows()
            self.action_new()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حذف الصندوق"))
        finally:
            conn.close()

    def _on_tree_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        if not values:
            return

        self.selected_account_id = int(values[0])
        self.account_code_var.set(str(values[1] or "").strip())

        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, values[2] or "")

        self.ent_location.delete(0, tk.END)
        self.ent_location.insert(0, values[3] or "")

        parent = str(values[4] or "").strip() or self.DEFAULT_PARENT_CODE
        self.cmb_parent.set(f"{parent} - حساب تحكم")
        self.cmb_status.set(values[5] or self.STATUS_ACTIVE)

    def refresh_rows(self):
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    status_expr = "COALESCE(is_active, true)" if "is_active" in self.accounts_columns else "true"
                    location_expr = "COALESCE(description, '')" if "description" in self.accounts_columns else "''"
                    parent_expr = "COALESCE(parent_code, '')" if "parent_code" in self.accounts_columns else "''"

                    cur.execute(
                        f"""
                        SELECT id, account_code, account_name, {location_expr}, {parent_expr}, {status_expr}
                        FROM finance.accounts
                        WHERE TRIM(parent_code) = %s OR TRIM(account_code) LIKE %s
                        ORDER BY account_code
                        """,
                        (self.DEFAULT_PARENT_CODE, f"{self.DEFAULT_PARENT_CODE}%"),
                    )
                    rows = cur.fetchall() or []

            for row in rows:
                self.tree.insert(
                    "",
                    tk.END,
                    values=(row[0], row[1], row[2], row[3], row[4], self._bool_to_status(row[5])),
                )
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل الصناديق"))
        finally:
            conn.close()
