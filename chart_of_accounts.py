import tkinter as tk
from tkinter import ttk, messagebox
# تأكد من وجود ملف db_connection.py في نفس مسار المشروع
from db_connection import get_connection


class ChartOfAccountsScreen:
    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.bg_color = "#f0f2f5"
        self.account_rows = {}

        self.frame = tk.Frame(master, bg=self.bg_color)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.main_card = tk.Frame(self.frame, bg="white", highlightthickness=1, highlightbackground="#d1d8e0")
        self.main_card.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=1100, height=800)

        self._setup_tree_style()
        self._build_header_buttons()
        self._build_tree_and_form()
        self._load_accounts_from_db()

    def _setup_tree_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", rowheight=35, font=("Segoe UI", 11), background="white", fieldbackground="white",
                        indent=35)
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background="#ecf0f1",
                        foreground=self.primary_color)
        style.map("Treeview", background=[('selected', self.accent_color)], foreground=[('selected', 'white')])

    def _build_header_buttons(self):
        header = tk.Frame(self.main_card, bg=self.primary_color, height=65)
        header.pack(fill="x", side="top")

        tk.Label(header, text="دليل الحسابات العقاري - Al-Sofi ERP", fg="white",
                 bg=self.primary_color, font=("Segoe UI", 18, "bold")).pack(side="right", padx=30, pady=15)

        btn_group = tk.Frame(header, bg=self.primary_color)
        btn_group.pack(side="left", padx=20)

        btn_data = [
            ("خروج🚪", "#e74c3c", self._exit_app),
            ("حذف🗑️", "#e67e22", self._delete_account),
            ("تعديل✏️", "#f1c40f", self._edit_account),
            ("حفظ💾", "#2ecc71", self._save_account),
            ("بحث🔍", "#9b59b6", self._search_account),
            ("جديد ✨", "#3498db", self._clear_form)
        ]

        for txt, clr, cmd in btn_data:
            tk.Button(btn_group, text=txt, bg=clr, fg="white", font=("Segoe UI", 10, "bold"),
                      width=9, bd=0, cursor="hand2", pady=7, command=cmd).pack(side="left", padx=5)

    def _build_tree_and_form(self):
        content = tk.Frame(self.main_card, bg="white")
        content.pack(fill="both", expand=True, padx=30, pady=20)

        self.form_container = tk.LabelFrame(content, text=" تفاصيل بطاقة الحساب ", bg="white",
                                            font=("Segoe UI", 12, "bold"), fg=self.primary_color,
                                            padx=20, pady=20, width=420)
        self.form_container.pack_propagate(False)
        self.form_container.pack(side="right", fill="y")

        self.entries = {}
        self.entries['account_code'] = self._create_styled_field(self.form_container, "رقم الحساب :")
        self.entries['account_name'] = self._create_styled_field(self.form_container, "اسم الحساب :")
        self.entries['parent_code'] = self._create_styled_field(self.form_container, "حساب الأب :")

        self.combo_type = self._create_styled_field(self.form_container, "نوع الحساب :", widget_type="combo",
                                                    values=["رئيسي", "فرعي", "تحليلي"], state="readonly")
        self.combo_nature = self._create_styled_field(self.form_container, "طبيعة الحساب :", widget_type="combo",
                                                      values=["مدين", "دائن"], state="readonly")

        tk.Frame(self.form_container, bg="#d1d8e0", height=1).pack(fill="x", pady=20)
        tk.Label(self.form_container, text="الرصيد الحالي", font=("Segoe UI", 12), bg="white", fg="#7f8c8d").pack()
        self.lbl_balance = tk.Label(self.form_container, text="0.00 ر.ي", font=("Segoe UI", 22, "bold"),
                                    bg="white", fg="#c0392b")
        self.lbl_balance.pack()

        tree_frame = tk.Frame(content, bg="white")
        tree_frame.pack(side="left", fill="both", expand=True, padx=(0, 15))

        tk.Label(tree_frame, text="📁 الهيكل التنظيمي للحسابات", font=("Segoe UI", 12, "bold"), bg="white",
                 fg=self.primary_color).pack(anchor="e", pady=(0, 5))

        self.tree = ttk.Treeview(tree_frame, columns=("code", "type", "nature", "level"), show="tree headings")
        self.tree.heading("#0", text="اسم الحساب", anchor="e")
        self.tree.heading("code", text="الكود", anchor="center")
        self.tree.heading("type", text="النوع", anchor="center")
        self.tree.heading("nature", text="الطبيعة", anchor="center")
        self.tree.heading("level", text="المستوى", anchor="center")

        self.tree.column("#0", width=250, anchor="e")
        self.tree.column("code", width=80, anchor="center")
        self.tree.column("type", width=80, anchor="center")
        self.tree.column("nature", width=80, anchor="center")
        self.tree.column("level", width=50, anchor="center")

        self.tree.pack(fill="both", expand=True)
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
            for acc in sorted(self.account_rows.values(), key=lambda x: x["account_code"]):
                p_code = acc["parent_code"]
                a_type = acc["account_type"]

                if a_type == "رئيسي":
                    icon, tag = "📁 ", "main_red"
                elif a_type == "فرعي":
                    icon, tag = "📂 ", "sub_blue"
                else:
                    icon, tag = "📄 ", "detail_black"

                parent_node = p_code if p_code in node_map else ""

                node_id = self.tree.insert(parent_node, "end", iid=acc["account_code"],
                                           text=f"{icon}{acc['account_name']}",
                                           values=(acc["account_code"], a_type, acc["nature"], acc["account_level"]),
                                           tags=(tag,))
                node_map[acc["account_code"]] = node_id

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
        container = tk.Frame(parent, bg="white")
        container.pack(fill="x", pady=8)
        if widget_type == "entry":
            field = tk.Entry(container, font=("Segoe UI", 14, "bold"), bd=2, relief="groove", justify="right", **kwargs)
        else:
            field = ttk.Combobox(container, font=("Segoe UI", 13, "bold"), justify="right", **kwargs)
        field.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(container, text=label_text, bg=self.sidebar_color, fg="white", font=("Segoe UI", 11, "bold"), width=18,
                 anchor="center", pady=6).pack(side="right")
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
        if reset_focus: self.entries['account_code'].focus_set()

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
    root = tk.Tk()
    root.title("Al-Sofi Real Estate ERP")
    root.geometry("1200x900")
    app = ChartOfAccountsScreen(root)
    root.mainloop()