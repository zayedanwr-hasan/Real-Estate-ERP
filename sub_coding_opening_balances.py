import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk

import ttkbootstrap as tb

from db_connection import get_connection


class SubCodingOpeningBalances:
    def __init__(self, master):
        self.master = master

        # Keep palette consistent with the rest of the ERP app.
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.separator_color = "#2c3e50"
        self.bg_color = "#f4f7f6"

        self.base_font = ("Segoe UI", 12, "bold")
        self.bold_font = ("Segoe UI", 13, "bold")
        self.title_font = ("Segoe UI", 18, "bold")

        self.selected_plot_id = None
        self.selected_vendor_id = None
        self.plot_rows_cache = []
        self.vendor_rows_cache = []

        self._setup_styles()
        self._build_layout()
        self._refresh_all_data()

    def _setup_styles(self):
        self.style = tb.Style()

        self.style.configure("ERP.Root.TFrame", background=self.bg_color)
        self.style.configure("ERP.Header.TFrame", background=self.primary_color)
        self.style.configure(
            "ERP.HeaderTitle.TLabel",
            background=self.primary_color,
            foreground=self.text_color,
            font=self.title_font,
            anchor="e",
        )
        self.style.configure("Card.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        self.style.configure("CardTitle.TLabel", background="#ffffff", foreground=self.primary_color, font=("Segoe UI", 13, "bold"))
        self.style.configure("Form.TLabel", background="#ffffff", font=self.bold_font, anchor="e", justify="right", foreground=self.primary_color)
        self.style.configure("Summary.TFrame", background="#f8fafc", relief="solid", borderwidth=1)
        self.style.configure("SummaryTitle.TLabel", background="#f8fafc", foreground=self.primary_color, font=self.bold_font)
        self.style.configure("SummaryAmount.TLabel", background="#f8fafc", foreground="#c0392b", font=("Segoe UI", 24, "bold"))
        self.style.configure("SummaryWords.TLabel", background="#f8fafc", foreground="#5a6a7a", font=self.base_font)
        self.style.configure("Amount.TEntry", fieldbackground="#fff4f4", foreground="#c0392b", font=("Segoe UI", 18, "bold"))
        self.style.configure("TNotebook.Tab", font=self.bold_font, padding=(14, 8))

        self.style.configure(
            "Treeview",
            rowheight=34,
            font=self.base_font,
            background="white",
            fieldbackground="white",
            foreground="#222222",
        )
        self.style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"), background=self.sidebar_color, foreground=self.primary_color)

    def _build_layout(self):
        self.root_container = ttk.Frame(self.master, style="ERP.Root.TFrame", padding=10)
        self.root_container.pack(fill="both", expand=True)

        self._build_header(self.root_container)

        notebook_wrapper = ttk.Frame(self.root_container, style="ERP.Root.TFrame")
        notebook_wrapper.pack(fill="both", expand=True, pady=(10, 0))

        self.notebook = ttk.Notebook(notebook_wrapper)
        self.notebook.pack(fill="both", expand=True)

        self.plot_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.plot_tab, text="تعريف العقارات")
        self._build_plot_interface()

        self.vendor_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.vendor_tab, text="الورثة والأرصدة الافتتاحية")
        self._build_vendor_interface()

    def _build_header(self, parent):
        header = ttk.Frame(parent, style="ERP.Header.TFrame", padding=(12, 10))
        header.pack(fill="x")
        header.columnconfigure(0, weight=0)
        header.columnconfigure(1, weight=1)

        actions = ttk.Frame(header, style="ERP.Header.TFrame")
        actions.grid(row=0, column=0, sticky="w")

        ttk.Button(actions, text="جديد", style="primary.TButton", command=self._action_new).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="حفظ", style="success.TButton", command=self._action_save).pack(side="left", padx=6)
        ttk.Button(actions, text="تعديل", style="warning.TButton", command=self._action_edit).pack(side="left", padx=6)
        ttk.Button(actions, text="حذف", style="danger.TButton", command=self._action_delete).pack(side="left", padx=6)
        ttk.Button(actions, text="بحث", style="secondary.TButton", command=self._action_search).pack(side="left", padx=6)
        ttk.Button(actions, text="خروج", style="dark.TButton", command=self._action_exit).pack(side="left", padx=(6, 0))

        ttk.Label(header, text="شاشة تعريف العقارات والورثة", style="ERP.HeaderTitle.TLabel").grid(row=0, column=1, sticky="e")

    def _build_plot_interface(self):
        container = ttk.Frame(self.plot_tab)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=2)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        table_card = ttk.Frame(container, style="Card.TFrame", padding=14)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(table_card, text="العقارات المسجلة", style="CardTitle.TLabel").pack(anchor="e", pady=(0, 8))

        cols = ("id", "name", "cost", "loc")
        heads = ["كود", "اسم العقار", "تكلفة/مساحة", "الموقع"]
        self.plot_tree = self._create_tree(table_card, cols, heads)
        self.plot_tree.bind("<<TreeviewSelect>>", self._on_plot_select)

        form_card = ttk.Frame(container, style="Card.TFrame", padding=14)
        form_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        form_card.columnconfigure(0, weight=1)

        ttk.Label(form_card, text="بيانات العقار", style="CardTitle.TLabel").grid(row=0, column=0, sticky="e", pady=(0, 8))
        self.p_name = self._create_label_entry(form_card, "اسم العقار:", 1)
        self.p_area = self._create_label_entry(form_card, "التكلفة/المساحة:", 2)
        self.p_loc = self._create_label_entry(form_card, "الموقع:", 3)

        ttk.Button(form_card, text="حفظ العقار", style="success.TButton", command=self._save_plot).grid(
            row=4, column=0, sticky="ew", pady=(12, 0)
        )

    def _build_vendor_interface(self):
        container = ttk.Frame(self.vendor_tab)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=2)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        table_card = ttk.Frame(container, style="Card.TFrame", padding=14)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(table_card, text="الورثة والأرصدة", style="CardTitle.TLabel").pack(anchor="e", pady=(0, 8))

        cols = ("id", "name", "group", "property", "bal")
        heads = ["كود", "الاسم", "المجموعة", "العقار المرتبط", "الرصيد"]
        self.vendor_tree = self._create_tree(table_card, cols, heads)
        self.vendor_tree.bind("<<TreeviewSelect>>", self._on_vendor_select)

        form_card = ttk.Frame(container, style="Card.TFrame", padding=14)
        form_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        form_card.columnconfigure(0, weight=1)

        ttk.Label(form_card, text="بيانات الوارث", style="CardTitle.TLabel").grid(row=0, column=0, sticky="e", pady=(0, 8))

        self.v_name = self._create_label_entry(form_card, "اسم الوارث:", 1)
        self.v_group = self._create_label_entry(form_card, "المجموعة:", 2)

        ttk.Label(form_card, text="اختر العقار (اختياري):", style="Form.TLabel").grid(row=3, column=0, sticky="e", pady=(8, 2))
        self.v_plot_cb = ttk.Combobox(form_card, state="readonly", justify="right", font=("Segoe UI", 12, "bold"))
        self.v_plot_cb.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        self.v_balance = self._create_label_entry(form_card, "رصيد افتتاحي (مدين):", 5, "Amount.TEntry")
        self.v_balance.insert(0, "0")
        self.v_balance.bind("<KeyRelease>", lambda _e: self._update_balance_preview())
        self.v_balance.bind("<FocusOut>", lambda _e: self._update_balance_preview())

        self._build_summary_box(form_card, 6)

        ttk.Button(form_card, text="حفظ الوارث", style="success.TButton", command=self._save_vendor).grid(
            row=7, column=0, sticky="ew", pady=(12, 0)
        )

    def _build_summary_box(self, parent, row):
        self.summary_amount_var = tk.StringVar(value="0.00")
        self.summary_words_var = tk.StringVar(value="فقط صفر")

        summary = ttk.Frame(parent, style="Summary.TFrame", padding=10)
        summary.grid(row=row, column=0, sticky="ew", pady=(8, 0))
        summary.columnconfigure(0, weight=1)

        ttk.Label(summary, text="ملخص الرصيد", style="SummaryTitle.TLabel").grid(row=0, column=0, sticky="e")
        ttk.Label(summary, textvariable=self.summary_amount_var, style="SummaryAmount.TLabel").grid(row=1, column=0, sticky="e")
        ttk.Label(summary, textvariable=self.summary_words_var, style="SummaryWords.TLabel").grid(row=2, column=0, sticky="e")

    def _create_label_entry(self, parent, txt, row, entry_style="TEntry"):
        ttk.Label(parent, text=txt, style="Form.TLabel").grid(row=row, column=0, sticky="e", pady=(8, 2))
        ent = ttk.Entry(parent, justify="right", font=("Segoe UI", 13, "bold"), style=entry_style)
        ent.grid(row=row + 1, column=0, sticky="ew", pady=(0, 6))
        return ent

    def _create_tree(self, parent, cols, heads):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")

        widths = {"id": 70, "name": 240, "cost": 130, "loc": 180, "group": 120, "property": 190, "bal": 120}
        for c, h in zip(cols, heads):
            tree.heading(c, text=h)
            tree.column(c, anchor="center", width=widths.get(c, 100), stretch=True)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True, side="left")

        tree.tag_configure("odd", background="#ffffff")
        tree.tag_configure("even", background="#f0f3f5")

        return tree

    def _fill_tree(self, tree, rows):
        tree.delete(*tree.get_children())
        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=row, tags=(tag,))

    def _refresh_all_data(self):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, property_name, COALESCE(total_cost, purchase_price, 0) AS total_cost, location FROM finance.properties")
        self.plot_rows_cache = cur.fetchall()
        self._fill_tree(self.plot_tree, self.plot_rows_cache)

        self.v_plot_cb["values"] = [f"{r[0]} - {r[1]}" for r in self.plot_rows_cache]
        self.v_plot_cb.set("")

        cur.execute(
            """
            SELECT v.id,
                   v.vendor_name,
                   v.group_name,
                   COALESCE(
                       (SELECT p.property_name
                        FROM finance.properties p
                        JOIN finance.ledger l ON l.property_id = p.id
                        WHERE l.vendor_id = v.id
                        LIMIT 1),
                       '-') AS property_name,
                   COALESCE((SELECT SUM(debit - credit) FROM finance.ledger WHERE vendor_id = v.id), 0) AS current_balance
            FROM finance.vendors v
            ORDER BY v.vendor_name
        """
        )
        self.vendor_rows_cache = cur.fetchall()
        self._fill_tree(self.vendor_tree, self.vendor_rows_cache)

        conn.close()

    def _save_plot(self):
        name = self.p_name.get().strip()
        cost = self.p_area.get().strip()
        loc = self.p_loc.get().strip()

        if not name:
            return messagebox.showwarning("تنبيه", "أدخل اسم العقار")

        try:
            cost_val = float(cost) if cost else None
        except Exception:
            cost_val = None

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO finance.properties (property_name, total_cost, location) VALUES (%s, %s, %s)",
                (name, cost_val, loc),
            )
            conn.commit()
            messagebox.showinfo("نجاح", "تم حفظ العقار")
            self._refresh_all_data()
            self._clear_plot_form()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _save_vendor(self):
        name = self.v_name.get().strip()
        group = self.v_group.get().strip()
        plot_info = self.v_plot_cb.get().strip()
        try:
            bal = float(self.v_balance.get().strip() or 0)
        except Exception:
            return messagebox.showwarning("تنبيه", "الرجاء إدخال رصيد افتتاحي صحيح")

        if not name:
            return messagebox.showwarning("تنبيه", "أكمل بيانات الوارث (الاسم)")

        property_id = None
        if plot_info:
            try:
                property_id = int(plot_info.split(" - ")[0])
            except Exception:
                property_id = None

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO finance.vendors (vendor_name, group_name) VALUES (%s, %s) RETURNING id", (name, group))
            v_id = cur.fetchone()[0]

            if bal > 0:
                cur.execute(
                    "INSERT INTO finance.vouchers (v_type, v_date, description) VALUES (%s, CURRENT_DATE, %s) RETURNING id",
                    ("رصيد افتتاحى", f"رصيد أول المدة: {name}"),
                )
                voc_id = cur.fetchone()[0]

                cur.execute(
                    "INSERT INTO finance.ledger (voucher_id, account_code, vendor_id, property_id, debit) VALUES (%s, %s, %s, %s, %s)",
                    (voc_id, "2101", v_id, property_id, bal),
                )
                cur.execute(
                    "INSERT INTO finance.ledger (voucher_id, account_code, credit) VALUES (%s, %s, %s)",
                    (voc_id, "3999", bal),
                )

            conn.commit()
            messagebox.showinfo("نجاح", "تم الحفظ")
            self._clear_vendor_form()
            self._refresh_all_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _action_new(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._clear_plot_form()
        else:
            self._clear_vendor_form()

    def _action_save(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._save_plot()
        else:
            self._save_vendor()

    def _action_edit(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._edit_plot()
        else:
            self._edit_vendor()

    def _action_delete(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._delete_plot()
        else:
            self._delete_vendor()

    def _action_search(self):
        query = simpledialog.askstring("بحث", "أدخل كلمة البحث:", parent=self.master)
        if query is None:
            return
        query = query.strip().lower()
        active_tab = self.notebook.index(self.notebook.select())

        if not query:
            self._refresh_all_data()
            return

        if active_tab == 0:
            filtered = [r for r in self.plot_rows_cache if query in str(r[1]).lower() or query in str(r[3] or "").lower()]
            self._fill_tree(self.plot_tree, filtered)
        else:
            filtered = [
                r
                for r in self.vendor_rows_cache
                if query in str(r[1]).lower() or query in str(r[2] or "").lower() or query in str(r[3] or "").lower()
            ]
            self._fill_tree(self.vendor_tree, filtered)

    def _action_exit(self):
        if messagebox.askyesno("تأكيد", "هل تريد إغلاق هذه الشاشة؟"):
            self.root_container.destroy()

    def _clear_plot_form(self):
        self.selected_plot_id = None
        self.p_name.delete(0, "end")
        self.p_area.delete(0, "end")
        self.p_loc.delete(0, "end")
        self.plot_tree.selection_remove(self.plot_tree.selection())

    def _clear_vendor_form(self):
        self.selected_vendor_id = None
        self.v_name.delete(0, "end")
        self.v_group.delete(0, "end")
        self.v_balance.delete(0, "end")
        self.v_balance.insert(0, "0")
        self.v_plot_cb.set("")
        self._update_balance_preview()
        self.vendor_tree.selection_remove(self.vendor_tree.selection())

    def _on_plot_select(self, _event=None):
        selected = self.plot_tree.selection()
        if not selected:
            return
        values = self.plot_tree.item(selected[0], "values")
        self.selected_plot_id = int(values[0])

        self.p_name.delete(0, "end")
        self.p_name.insert(0, values[1])
        self.p_area.delete(0, "end")
        self.p_area.insert(0, values[2])
        self.p_loc.delete(0, "end")
        self.p_loc.insert(0, values[3])

    def _on_vendor_select(self, _event=None):
        selected = self.vendor_tree.selection()
        if not selected:
            return
        values = self.vendor_tree.item(selected[0], "values")
        self.selected_vendor_id = int(values[0])

        self.v_name.delete(0, "end")
        self.v_name.insert(0, values[1])
        self.v_group.delete(0, "end")
        self.v_group.insert(0, values[2])
        self.v_balance.delete(0, "end")
        self.v_balance.insert(0, values[4])
        self._update_balance_preview()

    def _edit_plot(self):
        if not self.selected_plot_id:
            return messagebox.showwarning("تنبيه", "اختر عقارًا من الجدول أولاً")

        name = self.p_name.get().strip()
        cost = self.p_area.get().strip()
        loc = self.p_loc.get().strip()

        if not name:
            return messagebox.showwarning("تنبيه", "أدخل اسم العقار")

        try:
            cost_val = float(cost) if cost else None
        except Exception:
            return messagebox.showwarning("تنبيه", "التكلفة/المساحة غير صحيحة")

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE finance.properties SET property_name=%s, total_cost=%s, location=%s WHERE id=%s",
                (name, cost_val, loc, self.selected_plot_id),
            )
            conn.commit()
            messagebox.showinfo("نجاح", "تم تعديل بيانات العقار")
            self._refresh_all_data()
            self._clear_plot_form()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _edit_vendor(self):
        if not self.selected_vendor_id:
            return messagebox.showwarning("تنبيه", "اختر وارثًا من الجدول أولاً")

        name = self.v_name.get().strip()
        group = self.v_group.get().strip()
        plot_info = self.v_plot_cb.get().strip()
        try:
            bal = float(self.v_balance.get().strip() or 0)
        except Exception:
            return messagebox.showwarning("تنبيه", "الرصيد غير صحيح")

        if not name:
            return messagebox.showwarning("تنبيه", "أكمل بيانات الوارث (الاسم)")

        property_id = None
        if plot_info:
            try:
                property_id = int(plot_info.split(" - ")[0])
            except Exception:
                property_id = None

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "UPDATE finance.vendors SET vendor_name=%s, group_name=%s WHERE id=%s",
                (name, group, self.selected_vendor_id),
            )

            cur.execute(
                """
                SELECT l.voucher_id
                FROM finance.ledger l
                JOIN finance.vouchers v ON v.id = l.voucher_id
                WHERE l.vendor_id = %s
                  AND l.account_code = '2101'
                  AND v.v_type = %s
                ORDER BY l.id
                LIMIT 1
                """,
                (self.selected_vendor_id, "رصيد افتتاحى"),
            )
            opening_voucher = cur.fetchone()

            if opening_voucher:
                voucher_id = opening_voucher[0]
                cur.execute(
                    "UPDATE finance.ledger SET property_id=%s, debit=%s WHERE voucher_id=%s AND vendor_id=%s AND account_code='2101'",
                    (property_id, bal, voucher_id, self.selected_vendor_id),
                )
                cur.execute(
                    "UPDATE finance.ledger SET credit=%s WHERE voucher_id=%s AND account_code='3999'",
                    (bal, voucher_id),
                )

            conn.commit()
            messagebox.showinfo("نجاح", "تم تعديل بيانات الوارث")
            self._refresh_all_data()
            self._clear_vendor_form()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _delete_plot(self):
        if not self.selected_plot_id:
            return messagebox.showwarning("تنبيه", "اختر عقارًا من الجدول أولاً")

        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا العقار؟"):
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM finance.ledger WHERE property_id=%s", (self.selected_plot_id,))
            linked = cur.fetchone()[0]
            if linked > 0:
                return messagebox.showwarning("تنبيه", "لا يمكن حذف العقار لوجود قيود محاسبية مرتبطة به")

            cur.execute("DELETE FROM finance.properties WHERE id=%s", (self.selected_plot_id,))
            conn.commit()
            messagebox.showinfo("نجاح", "تم حذف العقار")
            self._refresh_all_data()
            self._clear_plot_form()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _delete_vendor(self):
        if not self.selected_vendor_id:
            return messagebox.showwarning("تنبيه", "اختر وارثًا من الجدول أولاً")

        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا الوارث؟"):
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM finance.ledger l
                LEFT JOIN finance.vouchers v ON v.id = l.voucher_id
                WHERE l.vendor_id = %s
                  AND COALESCE(v.v_type, '') <> %s
                """,
                (self.selected_vendor_id, "رصيد افتتاحى"),
            )
            has_non_opening_entries = cur.fetchone()[0]
            if has_non_opening_entries > 0:
                return messagebox.showwarning("تنبيه", "لا يمكن حذف الوارث لوجود قيود حركة مرتبطة به")

            cur.execute(
                """
                SELECT DISTINCT l.voucher_id
                FROM finance.ledger l
                JOIN finance.vouchers v ON v.id = l.voucher_id
                WHERE l.vendor_id = %s AND v.v_type = %s
                """,
                (self.selected_vendor_id, "رصيد افتتاحى"),
            )
            opening_vouchers = [r[0] for r in cur.fetchall() if r[0] is not None]

            if opening_vouchers:
                cur.execute("DELETE FROM finance.ledger WHERE voucher_id = ANY(%s)", (opening_vouchers,))
                cur.execute("DELETE FROM finance.vouchers WHERE id = ANY(%s)", (opening_vouchers,))

            cur.execute("DELETE FROM finance.vendors WHERE id=%s", (self.selected_vendor_id,))
            conn.commit()
            messagebox.showinfo("نجاح", "تم حذف الوارث")
            self._refresh_all_data()
            self._clear_vendor_form()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _update_balance_preview(self):
        text = self.v_balance.get().strip()
        try:
            value = float(text or 0)
        except Exception:
            value = 0.0
        self.summary_amount_var.set(f"{value:,.2f}")
        self.summary_words_var.set(self._amount_to_words(value))

    def _amount_to_words(self, value):
        number = int(abs(value))
        if number == 0:
            return "فقط صفر"
        words = self._int_to_arabic_words(number)
        return f"فقط {words}"

    def _int_to_arabic_words(self, n):
        units = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"]
        teens = ["عشرة", "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر", "ستة عشر", "سبعة عشر", "ثمانية عشر", "تسعة عشر"]
        tens = ["", "", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"]
        hundreds = ["", "مئة", "مئتان", "ثلاثمئة", "أربعمئة", "خمسمئة", "ستمئة", "سبعمئة", "ثمانمئة", "تسعمئة"]

        def under_1000(x):
            parts = []
            h = x // 100
            r = x % 100
            if h:
                parts.append(hundreds[h])
            if 10 <= r <= 19:
                parts.append(teens[r - 10])
            else:
                t = r // 10
                u = r % 10
                if u:
                    parts.append(units[u])
                if t:
                    parts.append(tens[t])
            return " و ".join(parts)

        chunks = []
        millions = n // 1000000
        thousands = (n % 1000000) // 1000
        rest = n % 1000

        if millions:
            chunks.append(f"{under_1000(millions)} مليون")
        if thousands:
            chunks.append(f"{under_1000(thousands)} ألف")
        if rest:
            chunks.append(under_1000(rest))

        return " و ".join([c for c in chunks if c])
