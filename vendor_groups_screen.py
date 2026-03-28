import tkinter as tk
from tkinter import messagebox, ttk

import ttkbootstrap as tb

from db_connection import get_connection, get_db_error_message


class VendorGroupsScreen:
    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.bg_color = "#f4f7f6"

        self._setup_styles()

        self.frame = tb.Frame(master, style="App.VGroup.Root.TFrame", padding=12)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.main_card = tb.Frame(self.frame, style="App.VGroup.Card.TFrame", padding=14)
        self.main_card.pack(fill="both", expand=True)

        form_row = tb.Frame(self.main_card, style="App.VGroup.Card.TFrame")
        form_row.pack(fill="x", pady=(0, 12))
        form_row.columnconfigure(0, weight=1)

        tb.Label(form_row, text="اسم المجموعة", style="App.VGroup.FieldLabel.TLabel").grid(row=0, column=1, sticky="e", padx=8, pady=6)
        self.entry_group_name = tb.Entry(form_row, justify="right", style="App.VGroup.Field.TEntry", font=("Segoe UI", 12, "bold"))
        self.entry_group_name.grid(row=0, column=0, sticky="ew", padx=8, pady=6)

        tb.Button(self.main_card, text="حفظ المجموعة", style="App.VGroup.Action.TButton", command=self.save_group).pack(anchor="e", pady=(0, 10))

        columns = ("group_name", "account_code")
        self.tree = ttk.Treeview(self.main_card, columns=columns, show="headings", style="App.VGroup.Treeview")
        self.tree.heading("group_name", text="اسم المجموعة", anchor="e")
        self.tree.heading("account_code", text="كود الحساب", anchor="e")
        self.tree.column("group_name", width=260, anchor="e")
        self.tree.column("account_code", width=160, anchor="e")

        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("odd", background="#ffffff")
        self.tree.tag_configure("even", background="#f0f3f5")

        self.refresh_groups()

    def _setup_styles(self):
        style = tb.Style()
        style.configure("App.VGroup.Root.TFrame", background=self.bg_color)
        style.configure("App.VGroup.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("App.VGroup.FieldLabel.TLabel", background="white", foreground=self.primary_color, font=("Segoe UI", 12, "bold"))
        style.configure("App.VGroup.Field.TEntry", fieldbackground="white", foreground=self.primary_color)
        style.configure("App.VGroup.Action.TButton", background="#27ae60", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.map("App.VGroup.Action.TButton", background=[("active", self.accent_color), ("pressed", self.accent_color)], foreground=[("active", "white"), ("pressed", "white")])
        style.configure("App.VGroup.Treeview", rowheight=30, font=("Segoe UI", 10), background="white", fieldbackground="white", foreground=self.primary_color)
        style.configure("App.VGroup.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.primary_color, foreground="white")

    def save_group(self):
        group_name = self.entry_group_name.get().strip()
        if not group_name:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم المجموعة")
            return

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO finance.vendor_groups (group_name) VALUES (%s)", (group_name,))
            messagebox.showinfo("نجاح", "تم حفظ المجموعة")
            self.entry_group_name.delete(0, tk.END)
            self.refresh_groups()
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل حفظ مجموعة الموردين"))
        finally:
            conn.close()

    def refresh_groups(self):
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT group_name, account_code
                        FROM finance.vendor_groups
                        ORDER BY group_name
                        """
                    )
                    rows = cur.fetchall() or []

            for idx, row in enumerate(rows):
                tag = "even" if idx % 2 == 0 else "odd"
                self.tree.insert("", tk.END, values=(row[0] or "", row[1] or ""), tags=(tag,))
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر تحميل مجموعات الموردين"))
        finally:
            conn.close()

