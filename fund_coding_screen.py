import tkinter as tk
from tkinter import messagebox, ttk

import ttkbootstrap as tb

from app_constants import ACCOUNT_LEVEL_ANALYTICAL
from db_connection import get_connection, get_db_error_message


class FundCodingScreen:
    STATUS_ACTIVE = "فعال"
    STATUS_INACTIVE = "غير فعال"

    def __init__(self, master):
        self.master = master

        self.primary_color = "#0f2233"
        self.card_color = "#1b2d3f"
        self.accent_color = "#00ffff"
        self.text_color = "#ecf0f1"
        self.bg_color = "#0b1622"

        self.selected_account_id = None
        self.has_is_active_column = False

        self._setup_styles()
        self._build_layout()
        self._refresh_schema_flags()
        self._load_rows()
        self._new_fund()

    def _setup_styles(self):
        style = tb.Style()
        style.configure("Fund.Root.TFrame", background=self.bg_color)
        style.configure("Fund.Card.TFrame", background=self.card_color, bordercolor=self.accent_color, borderwidth=1, relief="solid")
        style.configure("Fund.Header.TFrame", background=self.primary_color)
        style.configure("Fund.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 18, "bold"))
        style.configure("Fund.Label.TLabel", background=self.card_color, foreground=self.text_color, font=("Segoe UI", 11, "bold"), anchor="e")

        style.configure("Fund.New.TButton", background="#2980b9", foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(10, 6))
        style.configure("Fund.Del.TButton", background="#e74c3c", foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(10, 6))
        style.configure("Fund.Edit.TButton", background="#f1c40f", foreground="#1b1b1b", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(10, 6))
        style.configure("Fund.Save.TButton", background="#27ae60", foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(10, 6))

        style.configure("Fund.Treeview", rowheight=30, font=("Segoe UI", 10), background="white", fieldbackground="white")
        style.configure("Fund.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.primary_color, foreground="white")
        style.map("Fund.Treeview", background=[("selected", "#1abc9c")], foreground=[("selected", "white")])

    def _build_layout(self):
        self.frame = tb.Frame(self.master, style="Fund.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=0)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_rowconfigure(0, weight=0)
        self.frame.grid_rowconfigure(1, weight=1)

        self.card = tb.Frame(self.frame, style="Fund.Card.TFrame", padding=0)
        self.card.grid(row=0, column=1, sticky="n", padx=20, pady=(20, 12))

        header = tb.Frame(self.card, style="Fund.Header.TFrame", padding=(16, 12))
        header.grid(row=0, column=0, sticky="ew")
        tb.Label(header, text="ترميز الصندوق", style="Fund.Header.TLabel", anchor="e").pack(side="right")

        form = tb.Frame(self.card, style="Fund.Card.TFrame", padding=(20, 16, 20, 8))
        form.grid(row=1, column=0, sticky="ew")
        form.grid_columnconfigure(0, weight=1)

        self.ent_code = self._create_field(form, 0, "كود الصندوق")
        self.ent_name = self._create_field(form, 1, "اسم الصندوق")
        self.combo_status = self._create_field(form, 2, "الحالة", field_type="combo")

        buttons = tb.Frame(self.card, style="Fund.Card.TFrame", padding=(14, 8, 14, 14))
        buttons.grid(row=2, column=0, sticky="ew")
        for idx in range(4):
            buttons.grid_columnconfigure(idx, weight=1)

        tb.Button(buttons, text="جديد", style="Fund.New.TButton", command=self._new_fund).grid(row=0, column=3, padx=4, sticky="ew")
        tb.Button(buttons, text="حذف", style="Fund.Del.TButton", command=self._delete).grid(row=0, column=2, padx=4, sticky="ew")
        tb.Button(buttons, text="تعديل", style="Fund.Edit.TButton", command=self._edit).grid(row=0, column=1, padx=4, sticky="ew")
        tb.Button(buttons, text="حفظ", style="Fund.Save.TButton", command=self._save).grid(row=0, column=0, padx=4, sticky="ew")

        table_wrap = tb.Frame(self.frame, style="Fund.Card.TFrame", padding=(10, 8, 10, 10))
        table_wrap.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=24, pady=(0, 16))
        table_wrap.grid_columnconfigure(0, weight=1)
        table_wrap.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_wrap, columns=("id", "code", "name", "status"), show="headings", style="Fund.Treeview")
        self.tree.heading("id", text="ID", anchor="e")
        self.tree.column("id", width=70, anchor="e")
        self.tree.heading("code", text="كود الصندوق", anchor="e")
        self.tree.column("code", width=130, anchor="e")
        self.tree.heading("name", text="اسم الصندوق", anchor="e")
        self.tree.column("name", width=260, anchor="e")
        self.tree.heading("status", text="الحالة", anchor="e")
        self.tree.column("status", width=90, anchor="e")

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _create_field(self, parent, row, label_text, field_type="entry"):
        row_wrap = tb.Frame(parent, style="Fund.Card.TFrame")
        row_wrap.grid(row=row, column=0, sticky="ew", pady=10)
        row_wrap.grid_columnconfigure(0, weight=1)

        ttk.Label(row_wrap, text=label_text, style="Fund.Label.TLabel", width=14).grid(row=0, column=1, sticky="e", padx=(0, 5))

        if field_type == "combo":
            widget = ttk.Combobox(row_wrap, values=(self.STATUS_ACTIVE, self.STATUS_INACTIVE), state="readonly", justify="right")
            widget.set(self.STATUS_ACTIVE)
        else:
            widget = ttk.Entry(row_wrap, justify="right", font=("Segoe UI", 11, "bold"))

        widget.grid(row=0, column=0, sticky="ew")
        return widget

    def _refresh_schema_flags(self):
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema='finance' AND table_name='accounts' AND column_name='is_active'
                        """
                    )
                    self.has_is_active_column = cur.fetchone() is not None
        except Exception:
            self.has_is_active_column = False
        finally:
            conn.close()

    def _bool_to_status(self, is_active):
        return self.STATUS_ACTIVE if bool(is_active) else self.STATUS_INACTIVE

    def _status_to_bool(self, status_text):
        return status_text != self.STATUS_INACTIVE

    def _new_fund(self):
        self.selected_account_id = None
        self.ent_code.delete(0, tk.END)
        self.ent_name.delete(0, tk.END)
        self.combo_status.set(self.STATUS_ACTIVE)
        self.ent_code.focus_set()

    def _load_rows(self):
        self.tree.delete(*self.tree.get_children())

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    status_expr = "COALESCE(is_active, true)" if self.has_is_active_column else "true"
                    cur.execute(
                        f"""
                        SELECT id, account_code, account_name, {status_expr}
                        FROM finance.accounts
                        WHERE TRIM(account_code) = '1101'
                           OR TRIM(parent_code) = '1101'
                           OR TRIM(account_code) LIKE '1101%'
                        ORDER BY account_code
                        """
                    )
                    rows = cur.fetchall() or []

            for row in rows:
                acc_id, code, name, is_active = row
                self.tree.insert("", tk.END, iid=str(acc_id), values=(acc_id, code, name, self._bool_to_status(is_active)))
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل الصناديق"))
        finally:
            conn.close()

    def _on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        data = self.tree.item(selected[0], "values")
        if not data:
            return

        self.selected_account_id = int(data[0])
        self.ent_code.delete(0, tk.END)
        self.ent_code.insert(0, data[1] or "")
        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, data[2] or "")
        self.combo_status.set(data[3] or self.STATUS_ACTIVE)

    def _validate(self):
        code = self.ent_code.get().strip()
        name = self.ent_name.get().strip()
        if not code:
            messagebox.showwarning("تنبيه", "يرجى إدخال كود الصندوق")
            self.ent_code.focus_set()
            return None
        if not name:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم الصندوق")
            self.ent_name.focus_set()
            return None
        return {
            "code": code,
            "name": name,
            "is_active": self._status_to_bool(self.combo_status.get().strip() or self.STATUS_ACTIVE),
        }

    def _save(self):
        payload = self._validate()
        if not payload:
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    if self.has_is_active_column:
                        cur.execute(
                            """
                            INSERT INTO finance.accounts (account_code, account_name, parent_code, account_level, is_active)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (payload["code"], payload["name"], "1101", ACCOUNT_LEVEL_ANALYTICAL, payload["is_active"]),
                        )
                    else:
                        cur.execute(
                            """
                            INSERT INTO finance.accounts (account_code, account_name, parent_code, account_level)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (payload["code"], payload["name"], "1101", ACCOUNT_LEVEL_ANALYTICAL),
                        )

            self._load_rows()
            self._new_fund()
            messagebox.showinfo("نجاح", "تم حفظ الصندوق")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ الصندوق"))
        finally:
            conn.close()

    def _edit(self):
        if not self.selected_account_id:
            messagebox.showwarning("تنبيه", "اختر صندوقاً للتعديل")
            return

        payload = self._validate()
        if not payload:
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    if self.has_is_active_column:
                        cur.execute(
                            """
                            UPDATE finance.accounts
                            SET account_code = %s,
                                account_name = %s,
                                is_active = %s
                            WHERE id = %s
                            """,
                            (payload["code"], payload["name"], payload["is_active"], self.selected_account_id),
                        )
                    else:
                        cur.execute(
                            """
                            UPDATE finance.accounts
                            SET account_code = %s,
                                account_name = %s
                            WHERE id = %s
                            """,
                            (payload["code"], payload["name"], self.selected_account_id),
                        )

            self._load_rows()
            messagebox.showinfo("نجاح", "تم تعديل الصندوق")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل الصندوق"))
        finally:
            conn.close()

    def _delete(self):
        if not self.selected_account_id:
            messagebox.showwarning("تنبيه", "اختر صندوقاً للحذف")
            return

        if not messagebox.askyesno("تأكيد", "هل تريد حذف الصندوق المحدد؟"):
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM finance.accounts WHERE id=%s", (self.selected_account_id,))

            self._load_rows()
            self._new_fund()
            messagebox.showinfo("نجاح", "تم حذف الصندوق")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حذف الصندوق"))
        finally:
            conn.close()

