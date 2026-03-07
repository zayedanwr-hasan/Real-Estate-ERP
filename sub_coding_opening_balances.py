import tkinter as tk
from tkinter import ttk, messagebox
from db_connection import get_connection

class SubCodingOpeningBalances:
    def __init__(self, master):
        self.master = master
        self.master.title("Sub-Coding and Opening Balances")
        self.master.geometry("1200x800")
        self.master.configure(bg="#f0f2f5")

        # Colors and Fonts
        self.primary_color = "#2c3e50"
        self.accent_color = "#1abc9c"
        self.light_gray = "#f0f2f5"
        self.font_header = ("Segoe UI", 16, "bold")
        self.font_label = ("Segoe UI", 10, "bold")
        self.font_data = ("Segoe UI", 11)

        # Current Vendor ID for Editing
        self.current_vendor_id = None

        # Build UI
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self.master, bg=self.primary_color, height=60)
        header.pack(fill="x")
        tk.Label(header, text="Sub-Coding and Opening Balances", bg=self.primary_color, fg="white",
                 font=self.font_header).pack(pady=15)

        # Search Bar
        search_frame = tk.Frame(self.master, bg="white", highlightthickness=1, highlightbackground="#d1d8e0")
        search_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(search_frame, text="Search:", bg="white", font=self.font_label).pack(side="left", padx=10)
        self.search_entry = tk.Entry(search_frame, font=self.font_data, bd=1, relief="solid")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh_treeview())

        # Main Content
        content_frame = tk.Frame(self.master, bg=self.light_gray)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Form Frame
        form_frame = tk.Frame(content_frame, bg="white", highlightthickness=1, highlightbackground="#d1d8e0")
        form_frame.pack(side="right", fill="y", padx=10, pady=10)
        tk.Label(form_frame, text="Vendor Details", bg="white", font=self.font_header).pack(pady=10)

        self.name_entry = self._create_form_input(form_frame, "Name:")
        self.group_entry = self._create_form_input(form_frame, "Group:")
        self.plot_combobox = self._create_form_combobox(form_frame, "Plot:")
        self.balance_entry = self._create_form_input(form_frame, "Opening Balance:")
        self.balance_entry.insert(0, "0.00")

        # Buttons
        button_frame = tk.Frame(form_frame, bg="white")
        button_frame.pack(fill="x", pady=10)
        tk.Button(button_frame, text="Save", bg=self.accent_color, fg="white", font=self.font_label,
                  command=self._save_vendor).pack(fill="x", pady=5)
        tk.Button(button_frame, text="Clear", bg="#95a5a6", fg="white", font=self.font_label,
                  command=self._clear_form).pack(fill="x", pady=5)

        # Treeview Frame
        tree_frame = tk.Frame(content_frame, bg="white", highlightthickness=1, highlightbackground="#d1d8e0")
        tree_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.tree = self._create_treeview(tree_frame)
        self.tree.bind("<Double-1>", self._on_treeview_select)

        # Load Data
        self._load_plots()
        self._refresh_treeview()

    def _create_form_input(self, parent, label_text):
        tk.Label(parent, text=label_text, bg="white", font=self.font_label).pack(anchor="w", padx=10, pady=5)
        entry = tk.Entry(parent, font=self.font_data, bd=1, relief="solid")
        entry.pack(fill="x", padx=10, pady=5)
        return entry

    def _create_form_combobox(self, parent, label_text):
        tk.Label(parent, text=label_text, bg="white", font=self.font_label).pack(anchor="w", padx=10, pady=5)
        combobox = ttk.Combobox(parent, font=self.font_data, state="readonly")
        combobox.pack(fill="x", padx=10, pady=5)
        return combobox

    def _create_treeview(self, parent):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", rowheight=25, font=self.font_data,
                        borderwidth=1)
        style.configure("Treeview.Heading", background="#ecf0f1", font=self.font_label, borderwidth=1)
        style.map("Treeview", background=[("selected", "#d1d8e0")])

        tree = ttk.Treeview(parent, columns=("id", "name", "group", "plot", "balance"), show="headings")
        tree.heading("id", text="ID")
        tree.heading("name", text="Name")
        tree.heading("group", text="Group")
        tree.heading("plot", text="Plot")
        tree.heading("balance", text="Opening Balance")
        tree.column("id", width=50, anchor="center")
        tree.column("name", width=150, anchor="center")
        tree.column("group", width=100, anchor="center")
        tree.column("plot", width=150, anchor="center")
        tree.column("balance", width=100, anchor="center")
        tree.pack(fill="both", expand=True)

        tree.tag_configure("evenrow", background="white")
        tree.tag_configure("oddrow", background="#f9f9f9")

        return tree

    def _load_plots(self):
        conn = get_connection()
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("SELECT id, plot_name FROM finance.plots")
        self.plot_combobox["values"] = [f"{row[0]} - {row[1]}" for row in cur.fetchall()]
        conn.close()

    def _refresh_treeview(self):
        self.tree.delete(*self.tree.get_children())
        search_text = self.search_entry.get()
        conn = get_connection()
        if not conn:
            return
        cur = conn.cursor()
        query = """
            SELECT v.id, v.name, v.group_name, p.plot_name, 
                   (SELECT COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0) 
                    FROM finance.ledger WHERE vendor_id = v.id)
            FROM finance.vendors v
            LEFT JOIN finance.plots p ON v.plot_id = p.id
            WHERE v.name ILIKE %s OR v.group_name ILIKE %s
            ORDER BY v.id
        """
        cur.execute(query, (f"%{search_text}%", f"%{search_text}%"))
        for i, row in enumerate(cur.fetchall()):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=row, tags=(tag,))
        conn.close()

    def _on_treeview_select(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        values = self.tree.item(selected_item[0], "values")
        self.current_vendor_id = values[0]
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, values[1])
        self.group_entry.delete(0, tk.END)
        self.group_entry.insert(0, values[2])
        self.balance_entry.delete(0, tk.END)
        self.balance_entry.insert(0, values[4])
        for plot in self.plot_combobox["values"]:
            if values[3] in plot:
                self.plot_combobox.set(plot)

    def _save_vendor(self):
        name = self.name_entry.get()
        group = self.group_entry.get()
        plot = self.plot_combobox.get()
        balance = self.balance_entry.get()

        if not name or not group or not plot:
            messagebox.showwarning("Validation Error", "All fields are required.")
            return

        plot_id = plot.split(" - ")[0]
        conn = get_connection()
        if not conn:
            return
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO finance.vendors (name, group_name, plot_id) VALUES (%s, %s, %s) RETURNING id",
                        (name, group, plot_id))
            vendor_id = cur.fetchone()[0]
            if float(balance) > 0:
                cur.execute("INSERT INTO finance.ledger (voucher_id, account_code, vendor_id, plot_id, debit, credit) "
                            "VALUES (NULL, '2101', %s, %s, %s, 0)", (vendor_id, plot_id, balance))
                cur.execute("INSERT INTO finance.ledger (voucher_id, account_code, vendor_id, plot_id, debit, credit) "
                            "VALUES (NULL, '3999', %s, %s, 0, %s)", (vendor_id, plot_id, balance))
            conn.commit()
            messagebox.showinfo("Success", "Vendor saved successfully.")
            self._refresh_treeview()
            self._clear_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()

    def _clear_form(self):
        self.current_vendor_id = None
        self.name_entry.delete(0, tk.END)
        self.group_entry.delete(0, tk.END)
        self.balance_entry.delete(0, tk.END)
        self.balance_entry.insert(0, "0.00")
        self.plot_combobox.set("")


if __name__ == "__main__":
    root = tk.Tk()
    app = SubCodingOpeningBalances(root)
    root.mainloop()
