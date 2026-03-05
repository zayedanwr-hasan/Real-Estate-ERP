import tkinter as tk
from tkinter import ttk, messagebox
# تأكد من وجود ملف db_connection.py في نفس مسار المشروع
from db_connection import get_connection


class ChartOfAccountsScreen:
    def __init__(self, master):
        self.master = master
        # الهوية البصرية المعتمدة للنظام
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.bg_color = "#f0f2f5"
        self.account_rows = {}

        self.frame = tk.Frame(master, bg=self.bg_color)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.main_card = tk.Frame(self.frame, bg="white", highlightthickness=1, highlightbackground="#d1d8e0")
        self.main_card.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=1100, height=800)

        # 1. إعداد الستايل الهرمي المتقدم (Classic C# Tree Style)
        self._setup_tree_style()

        self._build_header_buttons()
        self._build_tree_and_form()

        # 2. تحميل البيانات الفعلية وترتيبها هرمياً
        self._load_accounts_from_db()

    def _setup_tree_style(self):
        """إعداد المظهر الهرمي الاحترافي بخطوط واضحة وتوسيع من اليمين"""
        style = ttk.Style()

        # استخدام محرك الرسوم 'clam' يتيح تحكماً أفضل في حجم الخطوط والارتفاعات
        style.theme_use('clam')

        style.configure("Treeview",
                        rowheight=35,
                        font=("Segoe UI", 11),
                        background="white",
                        fieldbackground="white",
                        indent=35)  # زيادة الإزاحة لعمل تسلسل هرمي واضح

        style.configure("Treeview.Heading",
                        font=("Segoe UI", 11, "bold"),
                        background="#ecf0f1",
                        foreground=self.primary_color)

        # لون التحديد عند اختيار حساب
        style.map("Treeview", background=[('selected', self.accent_color)], foreground=[('selected', 'white')])

    def _build_header_buttons(self):
        header = tk.Frame(self.main_card, bg=self.primary_color, height=65)
        header.pack(fill="x", side="top")

        tk.Label(header, text="دليل الحسابات المحاسبي - Al-Sofi ERP", fg="white",
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

        # --- الجانب الأيمن: بطاقة الحساب (Form) ---
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
                                                    values=["رئيسي", "تحليلي"], state="readonly")
        self.combo_nature = self._create_styled_field(self.form_container, "طبيعة الحساب :", widget_type="combo",
                                                      values=["مدين", "دائن"], state="readonly")

        tk.Frame(self.form_container, bg="#d1d8e0", height=1).pack(fill="x", pady=20)
        tk.Label(self.form_container, text="الرصيد الحالي", font=("Segoe UI", 12), bg="white", fg="#7f8c8d").pack()
        self.lbl_balance = tk.Label(self.form_container, text="0.00 ر.ي", font=("Segoe UI", 22, "bold"),
                                    bg="white", fg="#c0392b")
        self.lbl_balance.pack()

        # --- الجانب الأيسر: شجرة الحسابات (Treeview) ---
        tree_frame = tk.Frame(content, bg="white")
        tree_frame.pack(side="left", fill="both", expand=True, padx=(0, 15))

        tk.Label(tree_frame, text="📁 الهيكل التنظيمي للحسابات", font=("Segoe UI", 12, "bold"), bg="white",
                 fg=self.primary_color).pack(anchor="e", pady=(0, 5))

        # استخدام show="tree headings" لضمان ظهور التسلسل الهرمي والأعمدة معاً
        self.tree = ttk.Treeview(tree_frame, columns=("code", "nature"), show="tree headings")

        self.tree.heading("#0", text="اسم الحساب", anchor="e")
        self.tree.heading("code", text="الكود", anchor="center")
        self.tree.heading("nature", text="الطبيعة", anchor="center")

        # ضبط الأعمدة لتكون متناسقة مع الواجهة العربية
        self.tree.column("#0", width=380, anchor="e")
        self.tree.column("code", width=100, anchor="center")
        self.tree.column("nature", width=100, anchor="center")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _load_accounts_from_db(self):
        """تحميل البيانات وبناء الشجرة بأيقونات مختلفة للأب والابن"""
        self.tree.delete(*self.tree.get_children())
        self.account_rows.clear()

        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            query = """
                SELECT account_code, account_name, parent_code, account_type, nature
                FROM finance.accounts
                ORDER BY account_code ASC
            """
            cur.execute(query)
            rows = cur.fetchall()

            for code, name, p_code, a_type, nature in rows:
                self.account_rows[str(code)] = {
                    "account_code": str(code),
                    "account_name": name or "",
                    "parent_code": "" if p_code in (None, "", "0", 0) else str(p_code),
                    "account_type": a_type or "",
                    "nature": nature or ""
                }

            children_map = {}
            for acc in self.account_rows.values():
                parent_key = acc["parent_code"]
                children_map.setdefault(parent_key, []).append(acc)

            def add_nodes(parent_key, parent_iid=""):
                for acc in sorted(children_map.get(parent_key, []), key=lambda x: x["account_code"]):
                    is_parent = acc["account_type"] == "رئيسي"
                    display_name = f"📁 {acc['account_name']}" if is_parent else f"📄 {acc['account_name']}"
                    tag = "parent_row" if is_parent else "child_row"
                    code = acc["account_code"]
                    self.tree.insert(parent_iid, "end", iid=code, text=display_name,
                                     values=(code, acc["nature"]), tags=(tag,))
                    if is_parent:
                        self.tree.item(code, open=True)
                    add_nodes(code, code)

            add_nodes("")

            self.tree.tag_configure("parent_row", font=("Segoe UI", 11, "bold"))
            self.tree.tag_configure("child_row", font=("Segoe UI", 11))

        except Exception as e:
            messagebox.showerror("خطأ قاعدة بيانات", f"فشل تحميل البيانات: {e}")
        finally:
            conn.close()

    def _create_styled_field(self, parent, label_text, widget_type="entry", **kwargs):
        container = tk.Frame(parent, bg="white")
        container.pack(fill="x", pady=8)
        if widget_type == "entry":
            field = tk.Entry(container, font=("Segoe UI", 14, "bold"), bd=2, relief="groove", justify="right", **kwargs)
        elif widget_type == "combo":
            field = ttk.Combobox(container, font=("Segoe UI", 13, "bold"), justify="right", **kwargs)
        else:
            raise ValueError(f"Unsupported widget_type: {widget_type}")
        field.pack(side="left", fill="x", expand=True, padx=(0, 10))
        lbl = tk.Label(container, text=label_text, bg=self.sidebar_color, fg="white",
                       font=("Segoe UI", 11, "bold"), width=18, anchor="center", pady=6)
        lbl.pack(side="right")
        return field

    def _normalize_form_data(self):
        return {
            "account_code": self.entries['account_code'].get().strip(),
            "account_name": self.entries['account_name'].get().strip(),
            "parent_code": self.entries['parent_code'].get().strip(),
            "account_type": self.combo_type.get().strip(),
            "nature": self.combo_nature.get().strip()
        }

    def _validate_required(self, data):
        if not data["account_code"] or not data["account_name"]:
            messagebox.showwarning("بيانات ناقصة", "يرجى إدخال رقم الحساب واسم الحساب.")
            return False
        if data["parent_code"] and data["parent_code"] == data["account_code"]:
            messagebox.showwarning("بيانات غير صحيحة", "لا يمكن أن يكون الحساب أباً لنفسه.")
            return False
        return True

    def _save_account(self):
        data = self._normalize_form_data()
        if not self._validate_required(data):
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO finance.accounts (account_code, account_name, parent_code, account_type, nature)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    data["account_code"],
                    data["account_name"],
                    data["parent_code"] or None,
                    data["account_type"] or "تحليلي",
                    data["nature"] or None
                )
            )
            conn.commit()
            self._load_accounts_from_db()
            self._select_tree_item(data["account_code"])
            messagebox.showinfo("نجاح", "تم حفظ الحساب بنجاح.")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", f"تعذر حفظ الحساب: {e}")
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
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE finance.accounts
                SET account_name = %s,
                    parent_code = %s,
                    account_type = %s,
                    nature = %s
                WHERE account_code = %s
                """,
                (
                    data["account_name"],
                    data["parent_code"] or None,
                    data["account_type"] or "تحليلي",
                    data["nature"] or None,
                    data["account_code"]
                )
            )
            if cur.rowcount == 0:
                messagebox.showwarning("غير موجود", "الحساب المطلوب تعديله غير موجود.")
                return
            conn.commit()
            self._load_accounts_from_db()
            self._select_tree_item(data["account_code"])
            messagebox.showinfo("نجاح", "تم تعديل الحساب بنجاح.")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", f"تعذر تعديل الحساب: {e}")
        finally:
            conn.close()

    def _delete_account(self):
        code = self.entries['account_code'].get().strip()
        if not code:
            messagebox.showwarning("تنبيه", "يرجى تحديد الحساب المراد حذفه من الشجرة أولاً.")
            return

        if not messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف هذا الحساب؟"):
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM finance.accounts WHERE parent_code = %s", (code,))
            children_count = cur.fetchone()[0]
            if children_count > 0:
                messagebox.showerror("رفض الحذف", "لا يمكن حذف حساب رئيسي يحتوي على حسابات فرعية.")
                return

            cur.execute("DELETE FROM finance.accounts WHERE account_code = %s", (code,))
            if cur.rowcount == 0:
                messagebox.showwarning("غير موجود", "الحساب غير موجود أو تم حذفه مسبقاً.")
                return

            conn.commit()
            self._load_accounts_from_db()
            self._clear_form()
            messagebox.showinfo("نجاح", "تم حذف الحساب بنجاح.")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", f"تعذر حذف الحساب: {e}")
        finally:
            conn.close()

    def _search_account(self):
        keyword = self.entries['account_name'].get().strip()
        if not keyword:
            messagebox.showwarning("بحث", "أدخل اسم الحساب في الحقل ثم اضغط بحث.")
            return

        lowered = keyword.lower()
        for code in self.tree.get_children(""):
            # البحث يتم على كامل الشجرة بشكل تكراري
            found = self._find_in_branch(code, lowered)
            if found:
                self._select_tree_item(found)
                return

        messagebox.showinfo("بحث", "لم يتم العثور على حساب مطابق.")

    def _find_in_branch(self, node_id, lowered_keyword):
        item = self.tree.item(node_id)
        clean_name = item['text'].replace("📁 ", "").replace("📄 ", "").strip().lower()
        if lowered_keyword in clean_name:
            return node_id
        for child in self.tree.get_children(node_id):
            found = self._find_in_branch(child, lowered_keyword)
            if found:
                return found
        return None

    def _select_tree_item(self, item_id):
        if not self.tree.exists(item_id):
            return
        parent = self.tree.parent(item_id)
        while parent:
            self.tree.item(parent, open=True)
            parent = self.tree.parent(parent)
        self.tree.selection_set(item_id)
        self.tree.focus(item_id)
        self.tree.see(item_id)

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        code = selected[0]
        data = self.account_rows.get(code)
        if not data:
            return

        self._clear_form(reset_focus=False)
        self.entries['account_code'].insert(0, data["account_code"])
        self.entries['account_name'].insert(0, data["account_name"])
        self.entries['parent_code'].insert(0, data["parent_code"])
        self.combo_type.set(data["account_type"])
        self.combo_nature.set(data["nature"])

    def _clear_form(self, reset_focus=True):
        for e in self.entries.values():
            e.delete(0, tk.END)
        self.combo_type.set('')
        self.combo_nature.set('')
        self.lbl_balance.config(text="0.00 ر.ي")
        if reset_focus:
            self.entries['account_code'].focus_set()

    def _exit_app(self):
        if messagebox.askyesno("خروج", "هل تريد إغلاق التطبيق بأمان؟"):
            self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("نظام الصوفي المحاسبي - الهيكل الشجري")
    root.geometry("1200x900")
    app = ChartOfAccountsScreen(root)
    root.mainloop()


