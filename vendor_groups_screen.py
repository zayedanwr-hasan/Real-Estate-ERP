import tkinter as tk
from tkinter import messagebox, ttk

import ttkbootstrap as tb

from app_constants import ACCOUNT_LEVEL_ANALYTICAL, VENDOR_CONTROL_ACCOUNT_CODE
from combobox_helper import bind_searchable_combobox, set_combobox_values
from db_connection import get_connection, get_db_error_message


class VendorGroupsScreen:
    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#00ffff"
        self.text_color = "#ecf0f1"
        self.bg_color = "#f4f7f6"
        self.card_bg = "#3a4b5c"

        self.property_display_to_id = {}
        self.control_account_display_to_code = {}

        self.pending_heirs = []
        self.selected_group_id = None

        self.group_cols = set()
        self.vendor_cols = set()
        self.group_name_col = None
        self.group_property_col = None
        self.group_account_col = None
        self.vendor_name_col = None
        self.vendor_phone_col = None
        self.vendor_group_id_col = None
        self.vendor_group_name_col = None
        self.vendor_property_id_col = None

        self._setup_styles()
        self._refresh_schema_flags()
        self._build_layout()

        self.refresh_control_accounts()
        self.refresh_properties(show_warning=True)
        self.refresh_groups()
        self._bind_enter_navigation()
        self.action_new()

    def _setup_styles(self):
        style = tb.Style()
        style.configure("VG.Root.TFrame", background=self.bg_color)
        style.configure("VG.Card.TFrame", background=self.card_bg, bordercolor=self.accent_color, borderwidth=1, relief="solid")
        style.configure("VG.Title.TLabel", background=self.card_bg, foreground=self.text_color, font=("Segoe UI", 18, "bold"))
        style.configure("VG.FieldLabel.TLabel", background=self.card_bg, foreground=self.text_color, font=("Segoe UI", 11, "bold"), anchor="e")
        style.configure(
            "VG.Field.TEntry",
            font=("Segoe UI", 11),
            foreground=self.primary_color,
            fieldbackground="#f9fbff",
            bordercolor=self.accent_color,
            lightcolor=self.accent_color,
            darkcolor=self.accent_color,
            insertcolor=self.primary_color,
            padding=6,
        )
        style.configure("VG.Field.TCombobox", font=("Segoe UI", 11), foreground=self.primary_color)

        style.configure("VG.Treeview", rowheight=30, font=("Segoe UI", 10), background=self.card_bg, fieldbackground=self.card_bg, foreground="white")
        style.configure("VG.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.sidebar_color, foreground="white")
        style.map("VG.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "#102130")])

    def _build_layout(self):
        self.frame = tb.Frame(self.master, style="VG.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=0)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)

        self.card = tb.Frame(self.frame, style="VG.Card.TFrame", padding=(18, 16, 18, 16))
        self.card.grid(row=0, column=1, sticky="n", padx=20, pady=20)
        self.card.grid_columnconfigure(0, weight=1, minsize=1140)
        self.card.grid_rowconfigure(4, weight=1)

        tb.Label(self.card, text="ترميز مجموعات الموردين/الورثة", style="VG.Title.TLabel", anchor="e").grid(row=0, column=0, sticky="e", pady=(0, 10))

        self.master_form = tb.Frame(self.card, style="VG.Card.TFrame")
        self.master_form.grid(row=1, column=0, sticky="ew")
        self.master_form.grid_columnconfigure(0, weight=1)
        self.master_form.grid_columnconfigure(2, weight=1)

        land_wrap = tb.Frame(self.master_form, style="VG.Card.TFrame")
        land_wrap.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        land_wrap.grid_columnconfigure(0, weight=1)

        ttk.Label(land_wrap, text="الأرض", style="VG.FieldLabel.TLabel", width=14).grid(row=0, column=2, sticky="e", padx=(0, 8))
        self.cmb_land = ttk.Combobox(land_wrap, justify="right", state="readonly", style="VG.Field.TCombobox", font=("Segoe UI", 11))
        self.cmb_land.grid(row=0, column=0, sticky="ew")
        bind_searchable_combobox(self.cmb_land)
        self.btn_add_land = tb.Button(land_wrap, text="+", bootstyle="info-outline", width=3, command=self.open_land_popup)
        self.btn_add_land.grid(row=0, column=1, padx=(6, 0))

        self.ent_group_name = self._create_labeled_field(self.master_form, 0, 2, "اسم المجموعة", field_type="entry")
        self.cmb_control_account = self._create_labeled_field(self.master_form, 1, 0, "حساب التحكم", field_type="combo", values=(), state="readonly")
        bind_searchable_combobox(self.cmb_control_account)

        actions = tb.Frame(self.card, style="VG.Card.TFrame")
        actions.grid(row=2, column=0, sticky="ew", pady=(8, 12))
        actions.grid_columnconfigure(0, weight=1)
        actions_wrap = tb.Frame(actions, style="VG.Card.TFrame")
        actions_wrap.grid(row=0, column=0)

        tb.Button(actions_wrap, text="جديد", bootstyle="primary", command=self.action_new).grid(row=0, column=0, padx=4)
        tb.Button(actions_wrap, text="حفظ", bootstyle="success", command=self.action_save).grid(row=0, column=1, padx=4)
        tb.Button(actions_wrap, text="تعديل", bootstyle="warning", command=self.action_edit).grid(row=0, column=2, padx=4)
        tb.Button(actions_wrap, text="حذف", bootstyle="danger", command=self.action_delete).grid(row=0, column=3, padx=4)
        tb.Button(actions_wrap, text="تحديث", bootstyle="info", command=self.refresh_groups).grid(row=0, column=4, padx=4)

        detail_card = tb.Frame(self.card, style="VG.Card.TFrame", padding=(12, 10, 12, 10))
        detail_card.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        detail_card.grid_columnconfigure(0, weight=1)

        tb.Label(detail_card, text="الورثة الأفراد", style="VG.FieldLabel.TLabel", anchor="e").grid(row=0, column=0, sticky="e", pady=(0, 6))

        quick = tb.Frame(detail_card, style="VG.Card.TFrame")
        quick.grid(row=1, column=0, sticky="ew")
        quick.grid_columnconfigure(0, weight=1)
        quick.grid_columnconfigure(2, weight=1)

        self.ent_heir_name = self._create_labeled_field(quick, 0, 0, "اسم المورد/الوارث", field_type="entry")
        self.ent_heir_phone = self._create_labeled_field(quick, 0, 2, "رقم الهاتف", field_type="entry")

        tb.Button(detail_card, text="إضافة للقائمة", bootstyle="secondary", command=self.add_pending_heir).grid(row=2, column=0, sticky="e", pady=(8, 6))

        heir_cols = ("idx", "name", "phone")
        self.heirs_tree = ttk.Treeview(detail_card, columns=heir_cols, show="headings", style="VG.Treeview", height=5)
        self.heirs_tree.heading("idx", text="#", anchor="e")
        self.heirs_tree.heading("name", text="الاسم", anchor="e")
        self.heirs_tree.heading("phone", text="الهاتف", anchor="e")
        self.heirs_tree.column("idx", width=50, anchor="e")
        self.heirs_tree.column("name", width=360, anchor="e")
        self.heirs_tree.column("phone", width=250, anchor="e")
        self.heirs_tree.grid(row=3, column=0, sticky="ew")

        groups_wrap = tb.Frame(self.card, style="VG.Card.TFrame")
        groups_wrap.grid(row=4, column=0, sticky="nsew")
        groups_wrap.grid_columnconfigure(0, weight=1)
        groups_wrap.grid_rowconfigure(0, weight=1)

        cols = ("id", "group_name", "control_account", "land")
        self.groups_tree = ttk.Treeview(groups_wrap, columns=cols, show="headings", style="VG.Treeview")
        self.groups_tree.heading("id", text="ID", anchor="e")
        self.groups_tree.heading("group_name", text="اسم المجموعة", anchor="e")
        self.groups_tree.heading("control_account", text="حساب التحكم", anchor="e")
        self.groups_tree.heading("land", text="الأرض", anchor="e")
        self.groups_tree.column("id", width=70, anchor="e")
        self.groups_tree.column("group_name", width=280, anchor="e")
        self.groups_tree.column("control_account", width=200, anchor="e")
        self.groups_tree.column("land", width=260, anchor="e")
        self.groups_tree.grid(row=0, column=0, sticky="nsew")
        self.groups_tree.bind("<<TreeviewSelect>>", self._on_group_select)

    def _create_labeled_field(self, parent, row, col, label_text, field_type="entry", values=(), state="normal"):
        wrap = tb.Frame(parent, style="VG.Card.TFrame")
        wrap.grid(row=row, column=col, sticky="ew", padx=10, pady=10)
        wrap.grid_columnconfigure(0, weight=1)

        ttk.Label(wrap, text=label_text, style="VG.FieldLabel.TLabel", width=14).grid(row=0, column=1, sticky="e", padx=(0, 8))

        if field_type == "combo":
            widget = ttk.Combobox(wrap, values=values, state=state, justify="right", style="VG.Field.TCombobox", font=("Segoe UI", 11))
            if len(values) > 0:
                widget.set(values[0])
        else:
            widget = ttk.Entry(wrap, style="VG.Field.TEntry", justify="right", font=("Segoe UI", 11))
            if state != "normal":
                widget.configure(state=state)

        widget.grid(row=0, column=0, sticky="ew")
        return widget

    def _pick_col(self, columns, names):
        for name in names:
            if name in columns:
                return name
        return None

    def _refresh_schema_flags(self):
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'finance' AND table_name = 'vendor_groups'
                    """)
                    self.group_cols = {r[0] for r in (cur.fetchall() or [])}

                    cur.execute("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'finance' AND table_name = 'vendors'
                    """)
                    self.vendor_cols = {r[0] for r in (cur.fetchall() or [])}
        finally:
            conn.close()

        self.group_name_col = self._pick_col(self.group_cols, ("group_name", "name"))
        self.group_property_col = self._pick_col(self.group_cols, ("property_id",))
        self.group_account_col = self._pick_col(self.group_cols, ("account_code", "control_account"))

        self.vendor_name_col = self._pick_col(self.vendor_cols, ("vendor_name", "full_name", "name"))
        self.vendor_phone_col = self._pick_col(self.vendor_cols, ("phone", "mobile", "phone_number", "vendor_phone"))
        self.vendor_group_id_col = self._pick_col(self.vendor_cols, ("group_id", "vendor_group_id"))
        self.vendor_group_name_col = self._pick_col(self.vendor_cols, ("group_name", "vendor_group_name"))
        self.vendor_property_id_col = self._pick_col(self.vendor_cols, ("property_id",))

    def _bind_enter_navigation(self):
        order = [self.cmb_land, self.ent_group_name, self.cmb_control_account, self.ent_heir_name, self.ent_heir_phone]
        for idx, widget in enumerate(order):
            def next_widget(_event, i=idx):
                if i == len(order) - 1:
                    self.add_pending_heir()
                else:
                    order[i + 1].focus_set()
                return "break"
            widget.bind("<Return>", next_widget)

    def _set_form_enabled(self, enabled):
        entry_state = tk.NORMAL if enabled else tk.DISABLED
        combo_state = "readonly" if enabled else tk.DISABLED

        self.cmb_land.configure(state=combo_state)
        self.ent_group_name.configure(state=entry_state)
        self.cmb_control_account.configure(state=combo_state)
        self.ent_heir_name.configure(state=entry_state)
        self.ent_heir_phone.configure(state=entry_state)

    def refresh_properties(self, show_warning=False):
        self.property_display_to_id.clear()
        conn = get_connection()
        if not conn:
            self._set_form_enabled(False)
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, property_name FROM finance.properties ORDER BY property_name")
                    rows = cur.fetchall() or []
            values = []
            for pid, name in rows:
                display = (name or "").strip()
                if not display:
                    continue
                values.append(display)
                self.property_display_to_id[display] = pid

            self.cmb_land.configure(values=values)
            if values:
                if self.cmb_land.get().strip() not in self.property_display_to_id:
                    self.cmb_land.set(values[0])
                self._set_form_enabled(True)
            else:
                self.cmb_land.set("")
                self._set_form_enabled(False)
                if show_warning:
                    messagebox.showwarning("تنبيه", "لا توجد أراضي حالياً، يرجى إضافة أرض أولاً")
        except Exception as exc:
            self._set_form_enabled(False)
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل الأراضي"))
        finally:
            conn.close()

    def refresh_control_accounts(self):
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
                        WHERE TRIM(account_code) = %s
                        ORDER BY account_code
                        """,
                        (VENDOR_CONTROL_ACCOUNT_CODE,),
                    )
                    rows = cur.fetchall() or []
                    if not rows:
                        cur.execute(
                            """
                            SELECT account_code, account_name
                            FROM finance.accounts
                            WHERE is_active = true
                              AND account_level = 'تحليلي'
                              AND (parent_code = '21' OR account_code LIKE '21%')
                            ORDER BY account_code
                            """
                        )
                        rows = cur.fetchall() or []

            displays = []
            self.control_account_display_to_code.clear()
            for code, name in rows:
                code_txt = str(code or "").strip()
                if not code_txt:
                    continue
                name_txt = (name or "").strip()
                display = f"{code_txt} - {name_txt}" if name_txt else code_txt
                self.control_account_display_to_code[display] = code_txt
                displays.append(display)

            set_combobox_values(self.cmb_control_account, displays)
            default_display = None
            for display, code in self.control_account_display_to_code.items():
                if code == VENDOR_CONTROL_ACCOUNT_CODE:
                    default_display = display
                    break
            if default_display:
                self.cmb_control_account.set(default_display)
            elif displays and not self.cmb_control_account.get().strip():
                self.cmb_control_account.set(displays[0])
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل حسابات التحكم"))
        finally:
            conn.close()

    def open_land_popup(self):
        try:
            from properties_screen import PropertyScreen
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر فتح شاشة ترميز الأراضي"))
            return

        popup = tk.Toplevel(self.master.winfo_toplevel())
        popup.title("ترميز الأراضي")
        popup.geometry("1460x900")
        popup.transient(self.master.winfo_toplevel())
        popup.grab_set()

        try:
            PropertyScreen(popup)
        except Exception as exc:
            popup.destroy()
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل شاشة ترميز الأراضي"))
            return

        self.master.winfo_toplevel().wait_window(popup)
        self.refresh_properties(show_warning=True)

    def _clear_heir_inputs(self):
        self.ent_heir_name.delete(0, tk.END)
        self.ent_heir_phone.delete(0, tk.END)

    def _refresh_pending_heirs_tree(self):
        for item in self.heirs_tree.get_children():
            self.heirs_tree.delete(item)
        for idx, heir in enumerate(self.pending_heirs, start=1):
            self.heirs_tree.insert("", tk.END, values=(idx, heir["name"], heir["phone"]))

    def add_pending_heir(self):
        name = self.ent_heir_name.get().strip()
        phone = self.ent_heir_phone.get().strip()
        if not name:
            messagebox.showwarning("تنبيه", "اسم المورد/الوارث مطلوب")
            self.ent_heir_name.focus_set()
            return
        self.pending_heirs.append({"name": name, "phone": phone})
        self._clear_heir_inputs()
        self._refresh_pending_heirs_tree()
        self.ent_heir_name.focus_set()

    def _next_group_account_code(self, cur, parent_code):
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

    def _account_code_exists(self, cur, account_code):
        cur.execute("SELECT 1 FROM finance.accounts WHERE TRIM(account_code)=TRIM(%s) LIMIT 1", (account_code,))
        return cur.fetchone() is not None

    def _upsert_group_account(self, cur, account_code, group_name, parent_code):
        cur.execute("SELECT 1 FROM finance.accounts WHERE TRIM(account_code)=TRIM(%s) LIMIT 1", (account_code,))
        if cur.fetchone():
            set_parts = ["account_name = %s", "parent_code = %s", "account_level = %s"]
            params = [group_name, parent_code, ACCOUNT_LEVEL_ANALYTICAL, account_code]
            # noinspection SqlResolve,SqlNoDataSourceInspection,SqlDialectInspection
            cur.execute(
                f"UPDATE finance.accounts SET {', '.join(set_parts)} WHERE TRIM(account_code)=TRIM(%s)",
                tuple(params),
            )
            return

        # noinspection SqlResolve,SqlNoDataSourceInspection,SqlDialectInspection
        cur.execute(
            "INSERT INTO finance.accounts (account_code, account_name, parent_code, account_level, is_active) "
            "VALUES (%s, %s, %s, %s, true)",
            (account_code, group_name, parent_code, ACCOUNT_LEVEL_ANALYTICAL),
        )

    def action_new(self):
        self.selected_group_id = None
        self.ent_group_name.delete(0, tk.END)
        if self.cmb_land.cget("values"):
            self.cmb_land.set(self.cmb_land.cget("values")[0])
        if self.cmb_control_account.cget("values"):
            self.cmb_control_account.set(self.cmb_control_account.cget("values")[0])
        self.pending_heirs = []
        self._clear_heir_inputs()
        self._refresh_pending_heirs_tree()
        self.ent_group_name.focus_set()

    def _validate_master(self):
        if not self.group_name_col or not self.group_property_col:
            messagebox.showerror("خطأ", "هيكل جدول مجموعات الموردين غير مكتمل")
            return None
        if not self.vendor_name_col or not self.vendor_group_id_col or not self.vendor_property_id_col:
            messagebox.showerror("خطأ", "هيكل جدول الموردين غير مكتمل للربط")
            return None

        group_name = self.ent_group_name.get().strip()
        if not group_name:
            messagebox.showwarning("تنبيه", "اسم المجموعة مطلوب")
            self.ent_group_name.focus_set()
            return None

        property_id = self.property_display_to_id.get(self.cmb_land.get().strip())
        if not property_id:
            messagebox.showwarning("تنبيه", "يرجى اختيار الأرض")
            self.cmb_land.focus_set()
            return None

        account_code = self.control_account_display_to_code.get(self.cmb_control_account.get().strip(), "")
        return {"group_name": group_name, "property_id": property_id, "parent_code": account_code or VENDOR_CONTROL_ACCOUNT_CODE}

    def _insert_heirs(self, cur, group_id, group_name, property_id):
        for heir in self.pending_heirs:
            cols = [self.vendor_name_col, self.vendor_group_id_col, self.vendor_property_id_col]
            vals = ["%s", "%s", "%s"]
            params = [heir["name"], group_id, property_id]

            if self.vendor_group_name_col:
                cols.append(self.vendor_group_name_col)
                vals.append("%s")
                params.append(group_name)
            if self.vendor_phone_col:
                cols.append(self.vendor_phone_col)
                vals.append("%s")
                params.append(heir["phone"])

            # noinspection SqlResolve,SqlNoDataSourceInspection,SqlDialectInspection
            cur.execute(
                f"INSERT INTO finance.vendors ({', '.join(cols)}) VALUES ({', '.join(vals)})",
                tuple(params),
            )

    def action_save(self):
        data = self._validate_master()
        if not data:
            return
        if not self.pending_heirs:
            messagebox.showwarning("تنبيه", "أضف وارثاً واحداً على الأقل قبل الحفظ")
            self.ent_heir_name.focus_set()
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    group_account_code = self._next_group_account_code(cur, data["parent_code"])
                    while self._account_code_exists(cur, group_account_code):
                        group_account_code = self._next_group_account_code(cur, data["parent_code"])

                    self._upsert_group_account(cur, group_account_code, data["group_name"], data["parent_code"])

                    cols = [self.group_name_col, self.group_property_col]
                    vals = ["%s", "%s"]
                    params = [data["group_name"], data["property_id"]]
                    if self.group_account_col:
                        cols.append(self.group_account_col)
                        vals.append("%s")
                        params.append(group_account_code)

                    # noinspection SqlResolve,SqlNoDataSourceInspection,SqlDialectInspection
                    cur.execute(
                        f"INSERT INTO finance.vendor_groups ({', '.join(cols)}) VALUES ({', '.join(vals)}) RETURNING id",
                        tuple(params),
                    )
                    group_id = cur.fetchone()[0]
                    self._insert_heirs(cur, group_id, data["group_name"], data["property_id"])

            messagebox.showinfo("نجاح", "تم حفظ المجموعة والورثة بنجاح")
            self.refresh_groups()
            self.action_new()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ المجموعة والورثة"))
        finally:
            conn.close()

    def action_edit(self):
        if not self.selected_group_id:
            messagebox.showwarning("تنبيه", "يرجى اختيار مجموعة من الجدول أولاً")
            return
        data = self._validate_master()
        if not data:
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    current_group_account = ""
                    if self.group_account_col:
                        cur.execute(f"SELECT COALESCE({self.group_account_col}, '') FROM finance.vendor_groups WHERE id = %s", (self.selected_group_id,))
                        current_group_account = str((cur.fetchone() or [""])[0] or "").strip()

                    if not current_group_account:
                        current_group_account = self._next_group_account_code(cur, data["parent_code"])
                        while self._account_code_exists(cur, current_group_account):
                            current_group_account = self._next_group_account_code(cur, data["parent_code"])

                    self._upsert_group_account(cur, current_group_account, data["group_name"], data["parent_code"])

                    set_parts = [f"{self.group_name_col} = %s", f"{self.group_property_col} = %s"]
                    params = [data["group_name"], data["property_id"]]
                    if self.group_account_col:
                        set_parts.append(f"{self.group_account_col} = %s")
                        params.append(current_group_account)
                    params.append(self.selected_group_id)

                    cur.execute(
                        f"UPDATE finance.vendor_groups SET {', '.join(set_parts)} WHERE id = %s",
                        tuple(params),
                    )

                    if self.pending_heirs:
                        self._insert_heirs(cur, self.selected_group_id, data["group_name"], data["property_id"])

            messagebox.showinfo("نجاح", "تم تعديل المجموعة")
            self.refresh_groups()
            self.action_new()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل المجموعة"))
        finally:
            conn.close()

    def action_delete(self):
        if not self.selected_group_id:
            messagebox.showwarning("تنبيه", "يرجى اختيار مجموعة من الجدول أولاً")
            return
        if not messagebox.askyesno("تأكيد", "هل تريد حذف المجموعة المحددة؟"):
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    group_account = ""
                    cur.execute("SELECT COALESCE(account_code, '') FROM finance.vendor_groups WHERE id = %s", (self.selected_group_id,))
                    group_account = str((cur.fetchone() or [""])[0] or "").strip()

                    if group_account:
                        cur.execute("SELECT 1 FROM finance.ledger WHERE TRIM(account_code)=TRIM(%s) LIMIT 1", (group_account,))
                        if cur.fetchone():
                            messagebox.showwarning("تنبيه", "لا يمكن حذف المجموعة لوجود حركات محاسبية")
                            return

                    if self.vendor_group_id_col:
                        cur.execute(f"DELETE FROM finance.vendors WHERE {self.vendor_group_id_col} = %s", (self.selected_group_id,))
                    cur.execute("DELETE FROM finance.vendor_groups WHERE id = %s", (self.selected_group_id,))
                    if group_account:
                        cur.execute("DELETE FROM finance.accounts WHERE TRIM(account_code)=TRIM(%s)", (group_account,))

            messagebox.showinfo("نجاح", "تم حذف المجموعة")
            self.refresh_groups()
            self.action_new()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حذف المجموعة"))
        finally:
            conn.close()

    def refresh_groups(self):
        for item in self.groups_tree.get_children():
            self.groups_tree.delete(item)

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    account_expr = f"vg.{self.group_account_col}" if self.group_account_col else "NULL"
                    cur.execute(
                        f"""
                        SELECT vg.id, vg.{self.group_name_col}, COALESCE({account_expr}, ''), COALESCE(p.property_name, '')
                        FROM finance.vendor_groups vg
                        LEFT JOIN finance.properties p ON vg.{self.group_property_col} = p.id
                        ORDER BY vg.id DESC
                        """
                    )
                    rows = cur.fetchall() or []
            for row in rows:
                self.groups_tree.insert("", tk.END, values=row)
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل مجموعات الموردين"))
        finally:
            conn.close()

    def _on_group_select(self, _event=None):
        selected = self.groups_tree.selection()
        if not selected:
            return
        values = self.groups_tree.item(selected[0], "values")
        if not values:
            return

        self.selected_group_id = int(values[0])
        self.ent_group_name.delete(0, tk.END)
        self.ent_group_name.insert(0, values[1] or "")

        land_name = (values[3] or "").strip()
        if land_name in self.property_display_to_id:
            self.cmb_land.set(land_name)

        control_code = (values[2] or "").strip()
        for display, code in self.control_account_display_to_code.items():
            if code == control_code:
                self.cmb_control_account.set(display)
                break

        self._load_group_members(self.selected_group_id)

    def _load_group_members(self, group_id):
        self.pending_heirs = []

        conn = get_connection()
        if not conn:
            self._refresh_pending_heirs_tree()
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    phone_col = self.vendor_phone_col or "NULL"
                    cur.execute(
                        f"""
                        SELECT {self.vendor_name_col}, {phone_col}
                        FROM finance.vendors
                        WHERE {self.vendor_group_id_col} = %s
                        ORDER BY id
                        """,
                        (group_id,),
                    )
                    rows = cur.fetchall() or []

            for name, phone in rows:
                self.pending_heirs.append({"name": (name or ""), "phone": (phone or "")})
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل أفراد المجموعة"))
        finally:
            conn.close()

        self._refresh_pending_heirs_tree()

