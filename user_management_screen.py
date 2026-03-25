import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import ttkbootstrap as tb

from auth_service import (
    change_user_role,
    create_user,
    list_users,
    reset_user_password,
    set_user_active,
)


class UserManagementScreen:
    def __init__(self, master, current_user=None):
        self.master = master
        self.current_user = current_user or {}
        self.selected_user_id = None
        self.selected_username = ""

        self.bg_color = "#f4f7f6"
        self.primary_color = "#2c3e50"
        self.base_font = ("Segoe UI", 11)

        self.new_username_var = tk.StringVar()
        self.new_password_var = tk.StringVar()
        self.new_role_var = tk.StringVar(value="viewer")
        self.role_change_var = tk.StringVar(value="viewer")

        self._build_layout()
        self._refresh_users()

    def _build_layout(self):
        root = ttk.Frame(self.master, padding=12)
        root.pack(fill="both", expand=True)
        root.grid_columnconfigure(0, weight=2)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)

        left = ttk.Frame(root)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ttk.Label(left, text="إدارة المستخدمين والصلاحيات", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, sticky="e", pady=(0, 8)
        )

        self.tree = ttk.Treeview(
            left,
            columns=("id", "username", "role", "active", "must_change", "created"),
            show="headings",
        )
        headers = ["ID", "اسم المستخدم", "الدور", "نشط", "إجبار تغيير كلمة المرور", "تاريخ الإنشاء"]
        for col, head in zip(self.tree["columns"], headers):
            self.tree.heading(col, text=head, anchor="e")
            self.tree.column(col, anchor="e", width=130, stretch=True)

        self.tree.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        right = ttk.Frame(root, padding=10)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.grid_columnconfigure(0, weight=1)

        ttk.Label(right, text="إضافة مستخدم جديد", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="e")

        ttk.Label(right, text="اسم المستخدم").grid(row=1, column=0, sticky="e", pady=(8, 2))
        ttk.Entry(right, textvariable=self.new_username_var, justify="right", font=self.base_font).grid(row=2, column=0, sticky="ew")

        ttk.Label(right, text="كلمة المرور").grid(row=3, column=0, sticky="e", pady=(8, 2))
        ttk.Entry(right, textvariable=self.new_password_var, show="*", justify="right", font=self.base_font).grid(row=4, column=0, sticky="ew")

        ttk.Label(right, text="الدور").grid(row=5, column=0, sticky="e", pady=(8, 2))
        ttk.Combobox(right, textvariable=self.new_role_var, values=["admin", "accountant", "viewer"], state="readonly").grid(
            row=6, column=0, sticky="ew"
        )

        tb.Button(right, text="إنشاء مستخدم", bootstyle="success", command=self._create_user).grid(
            row=7, column=0, sticky="ew", pady=(10, 12)
        )

        ttk.Separator(right).grid(row=8, column=0, sticky="ew", pady=6)
        ttk.Label(right, text="إدارة المستخدم المحدد", font=("Segoe UI", 12, "bold")).grid(row=9, column=0, sticky="e")

        ttk.Label(right, text="تغيير الدور").grid(row=10, column=0, sticky="e", pady=(8, 2))
        ttk.Combobox(right, textvariable=self.role_change_var, values=["admin", "accountant", "viewer"], state="readonly").grid(
            row=11, column=0, sticky="ew"
        )

        tb.Button(right, text="تحديث الدور", bootstyle="info", command=self._change_role).grid(
            row=12, column=0, sticky="ew", pady=(8, 4)
        )
        tb.Button(right, text="تعطيل/تفعيل المستخدم", bootstyle="warning", command=self._toggle_active).grid(
            row=13, column=0, sticky="ew", pady=4
        )
        tb.Button(right, text="إعادة تعيين كلمة المرور", bootstyle="secondary", command=self._reset_password).grid(
            row=14, column=0, sticky="ew", pady=4
        )
        tb.Button(right, text="تحديث القائمة", bootstyle="primary", command=self._refresh_users).grid(
            row=15, column=0, sticky="ew", pady=(10, 0)
        )

    def _refresh_users(self):
        self.tree.delete(*self.tree.get_children())
        users = list_users()
        for i, user in enumerate(users):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "",
                "end",
                values=(
                    user["id"],
                    user["username"],
                    user["role"],
                    "نعم" if user["is_active"] else "لا",
                    "نعم" if user["must_change_password"] else "لا",
                    user["created_at"],
                ),
                tags=(tag,),
            )
        self.tree.tag_configure("even", background="#f8fafb")
        self.tree.tag_configure("odd", background="#ffffff")

    def _on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            self.selected_user_id = None
            self.selected_username = ""
            return
        row = self.tree.item(selected[0], "values")
        self.selected_user_id = int(row[0])
        self.selected_username = row[1]
        self.role_change_var.set(row[2])

    def _create_user(self):
        username = self.new_username_var.get().strip()
        password = self.new_password_var.get().strip()
        role = self.new_role_var.get().strip()

        if not username or not password:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم المستخدم وكلمة المرور")
            return

        try:
            create_user(username=username, password=password, role=role)
            messagebox.showinfo("نجاح", "تم إنشاء المستخدم بنجاح")
            self.new_username_var.set("")
            self.new_password_var.set("")
            self.new_role_var.set("viewer")
            self._refresh_users()
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc))

    def _change_role(self):
        if not self.selected_user_id:
            messagebox.showwarning("تنبيه", "اختر مستخدمًا أولًا")
            return
        new_role = self.role_change_var.get().strip()
        try:
            change_user_role(self.selected_user_id, new_role)
            messagebox.showinfo("نجاح", "تم تحديث الدور")
            self._refresh_users()
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc))

    def _toggle_active(self):
        if not self.selected_user_id:
            messagebox.showwarning("تنبيه", "اختر مستخدمًا أولًا")
            return

        current_row = self.tree.item(self.tree.selection()[0], "values")
        currently_active = current_row[3] == "نعم"

        try:
            set_user_active(self.selected_user_id, not currently_active)
            messagebox.showinfo("نجاح", "تم تحديث حالة المستخدم")
            self._refresh_users()
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc))

    def _reset_password(self):
        if not self.selected_user_id:
            messagebox.showwarning("تنبيه", "اختر مستخدمًا أولًا")
            return

        new_password = simpledialog.askstring(
            "إعادة تعيين كلمة المرور",
            f"كلمة مرور جديدة للمستخدم {self.selected_username}:",
            show="*",
        )
        if not new_password:
            return
        if len(new_password.strip()) < 6:
            messagebox.showwarning("تنبيه", "كلمة المرور يجب ألا تقل عن 6 أحرف")
            return

        try:
            reset_user_password(self.selected_user_id, new_password.strip())
            messagebox.showinfo("نجاح", "تمت إعادة تعيين كلمة المرور")
            self._refresh_users()
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc))

