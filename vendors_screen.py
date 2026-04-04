import tkinter as tk
from tkinter import messagebox, ttk

import ttkbootstrap as tb

from app_constants import VENDOR_CONTROL_ACCOUNT_CODE
from db_connection import get_connection, get_db_error_message


class VendorsScreen:
    STATUS_ACTIVE = "فعال"
    STATUS_INACTIVE = "غير فعال"

    def __init__(self, master):
        self.master = master

        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.card_color = "#e8eef3"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.bg_color = "#dde6ee"

        self.selected_vendor_id = None

        self.vendor_columns = set()
        self.phone_col = None
        self.nid_col = None
        self.control_col = None
        self.group_id_col = None
        self.group_name_col = None
        self.is_active_col = None

        self.group_display_to_data = {}

        self._setup_styles()
        self._build_layout()
        self._refresh_vendor_schema_flags()
        self._load_vendor_groups()
        self._load_rows()
        self._new_vendor()

    def _setup_styles(self):
        style = tb.Style()
        style.configure("Vend.Root.TFrame", background=self.bg_color)
        style.configure("Vend.Card.TFrame", background=self.card_color, bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("Vend.Header.TFrame", background=self.primary_color)
        style.configure("Vend.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 18, "bold"))
        style.configure("Vend.Label.TLabel", background=self.sidebar_color, foreground=self.text_color, font=("Segoe UI", 11, "bold"), anchor="e", padding=6)
        style.configure("Vend.Entry.TEntry", font=("Segoe UI", 11, "bold"), foreground=self.primary_color)
        style.configure("Vend.Combo.TCombobox", font=("Segoe UI", 11, "bold"), foreground=self.primary_color)

        style.configure("Vend.New.TButton", background="#2980b9", foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(10, 6))
        style.configure("Vend.Del.TButton", background="#e74c3c", foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(10, 6))
        style.configure("Vend.Edit.TButton", background="#f1c40f", foreground="#1b1b1b", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(10, 6))
        style.configure("Vend.Save.TButton", background="#27ae60", foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(10, 6))
        style.configure("Vend.Refresh.TButton", background="#16a085", foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(8, 5))

        style.configure("Vend.Treeview", rowheight=34, font=("Segoe UI", 10), background="#f7fafc", fieldbackground="#f7fafc", foreground=self.primary_color, borderwidth=0)
        style.configure("Vend.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.primary_color, foreground="white", relief="flat")
        style.map("Vend.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "white")])

    def _build_layout(self):
        self.frame = tb.Frame(self.master, style="Vend.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=0)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_rowconfigure(0, weight=0)
        self.frame.grid_rowconfigure(1, weight=1)

        self.card = tb.Frame(self.frame, style="Vend.Card.TFrame", padding=0)
        self.card.grid(row=0, column=1, sticky="n", padx=20, pady=(20, 12))
        self.card.grid_columnconfigure(0, weight=1, minsize=860)

        header = tb.Frame(self.card, style="Vend.Header.TFrame", padding=(20, 14))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        tb.Label(header, text="ترميز الموردين", style="Vend.Header.TLabel", anchor="e").grid(row=0, column=0, sticky="e")

        form_wrap = tb.Frame(self.card, style="Vend.Card.TFrame", padding=(30, 24, 30, 14))
        form_wrap.grid(row=1, column=0, sticky="ew")
        form_wrap.grid_columnconfigure(0, weight=1)

        self.ent_vendor_id = self._create_field_row(form_wrap, 0, "كود المورد", readonly=True)
        self.ent_name = self._create_field_row(form_wrap, 1, "الاسم الكلي")
        self.combo_group = self._create_field_row(form_wrap, 2, "مجموعة المورد", field_type="combo", values=("بدون مجموعة",), state="readonly")
        self.ent_phone = self._create_field_row(form_wrap, 3, "رقم الهاتف")
        self.ent_national_id = self._create_field_row(form_wrap, 4, "الهوية")
        self.ent_control = self._create_field_row(form_wrap, 5, "حساب التحكم", readonly=True)
        self.combo_status = self._create_field_row(form_wrap, 6, "الحالة", field_type="combo", values=(self.STATUS_ACTIVE, self.STATUS_INACTIVE), state="readonly")

        buttons_wrap = tb.Frame(self.card, style="Vend.Card.TFrame", padding=(16, 6, 16, 14))
        buttons_wrap.grid(row=2, column=0, sticky="ew")
        for idx in range(4):
            buttons_wrap.grid_columnconfigure(idx, weight=1)

        tb.Button(buttons_wrap, text="جديد", style="Vend.New.TButton", command=self._new_vendor).grid(row=0, column=3, padx=4, sticky="ew")
        tb.Button(buttons_wrap, text="حذف", style="Vend.Del.TButton", command=self._delete).grid(row=0, column=2, padx=4, sticky="ew")
        tb.Button(buttons_wrap, text="تعديل", style="Vend.Edit.TButton", command=self._edit).grid(row=0, column=1, padx=4, sticky="ew")
        tb.Button(buttons_wrap, text="حفظ", style="Vend.Save.TButton", command=self._save).grid(row=0, column=0, padx=4, sticky="ew")

        table_wrap = tb.Frame(self.frame, style="Vend.Card.TFrame", padding=(12, 10, 12, 12))
        table_wrap.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=24, pady=(0, 16))
        table_wrap.grid_columnconfigure(0, weight=1)
        table_wrap.grid_rowconfigure(1, weight=1)

        actions_bar = tb.Frame(table_wrap, style="Vend.Card.TFrame")
        actions_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        actions_bar.grid_columnconfigure(0, weight=1)
        tb.Button(actions_bar, text="تحديث", style="Vend.Refresh.TButton", command=self._load_rows).grid(row=0, column=0, sticky="e")

        cols = ("id", "name", "group", "phone", "national_id", "status")
        self.tree = ttk.Treeview(table_wrap, columns=cols, show="headings", style="Vend.Treeview")
        for col, title, width in (
            ("id", "ID", 70),
            ("name", "اسم المورد", 230),
            ("group", "المجموعة", 220),
            ("phone", "رقم الهاتف", 150),
            ("national_id", "الهوية", 140),
            ("status", "الحالة", 90),
        ):
            self.tree.heading(col, text=title, anchor="e")
            self.tree.column(col, width=width, anchor="e")

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        y_scroll.grid(row=1, column=1, sticky="ns")

        self.tree.tag_configure("odd", background="#f7fafc")
        self.tree.tag_configure("even", background="#edf3f8")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _create_field_row(self, parent, row, label_text, field_type="entry", readonly=False, values=None, state="normal"):
        row_wrap = tb.Frame(parent, style="Vend.Card.TFrame")
        row_wrap.grid(row=row, column=0, sticky="ew", pady=12)
        row_wrap.grid_columnconfigure(0, weight=1)

        ttk.Label(row_wrap, text=label_text, style="Vend.Label.TLabel", width=14).grid(row=0, column=1, sticky="e", padx=(0, 5))

        if field_type == "combo":
            widget = ttk.Combobox(
                row_wrap,
                values=values or (),
                state=state,
                justify="right",
                style="Vend.Combo.TCombobox",
                font=("Segoe UI", 11, "bold"),
            )
            if values:
                widget.set(values[0])
        else:
            widget = ttk.Entry(row_wrap, justify="right", style="Vend.Entry.TEntry", font=("Segoe UI", 11, "bold"))
            if readonly:
                widget.configure(state="readonly")

        widget.grid(row=0, column=0, sticky="ew")
        return widget

    def _set_entry(self, entry, value):
        was_readonly = str(entry.cget("state")) == "readonly"
        if was_readonly:
            entry.configure(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, value)
        if was_readonly:
            entry.configure(state="readonly")

    def _table_columns(self, cur, table_name):
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema='finance' AND table_name=%s
            """,
            (table_name,),
        )
        return {row[0] for row in (cur.fetchall() or [])}

    def _pick_column(self, columns, names):
        for name in names:
            if name in columns:
                return name
        return None

    def _refresh_vendor_schema_flags(self):
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cols = self._table_columns(cur, "vendors")
                    self.vendor_columns = cols
                    self.phone_col = self._pick_column(cols, ("phone", "mobile", "phone_number", "vendor_phone"))
                    self.nid_col = self._pick_column(cols, ("national_id", "id_number"))
                    self.control_col = "control_account" if "control_account" in cols else None
                    self.group_id_col = self._pick_column(cols, ("group_id", "vendor_group_id"))
                    self.group_name_col = self._pick_column(cols, ("group_name", "vendor_group_name"))
                    self.is_active_col = "is_active" if "is_active" in cols else None
        except Exception:
            self.vendor_columns = set()
            self.phone_col = None
            self.nid_col = None
            self.control_col = None
            self.group_id_col = None
            self.group_name_col = None
            self.is_active_col = None
        finally:
            conn.close()

    def _load_vendor_groups(self):
        self.group_display_to_data.clear()
        values = ["بدون مجموعة"]

        conn = get_connection()
        if not conn:
            self.combo_group.configure(values=values)
            self.combo_group.set("بدون مجموعة")
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cols = self._table_columns(cur, "vendor_groups")
                    if not cols:
                        self.combo_group.configure(values=values)
                        self.combo_group.set("بدون مجموعة")
                        return

                    id_col = "id" if "id" in cols else None
                    name_col = "group_name" if "group_name" in cols else None
                    code_col = "account_code" if "account_code" in cols else None

                    if not name_col:
                        self.combo_group.configure(values=values)
                        self.combo_group.set("بدون مجموعة")
                        return

                    select_cols = [name_col]
                    if id_col:
                        select_cols.insert(0, id_col)
                    if code_col:
                        select_cols.append(code_col)

                    cur.execute(f"SELECT {', '.join(select_cols)} FROM finance.vendor_groups ORDER BY {name_col}")
                    rows = cur.fetchall() or []

            for row in rows:
                idx = 0
                gid = None
                if id_col:
                    gid = row[idx]
                    idx += 1
                gname = row[idx] if idx < len(row) else ""
                idx += 1
                gcode = row[idx] if code_col and idx < len(row) else ""

                if not gname:
                    continue
                display = f"{gname} - {gcode}" if gcode else str(gname)
                self.group_display_to_data[display] = {
                    "id": gid,
                    "name": str(gname),
                    "account_code": str(gcode or ""),
                }
                values.append(display)

        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل مجموعات الموردين"))
        finally:
            conn.close()

        self.combo_group.configure(values=values)
        if self.combo_group.get().strip() not in values:
            self.combo_group.set("بدون مجموعة")

    def _status_to_bool(self, status_text):
        return status_text != self.STATUS_INACTIVE

    def _bool_to_status(self, is_active):
        return self.STATUS_ACTIVE if bool(is_active) else self.STATUS_INACTIVE

    def _fetch_next_vendor_id(self):
        conn = get_connection()
        if not conn:
            return "تلقائي"
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM finance.vendors")
                    row = cur.fetchone()
                    return str(row[0]) if row and row[0] is not None else "تلقائي"
        except Exception:
            return "تلقائي"
        finally:
            conn.close()

    def _new_vendor(self):
        self.selected_vendor_id = None
        self._set_entry(self.ent_vendor_id, self._fetch_next_vendor_id())
        self.ent_name.delete(0, tk.END)
        self.ent_phone.delete(0, tk.END)
        self.ent_national_id.delete(0, tk.END)
        self.combo_group.set("بدون مجموعة")
        self.combo_status.set(self.STATUS_ACTIVE)
        self._set_entry(self.ent_control, VENDOR_CONTROL_ACCOUNT_CODE)
        self.ent_name.focus_set()

    def _resolve_group_display(self, group_id, group_name):
        if group_id is not None:
            for display, data in self.group_display_to_data.items():
                if data.get("id") is not None and int(data.get("id")) == int(group_id):
                    return display

        if group_name:
            for display, data in self.group_display_to_data.items():
                if data.get("name") == str(group_name):
                    return display
            return str(group_name)

        return "بدون مجموعة"

    def _validate_inputs(self):
        name = self.ent_name.get().strip()
        if not name:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم المورد")
            self.ent_name.focus_set()
            return None

        group_display = self.combo_group.get().strip()
        group_data = self.group_display_to_data.get(group_display)

        return {
            "vendor_name": name,
            "phone": self.ent_phone.get().strip() or None,
            "national_id": self.ent_national_id.get().strip() or None,
            "control_account": VENDOR_CONTROL_ACCOUNT_CODE,
            "is_active": self._status_to_bool(self.combo_status.get().strip() or self.STATUS_ACTIVE),
            "group": group_data,
        }

    def _load_rows(self):
        self.tree.delete(*self.tree.get_children())
        self._refresh_vendor_schema_flags()
        self._load_vendor_groups()

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    phone_select = self.phone_col if self.phone_col else "NULL"
                    nid_select = self.nid_col if self.nid_col else "NULL"
                    control_select = f"COALESCE({self.control_col}, %s)" if self.control_col else "%s"
                    group_id_select = self.group_id_col if self.group_id_col else "NULL"
                    group_name_select = self.group_name_col if self.group_name_col else "NULL"
                    status_select = f"COALESCE({self.is_active_col}, true)" if self.is_active_col else "true"

                    cur.execute(
                        f"""
                        SELECT id, vendor_name, {phone_select}, {nid_select}, {control_select}, {group_id_select}, {group_name_select}, {status_select}
                        FROM finance.vendors
                        ORDER BY id DESC
                        """,
                        (VENDOR_CONTROL_ACCOUNT_CODE,),
                    )
                    rows = cur.fetchall() or []

            for idx, row in enumerate(rows):
                vendor_id, name, phone, nid, _control, group_id, group_name, is_active = row
                tag = "even" if idx % 2 == 0 else "odd"
                self.tree.insert(
                    "",
                    tk.END,
                    iid=str(vendor_id),
                    values=(
                        vendor_id,
                        name or "",
                        self._resolve_group_display(group_id, group_name),
                        phone or "",
                        nid or "",
                        self._bool_to_status(is_active),
                    ),
                    tags=(tag,),
                )
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل الموردين"))
        finally:
            conn.close()

    def _on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return

        data = self.tree.item(selected[0], "values")
        if not data:
            return

        self.selected_vendor_id = int(data[0])
        self._set_entry(self.ent_vendor_id, str(data[0]))

        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, data[1] or "")

        group_display = data[2] or "بدون مجموعة"
        if group_display not in self.combo_group.cget("values"):
            group_display = "بدون مجموعة"
        self.combo_group.set(group_display)

        self.ent_phone.delete(0, tk.END)
        self.ent_phone.insert(0, data[3] or "")

        self.ent_national_id.delete(0, tk.END)
        self.ent_national_id.insert(0, data[4] or "")

        self.combo_status.set(data[5] or self.STATUS_ACTIVE)
        self._set_entry(self.ent_control, VENDOR_CONTROL_ACCOUNT_CODE)

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
                    values = [payload["vendor_name"]]
                    extra_columns = []
                    extra_placeholders = []

                    if self.phone_col:
                        extra_columns.append(self.phone_col)
                        extra_placeholders.append("%s")
                        values.append(payload["phone"])
                    if self.nid_col:
                        extra_columns.append(self.nid_col)
                        extra_placeholders.append("%s")
                        values.append(payload["national_id"])
                    if self.control_col:
                        extra_columns.append(self.control_col)
                        extra_placeholders.append("%s")
                        values.append(payload["control_account"])
                    if self.is_active_col:
                        extra_columns.append(self.is_active_col)
                        extra_placeholders.append("%s")
                        values.append(payload["is_active"])

                    if self.group_id_col:
                        extra_columns.append(self.group_id_col)
                        extra_placeholders.append("%s")
                        values.append(payload["group"].get("id") if payload["group"] else None)
                    elif self.group_name_col:
                        extra_columns.append(self.group_name_col)
                        extra_placeholders.append("%s")
                        values.append(payload["group"].get("name") if payload["group"] else None)

                    extra_cols_sql = ", " + ", ".join(extra_columns) if extra_columns else ""
                    extra_vals_sql = ", " + ", ".join(extra_placeholders) if extra_placeholders else ""
                    sql = f"""
                        INSERT INTO finance.vendors (vendor_name{extra_cols_sql})
                        VALUES (%s{extra_vals_sql})
                    """
                    cur.execute(sql, tuple(values))

            self._load_rows()
            self._new_vendor()
            messagebox.showinfo("نجاح", "تم حفظ المورد")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ المورد"))
        finally:
            conn.close()

    def _edit(self):
        if not self.selected_vendor_id:
            messagebox.showwarning("تنبيه", "اختر مورداً للتعديل")
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
                    set_parts = ["vendor_name = %s"]
                    values = [payload["vendor_name"]]

                    if self.phone_col:
                        set_parts.append(f"{self.phone_col} = %s")
                        values.append(payload["phone"])
                    if self.nid_col:
                        set_parts.append(f"{self.nid_col} = %s")
                        values.append(payload["national_id"])
                    if self.control_col:
                        set_parts.append(f"{self.control_col} = %s")
                        values.append(payload["control_account"])
                    if self.is_active_col:
                        set_parts.append(f"{self.is_active_col} = %s")
                        values.append(payload["is_active"])

                    if self.group_id_col:
                        set_parts.append(f"{self.group_id_col} = %s")
                        values.append(payload["group"].get("id") if payload["group"] else None)
                    elif self.group_name_col:
                        set_parts.append(f"{self.group_name_col} = %s")
                        values.append(payload["group"].get("name") if payload["group"] else None)

                    values.append(self.selected_vendor_id)
                    cur.execute(
                        f"UPDATE finance.vendors SET {', '.join(set_parts)} WHERE id = %s",
                        tuple(values),
                    )

            self._load_rows()
            self._select_tree_row(self.selected_vendor_id)
            messagebox.showinfo("نجاح", "تم تعديل المورد")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل المورد"))
        finally:
            conn.close()

    def _delete(self):
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
                    cur.execute("DELETE FROM finance.vendors WHERE id = %s", (self.selected_vendor_id,))

            self._load_rows()
            self._new_vendor()
            messagebox.showinfo("نجاح", "تم حذف المورد")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حذف المورد"))
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
