import tkinter as tk
from tkinter import ttk, messagebox
from db_connection import get_connection

class PropertyScreen:
    def __init__(self, master):
        self.master = master
        self.frame = tk.Frame(master)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Arabic font for better RTL support
        self.arabic_font = ("Arial", 12)

        # Form fields
        self.label_name = tk.Label(self.frame, text="اسم العقار", anchor="e", font=self.arabic_font)
        self.label_name.grid(row=0, column=1, sticky="e", padx=5, pady=5)
        self.entry_name = tk.Entry(self.frame, font=self.arabic_font, justify='right')
        self.entry_name.grid(row=0, column=0, padx=5, pady=5)

        self.label_price = tk.Label(self.frame, text="سعر الشراء", anchor="e", font=self.arabic_font)
        self.label_price.grid(row=1, column=1, sticky="e", padx=5, pady=5)
        self.entry_price = tk.Entry(self.frame, font=self.arabic_font, justify='right')
        self.entry_price.grid(row=1, column=0, padx=5, pady=5)

        self.save_button = tk.Button(self.frame, text="حفظ", command=self.save_property, font=self.arabic_font)
        self.save_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Treeview for properties
        columns = ("id", "property_name", "purchase_price", "total_cost", "status")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", height=10)
        self.tree.heading("id", text="ID", anchor="e")
        self.tree.heading("property_name", text="اسم العقار", anchor="e")
        self.tree.heading("purchase_price", text="سعر الشراء", anchor="e")
        self.tree.heading("total_cost", text="التكلفة الكلية", anchor="e")
        self.tree.heading("status", text="الحالة", anchor="e")
        self.tree.column("id", anchor="e", width=60)
        self.tree.column("property_name", anchor="e", width=150)
        self.tree.column("purchase_price", anchor="e", width=100)
        self.tree.column("total_cost", anchor="e", width=100)
        self.tree.column("status", anchor="e", width=80)
        self.tree.grid(row=3, column=0, columnspan=2, padx=5, pady=10, sticky="nsew")

        self.frame.grid_rowconfigure(3, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        self.refresh_data()

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
                    for row in cur.fetchall():
                        self.tree.insert("", tk.END, values=row)
        except Exception as e:
            messagebox.showerror("خطأ في قاعدة البيانات", str(e))
        finally:
            conn.close()
