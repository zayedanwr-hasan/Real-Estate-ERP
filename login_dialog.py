import tkinter as tk
from tkinter import messagebox, ttk

from auth_service import authenticate_user, change_password


class LoginDialog:
    def __init__(self, parent):
        self.parent = parent
        self.result = None

        self.window = tk.Toplevel(parent)
        self.window.title("تسجيل الدخول")
        self.window.geometry("420x250")
        self.window.resizable(False, False)
        self.window.configure(bg="#f4f7f6")
        self.window.transient(parent)
        self.window.grab_set()

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self._build()

    def _build(self):
        frame = ttk.Frame(self.window, padding=16)
        frame.pack(fill="both", expand=True)
        frame.grid_columnconfigure(0, weight=1)

        ttk.Label(frame, text="تسجيل الدخول", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="e", pady=(0, 12))

        ttk.Label(frame, text="اسم المستخدم").grid(row=1, column=0, sticky="e")
        username_entry = ttk.Entry(frame, textvariable=self.username_var, justify="right", font=("Segoe UI", 11))
        username_entry.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text="كلمة المرور").grid(row=3, column=0, sticky="e")
        password_entry = ttk.Entry(frame, textvariable=self.password_var, justify="right", font=("Segoe UI", 11), show="*")
        password_entry.grid(row=4, column=0, sticky="ew", pady=(0, 12))

        actions = ttk.Frame(frame)
        actions.grid(row=5, column=0, sticky="ew")
        actions.grid_columnconfigure((0, 1), weight=1)

        ttk.Button(actions, text="دخول", command=self._submit).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Button(actions, text="إلغاء", command=self._cancel).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.window.bind("<Return>", lambda _e: self._submit())
        self.window.protocol("WM_DELETE_WINDOW", self._cancel)

        username_entry.focus_set()

    def _submit(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        if not username or not password:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم المستخدم وكلمة المرور", parent=self.window)
            return

        try:
            user = authenticate_user(username, password)
        except Exception as exc:
            messagebox.showerror("خطأ", f"تعذر تنفيذ تسجيل الدخول: {exc}", parent=self.window)
            return

        if not user:
            messagebox.showerror("خطأ", "بيانات الدخول غير صحيحة", parent=self.window)
            return

        if user.get("must_change_password"):
            new_password = self._prompt_new_password()
            if not new_password:
                return
            try:
                change_password(int(user["id"]), new_password)
                user["must_change_password"] = False
            except Exception as exc:
                messagebox.showerror("خطأ", f"تعذر تحديث كلمة المرور: {exc}", parent=self.window)
                return

        self.result = user
        self.window.destroy()

    def _prompt_new_password(self) -> str | None:
        prompt = tk.Toplevel(self.window)
        prompt.title("تغيير كلمة المرور")
        prompt.geometry("420x210")
        prompt.resizable(False, False)
        prompt.transient(self.window)
        prompt.grab_set()

        new_var = tk.StringVar()
        confirm_var = tk.StringVar()

        frame = ttk.Frame(prompt, padding=16)
        frame.pack(fill="both", expand=True)
        frame.grid_columnconfigure(0, weight=1)

        ttk.Label(frame, text="يجب تغيير كلمة مرور المدير الافتراضية", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="e", pady=(0, 10))
        ttk.Label(frame, text="كلمة المرور الجديدة").grid(row=1, column=0, sticky="e")
        ttk.Entry(frame, textvariable=new_var, show="*", justify="right").grid(row=2, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(frame, text="تأكيد كلمة المرور").grid(row=3, column=0, sticky="e")
        ttk.Entry(frame, textvariable=confirm_var, show="*", justify="right").grid(row=4, column=0, sticky="ew", pady=(0, 12))

        result = {"password": ""}

        def on_save():
            p1 = new_var.get().strip()
            p2 = confirm_var.get().strip()
            if len(p1) < 6:
                messagebox.showwarning("تنبيه", "كلمة المرور يجب ألا تقل عن 6 أحرف", parent=prompt)
                return
            if p1 != p2:
                messagebox.showwarning("تنبيه", "كلمتا المرور غير متطابقتين", parent=prompt)
                return
            result["password"] = p1
            prompt.destroy()

        ttk.Button(frame, text="حفظ", command=on_save).grid(row=5, column=0, sticky="ew")

        prompt.wait_window()
        return result["password"] or None

    def _cancel(self):
        self.result = None
        self.window.destroy()

    def show(self):
        self.parent.wait_window(self.window)
        return self.result

