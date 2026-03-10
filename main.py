import tkinter as tk
from tkinter import messagebox, ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from properties_screen import PropertyScreen
from payment_vouchers import PaymentVoucherScreen
from receipt_vouchers import ReceiptVoucherScreen
from chart_of_accounts import ChartOfAccountsScreen
from sub_coding_opening_balances import SubCodingOpeningBalances  # <--- إضافة هذا السطر

class RealEstateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("نظام محاسبي للمقاولات والعقارات - v2.0")
        self.root.geometry("1200x800")

        # --- لوحة الألوان الجديدة ---
        self.primary_color = "#2c3e50"  # الكحلي الغامق (Header)
        self.sidebar_color = "#34495e"  # الكحلي المتوسط (Sidebar)
        self.accent_color = "#1abc9c"  # التيركواز (Hover & Icons)
        self.text_color = "#ecf0f1"  # الأبيض الكريمي (للنصوص - واضح جداً)
        self.separator_color = "#2c3e50"  # لون الخط الفاصل
        self.bg_color = "#f4f7f6"  # خلفية النظام العامة

        self._setup_styles()
        self.root.configure(bg=self.bg_color)

        # 1. الترويسة العلوية
        self.header = ttk.Frame(self.root, style="App.Header.TFrame", height=70)
        self.header.pack(fill="x", side="top")

        ttk.Label(
            self.header,
            text="نظام الإدارة العقارية والمحاسبية المتكامل",
            style="App.Header.TLabel",
            anchor="center",
        ).pack(pady=15)

        # 2. السايد بار
        self.sidebar = ttk.Frame(self.root, style="App.Sidebar.TFrame", width=260)
        self.sidebar.pack(side="right", fill="y")

        ttk.Label(
            self.sidebar,
            text="القائمة الرئيسية",
            style="App.SidebarTitle.TLabel",
            anchor="center",
        ).pack(pady=(30, 10))

        self.create_menu()

        # 3. منطقة العرض
        self.display_area = ttk.Frame(self.root, style="App.Root.TFrame")
        self.display_area.pack(side="left", fill="both", expand=True)

        self.show_welcome_screen()

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("App.Root.TFrame", background=self.bg_color)
        style.configure("App.Header.TFrame", background=self.primary_color)
        style.configure("App.Sidebar.TFrame", background=self.sidebar_color)
        style.configure(
            "App.Header.TLabel",
            background=self.primary_color,
            foreground="white",
            font=("Segoe UI", 20, "bold"),
        )
        style.configure(
            "App.SidebarTitle.TLabel",
            background=self.sidebar_color,
            foreground="#bdc3c7",
            font=("Segoe UI", 12, "bold"),
        )
        style.configure(
            "App.Sidebar.TButton",
            background=self.sidebar_color,
            foreground=self.text_color,
            borderwidth=0,
            focusthickness=0,
            font=("Segoe UI", 12, "bold"),
            padding=(12, 10),
            anchor="e",
        )
        style.map(
            "App.Sidebar.TButton",
            background=[("active", self.accent_color), ("pressed", self.accent_color)],
            foreground=[("active", "white"), ("pressed", "white")],
        )
        style.configure("App.WelcomeTitle.TLabel", background=self.bg_color, foreground=self.primary_color, font=("Segoe UI", 26, "bold"))
        style.configure("App.WelcomeSub.TLabel", background=self.bg_color, foreground="#7f8c8d", font=("Segoe UI", 14, "bold"))

    def create_menu(self):
        """إنشاء القائمة مع تنسيق الألوان الجديد والخطوط الفاصلة"""
        menu_items = [
            ("🏢  إدارة العقارات", self.open_properties),
            ("📁  دليل الحسابات", self.open_accounts),
            ("🔗  الترميز الفرعي (الأراضي/الورثة)", self.open_sub_coding),  # <--- إضافة هذا الخيار
            ("📤  سند صرف نقدي", self.open_payment_voucher),
            ("📥  سند قبض نقدي", self.open_receipt_voucher),
            ("📝  قيد يومية يدوي", self.open_manual_journal),
            ("📊  التقارير المالية", self.open_reports),
            ("⚙️  إعدادات النظام", self.dummy_msg),
            ("🚪  إغلاق النظام", self.root.quit),
        ]

        for text, command in menu_items:
            btn_frame = ttk.Frame(self.sidebar, style="App.Sidebar.TFrame")
            btn_frame.pack(fill="x", padx=10, pady=2)

            btn = ttk.Button(
                btn_frame,
                text=text,
                style="App.Sidebar.TButton",
                command=command,
                cursor="hand2",
            )
            btn.pack(fill="x")

            line = ttk.Separator(self.sidebar, orient="horizontal")
            line.pack(fill="x", padx=25, pady=2)

    def clear_display_area(self):
        for widget in self.display_area.winfo_children():
            widget.destroy()

    def show_welcome_screen(self):
        self.clear_display_area()
        welcome_frame = ttk.Frame(self.display_area, style="App.Root.TFrame")
        welcome_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        ttk.Label(welcome_frame, text="مرحباً بك", style="App.WelcomeTitle.TLabel").pack()
        ttk.Label(
            welcome_frame,
            text="الإدارة المالية العقارية أصبحت أسهل",
            style="App.WelcomeSub.TLabel",
        ).pack(pady=10)

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

    def open_sub_coding(self):
        self.clear_display_area()
        try:
            self.current_page = SubCodingOpeningBalances(self.display_area)
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تحميل شاشة الترميز: {e}")

    def open_manual_journal(self):
        messagebox.showinfo("القيود", "قيد البرمجة...")

    def open_reports(self):
        messagebox.showinfo("التقارير", "قيد البرمجة...")

    def dummy_msg(self):
        messagebox.showinfo("الإعدادات", "خاص بالمدير")


if __name__ == "__main__":
    root = tb.Window(themename="flatly")
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = RealEstateApp(root)
    root.mainloop()