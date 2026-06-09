"""main_window.py — النافذة الرئيسية"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
from theme_tk import TK, apply_theme, setup_treeview, fill_treeview, style_button, style_entry, make_card
from datetime import datetime
from database import Database
from printer import Printer
from reports import Reports
from ui.sales_tab import SalesTab
from ui.supplier_invoices_tab import SupplierInvoicesTab
from ui.returns_tab import ReturnsTab
from ui.expenses_tab import ExpensesTab
from ui.inventory_tab import InventoryTab
from ui.materials_tab import MaterialsTab

class AccountingSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("مكتبة الفراشات - نظام البيع وإدارة المخزون")
        self.root.geometry("1400x750")
        self.root.configure(bg=TK.BG)
        apply_theme(self.root)
        self.center_window(1400, 750)

        self.db = Database()
        self.reports = Reports(root, self.db)
        self.printer = Printer(root)

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.create_notebook()
        self.check_low_stock()
        self.setup_shortcuts()

    def _on_closing(self):
        try:
            self.db.conn.commit()
            self.db.conn.close()
        except Exception:
            pass
        self.root.destroy()

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def setup_shortcuts(self):
        self.root.bind('<F1>', lambda e: self.add_new_material())
        self.root.bind('<F3>', lambda e: self.complete_sale())
        self.root.bind('<F5>', lambda e: self.refresh_all())
        self.root.bind('<Control-d>', lambda e: self.reports.show_daily_report())
        self.root.bind('<Control-D>', lambda e: self.reports.show_daily_report())
        self.root.bind('<Control-m>', lambda e: self.reports.show_monthly_report())
        self.root.bind('<Control-M>', lambda e: self.reports.show_monthly_report())
        self.root.bind('<Control-i>', lambda e: self.reports.show_inventory_report())
        self.root.bind('<Control-I>', lambda e: self.reports.show_inventory_report())
        self.root.bind('<Control-r>', lambda e: self.open_returns())
        self.root.bind('<Control-R>', lambda e: self.open_returns())
        self.root.bind('<Control-f>', lambda e: self.focus_search())
        self.root.bind('<Control-F>', lambda e: self.focus_search())
        self.root.bind('<Control-Right>', lambda e: self.next_tab())
        self.root.bind('<Control-Left>', lambda e: self.prev_tab())

    def refresh_materials(self):
        if hasattr(self, 'sales'):
            self.sales.load_materials()
            self.sales.status_label.config(text="🔄 تم تحديث قائمة المواد")
            self.root.after(2000, lambda: self.sales.status_label.config(text="✅ جاهز - امسح الباركود"))
        if hasattr(self, 'inventory'):
            self.inventory.load_inventory()
        if hasattr(self, 'materials'):
            self.materials.load_materials()
        if hasattr(self, 'supplier_invoices'):
            self.supplier_invoices.load_invoices()

    def add_new_material(self):
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0 and hasattr(self, 'sales'):
            self.sales.add_material()
        elif current_tab == 5 and hasattr(self, 'materials'):
            self.materials.add_material()
        else:
            self.notebook.select(5)
            if hasattr(self, 'materials'):
                self.materials.add_material()

    def complete_sale(self):
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0 and hasattr(self, 'sales'):
            self.sales.complete_sale()
        else:
            self.notebook.select(0)
            if hasattr(self, 'sales'):
                self.sales.complete_sale()

    def open_returns(self):
        self.notebook.select(2)

    def refresh_all(self):
        self.refresh_materials()
        if hasattr(self, 'expenses'):
            self.expenses.load_expenses()
        if hasattr(self, 'returns'):
            self.returns.load_returns()
            self.returns.load_exchanges()
        if hasattr(self, 'supplier_invoices'):
            self.supplier_invoices.load_invoices()
        messagebox.showinfo("تحديث", "✓ تم تحديث جميع البيانات بنجاح")

    def focus_search(self):
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0 and hasattr(self, 'sales'):
            self.sales.search_entry.focus()
        elif current_tab == 3 and hasattr(self, 'inventory'):
            self.inventory.search_entry.focus()
        elif current_tab == 5 and hasattr(self, 'materials'):
            self.materials.search_entry.focus()
        elif current_tab == 1 and hasattr(self, 'supplier_invoices'):
            self.supplier_invoices.search_entry.focus()

    def next_tab(self):
        current = self.notebook.index(self.notebook.select())
        if current < len(self.notebook.tabs()) - 1:
            self.notebook.select(current + 1)

    def prev_tab(self):
        current = self.notebook.index(self.notebook.select())
        if current > 0:
            self.notebook.select(current - 1)

    def check_low_stock(self):
        low_stock = self.db.get_low_stock_materials()
        out_stock = self.db.get_out_of_stock_materials()
        message = ""
        if out_stock:
            message += "❌ المواد التي نفدت من المخزون (ممنوع البيع):\n"
            for mat in out_stock:
                message += f"   • {mat[1]} (الكمية: {mat[2]})\n"
            message += "\n"
        if low_stock:
            message += "⚠️ المواد التي وصلت للحد الأدنى:\n"
            for mat in low_stock:
                message += f"   • {mat[1]} (المتبقي: {mat[2]} / الحد الأدنى: {mat[3]})\n"
        if message:
            messagebox.showwarning("⚠️ تنبيه المخزون", message)

    def create_notebook(self):
        header = tk.Frame(self.root, bg=TK.BG3, height=55)
        header.pack(fill='x')
        tk.Label(header, text="🦋 مكتبة الفراشات", font=('Arial', 18, 'bold'),
                bg=TK.BG3, fg=TK.WHITE).pack(side='left', padx=15, pady=8)
        tk.Label(header, text="نظام البيع وإدارة المخزون", font=('Arial', 11),
                bg=TK.BG3, fg=TK.ACCENT2).pack(side='left', padx=5)

        self.time_label = tk.Label(header, font=('Arial', 10), bg=TK.ACCENT2, fg=TK.WHITE)
        self.time_label.pack(side='right', padx=15)
        self.update_clock()

        menubar = tk.Menu(self.root)
        reports_menu = tk.Menu(menubar, tearoff=0)
        reports_menu.add_command(label="📊 التقرير اليومي (Ctrl+D)", command=self.reports.show_daily_report)
        reports_menu.add_command(label="📅 التقرير الشهري (Ctrl+M)", command=self.reports.show_monthly_report)
        reports_menu.add_command(label="📦 تقرير المخزون (Ctrl+I)", command=self.reports.show_inventory_report)
        menubar.add_cascade(label="📋 تقارير", menu=reports_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="⌨️ اختصارات البرنامج", command=self.show_shortcuts)
        menubar.add_cascade(label="❓ مساعدة", menu=help_menu)
        self.root.config(menu=menubar)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)

        self.sales_tab = tk.Frame(self.notebook, bg=TK.BG)
        self.notebook.add(self.sales_tab, text="🛒 البيع")
        self.sales = SalesTab(self.sales_tab, self.db, self.reports, self.printer, self.refresh_materials)

        self.supplier_invoices_tab = tk.Frame(self.notebook, bg=TK.BG)
        self.notebook.add(self.supplier_invoices_tab, text="📄 فواتير المشتريات")
        self.supplier_invoices = SupplierInvoicesTab(self.supplier_invoices_tab, self.db, self.refresh_materials)

        self.returns_tab = tk.Frame(self.notebook, bg=TK.BG)
        self.notebook.add(self.returns_tab, text="🔄 المرتجعات والتبديلات")
        self.returns = ReturnsTab(self.returns_tab, self.db, self.refresh_materials)

        self.inventory_tab = tk.Frame(self.notebook, bg=TK.BG)
        self.notebook.add(self.inventory_tab, text="📦 المخزون")
        self.inventory = InventoryTab(self.inventory_tab, self.db, self.refresh_materials)

        self.expenses_tab = tk.Frame(self.notebook, bg=TK.BG)
        self.notebook.add(self.expenses_tab, text="💸 المصروفات")
        self.expenses = ExpensesTab(self.expenses_tab, self.db)

        self.materials_tab = tk.Frame(self.notebook, bg=TK.BG)
        self.notebook.add(self.materials_tab, text="📦 المواد")
        self.materials = MaterialsTab(self.materials_tab, self.db, self.refresh_materials)

    def update_clock(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=f"🕐 {now}")
        self.root.after(1000, self.update_clock)

    def show_shortcuts(self):
        shortcuts = """
⌨️ اختصارات لوحة المفاتيح:
  F1          : إضافة مادة جديدة
  F3          : إتمام البيع
  F5          : تحديث جميع البيانات
  Ctrl + D    : التقرير اليومي
  Ctrl + M    : التقرير الشهري
  Ctrl + I    : تقرير المخزون
  Ctrl + R    : فتح المرتجعات
  Ctrl + F    : التركيز على حقل البحث
  Ctrl + →    : التبويب التالي
  Ctrl + ←    : التبويب السابق
"""
        messagebox.showinfo("⌨️ اختصارات البرنامج", shortcuts)
