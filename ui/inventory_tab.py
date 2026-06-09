"""inventory_tab.py — تبويب المخزون"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
from theme_tk import TK, apply_theme, setup_treeview, fill_treeview, style_button, style_entry, make_card
from datetime import datetime
from database import Database

class InventoryTab:
    def __init__(self, parent, db, on_material_change=None):
        self.parent = parent
        self.db = db
        self.on_material_change = on_material_change
        self.selected_material = None
        self.create_widgets()
        self.load_inventory()

    def create_widgets(self):
        control_frame = tk.Frame(self.parent, bg=TK.CARD)
        control_frame.pack(fill='x', padx=10, pady=10)

        btn_frame = tk.Frame(control_frame, bg=TK.CARD)
        btn_frame.pack(side='left', padx=10)

        tk.Button(btn_frame, text="➕ إضافة كمية للمخزون", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 10),
                 command=self.add_quantity, padx=15, pady=5).pack(side='left', padx=5)
        tk.Button(btn_frame, text="🔄 تحديث", bg=TK.ACCENT,  fg=TK.WHITE, font=('Arial', 10),
                 command=self.load_inventory, padx=15, pady=5).pack(side='left', padx=5)
        tk.Button(btn_frame, text="⚠️ تنبيهات المخزون", bg=TK.WARNING, fg=TK.WHITE, font=('Arial', 10),
                 command=self.show_low_stock_alert, padx=15, pady=5).pack(side='left', padx=5)
        tk.Button(btn_frame, text="📊 تقرير المخزون", bg=TK.ACCENT2, fg=TK.WHITE, font=('Arial', 10),
                 command=self.show_inventory_report, padx=15, pady=5).pack(side='left', padx=5)

        search_frame = tk.Frame(self.parent, bg=TK.CARD)
        search_frame.pack(fill='x', padx=10, pady=5)
        tk.Label(search_frame, text="🔍 بحث:", bg=TK.CARD, font=('Arial', 11)).pack(side='left', padx=5)
        self.search_entry = tk.Entry(search_frame, font=('Arial', 11), width=40)
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.load_inventory())

        tree_frame = tk.Frame(self.parent, bg=TK.CARD)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        columns = ('الباركود', 'اسم المادة', 'الوحدة', 'السعر', 'الكمية', 'الحد الأدنى', 'الحالة', 'قيمة المخزون')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=18)

        col_widths = [100, 180, 70, 100, 80, 100, 100, 120]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        summary_frame = tk.Frame(self.parent, bg=TK.BG, relief='ridge', bd=1)
        summary_frame.pack(fill='x', padx=10, pady=10)

        self.summary_label = tk.Label(summary_frame, text="💰 القيمة الإجمالية للمخزون: 0",
                                       font=('Arial', 12, 'bold'), bg=TK.BG, fg=TK.SUCCESS)
        self.summary_label.pack(pady=5)

        self.low_stock_label = tk.Label(summary_frame, text="",
                                         font=('Arial', 10), bg=TK.BG, fg=TK.DANGER)
        self.low_stock_label.pack(pady=2)

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0])['values']
            self.selected_material = {
                'barcode': selected[0].replace('bc_', '', 1),  # من iid للحفاظ على الأصفار
                'name': values[1],
                'current_qty': float(values[4]) if values[4] else 0
            }

    def notify_change(self):
        if self.on_material_change:
            self.on_material_change()

    def load_inventory(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = self.search_entry.get().strip().lower()
        materials = self.db.get_all_materials()

        total_value = 0

        for mat in materials:
            barcode_str = str(mat[0])
            if search and search not in mat[1].lower() and search not in barcode_str.lower():
                continue

            stock_value = mat[5] * mat[4]
            total_value += stock_value

            if mat[5] <= 0:
                status = "❌ نفد من المخزون - ممنوع البيع"
            elif mat[5] <= mat[6]:
                status = "⚠️ كمية منخفضة"
            else:
                status = "✅ متوفر"

            display_barcode = ' ' + barcode_str  # مسافة تمنع tkinter من حذف الأصفار
            item = self.tree.insert('', 'end', iid='bc_' + barcode_str, values=(
                display_barcode, mat[1], mat[3], f"{mat[4]:.2f}", f"{mat[5]:.2f}", f"{mat[6]:.2f}", status, f"{stock_value:.2f}"
            ))

            if mat[5] <= 0:
                self.tree.tag_configure('out_of_stock', background=TK.BG3)
                self.tree.item(item, tags=('out_of_stock',))

        self.summary_label.config(text=f"💰 القيمة الإجمالية للمخزون: {total_value:.2f}")

        low_stock_materials = self.db.get_low_stock_materials()
        out_stock_materials = self.db.get_out_of_stock_materials()

        alert_text = ""
        if out_stock_materials:
            alert_text += f"❌ مواد نفدت (ممنوع البيع): {len(out_stock_materials)}  |  "
        if low_stock_materials:
            alert_text += f"⚠️ مواد منخفضة: {len(low_stock_materials)}"

        self.low_stock_label.config(text=alert_text if alert_text else "✅ جميع المواد متوفرة")

    def add_quantity(self):
        if not self.selected_material:
            messagebox.showwarning("تنبيه", "الرجاء اختيار مادة من الجدول أولاً")
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title("➕ إضافة كمية للمخزون")
        dialog.geometry("450x400")
        dialog.configure(bg=TK.CARD)
        dialog.transient(self.parent)
        dialog.grab_set()

        tk.Label(dialog, text="➕ إضافة كمية للمخزون", font=('Arial', 16, 'bold'),
                bg=TK.CARD, fg=TK.SUCCESS).pack(pady=15)

        frame = tk.Frame(dialog, bg=TK.CARD)
        frame.pack(pady=15)

        tk.Label(frame, text="اسم المادة:", bg=TK.CARD, font=('Arial', 11)).grid(row=0, column=0, padx=10, pady=10, sticky='e')
        tk.Label(frame, text=self.selected_material['name'], bg=TK.CARD, font=('Arial', 11, 'bold'), fg=TK.ACCENT2).grid(row=0, column=1, padx=10, pady=10, sticky='w')

        tk.Label(frame, text="الباركود:", bg=TK.CARD, font=('Arial', 11)).grid(row=1, column=0, padx=10, pady=10, sticky='e')
        tk.Label(frame, text=self.selected_material['barcode'], bg=TK.CARD, font=('Arial', 11)).grid(row=1, column=1, padx=10, pady=10, sticky='w')

        tk.Label(frame, text="الكمية الحالية:", bg=TK.CARD, font=('Arial', 11)).grid(row=2, column=0, padx=10, pady=10, sticky='e')
        current_qty_label = tk.Label(frame, text=str(self.selected_material['current_qty']), bg=TK.CARD, font=('Arial', 11), fg=TK.SUCCESS)
        current_qty_label.grid(row=2, column=1, padx=10, pady=10, sticky='w')

        tk.Label(frame, text="الكمية المضافة:", bg=TK.CARD, font=('Arial', 11)).grid(row=3, column=0, padx=10, pady=10, sticky='e')
        qty_entry = tk.Entry(frame, font=('Arial', 11), width=20)
        qty_entry.grid(row=3, column=1, padx=10, pady=10, sticky='w')

        tk.Label(frame, text="سعر الشراء:", bg=TK.CARD, font=('Arial', 11)).grid(row=4, column=0, padx=10, pady=10, sticky='e')
        price_entry = tk.Entry(frame, font=('Arial', 11), width=20)
        price_entry.insert(0, "0")
        price_entry.grid(row=4, column=1, padx=10, pady=10, sticky='w')

        tk.Label(frame, text="اسم التاجر:", bg=TK.CARD, font=('Arial', 11)).grid(row=5, column=0, padx=10, pady=10, sticky='e')
        trader_entry = tk.Entry(frame, font=('Arial', 11), width=20)
        trader_entry.grid(row=5, column=1, padx=10, pady=10, sticky='w')

        def save():
            try:
                add_qty = float(qty_entry.get())
                if add_qty <= 0:
                    messagebox.showerror("خطأ", "الكمية المضافة يجب أن تكون أكبر من صفر")
                    return
            except Exception:
                messagebox.showerror("خطأ", "الكمية يجب أن تكون رقماً")
                return

            try:
                purchase_price = int(price_entry.get())
            except Exception:
                purchase_price = 0

            trader = trader_entry.get().strip()
            if not trader:
                trader = "مورد خارجي"

            date = datetime.now().strftime("%Y-%m-%d")

            self.db.add_purchase(date, self.selected_material['barcode'], self.selected_material['name'],
                                add_qty, purchase_price, trader)

            new_qty = self.selected_material['current_qty'] + add_qty
            self.selected_material['current_qty'] = new_qty

            dialog.destroy()
            self.load_inventory()
            self.notify_change()
            messagebox.showinfo("نجاح", f"✓ تم إضافة {add_qty} إلى {self.selected_material['name']}\nالكمية الحالية: {new_qty}")

        tk.Button(dialog, text="💾 إضافة كمية", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 11),
                 command=save, padx=25, pady=8).pack(pady=20)

    def show_low_stock_alert(self):
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
        else:
            messagebox.showinfo("ممتاز", "✅ جميع المواد متوفرة بكميات جيدة")

    def show_inventory_report(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("تقرير المخزون")
        dialog.geometry("1000x600")
        dialog.configure(bg=TK.CARD)

        tk.Label(dialog, text="📦 تقرير المخزون الحالي", font=('Arial', 16, 'bold'),
                bg=TK.CARD, fg=TK.ACCENT2).pack(pady=15)

        frame = tk.Frame(dialog, bg=TK.CARD)
        frame.pack(fill='both', expand=True, padx=15, pady=10)

        columns = ('الباركود', 'اسم المادة', 'الوحدة', 'السعر', 'الكمية', 'الحد الأدنى', 'الحالة')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=20)

        col_widths = [100, 200, 80, 100, 80, 100, 120]
        for col, width in zip(columns, col_widths):
            tree.heading(col, text=col)
            tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        materials = self.db.get_all_materials()
        total_value = 0

        for mat in materials:
            stock_value = mat[5] * mat[4]
            total_value += stock_value

            if mat[5] <= 0:
                status = "❌ نفد من المخزون - ممنوع البيع"
            elif mat[5] <= mat[6]:
                status = "⚠️ كمية منخفضة"
            else:
                status = "✅ متوفر"

            barcode_str = str(mat[0])
            tree.insert('', 'end', iid='bc_' + barcode_str, values=(
                ' ' + barcode_str, mat[1], mat[3], f"{mat[4]:.2f}", f"{mat[5]:.2f}", f"{mat[6]:.2f}", status
            ))

        summary_frame = tk.Frame(dialog, bg=TK.BG, relief='ridge', bd=1)
        summary_frame.pack(fill='x', padx=15, pady=10)

        tk.Label(summary_frame, text=f"💰 القيمة الإجمالية للمخزون: {total_value:.2f}", font=('Arial', 12, 'bold'),
                bg=TK.BG, fg=TK.SUCCESS).pack(side='left', padx=20, pady=8)

        low_stock = self.db.get_low_stock_materials()
        tk.Label(summary_frame, text=f"⚠️ مواد أقل من الحد الأدنى: {len(low_stock)}", font=('Arial', 12, 'bold'),
                bg=TK.BG, fg=TK.WARNING).pack(side='left', padx=20, pady=8)

        out_stock = self.db.get_out_of_stock_materials()
        tk.Label(summary_frame, text=f"❌ مواد نفدت (ممنوع البيع): {len(out_stock)}", font=('Arial', 12, 'bold'),
                bg=TK.BG, fg=TK.DANGER).pack(side='left', padx=20, pady=8)

        tk.Button(dialog, text="إغلاق", bg=TK.DANGER,  fg=TK.WHITE, command=dialog.destroy, padx=20, pady=5).pack(pady=10)

