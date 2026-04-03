import tkinter as tk
from tkinter import messagebox, ttk

import ttkbootstrap as tb

from app_constants import VENDOR_CONTROL_ACCOUNT_CODE
from db_connection import get_connection, get_db_error_message


class VendorsScreen:
    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.accent_color = "#1abc9c"
        self.bg_color = "#f4f7f6"

        self.selected_vendor_id = None

        self._setup_styles()
        self._build_layout()
        self._load_rows()

    def _setup_styles(self):
        style = tb.Style()
        style.configure("Vend.Root.TFrame", background=self.bg_color)
        style.configure("Vend.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("Vend.Header.TFrame", background=self.primary_color)
        style.configure("Vend.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 16, "bold"))
        style.configure("Vend.Treeview", rowheight=30, font=("Segoe UI", 10), background="white", fieldbackground="white")
        style.configure("Vend.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.primary_color, foreground="white")
        style.map("Vend.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "white")])

    def _build_layout(self):
        self.frame = tb.Frame(self.master, style="Vend.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        header = tb.Frame(self.frame, style="Vend.Header.TFrame", padding=10)
        header.pack(fill="x")
        tb.Label(header, text="ترميز الموردين/الورثة", style="Vend.Header.TLabel").pack(side="right")

        actions = tb.Frame(header, style="Vend.Header.TFrame")
        actions.pack(side="left")
        for title, cmd in (("جديد", self._clear_form), ("حفظ", self._save), ("تعديل", self._edit), ("حذف", self._delete)):
            tb.Button(actions, text=title, command=cmd).pack(side="left", padx=3)

        content = tb.Frame(self.frame, style="Vend.Root.TFrame", padding=10)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=2)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        table_card = tb.Frame(content, style="Vend.Card.TFrame", padding=8)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        form_card = tb.Frame(content, style="Vend.Card.TFrame", padding=8)
        form_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        form_card.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_card,
            columns=("id", "name", "phone", "national_id", "control_account"),
            show="headings",
            style="Vend.Treeview",
        )
        for col, title, width in (
            ("id", "ID", 70),
            ("name", "اسم المورد/الوارث", 240),
            ("phone", "الهاتف", 120),
            ("national_id", "الهوية", 130),
            ("control_account", "حساب التحكم", 110),
        ):
            self.tree.heading(col, text=title, anchor="e")
            self.tree.column(col, width=width, anchor="e")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.ent_name = self._make_entry(form_card, "اسم المورد/الوارث", 0)
        self.ent_phone = self._make_entry(form_card, "الهاتف", 2)
        self.ent_national_id = self._make_entry(form_card, "الهوية", 4)
        self.ent_control = self._make_entry(form_card, "حساب التحكم", 6, readonly=True)
        self._set_entry(self.ent_control, VENDOR_CONTROL_ACCOUNT_CODE)

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
        self.selected_vendor_id = None
        for entry in (self.ent_name, self.ent_phone, self.ent_national_id):
            entry.delete(0, tk.END)
        self._set_entry(self.ent_control, VENDOR_CONTROL_ACCOUNT_CODE)

    def _detect_columns(self, cur):
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema='finance' AND table_name='vendors'
            """
        )
        return {row[0] for row in (cur.fetchall() or [])}

    def _pick_column(self, columns, choices):
        for col in choices:
            if col in columns:
                return col
        return None

    def _load_rows(self):
        self.tree.delete(*self.tree.get_children())
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cols = self._detect_columns(cur)
                    phone_col = self._pick_column(cols, ("phone", "mobile", "phone_number", "vendor_phone"))
                    nid_col = self._pick_column(cols, ("national_id", "id_number"))
                    control_col = "control_account" if "control_account" in cols else None

                    phone_select = phone_col if phone_col else "NULL"
                    nid_select = nid_col if nid_col else "NULL"
                    control_select = f"COALESCE({control_col}, %s)" if control_col else "%s"

                    cur.execute(
                        f"""
                        SELECT id, vendor_name, {phone_select}, {nid_select}, {control_select}
                        FROM finance.vendors
                        ORDER BY id DESC
                        """,
                        (VENDOR_CONTROL_ACCOUNT_CODE,),
                    )
                    rows = cur.fetchall() or []

            for row in rows:
                self.tree.insert("", tk.END, iid=str(row[0]), values=tuple("" if v is None else v for v in row))
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل الموردين"))
        finally:
            conn.close()

    def _on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        row = self.tree.item(selected[0], "values")
        if not row:
            return

        self.selected_vendor_id = int(row[0])
        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, row[1] or "")
        self.ent_phone.delete(0, tk.END)
        self.ent_phone.insert(0, row[2] or "")
        self.ent_national_id.delete(0, tk.END)
        self.ent_national_id.insert(0, row[3] or "")
        self._set_entry(self.ent_control, row[4] or VENDOR_CONTROL_ACCOUNT_CODE)

    def _save(self):
        name = self.ent_name.get().strip()
        if not name:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم المورد/الوارث")
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cols = self._detect_columns(cur)
                    phone_col = self._pick_column(cols, ("phone", "mobile", "phone_number", "vendor_phone"))
                    nid_col = self._pick_column(cols, ("national_id", "id_number"))

                    insert_cols = ["vendor_name"]
                    values = [name]
                    if phone_col:
                        insert_cols.append(phone_col)
                        values.append(self.ent_phone.get().strip() or None)
                    if nid_col:
                        insert_cols.append(nid_col)
                        values.append(self.ent_national_id.get().strip() or None)
                    if "control_account" in cols:
                        insert_cols.append("control_account")
                        values.append(VENDOR_CONTROL_ACCOUNT_CODE)

                    placeholders = ", ".join(["%s"] * len(insert_cols))
                    cur.execute(
                        f"INSERT INTO finance.vendors ({', '.join(insert_cols)}) VALUES ({placeholders})",
                        tuple(values),
                    )

            self._clear_form()
            self._load_rows()
            messagebox.showinfo("نجاح", "تم حفظ المورد/الوارث")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ المورد/الوارث"))
        finally:
            conn.close()

    def _edit(self):
        if not self.selected_vendor_id:
            messagebox.showwarning("تنبيه", "اختر مورداً للتعديل")
            return

        name = self.ent_name.get().strip()
        if not name:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم المورد/الوارث")
            return

        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cols = self._detect_columns(cur)
                    phone_col = self._pick_column(cols, ("phone", "mobile", "phone_number", "vendor_phone"))
                    nid_col = self._pick_column(cols, ("national_id", "id_number"))

                    set_parts = ["vendor_name=%s"]
                    values = [name]
                    if phone_col:
                        set_parts.append(f"{phone_col}=%s")
                        values.append(self.ent_phone.get().strip() or None)
                    if nid_col:
                        set_parts.append(f"{nid_col}=%s")
                        values.append(self.ent_national_id.get().strip() or None)
                    if "control_account" in cols:
                        set_parts.append("control_account=%s")
                        values.append(VENDOR_CONTROL_ACCOUNT_CODE)

                    values.append(self.selected_vendor_id)
                    cur.execute(f"UPDATE finance.vendors SET {', '.join(set_parts)} WHERE id=%s", tuple(values))

            self._load_rows()
            messagebox.showinfo("نجاح", "تم تعديل المورد/الوارث")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل المورد/الوارث"))
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
                    cur.execute("DELETE FROM finance.vendors WHERE id=%s", (self.selected_vendor_id,))
            self._clear_form()
            self._load_rows()
            messagebox.showinfo("نجاح", "تم حذف المورد")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حذف المورد"))
        finally:
            conn.close()

