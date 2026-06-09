"""sales_tab.py — تبويب المبيعات"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
from theme_tk import TK, apply_theme, setup_treeview, fill_treeview, style_button, style_entry, make_card
from tkinter import simpledialog, filedialog
import pandas as pd
from datetime import datetime
from database import Database, round_to_500
from printer import Printer
from reports import Reports
from config import BASE_DIR

class SalesTab:
    def __init__(self, parent, db, reports, printer, on_material_change=None):
        self.parent = parent
        self.db = db
        self.reports = reports
        self.printer = printer
        self.on_material_change = on_material_change
        self.cart = []
        self.scan_buffer = ""
        self.current_invoice = self.db.get_next_invoice_number()

        self.create_widgets()
        self.load_materials()
        self.setup_barcode_scanner()

    def create_widgets(self):
        scan_frame = tk.Frame(self.parent, bg=TK.BG, pady=6)
        scan_frame.pack(fill='x', padx=15, pady=5)

        scan_box = tk.Frame(scan_frame, bg=TK.BG3, relief='ridge', bd=2)
        scan_box.pack(pady=3, fill='x')

        tk.Label(scan_box, text="📷", font=('Arial', 16), bg=TK.BG3).pack(side='left', padx=10, pady=5)
        tk.Label(scan_box, text="مسح الباركود", font=('Arial', 12, 'bold'), bg=TK.BG3, fg=TK.ACCENT2).pack(side='left', padx=3)

        self.quick_barcode = tk.Entry(scan_box, font=('Arial', 13), width=22, bg=TK.CARD, relief='sunken')
        self.quick_barcode.pack(side='left', padx=10, pady=6)
        self.quick_barcode.focus()
        tk.Label(scan_box, text="(ادخل الباركود أو امسح)", font=('Arial', 9), bg=TK.BG3, fg=TK.TEXT_SUB).pack(side='left', padx=5)

        main_frame = tk.Frame(self.parent, bg=TK.BG)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)

        left_frame = tk.LabelFrame(main_frame, text="📦 قائمة المواد", font=('Arial', 12, 'bold'),
                                    bg=TK.CARD, fg=TK.ACCENT2, padx=8, pady=5)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))

        search_frame = tk.Frame(left_frame, bg=TK.CARD)
        search_frame.pack(fill='x', pady=3)
        tk.Label(search_frame, text="🔍 بحث:", bg=TK.CARD, font=('Arial', 10)).pack(side='left', padx=3)
        self.search_entry = tk.Entry(search_frame, font=('Arial', 10), width=28)
        self.search_entry.pack(side='left', padx=3)
        self.search_entry.bind('<KeyRelease>', lambda e: self.load_materials())

        tree_frame = tk.Frame(left_frame, bg=TK.CARD)
        tree_frame.pack(fill='both', expand=True, pady=5)

        columns = ('الباركود', 'اسم المادة', 'التاجر', 'الوحدة', 'السعر', 'الكمية')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=14)

        col_widths = [100, 150, 100, 70, 80, 80]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.bind('<Double-1>', self.add_to_cart)

        btn_frame = tk.Frame(left_frame, bg=TK.CARD)
        btn_frame.pack(fill='x', pady=5)
        tk.Button(btn_frame, text="➕ إضافة مادة", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 9),
                 command=self.add_material, padx=12, pady=3).pack(side='left', padx=3)
        tk.Button(btn_frame, text="✏️ تعديل", bg=TK.WARNING, fg=TK.WHITE, font=('Arial', 9),
                 command=self.edit_material, padx=12, pady=3).pack(side='left', padx=3)
        tk.Button(btn_frame, text="🗑️ حذف", bg=TK.DANGER,  fg=TK.WHITE, font=('Arial', 9),
                 command=self.delete_material, padx=12, pady=3).pack(side='left', padx=3)
        tk.Button(btn_frame, text="📥 استيراد Excel", bg=TK.ACCENT,  fg=TK.WHITE, font=('Arial', 9),
                 command=self.import_from_excel, padx=12, pady=3).pack(side='left', padx=3)

        right_frame = tk.LabelFrame(main_frame, text="🛒 سلة الفاتورة", font=('Arial', 12, 'bold'),
                                     bg=TK.CARD, fg=TK.ACCENT2, padx=8, pady=5)
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        info_frame = tk.Frame(right_frame, bg=TK.CARD)
        info_frame.pack(fill='x', pady=3)
        self.invoice_label = tk.Label(info_frame, text=f"🧾 رقم الفاتورة: {self.current_invoice}",
                                       font=('Arial', 11, 'bold'), bg=TK.CARD, fg=TK.SUCCESS)
        self.invoice_label.pack(side='left', padx=5)
        self.date_label = tk.Label(info_frame, text=f"📅 {datetime.now().strftime('%Y-%m-%d')}",
                                    font=('Arial', 9), bg=TK.CARD)
        self.date_label.pack(side='right', padx=5)

        customer_frame = tk.Frame(right_frame, bg=TK.CARD)
        customer_frame.pack(fill='x', pady=3)
        tk.Label(customer_frame, text="👤 اسم العميل:", bg=TK.CARD, font=('Arial', 10)).pack(side='right', padx=3)
        self.customer_entry = tk.Entry(customer_frame, font=('Arial', 10), width=22)
        self.customer_entry.pack(side='right', padx=3)

        # ── زر تحديث الأسعار حسب سعر الدولار ──────────────────────
        dollar_frame = tk.Frame(right_frame, bg=TK.BG3, relief='ridge', bd=1)
        dollar_frame.pack(fill='x', pady=4)

        # عنوان القسم
        dollar_title = tk.Frame(dollar_frame, bg=TK.BG3)
        dollar_title.pack(fill='x')
        tk.Label(dollar_title, text="💵  تحديث الأسعار حسب سعر الصرف",
                 font=('Arial', 9, 'bold'), bg=TK.BG3, fg=TK.WHITE).pack(pady=3)

        # صف الإدخال
        dollar_row = tk.Frame(dollar_frame, bg=TK.BG3)
        dollar_row.pack(fill='x', padx=8, pady=6)

        # سعر الدولار القديم
        tk.Label(dollar_row, text="السعر القديم:", bg=TK.BG3,
                 font=('Arial', 9, 'bold'), fg=TK.SUCCESS).pack(side='right', padx=(8, 2))
        self.dollar_old_var = tk.StringVar(value="")
        tk.Entry(dollar_row, textvariable=self.dollar_old_var,
                 font=('Arial', 11, 'bold'), width=9, justify='center',
                 bg=TK.BG3, fg=TK.WARNING, relief='solid', bd=1
                 ).pack(side='right', padx=2)

        tk.Label(dollar_row, text="→", bg=TK.BG3,
                 font=('Arial', 12, 'bold'), fg=TK.SUCCESS).pack(side='right', padx=4)

        # سعر الدولار الجديد
        tk.Label(dollar_row, text="السعر الجديد:", bg=TK.BG3,
                 font=('Arial', 9, 'bold'), fg=TK.SUCCESS).pack(side='right', padx=(4, 2))
        self.dollar_new_var = tk.StringVar(value="")
        tk.Entry(dollar_row, textvariable=self.dollar_new_var,
                 font=('Arial', 11, 'bold'), width=9, justify='center',
                 bg=TK.BG3, fg=TK.SUCCESS, relief='solid', bd=1
                 ).pack(side='right', padx=2)

        # معاينة النسبة
        self.dollar_preview_var = tk.StringVar(value="")
        tk.Label(dollar_row, textvariable=self.dollar_preview_var,
                 bg=TK.BG3, font=('Arial', 9), fg=TK.TEXT_SUB).pack(side='left', padx=8)

        def update_preview(*_):
            try:
                old = float(self.dollar_old_var.get())
                new = float(self.dollar_new_var.get())
                if old > 0 and new > 0:
                    ratio = new / old
                    change = (ratio - 1) * 100
                    sign = "▲" if change >= 0 else "▼"
                    color = "#c62828" if change >= 0 else "#1565c0"
                    self.dollar_preview_var.set(f"{sign} {abs(change):.1f}%  (×{ratio:.4f})")
                else:
                    self.dollar_preview_var.set("")
            except (ValueError, ZeroDivisionError):
                self.dollar_preview_var.set("")

        self.dollar_old_var.trace_add('write', update_preview)
        self.dollar_new_var.trace_add('write', update_preview)

        def apply_dollar_rate():
            try:
                old_rate = float(self.dollar_old_var.get())
                new_rate = float(self.dollar_new_var.get())
                if old_rate <= 0 or new_rate <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("خطأ",
                    "يرجى إدخال سعر الدولار القديم والجديد بشكل صحيح\n"
                    "مثال: القديم = 8000  ←  الجديد = 10000")
                return

            ratio = new_rate / old_rate
            change_pct = (ratio - 1) * 100
            direction = f"زيادة {change_pct:.1f}%" if change_pct >= 0 else f"انخفاض {abs(change_pct):.1f}%"

            # جلب المواد المرتبطة بالدولار فقط
            linked_barcodes = self.db.get_dollar_linked_barcodes()
            cursor = self.db.conn.cursor()
            if linked_barcodes:
                placeholders = ','.join('?' * len(linked_barcodes))
                cursor.execute(f"SELECT barcode, name, sell_price FROM materials WHERE barcode IN ({placeholders})", list(linked_barcodes))
            else:
                cursor.execute("SELECT barcode, name, sell_price FROM materials")
            materials = cursor.fetchall()

            if not materials:
                messagebox.showwarning("تنبيه", "لا توجد مواد مرتبطة بالدولار للتحديث.\nاستخدم زر '⚙️ تحديد منتجات الدولار' أولاً.")
                return

            # دالة التقريب: تقريب لأقرب 500
            def syrian_round(price):
                import math
                return round_to_500(price)

            # بناء رسالة التأكيد مع أمثلة
            preview_lines = ""
            for bc, nm, sp in materials[:3]:
                new_sp = syrian_round(sp * ratio)
                preview_lines += f"   • {nm[:18]}: {sp:,} → {new_sp:,} ل.س\n"
            if len(materials) > 3:
                preview_lines += f"   ... و{len(materials)-3} مادة أخرى\n"

            scope_note = f"({len(materials)} مادة مرتبطة بالدولار)" if linked_barcodes else f"(جميع المواد - {len(materials)} مادة)"

            confirm_msg = (
                f"📊 سعر الدولار:\n"
                f"   القديم: {old_rate:,.0f} ل.س\n"
                f"   الجديد: {new_rate:,.0f} ل.س\n"
                f"   النسبة: {direction}\n\n"
                f"🔄 أمثلة على التحديث:\n"
                f"{preview_lines}\n"
                f"هل تريد تحديث الأسعار {scope_note}؟"
            )

            if not messagebox.askyesno("تأكيد تحديث الأسعار", confirm_msg):
                return

            for bc, nm, sp in materials:
                new_sp = syrian_round(sp / old_rate * new_rate)
                cursor.execute("UPDATE materials SET sell_price=? WHERE barcode=?", (new_sp, bc))
            self.db.conn.commit()

            self.load_materials()
            for item in self.cart:
                mat = self.db.get_material_by_barcode(item['barcode'])
                if mat:
                    item['price'] = mat[4]
                    item['total'] = item['quantity'] * mat[4]
            self.update_cart_display()

            self.dollar_old_var.set("")
            self.dollar_new_var.set("")

            messagebox.showinfo("تم ✅",
                f"✓ تم تحديث أسعار {len(materials)} مادة بنجاح\n"
                f"📈 نسبة التغيير: {direction}\n"
                f"💱 {old_rate:,.0f} → {new_rate:,.0f} ل.س")

        def manage_dollar_products():
            """نافذة لاختيار المنتجات المرتبطة بالدولار"""
            win = tk.Toplevel(self.parent)
            win.title("⚙️ تحديد منتجات الدولار")
            win.geometry("560x560")
            win.configure(bg=TK.CARD)
            win.transient(self.parent)
            win.grab_set()
            win.update_idletasks()
            sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
            win.geometry(f"560x560+{(sw-560)//2}+{(sh-560)//2}")

            tk.Label(win, text="⚙️ تحديد منتجات الدولار", font=('Arial', 14, 'bold'),
                     bg=TK.CARD, fg=TK.SUCCESS).pack(pady=10)
            tk.Label(win, text="اختر المنتجات التي سيتم تحديث أسعارها عند تغيير سعر الدولار.\nإذا لم تختر أي منتج سيتم تحديث جميع المنتجات.",
                     font=('Arial', 9), bg=TK.CARD, fg=TK.TEXT_SUB, justify='center').pack()

            linked = self.db.get_dollar_linked_barcodes()
            materials = self.db.get_all_materials()

            search_var = tk.StringVar()

            top_f = tk.Frame(win, bg=TK.CARD)
            top_f.pack(fill='x', padx=15, pady=5)
            tk.Label(top_f, text="🔍 بحث:", bg=TK.CARD, font=('Arial', 10)).pack(side='left')
            search_entry = tk.Entry(top_f, textvariable=search_var, font=('Arial', 10), width=20)
            search_entry.pack(side='left', padx=5)

            # أزرار تحديد الكل / إلغاء الكل
            def select_all():
                for cb_var in cb_vars:
                    cb_var.set(True)
            def deselect_all():
                for cb_var in cb_vars:
                    cb_var.set(False)

            btn_top = tk.Frame(top_f, bg=TK.CARD)
            btn_top.pack(side='right')
            tk.Button(btn_top, text="✅ تحديد الكل", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 8),
                      command=select_all, padx=8, pady=2).pack(side='left', padx=3)
            tk.Button(btn_top, text="❌ إلغاء الكل", bg=TK.DANGER,  fg=TK.WHITE, font=('Arial', 8),
                      command=deselect_all, padx=8, pady=2).pack(side='left', padx=3)

            list_frame = tk.Frame(win, bg=TK.CARD, relief='ridge', bd=1)
            list_frame.pack(fill='both', expand=True, padx=15, pady=5)

            canvas = tk.Canvas(list_frame, bg=TK.CARD)
            scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=canvas.yview)
            scroll_frame = tk.Frame(canvas, bg=TK.CARD)
            scroll_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
            canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')

            cb_vars = []
            cb_widgets = []
            cb_labels = []

            for mat in materials:
                var = tk.BooleanVar(value=(mat[0] in linked))
                cb = tk.Checkbutton(scroll_frame, text=f"{mat[1]}  ({mat[0]})",
                                    variable=var, bg=TK.CARD, font=('Arial', 10),
                                    anchor='w', justify='left')
                cb.pack(fill='x', padx=10, pady=1)
                cb_vars.append(var)
                cb_widgets.append(cb)
                cb_labels.append(f"{mat[1].lower()} {mat[0].lower()}")

            def filter_list(*_):
                q = search_var.get().lower()
                for i, cb in enumerate(cb_widgets):
                    if q in cb_labels[i]:
                        cb.pack(fill='x', padx=10, pady=1)
                    else:
                        cb.pack_forget()

            search_var.trace_add('write', filter_list)

            def save_selection():
                selected = [materials[i][0] for i, var in enumerate(cb_vars) if var.get()]
                self.db.set_dollar_linked_products(selected)
                count = len(selected)
                if count == 0:
                    msg = "✅ تم الحفظ - سيتم تحديث جميع المنتجات عند تغيير سعر الدولار"
                else:
                    msg = f"✅ تم حفظ {count} منتج مرتبط بالدولار"
                messagebox.showinfo("تم", msg, parent=win)
                win.destroy()

            tk.Button(win, text="💾 حفظ الاختيار", bg=TK.BG3, fg=TK.WHITE,
                      font=('Arial', 11, 'bold'), command=save_selection,
                      padx=20, pady=6).pack(pady=10)

        # زر تحديد منتجات الدولار - يُضاف داخل dollar_row
        tk.Button(dollar_row, text="⚙️ منتجات الدولار", bg=TK.SUCCESS, fg=TK.WHITE,
                  font=('Arial', 8, 'bold'), relief='flat', cursor='hand2',
                  padx=6, pady=5, command=manage_dollar_products).pack(side='right', padx=4)

        tk.Button(dollar_row, text="⚡ تحديث الأسعار", bg=TK.SUCCESS, fg=TK.WHITE,
                  font=('Arial', 9, 'bold'), relief='flat', cursor='hand2',
                  padx=10, pady=5, command=apply_dollar_rate).pack(side='right', padx=8)

        cart_frame = tk.Frame(right_frame, bg=TK.CARD)
        cart_frame.pack(fill='both', expand=True, pady=5)

        cart_columns = ('الباركود', 'المنتج', 'الوحدة', 'الكمية', 'السعر', 'الإجمالي')
        self.cart_tree = ttk.Treeview(cart_frame, columns=cart_columns, show='headings', height=8)

        cart_widths = [80, 130, 60, 60, 70, 80]
        for col, width in zip(cart_columns, cart_widths):
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=width)

        cart_scroll = ttk.Scrollbar(cart_frame, orient='vertical', command=self.cart_tree.yview)
        self.cart_tree.configure(yscrollcommand=cart_scroll.set)
        self.cart_tree.pack(side='left', fill='both', expand=True)
        cart_scroll.pack(side='right', fill='y')

        totals_frame = tk.Frame(right_frame, bg=TK.CARD)
        totals_frame.pack(fill='x', pady=5)

        row1 = tk.Frame(totals_frame, bg=TK.CARD)
        row1.pack(fill='x', pady=2)
        tk.Label(row1, text="🎁 الخصم (%):", bg=TK.CARD, font=('Arial', 10)).pack(side='right', padx=3)
        self.discount_entry = tk.Entry(row1, width=8, font=('Arial', 10), justify='center')
        self.discount_entry.pack(side='right', padx=3)
        self.discount_entry.insert(0, "0")
        self.discount_entry.bind('<KeyRelease>', lambda e: self.calculate_total())

        row2 = tk.Frame(totals_frame, bg=TK.CARD)
        row2.pack(fill='x', pady=2)
        tk.Label(row2, text="💰 الإجمالي:", font=('Arial', 12, 'bold'), bg=TK.CARD, fg=TK.DANGER).pack(side='right', padx=3)
        self.total_label = tk.Label(row2, text="0", font=('Arial', 13, 'bold'), bg=TK.CARD, fg=TK.DANGER)
        self.total_label.pack(side='right', padx=5)

        row3 = tk.Frame(totals_frame, bg=TK.CARD)
        row3.pack(fill='x', pady=2)
        tk.Label(row3, text="💵 المدفوع:", bg=TK.CARD, font=('Arial', 10)).pack(side='right', padx=3)
        self.paid_entry = tk.Entry(row3, width=12, font=('Arial', 10), justify='center')
        self.paid_entry.pack(side='right', padx=3)
        self.paid_entry.insert(0, str(self.total_label.cget('text')))
        self.paid_entry.bind('<KeyRelease>', self.calculate_total)
        tk.Label(row3, text="📋 المتبقي:", bg=TK.CARD, font=('Arial', 10)).pack(side='right', padx=3)
        self.remaining_label = tk.Label(row3, text="0", font=('Arial', 11, 'bold'), bg=TK.CARD, fg=TK.SUCCESS)
        self.remaining_label.pack(side='right', padx=3)

        button_frame = tk.Frame(right_frame, bg=TK.CARD)
        button_frame.pack(fill='x', pady=5)
        tk.Button(button_frame, text="💰 إتمام البيع (F3)", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 11, 'bold'),
                 command=self.complete_sale, padx=15, pady=6).pack(side='left', padx=3, expand=True, fill='x')
        tk.Button(button_frame, text="🗑️ تفريغ السلة", bg=TK.DANGER,  fg=TK.WHITE, font=('Arial', 9),
                 command=self.clear_cart, padx=10, pady=4).pack(side='right', padx=3)

        self.status_label = tk.Label(self.parent, text="✅ جاهز - امسح الباركود",
                                      bg=TK.BG3, fg=TK.TEXT, font=('Arial', 9), pady=4)
        self.status_label.pack(side='bottom', fill='x')

        self.cart_tree.bind('<Delete>', self.delete_selected_item)

    def delete_selected_item(self, event):
        selected = self.cart_tree.selection()
        if selected:
            item_index = self.cart_tree.index(selected[0])
            if item_index < len(self.cart):
                del self.cart[item_index]
                self.update_cart_display()
                self.status_label.config(text="🗑️ تم حذف العنصر من السلة")
                self.parent.after(2000, lambda: self.status_label.config(text="✅ جاهز - امسح الباركود"))

    def load_materials(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = self.search_entry.get() if hasattr(self, 'search_entry') else ""
        materials = self.db.get_all_materials()

        for mat in materials:
            if search.lower() in mat[1].lower() or search.lower() in mat[0].lower():
                item = self.tree.insert('', 'end', values=(mat[0], mat[1], mat[2] if mat[2] else '-', mat[3], mat[4], mat[5]))
                if mat[5] <= 0:
                    self.tree.tag_configure('out_of_stock', background=TK.BG3)
                    self.tree.item(item, tags=('out_of_stock',))

    def setup_barcode_scanner(self):
        def on_key_press(event):
            if event.widget == self.quick_barcode:
                return
            if event.widget == self.search_entry:
                return
            if event.widget == self.customer_entry:
                return
            if event.widget == self.discount_entry:
                return
            if event.widget == self.paid_entry:
                return
            if event.char.isdigit():
                self.scan_buffer += event.char
                self.parent.after(300, self.process_barcode)

        def on_enter(event):
            if event.widget == self.quick_barcode:
                barcode = self.quick_barcode.get()
                if barcode:
                    self.add_by_barcode(barcode)
                    self.quick_barcode.delete(0, tk.END)

        self.parent.bind('<Key>', on_key_press)
        self.quick_barcode.bind('<Return>', on_enter)

    def process_barcode(self):
        if self.scan_buffer:
            self.add_by_barcode(self.scan_buffer)
            self.scan_buffer = ""

    def _cart_qty_for(self, barcode):
        return sum(item['quantity'] for item in self.cart if item['barcode'] == barcode)

    def add_by_barcode(self, barcode):
        material = self.db.get_material_by_barcode(barcode)

        if material:
            stock_qty    = material[5]
            in_cart_qty  = self._cart_qty_for(barcode)
            available    = stock_qty - in_cart_qty

            if stock_qty <= 0:
                messagebox.showerror("خطأ",
                    f"⚠️ {material[1]} غير متوفر في المخزون!\n"
                    f"الكمية الحالية: {stock_qty}\nلا يمكن بيع هذا المنتج حالياً.")
                self.parent.bell()
                return

            if available <= 0:
                messagebox.showerror("تجاوز الكمية",
                    f"⚠️ لا يمكن إضافة المزيد من: {material[1]}\n"
                    f"الكمية في المخزون: {stock_qty}\n"
                    f"الكمية في السلة بالفعل: {in_cart_qty}\n"
                    f"لا يوجد مخزون إضافي.")
                self.parent.bell()
                return

            for item in self.cart:
                if item['barcode'] == barcode:
                    item['quantity'] += 1
                    item['total']     = item['quantity'] * item['price']
                    self.update_cart_display()
                    self.parent.bell()
                    self.status_label.config(
                        text=f"✅ تم تحديث: {material[1]} ×{item['quantity']}  (متبقي في المخزون: {available-1})")
                    self.parent.after(3000, lambda: self.status_label.config(text="✅ جاهز - امسح الباركود"))
                    return

            self.cart.append({
                'barcode': material[0],
                'name':    material[1],
                'unit':    material[3],
                'quantity': 1,
                'price':   material[4],
                'total':   material[4]
            })
            self.update_cart_display()
            self.parent.bell()
            self.status_label.config(
                text=f"✅ تم إضافة: {material[1]}  (متبقي في المخزون: {available-1})")
            self.parent.after(3000, lambda: self.status_label.config(text="✅ جاهز - امسح الباركود"))
        else:
            if messagebox.askyesno("❗ منتج غير موجود",
                    f"❌ الباركود {barcode} غير مسجل\n\nهل تريد إضافته الآن؟"):
                self.add_new_material_from_barcode(barcode)

    def add_new_material_from_barcode(self, barcode):
        dialog = tk.Toplevel(self.parent)
        dialog.title("➕ إضافة مادة جديدة")
        dialog.geometry("500x550")
        dialog.configure(bg=TK.CARD)
        dialog.transient(self.parent)
        dialog.grab_set()

        tk.Label(dialog, text="➕ إضافة مادة جديدة", font=('Arial', 16, 'bold'),
                bg=TK.CARD, fg=TK.ACCENT2).pack(pady=15)

        frame = tk.Frame(dialog, bg=TK.CARD)
        frame.pack(pady=10)

        labels = ['📦 الباركود', '📝 اسم المادة', '🏢 اسم التاجر', '📏 الوحدة', '💰 السعر', '📦 الكمية الابتدائية', '⚠️ الحد الأدنى']
        entries = {}

        for i, label in enumerate(labels):
            tk.Label(frame, text=label + ":", bg=TK.CARD, font=('Arial', 11)).grid(row=i, column=0, padx=10, pady=8, sticky='e')
            entry = tk.Entry(frame, font=('Arial', 11), width=25)
            entry.grid(row=i, column=1, padx=10, pady=8)
            entries[label] = entry

        entries['📦 الباركود'].insert(0, barcode)
        entries['📦 الباركود'].config(state='readonly')
        entries['📦 الكمية الابتدائية'].insert(0, "0")
        entries['⚠️ الحد الأدنى'].insert(0, "5")

        units = ['piece', 'carton', 'meter', 'kg']
        entries['📏 الوحدة'].delete(0, tk.END)
        entries['📏 الوحدة'].insert(0, 'piece')

        def save():
            name = entries['📝 اسم المادة'].get().strip()
            trader = entries['🏢 اسم التاجر'].get().strip()
            unit = entries['📏 الوحدة'].get()

            try:
                price = round_to_500(int(float(entries['💰 السعر'].get().replace(',', '').strip())))
            except Exception:
                messagebox.showerror("خطأ", "السعر يجب أن يكون رقماً")
                return

            try:
                quantity = float(entries['📦 الكمية الابتدائية'].get())
            except Exception:
                quantity = 0

            try:
                min_qty = float(entries['⚠️ الحد الأدنى'].get())
            except Exception:
                min_qty = 5

            if not name:
                messagebox.showerror("خطأ", "اسم المادة مطلوب")
                return

            success, msg = self.db.add_material(barcode, name, trader, unit, price, quantity, min_qty)
            messagebox.showinfo("نتيجة", msg)
            if success:
                dialog.destroy()
                self.load_materials()
                if self.on_material_change:
                    self.on_material_change()
                if quantity > 0:
                    self.add_by_barcode(barcode)

        tk.Button(dialog, text="💾 حفظ وإضافة إلى السلة", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 11),
                 command=save, padx=25, pady=8).pack(pady=20)

    def add_to_cart(self, event):
        if not self.tree.selection():
            return

        selected       = self.tree.selection()[0]
        values         = self.tree.item(selected, 'values')

        if not values or len(values) < 6:
            return

        barcode        = values[0]
        material_name  = values[1]
        stock_qty      = float(values[5])
        material_price = float(values[4])
        in_cart_qty    = self._cart_qty_for(barcode)
        available      = stock_qty - in_cart_qty

        if stock_qty <= 0:
            messagebox.showerror("خطأ",
                f"⚠️ المادة {material_name} غير متوفرة في المخزون!\n"
                f"الكمية المتوفرة: {stock_qty}\nلا يمكن بيع هذا المنتج حالياً.")
            self.parent.bell()
            return

        if available <= 0:
            messagebox.showerror("تجاوز الكمية",
                f"⚠️ لا يمكن إضافة المزيد من: {material_name}\n"
                f"الكمية في المخزون: {stock_qty}\n"
                f"الكمية في السلة بالفعل: {in_cart_qty}\n"
                f"لا يوجد مخزون إضافي.")
            self.parent.bell()
            return

        qty_window = tk.Toplevel(self.parent)
        qty_window.title("إدخال الكمية")
        qty_window.geometry("320x260")
        qty_window.configure(bg=TK.CARD)
        qty_window.transient(self.parent)
        qty_window.grab_set()

        qty_window.update_idletasks()
        x = (qty_window.winfo_screenwidth()  // 2) - 160
        y = (qty_window.winfo_screenheight() // 2) - 130
        qty_window.geometry(f"+{x}+{y}")

        tk.Label(qty_window, text=f"أدخل كمية {material_name}",
                 font=('Arial', 12, 'bold'), bg=TK.CARD, fg=TK.ACCENT2).pack(pady=12)

        info_frame = tk.Frame(qty_window, bg=TK.CARD)
        info_frame.pack()
        tk.Label(info_frame, text=f"المخزون الكلي: {stock_qty}",
                 font=('Arial', 10), bg=TK.CARD, fg=TK.TEXT_SUB).pack()
        if in_cart_qty > 0:
            tk.Label(info_frame, text=f"في السلة بالفعل: {in_cart_qty}",
                     font=('Arial', 10), bg=TK.CARD, fg=TK.WARNING).pack()
        tk.Label(info_frame, text=f"المتاح للإضافة: {available}",
                 font=('Arial', 11, 'bold'), bg=TK.CARD, fg=TK.SUCCESS).pack()

        qty_var   = tk.StringVar()
        qty_entry = tk.Entry(qty_window, textvariable=qty_var, font=('Arial', 14), width=15, justify='center')
        qty_entry.pack(pady=12)
        qty_entry.focus()

        error_label = tk.Label(qty_window, text="", fg=TK.DANGER, bg=TK.CARD, font=('Arial', 9))
        error_label.pack()

        def confirm():
            try:
                qty = float(qty_var.get())
                if qty <= 0:
                    error_label.config(text="⚠️ الكمية يجب أن تكون أكبر من صفر")
                    return
                if qty > available:
                    error_label.config(
                        text=f"⚠️ الكمية المطلوبة ({qty}) أكبر من المتاح ({available})")
                    self.parent.bell()
                    return
            except ValueError:
                error_label.config(text="⚠️ يرجى إدخال رقم صحيح")
                return

            for item in self.cart:
                if item['barcode'] == barcode:
                    item['quantity'] += qty
                    item['total']     = item['quantity'] * item['price']
                    self.update_cart_display()
                    self.parent.bell()
                    qty_window.destroy()
                    return

            self.cart.append({
                'barcode':  barcode,
                'name':     material_name,
                'unit':     values[3],
                'quantity': qty,
                'price':    material_price,
                'total':    qty * material_price
            })
            self.update_cart_display()
            self.parent.bell()
            qty_window.destroy()

        btn_frame = tk.Frame(qty_window, bg=TK.CARD)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="تأكيد", bg=TK.SUCCESS, fg=TK.WHITE,
                  font=('Arial', 11), command=confirm, padx=15, pady=3).pack(side='left', padx=10)
        tk.Button(btn_frame, text="إلغاء", bg=TK.DANGER,  fg=TK.WHITE,
                  font=('Arial', 11), command=qty_window.destroy, padx=15, pady=3).pack(side='left', padx=10)

        qty_entry.bind('<Return>', lambda event: confirm())

    def update_cart_display(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)

        for item in self.cart:
            self.cart_tree.insert('', 'end', values=(
                item['barcode'], item['name'], item['unit'],
                f"{item['quantity']:.2f}", f"{item['price']:.2f}", f"{item['total']:.2f}"
            ))

        self.calculate_total()

    def calculate_total(self, event=None):
        subtotal = sum(item['total'] for item in self.cart)
        try:
            discount_percent = float(self.discount_entry.get())
        except Exception:
            discount_percent = 0
        discount_amount = subtotal * discount_percent / 100
        total = subtotal - discount_amount
        self.total_label.config(text=f"{total:.2f}")
        try:
            paid = float(self.paid_entry.get()) if self.paid_entry.get() else 0
        except Exception:
            paid = 0
        remaining = total - paid
        self.remaining_label.config(text=f"{max(0, remaining):.2f}")
        return total, discount_amount

    def clear_cart(self):
        self.cart = []
        self.discount_entry.delete(0, tk.END)
        self.discount_entry.insert(0, "0")
        self.paid_entry.delete(0, tk.END)
        self.paid_entry.insert(0, "0")
        self.customer_entry.delete(0, tk.END)
        self.update_cart_display()

    def complete_sale(self):
        if not self.cart:
            messagebox.showwarning("⚠️ تحذير", "السلة فارغة! أضف منتجات أولاً")
            return

        for item in self.cart:
            material = self.db.get_material_by_barcode(item['barcode'])
            if material[5] < item['quantity']:
                messagebox.showerror("خطأ", f"⚠️ الكمية المطلوبة من {item['name']} غير متوفرة!\nالمتوفر: {material[5]}\nالمطلوب: {item['quantity']}\n\nلا يمكن إتمام عملية البيع.")
                self.parent.bell()
                return

        customer = self.customer_entry.get().strip()
        if not customer:
            customer = "زبون"

        subtotal = sum(item['total'] for item in self.cart)
        try:
            discount_percent = float(self.discount_entry.get())
        except Exception:
            discount_percent = 0
        discount_amount = subtotal * discount_percent / 100
        total = subtotal - discount_amount

        paid = total
        remaining = 0

        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        out_of_stock_warnings = []
        low_stock_warnings = []

        for item in self.cart:
            sale_id, new_qty, name = self.db.add_sale(
                self.current_invoice, item['barcode'], item['name'], customer,
                item['unit'], item['quantity'], item['price'], item['total'],
                discount_percent, discount_amount, date
            )

            material = self.db.get_material_by_barcode(item['barcode'])
            if new_qty is not None and new_qty == 0:
                out_of_stock_warnings.append(f"❌ {name}: نفدت الكمية تماماً!")
            elif new_qty is not None and new_qty <= material[6] and new_qty > 0:
                low_stock_warnings.append(f"⚠️ {name}: وصلت للحد الأدنى ({new_qty}/{material[6]})")

        invoice_data = {
            'invoice_number': self.current_invoice,
            'customer': customer,
            'date': date,
            'items': self.cart,
            'subtotal': subtotal,
            'discount_percent': discount_percent,
            'discount_amount': discount_amount,
            'total': total,
            'paid': paid,
            'remaining': remaining,
            'status': 'مدفوع بالكامل'
        }

        self.printer.print_invoice(invoice_data)

        success_msg = f"✓ تمت الفاتورة رقم {self.current_invoice}\n\n"
        success_msg += f"💰 الإجمالي: {total:.2f}\n"
        success_msg += f"💵 المدفوع: {paid:.2f}\n"
        success_msg += f"📋 المتبقي: {remaining:.2f}\n"

        if out_of_stock_warnings:
            success_msg += "\n\n" + "\n".join(out_of_stock_warnings)
        if low_stock_warnings:
            success_msg += "\n\n" + "\n".join(low_stock_warnings)

        messagebox.showinfo("✅ نجاح", success_msg)

        self.clear_cart()
        self.current_invoice = self.db.get_next_invoice_number()
        self.invoice_label.config(text=f"🧾 رقم الفاتورة: {self.current_invoice}")
        self.load_materials()

        if self.on_material_change:
            self.on_material_change()

        out_stock = self.db.get_out_of_stock_materials()
        if out_stock:
            msg = "⚠️ تنبيه: المواد التالية نفدت بالكامل من المخزون:\n"
            for mat in out_stock:
                msg += f"   • {mat[1]} (الكمية: {mat[2]})\n"
            messagebox.showwarning("⚠️ تنبيه المخزون", msg)

    def add_material(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("➕ إضافة مادة جديدة")
        dialog.geometry("550x600")
        dialog.configure(bg=TK.CARD)
        dialog.transient(self.parent)
        dialog.grab_set()

        tk.Label(dialog, text="➕ إضافة مادة جديدة", font=('Arial', 16, 'bold'),
                bg=TK.CARD, fg=TK.ACCENT2).pack(pady=15)

        frame = tk.Frame(dialog, bg=TK.CARD)
        frame.pack(pady=10)

        labels = ['📦 الباركود', '📝 اسم المادة', '🏢 اسم التاجر', '📏 الوحدة', '💰 السعر', '📦 الكمية الابتدائية', '⚠️ الحد الأدنى']
        entries = {}

        for i, label in enumerate(labels):
            tk.Label(frame, text=label + ":", bg=TK.CARD, font=('Arial', 11)).grid(row=i, column=0, padx=10, pady=8, sticky='e')
            entry = tk.Entry(frame, font=('Arial', 11), width=25)
            entry.grid(row=i, column=1, padx=10, pady=8)
            entries[label] = entry

        entries['📦 الكمية الابتدائية'].insert(0, "0")
        entries['⚠️ الحد الأدنى'].insert(0, "5")

        units = ['piece', 'carton', 'meter', 'kg']
        entries['📏 الوحدة'].delete(0, tk.END)
        entries['📏 الوحدة'].insert(0, 'piece')

        def save():
            barcode = entries['📦 الباركود'].get().strip()
            name = entries['📝 اسم المادة'].get().strip()
            trader = entries['🏢 اسم التاجر'].get().strip()
            unit = entries['📏 الوحدة'].get()

            try:
                price = round_to_500(int(float(entries['💰 السعر'].get().replace(',', '').strip())))
            except Exception:
                messagebox.showerror("خطأ", "السعر يجب أن يكون رقماً")
                return

            try:
                quantity = float(entries['📦 الكمية الابتدائية'].get())
            except Exception:
                quantity = 0

            try:
                min_qty = float(entries['⚠️ الحد الأدنى'].get())
            except Exception:
                min_qty = 5

            if not barcode or not name:
                messagebox.showerror("خطأ", "الباركود واسم المادة مطلوبان")
                return

            success, msg = self.db.add_material(barcode, name, trader, unit, price, quantity, min_qty)
            messagebox.showinfo("نتيجة", msg)
            if success:
                dialog.destroy()
                self.load_materials()
                if self.on_material_change:
                    self.on_material_change()

        tk.Button(dialog, text="💾 حفظ", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 11),
                 command=save, padx=25, pady=8).pack(pady=20)

    def edit_material(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ تنبيه", "الرجاء اختيار مادة للتعديل")
            return

        values = self.tree.item(selected[0])['values']

        dialog = tk.Toplevel(self.parent)
        dialog.title("✏️ تعديل مادة")
        dialog.geometry("550x600")
        dialog.configure(bg=TK.CARD)
        dialog.transient(self.parent)
        dialog.grab_set()

        tk.Label(dialog, text="✏️ تعديل مادة", font=('Arial', 16, 'bold'),
                bg=TK.CARD, fg=TK.WARNING).pack(pady=15)

        frame = tk.Frame(dialog, bg=TK.CARD)
        frame.pack(pady=10)

        labels = ['📦 الباركود', '📝 اسم المادة', '🏢 اسم التاجر', '📏 الوحدة', '💰 السعر', '📦 الكمية', '⚠️ الحد الأدنى']
        entries = {}

        for i, label in enumerate(labels):
            tk.Label(frame, text=label + ":", bg=TK.CARD, font=('Arial', 11)).grid(row=i, column=0, padx=10, pady=8, sticky='e')
            entry = tk.Entry(frame, font=('Arial', 11), width=25)
            if i < len(values):
                entry.insert(0, str(values[i]))
            entry.grid(row=i, column=1, padx=10, pady=8)
            entries[label] = entry

        def save():
            barcode = entries['📦 الباركود'].get().strip()
            name = entries['📝 اسم المادة'].get().strip()
            trader = entries['🏢 اسم التاجر'].get().strip()
            unit = entries['📏 الوحدة'].get()

            try:
                price = round_to_500(int(float(entries['💰 السعر'].get().replace(',', '').strip())))
            except Exception:
                messagebox.showerror("خطأ", "السعر يجب أن يكون رقماً")
                return

            try:
                quantity = float(entries['📦 الكمية'].get())
            except Exception:
                quantity = 0

            try:
                min_qty = float(entries['⚠️ الحد الأدنى'].get())
            except Exception:
                min_qty = 5

            success, msg = self.db.update_material(values[0], barcode, name, trader, unit, price, quantity, min_qty)
            messagebox.showinfo("نتيجة", msg)
            if success:
                dialog.destroy()
                self.load_materials()
                if self.on_material_change:
                    self.on_material_change()

        tk.Button(dialog, text="💾 حفظ التعديلات", bg=TK.WARNING, fg=TK.WHITE, font=('Arial', 11),
                 command=save, padx=25, pady=8).pack(pady=20)

    def delete_material(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ تنبيه", "الرجاء اختيار مادة للحذف")
            return

        values = self.tree.item(selected[0])['values']

        if messagebox.askyesno("🗑️ تأكيد الحذف", f"هل أنت متأكد من حذف المادة:\n\n📝 {values[1]}"):
            self.db.delete_material(values[0])
            self.load_materials()
            self.status_label.config(text=f"🗑️ تم حذف: {values[1]}")
            self.parent.after(2000, lambda: self.status_label.config(text="✅ جاهز - امسح الباركود"))
            if self.on_material_change:
                self.on_material_change()

    def import_from_excel(self):
        file_path = filedialog.askopenfilename(
            title="اختر ملف Excel",
            filetypes=[("All files", "*.*"), ("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
        )
        if not file_path or not os.path.exists(file_path):
            return

        try:
            df = pd.read_excel(file_path)
            df.columns = [str(c).strip() for c in df.columns]
            cols = df.columns.tolist()

            # ── اكتشاف الأعمدة بأولوية صارمة (الأكثر تحديداً أولاً) ──
            def detect_col(keywords, exclude=None):
                exclude = exclude or []
                for kw in keywords:
                    for col in cols:
                        if col in exclude:
                            continue
                        if kw in col:
                            return col
                return None

            barcode_col = detect_col(['باركود', 'barcode', 'رمز', 'كود', 'code', 'رقم'])
            name_col    = detect_col(['اسم المادة', 'اسم', 'name', 'المنتج', 'product', 'وصف'],
                                     exclude=[barcode_col] if barcode_col else [])
            price_col   = detect_col(['سعر', 'price', 'ثمن', 'sell'],
                                     exclude=[c for c in [barcode_col, name_col] if c])
            qty_col     = detect_col(['كمية', 'quantity', 'qty', 'stock', 'مخزون'],
                                     exclude=[c for c in [barcode_col, name_col, price_col] if c])

            mapping_ok  = [False]
            result_cols = [barcode_col, name_col, price_col, qty_col]

            map_win = tk.Toplevel()
            map_win.title("تعيين أعمدة الاستيراد")
            map_win.geometry("480x400")
            map_win.configure(bg="white")
            map_win.resizable(False, False)
            map_win.grab_set()
            sw, sh = map_win.winfo_screenwidth(), map_win.winfo_screenheight()
            map_win.geometry(f"480x400+{(sw-480)//2}+{(sh-400)//2}")

            tk.Label(map_win, text="📋 تعيين أعمدة الملف", font=("Arial", 13, "bold"),
                     bg="white", fg="#2c3e50").pack(pady=(15, 5))
            tk.Label(map_win, text=f"الأعمدة في الملف: {' | '.join(cols)}",
                     font=("Arial", 9), bg="white", fg="#7f8c8d", wraplength=440).pack(pady=(0, 10))

            CHOICES = ["-- لا يوجد --"] + cols
            fields = [
                ("🔢 عمود الباركود *", barcode_col),
                ("📝 عمود الاسم *",     name_col),
                ("💰 عمود السعر *",     price_col),
                ("📦 عمود الكمية",      qty_col),
            ]
            vars_ = []
            frm = tk.Frame(map_win, bg="white")
            frm.pack(padx=30, fill="x")
            for label, detected in fields:
                tk.Label(frm, text=label, font=("Arial", 11), bg="white", anchor="w").pack(fill="x", pady=(8, 0))
                v = tk.StringVar(value=detected if detected else "-- لا يوجد --")
                cb = ttk.Combobox(frm, textvariable=v, values=CHOICES, state="readonly", font=("Arial", 11))
                cb.pack(fill="x", pady=(2, 0))
                vars_.append(v)

            qty_default_var = tk.StringVar(value="0")
            qdf = tk.Frame(map_win, bg="white")
            qdf.pack(padx=30, fill="x", pady=(8, 0))
            tk.Label(qdf, text="الكمية الافتراضية إذا لم يوجد عمود:",
                     font=("Arial", 10), bg="white").pack(side="left")
            tk.Entry(qdf, textvariable=qty_default_var, font=("Arial", 11),
                     width=8, justify="center").pack(side="left", padx=8)

            def on_confirm():
                bc = vars_[0].get()
                nm = vars_[1].get()
                pr = vars_[2].get()
                qt = vars_[3].get()
                if bc == "-- لا يوجد --" or nm == "-- لا يوجد --" or pr == "-- لا يوجد --":
                    messagebox.showwarning("تنبيه", "الباركود والاسم والسعر مطلوبة!", parent=map_win)
                    return
                if len({bc, nm, pr}) < 3:
                    messagebox.showwarning("تنبيه", "لا يمكن تعيين نفس العمود لحقلين!", parent=map_win)
                    return
                result_cols[0] = bc
                result_cols[1] = nm
                result_cols[2] = pr
                result_cols[3] = None if qt == "-- لا يوجد --" else qt
                mapping_ok[0]  = True
                map_win.destroy()

            tk.Button(map_win, text="✅ تأكيد والمتابعة", bg="#27ae60", fg="white",
                      font=("Arial", 12, "bold"), command=on_confirm,
                      cursor="hand2", pady=6).pack(pady=15)
            map_win.wait_window()

            if not mapping_ok[0]:
                return

            barcode_col, name_col, price_col, qty_col = result_cols
            try:
                default_qty = float(qty_default_var.get())
            except Exception:
                default_qty = 0

            if not messagebox.askyesno("تأكيد الاستيراد",
                f"سيتم استيراد {len(df)} صف.\n\n"
                f"• الباركود : {barcode_col}\n"
                f"• الاسم    : {name_col}\n"
                f"• السعر    : {price_col}\n"
                f"• الكمية   : {qty_col or f'افتراضي ({int(default_qty)})'}\n\n"
                f"المنتجات الموجودة سيتم تحديثها. هل تريد المتابعة؟"):
                return

            count_new = count_updated = skipped = 0
            skip_details = []
            cursor = self.db.conn.cursor()
            EMPTY = {"nan", "none", "null", ""}

            for idx, row in df.iterrows():
                raw_bc = str(row[barcode_col]).strip()
                if raw_bc.endswith(".0"):
                    raw_bc = raw_bc[:-2]
                barcode = raw_bc
                name    = str(row[name_col]).strip()

                if barcode.lower() in EMPTY or name.lower() in EMPTY:
                    skipped += 1
                    skip_details.append(f"صف {idx+2}: باركود أو اسم فارغ")
                    continue

                try:
                    price = float(str(row[price_col]).replace(",", "").strip())
                    if price < 0:
                        raise ValueError("سعر سالب")
                except Exception:
                    skipped += 1
                    skip_details.append(f"صف {idx+2} [{name}]: سعر غير صالح ({row[price_col]})")
                    continue

                qty = default_qty
                if qty_col:
                    try:
                        q = str(row[qty_col]).replace(",", "").strip()
                        qty = float(q) if q.lower() not in EMPTY else default_qty
                    except Exception:
                        qty = default_qty

                try:
                    cursor.execute("SELECT barcode FROM materials WHERE barcode=?", (barcode,))
                    if cursor.fetchone():
                        cursor.execute(
                            "UPDATE materials SET name=?, sell_price=?, quantity=? WHERE barcode=?",
                            (name, round(price), qty, barcode)
                        )
                        count_updated += 1
                    else:
                        cursor.execute(
                            "INSERT INTO materials (barcode, name, trader_name, main_unit, sell_price, quantity, min_quantity) VALUES (?,?,?,?,?,?,?)",
                            (barcode, name, "", "piece", round(price), qty, 5)
                        )
                        count_new += 1
                except Exception as e:
                    skipped += 1
                    skip_details.append(f"صف {idx+2} [{name}]: {str(e)}")

            self.db.conn.commit()
            self.load_materials()
            if self.on_material_change:
                self.on_material_change()

            detail_msg = ""
            if skip_details:
                detail_msg = "\n\nتفاصيل الصفوف المتجاهلة:\n" + "\n".join(skip_details[:10])
                if len(skip_details) > 10:
                    detail_msg += f"\n... و{len(skip_details)-10} أخرى"

            messagebox.showinfo("اكتمل الاستيراد ✅",
                f"✅ منتجات جديدة أُضيفت  : {count_new}\n"
                f"🔄 منتجات تم تحديثها   : {count_updated}\n"
                f"⚠️ صفوف تم تجاهلها    : {skipped}"
                + detail_msg)

        except Exception as e:
            messagebox.showerror("خطأ", f"فشل الاستيراد: {str(e)}")

