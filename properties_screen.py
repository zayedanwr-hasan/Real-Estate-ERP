import tkinter as tk
from tkinter import messagebox
from ttkbootstrap import ttk
from db_connection import get_connection


class PropertyScreen:
    def __init__(self, master):
        self.master = master
        self.primary_color = "#2c3e50"
        self.sidebar_color = "#34495e"
        self.accent_color = "#1abc9c"
        self.text_color = "#ecf0f1"
        self.separator_color = "#2c3e50"
        self.bg_color = "#f4f7f6"

        self._setup_styles()

        self.frame = ttk.Frame(master, style="Property.Root.TFrame", padding=12)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.main_card = ttk.Frame(self.frame, style="Property.Card.TFrame", padding=14)
        self.main_card.pack(fill="both", expand=True)

        self.arabic_font = ("Segoe UI", 13, "bold")

        self.form_row = ttk.Frame(self.main_card, style="Property.Card.TFrame")
        self.form_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.form_row.columnconfigure(0, weight=1)
        self.form_row.columnconfigure(2, weight=1)

        self.label_name = ttk.Label(self.form_row, text="اسم العقار", style="Property.FieldLabel.TLabel", anchor="e")
        self.label_name.grid(row=0, column=1, sticky="e", padx=8, pady=8)
        self.entry_name = ttk.Entry(self.form_row, font=self.arabic_font, justify='right')
        self.entry_name.grid(row=0, column=0, padx=8, pady=8, sticky="ew")

        self.label_price = ttk.Label(self.form_row, text="سعر الشراء", style="Property.FieldLabel.TLabel", anchor="e")
        self.label_price.grid(row=0, column=3, sticky="e", padx=8, pady=8)
        self.entry_price = ttk.Entry(self.form_row, font=self.arabic_font, justify='right')
        self.entry_price.grid(row=0, column=2, padx=8, pady=8, sticky="ew")

        self.save_button = ttk.Button(self.main_card, text="حفظ", bootstyle="success", command=self.save_property)
        self.save_button.grid(row=1, column=0, columnspan=2, pady=(0, 12), sticky="e")

        columns = ("id", "property_name", "purchase_price", "total_cost", "status")
        table_wrap = ttk.Frame(self.main_card, style="Property.Card.TFrame")
        table_wrap.grid(row=2, column=0, columnspan=2, sticky="nsew")
        table_wrap.rowconfigure(0, weight=1)
        table_wrap.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=12)
        self.tree.heading("id", text="ID", anchor="e")
        self.tree.heading("property_name", text="اسم العقار", anchor="e")
        self.tree.heading("purchase_price", text="سعر الشراء", anchor="e")
        self.tree.heading("total_cost", text="التكلفة الكلية", anchor="e")
        self.tree.heading("status", text="الحالة", anchor="e")
        self.tree.column("id", anchor="e", width=70)
        self.tree.column("property_name", anchor="e", width=220)
        self.tree.column("purchase_price", anchor="e", width=160)
        self.tree.column("total_cost", anchor="e", width=160)
        self.tree.column("status", anchor="e", width=120)

        y_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_wrap, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        self.tree.tag_configure("odd", background="#ffffff")
        self.tree.tag_configure("even", background="#f0f3f5")

        self.main_card.grid_rowconfigure(2, weight=1)
        self.main_card.grid_columnconfigure(0, weight=1)
        self.main_card.grid_columnconfigure(1, weight=1)

        self.refresh_data()

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("Property.Root.TFrame", background=self.bg_color)
        style.configure("Property.Card.TFrame", background="white", bordercolor="#d1d8e0", borderwidth=1, relief="solid")
        style.configure("Property.FieldLabel.TLabel", background="white", foreground=self.primary_color, font=("Segoe UI", 13, "bold"))
        style.configure("Treeview", rowheight=30, font=("Segoe UI", 10), background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background="#ecf0f1", foreground=self.primary_color)

    def save_property(self):
        name = self.entry_name.get().strip()
        price = self.entry_price.get().strip()
        if not name or not price:
            messagebox.showerror("خطأ", "يرجى إدخال جميع البيانات")
            return
        try:
            price_val = float(price)
        except ValueError:
            messagebox.showerror("خطأ", "سعر الشراء يجب أن يكون رقمًا")
            return
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO finance.properties (property_name, purchase_price, total_cost, status)
                        VALUES (%s, %s, %s, %s)
                    """, (name, price_val, price_val, 'نشط'))
            messagebox.showinfo("تم الحفظ", "تم إضافة العقار بنجاح")
            self.entry_name.delete(0, tk.END)
            self.entry_price.delete(0, tk.END)
            self.refresh_data()
        except Exception as e:
            messagebox.showerror("خطأ في قاعدة البيانات", str(e))
        finally:
            conn.close()

    def refresh_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, property_name, purchase_price, total_cost, status FROM finance.properties ORDER BY id DESC")
                    for idx, row in enumerate(cur.fetchall()):
                        tag = "even" if idx % 2 == 0 else "odd"
                        self.tree.insert("", tk.END, values=row, tags=(tag,))
        except Exception as e:
            messagebox.showerror("خطأ في قاعدة البيانات", str(e))
        finally:
            conn.close()
