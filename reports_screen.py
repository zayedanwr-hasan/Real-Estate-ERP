import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import filedialog, messagebox, ttk

import ttkbootstrap as tb

from combobox_helper import bind_searchable_combobox, set_combobox_values
from db_connection import get_connection


def export_to_excel(data, filename):
    """Export a report payload to Excel using pandas/openpyxl."""
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("مكتبة pandas غير مثبتة. ثبّت pandas وopenpyxl أولاً.") from exc

    frame = pd.DataFrame(data.get("rows", []), columns=data.get("columns", []))
    frame.to_excel(filename, index=False)


def export_to_pdf(data, filename, title):
    """Export a report payload to PDF using reportlab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise RuntimeError("مكتبة reportlab غير مثبتة. ثبّتها أولاً.") from exc

    doc = SimpleDocTemplate(filename, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()

    story = [Paragraph(title, styles["Title"]), Spacer(1, 10)]

    date_from = data.get("date_from", "")
    date_to = data.get("date_to", "")
    if date_from and date_to:
        story.append(Paragraph(f"الفترة: {date_from} إلى {date_to}", styles["Normal"]))
        story.append(Spacer(1, 10))

    columns = data.get("columns", [])
    rows = data.get("rows", [])
    table_data = [columns] + [["" if value is None else str(value) for value in row] for row in rows]

    report_table = Table(table_data, repeatRows=1)
    report_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d8e0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f3f5")]),
            ]
        )
    )
    story.append(report_table)

    summary = data.get("summary", {})
    if summary:
        story.append(Spacer(1, 10))
        summary_text = " | ".join([f"{k}: {v:,.2f}" for k, v in summary.items()])
        story.append(Paragraph(summary_text, styles["Heading3"]))

    doc.build(story)


class ReportsScreen:
    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.bg_color = "#f4f7f6"
        self.soft_card_bg = "#f8fafb"
        self.summary_bg = "#e9f7f4"

        self._setup_styles()

        self.frame = tb.Frame(master, style="App.Reports.Root.TFrame")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.main_card = tb.Frame(self.frame, style="App.Reports.Card.TFrame")
        self.main_card.pack(fill="both", expand=True, padx=14, pady=14)

        self._build_header()
        self._build_notebook()
        self._load_filter_sources()

        self.report_to_tab = {
            "كشف حساب وارث": ("heirs", "كشف حساب وارث"),
            "ملخص وارث": ("heirs", "ملخص وارث"),
            "أرصدة الورثة او المجموعة": ("heirs", "أرصدة الورثة"),
            "توزيع الأرباح": ("heirs", "توزيع الأرباح"),
            "كشف حساب عقار": ("properties", "كشف حساب عقار"),
            "تقرير الإيرادات": ("properties", "إيرادات العقارات"),
            "تقرير المصروفات": ("properties", "مصروفات العقارات"),
            "صافي الربح": ("properties", "صافي ربح العقارات"),
            "سندات الصرف": ("vouchers", "سندات الصرف"),
            "سندات القبض": ("vouchers", "سندات القبض"),
            "تقرير يومي": ("vouchers", "تقرير السندات اليومي"),
            "دفتر الأستاذ": ("financial", "دفتر الأستاذ"),
            "ميزان المراجعة": ("financial", "ميزان المراجعة"),
            "قائمة الدخل": ("financial", "قائمة الدخل"),
            "التدفقات النقدية": ("financial", "التدفقات النقدية"),
            "حسب الحساب": ("advanced", "تصفية حسب الحساب"),
            "حسب الوارث": ("advanced", "تصفية حسب الوارث"),
            "حسب العقار": ("advanced", "تصفية حسب العقار"),
            "مقارنة فترات": ("advanced", "مقارنة فترتين"),
        }

    def _setup_styles(self):
        style = tb.Style()
        style.configure("App.Reports.Root.TFrame", background=self.bg_color)
        style.configure("App.Reports.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("App.Reports.Header.TFrame", background=self.primary_color)
        style.configure("App.Reports.Header.TLabel", background=self.primary_color, foreground="white", font=("Segoe UI", 18, "bold"))

        style.configure("App.Reports.Notebook", background="white", borderwidth=0)
        style.configure("App.Reports.Notebook.Tab", font=("Segoe UI", 11, "bold"), padding=(18, 8))
        style.map("App.Reports.Notebook.Tab", background=[("selected", "#dfe6eb")], foreground=[("selected", self.primary_color)])

        style.configure("App.Reports.Tab.TFrame", background="white")
        style.configure("App.Reports.FilterCard.TFrame", background=self.soft_card_bg, bordercolor="#d8e1e8", borderwidth=1, relief="solid")
        style.configure("App.Reports.TableCard.TFrame", background="white", bordercolor="#d8e1e8", borderwidth=1, relief="solid")
        style.configure("App.Reports.Summary.TFrame", background=self.summary_bg, bordercolor="#b8ded6", borderwidth=1, relief="solid")

        style.configure("App.Reports.FieldLabel.TLabel", background=self.soft_card_bg, foreground=self.primary_color, font=("Segoe UI", 11, "bold"))
        style.configure("App.Reports.SummaryTitle.TLabel", background=self.summary_bg, foreground=self.primary_color, font=("Segoe UI", 11, "bold"))
        style.configure("App.Reports.SummaryValue.TLabel", background=self.summary_bg, foreground="#0e6251", font=("Segoe UI", 16, "bold"))

        style.configure("App.Reports.Field.TEntry", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 11, "bold"))
        style.configure("App.Reports.Field.TCombobox", fieldbackground="white", foreground=self.primary_color, font=("Segoe UI", 11, "bold"))

        style.configure("App.Reports.Primary.TButton", background="#2980b9", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Reports.Success.TButton", background="#27ae60", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        style.configure("App.Reports.Warning.TButton", background="#f39c12", foreground="white", borderwidth=0, font=("Segoe UI", 11, "bold"), padding=(10, 6))
        for btn_style in ("App.Reports.Primary.TButton", "App.Reports.Success.TButton", "App.Reports.Warning.TButton"):
            style.map(btn_style, background=[("active", self.accent_color), ("pressed", self.accent_color)], foreground=[("active", "white"), ("pressed", "white")])

        style.configure("App.Reports.Treeview", rowheight=30, font=("Segoe UI", 10), background="white", fieldbackground="white", foreground=self.primary_color)
        style.configure("App.Reports.Treeview.Heading", font=("Segoe UI", 11, "bold"), background=self.primary_color, foreground="white")
        style.map("App.Reports.Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "white")])
        style.map("App.Reports.Treeview.Heading", background=[("active", self.primary_color), ("pressed", self.primary_color)], foreground=[("active", "white"), ("pressed", "white")])
        style.configure("App.Reports.Vertical.TScrollbar", background=self.sidebar_color, troughcolor=self.bg_color, arrowcolor=self.primary_color)
        style.configure("App.Reports.Horizontal.TScrollbar", background=self.sidebar_color, troughcolor=self.bg_color, arrowcolor=self.primary_color)

    def _build_header(self):
        header = tb.Frame(self.main_card, style="App.Reports.Header.TFrame", height=62)
        header.pack(fill="x")
        tb.Label(header, text="شاشة التقارير - Al-Sofi ERP", style="App.Reports.Header.TLabel").pack(side="right", padx=24, pady=12)

    def _build_notebook(self):
        container = tb.Frame(self.main_card, style="App.Reports.Tab.TFrame", padding=(14, 12))
        container.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(container, style="App.Reports.Notebook")
        self.notebook.pack(fill="both", expand=True)

        self.tabs = {}
        self.tab_order = ["heirs", "properties", "vouchers", "financial", "advanced"]

        self._create_report_tab("heirs", "تقارير الورثة", {
            "كشف حساب وارث": self.get_heir_statement,
            "ملخص وارث": self.get_heir_summary,
            "أرصدة الورثة": self.get_heir_balances,
            "توزيع الأرباح": self.get_profit_distribution,
        })
        self._create_report_tab("properties", "تقارير العقارات", {
            "كشف حساب عقار": self.get_property_statement,
            "إيرادات العقارات": self.get_property_income,
            "مصروفات العقارات": self.get_property_expense,
            "صافي ربح العقارات": self.get_property_profit,
        })
        self._create_report_tab("vouchers", "تقارير السندات", {
            "سندات الصرف": self.get_payment_vouchers,
            "سندات القبض": self.get_receipt_vouchers,
            "تقرير السندات اليومي": self.get_daily_vouchers,
        })
        self._create_report_tab("financial", "التقارير المالية", {
            "دفتر الأستاذ": self.get_general_ledger,
            "ميزان المراجعة": self.get_trial_balance,
            "قائمة الدخل": self.get_income_statement,
            "التدفقات النقدية": self.get_cash_flow,
        })
        self._create_report_tab("advanced", "تقارير متقدمة", {
            "تصفية حسب الحساب": self.filter_by_account,
            "تصفية حسب الوارث": self.filter_by_heir,
            "تصفية حسب العقار": self.filter_by_property,
            "مقارنة فترتين": self.compare_periods,
        })

    def _create_report_tab(self, tab_key, title, reports_map):
        tab_frame = tb.Frame(self.notebook, style="App.Reports.Tab.TFrame", padding=10)
        tab_frame.pack(fill="both", expand=True)
        self.notebook.add(tab_frame, text=title)

        state = {
            "report_var": tk.StringVar(value=next(iter(reports_map.keys()))),
            "date_from_var": tk.StringVar(value=self._default_date_from()),
            "date_to_var": tk.StringVar(value=date.today().strftime("%Y-%m-%d")),
            "heir_var": tk.StringVar(),
            "property_var": tk.StringVar(),
            "account_var": tk.StringVar(),
            "reports": reports_map,
            "last_data": None,
        }

        filter_card = tb.Frame(tab_frame, style="App.Reports.FilterCard.TFrame", padding=12)
        filter_card.pack(fill="x", pady=(0, 10))

        self._build_filter_widgets(filter_card, state)
        self._build_action_buttons(filter_card, tab_key)

        table_card = tb.Frame(tab_frame, style="App.Reports.TableCard.TFrame", padding=10)
        table_card.pack(fill="both", expand=True)

        state["tree"] = self._build_results_tree(table_card)

        summary_card = tb.Frame(tab_frame, style="App.Reports.Summary.TFrame", padding=10)
        summary_card.pack(fill="x", pady=(10, 0))
        state["summary_labels"] = self._build_summary_panel(summary_card)

        self.tabs[tab_key] = state

    def _build_filter_widgets(self, parent, state):
        parent.columnconfigure((0, 1, 2, 3, 4), weight=1)

        ttk.Label(parent, text="من تاريخ", style="App.Reports.FieldLabel.TLabel").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        ttk.Entry(parent, textvariable=state["date_from_var"], style="App.Reports.Field.TEntry", justify="center").grid(row=1, column=0, padx=6, pady=4, sticky="ew")

        ttk.Label(parent, text="إلى تاريخ", style="App.Reports.FieldLabel.TLabel").grid(row=0, column=1, padx=6, pady=6, sticky="e")
        ttk.Entry(parent, textvariable=state["date_to_var"], style="App.Reports.Field.TEntry", justify="center").grid(row=1, column=1, padx=6, pady=4, sticky="ew")

        ttk.Label(parent, text="الوارث", style="App.Reports.FieldLabel.TLabel").grid(row=0, column=2, padx=6, pady=6, sticky="e")
        heir_combo = ttk.Combobox(parent, textvariable=state["heir_var"], style="App.Reports.Field.TCombobox", justify="right")
        heir_combo.grid(row=1, column=2, padx=6, pady=4, sticky="ew")
        bind_searchable_combobox(heir_combo)

        ttk.Label(parent, text="العقار", style="App.Reports.FieldLabel.TLabel").grid(row=0, column=3, padx=6, pady=6, sticky="e")
        property_combo = ttk.Combobox(parent, textvariable=state["property_var"], style="App.Reports.Field.TCombobox", justify="right")
        property_combo.grid(row=1, column=3, padx=6, pady=4, sticky="ew")
        bind_searchable_combobox(property_combo)

        ttk.Label(parent, text="الحساب", style="App.Reports.FieldLabel.TLabel").grid(row=0, column=4, padx=6, pady=6, sticky="e")
        account_combo = ttk.Combobox(parent, textvariable=state["account_var"], style="App.Reports.Field.TCombobox", justify="right")
        account_combo.grid(row=1, column=4, padx=6, pady=4, sticky="ew")
        bind_searchable_combobox(account_combo)

        ttk.Label(parent, text="نوع التقرير", style="App.Reports.FieldLabel.TLabel").grid(row=2, column=4, padx=6, pady=(12, 6), sticky="e")
        report_combo = ttk.Combobox(parent, textvariable=state["report_var"], style="App.Reports.Field.TCombobox", justify="right", state="readonly")
        report_combo.grid(row=3, column=2, columnspan=3, padx=6, pady=4, sticky="ew")
        set_combobox_values(report_combo, list(state["reports"].keys()))

        state["heir_combo"] = heir_combo
        state["property_combo"] = property_combo
        state["account_combo"] = account_combo

    def _build_action_buttons(self, parent, tab_key):
        action_frame = tb.Frame(parent, style="App.Reports.FilterCard.TFrame")
        action_frame.grid(row=3, column=0, columnspan=2, pady=8, sticky="w")

        ttk.Button(action_frame, text="عرض التقرير", style="App.Reports.Primary.TButton", command=lambda: self._generate_report(tab_key)).pack(side="left", padx=4)
        ttk.Button(action_frame, text="تصدير PDF", style="App.Reports.Warning.TButton", command=lambda: self._on_export_pdf(tab_key)).pack(side="left", padx=4)
        ttk.Button(action_frame, text="تصدير Excel", style="App.Reports.Success.TButton", command=lambda: self._on_export_excel(tab_key)).pack(side="left", padx=4)

    def _build_results_tree(self, parent):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        tree = ttk.Treeview(parent, show="headings", style="App.Reports.Treeview")

        y_scroll = ttk.Scrollbar(parent, orient="vertical", style="App.Reports.Vertical.TScrollbar", command=tree.yview)
        x_scroll = ttk.Scrollbar(parent, orient="horizontal", style="App.Reports.Horizontal.TScrollbar", command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        tree.tag_configure("even", background="#f0f3f5")
        tree.tag_configure("odd", background="#ffffff")
        return tree

    def _build_summary_panel(self, parent):
        labels = {}
        for col in range(3):
            parent.columnconfigure(col, weight=1)

        label_map = [
            ("total_debit", "إجمالي المدين"),
            ("total_credit", "إجمالي الدائن"),
            ("balance", "الرصيد"),
        ]
        for idx, (key, title) in enumerate(label_map):
            item = tb.Frame(parent, style="App.Reports.Summary.TFrame")
            item.grid(row=0, column=idx, padx=6, sticky="ew")
            ttk.Label(item, text=title, style="App.Reports.SummaryTitle.TLabel").pack(anchor="e")
            labels[key] = ttk.Label(item, text="0.00", style="App.Reports.SummaryValue.TLabel")
            labels[key].pack(anchor="e")

        return labels

    def _default_date_from(self):
        today = date.today()
        return today.replace(day=1).strftime("%Y-%m-%d")

    def _load_filter_sources(self):
        heirs = self._fetch_lookup("SELECT id, heir_name FROM finance.heirs ORDER BY heir_name")
        properties = self._fetch_lookup("SELECT id, property_name FROM finance.properties ORDER BY property_name")
        accounts = self._fetch_lookup("SELECT account_code, account_name FROM finance.accounts ORDER BY account_code")

        for state in self.tabs.values():
            set_combobox_values(state["heir_combo"], [f"{item[0]} - {item[1]}" for item in heirs])
            set_combobox_values(state["property_combo"], [f"{item[0]} - {item[1]}" for item in properties])
            set_combobox_values(state["account_combo"], [f"{item[0]} - {item[1]}" for item in accounts])

    def _fetch_lookup(self, query):
        conn = get_connection()
        if not conn:
            return []
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    return cur.fetchall()
        except Exception:
            return []
        finally:
            conn.close()

    def _extract_prefix(self, value):
        text = (value or "").strip()
        return text.split(" - ")[0].strip() if " - " in text else text

    def _validate_filters(self, tab_key):
        state = self.tabs[tab_key]
        date_from = state["date_from_var"].get().strip()
        date_to = state["date_to_var"].get().strip()

        try:
            from_dt = datetime.strptime(date_from, "%Y-%m-%d").date()
            to_dt = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showwarning("تنبيه", "صيغة التاريخ يجب أن تكون YYYY-MM-DD")
            return None

        if from_dt > to_dt:
            messagebox.showwarning("تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return None

        return {
            "date_from": date_from,
            "date_to": date_to,
            "heir_id": self._extract_prefix(state["heir_var"].get()),
            "property_id": self._extract_prefix(state["property_var"].get()),
            "account_code": self._extract_prefix(state["account_var"].get()),
        }

    def _generate_report(self, tab_key):
        filters = self._validate_filters(tab_key)
        if not filters:
            return

        state = self.tabs[tab_key]
        report_name = state["report_var"].get()
        handler = state["reports"].get(report_name)
        if not handler:
            messagebox.showwarning("تنبيه", "لم يتم العثور على نوع التقرير")
            return

        try:
            payload = handler(filters)
        except ValueError as exc:
            messagebox.showwarning("تنبيه", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("خطأ", f"تعذر إنشاء التقرير: {exc}")
            return

        if not payload["rows"]:
            self._update_tree(state, payload["columns"], [])
            self._update_summary(state, payload.get("summary", {}))
            state["last_data"] = payload
            messagebox.showinfo("نتيجة", "لا توجد بيانات مطابقة للفلاتر المحددة")
            return

        self._update_tree(state, payload["columns"], payload["rows"])
        self._update_summary(state, payload.get("summary", {}))
        state["last_data"] = payload

    def _update_tree(self, state, columns, rows):
        tree = state["tree"]
        tree.delete(*tree.get_children())

        tree.configure(columns=columns)
        for col in columns:
            tree.heading(col, text=col, anchor="e")
            tree.column(col, anchor="e", width=140, minwidth=110)

        for idx, row in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            tree.insert("", "end", values=row, tags=(tag,))

    def _update_summary(self, state, summary):
        labels = state["summary_labels"]
        labels["total_debit"].configure(text=f"{summary.get('total_debit', 0):,.2f}")
        labels["total_credit"].configure(text=f"{summary.get('total_credit', 0):,.2f}")
        labels["balance"].configure(text=f"{summary.get('balance', 0):,.2f}")

    def _on_export_excel(self, tab_key):
        state = self.tabs[tab_key]
        data = state.get("last_data")
        if not data or not data.get("rows"):
            messagebox.showwarning("تنبيه", "اعرض التقرير أولاً قبل التصدير")
            return

        file_name = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not file_name:
            return

        try:
            export_to_excel(data, file_name)
            messagebox.showinfo("نجاح", "تم تصدير التقرير إلى Excel")
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc))

    def _on_export_pdf(self, tab_key):
        state = self.tabs[tab_key]
        data = state.get("last_data")
        if not data or not data.get("rows"):
            messagebox.showwarning("تنبيه", "اعرض التقرير أولاً قبل التصدير")
            return

        file_name = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not file_name:
            return

        try:
            export_to_pdf(data, file_name, data.get("title", "تقرير"))
            messagebox.showinfo("نجاح", "تم تصدير التقرير إلى PDF")
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc))

    def _run_report_query(self, title, sql, params, filters):
        columns, rows = self._run_query(sql, params)
        summary = self._compute_summary(columns, rows)
        return {
            "title": title,
            "columns": columns,
            "rows": rows,
            "summary": summary,
            "date_from": filters["date_from"],
            "date_to": filters["date_to"],
        }

    def _run_query(self, query, params):
        conn = get_connection()
        if not conn:
            return [], []
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    columns = [desc[0] for desc in cur.description] if cur.description else []
            return columns, rows
        except Exception as exc:
            raise RuntimeError(f"خطأ في قاعدة البيانات: {exc}") from exc
        finally:
            conn.close()

    def _base_filters(self, filters, date_field="v.v_date"):
        conditions = [f"{date_field} BETWEEN %s AND %s"]
        params = [filters["date_from"], filters["date_to"]]

        if filters.get("heir_id"):
            conditions.append("l.heir_id = %s")
            params.append(filters["heir_id"])
        if filters.get("property_id"):
            conditions.append("l.property_id = %s")
            params.append(filters["property_id"])
        if filters.get("account_code"):
            conditions.append("l.account_code = %s")
            params.append(filters["account_code"])

        return " AND ".join(conditions), params

    def _compute_summary(self, columns, rows):
        if not rows:
            return {"total_debit": 0.0, "total_credit": 0.0, "balance": 0.0}

        idx = {name.lower(): pos for pos, name in enumerate(columns)}
        total_debit = 0.0
        total_credit = 0.0

        for row in rows:
            if "debit" in idx:
                total_debit += float(row[idx["debit"]] or 0)
            if "credit" in idx:
                total_credit += float(row[idx["credit"]] or 0)
            if "income" in idx:
                total_credit += float(row[idx["income"]] or 0)
            if "expense" in idx:
                total_debit += float(row[idx["expense"]] or 0)

        return {
            "total_debit": total_debit,
            "total_credit": total_credit,
            "balance": total_debit - total_credit,
        }

    # =====================
    # Heirs Reports
    # =====================
    def get_heir_statement(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            SELECT v.id AS voucher_id,
                   v.v_date,
                   COALESCE(h.heir_name, '-') AS heir_name,
                   COALESCE(p.property_name, '-') AS property_name,
                   COALESCE(a.account_name, '-') AS account_name,
                   COALESCE(l.debit, 0) AS debit,
                   COALESCE(l.credit, 0) AS credit,
                   COALESCE(l.debit, 0) - COALESCE(l.credit, 0) AS balance
            FROM finance.ledger l
            JOIN finance.vouchers v ON v.id = l.voucher_id
            LEFT JOIN finance.heirs h ON h.id = l.heir_id
            LEFT JOIN finance.properties p ON p.id = l.property_id
            LEFT JOIN finance.accounts a ON a.account_code = l.account_code
            WHERE {where_sql}
            ORDER BY v.v_date, v.id
        """
        return self._run_report_query("كشف حساب وارث", query, params, filters)

    def get_heir_summary(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            SELECT COALESCE(h.heir_name, 'غير محدد') AS heir_name,
                   SUM(COALESCE(l.debit, 0)) AS debit,
                   SUM(COALESCE(l.credit, 0)) AS credit,
                   SUM(COALESCE(l.debit, 0) - COALESCE(l.credit, 0)) AS balance
            FROM finance.ledger l
            JOIN finance.vouchers v ON v.id = l.voucher_id
            LEFT JOIN finance.heirs h ON h.id = l.heir_id
            WHERE {where_sql}
            GROUP BY h.heir_name
            ORDER BY h.heir_name
        """
        return self._run_report_query("ملخص وارث", query, params, filters)

    def get_heir_balances(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            SELECT COALESCE(h.heir_name, 'غير محدد') AS heir_name,
                   SUM(COALESCE(l.debit, 0)) AS debit,
                   SUM(COALESCE(l.credit, 0)) AS credit,
                   SUM(COALESCE(l.debit, 0) - COALESCE(l.credit, 0)) AS balance
            FROM finance.ledger l
            JOIN finance.vouchers v ON v.id = l.voucher_id
            LEFT JOIN finance.heirs h ON h.id = l.heir_id
            WHERE {where_sql}
            GROUP BY h.heir_name
            ORDER BY balance DESC
        """
        return self._run_report_query("أرصدة الورثة", query, params, filters)

    def get_profit_distribution(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            WITH net_profit AS (
                SELECT SUM(COALESCE(l.credit, 0) - COALESCE(l.debit, 0)) AS profit
                FROM finance.ledger l
                JOIN finance.vouchers v ON v.id = l.voucher_id
                WHERE {where_sql}
            ), heirs_count AS (
                SELECT NULLIF(COUNT(*), 0) AS total_heirs FROM finance.heirs
            )
            SELECT h.heir_name,
                   COALESCE(np.profit, 0) AS total_profit,
                   COALESCE(np.profit / hc.total_heirs, 0) AS distributed_share,
                   0::numeric AS debit,
                   COALESCE(np.profit / hc.total_heirs, 0) AS credit
            FROM finance.heirs h
            CROSS JOIN net_profit np
            CROSS JOIN heirs_count hc
            ORDER BY h.heir_name
        """
        return self._run_report_query("توزيع الأرباح", query, params, filters)

    # =====================
    # Property Reports
    # =====================
    def get_property_statement(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            SELECT v.id AS voucher_id,
                   v.v_date,
                   COALESCE(p.property_name, '-') AS property_name,
                   COALESCE(a.account_name, '-') AS account_name,
                   COALESCE(l.debit, 0) AS debit,
                   COALESCE(l.credit, 0) AS credit,
                   COALESCE(l.credit, 0) - COALESCE(l.debit, 0) AS balance
            FROM finance.ledger l
            JOIN finance.vouchers v ON v.id = l.voucher_id
            LEFT JOIN finance.properties p ON p.id = l.property_id
            LEFT JOIN finance.accounts a ON a.account_code = l.account_code
            WHERE {where_sql}
            ORDER BY v.v_date, v.id
        """
        return self._run_report_query("كشف حساب عقار", query, params, filters)

    def get_property_income(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            SELECT COALESCE(p.property_name, 'غير محدد') AS property_name,
                   SUM(COALESCE(l.credit, 0)) AS credit,
                   0::numeric AS debit,
                   SUM(COALESCE(l.credit, 0)) AS balance
            FROM finance.ledger l
            JOIN finance.vouchers v ON v.id = l.voucher_id
            LEFT JOIN finance.properties p ON p.id = l.property_id
            WHERE {where_sql} AND v.v_type = 'قبض'
            GROUP BY p.property_name
            ORDER BY property_name
        """
        return self._run_report_query("إيرادات العقارات", query, params, filters)

    def get_property_expense(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            SELECT COALESCE(p.property_name, 'غير محدد') AS property_name,
                   SUM(COALESCE(l.debit, 0)) AS debit,
                   0::numeric AS credit,
                   SUM(COALESCE(l.debit, 0)) AS balance
            FROM finance.ledger l
            JOIN finance.vouchers v ON v.id = l.voucher_id
            LEFT JOIN finance.properties p ON p.id = l.property_id
            WHERE {where_sql} AND v.v_type = 'صرف'
            GROUP BY p.property_name
            ORDER BY property_name
        """
        return self._run_report_query("مصروفات العقارات", query, params, filters)

    def get_property_profit(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            SELECT COALESCE(p.property_name, 'غير محدد') AS property_name,
                   SUM(COALESCE(l.credit, 0)) AS income,
                   SUM(COALESCE(l.debit, 0)) AS expense,
                   SUM(COALESCE(l.credit, 0) - COALESCE(l.debit, 0)) AS balance
            FROM finance.ledger l
            JOIN finance.vouchers v ON v.id = l.voucher_id
            LEFT JOIN finance.properties p ON p.id = l.property_id
            WHERE {where_sql}
            GROUP BY p.property_name
            ORDER BY balance DESC
        """
        return self._run_report_query("صافي ربح العقارات", query, params, filters)

    # =====================
    # Voucher Reports
    # =====================
    def get_payment_vouchers(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            SELECT v.id AS voucher_id,
                   v.v_date,
                   COALESCE(v.description, '-') AS description,
                   COALESCE(l.debit, 0) AS debit,
                   0::numeric AS credit,
                   COALESCE(p.property_name, '-') AS property_name
            FROM finance.vouchers v
            JOIN finance.ledger l ON l.voucher_id = v.id
            LEFT JOIN finance.properties p ON p.id = l.property_id
            WHERE {where_sql} AND v.v_type = 'صرف'
            ORDER BY v.v_date, v.id
        """
        return self._run_report_query("سندات الصرف", query, params, filters)

    def get_receipt_vouchers(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            SELECT v.id AS voucher_id,
                   v.v_date,
                   COALESCE(v.description, '-') AS description,
                   0::numeric AS debit,
                   COALESCE(l.credit, 0) AS credit,
                   COALESCE(p.property_name, '-') AS property_name
            FROM finance.vouchers v
            JOIN finance.ledger l ON l.voucher_id = v.id
            LEFT JOIN finance.properties p ON p.id = l.property_id
            WHERE {where_sql} AND v.v_type = 'قبض'
            ORDER BY v.v_date, v.id
        """
        return self._run_report_query("سندات القبض", query, params, filters)

    def get_daily_vouchers(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            SELECT v.v_date,
                   COUNT(DISTINCT v.id) AS vouchers_count,
                   SUM(COALESCE(l.debit, 0)) AS debit,
                   SUM(COALESCE(l.credit, 0)) AS credit,
                   SUM(COALESCE(l.debit, 0) - COALESCE(l.credit, 0)) AS balance
            FROM finance.vouchers v
            JOIN finance.ledger l ON l.voucher_id = v.id
            WHERE {where_sql}
            GROUP BY v.v_date
            ORDER BY v.v_date
        """
        return self._run_report_query("تقرير السندات اليومي", query, params, filters)

    # =====================
    # Financial Reports
    # =====================
    def get_general_ledger(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            SELECT v.v_date,
                   v.id AS voucher_id,
                   COALESCE(a.account_code, '-') AS account_code,
                   COALESCE(a.account_name, '-') AS account_name,
                   COALESCE(l.debit, 0) AS debit,
                   COALESCE(l.credit, 0) AS credit,
                   COALESCE(l.debit, 0) - COALESCE(l.credit, 0) AS balance
            FROM finance.ledger l
            JOIN finance.vouchers v ON v.id = l.voucher_id
            LEFT JOIN finance.accounts a ON a.account_code = l.account_code
            WHERE {where_sql}
            ORDER BY v.v_date, a.account_code
        """
        return self._run_report_query("دفتر الأستاذ", query, params, filters)

    def get_trial_balance(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            SELECT COALESCE(a.account_code, '-') AS account_code,
                   COALESCE(a.account_name, '-') AS account_name,
                   SUM(COALESCE(l.debit, 0)) AS debit,
                   SUM(COALESCE(l.credit, 0)) AS credit,
                   SUM(COALESCE(l.debit, 0) - COALESCE(l.credit, 0)) AS balance
            FROM finance.ledger l
            JOIN finance.vouchers v ON v.id = l.voucher_id
            LEFT JOIN finance.accounts a ON a.account_code = l.account_code
            WHERE {where_sql}
            GROUP BY a.account_code, a.account_name
            ORDER BY a.account_code
        """
        return self._run_report_query("ميزان المراجعة", query, params, filters)

    def get_income_statement(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            SELECT COALESCE(a.account_name, '-') AS account_name,
                   SUM(CASE WHEN a.nature = 'دائن' THEN COALESCE(l.credit, 0) ELSE 0 END) AS income,
                   SUM(CASE WHEN a.nature = 'مدين' THEN COALESCE(l.debit, 0) ELSE 0 END) AS expense,
                   SUM(CASE WHEN a.nature = 'دائن' THEN COALESCE(l.credit, 0) ELSE 0 END) -
                   SUM(CASE WHEN a.nature = 'مدين' THEN COALESCE(l.debit, 0) ELSE 0 END) AS balance
            FROM finance.ledger l
            JOIN finance.vouchers v ON v.id = l.voucher_id
            LEFT JOIN finance.accounts a ON a.account_code = l.account_code
            WHERE {where_sql}
            GROUP BY a.account_name
            ORDER BY account_name
        """
        return self._run_report_query("قائمة الدخل", query, params, filters)

    def get_cash_flow(self, filters):
        where_sql, params = self._base_filters(filters)
        query = f"""
            SELECT v.v_date,
                   SUM(COALESCE(l.credit, 0)) AS cash_in,
                   SUM(COALESCE(l.debit, 0)) AS cash_out,
                   SUM(COALESCE(l.credit, 0) - COALESCE(l.debit, 0)) AS balance
            FROM finance.vouchers v
            JOIN finance.ledger l ON l.voucher_id = v.id
            WHERE {where_sql}
            GROUP BY v.v_date
            ORDER BY v.v_date
        """
        return self._run_report_query("التدفقات النقدية", query, params, filters)

    # =====================
    # Advanced Reports
    # =====================
    def filter_by_account(self, filters):
        if not filters.get("account_code"):
            raise ValueError("يرجى اختيار حساب لتنفيذ التقرير")
        return self.get_general_ledger(filters)

    def filter_by_heir(self, filters):
        if not filters.get("heir_id"):
            raise ValueError("يرجى اختيار وارث لتنفيذ التقرير")
        return self.get_heir_statement(filters)

    def filter_by_property(self, filters):
        if not filters.get("property_id"):
            raise ValueError("يرجى اختيار عقار لتنفيذ التقرير")
        return self.get_property_statement(filters)

    def compare_periods(self, filters):
        start_dt = datetime.strptime(filters["date_from"], "%Y-%m-%d").date()
        end_dt = datetime.strptime(filters["date_to"], "%Y-%m-%d").date()
        days = max((end_dt - start_dt).days, 0)

        prev_end = start_dt - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days)

        current_query = """
            SELECT SUM(COALESCE(l.debit, 0)) AS debit,
                   SUM(COALESCE(l.credit, 0)) AS credit
            FROM finance.ledger l
            JOIN finance.vouchers v ON v.id = l.voucher_id
            WHERE v.v_date BETWEEN %s AND %s
        """
        previous_query = """
            SELECT SUM(COALESCE(l.debit, 0)) AS debit,
                   SUM(COALESCE(l.credit, 0)) AS credit
            FROM finance.ledger l
            JOIN finance.vouchers v ON v.id = l.voucher_id
            WHERE v.v_date BETWEEN %s AND %s
        """

        cur_cols, cur_rows = self._run_query(current_query, [filters["date_from"], filters["date_to"]])
        _, prev_rows = self._run_query(previous_query, [prev_start.strftime("%Y-%m-%d"), prev_end.strftime("%Y-%m-%d")])

        cur_debit = float(cur_rows[0][0] or 0) if cur_rows else 0.0
        cur_credit = float(cur_rows[0][1] or 0) if cur_rows else 0.0
        prev_debit = float(prev_rows[0][0] or 0) if prev_rows else 0.0
        prev_credit = float(prev_rows[0][1] or 0) if prev_rows else 0.0

        columns = ["البند", "الفترة الحالية", "الفترة السابقة", "الفرق"]
        rows = [
            ("إجمالي المدين", cur_debit, prev_debit, cur_debit - prev_debit),
            ("إجمالي الدائن", cur_credit, prev_credit, cur_credit - prev_credit),
            ("الصافي", cur_credit - cur_debit, prev_credit - prev_debit, (cur_credit - cur_debit) - (prev_credit - prev_debit)),
        ]

        summary = {
            "total_debit": cur_debit,
            "total_credit": cur_credit,
            "balance": cur_debit - cur_credit,
        }

        return {
            "title": "مقارنة فترتين",
            "columns": columns,
            "rows": rows,
            "summary": summary,
            "date_from": filters["date_from"],
            "date_to": filters["date_to"],
        }

    def open_report(self, report_name):
        route = self.report_to_tab.get(report_name)
        if not route:
            self.notebook.select(0)
            return

        tab_key, option_name = route
        tab_index = self.tab_order.index(tab_key)
        self.notebook.select(tab_index)

        state = self.tabs[tab_key]
        if option_name in state["reports"]:
            state["report_var"].set(option_name)
        self._generate_report(tab_key)


def open_report(master, report_name):
    """Factory helper used by the main app to open a report directly."""
    screen = ReportsScreen(master)
    if report_name:
        screen.open_report(report_name)
    return screen

