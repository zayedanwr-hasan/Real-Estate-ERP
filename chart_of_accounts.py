import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
# تأكد من وجود ملف db_connection.py في نفس مسار المشروع
from db_connection import get_connection
from combobox_helper import bind_searchable_combobox, set_combobox_values


class ChartOfAccountsScreen:
    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.separator_color = "#2c3e50"
        self.bg_color = "#f4f7f6"
        self.account_rows = {}

        self.frame = ttk.Frame(master, style="App.Accounts.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.main_card = ttk.Frame(self.frame, style="App.Accounts.Card.TFrame", padding=0)
        self.main_card.pack(fill="both", expand=True, padx=14, pady=14)

        self._setup_tree_style()
        self._build_header_buttons()
        self._build_tree_and_form()
        self._load_accounts_from_db()

    def _setup_tree_style(self):
        style = ttk.Style()
        style.configure("App.Accounts.Root.TFrame", background=self.bg_color)
        style.configure("App.Accounts.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("App.Accounts.Header.TFrame", background=self.primary_color)
        style.configure("App.Accounts.HeaderTitle.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 18, "bold"))
        style.configure("App.Accounts.Content.TFrame", background="white")
        style.configure("App.Accounts.Form.TLabelframe", background="white", bordercolor="#d8e1e8", borderwidth=1, relief="solid")
        style.configure("App.Accounts.Form.TLabelframe.Label", background="white", foreground=self.primary_color, font=("Segoe UI", 13, "bold"))
        style.configure("App.Accounts.Value.TLabel", background="white", foreground=self.sidebar_color, font=("Segoe UI", 13, "bold"))
        style.configure("App.Accounts.Balance.TLabel", background="white", foreground="#c0392b", font=("Segoe UI", 24, "bold"))
        style.configure("App.Accounts.FieldLabel.TLabel", background=self.sidebar_color, foreground=self.text_color, font=("Segoe UI", 12, "bold"), anchor="center", padding=8)
        style.configure("App.Accounts.Field.TEntry", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 14, "bold"))
        style.configure("App.Accounts.Field.TCombobox", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 13, "bold"))
        style.configure("App.Accounts.TreeTitle.TLabel", background="white", foreground=self.primary_color, font=("Segoe UI", 13, "bold"))
        style.configure("App.Accounts.Primary.TButton", background="#2980b9", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Accounts.Success.TButton", background="#27ae60", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Accounts.Warning.TButton", background="#f1c40f", foreground="#2c3e50", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Accounts.Danger.TButton", background="#e74c3c", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Accounts.Info.TButton", background="#8e44ad", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Accounts.Exit.TButton", background="#e67e22", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))

        for btn_style in (
            "App.Accounts.Primary.TButton",
            "App.Accounts.Success.TButton",
            "App.Accounts.Warning.TButton",
            "App.Accounts.Danger.TButton",
            "App.Accounts.Info.TButton",
            "App.Accounts.Exit.TButton",
        ):
            style.map(
                btn_style,
                background=[("active", self.accent_color), ("pressed", self.accent_color)],
                foreground=[("active", "white"), ("pressed", "white")],
            )

        style.configure("App.Accounts.Treeview", rowheight=30, font=("Segoe UI", 10), background="white", fieldbackground="white", foreground=self.primary_color, indent=28)
        style.configure("App.Accounts.Treeview.Heading", font=("Segoe UI", 11, "bold"), background=self.primary_color, foreground="white")
        style.map("App.Accounts.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "white")])
        style.map("App.Accounts.Treeview.Heading", background=[("active", self.primary_color), ("pressed", self.primary_color)], foreground=[("active", "white"), ("pressed", "white")])
        style.configure("App.Accounts.Horizontal.TSeparator", background=self.separator_color)
        style.configure(
            "App.Accounts.Vertical.TScrollbar",
            background=self.sidebar_color,
            troughcolor=self.bg_color,
            arrowcolor=self.primary_color,
        )
        style.configure(
            "App.Accounts.Horizontal.TScrollbar",
            background=self.sidebar_color,
            troughcolor=self.bg_color,
            arrowcolor=self.primary_color,
        )

    def _build_header_buttons(self):
        header = ttk.Frame(self.main_card, style="App.Accounts.Header.TFrame", height=68)
        header.pack(fill="x", side="top")

        ttk.Label(header, text="دليل الحسابات العقاري - Al-Sofi ERP", style="App.Accounts.HeaderTitle.TLabel").pack(
            side="right", padx=30, pady=15
        )

        btn_group = ttk.Frame(header, style="App.Accounts.Header.TFrame")
        btn_group.pack(side="left", padx=20)

        btn_data = [
            ("جديد", "App.Accounts.Primary.TButton", self._clear_form),
            ("حفظ", "App.Accounts.Success.TButton", self._save_account),
            ("تعديل", "App.Accounts.Warning.TButton", self._edit_account),
            ("حذف", "App.Accounts.Danger.TButton", self._delete_account),
            ("بحث", "App.Accounts.Info.TButton", self._search_account),
            ("خروج", "App.Accounts.Exit.TButton", self._exit_app),
        ]

        for txt, style_name, cmd in btn_data:
            ttk.Button(btn_group, text=txt, style=style_name, width=9, command=cmd).pack(side="left", padx=5)

    def _build_tree_and_form(self):
        content = ttk.Frame(self.main_card, style="App.Accounts.Content.TFrame", padding=(24, 18))
        content.pack(fill="both", expand=True)

        self.form_container = ttk.Labelframe(content, text=" تفاصيل بطاقة الحساب ", style="App.Accounts.Form.TLabelframe", padding=18, width=430)
        self.form_container.pack_propagate(False)
        self.form_container.pack(side="right", fill="y")

        self.entries = {}
        self.entries['account_code'] = self._create_styled_field(self.form_container, "رقم الحساب :")
        self.entries['account_name'] = self._create_styled_field(self.form_container, "اسم الحساب :")
        self.entries['parent_code'] = self._create_styled_field(self.form_container, "حساب الأب :")

        self.combo_type = self._create_styled_field(
            self.form_container,
            "نوع الحساب :",
            widget_type="combo",
            state="readonly",
        )
        self.combo_nature = self._create_styled_field(
            self.form_container,
            "طبيعة الحساب :",
            widget_type="combo",
            state="readonly",
        )
        set_combobox_values(self.combo_type, ["رئيسي", "فرعي", "تحليلي"])
        set_combobox_values(self.combo_nature, ["مدين", "دائن"])
        bind_searchable_combobox(self.combo_type)
        bind_searchable_combobox(self.combo_nature)

        ttk.Separator(self.form_container, orient="horizontal", style="App.Accounts.Horizontal.TSeparator").pack(fill="x", pady=20)
        ttk.Label(self.form_container, text="الرصيد الحالي", style="App.Accounts.Value.TLabel").pack()
        self.lbl_balance = ttk.Label(self.form_container, text="0.00 ر.ي", style="App.Accounts.Balance.TLabel")
        self.lbl_balance.pack()

        tree_frame = ttk.Frame(content, style="App.Accounts.Content.TFrame")
        tree_frame.pack(side="left", fill="both", expand=True, padx=(0, 15))

        ttk.Label(tree_frame, text="الهيكل التنظيمي للحسابات", style="App.Accounts.TreeTitle.TLabel", anchor="e").pack(anchor="e", pady=(0, 8))

        tree_container = ttk.Frame(tree_frame, style="App.Accounts.Content.TFrame")
        tree_container.pack(fill="both", expand=True)
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_container, columns=("code", "type", "nature", "level"), show="tree headings", style="App.Accounts.Treeview")
        self.tree.heading("#0", text="اسم الحساب", anchor="e")
        self.tree.heading("code", text="الكود", anchor="center")
        self.tree.heading("type", text="النوع", anchor="center")
        self.tree.heading("nature", text="الطبيعة", anchor="center")
        self.tree.heading("level", text="المستوى", anchor="center")

        self.tree.column("#0", width=280, anchor="e")
        self.tree.column("code", width=95, anchor="center")
        self.tree.column("type", width=95, anchor="center")
        self.tree.column("nature", width=95, anchor="center")
        self.tree.column("level", width=70, anchor="center")

        y_scroll = ttk.Scrollbar(tree_container, orient="vertical", style="App.Accounts.Vertical.TScrollbar", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(tree_container, orient="horizontal", style="App.Accounts.Horizontal.TScrollbar", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        self.tree.tag_configure("odd", background="#ffffff")
        self.tree.tag_configure("even", background="#f0f3f5")

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _load_accounts_from_db(self):
        self.tree.delete(*self.tree.get_children())
        self.account_rows.clear()
        conn = get_connection()
        if not conn: return

        try:
            cur = conn.cursor()
            query = "SELECT account_code, account_name, parent_code, account_type, nature, account_level FROM finance.accounts ORDER BY account_code ASC"
            cur.execute(query)
            rows = cur.fetchall()

            for code, name, p_code, a_type, nature, level in rows:
                self.account_rows[str(code)] = {
                    "account_code": str(code), "account_name": name or "",
                    "parent_code": "" if p_code in (None, "", "0", 0) else str(p_code),
                    "account_type": a_type or "", "nature": nature or "", "account_level": level or 1
                }

            node_map = {}
            row_idx = 0
            for acc in sorted(self.account_rows.values(), key=lambda x: x["account_code"]):
                p_code = acc["parent_code"]
                a_type = acc["account_type"]

                if a_type == "رئيسي":
                    icon, type_tag = "📁 ", "main_red"
                elif a_type == "فرعي":
                    icon, type_tag = "📂 ", "sub_blue"
                else:
                    icon, type_tag = "📄 ", "detail_black"

                parent_node = p_code if p_code in node_map else ""
                stripe_tag = "even" if row_idx % 2 == 0 else "odd"
                node_id = self.tree.insert(
                    parent_node,
                    "end",
                    iid=acc["account_code"],
                    text=f"{icon}{acc['account_name']}",
                    values=(acc["account_code"], a_type, acc["nature"], acc["account_level"]),
                    tags=(stripe_tag, type_tag),
                )
                node_map[acc["account_code"]] = node_id
                row_idx += 1

                if a_type in ["رئيسي", "فرعي"]:
                    self.tree.item(node_id, open=True)

            self.tree.tag_configure("main_red", font=("Segoe UI", 11, "bold"), foreground="#c0392b")
            self.tree.tag_configure("sub_blue", font=("Segoe UI", 11, "bold"), foreground="#2980b9")
            self.tree.tag_configure("detail_black", font=("Segoe UI", 11), foreground="#2c3e50")

        except Exception as e:
            messagebox.showerror("خطأ", f"فشل تحميل البيانات: {e}")
        finally:
            conn.close()

    def _get_level_from_parent(self, parent_code):
        if not parent_code: return 1
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT account_level FROM finance.accounts WHERE TRIM(account_code) = TRIM(%s)",
                        (parent_code,))
            res = cur.fetchone()
            return (res[0] + 1) if res else 1
        finally:
            conn.close()

    def _save_account(self):
        data = self._normalize_form_data()
        if not self._validate_required(data): return
        level = self._get_level_from_parent(data["parent_code"])
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                        INSERT INTO finance.accounts (account_code, account_name, parent_code, account_type, nature,
                                                      account_level)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """, (data["account_code"], data["account_name"], data["parent_code"] or None,
                              data["account_type"], data["nature"], level))
            conn.commit()
            self._load_accounts_from_db()
            messagebox.showinfo("نجاح", "تم حفظ الحساب بنجاح.")
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر الحفظ: {e}")
        finally:
            conn.close()

    def _edit_account(self):
        data = self._normalize_form_data()
        if not self._validate_required(data): return

        level = self._get_level_from_parent(data["parent_code"])
        conn = get_connection()
        try:
            cur = conn.cursor()
            # استخدام TRIM لضمان مطابقة الكود حتى لو كان به مسافات مخفية
            cur.execute("""
                        UPDATE finance.accounts
                        SET account_name  = %s,
                            parent_code   = %s,
                            account_type  = %s,
                            nature        = %s,
                            account_level = %s
                        WHERE TRIM(account_code) = TRIM(%s)
                        """, (data["account_name"], data["parent_code"] or None,
                              data["account_type"], data["nature"], level, data["account_code"]))

            if cur.rowcount == 0:
                messagebox.showwarning("تنبيه", "لم يتم العثور على السجل لتعديله.")
            else:
                conn.commit()
                self._load_accounts_from_db()
                messagebox.showinfo("نجاح", "تم التحديث بنجاح.")
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("خطأ", f"فشل التعديل: {e}")
        finally:
            if conn: conn.close()

    def _delete_account(self):
        code = self.entries['account_code'].get().strip()
        if not code: return
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف الحساب؟"): return
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM finance.accounts WHERE TRIM(account_code) = TRIM(%s)", (code,))
            conn.commit()
            self._load_accounts_from_db()
            self._clear_form()
            messagebox.showinfo("نجاح", "تم حذف الحساب.")
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر الحذف: {e}")
        finally:
            conn.close()

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        code = selected[0]
        data = self.account_rows.get(code)
        if not data: return

        self._clear_form(reset_focus=False)

        # وضع الكود وجعله للقراءة فقط لضمان دقة التعديل
        self.entries['account_code'].config(state='normal')
        self.entries['account_code'].insert(0, data["account_code"])
        self.entries['account_code'].config(state='readonly')

        self.entries['account_name'].insert(0, data["account_name"])
        self.entries['parent_code'].insert(0, data["parent_code"])
        self.combo_type.set(data["account_type"])
        self.combo_nature.set(data["nature"])

    def _create_styled_field(self, parent, label_text, widget_type="entry", **kwargs):
        container = ttk.Frame(parent, style="App.Accounts.Content.TFrame")
        container.pack(fill="x", pady=10)
        if widget_type == "entry":
            field = ttk.Entry(container, style="App.Accounts.Field.TEntry", justify="right", **kwargs)
        else:
            field = ttk.Combobox(container, style="App.Accounts.Field.TCombobox", justify="right", **kwargs)
        field.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Label(container, text=label_text, style="App.Accounts.FieldLabel.TLabel", width=18).pack(side="right")
        return field

    def _normalize_form_data(self):
        # قراءة البيانات حتى لو كان الحقل Readonly
        return {
            "account_code": self.entries['account_code'].get().strip(),
            "account_name": self.entries['account_name'].get().strip(),
            "parent_code": self.entries['parent_code'].get().strip(),
            "account_type": self.combo_type.get(),
            "nature": self.combo_nature.get()
        }

    def _validate_required(self, data):
        if not data["account_code"] or not data["account_name"]:
            messagebox.showwarning("تنبيه", "أدخل رقم واسم الحساب.")
            return False
        return True

    def _clear_form(self, reset_focus=True):
        for e in self.entries.values():
            e.config(state='normal')
            e.delete(0, tk.END)
        self.combo_type.set('')
        self.combo_nature.set('')
        if reset_focus:
            self.entries['account_code'].focus_set()

    def _search_account(self):
        keyword = self.entries['account_name'].get().strip().lower()
        if not keyword: return
        for item in self.tree.get_children():
            if self._find_recursive(item, keyword): return
        messagebox.showinfo("بحث", "غير موجود.")

    def _find_recursive(self, item, keyword):
        if keyword in self.tree.item(item)['text'].lower():
            self.tree.selection_set(item)
            self.tree.see(item)
            return True
        for child in self.tree.get_children(item):
            if self._find_recursive(child, keyword): return True
        return False

    def _exit_app(self):
        self.master.destroy()


if __name__ == "__main__":
    import ttkbootstrap as tb

    root = tb.Window(themename="flatly")
    root.title("Al-Sofi Real Estate ERP")
    root.geometry("1200x900")
    app = ChartOfAccountsScreen(root)
    root.mainloop()

