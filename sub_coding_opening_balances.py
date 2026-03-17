# subcoding_opening_balances.py
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import ttkbootstrap as tb
from db_connection import get_connection

class SubCodingOpeningBalances:
    def __init__(self, master):
        self.master = master

        # Palette
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.bg_color = "#f4f7f6"

        # Action button colors (required per spec)
        self.color_new = "#3498db"
        self.color_save = "#27ae60"
        self.color_edit = "#f1c40f"
        self.color_delete = "#e74c3c"
        self.color_search = "#8e44ad"
        self.color_exit = "#e67e22"

        # Fonts aligned with voucher screens
        self.base_font = ("Segoe UI", 11)
        self.bold_font = ("Segoe UI", 11, "bold")
        self.title_font = ("Segoe UI", 20, "bold")

        # state
        self.selected_plot_id = None
        self.selected_vendor_id = None
        self.plot_rows_cache = []
        self.vendor_rows_cache = []
        self.plot_map = {}
        self.vendor_map = {}

        # vars
        self.summary_amount_var = tk.StringVar(value="0.00")
        self.summary_words_var = tk.StringVar(value="فقط صفر")

        # style + layout
        self._setup_styles()
        self._build_layout()
        # initial data load
        self._refresh_all_data()

    def _setup_styles(self):
        self.style = tb.Style(theme="flatly")  # base theme but we customize heavily

        # Root frames and cards
        self.style.configure("App.Root.TFrame", background=self.bg_color)
        self.style.configure("App.Header.TFrame", background=self.primary_color)
        self.style.configure("App.HeaderTitle.TLabel", background=self.primary_color, foreground="white", font=self.title_font, anchor="e")

        self.style.configure("App.Card.TFrame", background="white", relief="solid", borderwidth=1, bordercolor="#d1d8e0")
        self.style.configure("App.CardTitle.TLabel", background="white", foreground=self.primary_color, font=("Segoe UI", 13, "bold"), anchor="e")
        self.style.configure("App.FormLabel.TLabel", background="white", foreground=self.primary_color, font=("Segoe UI", 12, "bold"), anchor="e", justify="right")
        self.style.configure("App.Field.TEntry", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 11))
        self.style.configure("App.Field.TCombobox", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 11))

        # Summary box
        self.style.configure("App.Summary.TFrame", background=self.bg_color, relief="flat")
        self.style.configure("App.SummaryTitle.TLabel", background=self.bg_color, foreground=self.primary_color, font=("Segoe UI", 12, "bold"))
        self.style.configure("App.SummaryAmount.TLabel", background=self.bg_color, foreground=self.color_delete, font=("Segoe UI", 24, "bold"))
        self.style.configure("App.SummaryWords.TLabel", background=self.bg_color, foreground=self.sidebar_color, font=("Segoe UI", 14, "bold"))

        # Buttons styles aligned with voucher screens.
        self.style.configure("App.SubCoding.Primary.TButton", background=self.color_new, foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        self.style.configure("App.SubCoding.Success.TButton", background=self.color_save, foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        self.style.configure("App.SubCoding.Warning.TButton", background=self.color_edit, foreground="#2c3e50", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        self.style.configure("App.SubCoding.Danger.TButton", background=self.color_delete, foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        self.style.configure("App.SubCoding.Info.TButton", background=self.color_search, foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        self.style.configure("App.SubCoding.Exit.TButton", background=self.color_exit, foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))

        for button_style in (
            "App.SubCoding.Primary.TButton",
            "App.SubCoding.Success.TButton",
            "App.SubCoding.Warning.TButton",
            "App.SubCoding.Danger.TButton",
            "App.SubCoding.Info.TButton",
            "App.SubCoding.Exit.TButton",
        ):
            self.style.map(
                button_style,
                background=[("active", self.accent_color), ("pressed", self.accent_color)],
                foreground=[("active", "white"), ("pressed", "white")],
            )

        # Notebook aligned to the same modern ERP styling language.
        self.style.configure("App.SubCoding.TNotebook", background=self.bg_color, borderwidth=0)
        self.style.configure("App.SubCoding.TNotebook.Tab", font=("Segoe UI", 11, "bold"), padding=(14, 8), background=self.sidebar_color, foreground=self.text_color)
        self.style.map(
            "App.SubCoding.TNotebook.Tab",
            background=[("selected", self.accent_color), ("active", self.accent_color)],
            foreground=[("selected", "white"), ("active", "white")],
        )

        # Treeview (table) style
        self.style.configure("App.Treeview", rowheight=30, font=self.base_font, background="white", fieldbackground="white", foreground=self.primary_color)
        self.style.configure("App.Treeview.Heading", font=("Segoe UI", 11, "bold"), background=self.primary_color, foreground="white")
        # selection color (single place)
        self.style.map("App.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "white")])
        self.style.configure("App.Vertical.TScrollbar", troughcolor=self.bg_color, bordercolor=self.sidebar_color, arrowcolor=self.primary_color)

    def _build_layout(self):
        # Support both standalone windows and embedded Frame hosts.
        host_window = self.master.winfo_toplevel() if hasattr(self.master, "winfo_toplevel") else None
        if host_window and host_window is self.master and hasattr(host_window, "title"):
            host_window.title("SubCoding - Opening Balances")

        if isinstance(self.master, (tk.Tk, tk.Toplevel)):
            self.master.configure(bg=self.bg_color)
        elif host_window and host_window is not self.master:
            try:
                host_window.configure(bg=self.bg_color)
            except tk.TclError:
                pass

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        root = ttk.Frame(self.master, style="App.Root.TFrame", padding=12)
        root.grid(sticky="nsew")
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # header
        header = ttk.Frame(root, style="App.Header.TFrame", padding=(12,10))
        header.grid(row=0, column=0, sticky="ew", pady=(0,12))
        header.grid_columnconfigure(1, weight=1)

        actions = ttk.Frame(header, style="App.Header.TFrame")
        actions.grid(row=0, column=0, sticky="w")

        ttk.Button(actions, text="جديد", style="App.SubCoding.Primary.TButton", command=self._action_new).grid(row=0, column=0, padx=(0,8))
        ttk.Button(actions, text="حفظ", style="App.SubCoding.Success.TButton", command=self._action_save).grid(row=0, column=1, padx=8)
        ttk.Button(actions, text="تعديل", style="App.SubCoding.Warning.TButton", command=self._action_edit).grid(row=0, column=2, padx=8)
        ttk.Button(actions, text="حذف", style="App.SubCoding.Danger.TButton", command=self._action_delete).grid(row=0, column=3, padx=8)
        ttk.Button(actions, text="بحث", style="App.SubCoding.Info.TButton", command=self._action_search).grid(row=0, column=4, padx=8)
        ttk.Button(actions, text="خروج", style="App.SubCoding.Exit.TButton", command=self._action_exit).grid(row=0, column=5, padx=(8,0))

        ttk.Label(header, text="شاشة تعريف العقارات والورثة", style="App.HeaderTitle.TLabel").grid(row=0, column=1, sticky="e")

        # Notebook
        notebook_wrapper = ttk.Frame(root, style="App.Root.TFrame", padding=(0, 6, 0, 0))
        notebook_wrapper.grid(row=1, column=0, sticky="nsew")
        notebook_wrapper.grid_rowconfigure(0, weight=1)
        notebook_wrapper.grid_columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(notebook_wrapper, style="App.SubCoding.TNotebook")
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        # tabs
        self.plot_tab = ttk.Frame(self.notebook, style="App.Root.TFrame", padding=12)
        self.vendor_tab = ttk.Frame(self.notebook, style="App.Root.TFrame", padding=12)
        self.plot_tab.grid_rowconfigure(0, weight=1)
        self.plot_tab.grid_columnconfigure(0, weight=1)
        self.vendor_tab.grid_rowconfigure(0, weight=1)
        self.vendor_tab.grid_columnconfigure(0, weight=1)

        self.notebook.add(self.plot_tab, text="تعريف العقارات")
        self.notebook.add(self.vendor_tab, text="الورثة والأرصدة الافتتاحية")

        # build tab interfaces
        self._build_plot_interface()
        self._build_vendor_interface()

    # ---------------------------
    # Plot (properties) UI
    # ---------------------------
    def _build_plot_interface(self):
        container = ttk.Frame(self.plot_tab, style="App.Root.TFrame")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=2)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # table card
        table_card = ttk.Frame(container, style="App.Card.TFrame", padding=12)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        table_card.grid_rowconfigure(1, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        ttk.Label(table_card, text="العقارات المسجلة", style="App.CardTitle.TLabel").grid(row=0, column=0, sticky="e", pady=(0,8))
        cols = ("id", "name", "cost", "loc")
        heads = ["كود", "اسم العقار", "تكلفة/مساحة", "الموقع"]
        self.plot_tree = self._create_tree(table_card, 1, 0, cols, heads)
        self.plot_tree.bind("<<TreeviewSelect>>", self._on_plot_select)

        # form card
        form_card = ttk.Frame(container, style="App.Card.TFrame", padding=12)
        form_card.grid(row=0, column=1, sticky="nsew", padx=(8,0))
        form_card.grid_columnconfigure(0, weight=1)

        ttk.Label(form_card, text="بيانات العقار", style="App.CardTitle.TLabel").grid(row=0, column=0, sticky="e", pady=(0,8))

        self.p_name = self._create_label_entry(form_card, "اسم العقار:", 1)
        self.p_area = self._create_label_entry(form_card, "التكلفة/المساحة:", 3)
        self.p_loc = self._create_label_entry(form_card, "الموقع:", 5)

        ttk.Button(form_card, text="حفظ العقار", style="App.SubCoding.Success.TButton", command=self._save_plot).grid(
            row=7, column=0, sticky="ew", pady=(12, 0)
        )

    # ---------------------------
    # Vendor UI
    # ---------------------------
    def _build_vendor_interface(self):
        container = ttk.Frame(self.vendor_tab, style="App.Root.TFrame")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=2)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        table_card = ttk.Frame(container, style="App.Card.TFrame", padding=12)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0,8))
        table_card.grid_rowconfigure(1, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        ttk.Label(table_card, text="الورثة والأرصدة", style="App.CardTitle.TLabel").grid(row=0, column=0, sticky="e", pady=(0,8))
        cols = ("id", "name", "group", "property", "bal")
        heads = ["كود", "الاسم", "المجموعة", "العقار المرتبط", "الرصيد"]
        self.vendor_tree = self._create_tree(table_card, 1, 0, cols, heads)
        self.vendor_tree.bind("<<TreeviewSelect>>", self._on_vendor_select)

        form_card = ttk.Frame(container, style="App.Card.TFrame", padding=12)
        form_card.grid(row=0, column=1, sticky="nsew", padx=(8,0))
        form_card.grid_columnconfigure(0, weight=1)

        ttk.Label(form_card, text="بيانات الوارث", style="App.CardTitle.TLabel").grid(row=0, column=0, sticky="e", pady=(0,8))

        self.v_name = self._create_label_entry(form_card, "اسم الوارث:", 1)
        self.v_group = self._create_label_entry(form_card, "المجموعة:", 3)

        ttk.Label(form_card, text="اختر العقار (اختياري):", style="App.FormLabel.TLabel").grid(row=5, column=0, sticky="e", pady=(8,2))
        self.v_plot_cb = ttk.Combobox(form_card, style="App.Field.TCombobox", state="readonly", justify="right", font=("Segoe UI", 12, "bold"))
        self.v_plot_cb.grid(row=6, column=0, sticky="ew", pady=(0,8))

        self.v_balance = self._create_label_entry(form_card, "رصيد افتتاحي (مدين):", 8)
        self.v_balance.insert(0, "0")
        self.v_balance.bind("<KeyRelease>", lambda _e: self._update_balance_preview())
        self.v_balance.bind("<FocusOut>", lambda _e: self._update_balance_preview())

        # summary box
        self._build_summary_box(form_card, 10)

        ttk.Button(form_card, text="حفظ الوارث", style="App.SubCoding.Success.TButton", command=self._save_vendor).grid(
            row=12, column=0, sticky="ew", pady=(12, 0)
        )

    def _build_summary_box(self, parent, row):
        summary = ttk.Frame(parent, style="App.Summary.TFrame", padding=10)
        summary.grid(row=row, column=0, sticky="ew", pady=(8,0))
        summary.columnconfigure(0, weight=1)

        ttk.Label(summary, text="ملخص الرصيد", style="App.SummaryTitle.TLabel").grid(row=0, column=0, sticky="e")
        ttk.Label(summary, textvariable=self.summary_amount_var, style="App.SummaryAmount.TLabel").grid(row=1, column=0, sticky="e")
        ttk.Label(summary, textvariable=self.summary_words_var, style="App.SummaryWords.TLabel").grid(row=2, column=0, sticky="e")

    # helper to create label above entry (consistent padding)
    def _create_label_entry(self, parent, txt, row, entry_style="App.Field.TEntry"):
        ttk.Label(parent, text=txt, style="App.FormLabel.TLabel").grid(row=row, column=0, sticky="e", pady=(8,2))
        ent = ttk.Entry(parent, justify="right", font=self.base_font, style=entry_style)
        ent.grid(row=row+1, column=0, sticky="ew", pady=(0,6), ipady=6)
        return ent

    # tree builder
    def _create_tree(self, parent, row, column, cols, heads):
        frame = ttk.Frame(parent, style="App.Card.TFrame")
        frame.grid(row=row, column=column, sticky="nsew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse", style="App.Treeview")
        widths = {"id": 80, "name": 240, "cost": 140, "loc": 160, "group": 140, "property": 190, "bal": 120}

        for col_name, head in zip(cols, heads):
            tree.heading(col_name, text=head, anchor="center")
            tree.column(col_name, anchor="center", width=widths.get(col_name, 120), stretch=True)

        vsb = ttk.Scrollbar(frame, orient="vertical", style="App.Vertical.TScrollbar", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns", padx=(6,0))

        # row striping tags
        tree.tag_configure("odd", background="white")
        tree.tag_configure("even", background="#f0f3f5")
        tree.tag_configure("empty", foreground=self.sidebar_color)
        return tree

    # ---------------------------
    # Data population & reload
    # ---------------------------
    def _show_empty_state(self, tree, columns_count, text="No Data Available"):
        tree.delete(*tree.get_children())
        empty_values = [text] + ["" for _ in range(columns_count - 1)]
        tree.insert("", "end", iid="__empty__", values=tuple(empty_values), tags=("empty",))
        # make sure selection cleared
        try:
            tree.selection_remove(tree.selection())
        except Exception:
            pass

    def _fill_tree(self, tree, rows, columns_count):
        tree.delete(*tree.get_children())
        if not rows:
            self._show_empty_state(tree, columns_count)
            return
        for index, row in enumerate(rows):
            tag = "even" if index % 2 == 0 else "odd"
            # ensure all values converted to string to avoid display errors
            vals = tuple("" if v is None else v for v in row)
            tree.insert("", "end", iid=str(row[0]), values=vals, tags=(tag,))

    def _refresh_all_data(self):
        conn = get_connection()
        if not conn:
            messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
            return
        try:
            cur = conn.cursor()
            # properties
            cur.execute(
                """
                SELECT id,
                       property_name,
                       COALESCE(total_cost, purchase_price, 0) AS total_cost,
                       COALESCE(location, '') AS location
                FROM finance.properties
                ORDER BY id DESC
                """
            )
            self.plot_rows_cache = cur.fetchall()
            self.plot_map = {int(r[0]): r for r in self.plot_rows_cache}
            self._fill_tree(self.plot_tree, self.plot_rows_cache, 4)

            # fill property combobox
            self.v_plot_cb["values"] = [f"{r[0]} - {r[1]}" for r in self.plot_rows_cache]
            if self.v_plot_cb.get() not in self.v_plot_cb["values"]:
                self.v_plot_cb.set("")

            # vendors + balances
            cur.execute(
                """
                SELECT v.id,
                       v.vendor_name,
                       COALESCE(v.group_name, '') AS group_name,
                       COALESCE(
                           (SELECT p.property_name
                            FROM finance.properties p
                            WHERE p.id = (
                                SELECT l2.property_id
                                FROM finance.ledger l2
                                WHERE l2.vendor_id = v.id
                                ORDER BY l2.id DESC
                                LIMIT 1
                            )),
                           '-'
                       ) AS property_name,
                       COALESCE((SELECT SUM(debit - credit) FROM finance.ledger WHERE vendor_id = v.id), 0) AS current_balance
                FROM finance.vendors v
                ORDER BY v.vendor_name
                """
            )
            vendor_rows_raw = cur.fetchall()
            # vendor_rows_cache arranged to match columns shown earlier
            self.vendor_rows_cache = [(r[0], r[1], r[2], r[3], r[4]) for r in vendor_rows_raw]
            # vendor_map holds details used when selecting
            self.vendor_map = {
                int(r[0]): {
                    "id": int(r[0]),
                    "name": r[1],
                    "group": r[2],
                    "property_name": r[3],
                    "balance": r[4],
                }
                for r in vendor_rows_raw
            }
            self._fill_tree(self.vendor_tree, self.vendor_rows_cache, 5)
        except Exception as e:
            messagebox.showerror("خطأ", str(e))
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # ---------------------------
    # CRUD: Save / Edit / Delete
    # ---------------------------
    def _save_plot(self):
        name = self.p_name.get().strip()
        cost = self.p_area.get().strip()
        loc = self.p_loc.get().strip()

        if not name:
            return messagebox.showwarning("تنبيه", "أدخل اسم العقار")

        try:
            cost_val = float(cost) if cost else None
        except Exception:
            return messagebox.showwarning("تنبيه", "التكلفة/المساحة غير صحيحة")

        conn = get_connection()
        if not conn:
            return messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO finance.properties (property_name, total_cost, location) VALUES (%s, %s, %s)",
                (name, cost_val, loc),
            )
            conn.commit()
            messagebox.showinfo("نجاح", "تم حفظ العقار")
            self._clear_plot_form()
            self._refresh_all_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _save_vendor(self):
        name = self.v_name.get().strip()
        group = self.v_group.get().strip()
        plot_info = self.v_plot_cb.get().strip()
        try:
            bal = float(self.v_balance.get().strip() or 0)
        except Exception:
            return messagebox.showwarning("تنبيه", "الرجاء إدخال رصيد افتتاحي صحيح")

        if not name:
            return messagebox.showwarning("تنبيه", "أكمل بيانات الوارث (الاسم)")

        property_id = None
        if plot_info:
            try:
                property_id = int(plot_info.split(" - ")[0])
            except Exception:
                property_id = None

        conn = get_connection()
        if not conn:
            return messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO finance.vendors (vendor_name, group_name) VALUES (%s, %s) RETURNING id", (name, group))
            v_id = cur.fetchone()[0]

            if bal > 0:
                cur.execute(
                    "INSERT INTO finance.vouchers (v_type, v_date, description) VALUES (%s, CURRENT_DATE, %s) RETURNING id",
                    ("رصيد افتتاحى", f"رصيد أول المدة: {name}"),
                )
                voc_id = cur.fetchone()[0]

                # debit to vendor (account 2101)
                cur.execute(
                    "INSERT INTO finance.ledger (voucher_id, account_code, vendor_id, property_id, debit) VALUES (%s, %s, %s, %s, %s)",
                    (voc_id, "2101", v_id, property_id, bal),
                )
                # balancing credit (account 3999). keep vendor_id NULL for general ledger credit line (depends on your schema)
                cur.execute(
                    "INSERT INTO finance.ledger (voucher_id, account_code, credit) VALUES (%s, %s, %s)",
                    (voc_id, "3999", bal),
                )

            conn.commit()
            messagebox.showinfo("نجاح", "تم الحفظ")
            self._clear_vendor_form()
            self._refresh_all_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    # ---------------------------
    # Actions - wrappers
    # ---------------------------
    def _action_new(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._clear_plot_form()
        else:
            self._clear_vendor_form()

    def _action_save(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._save_plot()
        else:
            self._save_vendor()

    def _action_edit(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._edit_plot()
        else:
            self._edit_vendor()

    def _action_delete(self):
        if self.notebook.index(self.notebook.select()) == 0:
            self._delete_plot()
        else:
            self._delete_vendor()

    def _action_search(self):
        query = simpledialog.askstring("بحث", "أدخل كلمة البحث:", parent=self.master)
        if query is None:
            return
        query = query.strip().lower()
        active_tab = self.notebook.index(self.notebook.select())

        if not query:
            self._refresh_all_data()
            return

        if active_tab == 0:
            filtered = [r for r in self.plot_rows_cache if query in str(r[1]).lower() or query in str(r[3] or "").lower()]
            self._fill_tree(self.plot_tree, filtered, 4)
        else:
            filtered = [r for r in self.vendor_rows_cache if query in str(r[1]).lower() or query in str(r[2] or "").lower() or query in str(r[3] or "").lower()]
            self._fill_tree(self.vendor_tree, filtered, 5)

    def _action_exit(self):
        if messagebox.askyesno("تأكيد", "هل تريد إغلاق هذه الشاشة؟"):
            self.master.destroy()

    # ---------------------------
    # Clear forms & selection logic
    # ---------------------------
    def _clear_plot_form(self):
        self.selected_plot_id = None
        self.p_name.delete(0, "end")
        self.p_area.delete(0, "end")
        self.p_loc.delete(0, "end")
        try:
            self.plot_tree.selection_remove(self.plot_tree.selection())
        except Exception:
            pass

    def _clear_vendor_form(self):
        self.selected_vendor_id = None
        self.v_name.delete(0, "end")
        self.v_group.delete(0, "end")
        self.v_balance.delete(0, "end")
        self.v_balance.insert(0, "0")
        self.v_plot_cb.set("")
        self._update_balance_preview()
        try:
            self.vendor_tree.selection_remove(self.vendor_tree.selection())
        except Exception:
            pass

    def _on_plot_select(self, _event=None):
        selected = self.plot_tree.selection()
        if not selected:
            return
        iid = selected[0]
        if iid == "__empty__":
            return
        self.selected_plot_id = int(iid)
        row = self.plot_map.get(self.selected_plot_id)
        if not row:
            return
        # populate
        self.p_name.delete(0, "end"); self.p_name.insert(0, row[1] or "")
        self.p_area.delete(0, "end"); self.p_area.insert(0, str(row[2]) if row[2] is not None else "")
        self.p_loc.delete(0, "end"); self.p_loc.insert(0, row[3] or "")

    def _on_vendor_select(self, _event=None):
        selected = self.vendor_tree.selection()
        if not selected:
            return
        iid = selected[0]
        if iid == "__empty__":
            return
        self.selected_vendor_id = int(iid)
        row = self.vendor_map.get(self.selected_vendor_id)
        if not row:
            return
        self.v_name.delete(0, "end"); self.v_name.insert(0, row["name"] or "")
        self.v_group.delete(0, "end"); self.v_group.insert(0, row["group"] or "")
        self.v_balance.delete(0, "end"); self.v_balance.insert(0, str(row["balance"] or 0))
        # attempt to set combobox by property name
        prop_name = row.get("property_name")
        if prop_name and prop_name != "-":
            for val in self.v_plot_cb["values"]:
                if val.endswith(f" - {prop_name}"):
                    self.v_plot_cb.set(val)
                    break
        else:
            self.v_plot_cb.set("")
        self._update_balance_preview()

    # ---------------------------
    # Edit / Delete implementations
    # ---------------------------
    def _edit_plot(self):
        if not self.selected_plot_id:
            return messagebox.showwarning("تنبيه", "اختر عقارًا من الجدول أولاً")

        name = self.p_name.get().strip()
        cost = self.p_area.get().strip()
        loc = self.p_loc.get().strip()

        if not name:
            return messagebox.showwarning("تنبيه", "أدخل اسم العقار")

        try:
            cost_val = float(cost) if cost else None
        except Exception:
            return messagebox.showwarning("تنبيه", "التكلفة/المساحة غير صحيحة")

        conn = get_connection()
        if not conn:
            return messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
        cur = conn.cursor()
        try:
            cur.execute("UPDATE finance.properties SET property_name=%s, total_cost=%s, location=%s WHERE id=%s",
                        (name, cost_val, loc, self.selected_plot_id))
            conn.commit()
            messagebox.showinfo("نجاح", "تم تعديل بيانات العقار")
            self._clear_plot_form()
            self._refresh_all_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _edit_vendor(self):
        if not self.selected_vendor_id:
            return messagebox.showwarning("تنبيه", "اختر وارثًا من الجدول أولاً")

        name = self.v_name.get().strip()
        group = self.v_group.get().strip()
        plot_info = self.v_plot_cb.get().strip()
        try:
            bal = float(self.v_balance.get().strip() or 0)
        except Exception:
            return messagebox.showwarning("تنبيه", "الرصيد غير صحيح")

        if not name:
            return messagebox.showwarning("تنبيه", "أكمل بيانات الوارث (الاسم)")

        property_id = None
        if plot_info:
            try:
                property_id = int(plot_info.split(" - ")[0])
            except Exception:
                property_id = None

        conn = get_connection()
        if not conn:
            return messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
        cur = conn.cursor()
        try:
            cur.execute("UPDATE finance.vendors SET vendor_name=%s, group_name=%s WHERE id=%s", (name, group, self.selected_vendor_id))

            # update opening voucher lines if present
            cur.execute(
                """
                SELECT l.voucher_id
                FROM finance.ledger l
                JOIN finance.vouchers v ON v.id = l.voucher_id
                WHERE l.vendor_id = %s
                  AND l.account_code = '2101'
                  AND v.v_type = %s
                ORDER BY l.id
                LIMIT 1
                """,
                (self.selected_vendor_id, "رصيد افتتاحى"),
            )
            opening_voucher = cur.fetchone()
            if opening_voucher:
                voucher_id = opening_voucher[0]
                cur.execute(
                    "UPDATE finance.ledger SET property_id=%s, debit=%s WHERE voucher_id=%s AND vendor_id=%s AND account_code='2101'",
                    (property_id, bal, voucher_id, self.selected_vendor_id),
                )
                cur.execute("UPDATE finance.ledger SET credit=%s WHERE voucher_id=%s AND account_code='3999'", (bal, voucher_id))

            conn.commit()
            messagebox.showinfo("نجاح", "تم تعديل بيانات الوارث")
            self._clear_vendor_form()
            self._refresh_all_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _delete_plot(self):
        if not self.selected_plot_id:
            return messagebox.showwarning("تنبيه", "اختر عقارًا من الجدول أولاً")
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا العقار؟"):
            return
        conn = get_connection()
        if not conn:
            return messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM finance.ledger WHERE property_id=%s", (self.selected_plot_id,))
            linked = cur.fetchone()[0]
            if linked > 0:
                return messagebox.showwarning("تنبيه", "لا يمكن حذف العقار لوجود قيود محاسبية مرتبطة به")
            cur.execute("DELETE FROM finance.properties WHERE id=%s", (self.selected_plot_id,))
            conn.commit()
            messagebox.showinfo("نجاح", "تم حذف العقار")
            self._clear_plot_form()
            self._refresh_all_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    def _delete_vendor(self):
        if not self.selected_vendor_id:
            return messagebox.showwarning("تنبيه", "اختر وارثًا من الجدول أولاً")
        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا الوارث؟"):
            return
        conn = get_connection()
        if not conn:
            return messagebox.showerror("خطأ", "تعذر الاتصال بقاعدة البيانات")
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM finance.ledger l
                LEFT JOIN finance.vouchers v ON v.id = l.voucher_id
                WHERE l.vendor_id = %s
                  AND COALESCE(v.v_type, '') <> %s
                """,
                (self.selected_vendor_id, "رصيد افتتاحى"),
            )
            has_non_opening_entries = cur.fetchone()[0]
            if has_non_opening_entries > 0:
                return messagebox.showwarning("تنبيه", "لا يمكن حذف الوارث لوجود قيود حركة مرتبطة به")

            cur.execute(
                """
                SELECT DISTINCT l.voucher_id
                FROM finance.ledger l
                JOIN finance.vouchers v ON v.id = l.voucher_id
                WHERE l.vendor_id = %s AND v.v_type = %s
                """,
                (self.selected_vendor_id, "رصيد افتتاحى"),
            )
            opening_vouchers = [r[0] for r in cur.fetchall() if r[0] is not None]

            if opening_vouchers:
                cur.execute("DELETE FROM finance.ledger WHERE voucher_id = ANY(%s)", (opening_vouchers,))
                cur.execute("DELETE FROM finance.vouchers WHERE id = ANY(%s)", (opening_vouchers,))

            cur.execute("DELETE FROM finance.vendors WHERE id=%s", (self.selected_vendor_id,))
            conn.commit()
            messagebox.showinfo("نجاح", "تم حذف الوارث")
            self._clear_vendor_form()
            self._refresh_all_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("خطأ", str(e))
        finally:
            conn.close()

    # ---------------------------
    # UX helpers
    # ---------------------------
    def _update_balance_preview(self):
        text = self.v_balance.get().strip()
        try:
            value = float(text or 0)
        except Exception:
            value = 0.0
        self.summary_amount_var.set(f"{value:,.2f}")
        self.summary_words_var.set(self._amount_to_words(value))

    def _amount_to_words(self, value):
        number = int(abs(value))
        if number == 0:
            return "فقط صفر"
        words = self._int_to_arabic_words(number)
        return f"فقط {words}"

    def _int_to_arabic_words(self, n):
        units = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"]
        teens = ["عشرة", "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر", "ستة عشر", "سبعة عشر", "ثمانية عشر", "تسعة عشر"]
        tens = ["", "", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"]
        hundreds = ["", "مئة", "مئتان", "ثلاثمئة", "أربعمئة", "خمسمئة", "ستمئة", "سبعمئة", "ثمانمئة", "تسعمئة"]

        def under_1000(x):
            parts = []
            h = x // 100
            r = x % 100
            if h:
                parts.append(hundreds[h])
            if 10 <= r <= 19:
                parts.append(teens[r - 10])
            else:
                t = r // 10
                u = r % 10
                if u:
                    parts.append(units[u])
                if t:
                    parts.append(tens[t])
            return " و ".join(parts)

        chunks = []
        millions = n // 1000000
        thousands = (n % 1000000) // 1000
        rest = n % 1000

        if millions:
            chunks.append(f"{under_1000(millions)} مليون")
        if thousands:
            chunks.append(f"{under_1000(thousands)} ألف")
        if rest:
            chunks.append(under_1000(rest))

        return " و ".join([c for c in chunks if c])

# Example usage:

