import tkinter as tk
from tkinter import messagebox, ttk

import ttkbootstrap as tb

from combobox_helper import bind_searchable_combobox, set_combobox_values
from db_connection import get_connection, get_db_error_message


class PropertyScreen:
    STATUS_VALUES = ("متاحة", "محجوزة", "مباعة")

    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#00ffff"
        self.text_color = "#ecf0f1"
        self.bg_color = "#f4f7f6"
        self.card_bg = "#3a4b5c"

        self.properties_columns = set()
        self.account_display_to_code = {}
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
        self.frame.grid_columnconfigure(1, weight=0)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        self.card = tb.Frame(self.frame, style="Land.Card.TFrame", padding=(18, 16, 18, 16))
        self.card.grid(row=0, column=1, sticky="n", padx=20, pady=20)
        self.card.grid_columnconfigure(0, weight=1, minsize=1080)
        self.card.grid_rowconfigure(3, weight=1)

        tb.Label(self.card, text="ترميز الأراضي", style="Land.Title.TLabel", anchor="e").grid(row=0, column=0, sticky="e", pady=(0, 10))

        self.form = tb.Frame(self.card, style="Land.Card.TFrame")
        self.form.grid(row=1, column=0, sticky="ew")
        self.form.grid_columnconfigure(0, weight=1)
        self.form.grid_columnconfigure(2, weight=1)

        self.ent_name = self._create_labeled_field(self.form, 0, 0, "اسم الأرض", field_type="entry")
        self.ent_price = self._create_labeled_field(self.form, 0, 2, "سعر الشراء", field_type="entry")
        self.ent_location = self._create_labeled_field(self.form, 1, 0, "الموقع", field_type="entry")
        self.cmb_status = self._create_labeled_field(self.form, 1, 2, "الحالة", field_type="combo", values=self.STATUS_VALUES, state="readonly")
        self.cmb_account = self._create_labeled_field(self.form, 2, 0, "رابط الحساب", field_type="combo", values=(), state="readonly")
        bind_searchable_combobox(self.cmb_account)
        self.account_code_var = tk.StringVar()
        self.ent_account_code = self._create_labeled_field(
            self.form,
            2,
            2,
            "كود الحساب",
            field_type="entry",
            textvariable=self.account_code_var,
            state="readonly",
        )

        self.cmb_status.set(self.STATUS_VALUES[0])
        self.cmb_account.bind("<<ComboboxSelected>>", self._on_account_selected)

        actions = tb.Frame(self.card, style="Land.Card.TFrame")
        actions.grid(row=2, column=0, sticky="ew", pady=(8, 12))
        actions.grid_columnconfigure(0, weight=1)
        actions_wrap = tb.Frame(actions, style="Land.Card.TFrame")
        actions_wrap.grid(row=0, column=0)

        tb.Button(actions_wrap, text="جديد", bootstyle="primary", command=self.action_new).grid(row=0, column=0, padx=4)
        tb.Button(actions_wrap, text="حفظ", bootstyle="success", command=self.action_save).grid(row=0, column=1, padx=4)
        tb.Button(actions_wrap, text="تعديل", bootstyle="warning", command=self.action_edit).grid(row=0, column=2, padx=4)
        tb.Button(actions_wrap, text="حذف", bootstyle="danger", command=self.action_delete).grid(row=0, column=3, padx=4)
        tb.Button(actions_wrap, text="بحث/تحديث", bootstyle="info", command=self.refresh_rows).grid(row=0, column=4, padx=4)

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
        self.tree.column("id", width=70, anchor="e")
        self.tree.column("name", width=240, anchor="e")
        self.tree.column("price", width=160, anchor="e")
        self.tree.column("location", width=240, anchor="e")
        self.tree.column("status", width=120, anchor="e")
        self.tree.column("account_code", width=140, anchor="e")

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _create_labeled_field(self, parent, row, col, label_text, field_type="entry", values=(), state="normal", textvariable=None):
        wrap = tb.Frame(parent, style="Land.Card.TFrame")
        wrap.grid(row=row, column=col, sticky="ew", padx=10, pady=12)
        wrap.grid_columnconfigure(0, weight=1)

        ttk.Label(wrap, text=label_text, style="Land.FieldLabel.TLabel", width=14).grid(row=0, column=1, sticky="e", padx=(0, 8))

        if field_type == "combo":
            widget = ttk.Combobox(
                wrap,
                values=values,
                state=state,
                justify="right",
                style="Land.Field.TCombobox",
                font=("Segoe UI", 11),
                textvariable=textvariable,
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
            )
            if state != "normal":
                widget.configure(state=state)

        widget.grid(row=0, column=0, sticky="ew")
        return widget

    def _refresh_schema_flags(self):
        conn = get_connection()
        if not conn:
            self.properties_columns = set()
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'finance' AND table_name = 'properties'
                        """
                    )
                    self.properties_columns = {row[0] for row in (cur.fetchall() or [])}
        except Exception:
            self.properties_columns = set()
        finally:
            conn.close()

    def _bind_enter_navigation(self):
        order = [self.ent_name, self.ent_price, self.ent_location, self.cmb_status, self.cmb_account]
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
        display = self.cmb_account.get().strip()
        self.account_code_var.set(self.account_display_to_code.get(display, ""))

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
            self.account_display_to_code.clear()
            for code, name in rows:
                code_text = str(code or "").strip()
                if not code_text:
                    continue
                label = (name or "").strip()
                display = f"{code_text} - {label}" if label else code_text
                self.account_display_to_code[display] = code_text
                displays.append(display)

            set_combobox_values(self.cmb_account, displays)
            if displays and not self.cmb_account.get().strip():
                self.cmb_account.set(displays[0])
                self._on_account_selected()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل حسابات الأراضي"))
        finally:
            conn.close()

    def _clear_form(self):
        self.ent_name.delete(0, tk.END)
        self.ent_price.delete(0, tk.END)
        self.ent_location.delete(0, tk.END)
        self.cmb_status.set(self.STATUS_VALUES[0])
        if self.cmb_account.cget("values"):
            self.cmb_account.set(self.cmb_account.cget("values")[0])
            self._on_account_selected()
        else:
            self.account_code_var.set("")

    def action_new(self):
        self.selected_property_id = None
        self._clear_form()
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
            messagebox.showwarning("تنبيه", "يرجى اختيار رابط الحساب")
            self.cmb_account.focus_set()
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

                    cur.execute(
                        f"INSERT INTO finance.properties ({', '.join(cols)}) VALUES ({', '.join(vals)})",
                        tuple(params),
                    )

            messagebox.showinfo("نجاح", "تم حفظ الأرض بنجاح")
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
                        params.append(data["account_code"])

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
                    cur.execute("DELETE FROM finance.properties WHERE id = %s", (self.selected_property_id,))

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

        code = str(values[5] or "").strip()
        self.account_code_var.set(code)
        for display, display_code in self.account_display_to_code.items():
            if display_code == code:
                self.cmb_account.set(display)
                break

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
