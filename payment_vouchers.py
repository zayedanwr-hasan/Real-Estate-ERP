import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime

import ttkbootstrap as ttk

from app_constants import SYSTEM_NAME, VOUCHER_TYPE_PAYMENT
from combobox_helper import bind_searchable_combobox, set_combobox_values
from db_connection import get_connection, get_db_error_message


class PaymentVoucherScreen:
    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.bg_color = "#f4f7f6"

        self.property_display_to_id = {}

        self.voucher_id_var = tk.StringVar(value="تلقائي")
        self.amount_var = tk.StringVar(value="0.00")
        self.amount_var.trace_add("write", self._update_total_display)

        self._setup_styles()

        self.frame = ttk.Frame(master, style="App.Payment.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.main_card = ttk.Frame(self.frame, style="App.Payment.Card.TFrame")
        self.main_card.pack(fill="both", expand=True, padx=14, pady=14)

        self._build_header_buttons()
        self._build_form_content()
        self._load_initial_data()
        self._set_fields_state("disabled")

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
            style.map(btn_style, background=[("active", self.accent_color), ("pressed", self.accent_color)], foreground=[("active", "white"), ("pressed", "white")])

    def _build_header_buttons(self):
        header = ttk.Frame(self.main_card, style="App.Payment.Header.TFrame", height=68)
        header.pack(fill="x", side="top")

        ttk.Label(header, text=f"سند صرف نقدي - {SYSTEM_NAME}", style="App.Payment.Header.TLabel").pack(side="right", padx=30, pady=15)

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

        if widget_type == "entry":
            field = ttk.Entry(container, style="App.Payment.Field.TEntry", justify="right", **kwargs)
        elif widget_type == "combo":
            field = ttk.Combobox(container, style="App.Payment.Field.TCombobox", justify="right", **kwargs)
        else:
            field = tk.Text(container, font=("Segoe UI", 13, "bold"), bd=1, relief="solid", height=4, **kwargs)

        field.pack(side="left", fill="x", expand=True, padx=(0, 15))
        ttk.Label(container, text=label_text, style="App.Payment.FieldLabel.TLabel", width=22).pack(side="right")
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

        self.combo_prop = self._create_full_width_field(self.container, "الأرض /الأراضي :", widget_type="combo", state="readonly")
        self.combo_acc = self._create_full_width_field(self.container, "الحساب المحاسبي المدين :", widget_type="combo", state="readonly")

        bind_searchable_combobox(self.combo_prop)
        bind_searchable_combobox(self.combo_acc)

        self.ent_amount = self._create_full_width_field(self.container, "المبلغ المستحق صرفه :", textvariable=self.amount_var)
        self.ent_amount.configure(font=("Segoe UI", 22, "bold"), foreground="#c0392b")

        self.txt_desc = self._create_full_width_field(self.container, "شرح البيان العام :", widget_type="text")

        self.total_box = ttk.Frame(self.container, style="App.Payment.Total.TFrame", padding=16)
        self.total_box.pack(fill="x", pady=(24, 0))
        self.lbl_total_num = ttk.Label(self.total_box, text="الإجمالي: 0.00 ر.ي", style="App.Payment.TotalAmount.TLabel", anchor="center")
        self.lbl_total_num.pack()
        self.lbl_total_word = ttk.Label(self.total_box, text="فقط وقدره: لا شيء ريال يمني لا غير", style="App.Payment.TotalWords.TLabel", anchor="center")
        self.lbl_total_word.pack(pady=5)

    def _set_fields_state(self, state):
        for widget in (self.ent_date, self.combo_prop, self.combo_acc, self.ent_amount):
            widget.config(state=state)
        self.txt_desc.config(state="normal" if state == "normal" else "disabled", bg="white" if state == "normal" else "#f5f6f7")

    def _extract_code(self, display_value):
        text = (display_value or "").strip()
        if not text:
            return ""
        return text.split(" - ", 1)[0].strip()

    def _reset_and_new(self):
        self._set_fields_state("normal")
        self.amount_var.set("0.00")
        self.txt_desc.delete("1.0", tk.END)
        self.ent_date.delete(0, tk.END)
        self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM finance.vouchers")
                    self.voucher_id_var.set(str(cur.fetchone()[0]))
        except Exception:
            self.voucher_id_var.set("تلقائي")
        finally:
            conn.close()

    def _load_initial_data(self):
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, property_name, account_code FROM finance.properties ORDER BY property_name")
                    properties = cur.fetchall() or []
                    cur.execute(
                        """
                        SELECT account_code, account_name
                        FROM finance.accounts
                        WHERE account_level = 'تحليلي'
                          AND is_active = true
                        ORDER BY account_code
                        """
                    )
                    accounts = cur.fetchall() or []

            prop_values = []
            self.property_display_to_id = {}
            for row in properties:
                pid = row[0]
                pname = row[1] or ""
                pcode = str(row[2] or "").strip()
                display = f"{pcode} - {pname}" if pcode else pname
                if display:
                    prop_values.append(display)
                    self.property_display_to_id[display] = int(pid)

            set_combobox_values(self.combo_prop, prop_values)
            set_combobox_values(self.combo_acc, [f"{r[0]} - {r[1]}" for r in accounts if r[0]])
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل بيانات السند"))
        finally:
            conn.close()

    def _save_voucher(self):
        if self.ent_amount["state"] == "disabled":
            messagebox.showwarning("تنبيه", "يجب الضغط على زر 'جديد' أولاً")
            return
        self._persist_voucher(is_update=False)

    def _persist_voucher(self, is_update):
        prop_display = self.combo_prop.get().strip()
        prop_id = self.property_display_to_id.get(prop_display)
        acc_code = self._extract_code(self.combo_acc.get())
        if not prop_id or not acc_code:
            messagebox.showwarning("تنبيه", "يرجى اختيار الأرض والحساب")
            return

        try:
            amount = float((self.amount_var.get() or "0").replace(",", ""))
        except ValueError:
            messagebox.showwarning("تنبيه", "المبلغ يجب أن يكون رقمًا")
            return

        description = self.txt_desc.get("1.0", tk.END).strip()
        voucher_id = self.voucher_id_var.get().strip()

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    if is_update:
                        if not voucher_id.isdigit():
                            messagebox.showwarning("تنبيه", "ابحث عن سند صحيح قبل التعديل")
                            return
                        cur.execute(
                            "UPDATE finance.vouchers SET v_type=%s, v_date=%s, description=%s WHERE id=%s",
                            (VOUCHER_TYPE_PAYMENT, self.ent_date.get().strip(), description, int(voucher_id)),
                        )
                        cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (int(voucher_id),))
                        current_id = int(voucher_id)
                    else:
                        cur.execute(
                            "INSERT INTO finance.vouchers (v_type, v_date, description) VALUES (%s, %s, %s) RETURNING id",
                            (VOUCHER_TYPE_PAYMENT, self.ent_date.get().strip(), description),
                        )
                        current_id = int(cur.fetchone()[0])
                        self.voucher_id_var.set(str(current_id))

                    cur.execute(
                        "INSERT INTO finance.ledger (voucher_id, account_code, property_id, debit) VALUES (%s, %s, %s, %s)",
                        (current_id, acc_code, int(prop_id), amount),
                    )

            messagebox.showinfo("نجاح", "تم حفظ السند بنجاح")
            self._set_fields_state("disabled")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ سند الصرف"))
        finally:
            conn.close()

    def _update_voucher(self):
        self._persist_voucher(is_update=True)

    def _search_voucher(self):
        voucher_id = simpledialog.askstring("بحث", "أدخل رقم سند الصرف:", parent=self.master)
        if not voucher_id or not voucher_id.isdigit():
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT v.id, v.v_date, v.description, l.property_id, l.account_code, COALESCE(l.debit, 0)
                        FROM finance.vouchers v
                        JOIN finance.ledger l ON l.voucher_id = v.id
                        WHERE v.id = %s AND v.v_type = %s
                        ORDER BY l.id
                        LIMIT 1
                        """,
                        (int(voucher_id), VOUCHER_TYPE_PAYMENT),
                    )
                    row = cur.fetchone()

            if not row:
                messagebox.showinfo("بحث", "لم يتم العثور على السند")
                return

            self._set_fields_state("normal")
            self.voucher_id_var.set(str(row[0]))
            self.ent_date.delete(0, tk.END)
            self.ent_date.insert(0, str(row[1]))
            self.txt_desc.delete("1.0", tk.END)
            self.txt_desc.insert("1.0", row[2] or "")
            self.amount_var.set(str(row[5]))

            prop_match = []
            for display, pid in self.property_display_to_id.items():
                if int(pid) == int(row[3]):
                    prop_match.append(display)
                    break
            acc_match = [v for v in self.combo_acc["values"] if v.startswith(f"{row[4]} -")]
            self.combo_prop.set(prop_match[0] if prop_match else "")
            self.combo_acc.set(acc_match[0] if acc_match else "")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر جلب السند"))
        finally:
            conn.close()

    def _delete_voucher(self):
        voucher_id = self.voucher_id_var.get().strip()
        if not voucher_id.isdigit():
            messagebox.showwarning("تنبيه", "ابحث عن سند صحيح قبل الحذف")
            return

        if not messagebox.askyesno("تأكيد", "هل تريد حذف السند المحدد؟"):
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM finance.ledger WHERE voucher_id=%s", (int(voucher_id),))
                    cur.execute("DELETE FROM finance.vouchers WHERE id=%s AND v_type=%s", (int(voucher_id), VOUCHER_TYPE_PAYMENT))

            messagebox.showinfo("نجاح", "تم حذف سند الصرف")
            self.voucher_id_var.set("تلقائي")
            self._set_fields_state("disabled")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حذف سند الصرف"))
        finally:
            conn.close()

    def _update_total_display(self, *_):
        try:
            val = self.amount_var.get()
            amount = float(val) if val and val != "." else 0.0
            self.lbl_total_num.config(text=f"الإجمالي: {amount:,.2f} ر.ي")
            self.lbl_total_word.config(text=f"فقط وقدره: {amount:,.2f} ريال يمني لا غير")
        except Exception:
            pass
