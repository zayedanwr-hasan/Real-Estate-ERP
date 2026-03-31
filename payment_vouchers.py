import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog
import ttkbootstrap as ttk

from app_constants import SYSTEM_NAME, VOUCHER_TYPE_PAYMENT
from combobox_helper import bind_searchable_combobox, set_combobox_values
from db_connection import get_connection, get_db_error_message


class PaymentVoucherScreen:
    def __init__(self, master):
        self.master = master

        # ألوان النظام (مطابقة لهوية تطبيقك)
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.bg_color = "#f4f7f6"

        # متغيرات الحقول العلوية (Header)
        self.voucher_id_var = tk.StringVar(value="تلقائي")
        self.reference_no_var = tk.StringVar(value="10001")
        self.voucher_type_var = tk.StringVar(value=VOUCHER_TYPE_PAYMENT)
        self.currency_var = tk.StringVar(value="ريال يمني")
        self.cash_account_var = tk.StringVar()

        # متغيرات بيانات المستفيد
        self.beneficiary_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.related_property_var = tk.StringVar()

        # متغيرات محرر البند (Line Editor)
        self.line_account_code_var = tk.StringVar()
        self.line_account_name_var = tk.StringVar()
        self.line_amount_var = tk.StringVar(value="0.00")
        self.line_exchange_rate_var = tk.StringVar(value="1.00")
        # تم إلغاء وصف البند المنفصل والاكتفاء بالوصف العام

        # خرائط الحسابات
        self.account_display_to_code = {}
        self.account_code_to_name = {}
        self.account_code_to_display = {}

        # بيانات المستفيدين
        self.beneficiary_display_to_data = {}

        # البنود في الجدول
        self.line_items = []
        self.selected_line_index = None

        self._setup_styles()

        self.frame = ttk.Frame(master, style="App.Payment.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.main_card = ttk.Frame(self.frame, style="App.Payment.Card.TFrame")
        self.main_card.pack(fill="both", expand=True, padx=12, pady=12)

        self._build_header_buttons()
        self._build_form_content()

        # تحميل الحسابات والمستفيدين وربطها
        self.load_accounts()
        self.load_beneficiaries()
        self._reset_and_new()

    # إعداد أنماط واجهة المستخدم
    def _setup_styles(self):
        style = ttk.Style()
        style.configure("App.Payment.Root.TFrame", background=self.bg_color)
        style.configure("App.Payment.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("App.Payment.Header.TFrame", background=self.primary_color)
        style.configure("App.Payment.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 18, "bold"))
        style.configure("App.Payment.Content.TFrame", background="white")
        style.configure("App.Payment.FieldLabel.TLabel",
                        background=self.sidebar_color, foreground=self.text_color,
                        font=("Segoe UI", 11, "bold"), anchor="center", padding=6)
        style.configure("App.Payment.Field.TEntry",
                        fieldbackground="white", foreground=self.primary_color,
                        font=("Segoe UI", 11, "bold"))
        style.configure("App.Payment.Field.TCombobox",
                        fieldbackground="white", foreground=self.primary_color,
                        font=("Segoe UI", 11, "bold"))
        style.configure("App.Payment.Total.TFrame",
                        background="#f8f9fa", bordercolor="#d8e1e8",
                        borderwidth=1, relief="solid")
        style.configure("App.Payment.TotalAmount.TLabel",
                        background="#f8f9fa", foreground="#c0392b",
                        font=("Segoe UI", 15, "bold"))
        style.configure("App.Payment.TotalWords.TLabel",
                        background="#f8f9fa", foreground=self.sidebar_color,
                        font=("Segoe UI", 11, "bold"))
        style.configure("App.Payment.Primary.TButton",
                        background="#2980b9", foreground="white",
                        borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10,6))
        style.configure("App.Payment.Success.TButton",
                        background="#27ae60", foreground="white",
                        borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10,6))
        style.configure("App.Payment.Warning.TButton",
                        background="#f1c40f", foreground="#2c3e50",
                        borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10,6))
        style.configure("App.Payment.Danger.TButton",
                        background="#e74c3c", foreground="white",
                        borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10,6))
        style.configure("App.Payment.Info.TButton",
                        background="#8e44ad", foreground="white",
                        borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10,6))
        style.configure("App.Payment.History.TButton",
                        background="#16a085", foreground="white",
                        borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10,6))

        for btn_style in ("App.Payment.Primary.TButton", "App.Payment.Success.TButton",
                          "App.Payment.Warning.TButton", "App.Payment.Danger.TButton",
                          "App.Payment.Info.TButton", "App.Payment.History.TButton"):
            style.map(btn_style,
                      background=[("active", self.accent_color), ("pressed", self.accent_color)],
                      foreground=[("active", "white"), ("pressed", "white")])

        style.configure("App.Payment.Treeview",
                        background="white", fieldbackground="white",
                        foreground=self.primary_color, rowheight=32,
                        font=("Segoe UI", 10, "bold"))
        style.configure("App.Payment.Treeview.Heading",
                        background=self.primary_color, foreground="white",
                        font=("Segoe UI", 10, "bold"))
        style.map("App.Payment.Treeview",
                  background=[("selected", self.accent_color)],
                  foreground=[("selected", "white")])

    # بناء أزرار ترويسة (New, Save, Edit, Delete, Search, History, Print)
    def _build_header_buttons(self):
        header = ttk.Frame(self.main_card, style="App.Payment.Header.TFrame", height=68)
        header.pack(fill="x", side="top")
        ttk.Label(header, text=f"سند صرف - {SYSTEM_NAME}", style="App.Payment.Header.TLabel")\
            .pack(side="right", padx=30, pady=15)

        btn_group = ttk.Frame(header, style="App.Payment.Header.TFrame")
        btn_group.pack(side="left", padx=20)

        btn_data = [
            ("جديد", "App.Payment.Primary.TButton", self._reset_and_new),
            ("حفظ", "App.Payment.Success.TButton", lambda: self.save_voucher(is_update=False)),
            ("تعديل", "App.Payment.Warning.TButton", self._update_voucher),
            ("حذف", "App.Payment.Danger.TButton", self._delete_voucher),
            ("بحث", "App.Payment.Primary.TButton", self._search_voucher),
            ("السجلات", "App.Payment.History.TButton", self._show_history),
            ("طباعة", "App.Payment.Info.TButton", self._print_voucher),
        ]
        for txt, style_name, cmd in btn_data:
            ttk.Button(btn_group, text=txt, style=style_name, width=9, command=cmd)\
                .pack(side="left", padx=5)

    def _build_form_content(self):
        self.container = ttk.Frame(self.main_card, style="App.Payment.Content.TFrame", padding=(18,12))
        self.container.pack(fill="both", expand=True)
        self._build_header_section()
        self._build_beneficiary_section()
        self._build_line_editor()
        self._build_lines_table()
        self._build_totals_section()

    # حقل إدخال عام مُركب (Label + Entry/Combobox)
    def _create_compact_field(self, parent, label_text, widget_type="entry", label_width=14, text_height=2, **kwargs):
        container = ttk.Frame(parent, style="App.Payment.Content.TFrame")
        container.pack(side="right", fill="x", expand=True, padx=(8,0), pady=3)
        if widget_type == "entry":
            field = ttk.Entry(container, style="App.Payment.Field.TEntry", justify="right", **kwargs)
        elif widget_type == "combo":
            field = ttk.Combobox(container, style="App.Payment.Field.TCombobox", justify="right", **kwargs)
        else:
            field = tk.Text(container, font=("Segoe UI", 11, "bold"),
                            bd=1, relief="solid", height=text_height)
        field.pack(side="left", fill="x", expand=True, padx=(0,8))
        ttk.Label(container, text=label_text, style="App.Payment.FieldLabel.TLabel",
                  width=label_width).pack(side="right")
        return field

    # قسم بيانات السند
    def _build_header_section(self):
        header_box = ttk.Labelframe(self.container, text=" بيانات السند ", style="App.Payment.Content.TFrame", padding=6)
        header_box.pack(fill="x", pady=(0,6))
        row1 = ttk.Frame(header_box, style="App.Payment.Content.TFrame"); row1.pack(fill="x")
        self.ent_id = self._create_compact_field(row1, "رقم السند :", textvariable=self.voucher_id_var, state="readonly", label_width=13)
        self.ent_reference_no = self._create_compact_field(row1, "رقم المرجع :", textvariable=self.reference_no_var, state="readonly", label_width=13)
        self.ent_date = self._create_date_field(row1, "التاريخ :")
        self.ent_type = self._create_compact_field(row1, "نوع السند :", textvariable=self.voucher_type_var, state="readonly", label_width=13)
        row2 = ttk.Frame(header_box, style="App.Payment.Content.TFrame"); row2.pack(fill="x")
        self.combo_currency = self._create_compact_field(
            row2, "العملة :", widget_type="combo", state="readonly",
            textvariable=self.currency_var,
            values=("ريال يمني","ريال سعودي","دولار"),
            label_width=13
        )
        self.combo_cash_account = self._create_compact_field(
            row2, "حساب النقد / البنك :", widget_type="combo", state="normal",
            textvariable=self.cash_account_var, label_width=19
        )
        bind_searchable_combobox(self.combo_cash_account)

        desc_row = ttk.Frame(header_box, style="App.Payment.Content.TFrame"); desc_row.pack(fill="x")
        self.txt_desc = self._create_compact_field(desc_row, "الوصف العام :", widget_type="text", text_height=2, label_width=13)

    # حقل إدخال تاريخ
    def _create_date_field(self, parent, label_text):
        container = ttk.Frame(parent, style="App.Payment.Content.TFrame")
        container.pack(side="right", fill="x", expand=True, padx=(8,0), pady=3)
        date_class = getattr(ttk, "DateEntry", None)
        if date_class:
            field = date_class(container, bootstyle="primary", dateformat="%Y-%m-%d")
            field.entry.configure(justify="right", font=("Segoe UI", 11, "bold"))
        else:
            field = ttk.Entry(container, style="App.Payment.Field.TEntry", justify="right")
        field.pack(side="left", fill="x", expand=True, padx=(0,8))
        ttk.Label(container, text=label_text, style="App.Payment.FieldLabel.TLabel", width=13).pack(side="right")
        return field

    # قسم بيانات المستفيد
    def _build_beneficiary_section(self):
        box = ttk.Labelframe(self.container, text=" بيانات المستفيد ", style="App.Payment.Content.TFrame", padding=6)
        box.pack(fill="x", pady=(0,6))
        row1 = ttk.Frame(box, style="App.Payment.Content.TFrame"); row1.pack(fill="x")
        self.combo_beneficiary = self._create_compact_field(
            row1, "اسم المستفيد :", widget_type="combo", state="normal",
            textvariable=self.beneficiary_var, label_width=14
        )
        bind_searchable_combobox(self.combo_beneficiary)
        self.combo_beneficiary.bind("<<ComboboxSelected>>", self._on_beneficiary_selected)
        row2 = ttk.Frame(box, style="App.Payment.Content.TFrame"); row2.pack(fill="x")
        self.ent_phone = self._create_compact_field(row2, "رقم الهاتف :", textvariable=self.phone_var, state="readonly", label_width=13)
        self.ent_related_property = self._create_compact_field(row2, "الأرض المرتبطة :", textvariable=self.related_property_var, state="readonly", label_width=15)

    # محرر إضافة/تعديل بند
    def _build_line_editor(self):
        editor = ttk.Labelframe(self.container, text=" إضافة / تعديل بند ", style="App.Payment.Content.TFrame", padding=6)
        editor.pack(fill="x", pady=(0,6))
        row1 = ttk.Frame(editor, style="App.Payment.Content.TFrame"); row1.pack(fill="x")
        self.combo_line_account = self._create_compact_field(
            row1, "الحساب التحليلي :", widget_type="combo", state="normal", label_width=16
        )
        bind_searchable_combobox(self.combo_line_account)
        self.combo_line_account.bind("<<ComboboxSelected>>", self._on_line_account_selected)
        self.combo_line_account.bind("<Return>", lambda _e: self.add_row())
        self.ent_line_account_code = self._create_compact_field(
            row1, "كود الحساب :", textvariable=self.line_account_code_var, state="readonly", label_width=13
        )
        self.ent_line_account_name = self._create_compact_field(
            row1, "اسم الحساب :", textvariable=self.line_account_name_var, state="readonly", label_width=13
        )
        row2 = ttk.Frame(editor, style="App.Payment.Content.TFrame"); row2.pack(fill="x")
        self.ent_line_amount = self._create_compact_field(row2, "المبلغ :", textvariable=self.line_amount_var, label_width=11)
        self.ent_line_amount.bind("<KeyRelease>", lambda _e: self._format_amount_during_typing(self.line_amount_var))
        self.ent_line_amount.bind("<Return>", lambda _e: self.add_row())
        self.ent_line_exchange_rate = self._create_compact_field(row2, "سعر الصرف :", textvariable=self.line_exchange_rate_var, label_width=13)
        self.ent_line_exchange_rate.bind("<KeyRelease>", lambda _e: self._format_amount_during_typing(self.line_exchange_rate_var))
        self.ent_line_exchange_rate.bind("<Return>", lambda _e: self.add_row())
        # تم حذف حقل الوصف من إدخال البنود
        row3 = ttk.Frame(editor, style="App.Payment.Content.TFrame"); row3.pack(fill="x", pady=(4,0))
        ttk.Button(row3, text="تثبيت البند", style="App.Payment.Success.TButton", width=14, command=self.add_row).pack(side="left")
        ttk.Label(row3, text="Double-click لتعديل السطر, Delete للحذف", background="white", foreground=self.sidebar_color, font=("Segoe UI", 10, "bold")).pack(side="right")

    # بناء جدول البنود (مستطيل رئيسي وذو ألوان متبادلة لكل سطر)
    def _build_lines_table(self):
        table_area = ttk.Frame(self.container, style="App.Payment.Content.TFrame")
        table_area.pack(fill="both", expand=True, pady=(2,0))
        table_wrap = ttk.Frame(table_area, style="App.Payment.Content.TFrame")
        table_wrap.pack(fill="both", expand=True)

        # ترتيب سابق (عرض RTL): يبدأ بصرياً من اليمين بكود الحساب وينتهي بالوصف
        cols = ("description", "voucher_type", "voucher_number", "exchange_rate", "amount", "account_name", "account_code")
        self.lines_tree = ttk.Treeview(table_wrap, columns=cols, show="headings",
                                       height=12, style="App.Payment.Treeview", selectmode="browse")
        self.lines_tree.heading("description", text="الوصف"); self.lines_tree.column("description", width=320, anchor="e")
        self.lines_tree.heading("voucher_type", text="نوع السند"); self.lines_tree.column("voucher_type", width=110, anchor="center", stretch=False)
        self.lines_tree.heading("voucher_number", text="رقم السند"); self.lines_tree.column("voucher_number", width=110, anchor="center", stretch=False)
        self.lines_tree.heading("exchange_rate", text="سعر الصرف"); self.lines_tree.column("exchange_rate", width=110, anchor="e", stretch=False)
        self.lines_tree.heading("amount", text="المبلغ"); self.lines_tree.column("amount", width=125, anchor="e", stretch=False)
        self.lines_tree.heading("account_name", text="اسم الحساب"); self.lines_tree.column("account_name", width=230, anchor="e")
        self.lines_tree.heading("account_code", text="كود الحساب"); self.lines_tree.column("account_code", width=120, anchor="center", stretch=False)

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.lines_tree.yview)
        self.lines_tree.configure(yscrollcommand=y_scroll.set)
        self.lines_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

        # تلوين الصفوف بالتناوب
        self.lines_tree.tag_configure("odd", background="#f8f9fa")
        self.lines_tree.tag_configure("even", background="#ffffff")

        self.lines_tree.bind("<<TreeviewSelect>>", self._on_line_selected)
        self.lines_tree.bind("<Double-1>", self._on_line_selected)
        self.lines_tree.bind("<Delete>", lambda e: self._delete_selected_line())

    # قسم عرض المجموع النهائي
    def _build_totals_section(self):
        self.total_box = ttk.Frame(self.container, style="App.Payment.Total.TFrame", padding=10)
        self.total_box.pack(fill="x", pady=(8,0))
        self.lbl_total = ttk.Label(self.total_box, text="إجمالي المبلغ: 0.00",
                                   style="App.Payment.TotalAmount.TLabel", anchor="center")
        self.lbl_total.pack()
        self.lbl_total_words = ttk.Label(self.total_box, text="",
                                         style="App.Payment.TotalWords.TLabel", anchor="center")
        self.lbl_total_words.pack(pady=2)

    # ================== الدوال المساعدة ==================

    def _table_has_column(self, cur, table, column):
        cur.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_schema='finance' AND table_name=%s AND column_name=%s",
            (table, column)
        )
        return cur.fetchone() is not None

    def _parse_amount(self, raw_value):
        value = (raw_value or "").replace(",", "").strip()
        if not value:
            return 0.0
        return float(value)

    def _fmt_amount(self, value):
        try:
            return f"{float(value):,.2f}"
        except:
            return "0.00"

    def _format_amount_during_typing(self, var_obj):
        raw = var_obj.get().strip()
        if not raw:
            return
        # تحويل الأرقام العربية إلى لاتينية
        trans = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        raw = raw.translate(trans)
        cleaned = "".join(ch for ch in raw if ch.isdigit() or ch in ".,")
        cleaned = cleaned.replace(",", "")
        if not cleaned:
            var_obj.set("")
            return
        if cleaned.count(".") > 1:
            first, rest = cleaned.split(".", 1)
            cleaned = first + "." + rest.replace(".", "")
        try:
            if "." in cleaned:
                int_part, dec_part = cleaned.split(".", 1)
                int_part = int_part or "0"
                dec_part = "".join(ch for ch in dec_part if ch.isdigit())[:2]
                formatted = f"{int(int_part):,}" + "." + dec_part
            else:
                formatted = f"{int(cleaned):,}"
            var_obj.set(formatted)
        except:
            pass

    def _set_date_value(self, value):
        if hasattr(self.ent_date, "entry"):
            self.ent_date.entry.delete(0, tk.END)
            self.ent_date.entry.insert(0, value)
        else:
            self.ent_date.delete(0, tk.END)
            self.ent_date.insert(0, value)

    def _get_date_value(self):
        if hasattr(self.ent_date, "entry"):
            return self.ent_date.entry.get().strip()
        return self.ent_date.get().strip()

    def _refresh_totals_label(self):
        total = sum(float(line.get("amount",0) or 0) for line in self.line_items)
        self.lbl_total.config(text=f"إجمالي المبلغ: {self._fmt_amount(total)}")
        self.lbl_total_words.config(text=f"فقط وقدره: {self._fmt_amount(total)} {self.currency_var.get()} لا غير")

    def calculate_totals(self):
        self._refresh_totals_label()

    def _sync_row_auto_values(self):
        voucher_no = self.voucher_id_var.get().strip()
        voucher_type = self.voucher_type_var.get().strip() or VOUCHER_TYPE_PAYMENT
        for line in self.line_items:
            line["voucher_number"] = voucher_no
            line["voucher_type"] = voucher_type
            line["description"] = self.txt_desc.get("1.0", tk.END).strip()

    def _next_reference_no(self, cur):
        cur.execute("SELECT COALESCE(MAX(reference_no::BIGINT), 10000) + 1 FROM finance.vouchers")
        row = cur.fetchone()
        return str(row[0]) if row and row[0] is not None else "10001"

    def _fetch_next_ids(self):
        conn = get_connection()
        if not conn:
            return "تلقائي", "10001"
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM finance.vouchers")
                    vid_row = cur.fetchone()
                    ref_no = self._next_reference_no(cur)
                    next_id = str(vid_row[0]) if vid_row and vid_row[0] is not None else "تلقائي"
                    return next_id, ref_no
        except Exception:
            return "تلقائي", "10001"
        finally:
            conn.close()

    def _reset_and_new(self):
        self.voucher_id_var.set("تلقائي")
        self.reference_no_var.set("10001")
        self.voucher_type_var.set(VOUCHER_TYPE_PAYMENT)
        self.currency_var.set("ريال يمني")

        self.cash_account_var.set("")
        self.beneficiary_var.set("")
        self.phone_var.set("")
        self.related_property_var.set("")

        self.txt_desc.delete("1.0", tk.END)
        self._set_date_value(datetime.now().strftime("%Y-%m-%d"))

        self.line_items.clear()
        self._reset_line_editor()
        self._refresh_lines_table()

        next_id, next_ref = self._fetch_next_ids()
        self.voucher_id_var.set(next_id)
        self.reference_no_var.set(next_ref)

    # ================== تحميل البيانات من قاعدة البيانات ==================

    def load_accounts(self):
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT account_code, account_name
                FROM finance.accounts
                WHERE account_level = 'تحليلي'
                  AND COALESCE(is_active, true) = true
                ORDER BY account_code
            """)
            rows = cur.fetchall() or []
            values = []
            self.account_display_to_code.clear()
            self.account_code_to_display.clear()
            self.account_code_to_name.clear()
            for code, name in rows:
                code_txt = str(code or "").strip()
                name_txt = str(name or "").strip()
                if not code_txt:
                    continue
                display = f"{code_txt} - {name_txt}"
                values.append(display)
                self.account_display_to_code[display] = code_txt
                self.account_code_to_display[code_txt] = display
                self.account_code_to_name[code_txt] = name_txt
            set_combobox_values(self.combo_line_account, values)
            set_combobox_values(self.combo_cash_account, values)
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل الحسابات"))
        finally:
            conn.close()

    def load_beneficiaries(self):
        conn = get_connection()
        if not conn:
            return
        try:
            cur = conn.cursor()
            # جلب العقارات
            cur.execute("SELECT id, property_name FROM finance.properties ORDER BY property_name")
            props = cur.fetchall() or []
            # إيجاد عمود الهاتف في جدول الموردين (إن وجد)
            phone_col = None
            for col in ("phone", "mobile", "phone_number", "vendor_phone"):
                if self._table_has_column(cur, "vendors", col):
                    phone_col = col
                    break
            phone_select = f"v.{phone_col}" if phone_col else "NULL"
            # جلب بيانات الموردين
            cur.execute(f"""
                SELECT v.id, v.vendor_name, {phone_select}, v.property_id, p.property_name
                FROM finance.vendors v
                LEFT JOIN finance.properties p ON p.id = v.property_id
                ORDER BY v.vendor_name
            """)
            vendors = cur.fetchall() or []
            # جلب مجموعات الموردين
            cur.execute("SELECT id, group_name FROM finance.vendor_groups ORDER BY group_name")
            groups = cur.fetchall() or []
            self.beneficiary_display_to_data.clear()
            values = []
            prop_map = {pid: (pname or "") for pid,pname in props}
            for vid, name, phone, prop_id, prop_name in vendors:
                if not name:
                    continue
                display = f"مورد: {name}"
                related = prop_name or (prop_map.get(prop_id, "") if prop_id else "")
                self.beneficiary_display_to_data[display] = {
                    "type": "vendor", "vendor_id": int(vid),
                    "property_id": int(prop_id) if prop_id is not None else None,
                    "phone": str(phone or ""), "related_property": related
                }
                values.append(display)
            for gid, gname in groups:
                if not gname: continue
                display = f"مجموعة موردين: {gname}"
                self.beneficiary_display_to_data[display] = {
                    "type": "group", "group_id": int(gid),
                    "vendor_id": None, "property_id": None, "phone": "", "related_property": ""
                }
                values.append(display)
            for pid, pname in props:
                if not pname: continue
                display = f"أرض: {pname}"
                self.beneficiary_display_to_data[display] = {
                    "type": "property", "vendor_id": None,
                    "property_id": int(pid), "phone": "", "related_property": pname
                }
                values.append(display)
            set_combobox_values(self.combo_beneficiary, values)
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل المستفيدين"))
        finally:
            conn.close()

    # ================== أحداث اختيار المستفيد ==================
    def _on_beneficiary_selected(self, *_):
        data = self.beneficiary_display_to_data.get(self.combo_beneficiary.get().strip(), {})
        self.phone_var.set(data.get("phone", ""))
        self.related_property_var.set(data.get("related_property", ""))

    # ================== أحداث اختيار الحساب في محرر البند ==================
    def _on_line_account_selected(self, *_):
        acc = self.combo_line_account.get().strip()
        code = self.account_display_to_code.get(acc, "")
        self.line_account_code_var.set(code)
        self.line_account_name_var.set(self.account_code_to_name.get(code, ""))

    # ================== إعادة تهيئة محرر البند ==================
    def _reset_line_editor(self):
        self.combo_line_account.set("")
        self.line_account_code_var.set("")
        self.line_account_name_var.set("")
        self.line_amount_var.set("0.00")
        self.line_exchange_rate_var.set("1.00")
        self.selected_line_index = None

    # ================== تكوين بيانات البند من محرر ==================
    def _line_from_editor(self):
        acc_disp = self.combo_line_account.get().strip()
        code = self.account_display_to_code.get(acc_disp)
        if not code:
            messagebox.showwarning("تنبيه", "اختر حسابا تحليليا صحيحا للبند")
            return None
        try:
            amt = self._parse_amount(self.line_amount_var.get())
        except:
            messagebox.showwarning("تنبيه", "المبلغ غير صحيح")
            return None
        try:
            rate = self._parse_amount(self.line_exchange_rate_var.get())
        except:
            messagebox.showwarning("تنبيه", "سعر الصرف غير صحيح")
            return None
        # الوصف لكل بند يأتي من الوصف العام
        desc = self.txt_desc.get("1.0", tk.END).strip()
        if amt <= 0:
            messagebox.showwarning("تنبيه", "المبلغ يجب أن يكون أكبر من صفر")
            return None
        if rate <= 0:
            messagebox.showwarning("تنبيه", "سعر الصرف يجب أن يكون أكبر من صفر")
            return None
        return {
            "account_code": code,
            "account_name": self.account_code_to_name.get(code, ""),
            "amount": amt,
            "exchange_rate": rate,
            "voucher_number": self.voucher_id_var.get().strip(),
            "voucher_type": self.voucher_type_var.get().strip(),
            "description": desc
        }

    # ================== إضافة بند ==================
    def add_row(self):
        line = self._line_from_editor()
        if not line:
            return
        if self.selected_line_index is None:
            self.line_items.append(line)
        else:
            self.line_items[self.selected_line_index] = line
        self._reset_line_editor()
        self._refresh_lines_table()

    # ================== اختيار بند من الجدول (Double-click) ==================
    def _on_line_selected(self, event=None):
        sel = self.lines_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(self.line_items):
            return
        self.selected_line_index = idx
        line = self.line_items[idx]
        disp = self.account_code_to_display.get(line.get("account_code"), "")
        self.combo_line_account.set(disp)
        self.line_account_code_var.set(line.get("account_code", ""))
        self.line_account_name_var.set(line.get("account_name", ""))
        self.line_amount_var.set(self._fmt_amount(line.get("amount", 0)))
        self.line_exchange_rate_var.set(self._fmt_amount(line.get("exchange_rate", 1)))

    # ================== حذف بند محدد ==================
    def _delete_selected_line(self):
        sel = self.lines_tree.selection()
        if not sel and self.selected_line_index is None:
            messagebox.showwarning("تنبيه", "اختر بندا من الجدول أولاً")
            return
        idx = self.selected_line_index if self.selected_line_index is not None else int(sel[0])
        if idx < 0 or idx >= len(self.line_items):
            return
        del self.line_items[idx]
        self._reset_line_editor()
        self._refresh_lines_table()

    # ================== تحديث عرض الجدول ==================
    def _refresh_lines_table(self):
        self.lines_tree.delete(*self.lines_tree.get_children())
        for idx, line in enumerate(self.line_items, start=1):
            tag = "even" if idx % 2 == 0 else "odd"
            self.lines_tree.insert(
                "",
                tk.END,
                iid=str(idx-1),
                values=(
                    line.get("description", ""),
                    line.get("voucher_type", ""),
                    line.get("voucher_number", ""),
                    self._fmt_amount(line.get("exchange_rate", 1)),
                    self._fmt_amount(line.get("amount", 0)),
                    line.get("account_name", ""),
                    line.get("account_code", ""),
                ),
                tags=(tag,)
            )
        self._refresh_totals_label()

    # ================== استعراض سجلات السندات (History) ==================
    def _show_history(self):
        history_win = tk.Toplevel(self.master)
        history_win.title("قائمة سندات الصرف")
        history_win.geometry("620x420")
        tree = ttk.Treeview(history_win, columns=("id","ref","date","desc"), show="headings")
        tree.heading("id", text="رقم السند"); tree.column("id", width=90, anchor="center")
        tree.heading("ref", text="رقم المرجع"); tree.column("ref", width=100, anchor="center")
        tree.heading("date", text="التاريخ"); tree.column("date", width=120, anchor="center")
        tree.heading("desc", text="الوصف"); tree.column("desc", width=280, anchor="e")
        tree.pack(fill="both", expand=True)
        conn = None
        try:
            conn = get_connection()
            if not conn:
                return
            cur = conn.cursor()
            cur.execute(
                "SELECT id, COALESCE(reference_no, ''), v_date, description FROM finance.vouchers WHERE v_type=%s ORDER BY v_date DESC, id DESC",
                (VOUCHER_TYPE_PAYMENT,)
            )
            for vid, ref_no, vdate, vdesc in cur.fetchall():
                tree.insert("", tk.END, values=(vid, ref_no, str(vdate), vdesc))
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل السجلات"))
        finally:
            if conn:
                conn.close()
        # عند النقر المزدوج، تحميل السند المحدد
        def load_from_history(event):
            sel = tree.selection()
            if not sel:
                return
            vid = tree.item(sel[0])["values"][0]
            history_win.destroy()
            self._load_voucher_by_id(vid)
        tree.bind("<Double-1>", load_from_history)

    # ================== البحث عن سند ==================
    def _search_voucher(self):
        vid = simpledialog.askinteger("بحث", "أدخل رقم السند:")
        if vid:
            self._load_voucher_by_id(vid)

    # ================== التحقق قبل الحفظ ==================
    def _validate_before_save(self):
        ben_disp = self.combo_beneficiary.get().strip()
        ben = self.beneficiary_display_to_data.get(ben_disp)
        if not ben:
            messagebox.showwarning("تنبيه", "يرجى اختيار اسم المستفيد")
            return None
        cash_disp = self.combo_cash_account.get().strip()
        cash_code = self.account_display_to_code.get(cash_disp)
        if not cash_code:
            messagebox.showwarning("تنبيه", "يرجى اختيار حساب النقد / البنك")
            return None
        if cash_code not in self.account_code_to_name:
            messagebox.showwarning("تنبيه", "حساب النقد / البنك يجب أن يكون تحليلي")
            return None
        if not self.line_items:
            messagebox.showwarning("تنبيه", "يرجى إضافة بنود إلى السند")
            return None
        for line in self.line_items:
            if line.get("account_code") not in self.account_code_to_name:
                messagebox.showwarning("تنبيه", "كل بنود السند يجب أن تكون بحسابات تحليلية")
                return None
            if float(line.get("amount",0) or 0) <= 0:
                messagebox.showwarning("تنبيه", "يجب أن تكون كل مبالغ البنود أكبر من صفر")
                return None
        total = sum(float(line.get("amount",0) or 0) for line in self.line_items)
        if total <= 0:
            messagebox.showwarning("تنبيه", "يجب أن يكون إجمالي السند أكبر من صفر")
            return None
        return {"beneficiary": ben, "cash_account_code": cash_code, "total_amount": total}

    # ================== حفظ السند ==================
    def save_voucher(self, is_update=False):
        valid = self._validate_before_save()
        if not valid:
            return
        vid_text = self.voucher_id_var.get().strip()
        ref_no = self.reference_no_var.get().strip()
        desc = self.txt_desc.get("1.0", tk.END).strip()
        date = self._get_date_value() or datetime.now().strftime("%Y-%m-%d")
        conn = None
        try:
            conn = get_connection()
            if not conn:
                return
            cur = conn.cursor()
            if is_update:
                if not vid_text.isdigit():
                    messagebox.showwarning("تنبيه", "رقم السند غير صالح للتعديل")
                    return
                vid = int(vid_text)
                cur.execute(
                    "UPDATE finance.vouchers SET reference_no=%s, v_type=%s, v_date=%s, description=%s WHERE id=%s",
                    (ref_no, VOUCHER_TYPE_PAYMENT, date, desc, vid),
                )
                cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (vid,))
            else:
                cur.execute(
                    "INSERT INTO finance.vouchers (reference_no, v_type, v_date, description) VALUES (%s, %s, %s, %s) RETURNING id",
                    (ref_no, VOUCHER_TYPE_PAYMENT, date, desc),
                )
                vid = cur.fetchone()[0]
                self.voucher_id_var.set(str(vid))
            ben = valid["beneficiary"]
            vendor_id = ben.get("vendor_id")
            property_id = ben.get("property_id")
            cash_code = valid["cash_account_code"]
            total_amt = valid["total_amount"]
            cur.execute(
                "INSERT INTO finance.ledger (voucher_id, account_code, vendor_id, property_id, debit, credit, line_description, posting_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (vid, cash_code, None, None, 0, total_amt, desc or "سند صرف", date))
            for line in self.line_items:
                cur.execute(
                    "INSERT INTO finance.ledger (voucher_id, account_code, vendor_id, property_id, debit, credit, line_description, posting_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (vid, line["account_code"], vendor_id, property_id, line["amount"], 0, line.get("description", ""), date))
            conn.commit()
            self.reference_no_var.set(ref_no)
            self._sync_row_auto_values()
            self._refresh_lines_table()
            messagebox.showinfo("نجاح", "تم حفظ سند الصرف بنجاح")
        except Exception as exc:
            if conn:
                conn.rollback()
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ السند"))
        finally:
            if conn:
                conn.close()

    # ================== تحميل سند برقم محدد ==================
    def _load_voucher_by_id(self, voucher_id):
        conn = get_connection()
        if not conn:
            messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
            return False
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, COALESCE(reference_no, ''), v_date, description FROM finance.vouchers WHERE id=%s AND v_type=%s",
                (voucher_id, VOUCHER_TYPE_PAYMENT),
            )
            row = cur.fetchone()
            if not row:
                messagebox.showinfo("نتيجة البحث", "لم يتم العثور على سند صرف بهذا الرقم")
                return False
            self.voucher_id_var.set(str(row[0]))
            self.reference_no_var.set(str(row[1] or ""))
            self._set_date_value(str(row[2]))
            self.txt_desc.delete("1.0", tk.END)
            self.txt_desc.insert("1.0", row[3] or "")
            cur.execute("SELECT account_code, debit, credit, line_description, vendor_id, property_id FROM finance.ledger WHERE voucher_id=%s ORDER BY id", (voucher_id,))
            ledger_rows = cur.fetchall()
            self.line_items.clear()
            beneficiary_set = False
            cash_set = False
            for acc_code, debit, credit, line_desc, vend_id, prop_id in ledger_rows:
                acc_code = str(acc_code or "")
                debit = float(debit or 0)
                credit = float(credit or 0)
                # سطر البنك/النقد (credit)
                if credit > 0 and debit == 0 and not cash_set:
                    disp = self.account_code_to_display.get(acc_code, "")
                    if disp:
                        self.combo_cash_account.set(disp)
                    cash_set = True
                    continue
                amt = debit if debit > 0 else credit
                if amt <= 0:
                    continue
                self.line_items.append({
                    "account_code": acc_code,
                    "account_name": self.account_code_to_name.get(acc_code, ""),
                    "amount": amt,
                    "exchange_rate": 1.0,
                    "voucher_number": str(voucher_id),
                    "voucher_type": VOUCHER_TYPE_PAYMENT,
                    "description": line_desc or ""
                })
                # تحديد بيانات المستفيد لأول مرة
                if not beneficiary_set and (vend_id or prop_id):
                    disp = self._resolve_beneficiary_display(vend_id, prop_id)
                    if disp:
                        self.combo_beneficiary.set(disp)
                        self._on_beneficiary_selected()
                        beneficiary_set = True
            self._reset_line_editor()
            self._refresh_lines_table()
            return True
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل السند"))
            return False
        finally:
            conn.close()

    # إيجاد عرض المستفيد بناء على المعرفات
    def _resolve_beneficiary_display(self, vendor_id, property_id):
        for disp, data in self.beneficiary_display_to_data.items():
            if vendor_id is not None and data.get("type") == "vendor" and int(data.get("vendor_id", 0) or 0) == int(vendor_id):
                return disp
            prop = data.get("property_id")
            if prop is not None and int(prop) == int(property_id):
                return disp
        return ""

    # طلب رقم سند من المستخدم
    def _request_voucher_id(self, title):
        ask = simpledialog.askstring(title, "أدخل رقم السند:", parent=self.master)
        if ask and ask.isdigit():
            return int(ask)
        return None

    def _update_voucher(self):
        current = self.voucher_id_var.get().strip()
        if current.isdigit():
            self.save_voucher(is_update=True)
            return
        vid = self._request_voucher_id("تعديل سند")
        if vid is None:
            return
        if self._load_voucher_by_id(vid):
            self.save_voucher(is_update=True)

    def _delete_voucher(self):
        current = self.voucher_id_var.get().strip()
        voucher_id = int(current) if current.isdigit() else self._request_voucher_id("حذف سند")
        if voucher_id is None:
            return
        if not messagebox.askyesno("تأكيد", "هل تريد حذف السند المحدد؟"):
            return
        conn = get_connection()
        if not conn:
            messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
            return
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (voucher_id,))
            cur.execute("DELETE FROM finance.vouchers WHERE id=%s AND v_type=%s", (voucher_id, VOUCHER_TYPE_PAYMENT))
            conn.commit()
            messagebox.showinfo("نجاح", "تم حذف سند الصرف")
            self._reset_and_new()
        except Exception as exc:
            conn.rollback()
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حذف سند"))
        finally:
            conn.close()

    def _print_voucher(self):
        voucher_id = self.voucher_id_var.get().strip()
        if not voucher_id.isdigit():
            messagebox.showwarning("تنبيه", "احفظ السند أولاً قبل الطباعة")
            return
        messagebox.showinfo("طباعة", f"تم تجهيز سند الصرف رقم {voucher_id} للطباعة")
