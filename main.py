import tkinter as tk
from tkinter import messagebox
from properties_screen import PropertyScreen
from payment_vouchers import PaymentVoucherScreen
from receipt_vouchers import ReceiptVoucherScreen
from chart_of_accounts import ChartOfAccountsScreen

class RealEstateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("نظام الصوفي للمقاولات والعقارات - v2.0")
        self.root.geometry("1200x800")

        # --- لوحة الألوان الجديدة ---
        self.primary_color = "#2c3e50"  # الكحلي الغامق (Header)
        self.sidebar_color = "#34495e"  # الكحلي المتوسط (Sidebar)
        self.accent_color = "#1abc9c"  # التيركواز (Hover & Icons)
        self.text_color = "#ecf0f1"  # الأبيض الكريمي (للنصوص - واضح جداً)
        self.separator_color = "#2c3e50"  # لون الخط الفاصل
        self.bg_color = "#f4f7f6"  # خلفية النظام العامة

        self.root.configure(bg=self.bg_color)

        # 1. الترويسة العلوية
        self.header = tk.Frame(self.root, bg=self.primary_color, height=70)
        self.header.pack(fill="x", side="top")

        tk.Label(self.header, text="نظام الإدارة العقارية والمحاسبية المتكامل",
                 fg="white", bg=self.primary_color, font=("Segoe UI", 20, "bold")).pack(pady=15)

        # 2. السايد بار
        self.sidebar = tk.Frame(self.root, bg=self.sidebar_color, width=260)
        self.sidebar.pack(side="right", fill="y")

        # عنوان السايد بار بلون رمادي فاتح لتمييزه عن الأزرار
        tk.Label(self.sidebar, text="القائمة الرئيسية", fg="#bdc3c7",
                 bg=self.sidebar_color, font=("Segoe UI", 10, "bold")).pack(pady=(30, 10))

        self.create_menu()

        # 3. منطقة العرض
        self.display_area = tk.Frame(self.root, bg=self.bg_color)
        self.display_area.pack(side="left", fill="both", expand=True)

        self.show_welcome_screen()

    def create_menu(self):
        """إنشاء القائمة مع تنسيق الألوان الجديد والخطوط الفاصلة"""
        menu_items = [
            ("🏢  إدارة العقارات", self.open_properties),
            ("📁  دليل الحسابات", self.open_accounts),
            ("📤  سند صرف نقدي", self.open_payment_voucher),
            ("📥  سند قبض نقدي", self.open_receipt_voucher),
            ("📝  قيد يومية يدوي", self.open_manual_journal),
            ("📊  التقارير المالية", self.open_reports),
            ("⚙️  إعدادات النظام", self.dummy_msg),
            ("🚪  إغلاق النظام", self.root.quit),
        ]

        for text, command in menu_items:
            # حاوية الزر
            btn_frame = tk.Frame(self.sidebar, bg=self.sidebar_color)
            btn_frame.pack(fill="x", padx=10, pady=2)

            btn = tk.Button(
                btn_frame,
                text=text,
                font=("Segoe UI", 11, "bold"),
                bg=self.sidebar_color,
                fg=self.text_color,  # اللون الكريمي المختار
                bd=0,
                padx=20,
                pady=12,
                anchor="e",
                activebackground=self.accent_color,
                activeforeground="white",
                cursor="hand2",
                command=command,
            )
            btn.pack(fill="x")

            # إضافة الخط الفاصل (Separator)
            line = tk.Frame(self.sidebar, bg=self.separator_color, height=1)
            line.pack(fill="x", padx=25, pady=2)

            # تأثير الـ Hover المطور (تغيير لون النص أيضاً عند المرور)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.accent_color, fg="white"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.sidebar_color, fg=self.text_color))

    def clear_display_area(self):
        for widget in self.display_area.winfo_children():
            widget.destroy()

    def show_welcome_screen(self):
        self.clear_display_area()
        welcome_frame = tk.Frame(self.display_area, bg=self.bg_color)
        welcome_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(welcome_frame, text="مرحباً بك في نظام الصوفي",
                 font=("Segoe UI", 26, "bold"), bg=self.bg_color, fg=self.primary_color).pack()
        tk.Label(welcome_frame, text="الإدارة المالية العقارية أصبحت أسهل",
                 font=("Segoe UI", 14), bg=self.bg_color, fg="#7f8c8d").pack(pady=10)

    # --- دالات الربط ---
    def open_properties(self):
        self.clear_display_area()
        try:
            self.current_page = PropertyScreen(self.display_area)
        except Exception as e:
            messagebox.showerror("خطأ", str(e))

    def open_payment_voucher(self):
        self.clear_display_area()
        try:
            self.current_page = PaymentVoucherScreen(self.display_area)
        except Exception as e:
            messagebox.showerror("خطأ", str(e))

    def open_receipt_voucher(self):
        self.clear_display_area()
        try:
            self.current_page = ReceiptVoucherScreen(self.display_area)
        except Exception as e:
            messagebox.showerror("خطأ", str(e))

    def open_accounts(self):
        self.clear_display_area()
        try:
            # نقوم بتمرير منطقة العرض لكي تظهر الشجرة بداخلها
            self.current_page = ChartOfAccountsScreen(self.display_area)
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تحميل دليل الحسابات: {e}")

    def open_manual_journal(self):
        messagebox.showinfo("القيود", "قيد البرمجة...")

    def open_reports(self):
        messagebox.showinfo("التقارير", "قيد البرمجة...")

    def dummy_msg(self):
        messagebox.showinfo("الإعدادات", "خاص بالمدير")


if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = RealEstateApp(root)
    root.mainloop()