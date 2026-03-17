import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
import ttkbootstrap as ttk
from db_connection import get_connection


class PaymentVoucherScreen:
    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.separator_color = "#2c3e50"
        self.bg_color = "#f4f7f6"

        self.DEFAULT_CASH_ACC = "1101 - الصندوق الرئيسي"

        self._setup_styles()

        self.frame = ttk.Frame(master, style="App.Payment.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.voucher_id_var = tk.StringVar(value="تلقائي")
        self.amount_var = tk.StringVar(value="0.00")
        self.amount_var.trace_add("write", self._update_total_display)

        self.main_card = ttk.Frame(self.frame, style="App.Payment.Card.TFrame")
        self.main_card.pack(fill="both", expand=True, padx=14, pady=14)

        self._build_header_buttons()
        self._build_form_content()
        self._load_initial_data()
        self._set_fields_state('disabled')

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("App.Payment.Root.TFrame", background=self.bg_color)
        style.configure("App.Payment.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("App.Payment.Header.TFrame", background=self.primary_color)
        style.configure("App.Payment.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 20, "bold"))
        style.configure("App.Payment.Content.TFrame", background="white")
        style.configure("App.Payment.FieldLabel.TLabel", background=self.sidebar_color, foreground=self.text_color, font=("Segoe UI", 13, "bold"), anchor="center", padding=9)
        style.configure("App.Payment.Field.TEntry", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 15, "bold"))
        style.configure("App.Payment.Field.TCombobox", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 14, "bold"))
        style.configure("App.Payment.Total.TFrame", background="#f8f9fa", bordercolor="#d8e1e8", borderwidth=1, relief="solid")
        style.configure("App.Payment.TotalAmount.TLabel", background="#f8f9fa", foreground="#c0392b", font=("Segoe UI", 30, "bold"))
        style.configure("App.Payment.TotalWords.TLabel", background="#f8f9fa", foreground=self.sidebar_color, font=("Segoe UI", 14, "bold"))

        # Distinct action colors to match the original ERP toolbar look.
        style.configure("App.Payment.Primary.TButton", background="#2980b9", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Payment.Success.TButton", background="#27ae60", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Payment.Warning.TButton", background="#f1c40f", foreground="#2c3e50", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Payment.Danger.TButton", background="#e74c3c", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Payment.Info.TButton", background="#8e44ad", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Payment.Exit.TButton", background="#e67e22", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))

        for btn_style in (
            "App.Payment.Primary.TButton",
            "App.Payment.Success.TButton",
            "App.Payment.Warning.TButton",
            "App.Payment.Danger.TButton",
            "App.Payment.Info.TButton",
            "App.Payment.Exit.TButton",
        ):
            style.map(
                btn_style,
                background=[("active", self.accent_color), ("pressed", self.accent_color)],
                foreground=[("active", "white"), ("pressed", "white")],
            )

    def _build_header_buttons(self):
        header = ttk.Frame(self.main_card, style="App.Payment.Header.TFrame", height=68)
        header.pack(fill="x", side="top")

        ttk.Label(header, text="سند صرف نقدي - Al-Sofi ERP", style="App.Payment.Header.TLabel").pack(side="right", padx=30, pady=15)

        btn_group = ttk.Frame(header, style="App.Payment.Header.TFrame")
        btn_group.pack(side="left", padx=20)

        btn_data = [
            ("جديد", "App.Payment.Primary.TButton", self._reset_and_new),
            ("حفظ", "App.Payment.Success.TButton", self._save_voucher),
            ("تعديل", "App.Payment.Warning.TButton", self._update_voucher),
            ("حذف", "App.Payment.Danger.TButton", self._delete_voucher),
            ("بحث", "App.Payment.Info.TButton", self._search_voucher),
            ("خروج", "App.Payment.Exit.TButton", self.master.quit),
        ]

        for txt, style_name, cmd in btn_data:
            ttk.Button(btn_group, text=txt, style=style_name, width=9, command=cmd).pack(side="left", padx=5)

    def _create_full_width_field(self, parent, label_text, widget_type="entry", **kwargs):
        container = ttk.Frame(parent, style="App.Payment.Content.TFrame")
        container.pack(fill="x", pady=10)

        field = None
        if widget_type == "entry":
            field = ttk.Entry(container, style="App.Payment.Field.TEntry", justify="right", **kwargs)
        elif widget_type == "combo":
            field = ttk.Combobox(container, style="App.Payment.Field.TCombobox", justify="right", **kwargs)
        elif widget_type == "text":
            field = tk.Text(container, font=("Segoe UI", 13, "bold"), bd=1, relief="solid", height=4, **kwargs)

        if field is None:
            raise ValueError(f"Unsupported widget_type: {widget_type}")

        field.pack(side="left", fill="x", expand=True, padx=(0, 15))

        lbl = ttk.Label(container, text=label_text, style="App.Payment.FieldLabel.TLabel", width=22)
        lbl.pack(side="right")
        return field

    def _build_form_content(self):
        self.container = ttk.Frame(self.main_card, style="App.Payment.Content.TFrame", padding=(40, 26))
        self.container.pack(fill="both", expand=True)

        top_row = ttk.Frame(self.container, style="App.Payment.Content.TFrame")
        top_row.pack(fill="x", pady=5)

        date_frame = ttk.Frame(top_row, style="App.Payment.Content.TFrame")
        date_frame.pack(side="left", fill="x", expand=True)
        self.ent_date = self._create_full_width_field(date_frame, "تاريخ الصرف :")

        id_frame = ttk.Frame(top_row, style="App.Payment.Content.TFrame")
        id_frame.pack(side="right", fill="x", expand=True, padx=(20, 0))
        self.ent_id = self._create_full_width_field(id_frame, "رقم السند :", textvariable=self.voucher_id_var, state="readonly")

        self.combo_project = self._create_full_width_field(self.container, "المشروع التابع :", widget_type="combo", state="readonly")
        self.combo_project.bind("<<ComboboxSelected>>", self._filter_properties)

        self.combo_prop = self._create_full_width_field(self.container, "العقار / الوحدة :", widget_type="combo", state="readonly")
        self.combo_acc = self._create_full_width_field(self.container, "الحساب المحاسبي المدين :", widget_type="combo", state="readonly")

        self.ent_amount = self._create_full_width_field(self.container, "المبلغ المستحق صرفه :", textvariable=self.amount_var)
        self.ent_amount.configure(font=("Segoe UI", 22, "bold"), foreground="#c0392b")

        self.txt_desc = self._create_full_width_field(self.container, "شرح البيان العام :", widget_type="text")

        self.total_box = ttk.Frame(self.container, style="App.Payment.Total.TFrame", padding=16)
        self.total_box.pack(fill="x", pady=(24, 0))
        self.lbl_total_num = ttk.Label(self.total_box, text="الإجمالي: 0.00 ر.ي", style="App.Payment.TotalAmount.TLabel", anchor="center")
        self.lbl_total_num.pack()
        self.lbl_total_word = ttk.Label(self.total_box, text="فقط وقدره: لا شيء ريال يمني لا غير", style="App.Payment.TotalWords.TLabel", anchor="center")
        self.lbl_total_word.pack(pady=5)

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
        self.txt_desc.config(state='normal' if state == 'normal' else 'disabled', bg="white" if state == 'normal' else "#f5f6f7")

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
        voucher_id = simpledialog.askstring("بحث", "أدخل رقم سند الصرف:", parent=self.master)
        if not voucher_id:
            return

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT v.id,
                       v.v_date,
                       v.description,
                       l.property_id,
                       COALESCE(p.project_id, 0) AS project_id,
                       l.account_code,
                       COALESCE(l.debit, 0) AS amount
                FROM finance.vouchers v
                JOIN finance.ledger l ON l.voucher_id = v.id
                LEFT JOIN finance.properties p ON p.id = l.property_id
                WHERE v.id = %s
                  AND v.v_type = 'صرف'
                ORDER BY l.id
                LIMIT 1
                """,
                (voucher_id,),
            )
            row = cur.fetchone()
            if not row:
                return messagebox.showinfo("بحث", "لم يتم العثور على السند")

            self._set_fields_state('normal')
            self.voucher_id_var.set(str(row[0]))
            self.ent_date.delete(0, tk.END)
            self.ent_date.insert(0, str(row[1]))
            self.txt_desc.delete("1.0", tk.END)
            self.txt_desc.insert("1.0", row[2] or "")
            self.amount_var.set(str(row[6]))

            if row[4]:
                project_match = [v for v in self.combo_project['values'] if v.startswith(f"{row[4]} -")]
                if project_match:
                    self.combo_project.set(project_match[0])
                    self._filter_properties()

            if row[3]:
                prop_match = [v for v in self.combo_prop['values'] if v.startswith(f"{row[3]} -")]
                if prop_match:
                    self.combo_prop.set(prop_match[0])

            if row[5]:
                acc_match = [v for v in self.combo_acc['values'] if v.startswith(f"{row[5]} -")]
                if acc_match:
                    self.combo_acc.set(acc_match[0])
        except Exception as e:
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _update_voucher(self):
        voucher_id = self.voucher_id_var.get().strip()
        if not voucher_id.isdigit():
            return messagebox.showwarning("تنبيه", "ابحث عن سند صحيح قبل التعديل")

        conn = get_connection()
        try:
            cur = conn.cursor()
            p_id = int(self.combo_prop.get().split(' - ')[0])
            a_code = self.combo_acc.get().split(' - ')[0]
            amt = float(self.amount_var.get())
            desc = self.txt_desc.get("1.0", tk.END).strip()

            cur.execute("UPDATE finance.vouchers SET v_date=%s, description=%s WHERE id=%s AND v_type='صرف'", (self.ent_date.get(), desc, voucher_id))
            cur.execute(
                """
                UPDATE finance.ledger
                SET account_code=%s, property_id=%s, debit=%s, credit=NULL
                WHERE voucher_id=%s AND vendor_id IS NULL
                """,
                (a_code, p_id, amt, voucher_id),
            )
            conn.commit()
            messagebox.showinfo("نجاح", "تم تعديل سند الصرف")
            self._set_fields_state('disabled')
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))

        finally:
            conn.close()

    def _delete_voucher(self):
        voucher_id = self.voucher_id_var.get().strip()
        if not voucher_id.isdigit():
            return messagebox.showwarning("تنبيه", "ابحث عن سند صحيح قبل الحذف")

        if not messagebox.askyesno("تأكيد", "هل تريد حذف السند المحدد؟"):
            return

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (voucher_id,))
            cur.execute("DELETE FROM finance.vouchers WHERE id=%s AND v_type='صرف'", (voucher_id,))
            conn.commit()
            messagebox.showinfo("نجاح", "تم حذف سند الصرف")
            self.voucher_id_var.set("تلقائي")
            self._set_fields_state('disabled')
            self._reset_and_new()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()
