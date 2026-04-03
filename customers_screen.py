import tkinter as tk
from tkinter import messagebox, ttk

import ttkbootstrap as tb

from app_constants import CUSTOMER_CONTROL_ACCOUNT_CODE
from db_connection import get_connection, get_db_error_message


class CustomersScreen:
    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.accent_color = "#1abc9c"
        self.bg_color = "#f4f7f6"

        self.selected_customer_id = None

        self._setup_styles()
        self._build_layout()
        self._load_rows()

    def _setup_styles(self):
        style = tb.Style()
        style.configure("Cust.Root.TFrame", background=self.bg_color)
        style.configure("Cust.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("Cust.Header.TFrame", background=self.primary_color)
        style.configure("Cust.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 16, "bold"))
        style.configure("Cust.Treeview", rowheight=30, font=("Segoe UI", 10), background="white", fieldbackground="white")
        style.configure("Cust.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.primary_color, foreground="white")
        style.map("Cust.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "white")])

    def _build_layout(self):
        self.frame = tb.Frame(self.master, style="Cust.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        header = tb.Frame(self.frame, style="Cust.Header.TFrame", padding=10)
        header.pack(fill="x")
        tb.Label(header, text="ترميز العملاء", style="Cust.Header.TLabel").pack(side="right")

        actions = tb.Frame(header, style="Cust.Header.TFrame")
        actions.pack(side="left")
        for title, cmd in (("جديد", self._clear_form), ("حفظ", self._save), ("تعديل", self._edit), ("حذف", self._delete)):
            tb.Button(actions, text=title, command=cmd).pack(side="left", padx=3)

        content = tb.Frame(self.frame, style="Cust.Root.TFrame", padding=10)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=2)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        table_card = tb.Frame(content, style="Cust.Card.TFrame", padding=8)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        form_card = tb.Frame(content, style="Cust.Card.TFrame", padding=8)
        form_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        form_card.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_card,
            columns=("id", "code", "name", "phone", "national_id", "control_account"),
            show="headings",
            style="Cust.Treeview",
        )
        for col, title, width in (
            ("id", "ID", 70),
            ("code", "كود العميل", 110),
            ("name", "اسم العميل", 220),
            ("phone", "الهاتف", 120),
            ("national_id", "الهوية", 130),
            ("control_account", "حساب التحكم", 110),
        ):
            self.tree.heading(col, text=title, anchor="e")
            self.tree.column(col, width=width, anchor="e")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.ent_code = self._make_entry(form_card, "كود العميل", 0)
        self.ent_name = self._make_entry(form_card, "اسم العميل", 2)
        self.ent_phone = self._make_entry(form_card, "الهاتف", 4)
        self.ent_national_id = self._make_entry(form_card, "الهوية", 6)
        self.ent_control = self._make_entry(form_card, "حساب التحكم", 8, readonly=True)
        self._set_entry(self.ent_control, CUSTOMER_CONTROL_ACCOUNT_CODE)

    def _make_entry(self, parent, label, row, readonly=False):
        ttk.Label(parent, text=label, anchor="e").grid(row=row, column=0, sticky="e", pady=(8, 4))
        ent = ttk.Entry(parent, justify="right", font=("Segoe UI", 11, "bold"))
        ent.grid(row=row + 1, column=0, sticky="ew")
        if readonly:
            ent.configure(state="readonly")
        return ent

    def _set_entry(self, entry, value):
        readonly = str(entry.cget("state")) == "readonly"
        if readonly:
            entry.configure(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, value)
        if readonly:
            entry.configure(state="readonly")

    def _clear_form(self):
        self.selected_customer_id = None
        for entry in (self.ent_code, self.ent_name, self.ent_phone, self.ent_national_id):
            entry.delete(0, tk.END)
        self._set_entry(self.ent_control, CUSTOMER_CONTROL_ACCOUNT_CODE)

    def _load_rows(self):
        self.tree.delete(*self.tree.get_children())
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, customer_code, customer_name, phone, national_id, COALESCE(control_account, %s)
                        FROM finance.customers
                        ORDER BY id DESC
                        """,
                        (CUSTOMER_CONTROL_ACCOUNT_CODE,),
                    )
                    rows = cur.fetchall() or []

            for row in rows:
                self.tree.insert("", tk.END, iid=str(row[0]), values=tuple("" if v is None else v for v in row))
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل العملاء"))
        finally:
            conn.close()

    def _on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        row = self.tree.item(selected[0], "values")
        if not row:
            return

        self.selected_customer_id = int(row[0])
        self.ent_code.delete(0, tk.END)
        self.ent_code.insert(0, row[1] or "")
        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, row[2] or "")
        self.ent_phone.delete(0, tk.END)
        self.ent_phone.insert(0, row[3] or "")
        self.ent_national_id.delete(0, tk.END)
        self.ent_national_id.insert(0, row[4] or "")
        self._set_entry(self.ent_control, row[5] or CUSTOMER_CONTROL_ACCOUNT_CODE)

    def _save(self):
        name = self.ent_name.get().strip()
        if not name:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم العميل")
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO finance.customers (customer_code, customer_name, phone, national_id, control_account)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            self.ent_code.get().strip() or None,
                            name,
                            self.ent_phone.get().strip() or None,
                            self.ent_national_id.get().strip() or None,
                            CUSTOMER_CONTROL_ACCOUNT_CODE,
                        ),
                    )
            self._clear_form()
            self._load_rows()
            messagebox.showinfo("نجاح", "تم حفظ العميل")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ العميل"))
        finally:
            conn.close()

    def _edit(self):
        if not self.selected_customer_id:
            messagebox.showwarning("تنبيه", "اختر عميلاً للتعديل")
            return

        name = self.ent_name.get().strip()
        if not name:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم العميل")
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE finance.customers
                        SET customer_code=%s,
                            customer_name=%s,
                            phone=%s,
                            national_id=%s,
                            control_account=%s
                        WHERE id=%s
                        """,
                        (
                            self.ent_code.get().strip() or None,
                            name,
                            self.ent_phone.get().strip() or None,
                            self.ent_national_id.get().strip() or None,
                            CUSTOMER_CONTROL_ACCOUNT_CODE,
                            self.selected_customer_id,
                        ),
                    )
            self._load_rows()
            messagebox.showinfo("نجاح", "تم تعديل العميل")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل العميل"))
        finally:
            conn.close()

    def _delete(self):
        if not self.selected_customer_id:
            messagebox.showwarning("تنبيه", "اختر عميلاً للحذف")
            return
        if not messagebox.askyesno("تأكيد", "هل تريد حذف العميل المحدد؟"):
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM finance.customers WHERE id=%s", (self.selected_customer_id,))
            self._clear_form()
            self._load_rows()
            messagebox.showinfo("نجاح", "تم حذف العميل")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حذف العميل"))
        finally:
            conn.close()
