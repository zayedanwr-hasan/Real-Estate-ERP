import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Optional

import ttkbootstrap as tb

from db_connection import get_connection, get_db_error_message


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _table_columns(cur, table_name):
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'finance' AND table_name = %s
        """,
        (table_name,),
    )
    return {row[0] for row in (cur.fetchall() or [])}


def _pick_column(columns, names):
    for name in names:
        if name in columns:
            return name
    return None


def _resolve_settings_columns(cur) -> Optional[Dict[str, Optional[str]]]:
    cols = _table_columns(cur, "system_settings")
    if not cols:
        return None

    mapping = {
        "company_name": _pick_column(cols, ("company_name", "company", "name")),
        "phone": _pick_column(cols, ("phone_number", "phone", "mobile")),
        "email": _pick_column(cols, ("email", "mail")),
        "address": _pick_column(cols, ("address", "company_address")),
        "logo_path": _pick_column(cols, ("logo_path", "logo", "company_logo")),
    }

    if not mapping["company_name"]:
        return None
    return mapping


def get_settings() -> Optional[Dict[str, str]]:
    """Return the single settings row from finance.system_settings, or None."""
    conn = get_connection()
    if not conn:
        return None

    try:
        with conn:
            with conn.cursor() as cur:
                mapping = _resolve_settings_columns(cur)
                if not mapping:
                    return None

                select_cols = [
                    mapping["company_name"],
                    mapping["phone"] or "NULL",
                    mapping["email"] or "NULL",
                    mapping["address"] or "NULL",
                    mapping["logo_path"] or "NULL",
                ]
                cur.execute(
                    f"SELECT {', '.join(select_cols)} FROM finance.system_settings LIMIT 1"
                )
                row = cur.fetchone()
                if not row:
                    return None

                return {
                    "company_name": row[0] or "",
                    "phone_number": row[1] or "",
                    "email": row[2] or "",
                    "address": row[3] or "",
                    "logo_path": row[4] or "",
                }
    except Exception as exc:
        messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل إعدادات النظام"))
        return None
    finally:
        conn.close()


def save_settings(data):
    """Upsert the single settings row in finance.system_settings."""
    conn = get_connection()
    if not conn:
        return False

    company_name = (data.get("company_name") or "").strip()
    phone_number = (data.get("phone_number") or "").strip()
    email = (data.get("email") or "").strip()
    address = (data.get("address") or "").strip()
    logo_path = (data.get("logo_path") or "").strip()

    try:
        with conn:
            with conn.cursor() as cur:
                mapping = _resolve_settings_columns(cur)
                if not mapping:
                    messagebox.showerror("خطأ", "جدول system_settings غير جاهز أو يفتقد عمود اسم الشركة")
                    return False

                set_parts = [f"{mapping['company_name']} = %s"]
                params = [company_name]

                if mapping["phone"]:
                    set_parts.append(f"{mapping['phone']} = %s")
                    params.append(phone_number)
                if mapping["email"]:
                    set_parts.append(f"{mapping['email']} = %s")
                    params.append(email)
                if mapping["address"]:
                    set_parts.append(f"{mapping['address']} = %s")
                    params.append(address)
                if mapping["logo_path"]:
                    set_parts.append(f"{mapping['logo_path']} = %s")
                    params.append(logo_path)

                cur.execute(
                    """
                    UPDATE finance.system_settings
                    SET {set_clause}
                    WHERE ctid IN (
                        SELECT ctid FROM finance.system_settings LIMIT 1
                    )
                    """.format(set_clause=", ".join(set_parts)),
                    tuple(params),
                )

                if cur.rowcount == 0:
                    insert_cols = [mapping["company_name"]]
                    insert_vals = ["%s"]
                    insert_params = [company_name]

                    if mapping["phone"]:
                        insert_cols.append(mapping["phone"])
                        insert_vals.append("%s")
                        insert_params.append(phone_number)
                    if mapping["email"]:
                        insert_cols.append(mapping["email"])
                        insert_vals.append("%s")
                        insert_params.append(email)
                    if mapping["address"]:
                        insert_cols.append(mapping["address"])
                        insert_vals.append("%s")
                        insert_params.append(address)
                    if mapping["logo_path"]:
                        insert_cols.append(mapping["logo_path"])
                        insert_vals.append("%s")
                        insert_params.append(logo_path)

                    cur.execute(
                        f"INSERT INTO finance.system_settings ({', '.join(insert_cols)}) "
                        f"VALUES ({', '.join(insert_vals)})",
                        tuple(insert_params),
                    )
        return True
    except Exception as exc:
        messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر حفظ إعدادات النظام"))
        return False
    finally:
        conn.close()


class SystemSettingsScreen:
    def __init__(self, master, current_user=None):
        self.master = master
        self.current_user = current_user

        self.primary_color = "#2C3E50"
        self.accent_color = "#1ABC9C"
        self.bg_color = "#F4F7F6"
        self.card_bg = "#FFFFFF"
        self.label_bg = "#E9EEF2"

        self.company_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.logo_path_var = tk.StringVar()

        self._setup_styles()
        self._build_layout()
        self.load_settings()

    def _setup_styles(self):
        style = tb.Style()

        style.configure("SysSet.Root.TFrame", background=self.bg_color)
        style.configure(
            "SysSet.Card.TFrame",
            background=self.card_bg,
            bordercolor="#D8DFE5",
            borderwidth=1,
            relief="solid",
        )
        style.configure("SysSet.Header.TFrame", background=self.card_bg)
        style.configure(
            "SysSet.Title.TLabel",
            background=self.card_bg,
            foreground=self.primary_color,
            font=("Segoe UI", 20, "bold"),
            anchor="e",
        )
        style.configure(
            "SysSet.Subtitle.TLabel",
            background=self.card_bg,
            foreground="#7F8C8D",
            font=("Segoe UI", 11),
            anchor="e",
        )

        style.configure(
            "SysSet.Label.TLabel",
            background=self.label_bg,
            foreground=self.primary_color,
            font=("Segoe UI", 11, "bold"),
            anchor="e",
            padding=6,
        )

        style.configure(
            "SysSet.Entry.TEntry",
            font=("Segoe UI", 11),
            foreground=self.primary_color,
            fieldbackground="#FFFFFF",
            bordercolor="#C9D3DB",
            lightcolor="#C9D3DB",
            darkcolor="#C9D3DB",
            insertcolor=self.primary_color,
            padding=6,
        )
        style.map(
            "SysSet.Entry.TEntry",
            bordercolor=[("focus", self.accent_color)],
            lightcolor=[("focus", self.accent_color)],
            darkcolor=[("focus", self.accent_color)],
        )

        style.configure(
            "SysSet.Primary.TButton",
            background=self.primary_color,
            foreground="white",
            font=("Segoe UI", 11, "bold"),
            borderwidth=0,
            padding=(14, 8),
        )
        style.configure(
            "SysSet.Secondary.TButton",
            background="#7F8C8D",
            foreground="white",
            font=("Segoe UI", 11, "bold"),
            borderwidth=0,
            padding=(14, 8),
        )
        style.configure(
            "SysSet.Choose.TButton",
            background=self.accent_color,
            foreground="white",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            padding=(10, 7),
        )

    def _build_layout(self):
        self.frame = tb.Frame(self.master, style="SysSet.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=0)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=0)
        self.frame.grid_rowconfigure(2, weight=1)

        self.card = tb.Frame(self.frame, style="SysSet.Card.TFrame", padding=(22, 20, 22, 18))
        self.card.grid(row=1, column=1, sticky="n", padx=20, pady=20)
        self.card.grid_columnconfigure(0, weight=1, minsize=560)

        header = tb.Frame(self.card, style="SysSet.Header.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)

        tb.Label(header, text="إعدادات النظام", style="SysSet.Title.TLabel").grid(row=0, column=0, sticky="e")
        tb.Label(header, text="System Configuration", style="SysSet.Subtitle.TLabel").grid(row=1, column=0, sticky="e", pady=(2, 0))

        form = tb.Frame(self.card, style="SysSet.Card.TFrame")
        form.grid(row=1, column=0, sticky="ew")
        form.grid_columnconfigure(0, weight=1)

        self.ent_company = self._create_entry_row(form, 0, "اسم الشركة", self.company_var)
        self.ent_phone = self._create_entry_row(form, 1, "رقم الهاتف", self.phone_var)
        self.ent_email = self._create_entry_row(form, 2, "البريد الإلكتروني", self.email_var)
        self.ent_address = self._create_entry_row(form, 3, "العنوان", self.address_var)

        self._create_logo_row(form, 4)

        buttons = tb.Frame(self.card, style="SysSet.Card.TFrame")
        buttons.grid(row=2, column=0, sticky="ew", pady=(18, 0))
        buttons.grid_columnconfigure(0, weight=1)

        btn_wrap = tb.Frame(buttons, style="SysSet.Card.TFrame")
        btn_wrap.grid(row=0, column=0)

        tb.Button(btn_wrap, text="💾 حفظ", style="SysSet.Primary.TButton", command=self.on_save).grid(
            row=0, column=0, padx=4
        )
        tb.Button(btn_wrap, text="🔄 إعادة تحميل", style="SysSet.Secondary.TButton", command=self.load_settings).grid(
            row=0, column=1, padx=4
        )

        self.ent_company.focus_set()

    def _create_entry_row(self, parent, row_idx, label_text, var):
        row = tb.Frame(parent, style="SysSet.Card.TFrame")
        row.grid(row=row_idx, column=0, sticky="ew", pady=8)
        row.grid_columnconfigure(0, weight=1)

        ttk.Label(row, text=label_text, style="SysSet.Label.TLabel", width=16).grid(
            row=0, column=1, sticky="e", padx=(0, 8)
        )

        entry = ttk.Entry(
            row,
            textvariable=var,
            style="SysSet.Entry.TEntry",
            justify="right",
            font=("Segoe UI", 11),
        )
        entry.grid(row=0, column=0, sticky="ew")
        return entry

    def _create_logo_row(self, parent, row_idx):
        row = tb.Frame(parent, style="SysSet.Card.TFrame")
        row.grid(row=row_idx, column=0, sticky="ew", pady=8)
        row.grid_columnconfigure(0, weight=1)

        ttk.Label(row, text="الشعار", style="SysSet.Label.TLabel", width=16).grid(
            row=0, column=1, sticky="e", padx=(0, 8)
        )

        logo_field = tb.Frame(row, style="SysSet.Card.TFrame")
        logo_field.grid(row=0, column=0, sticky="ew")
        logo_field.grid_columnconfigure(0, weight=1)

        self.ent_logo = ttk.Entry(
            logo_field,
            textvariable=self.logo_path_var,
            style="SysSet.Entry.TEntry",
            justify="right",
            font=("Segoe UI", 11),
            state="readonly",
        )
        self.ent_logo.grid(row=0, column=0, sticky="ew")

        tb.Button(
            logo_field,
            text="اختيار ملف",
            style="SysSet.Choose.TButton",
            command=self._choose_logo,
        ).grid(row=0, column=1, padx=(8, 0))

    def _bind_focus_highlight(self, entry):
        # Focus highlight is handled via style.map("SysSet.Entry.TEntry", state="focus").
        return

    def _choose_logo(self):
        file_path = filedialog.askopenfilename(
            title="اختيار شعار الشركة",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
                ("All Files", "*.*"),
            ],
        )
        if not file_path:
            return

        normalized = os.path.normpath(file_path)
        self.logo_path_var.set(normalized)

    def _validate(self):
        company_name = self.company_var.get().strip()
        email = self.email_var.get().strip()

        if not company_name:
            messagebox.showwarning("تنبيه", "اسم الشركة حقل إلزامي")
            self.ent_company.focus_set()
            return False

        if email and not EMAIL_REGEX.match(email):
            messagebox.showwarning("تنبيه", "صيغة البريد الإلكتروني غير صحيحة")
            self.ent_email.focus_set()
            return False

        return True

    def load_settings(self):
        data = get_settings()
        if data is None:
            self.company_var.set("")
            self.phone_var.set("")
            self.email_var.set("")
            self.address_var.set("")
            self.logo_path_var.set("")
            return

        self.company_var.set(data.get("company_name", ""))
        self.phone_var.set(data.get("phone_number", ""))
        self.email_var.set(data.get("email", ""))
        self.address_var.set(data.get("address", ""))
        self.logo_path_var.set(data.get("logo_path", ""))

    def on_save(self):
        if not self._validate():
            return

        payload = {
            "company_name": self.company_var.get(),
            "phone_number": self.phone_var.get(),
            "email": self.email_var.get(),
            "address": self.address_var.get(),
            "logo_path": self.logo_path_var.get(),
        }

        if save_settings(payload):
            messagebox.showinfo("نجاح", "تم حفظ إعدادات النظام بنجاح")


# Backward-compatible class name used by main.py
SettingsScreen = SystemSettingsScreen

