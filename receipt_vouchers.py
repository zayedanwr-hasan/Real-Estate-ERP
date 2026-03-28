import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import ttkbootstrap as ttk

from app_constants import SYSTEM_NAME
from combobox_helper import bind_searchable_combobox, set_combobox_values
from db_connection import get_connection, get_db_error_message


class ReceiptVoucherScreen:
    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.bg_color = "#f4f7f6"

        self.voucher_type = "سند قبض"
        self.voucher_id_var = tk.StringVar(value="تلقائي")

        self.property_display_to_id = {}
        self.account_display_to_code = {}
        self.vendor_display_to_id = {}

        self.line_items = []
        self.selected_line_index = None

        self._setup_styles()
        self.frame = ttk.Frame(master, style="App.Receipt.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.main_card = ttk.Frame(self.frame, style="App.Receipt.Card.TFrame")
        self.main_card.pack(fill="both", expand=True, padx=14, pady=14)

        self._build_header_buttons()
        self._build_form_content()
        self._load_initial_data()
        self._reset_and_new()

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("App.Receipt.Root.TFrame", background=self.bg_color)
        style.configure("App.Receipt.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("App.Receipt.Header.TFrame", background=self.primary_color)
        style.configure("App.Receipt.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 20, "bold"))
        style.configure("App.Receipt.Content.TFrame", background="white")
        style.configure("App.Receipt.FieldLabel.TLabel", background=self.sidebar_color, foreground=self.text_color, font=("Segoe UI", 13, "bold"), anchor="center", padding=9)
        style.configure("App.Receipt.Field.TEntry", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 15, "bold"))
        style.configure("App.Receipt.Field.TCombobox", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 14, "bold"))
        style.configure("App.Receipt.Total.TFrame", background="#f8f9fa", bordercolor="#d8e1e8", borderwidth=1, relief="solid")
        style.configure("App.Receipt.TotalAmount.TLabel", background="#f8f9fa", foreground="#1b5e20", font=("Segoe UI", 30, "bold"))
        style.configure("App.Receipt.TotalWords.TLabel", background="#f8f9fa", foreground=self.sidebar_color, font=("Segoe UI", 14, "bold"))

        style.configure("App.Receipt.Primary.TButton", background="#2980b9", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Receipt.Success.TButton", background="#27ae60", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Receipt.Warning.TButton", background="#f1c40f", foreground="#2c3e50", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Receipt.Danger.TButton", background="#e74c3c", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Receipt.Info.TButton", background="#8e44ad", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Receipt.Exit.TButton", background="#e67e22", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))

        for btn_style in (
            "App.Receipt.Primary.TButton",
            "App.Receipt.Success.TButton",
            "App.Receipt.Warning.TButton",
            "App.Receipt.Danger.TButton",
            "App.Receipt.Info.TButton",
            "App.Receipt.Exit.TButton",
        ):
            style.map(btn_style, background=[("active", self.accent_color), ("pressed", self.accent_color)], foreground=[("active", "white"), ("pressed", "white")])

    def _build_header_buttons(self):
        header = ttk.Frame(self.main_card, style="App.Receipt.Header.TFrame", height=68)
        header.pack(fill="x", side="top")
        ttk.Label(header, text=f"سند قبض - {SYSTEM_NAME}", style="App.Receipt.Header.TLabel").pack(side="right", padx=30, pady=15)

        btn_group = ttk.Frame(header, style="App.Receipt.Header.TFrame")
        btn_group.pack(side="left", padx=20)

        btn_data = [
            ("جديد", "App.Receipt.Primary.TButton", self._reset_and_new),
            ("إضافة سطر", "App.Receipt.Success.TButton", self._add_line),
            ("تعديل سطر", "App.Receipt.Warning.TButton", self._edit_line),
            ("حذف سطر", "App.Receipt.Danger.TButton", self._delete_line),
            ("حفظ السند", "App.Receipt.Info.TButton", self._save_voucher),
            ("طباعة", "App.Receipt.Primary.TButton", self._print_voucher),
            ("خروج", "App.Receipt.Exit.TButton", self.master.quit),
        ]
        for txt, style_name, cmd in btn_data:
            ttk.Button(btn_group, text=txt, style=style_name, width=10, command=cmd).pack(side="left", padx=4)

    def _create_full_width_field(self, parent, label_text, widget_type="entry", **kwargs):
        container = ttk.Frame(parent, style="App.Receipt.Content.TFrame")
        container.pack(fill="x", pady=8)

        if widget_type == "entry":
            field = ttk.Entry(container, style="App.Receipt.Field.TEntry", justify="right", **kwargs)
        elif widget_type == "combo":
            field = ttk.Combobox(container, style="App.Receipt.Field.TCombobox", justify="right", **kwargs)
        else:
            field = tk.Text(container, font=("Segoe UI", 13, "bold"), bd=1, relief="solid", height=3, **kwargs)

        field.pack(side="left", fill="x", expand=True, padx=(0, 15))
        ttk.Label(container, text=label_text, style="App.Receipt.FieldLabel.TLabel", width=22).pack(side="right")
        return field

    def _build_form_content(self):
        self.container = ttk.Frame(self.main_card, style="App.Receipt.Content.TFrame", padding=(32, 18))
        self.container.pack(fill="both", expand=True)

        row1 = ttk.Frame(self.container, style="App.Receipt.Content.TFrame")
        row1.pack(fill="x")
        left1 = ttk.Frame(row1, style="App.Receipt.Content.TFrame")
        left1.pack(side="left", fill="x", expand=True)
        right1 = ttk.Frame(row1, style="App.Receipt.Content.TFrame")
        right1.pack(side="right", fill="x", expand=True, padx=(16, 0))

        self.ent_date = self._create_full_width_field(left1, "التاريخ :")
        self.ent_id = self._create_full_width_field(right1, "رقم السند :", textvariable=self.voucher_id_var, state="readonly")

        row2 = ttk.Frame(self.container, style="App.Receipt.Content.TFrame")
        row2.pack(fill="x")
        left2 = ttk.Frame(row2, style="App.Receipt.Content.TFrame")
        left2.pack(side="left", fill="x", expand=True)
        right2 = ttk.Frame(row2, style="App.Receipt.Content.TFrame")
        right2.pack(side="right", fill="x", expand=True, padx=(16, 0))

        self.combo_currency = self._create_full_width_field(left2, "العملة :", widget_type="combo", state="readonly")
        self.combo_cash_acc = self._create_full_width_field(right2, "حساب النقد/البنك :", widget_type="combo", state="readonly")

        row3 = ttk.Frame(self.container, style="App.Receipt.Content.TFrame")
        row3.pack(fill="x")
        self.combo_beneficiary = self._create_full_width_field(row3, "اسم المستفيد :", widget_type="combo", state="readonly")

        bind_searchable_combobox(self.combo_currency)
        bind_searchable_combobox(self.combo_cash_acc)
        bind_searchable_combobox(self.combo_beneficiary)

        self.txt_desc = self._create_full_width_field(self.container, "البيان :", widget_type="text")
        self.txt_notes = self._create_full_width_field(self.container, "ملاحظات :", widget_type="text")

        self._build_line_editor()
        self._build_lines_table()

        self.total_box = ttk.Frame(self.container, style="App.Receipt.Total.TFrame", padding=14)
        self.total_box.pack(fill="x", pady=(16, 0))
        self.lbl_total_num = ttk.Label(self.total_box, text="إجمالي القبض: 0.00 ر.ي", style="App.Receipt.TotalAmount.TLabel", anchor="center")
        self.lbl_total_num.pack()
        self.lbl_total_word = ttk.Label(self.total_box, text="فقط وقدره: لا شيء ريال يمني لا غير", style="App.Receipt.TotalWords.TLabel", anchor="center")
        self.lbl_total_word.pack(pady=4)

    def _build_line_editor(self):
        editor = ttk.Labelframe(self.container, text=" تفاصيل السطر ", style="App.Receipt.Content.TFrame", padding=10)
        editor.pack(fill="x", pady=(12, 6))

        r1 = ttk.Frame(editor, style="App.Receipt.Content.TFrame")
        r1.pack(fill="x")
        left = ttk.Frame(r1, style="App.Receipt.Content.TFrame")
        left.pack(side="left", fill="x", expand=True)
        right = ttk.Frame(r1, style="App.Receipt.Content.TFrame")
        right.pack(side="right", fill="x", expand=True, padx=(12, 0))

        self.combo_line_acc = self._create_full_width_field(left, "حساب السطر :", widget_type="combo", state="readonly")
        self.ent_line_amount = self._create_full_width_field(right, "المبلغ :")

        r2 = ttk.Frame(editor, style="App.Receipt.Content.TFrame")
        r2.pack(fill="x")
        left2 = ttk.Frame(r2, style="App.Receipt.Content.TFrame")
        left2.pack(side="left", fill="x", expand=True)
        right2 = ttk.Frame(r2, style="App.Receipt.Content.TFrame")
        right2.pack(side="right", fill="x", expand=True, padx=(12, 0))

        self.combo_line_property = self._create_full_width_field(left2, "الأرض (اختياري) :", widget_type="combo", state="readonly")
        self.combo_line_vendor = self._create_full_width_field(right2, "المورد (اختياري) :", widget_type="combo", state="readonly")

        self.ent_line_desc = self._create_full_width_field(editor, "وصف السطر :")

        bind_searchable_combobox(self.combo_line_acc)
        bind_searchable_combobox(self.combo_line_property)
        bind_searchable_combobox(self.combo_line_vendor)

    def _build_lines_table(self):
        table_frame = ttk.Frame(self.container, style="App.Receipt.Content.TFrame")
        table_frame.pack(fill="both", expand=True, pady=(6, 0))

        cols = ("code", "name", "amount", "desc", "property", "vendor")
        self.lines_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.lines_tree.heading("code", text="كود الحساب")
        self.lines_tree.heading("name", text="اسم الحساب")
        self.lines_tree.heading("amount", text="المبلغ")
        self.lines_tree.heading("desc", text="الوصف")
        self.lines_tree.heading("property", text="الأرض")
        self.lines_tree.heading("vendor", text="المورد")

        self.lines_tree.column("code", width=110, anchor="center")
        self.lines_tree.column("name", width=180, anchor="e")
        self.lines_tree.column("amount", width=120, anchor="e")
        self.lines_tree.column("desc", width=190, anchor="e")
        self.lines_tree.column("property", width=140, anchor="e")
        self.lines_tree.column("vendor", width=140, anchor="e")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.lines_tree.yview)
        self.lines_tree.configure(yscrollcommand=y_scroll.set)

        self.lines_tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")
        self.lines_tree.bind("<<TreeviewSelect>>", self._on_line_selected)

    def _set_fields_state(self, state):
        for widget in (self.ent_date, self.combo_currency, self.combo_cash_acc, self.combo_beneficiary):
            widget.config(state=state)
        self.txt_desc.config(state="normal" if state == "normal" else "disabled", bg="white" if state == "normal" else "#f5f6f7")
        self.txt_notes.config(state="normal" if state == "normal" else "disabled", bg="white" if state == "normal" else "#f5f6f7")

    def _extract_code(self, display_value):
        text = (display_value or "").strip()
        if not text:
            return ""
        return text.split(" - ", 1)[0].strip()

    def _fmt_amount(self, value):
        return f"{float(value):,.2f}"

    def _parse_amount(self, text):
        return float((text or "0").replace(",", "").strip())

    def _reset_and_new(self):
        self._set_fields_state("normal")
        self.ent_date.delete(0, tk.END)
        self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.combo_currency.set("ريال يمني")
        self.combo_cash_acc.set("")
        self.combo_beneficiary.set("")

        self.txt_desc.delete("1.0", tk.END)
        self.txt_notes.delete("1.0", tk.END)

        self.line_items.clear()
        self.selected_line_index = None
        self._clear_line_editor()
        self._refresh_lines_table()

        conn = get_connection()
        if not conn:
            self.voucher_id_var.set("تلقائي")
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

                    cur.execute("SELECT id, vendor_name, account_code FROM finance.vendors ORDER BY vendor_name")
                    vendors = cur.fetchall() or []

            prop_values = []
            self.property_display_to_id = {}
            for pid, pname, pcode in properties:
                display = f"{str(pcode or '').strip()} - {(pname or '').strip()}".strip(" -")
                if display:
                    prop_values.append(display)
                    self.property_display_to_id[display] = int(pid)

            account_values = []
            self.account_display_to_code = {}
            for acode, aname in accounts:
                code = str(acode or "").strip()
                display = f"{code} - {(aname or '').strip()}".strip(" -")
                if code and display:
                    account_values.append(display)
                    self.account_display_to_code[display] = code

            vendor_values = []
            self.vendor_display_to_id = {}
            for vid, vname, vcode in vendors:
                display = f"{str(vcode or '').strip()} - {(vname or '').strip()}".strip(" -")
                if display:
                    vendor_values.append(display)
                    self.vendor_display_to_id[display] = int(vid)

            set_combobox_values(self.combo_currency, ["ريال يمني", "USD", "SAR"])
            set_combobox_values(self.combo_cash_acc, account_values)
            set_combobox_values(self.combo_beneficiary, vendor_values)

            set_combobox_values(self.combo_line_acc, account_values)
            set_combobox_values(self.combo_line_property, ["", *prop_values])
            set_combobox_values(self.combo_line_vendor, ["", *vendor_values])

        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل بيانات سند القبض"))
        finally:
            conn.close()

    def _clear_line_editor(self):
        self.combo_line_acc.set("")
        self.ent_line_amount.delete(0, tk.END)
        self.ent_line_desc.delete(0, tk.END)
        self.combo_line_property.set("")
        self.combo_line_vendor.set("")

    def _line_from_editor(self):
        acc_display = self.combo_line_acc.get().strip()
        acc_code = self.account_display_to_code.get(acc_display)
        if not acc_code:
            messagebox.showwarning("تنبيه", "اختر حسابًا تحليليًا للسطر")
            return None

        try:
            amount = self._parse_amount(self.ent_line_amount.get())
        except Exception:
            messagebox.showwarning("تنبيه", "المبلغ غير صحيح")
            return None

        if amount <= 0:
            messagebox.showwarning("تنبيه", "قيمة السطر يجب أن تكون أكبر من صفر")
            return None

        prop_display = self.combo_line_property.get().strip()
        vendor_display = self.combo_line_vendor.get().strip()

        return {
            "account_code": acc_code,
            "account_name": acc_display.split(" - ", 1)[1] if " - " in acc_display else acc_display,
            "amount": amount,
            "description": self.ent_line_desc.get().strip(),
            "property_id": self.property_display_to_id.get(prop_display),
            "property_name": prop_display.split(" - ", 1)[1] if " - " in prop_display else prop_display,
            "vendor_id": self.vendor_display_to_id.get(vendor_display),
            "vendor_name": vendor_display.split(" - ", 1)[1] if " - " in vendor_display else vendor_display,
        }

    def _add_line(self):
        line = self._line_from_editor()
        if not line:
            return
        self.line_items.append(line)
        self._clear_line_editor()
        self._refresh_lines_table()

    def _edit_line(self):
        if self.selected_line_index is None:
            messagebox.showwarning("تنبيه", "اختر سطرًا للتعديل")
            return

        line = self._line_from_editor()
        if not line:
            return

        self.line_items[self.selected_line_index] = line
        self.selected_line_index = None
        self._clear_line_editor()
        self._refresh_lines_table()

    def _delete_line(self):
        if self.selected_line_index is None:
            messagebox.showwarning("تنبيه", "اختر سطرًا للحذف")
            return
        del self.line_items[self.selected_line_index]
        self.selected_line_index = None
        self._clear_line_editor()
        self._refresh_lines_table()

    def _on_line_selected(self, _event=None):
        selected = self.lines_tree.selection()
        if not selected:
            return

        idx = int(selected[0])
        if idx < 0 or idx >= len(self.line_items):
            return

        self.selected_line_index = idx
        line = self.line_items[idx]

        for display, code in self.account_display_to_code.items():
            if code == line["account_code"]:
                self.combo_line_acc.set(display)
                break

        self.ent_line_amount.delete(0, tk.END)
        self.ent_line_amount.insert(0, self._fmt_amount(line["amount"]))
        self.ent_line_desc.delete(0, tk.END)
        self.ent_line_desc.insert(0, line["description"])

        self.combo_line_property.set("")
        if line.get("property_id"):
            for display, pid in self.property_display_to_id.items():
                if pid == line["property_id"]:
                    self.combo_line_property.set(display)
                    break

        self.combo_line_vendor.set("")
        if line.get("vendor_id"):
            for display, vid in self.vendor_display_to_id.items():
                if vid == line["vendor_id"]:
                    self.combo_line_vendor.set(display)
                    break

    def _refresh_lines_table(self):
        self.lines_tree.delete(*self.lines_tree.get_children())
        total = 0.0
        for idx, line in enumerate(self.line_items):
            total += line["amount"]
            self.lines_tree.insert(
                "",
                tk.END,
                iid=str(idx),
                values=(
                    line["account_code"],
                    line["account_name"],
                    self._fmt_amount(line["amount"]),
                    line.get("description", ""),
                    line.get("property_name", ""),
                    line.get("vendor_name", ""),
                ),
            )

        self.lbl_total_num.config(text=f"إجمالي القبض: {self._fmt_amount(total)} ر.ي")
        self.lbl_total_word.config(text=f"فقط وقدره: {self._fmt_amount(total)} ريال يمني لا غير")

    def _save_voucher(self):
        cash_display = self.combo_cash_acc.get().strip()
        cash_account_code = self.account_display_to_code.get(cash_display)
        beneficiary_id = self.vendor_display_to_id.get(self.combo_beneficiary.get().strip())

        if not cash_account_code:
            messagebox.showwarning("تنبيه", "اختر حساب النقد/البنك (تحليلي)")
            return

        if beneficiary_id is None:
            messagebox.showwarning("تنبيه", "اختر اسم المستفيد")
            return

        if not self.line_items:
            messagebox.showwarning("تنبيه", "يجب إضافة سطر واحد على الأقل")
            return

        for line in self.line_items:
            if line["amount"] <= 0:
                messagebox.showwarning("تنبيه", "كل مبالغ السطور يجب أن تكون أكبر من صفر")
                return

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    desc = self.txt_desc.get("1.0", tk.END).strip()
                    notes = self.txt_notes.get("1.0", tk.END).strip()
                    full_desc = f"{desc}\n{notes}".strip()

                    cur.execute(
                        """
                        INSERT INTO finance.vouchers (v_type, v_date, description)
                        VALUES (%s, %s, %s)
                        RETURNING id
                        """,
                        (self.voucher_type, self.ent_date.get().strip(), full_desc),
                    )
                    voucher_id = int(cur.fetchone()[0])

                    for line in self.line_items:
                        line_vendor_id = line.get("vendor_id") or beneficiary_id

                        # Debit cash/bank account for receipt voucher.
                        cur.execute(
                            """
                            INSERT INTO finance.ledger (voucher_id, account_code, property_id, vendor_id, debit, description)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (
                                voucher_id,
                                cash_account_code,
                                line.get("property_id"),
                                line_vendor_id,
                                line["amount"],
                                line.get("description", ""),
                            ),
                        )

                        # Credit line account.
                        cur.execute(
                            """
                            INSERT INTO finance.ledger (voucher_id, account_code, property_id, vendor_id, credit, description)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (
                                voucher_id,
                                line["account_code"],
                                line.get("property_id"),
                                line_vendor_id,
                                line["amount"],
                                line.get("description", ""),
                            ),
                        )

            self.voucher_id_var.set(str(voucher_id))
            messagebox.showinfo("نجاح", "تم حفظ سند القبض بنجاح")
            self._set_fields_state("disabled")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ سند القبض"))
        finally:
            conn.close()

    def _print_voucher(self):
        messagebox.showinfo("طباعة", "تم تجهيز السند للطباعة")
