import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk

from app_constants import ACCOUNT_LEVELS, SYSTEM_NAME
from combobox_helper import bind_searchable_combobox, set_combobox_values
from db_connection import get_connection, get_db_error_message


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
        self._last_selected_iid = None

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

        # Requested level colors: main red, sub blue, analytical black, assistant coordinated.
        self.type_text_styles = {
            "رئيسي": {"foreground": "#c0392b", "font": ("Segoe UI", 11, "bold")},
            "فرعي": {"foreground": "#2471a3", "font": ("Segoe UI", 11, "bold")},
            "مساعد": {"foreground": "#b9770e", "font": ("Segoe UI", 10, "bold")},
            "تحليلي": {"foreground": "#1f1f1f", "font": ("Segoe UI", 10, "bold")},
        }

        style.configure(
            "App.Accounts.Treeview",
            rowheight=30,
            font=("Segoe UI", 10),
            background="white",
            fieldbackground="white",
            foreground=self.primary_color,
            indent=28,
            borderwidth=0,
        )
        style.configure(
            "App.Accounts.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background=self.primary_color,
            foreground="white",
        )
        style.map(
            "App.Accounts.Treeview",
            background=[("selected", self.accent_color)],
            foreground=[("selected", "white")],
        )
        style.configure("App.Accounts.Horizontal.TSeparator", background=self.separator_color)
        style.configure("App.Accounts.Vertical.TScrollbar", background=self.sidebar_color, troughcolor=self.bg_color, arrowcolor=self.primary_color)
        style.configure("App.Accounts.Horizontal.TScrollbar", background=self.sidebar_color, troughcolor=self.bg_color, arrowcolor=self.primary_color)

    def _build_header_buttons(self):
        header = ttk.Frame(self.main_card, style="App.Accounts.Header.TFrame", height=68)
        header.pack(fill="x", side="top")

        ttk.Label(header, text=f"دليل الحسابات العقاري - {SYSTEM_NAME}", style="App.Accounts.HeaderTitle.TLabel").pack(side="right", padx=30, pady=15)

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
        self.entries["account_code"] = self._create_styled_field(self.form_container, "رقم الحساب :")
        self.entries["account_name"] = self._create_styled_field(self.form_container, "اسم الحساب :")
        self.entries["parent_code"] = self._create_styled_field(self.form_container, "حساب الأب :")

        self.combo_type = self._create_styled_field(self.form_container, "نوع الحساب :", widget_type="combo", state="readonly")
        self.combo_level = self._create_styled_field(self.form_container, "المستوى :", widget_type="combo", state="readonly")
        self.combo_nature = self._create_styled_field(self.form_container, "طبيعة الحساب :", widget_type="combo", state="readonly")

        set_combobox_values(self.combo_type, ["ميزانية", "نتيجة"])
        set_combobox_values(self.combo_level, ACCOUNT_LEVELS)
        set_combobox_values(self.combo_nature, ["مدين", "دائن"])
        bind_searchable_combobox(self.combo_type)
        bind_searchable_combobox(self.combo_level)
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
        self.tree.column("level", width=90, anchor="center")

        y_scroll = ttk.Scrollbar(tree_container, orient="vertical", style="App.Accounts.Vertical.TScrollbar", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(tree_container, orient="horizontal", style="App.Accounts.Horizontal.TScrollbar", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _load_accounts_from_db(self):
        self.tree.delete(*self.tree.get_children())
        self.account_rows.clear()
        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT account_code, account_name, parent_code, account_type, account_level, nature
                        FROM finance.accounts
                        ORDER BY account_code ASC
                        """
                    )
                    rows = cur.fetchall() or []

            for code, name, p_code, a_type, a_level, nature in rows:
                level_text = (a_level or "").strip()
                if level_text not in ACCOUNT_LEVELS:
                    level_text = "تحليلي"

                type_text = (a_type or "").strip()
                if type_text not in ("ميزانية", "نتيجة"):
                    type_text = "ميزانية"

                self.account_rows[str(code)] = {
                    "account_code": str(code),
                    "account_name": name or "",
                    "parent_code": "" if p_code in (None, "", "0", 0) else str(p_code),
                    "account_type": type_text,
                    "nature": nature or "",
                    "account_level": level_text,
                }

            node_map = {}
            row_idx = 0
            for acc in sorted(self.account_rows.values(), key=lambda x: x["account_code"]):
                p_code = acc["parent_code"]
                level = acc["account_level"]

                if level == "رئيسي":
                    icon = "📁 "
                    type_tag = "type_main"
                elif level == "فرعي":
                    icon = "📂 "
                    type_tag = "type_sub"
                elif level == "مساعد":
                    icon = "🧩 "
                    type_tag = "type_assistant"
                else:
                    icon = "📄 "
                    type_tag = "type_analytical"

                parent_node = p_code if p_code in node_map else ""
                stripe_tag = "even" if row_idx % 2 == 0 else "odd"
                node_id = self.tree.insert(
                    parent_node,
                    "end",
                    iid=acc["account_code"],
                    text=f"{icon}{acc['account_name']}",
                    values=(acc["account_code"], acc["account_type"], acc["nature"], acc["account_level"]),
                    tags=(stripe_tag, type_tag),
                )
                node_map[acc["account_code"]] = node_id
                row_idx += 1

                if level in ("رئيسي", "فرعي"):
                    self.tree.item(node_id, open=True)

            self.tree.tag_configure("odd", background="#ffffff")
            self.tree.tag_configure("even", background="#f0f3f5")

            self.tree.tag_configure("type_main", foreground=self.type_text_styles["رئيسي"]["foreground"], font=self.type_text_styles["رئيسي"]["font"])
            self.tree.tag_configure("type_sub", foreground=self.type_text_styles["فرعي"]["foreground"], font=self.type_text_styles["فرعي"]["font"])
            self.tree.tag_configure("type_assistant", foreground=self.type_text_styles["مساعد"]["foreground"], font=self.type_text_styles["مساعد"]["font"])
            self.tree.tag_configure("type_analytical", foreground=self.type_text_styles["تحليلي"]["foreground"], font=self.type_text_styles["تحليلي"]["font"])

        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تحميل دليل الحسابات"))
        finally:
            conn.close()

    def _save_account(self):
        data = self._normalize_form_data()
        if not self._validate_required(data):
            return

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO finance.accounts (account_code, account_name, parent_code, account_type, account_level, nature, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, true)
                        """,
                        (
                            data["account_code"],
                            data["account_name"],
                            data["parent_code"] or None,
                            data["account_type"],
                            data["account_level"],
                            data["nature"],
                        ),
                    )
            self._load_accounts_from_db()
            messagebox.showinfo("نجاح", "تم حفظ الحساب بنجاح")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر حفظ الحساب"))
        finally:
            conn.close()

    def _edit_account(self):
        data = self._normalize_form_data()
        if not self._validate_required(data):
            return

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE finance.accounts
                        SET account_name=%s,
                            parent_code=%s,
                            account_type=%s,
                            account_level=%s,
                            nature=%s
                        WHERE TRIM(account_code) = TRIM(%s)
                        """,
                        (
                            data["account_name"],
                            data["parent_code"] or None,
                            data["account_type"],
                            data["account_level"],
                            data["nature"],
                            data["account_code"],
                        ),
                    )
                    if cur.rowcount == 0:
                        messagebox.showwarning("تنبيه", "لم يتم العثور على السجل لتعديله")
                        return
            self._load_accounts_from_db()
            messagebox.showinfo("نجاح", "تم التحديث بنجاح")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "فشل تعديل الحساب"))
        finally:
            conn.close()

    def _delete_account(self):
        code = self.entries["account_code"].get().strip()
        if not code:
            return
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف الحساب؟"):
            return

        conn = get_connection()
        if not conn:
            return

        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM finance.accounts WHERE TRIM(account_code) = TRIM(%s)", (code,))
            self._load_accounts_from_db()
            self._clear_form()
            messagebox.showinfo("نجاح", "تم حذف الحساب")
        except Exception as exc:
            messagebox.showerror("خطأ", get_db_error_message(exc, "تعذر حذف الحساب"))
        finally:
            conn.close()

    def _on_tree_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return

        code = selected[0]
        data = self.account_rows.get(code)
        if not data:
            return

        self._clear_form(reset_focus=False)
        self.entries["account_code"].config(state="normal")
        self.entries["account_code"].insert(0, data["account_code"])
        self.entries["account_code"].config(state="readonly")

        self.entries["account_name"].insert(0, data["account_name"])
        self.entries["parent_code"].insert(0, data["parent_code"])
        self.combo_type.set(data["account_type"])
        self.combo_level.set(data["account_level"])
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
        return {
            "account_code": self.entries["account_code"].get().strip(),
            "account_name": self.entries["account_name"].get().strip(),
            "parent_code": self.entries["parent_code"].get().strip(),
            "account_type": self.combo_type.get().strip(),
            "account_level": self.combo_level.get().strip(),
            "nature": self.combo_nature.get().strip(),
        }

    def _validate_required(self, data):
        if not data["account_code"] or not data["account_name"]:
            messagebox.showwarning("تنبيه", "أدخل رقم واسم الحساب")
            return False
        if not data["account_type"]:
            messagebox.showwarning("تنبيه", "اختر نوع الحساب")
            return False
        if not data["account_level"]:
            messagebox.showwarning("تنبيه", "اختر مستوى الحساب")
            return False
        return True

    def _clear_form(self, reset_focus=True):
        for e in self.entries.values():
            e.config(state="normal")
            e.delete(0, tk.END)
        self.combo_type.set("")
        self.combo_level.set("")
        self.combo_nature.set("")
        if reset_focus:
            self.entries["account_code"].focus_set()

    def _search_account(self):
        keyword = self.entries["account_name"].get().strip().lower()
        if not keyword:
            return
        for item in self.tree.get_children():
            if self._find_recursive(item, keyword):
                return
        messagebox.showinfo("بحث", "غير موجود")

    def _find_recursive(self, item, keyword):
        if keyword in self.tree.item(item)["text"].lower():
            self.tree.selection_set(item)
            self.tree.see(item)
            return True
        for child in self.tree.get_children(item):
            if self._find_recursive(child, keyword):
                return True
        return False

    def _exit_app(self):
        self.master.destroy()

    def expand_all(self, tree):
        def _expand(node):
            children = tree.get_children(node)
            if not children:
                return
            tree.item(node, open=True)
            for child in children:
                _expand(child)

        for root in tree.get_children(""):
            _expand(root)

    def collapse_all(self, tree):
        def _collapse(node):
            for child in tree.get_children(node):
                _collapse(child)
            tree.item(node, open=False)

        for root in tree.get_children(""):
            _collapse(root)

    def toggle_item(self, event):
        # Keep default arrow behavior intact.
        if "indicator" in self.tree.identify_element(event.x, event.y):
            return

        iid = self.tree.identify_row(event.y)
        if not iid:
            return

        if self.tree.get_children(iid):
            is_open = bool(self.tree.item(iid, "open"))
            self.tree.item(iid, open=not is_open)

    def _on_tree_hover(self, event):
        iid = self.tree.identify_row(event.y)
        self.tree.configure(cursor="hand2" if iid else "")

    def _on_tree_open(self, _event=None):
        iid = self.tree.focus()
        if not iid:
            return
        data = self.account_rows.get(iid)
        if not data:
            return
        if data.get("account_type") in ("رئيسي", "فرعي"):
            self.tree.item(iid, text=f"📂 {data.get('account_name', '')}")

    def _on_tree_close(self, _event=None):
        iid = self.tree.focus()
        if not iid:
            return
        data = self.account_rows.get(iid)
        if not data:
            return
        if data.get("account_type") in ("رئيسي", "فرعي"):
            self.tree.item(iid, text=f"📁 {data.get('account_name', '')}")


if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    root.title(SYSTEM_NAME)
    root.geometry("1200x900")
    app = ChartOfAccountsScreen(root)
    root.mainloop()

