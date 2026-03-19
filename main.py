import ttkbootstrap as tb
from tkinter import ttk, messagebox

from properties_screen import PropertyScreen
from payment_vouchers import PaymentVoucherScreen
from receipt_vouchers import ReceiptVoucherScreen
from chart_of_accounts import ChartOfAccountsScreen
from sub_coding_opening_balances import SubCodingOpeningBalances
from adjustment_journal import AdjustmentJournalEntryScreen


class RealEstateApp:
    def __init__(self, root: tb.Window):
        self.root = root
        self.root.title("نظام محاسبي للمقاولات والعقارات - v2.0")
        self.root.geometry("1200x800")

        # =========================
        # لوحة الألوان
        # =========================
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.separator_color = "#2c3e50"
        self.bg_color = "#f4f7f6"

        self.style = tb.Style()
        self._setup_styles()

        self.root.configure(bg=self.bg_color)

        # =========================
        # Header
        # =========================
        self.header = tb.Frame(self.root, style="App.Header.TFrame")
        self.header.pack(fill="x")

        tb.Label(
            self.header,
            text="نظام الإدارة العقارية والمحاسبية المتكامل",
            style="App.Header.TLabel"
        ).pack(pady=12)

        # =========================
        # Sidebar
        # =========================
        self.sidebar = tb.Frame(self.root, style="App.Sidebar.TFrame", width=260)
        self.sidebar.pack(side="right", fill="y")

        tb.Label(
            self.sidebar,
            text="القائمة الرئيسية",
            style="App.SidebarTitle.TLabel"
        ).pack(pady=(30, 12))

        self.create_menu()

        # =========================
        # Display Area
        # =========================
        self.display_area = tb.Frame(self.root, style="App.Root.TFrame")
        self.display_area.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        self.show_welcome_screen()

    def _setup_styles(self):
        s = self.style

        # إجبار الخلفيات
        s.configure(".", background=self.bg_color)
        s.configure("TFrame", background=self.bg_color)
        s.configure("TLabel", background=self.bg_color)

        # Header
        s.configure("App.Header.TFrame", background=self.primary_color)
        s.configure(
            "App.Header.TLabel",
            background=self.primary_color,
            foreground=self.text_color,
            font=("Segoe UI", 18, "bold")
        )

        # Sidebar
        s.configure("App.Sidebar.TFrame", background=self.sidebar_color)
        s.configure(
            "App.SidebarTitle.TLabel",
            background=self.sidebar_color,
            foreground="#bdc3c7",
            font=("Segoe UI", 12, "bold")
        )

        s.configure(
            "App.Sidebar.TButton",
            background=self.sidebar_color,
            foreground=self.text_color,
            borderwidth=0,
            font=("Segoe UI", 11, "bold"),
            padding=(10, 8),
            anchor="e",
        )

        s.map(
            "App.Sidebar.TButton",
            background=[("active", self.accent_color)],
            foreground=[("active", "white")]
        )

        # Root
        s.configure("App.Root.TFrame", background=self.bg_color)

        # Welcome
        s.configure(
            "App.WelcomeTitle.TLabel",
            background=self.bg_color,
            foreground=self.primary_color,
            font=("Segoe UI", 24, "bold")
        )

        s.configure(
            "App.WelcomeSub.TLabel",
            background=self.bg_color,
            foreground="#7f8c8d",
            font=("Segoe UI", 14)
        )

    def create_menu(self):
        menu_items = [
            ("🏢 إدارة العقارات", self.open_properties),
            ("📁 دليل الحسابات", self.open_accounts),
            ("🔗 الترميز الفرعي", self.open_sub_coding),
            ("📤 سند صرف نقدي", self.open_payment_voucher),
            ("📥 سند قبض نقدي", self.open_receipt_voucher),
            ("🧾 قيد تسوية", self.open_adjustment_journal),
            ("📊 التقارير", self.open_reports),
            ("⚙️ الإعدادات", self.dummy_msg),
            ("🚪 خروج", self.root.quit),
        ]

        for text, command in menu_items:
            frame = tb.Frame(self.sidebar, style="App.Sidebar.TFrame")
            frame.pack(fill="x", padx=10, pady=6)

            btn = ttk.Button(
                frame,
                text=text,
                style="App.Sidebar.TButton",  # ✅ موحد
                command=command,
                cursor="hand2"
            )
            btn.pack(fill="x")

            ttk.Separator(self.sidebar).pack(fill="x", padx=20, pady=4)

    def clear_display_area(self):
        for widget in self.display_area.winfo_children():
            widget.destroy()

    def show_welcome_screen(self):
        self.clear_display_area()

        frame = tb.Frame(self.display_area, style="App.Root.TFrame")
        frame.pack(fill="both", expand=True)

        card = tb.Frame(frame, style="App.Root.TFrame", padding=20)
        card.place(relx=0.5, rely=0.4, anchor="center", width=800, height=300)

        tb.Label(card, text="مرحباً بك", style="App.WelcomeTitle.TLabel").pack(pady=10)
        tb.Label(
            card,
            text="الإدارة المالية العقارية أصبحت أسهل",
            style="App.WelcomeSub.TLabel"
        ).pack()

    # =========================
    # Navigation
    # =========================
    def open_properties(self):
        self.clear_display_area()
        self.current_page = PropertyScreen(self.display_area)

    def open_payment_voucher(self):
        self.clear_display_area()
        self.current_page = PaymentVoucherScreen(self.display_area)

    def open_receipt_voucher(self):
        self.clear_display_area()
        self.current_page = ReceiptVoucherScreen(self.display_area)

    def open_accounts(self):
        self.clear_display_area()
        self.current_page = ChartOfAccountsScreen(self.display_area)

    def open_sub_coding(self):
        self.clear_display_area()
        self.current_page = SubCodingOpeningBalances(self.display_area)


    def open_adjustment_journal(self):
        self.clear_display_area()
        self.current_page = AdjustmentJournalEntryScreen(self.display_area)

    def open_reports(self):
        messagebox.showinfo("قريباً", "قيد التطوير")

    def dummy_msg(self):
        messagebox.showinfo("الإعدادات", "خاص بالمدير")


if __name__ == "__main__":
    root = tb.Window(themename="flatly")

    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    app = RealEstateApp(root)
    root.mainloop()