import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from db_connection import get_connection


class PaymentVoucherScreen:
    def __init__(self, master):
        self.master = master
        # الهوية البصرية الخاصة بك
        self.sidebar_color = "#34495e"
        self.text_color = "#ecf0f1"

        # --- الإضافة 1: تعريف حساب الصندوق الافتراضي ---
        self.DEFAULT_CASH_ACC = "1101 - الصندوق الرئيسي"

        self.frame = tk.Frame(master, bg="#f0f2f5")
        self.frame.pack(fill=tk.BOTH, expand=True)

        # متغيرات الربط
        self.voucher_id_var = tk.StringVar(value="تلقائي")
        self.amount_var = tk.StringVar(value="0.00")
        self.amount_var.trace_add("write", self._update_total_display)

        # الكارد الرئيسي الممتد (1100x800) كما في تصميمك
        self.main_card = tk.Frame(self.frame, bg="white", highlightthickness=1, highlightbackground="#d1d8e0")
        self.main_card.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=1100, height=800)

        self._build_header_buttons()
        self._build_form_content()
        self._load_initial_data()

        # تفعيل حالة Read-Only عند التشغيل
        self._set_fields_state('disabled')

    def _build_header_buttons(self):
        """شريط العمليات العلوي للسند"""
        header = tk.Frame(self.main_card, bg="#2c3e50", height=65)
        header.pack(fill="x", side="top")

        tk.Label(header, text="سند صرف نقدي - Al-Sofi ERP", fg="white",
                 bg="#2c3e50", font=("Arial", 18, "bold")).pack(side="right", padx=30, pady=15)

        btn_group = tk.Frame(header, bg="#2c3e50")
        btn_group.pack(side="left", padx=20)

        btn_data = [
            ("خروج", "#e74c3c", self.master.quit),
            ("حذف", "#e67e22", self._delete_voucher),
            ("تعديل", "#f1c40f", self._update_voucher),
            ("حفظ", "#2ecc71", self._save_voucher),
            ("بحث", "#9b59b6", self._search_voucher),
            ("جديد ✨", "#3498db", self._reset_and_new)
        ]

        for txt, clr, cmd in btn_data:
            tk.Button(btn_group, text=txt, bg=clr, fg="white", font=("Arial", 10, "bold"),
                      width=9, bd=0, cursor="hand2", pady=7, command=cmd).pack(side="left", padx=5)

    def _create_full_width_field(self, parent, label_text, widget_type="entry", **kwargs):
        container = tk.Frame(parent, bg="white")
        container.pack(fill="x", pady=12)

        if widget_type == "entry":
            field = tk.Entry(container, font=("Arial", 15, "bold"), bd=2, relief="groove", justify="right", **kwargs)
        elif widget_type == "combo":
            field = ttk.Combobox(container, font=("Arial", 15, "bold"), justify="right", **kwargs)
        elif widget_type == "text":
            field = tk.Text(container, font=("Arial", 14, "bold"), bd=2, relief="groove", height=4, **kwargs)

        field.pack(side="left", fill="x", expand=True, padx=(0, 15))

        lbl = tk.Label(container, text=label_text, bg=self.sidebar_color, fg=self.text_color,
                       font=("Arial", 12, "bold"), width=22, anchor="center", pady=8)
        lbl.pack(side="right")
        return field

    def _build_form_content(self):
        self.container = tk.Frame(self.main_card, bg="white")
        self.container.pack(fill="both", expand=True, padx=45, pady=30)

        top_row = tk.Frame(self.container, bg="white")
        top_row.pack(fill="x", pady=5)

        # التاريخ
        date_frame = tk.Frame(top_row, bg="white")
        date_frame.pack(side="left", fill="x", expand=True)
        self.ent_date = self._create_full_width_field(date_frame, "تاريخ الصرف :")

        # رقم السند
        id_frame = tk.Frame(top_row, bg="white")
        id_frame.pack(side="right", fill="x", expand=True, padx=(20, 0))
        self.ent_id = self._create_full_width_field(id_frame, "رقم السند :", textvariable=self.voucher_id_var,
                                                    state="readonly")
        self.ent_id.config(readonlybackground="#ecf0f1", fg="#c0392b")

        # --- الإضافة 2: فصل المشروع عن العقار ---
        self.combo_project = self._create_full_width_field(self.container, "المشروع التابع :", widget_type="combo")
        self.combo_project.bind("<<ComboboxSelected>>", self._filter_properties)

        self.combo_prop = self._create_full_width_field(self.container, "العقار / الوحدة :", widget_type="combo")

        self.combo_acc = self._create_full_width_field(self.container, "الحساب المحاسبي المدين :", widget_type="combo")

        # المبلغ
        self.ent_amount = self._create_full_width_field(self.container, "المبلغ المستحق صرفه :",
                                                        textvariable=self.amount_var)
        self.ent_amount.config(bg="#fffde7", fg="#c0392b", font=("Arial", 24, "bold"))

        self.txt_desc = self._create_full_width_field(self.container, "شرح البيان العام :", widget_type="text")

        # منطقة الإجمالي السفلية
        self.total_box = tk.Frame(self.container, bg="#f8f9fa", pady=20, bd=1, relief="solid")
        self.total_box.pack(fill="x", pady=(30, 0))
        self.lbl_total_num = tk.Label(self.total_box, text="الإجمالي: 0.00 ر.ي", font=("Arial", 30, "bold"),
                                      bg="#f8f9fa", fg="#c0392b")
        self.lbl_total_num.pack()
        self.lbl_total_word = tk.Label(self.total_box, text="فقط وقدره: لا شيء ريال يمني لا غير",
                                       font=("Arial", 14, "bold"), bg="#f8f9fa", fg=self.sidebar_color)
        self.lbl_total_word.pack(pady=5)

    # --- الإضافة 3: تصفية العقارات حسب المشروع المختار ---
    def _filter_properties(self, event=None):
        project_selection = self.combo_project.get()
        if not project_selection: return
        project_id = project_selection.split(' - ')[0]
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT id, property_name FROM finance.properties WHERE project_id = %s", (project_id,))
            self.combo_prop['values'] = [f"{r[0]} - {r[1]}" for r in cur.fetchall()]
            self.combo_prop.set('')  # مسح الاختيار السابق عند تغيير المشروع
            conn.close()

    def _set_fields_state(self, state):
        widgets = [self.ent_date, self.combo_project, self.combo_prop, self.combo_acc, self.ent_amount]
        for w in widgets:
            w.config(state=state)
        self.txt_desc.config(state='normal' if state == 'normal' else 'disabled',
                             bg="white" if state == 'normal' else "#f5f6f7")

    def _reset_and_new(self):
        """تصفير الحقول ووضع الصندوق الافتراضي"""
        self._set_fields_state('normal')
        self.amount_var.set("0.00")
        self.txt_desc.delete("1.0", tk.END)
        self.ent_date.delete(0, tk.END)
        self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # --- الإضافة 4: وضع كود الصندوق الافتراضي في الحساب المحاسبي ---
        self.combo_acc.set(self.DEFAULT_CASH_ACC)

        conn = get_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM finance.vouchers")
                next_id = cur.fetchone()[0]
                self.voucher_id_var.set(str(next_id))
            finally:
                conn.close()

    def _save_voucher(self):
        if self.ent_amount['state'] == 'disabled':
            messagebox.showwarning("تنبيه", "يجب الضغط على زر 'جديد' أولاً")
            return
        self._execute_db_action("INSERT")

    def _execute_db_action(self, mode, v_id=None):
        conn = get_connection()
        try:
            cur = conn.cursor()
            # التأكد من اختيار العقار
            if not self.combo_prop.get():
                messagebox.showwarning("تنبيه", "يرجى اختيار العقار أولاً")
                return

            p_id = int(self.combo_prop.get().split(' - ')[0])
            a_code = self.combo_acc.get().split(' - ')[0]
            amt = float(self.amount_var.get())
            desc = self.txt_desc.get("1.0", tk.END).strip()

            cur.execute(
                "INSERT INTO finance.vouchers (v_type, v_date, description) VALUES ('صرف', %s, %s) RETURNING id",
                (self.ent_date.get(), desc))
            new_id = cur.fetchone()[0]

            cur.execute(
                "INSERT INTO finance.ledger (voucher_id, account_code, property_id, debit) VALUES (%s,%s,%s,%s)",
                (new_id, a_code, p_id, amt))

            conn.commit()
            messagebox.showinfo("نجاح", f"تم حفظ السند بنجاح")
            self._set_fields_state('disabled')
        except Exception as e:
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _load_initial_data(self):
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            # جلب المشاريع أولاً
            cur.execute("SELECT id, project_name FROM finance.projects")
            self.combo_project['values'] = [f"{r[0]} - {r[1]}" for r in cur.fetchall()]

            # جلب الحسابات
            cur.execute("SELECT account_code, account_name FROM finance.accounts WHERE account_type='تحليلي'")
            self.combo_acc['values'] = [f"{r[0]} - {r[1]}" for r in cur.fetchall()]
            conn.close()

    def _update_total_display(self, *args):
        try:
            val = self.amount_var.get()
            amount = float(val) if val and val != "." else 0.0
            self.lbl_total_num.config(text=f"الإجمالي: {amount:,.2f} ر.ي")
            self.lbl_total_word.config(text=f"فقط وقدره: {amount:,.2f} ريال يمني لا غير")
        except:
            pass

    def _search_voucher(self):
        self._set_fields_state('normal')

    def _update_voucher(self):
        self._set_fields_state('normal')

    def _delete_voucher(self):
        pass