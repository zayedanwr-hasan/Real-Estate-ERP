import tkinter as tk
from tkinter import messagebox, ttk

import ttkbootstrap as tb

from app_constants import ACCOUNT_LEVEL_ANALYTICAL
from combobox_helper import set_combobox_values
from db_connection import get_connection, get_db_error_message


class PropertyScreen:
    STATUS_VALUES = ("متاحة", "محجوزة", "مباعة")
    PARENT_ACCOUNT_CODE = "1111"
    PARENT_ACCOUNT_DISPLAY = "1111 - الأراضي والعقارات"
    DEFAULT_ACCOUNT_TYPE = "أصول"
    DEFAULT_NATURE = "مدين"

    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#00ffff"
        self.text_color = "#ecf0f1"
        self.bg_color = "#f4f7f6"
        self.card_bg = "#3a4b5c"

        self.field_width_chars = 44
        self.properties_columns = set()
        self.accounts_columns = set()
        self.ledger_columns = set()
        self.selected_property_id = None

        self._setup_styles()
        self._refresh_schema_flags()
        self._build_layout()

        self.refresh_account_choices()
        self.refresh_rows()
        self._bind_enter_navigation()
        self.action_new()

    def _setup_styles(self):
        style = tb.Style()
        style.configure("Land.Root.TFrame", background=self.bg_color)
        style.configure(
            "Land.Card.TFrame",
            background=self.card_bg,
            bordercolor=self.accent_color,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Land.Title.TLabel",
            background=self.card_bg,
            foreground=self.text_color,
            font=("Segoe UI", 18, "bold"),
        )
        style.configure(
            "Land.FieldLabel.TLabel",
            background=self.card_bg,
            foreground=self.text_color,
            font=("Segoe UI", 11, "bold"),
            anchor="e",
        )
        style.configure(
            "Land.Field.TEntry",
            font=("Segoe UI", 11),
            foreground=self.primary_color,
            fieldbackground="#f9fbff",
            bordercolor=self.accent_color,
            lightcolor=self.accent_color,
            darkcolor=self.accent_color,
            insertcolor=self.primary_color,
            padding=6,
        )
        style.configure("Land.Field.TCombobox", font=("Segoe UI", 11), foreground=self.primary_color)

        style.configure("Land.Treeview", rowheight=30, font=("Segoe UI", 10), background=self.card_bg, fieldbackground=self.card_bg, foreground="white")
        style.configure("Land.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.sidebar_color, foreground="white")
        style.map("Land.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "#102130")])

    def _build_layout(self):
        self.frame = tb.Frame(self.master, style="Land.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        self.card = tb.Frame(self.frame, style="Land.Card.TFrame", padding=(30, 24, 30, 24))
        self.card.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)
        self.card.grid_columnconfigure(0, weight=1, minsize=1400)
        self.card.grid_rowconfigure(3, weight=1)

        tb.Label(self.card, text="ترميز الأراضي", style="Land.Title.TLabel", anchor="e").grid(row=0, column=0, sticky="e", pady=(0, 12))

        self.form = tb.Frame(self.card, style="Land.Card.TFrame")
        self.form.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        self.form.grid_columnconfigure(0, weight=1, uniform="formcol")
        self.form.grid_columnconfigure(2, weight=1, uniform="formcol")

        self.ent_name = self._create_labeled_field(self.form, 0, 0, "اسم الأرض", field_type="entry")
        self.ent_price = self._create_labeled_field(self.form, 0, 2, "سعر الشراء", field_type="entry")
        self.ent_location = self._create_labeled_field(self.form, 1, 0, "الموقع", field_type="entry")
        self.cmb_status = self._create_labeled_field(self.form, 1, 2, "الحالة", field_type="combo", values=self.STATUS_VALUES, state="readonly")
        self.cmb_account = self._create_labeled_field(
            self.form,
            2,
            0,
            "رابط الحساب الأب",
            field_type="combo",
            values=(self.PARENT_ACCOUNT_DISPLAY,),
            state="readonly",
        )
        self.account_code_var = tk.StringVar()
        self.ent_account_code = self._create_labeled_field(
            self.form,
            2,
            2,
            "كود الحساب",
            field_type="entry",
            textvariable=self.account_code_var,
            state="normal",
        )

        self.cmb_status.set(self.STATUS_VALUES[0])
        self.cmb_account.set(self.PARENT_ACCOUNT_DISPLAY)
        self.cmb_account.bind("<<ComboboxSelected>>", self._on_account_selected)

        actions = tb.Frame(self.card, style="Land.Card.TFrame")
        actions.grid(row=2, column=0, sticky="ew", pady=(10, 14))
        actions.grid_columnconfigure(0, weight=1)
        actions_wrap = tb.Frame(actions, style="Land.Card.TFrame")
        actions_wrap.grid(row=0, column=0)

        button_specs = [
            ("جديد", "primary", self.action_new),
            ("حفظ", "success", self.action_save),
            ("تعديل", "warning", self.action_edit),
            ("حذف", "danger", self.action_delete),
            ("تحديث", "info", self.refresh_rows),
        ]
        for idx, (label, style_name, command) in enumerate(button_specs):
            tb.Button(actions_wrap, text=label, bootstyle=style_name, command=command, width=12).grid(row=0, column=idx, padx=7)

        table_wrap = tb.Frame(self.card, style="Land.Card.TFrame")
        table_wrap.grid(row=3, column=0, sticky="nsew")
        table_wrap.grid_columnconfigure(0, weight=1)
        table_wrap.grid_rowconfigure(0, weight=1)

        cols = ("id", "name", "price", "location", "status", "account_code")
        self.tree = ttk.Treeview(table_wrap, columns=cols, show="headings", style="Land.Treeview")
        self.tree.heading("id", text="ID", anchor="e")
        self.tree.heading("name", text="اسم الأرض", anchor="e")
        self.tree.heading("price", text="سعر الشراء", anchor="e")
        self.tree.heading("location", text="الموقع", anchor="e")
        self.tree.heading("status", text="الحالة", anchor="e")
        self.tree.heading("account_code", text="كود الحساب", anchor="e")
        self.tree.column("id", width=80, anchor="e")
        self.tree.column("name", width=320, anchor="e")
        self.tree.column("price", width=190, anchor="e")
        self.tree.column("location", width=320, anchor="e")
        self.tree.column("status", width=140, anchor="e")
        self.tree.column("account_code", width=170, anchor="e")

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _create_labeled_field(self, parent, row, col, label_text, field_type="entry", values=(), state="normal", textvariable=None):
        wrap = tb.Frame(parent, style="Land.Card.TFrame")
        wrap.grid(row=row, column=col, sticky="ew", padx=10, pady=10)
        wrap.grid_columnconfigure(0, weight=1)

        ttk.Label(wrap, text=label_text, style="Land.FieldLabel.TLabel", width=14).grid(row=0, column=1, sticky="e", padx=(0, 10))

        if field_type == "combo":
            widget = ttk.Combobox(
                wrap,
                values=values,
                state=state,
                justify="right",
                style="Land.Field.TCombobox",
                font=("Segoe UI", 11),
                textvariable=textvariable,
                width=self.field_width_chars,
            )
            if len(values) > 0:
                widget.set(values[0])
        else:
            widget = ttk.Entry(
                wrap,
                style="Land.Field.TEntry",
                justify="right",
                font=("Segoe UI", 11),
                textvariable=textvariable,
                width=self.field_width_chars,
            )
            if state != "normal":
                widget.configure(state=state)

        widget.grid(row=0, column=0, sticky="ew")
        return widget

    def _refresh_schema_flags(self):
        conn = get_connection()
        if not conn:
            self.properties_columns = set()
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
                        WHERE table_schema = 'finance'
                          AND table_name IN ('properties', 'accounts', 'ledger')
                        """
                    )
                    rows = cur.fetchall() or []

            self.properties_columns = {col for table, col in rows if table == "properties"}
            self.accounts_columns = {col for table, col in rows if table == "accounts"}
            self.ledger_columns = {col for table, col in rows if table == "ledger"}
        except Exception:
            self.properties_columns = set()
            self.accounts_columns = set()
            self.ledger_columns = set()
        finally:
            conn.close()

    def _bind_enter_navigation(self):
        order = [self.ent_name, self.ent_price, self.ent_location, self.cmb_status, self.ent_account_code]
        for idx, widget in enumerate(order):

            def go_next(_event, i=idx):
                if i == len(order) - 1:
                    if self.selected_property_id:
                        self.action_edit()
                    else:
                        self.action_save()
                else:
                    order[i + 1].focus_set()
                return "break"

            widget.bind("<Return>", go_next)

    def _on_account_selected(self, _event=None):
        if not self.cmb_account.get().strip():
            self.cmb_account.set(self.PARENT_ACCOUNT_DISPLAY)

    def refresh_account_choices(self):
        set_combobox_values(self.cmb_account, [self.PARENT_ACCOUNT_DISPLAY])
        self.cmb_account.set(self.PARENT_ACCOUNT_DISPLAY)

    def _clear_form(self):
        self.ent_name.delete(0, tk.END)
        self.ent_price.delete(0, tk.END)
        self.ent_location.delete(0, tk.END)
        self.cmb_status.set(self.STATUS_VALUES[0])
        self.cmb_account.set(self.PARENT_ACCOUNT_DISPLAY)
        self.account_code_var.set("")

    def _get_next_sub_account_code(self):
        conn = get_connection()
        if not conn:
            return f"{self.PARENT_ACCOUNT_CODE}001"

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT COALESCE(MAX(CAST(SUBSTRING(TRIM(account_code) FROM 5) AS BIGINT)), 0)
                        FROM finance.accounts
                        WHERE TRIM(account_code) LIKE %s
                          AND LENGTH(TRIM(account_code)) > 4
                          AND SUBSTRING(TRIM(account_code) FROM 5) ~ '^[0-9]+$'
                        """,
                        (f"{self.PARENT_ACCOUNT_CODE}%",),
                    )
                    max_suffix = int((cur.fetchone() or [0])[0] or 0)

            next_suffix = max_suffix + 1
            return f"{self.PARENT_ACCOUNT_CODE}{next_suffix:03d}"
        except Exception:
            return f"{self.PARENT_ACCOUNT_CODE}001"
        finally:
            conn.close()

    def action_new(self):
        self.selected_property_id = None
        self._clear_form()
        self.account_code_var.set(self._get_next_sub_account_code())
        self.ent_name.focus_set()

    def _parse_form(self):
        name = self.ent_name.get().strip()
        price_text = self.ent_price.get().strip()
        location = self.ent_location.get().strip()
        status = self.cmb_status.get().strip() or self.STATUS_VALUES[0]
        account_code = self.account_code_var.get().strip()

        if not name:
            messagebox.showwarning("تنبيه", "اسم الأرض مطلوب")
            self.ent_name.focus_set()
            return None

        if not account_code:
            messagebox.showwarning("تنبيه", "يرجى إدخال كود الحساب")
            self.ent_account_code.focus_set()
            return None

        if not account_code.isdigit() or not account_code.startswith(self.PARENT_ACCOUNT_CODE) or len(account_code) <= len(self.PARENT_ACCOUNT_CODE):
            messagebox.showwarning("تنبيه", "كود الحساب يجب أن يبدأ بـ 1111 ويكون رقمياً")
            self.ent_account_code.focus_set()
            return None

        if price_text:
            try:
                purchase_price = float(price_text.replace(",", ""))
            except ValueError:
                messagebox.showwarning("تنبيه", "سعر الشراء يجب أن يكون رقمًا")
                self.ent_price.focus_set()
                return None
        else:
            purchase_price = 0.0

        return {
            "name": name,
            "purchase_price": purchase_price,
            "location": location,
            "status": status,
            "account_code": account_code,
            "parent_code": self.PARENT_ACCOUNT_CODE,
        }

    def _name_exists(self, cur, name, ignore_id=None):
        if ignore_id:
            cur.execute(
                "SELECT 1 FROM finance.properties WHERE property_name = %s AND id <> %s LIMIT 1",
                (name, ignore_id),
            )
        else:
            cur.execute(
                "SELECT 1 FROM finance.properties WHERE property_name = %s LIMIT 1",
                (name,),
            )
        return cur.fetchone() is not None

    def _account_code_exists(self, cur, account_code, ignore_code=None):
        if ignore_code:
            cur.execute(
                "SELECT 1 FROM finance.accounts WHERE TRIM(account_code) = TRIM(%s) AND TRIM(account_code) <> TRIM(%s) LIMIT 1",
                (account_code, ignore_code),
            )
        else:
            cur.execute(
                "SELECT 1 FROM finance.accounts WHERE TRIM(account_code) = TRIM(%s) LIMIT 1",
                (account_code,),
            )
        return cur.fetchone() is not None

    def _ledger_has_transactions(self, cur, account_code):
        if not account_code or "account_code" not in self.ledger_columns:
            return False
        cur.execute("SELECT 1 FROM finance.ledger WHERE TRIM(account_code) = TRIM(%s) LIMIT 1", (account_code,))
        return cur.fetchone() is not None

    def _insert_account_row(self, cur, account_code, account_name):
        cols = ["account_code", "account_name"]
        vals = ["%s", "%s"]
        params = [account_code, account_name]

        if "parent_code" in self.accounts_columns:
            cols.append("parent_code")
            vals.append("%s")
            params.append(self.PARENT_ACCOUNT_CODE)
        if "account_level" in self.accounts_columns:
            cols.append("account_level")
            vals.append("%s")
            params.append(ACCOUNT_LEVEL_ANALYTICAL)
        if "account_type" in self.accounts_columns:
            cols.append("account_type")
            vals.append("%s")
            params.append(self.DEFAULT_ACCOUNT_TYPE)
        if "nature" in self.accounts_columns:
            cols.append("nature")
            vals.append("%s")
            params.append(self.DEFAULT_NATURE)
        if "is_active" in self.accounts_columns:
            cols.append("is_active")
            vals.append("%s")
            params.append(True)

        # noinspection SqlResolve
        cur.execute(
            f"INSERT INTO finance.accounts ({', '.join(cols)}) VALUES ({', '.join(vals)})",
            tuple(params),
        )

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
                        messagebox.showwarning("تنبيه", "اسم الأرض موجود مسبقاً")
                        self.ent_name.focus_set()
                        return

                    if self._account_code_exists(cur, data["account_code"]):
                        messagebox.showwarning("تنبيه", "كود الحساب مستخدم مسبقاً")
                        self.ent_account_code.focus_set()
                        return

                    self._insert_account_row(cur, data["account_code"], data["name"])

                    cols = ["property_name"]
                    vals = ["%s"]
                    params = [data["name"]]

                    if "purchase_price" in self.properties_columns:
                        cols.append("purchase_price")
                        vals.append("%s")
                        params.append(data["purchase_price"])
                    if "total_cost" in self.properties_columns:
                        cols.append("total_cost")
                        vals.append("%s")
                        params.append(data["purchase_price"])
                    if "location" in self.properties_columns:
                        cols.append("location")
                        vals.append("%s")
                        params.append(data["location"])
                    if "status" in self.properties_columns:
                        cols.append("status")
                        vals.append("%s")
                        params.append(data["status"])
                    if "account_code" in self.properties_columns:
                        cols.append("account_code")
                        vals.append("%s")
                        params.append(data["account_code"])

                    # noinspection SqlResolve
                    cur.execute(
                        f"INSERT INTO finance.properties ({', '.join(cols)}) VALUES ({', '.join(vals)})",
                        tuple(params),
                    )

            messagebox.showinfo("نجاح", "تم حفظ الأرض والحساب المرتبط بنجاح")
            self.refresh_rows()
            self.action_new()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ الأرض"))
        finally:
            conn.close()

    def action_edit(self):
        if not self.selected_property_id:
            messagebox.showwarning("تنبيه", "يرجى اختيار أرض من الجدول أولاً")
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
                    if self._name_exists(cur, data["name"], ignore_id=self.selected_property_id):
                        messagebox.showwarning("تنبيه", "اسم الأرض موجود مسبقاً")
                        self.ent_name.focus_set()
                        return

                    cur.execute(
                        "SELECT COALESCE(account_code, '') FROM finance.properties WHERE id = %s",
                        (self.selected_property_id,),
                    )
                    row = cur.fetchone()
                    if not row:
                        messagebox.showwarning("تنبيه", "السجل المحدد لم يعد موجوداً")
                        self.refresh_rows()
                        self.action_new()
                        return

                    old_account_code = str(row[0] or "").strip()
                    new_account_code = data["account_code"]

                    if old_account_code and old_account_code != new_account_code:
                        if self._ledger_has_transactions(cur, old_account_code):
                            messagebox.showwarning("تنبيه", "لا يمكن تعديل كود الحساب لوجود حركات في دفتر الأستاذ")
                            self.ent_account_code.focus_set()
                            return
                        if self._account_code_exists(cur, new_account_code, ignore_code=old_account_code):
                            messagebox.showwarning("تنبيه", "كود الحساب الجديد مستخدم مسبقاً")
                            self.ent_account_code.focus_set()
                            return

                    if old_account_code:
                        acc_set_parts = ["account_name = %s"]
                        acc_params = [data["name"]]

                        if old_account_code != new_account_code:
                            acc_set_parts.append("account_code = %s")
                            acc_params.append(new_account_code)
                        if "parent_code" in self.accounts_columns:
                            acc_set_parts.append("parent_code = %s")
                            acc_params.append(self.PARENT_ACCOUNT_CODE)
                        if "account_level" in self.accounts_columns:
                            acc_set_parts.append("account_level = %s")
                            acc_params.append(ACCOUNT_LEVEL_ANALYTICAL)

                        acc_params.append(old_account_code)
                        cur.execute(
                            f"UPDATE finance.accounts SET {', '.join(acc_set_parts)} WHERE TRIM(account_code) = TRIM(%s)",
                            tuple(acc_params),
                        )

                        if cur.rowcount == 0:
                            self._insert_account_row(cur, new_account_code, data["name"])
                    else:
                        if self._account_code_exists(cur, new_account_code):
                            messagebox.showwarning("تنبيه", "كود الحساب مستخدم مسبقاً")
                            self.ent_account_code.focus_set()
                            return
                        self._insert_account_row(cur, new_account_code, data["name"])

                    set_parts = ["property_name = %s"]
                    params = [data["name"]]

                    if "purchase_price" in self.properties_columns:
                        set_parts.append("purchase_price = %s")
                        params.append(data["purchase_price"])
                    if "total_cost" in self.properties_columns:
                        set_parts.append("total_cost = %s")
                        params.append(data["purchase_price"])
                    if "location" in self.properties_columns:
                        set_parts.append("location = %s")
                        params.append(data["location"])
                    if "status" in self.properties_columns:
                        set_parts.append("status = %s")
                        params.append(data["status"])
                    if "account_code" in self.properties_columns:
                        set_parts.append("account_code = %s")
                        params.append(new_account_code)

                    params.append(self.selected_property_id)
                    cur.execute(
                        f"UPDATE finance.properties SET {', '.join(set_parts)} WHERE id = %s",
                        tuple(params),
                    )

            messagebox.showinfo("نجاح", "تم تعديل الأرض بنجاح")
            self.refresh_rows()
            self.action_new()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل الأرض"))
        finally:
            conn.close()

    def action_delete(self):
        if not self.selected_property_id:
            messagebox.showwarning("تنبيه", "يرجى اختيار أرض من الجدول أولاً")
            return

        if not messagebox.askyesno("تأكيد", "هل تريد حذف الأرض المحددة؟"):
            return

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COALESCE(account_code, '') FROM finance.properties WHERE id = %s",
                        (self.selected_property_id,),
                    )
                    row = cur.fetchone()
                    account_code = str((row or [""])[0] or "").strip()

                    if self._ledger_has_transactions(cur, account_code):
                        messagebox.showwarning("تنبيه", "لا يمكن حذف الأرض لأن الحساب المرتبط عليه حركات محاسبية")
                        return

                    cur.execute("DELETE FROM finance.properties WHERE id = %s", (self.selected_property_id,))
                    if account_code:
                        cur.execute("DELETE FROM finance.accounts WHERE TRIM(account_code) = TRIM(%s)", (account_code,))

            messagebox.showinfo("نجاح", "تم حذف الأرض")
            self.refresh_rows()
            self.action_new()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حذف الأرض"))
        finally:
            conn.close()

    def _on_tree_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        if not values:
            return

        self.selected_property_id = int(values[0])
        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, values[1])

        self.ent_price.delete(0, tk.END)
        self.ent_price.insert(0, values[2])

        self.ent_location.delete(0, tk.END)
        self.ent_location.insert(0, values[3])

        self.cmb_status.set(values[4] or self.STATUS_VALUES[0])
        self.cmb_account.set(self.PARENT_ACCOUNT_DISPLAY)
        self.account_code_var.set(str(values[5] or "").strip())

    def refresh_rows(self):
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
                        SELECT
                            id,
                            property_name,
                            COALESCE(purchase_price, 0) AS purchase_price,
                            COALESCE(location, '') AS location,
                            COALESCE(status, '') AS status,
                            COALESCE(account_code, '') AS account_code
                        FROM finance.properties
                        ORDER BY id DESC
                        """
                    )
                    rows = cur.fetchall() or []

            for row in rows:
                self.tree.insert("", tk.END, values=row)
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل بيانات الأراضي"))
        finally:
            conn.close()
