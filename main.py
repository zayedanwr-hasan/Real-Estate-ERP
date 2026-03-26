import importlib
import ttkbootstrap as tb
from tkinter import ttk, messagebox

from properties_screen import PropertyScreen
from payment_vouchers import PaymentVoucherScreen
from receipt_vouchers import ReceiptVoucherScreen
from chart_of_accounts import ChartOfAccountsScreen
from sub_coding_opening_balances import SubCodingOpeningBalances
from adjustment_journal import AdjustmentJournalEntryScreen
from reports_screen import ReportsScreen


class RealEstateApp:
    def __init__(self, root: tb.Window):
        self.root = root
        self.root.title("نظام محاسبي للمقاولات والعقارات - v2.0")
        self.root.geometry("1200x800")

        self.current_user = None

        # =========================
        # لوحة الألوان
        # =========================
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#2c3e50"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.separator_color = "#2c3e50"
        self.bg_color = "#f4f7f6"

        self._active_sidebar_button = None
        self._reports_root_expanded = False
        self._expanded_report_section = None
        self._report_section_widgets = {}

        self.report_sections = {
            "تقارير الورثة": ["كشف حساب وارث", "ملخص وارث", "أرصدة الورثة"],
            "تقارير العقارات": ["كشف حساب عقار", "تقرير الإيرادات", "تقرير المصروفات", "صافي الربح"],
            "تقارير السندات": ["سندات الصرف", "سندات القبض", "تقرير يومي"],
            "التقارير المالية": ["دفتر الأستاذ", "ميزان المراجعة", "قائمة الدخل", "التدفقات النقدية"],
            "تقارير متقدمة": ["حسب الحساب", "حسب الوارث", "حسب العقار", "مقارنة فترات"],
        }

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

        if not self._show_login_dialog():
            self.root.destroy()
            return

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
        s.configure(
            "App.SidebarSection.TButton",
            background=self.sidebar_color,
            foreground="#d9e2ec",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
            padding=(10, 7),
            anchor="e",
        )
        s.configure(
            "App.SidebarSub.TButton",
            background=self.sidebar_color,
            foreground="#c7d2de",
            borderwidth=0,
            font=("Segoe UI", 10),
            padding=(16, 6),
            anchor="e",
        )
        s.configure(
            "App.SidebarActive.TButton",
            background=self.accent_color,
            foreground="white",
            borderwidth=0,
            font=("Segoe UI", 11, "bold"),
            padding=(10, 8),
            anchor="e",
        )

        s.map(
            "App.Sidebar.TButton",
            background=[("active", "#34495E")],
            foreground=[("active", "white")]
        )
        s.map(
            "App.SidebarSection.TButton",
            background=[("active", "#34495E")],
            foreground=[("active", "white")]
        )
        s.map(
            "App.SidebarSub.TButton",
            background=[("active", "#34495E")],
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

    def _set_active_sidebar_button(self, button):
        if self._active_sidebar_button and self._active_sidebar_button.winfo_exists():
            prev_style = getattr(self._active_sidebar_button, "_default_style", "App.Sidebar.TButton")
            self._active_sidebar_button.configure(style=prev_style)

        default_style = getattr(button, "_default_style", "App.Sidebar.TButton")
        button._default_style = default_style
        button.configure(style="App.SidebarActive.TButton")
        self._active_sidebar_button = button

    def _create_nav_button(self, parent, text, command, style_name="App.Sidebar.TButton", padx=10, pady=4):
        row = tb.Frame(parent, style="App.Sidebar.TFrame")
        row.pack(fill="x", padx=padx, pady=pady)

        btn = ttk.Button(row, text=text, style=style_name, cursor="hand2")
        btn._default_style = style_name
        btn.configure(command=lambda b=btn, c=command: (self._set_active_sidebar_button(b), c()))
        btn.pack(fill="x")
        return btn

    def _build_reports_accordion(self, parent):
        reports_wrap = tb.Frame(parent, style="App.Sidebar.TFrame")
        reports_wrap.pack(fill="x", padx=10, pady=6)

        self.btn_reports_root = ttk.Button(
            reports_wrap,
            text="▶ 📊 التقارير",
            style="App.Sidebar.TButton",
            cursor="hand2",
            command=self._toggle_reports_root,
        )
        self.btn_reports_root._default_style = "App.Sidebar.TButton"
        self.btn_reports_root.pack(fill="x")

        # Keep submenu attached directly below the reports root item.
        self.reports_container = tb.Frame(reports_wrap, style="App.Sidebar.TFrame")

        for section_name, reports in self.report_sections.items():
            # Wrap each section in its own container so children stay under their parent.
            section_wrap = tb.Frame(self.reports_container, style="App.Sidebar.TFrame")
            section_wrap.pack(fill="x", padx=14, pady=(2, 1))

            section_btn_row = tb.Frame(section_wrap, style="App.Sidebar.TFrame")
            section_btn_row.pack(fill="x")

            section_btn = ttk.Button(
                section_btn_row,
                text=f"▶ {section_name}",
                style="App.SidebarSection.TButton",
                cursor="hand2",
                command=lambda n=section_name: self._toggle_report_section(n),
            )
            section_btn.pack(fill="x")

            # Important: children frame is now inside section_wrap (not global container).
            items_frame = tb.Frame(section_wrap, style="App.Sidebar.TFrame")

            for report_name in reports:
                report_row = tb.Frame(items_frame, style="App.Sidebar.TFrame")
                report_row.pack(fill="x", padx=10, pady=1)

                report_btn = ttk.Button(
                    report_row,
                    text=f"- {report_name}",
                    style="App.SidebarSub.TButton",
                    cursor="hand2",
                )
                report_btn._default_style = "App.SidebarSub.TButton"
                report_btn.configure(command=lambda rn=report_name, b=report_btn: (self._set_active_sidebar_button(b), self.open_report(rn)))
                report_btn.pack(fill="x")

            self._report_section_widgets[section_name] = {
                "button": section_btn,
                "items": items_frame,
            }

    def _toggle_reports_root(self, force_expand=False):
        if force_expand:
            self._reports_root_expanded = False

        if self._reports_root_expanded:
            self.reports_container.pack_forget()
            self.btn_reports_root.configure(text="▶ 📊 التقارير")
            self._reports_root_expanded = False
            self._collapse_all_report_sections()
            return

        self.reports_container.pack(fill="x", pady=(2, 0))
        self.btn_reports_root.configure(text="▼ 📊 التقارير")
        self._reports_root_expanded = True

    def _collapse_all_report_sections(self):
        for name, widgets in self._report_section_widgets.items():
            widgets["items"].pack_forget()
            widgets["button"].configure(text=f"▶ {name}")
        self._expanded_report_section = None

    def _toggle_report_section(self, section_name):
        if not self._reports_root_expanded:
            self._toggle_reports_root(force_expand=True)

        if self._expanded_report_section == section_name:
            widgets = self._report_section_widgets[section_name]
            widgets["items"].pack_forget()
            widgets["button"].configure(text=f"▶ {section_name}")
            self._expanded_report_section = None
            return

        self._collapse_all_report_sections()
        widgets = self._report_section_widgets[section_name]
        widgets["items"].pack(fill="x", padx=14, pady=(0, 4))
        widgets["button"].configure(text=f"▼ {section_name}")
        self._expanded_report_section = section_name

    def create_menu(self):
        self._create_nav_button(self.sidebar, "🏢 إدارة العقارات", self.open_properties)
        ttk.Separator(self.sidebar).pack(fill="x", padx=20, pady=3)

        self._create_nav_button(self.sidebar, "📁 دليل الحسابات", self.open_accounts)
        ttk.Separator(self.sidebar).pack(fill="x", padx=20, pady=3)

        self._create_nav_button(self.sidebar, "🔗 الترميز الفرعي", self.open_sub_coding)
        ttk.Separator(self.sidebar).pack(fill="x", padx=20, pady=3)

        self._create_nav_button(self.sidebar, "📤 سند صرف نقدي", self.open_payment_voucher)
        ttk.Separator(self.sidebar).pack(fill="x", padx=20, pady=3)

        self._create_nav_button(self.sidebar, "📥 سند قبض نقدي", self.open_receipt_voucher)
        ttk.Separator(self.sidebar).pack(fill="x", padx=20, pady=3)

        self._create_nav_button(self.sidebar, "🧾 قيد تسوية", self.open_adjustment_journal)
        ttk.Separator(self.sidebar).pack(fill="x", padx=20, pady=3)

        self._build_reports_accordion(self.sidebar)
        self._toggle_reports_root(force_expand=True)
        ttk.Separator(self.sidebar).pack(fill="x", padx=20, pady=3)

        self._create_nav_button(self.sidebar, "⚙️ الإعدادات", self.open_settings)
        ttk.Separator(self.sidebar).pack(fill="x", padx=20, pady=3)

        self._create_nav_button(self.sidebar, "🚪 خروج", self.root.quit)

    def _show_login_dialog(self):
        # Legacy hook kept to avoid breaking startup flow when auth is disabled.
        return True

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
        self.clear_display_area()
        self.current_page = ReportsScreen(self.display_area)

    def open_settings(self):
        self.clear_display_area()
        try:
            settings_module = importlib.import_module("settings_screen")
            settings_cls = getattr(settings_module, "SettingsScreen")
        except Exception:
            messagebox.showinfo("تنبيه", "شاشة الإعدادات غير متوفرة حالياً")
            return
        self.current_page = settings_cls(self.display_area, current_user=self.current_user)

    def open_report(self, report_name):
        self.clear_display_area()
        self.current_page = ReportsScreen(self.display_area)
        self.current_page.open_report(report_name)


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