"""supplier_invoices_tab.py — تبويب فواتير الموردين"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
from theme_tk import TK, apply_theme, setup_treeview, fill_treeview, style_button, style_entry, make_card
from datetime import datetime
from database import Database, round_to_500
from printer import Printer

class SupplierInvoicesTab:
    def __init__(self, parent, db, on_material_change=None):
        self.parent = parent
        self.db = db
        self.on_material_change = on_material_change
        self.selected_invoice = None
        self.create_widgets()
        self.load_invoices()

    def create_widgets(self):
        control_frame = tk.Frame(self.parent, bg=TK.CARD)
        control_frame.pack(fill='x', padx=10, pady=10)

        btn_frame = tk.Frame(control_frame, bg=TK.CARD)
        btn_frame.pack(side='left', padx=10)

        tk.Button(btn_frame, text="➕ فاتورة مشتريات جديدة", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 10),
                 command=self.add_invoice, padx=15, pady=5).pack(side='left', padx=5)

        tk.Button(btn_frame, text="✏️ تعديل فاتورة", bg=TK.WARNING, fg=TK.WHITE, font=('Arial', 10),
                 command=self.edit_invoice, padx=15, pady=5).pack(side='left', padx=5)

        tk.Button(btn_frame, text="💰 تسجيل دفعة", bg=TK.ACCENT,  fg=TK.WHITE, font=('Arial', 10),
                 command=self.add_payment, padx=15, pady=5).pack(side='left', padx=5)

        tk.Button(btn_frame, text="🗑️ حذف فاتورة", bg=TK.DANGER,  fg=TK.WHITE, font=('Arial', 10),
                 command=self.delete_invoice, padx=15, pady=5).pack(side='left', padx=5)

        tk.Button(btn_frame, text="🔄 تحديث", bg=TK.ACCENT2, fg=TK.WHITE, font=('Arial', 10),
                 command=self.load_invoices, padx=15, pady=5).pack(side='left', padx=5)

        filter_frame = tk.Frame(control_frame, bg=TK.CARD)
        filter_frame.pack(side='right', padx=10)

        tk.Label(filter_frame, text="بحث عن تاجر:", bg=TK.CARD, font=('Arial', 10)).pack(side='left', padx=5)
        self.search_entry = tk.Entry(filter_frame, width=20, font=('Arial', 10))
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.load_invoices())

        summary_frame = tk.Frame(self.parent, bg=TK.BG, relief='ridge', bd=1)
        summary_frame.pack(fill='x', padx=10, pady=5)
        self.summary_label = tk.Label(summary_frame, text="📊 إجمالي فواتير المشتريات: 0 فاتورة | 💰 الإجمالي: 0 | 💵 المدفوع: 0 | 📋 المتبقي: 0",
                                       font=('Arial', 11, 'bold'), bg=TK.BG, fg=TK.TEXT)
        self.summary_label.pack(pady=8)

        tree_frame = tk.Frame(self.parent, bg=TK.CARD)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        columns = ('رقم الفاتورة', 'التاجر', 'التاريخ', 'الإجمالي', 'المدفوع', 'المتبقي', 'الحالة', 'ملاحظات')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=14)

        col_widths = [120, 180, 100, 120, 120, 120, 120, 150]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.bind('<<TreeviewSelect>>', self.on_select)

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            # نستخرج رقم الفاتورة الأصلي من iid بدل values لأن Treeview يحوّل "001" إلى 1
            iid = selected[0]  # مثال: "inv_001"
            self.selected_invoice = iid.replace("inv_", "", 1)

    def load_invoices(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = self.search_entry.get().strip().lower()
        invoices = self.db.get_all_supplier_invoices()

        total_amount = 0
        total_paid = 0
        total_remaining = 0

        for inv in invoices:
            if search and search not in inv[1].lower():
                continue

            status_color = ""
            if inv[7] == 'مدفوع بالكامل':
                status_color = '✅ '
            elif inv[7] == 'مدفوع جزئياً':
                status_color = '⚠️ '
            else:
                status_color = '❌ '

            self.tree.insert('', 'end', iid=f"inv_{inv[1]}", values=(
                inv[1], inv[2], inv[3], f"{inv[4]:.2f}", f"{inv[5]:.2f}", f"{inv[6]:.2f}",
                f"{status_color}{inv[7]}", inv[8] if inv[8] else '-'
            ))

            total_amount += inv[4]
            total_paid += inv[5]
            total_remaining += inv[6]

        summary = self.db.get_supplier_invoices_summary()
        self.summary_label.config(text=f"📊 إجمالي فواتير المشتريات: {summary['total_count']} فاتورة | 💰 الإجمالي: {summary['total_amount']:.2f} | 💵 المدفوع: {summary['total_paid']:.2f} | 📋 المتبقي: {summary['total_remaining']:.2f}")

    def add_invoice(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("➕ إضافة فاتورة مشتريات جديدة")
        dialog.geometry("750x700")
        dialog.configure(bg=TK.CARD)
        dialog.transient(self.parent)
        dialog.grab_set()

        tk.Label(dialog, text="➕ إضافة فاتورة مشتريات جديدة", font=('Arial', 16, 'bold'),
                bg=TK.CARD, fg=TK.SUCCESS).pack(pady=15)

        main_frame = tk.Frame(dialog, bg=TK.CARD)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        info_frame = tk.LabelFrame(main_frame, text="📄 معلومات الفاتورة",
                                    font=('Arial', 12, 'bold'), bg=TK.CARD, fg=TK.ACCENT)
        info_frame.pack(fill='x', pady=5)

        row1 = tk.Frame(info_frame, bg=TK.CARD)
        row1.pack(fill='x', padx=10, pady=5)

        tk.Label(row1, text="رقم الفاتورة:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)
        invoice_entry = tk.Entry(row1, font=('Arial', 11), width=20)
        invoice_entry.pack(side='right', padx=5)

        row2 = tk.Frame(info_frame, bg=TK.CARD)
        row2.pack(fill='x', padx=10, pady=5)

        tk.Label(row2, text="اسم التاجر:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)
        supplier_entry = tk.Entry(row2, font=('Arial', 11), width=30)
        supplier_entry.pack(side='right', padx=5)

        row3 = tk.Frame(info_frame, bg=TK.CARD)
        row3.pack(fill='x', padx=10, pady=5)

        tk.Label(row3, text="تاريخ الفاتورة:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)
        date_entry = tk.Entry(row3, font=('Arial', 11), width=15)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.pack(side='right', padx=5)

        row4 = tk.Frame(info_frame, bg=TK.CARD)
        row4.pack(fill='x', padx=10, pady=5)

        tk.Label(row4, text="ملاحظات:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)
        notes_entry = tk.Entry(row4, font=('Arial', 11), width=40)
        notes_entry.pack(side='right', padx=5)

        products_frame = tk.LabelFrame(main_frame, text="📦 المنتجات",
                                        font=('Arial', 12, 'bold'), bg=TK.CARD, fg=TK.ACCENT2)
        products_frame.pack(fill='both', expand=True, pady=5)

        add_product_frame = tk.Frame(products_frame, bg=TK.CARD)
        add_product_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(add_product_frame, text="الباركود:", bg=TK.CARD, font=('Arial', 10)).pack(side='right', padx=3)
        barcode_entry = tk.Entry(add_product_frame, width=15, font=('Arial', 10))
        barcode_entry.pack(side='right', padx=3)

        tk.Label(add_product_frame, text="الكمية:", bg=TK.CARD, font=('Arial', 10)).pack(side='right', padx=3)
        qty_entry = tk.Entry(add_product_frame, width=10, font=('Arial', 10))
        qty_entry.pack(side='right', padx=3)

        tk.Label(add_product_frame, text="سعر الشراء:", bg=TK.CARD, font=('Arial', 10)).pack(side='right', padx=3)
        price_entry = tk.Entry(add_product_frame, width=12, font=('Arial', 10))
        price_entry.pack(side='right', padx=3)

        tree_frame = tk.Frame(products_frame, bg=TK.CARD)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        columns = ('الباركود', 'اسم المنتج', 'الكمية', 'سعر الشراء', 'الإجمالي')
        products_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=6)

        col_widths = [100, 180, 80, 100, 120]
        for col, width in zip(columns, col_widths):
            products_tree.heading(col, text=col)
            products_tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=products_tree.yview)
        products_tree.configure(yscrollcommand=scrollbar.set)
        products_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        products_list = []

        def add_product():
            barcode = barcode_entry.get().strip()
            if not barcode:
                messagebox.showerror("خطأ", "الرجاء إدخال الباركود")
                return

            material = self.db.get_material_by_barcode(barcode)
            if not material:
                if messagebox.askyesno("منتج غير موجود", f"الباركود {barcode} غير مسجل.\nهل تريد إضافته الآن؟"):
                    add_new_material_from_invoice(barcode)
                return

            try:
                quantity = float(qty_entry.get())
                if quantity <= 0:
                    messagebox.showerror("خطأ", "الكمية يجب أن تكون أكبر من صفر")
                    return
            except Exception:
                messagebox.showerror("خطأ", "الكمية يجب أن تكون رقماً")
                return

            try:
                price = float(price_entry.get())
                if price <= 0:
                    messagebox.showerror("خطأ", "سعر الشراء يجب أن يكون أكبر من صفر")
                    return
            except Exception:
                messagebox.showerror("خطأ", "سعر الشراء يجب أن يكون رقماً")
                return

            total = quantity * price
            products_list.append({
                'barcode': barcode,
                'name': material[1],
                'quantity': quantity,
                'price': price,
                'total': total
            })

            products_tree.insert('', 'end', values=(' ' + str(barcode), material[1], f"{quantity:.2f}", f"{price:.2f}", f"{total:.2f}"))

            barcode_entry.delete(0, tk.END)
            qty_entry.delete(0, tk.END)
            price_entry.delete(0, tk.END)
            barcode_entry.focus()
            update_total()

        def add_new_material_from_invoice(barcode):
            sub_dialog = tk.Toplevel(dialog)
            sub_dialog.title("➕ إضافة مادة جديدة")
            sub_dialog.geometry("500x550")
            sub_dialog.configure(bg=TK.CARD)
            sub_dialog.transient(dialog)
            sub_dialog.grab_set()

            tk.Label(sub_dialog, text="➕ إضافة مادة جديدة", font=('Arial', 16, 'bold'),
                    bg=TK.CARD, fg=TK.ACCENT2).pack(pady=15)

            frame = tk.Frame(sub_dialog, bg=TK.CARD)
            frame.pack(pady=10)

            labels = ['📦 الباركود', '📝 اسم المادة', '🏢 اسم التاجر', '📏 الوحدة', '💰 سعر البيع', '📦 الكمية الابتدائية', '⚠️ الحد الأدنى']
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

            def save_material():
                name = entries['📝 اسم المادة'].get().strip()
                trader = entries['🏢 اسم التاجر'].get().strip()
                unit = entries['📏 الوحدة'].get()

                try:
                    sell_price = round_to_500(int(float(entries['💰 سعر البيع'].get().replace(',', '').strip())))
                except Exception as e:
                    messagebox.showerror("خطأ", f"السعر يجب أن يكون رقماً\n\nتفاصيل الخطأ:\n{type(e).__name__}: {e}\n\nالقيمة المدخلة: [{entries['💰 سعر البيع'].get()}]")
                    return

                if not name:
                    messagebox.showerror("خطأ", "اسم المادة مطلوب")
                    return

                success, msg = self.db.add_material(barcode, name, trader, unit, sell_price, 0, 5)
                messagebox.showinfo("نتيجة", msg)
                if success:
                    sub_dialog.destroy()
                    add_product()

            tk.Button(sub_dialog, text="💾 حفظ", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 11),
                     command=save_material, padx=25, pady=8).pack(pady=20)

        def update_total():
            total = sum(p['total'] for p in products_list)
            total_label.config(text=f"💰 إجمالي الفاتورة: {total:.2f}")

        total_frame = tk.Frame(main_frame, bg=TK.BG, relief='ridge', bd=1)
        total_frame.pack(fill='x', pady=5)

        total_label = tk.Label(total_frame, text="💰 إجمالي الفاتورة: 0.00",
                                font=('Arial', 13, 'bold'), bg=TK.BG, fg=TK.DANGER)
        total_label.pack(pady=8)

        def save_invoice():
            invoice_num = invoice_entry.get().strip()
            if not invoice_num:
                messagebox.showerror("خطأ", "رقم الفاتورة مطلوب")
                return

            supplier = supplier_entry.get().strip()
            if not supplier:
                messagebox.showerror("خطأ", "اسم التاجر مطلوب")
                return

            if not products_list:
                messagebox.showerror("خطأ", "يجب إضافة منتج واحد على الأقل")
                return

            invoice_date = date_entry.get().strip()
            notes = notes_entry.get().strip()
            total = sum(p['total'] for p in products_list)

            existing = self.db.get_supplier_invoice_by_number(invoice_num)
            if existing:
                messagebox.showerror("خطأ", f"رقم الفاتورة '{invoice_num}' موجود مسبقاً")
                return

            result = self.db.add_supplier_invoice(invoice_num, supplier, invoice_date, total, notes)
            if result is None:
                messagebox.showerror("خطأ", f"رقم الفاتورة '{invoice_num}' موجود مسبقاً")
                return

            for product in products_list:
                self.db.add_invoice_item(invoice_num, product['barcode'], product['name'],
                                        product['quantity'], product['price'])

            messagebox.showinfo("نجاح", f"✓ تم تسجيل فاتورة المشتريات رقم {invoice_num}\n"
                                f"🏢 التاجر: {supplier}\n"
                                f"💰 الإجمالي: {total:.2f}\n"
                                f"📦 عدد المنتجات: {len(products_list)}")

            dialog.destroy()
            self.load_invoices()
            if self.on_material_change:
                self.on_material_change()

        tk.Button(add_product_frame, text="➕ إضافة منتج", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 10),
                 command=add_product, padx=15, pady=3).pack(side='right', padx=5)

        btn_frame = tk.Frame(main_frame, bg=TK.CARD)
        btn_frame.pack(fill='x', pady=10)

        tk.Button(btn_frame, text="💾 حفظ الفاتورة", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 11),
                 command=save_invoice, padx=25, pady=8).pack(side='left', padx=10, expand=True, fill='x')

        tk.Button(btn_frame, text="❌ إلغاء", bg=TK.DANGER,  fg=TK.WHITE, font=('Arial', 11),
                 command=dialog.destroy, padx=25, pady=8).pack(side='right', padx=10, expand=True, fill='x')

    def edit_invoice(self):
        if not self.selected_invoice:
            messagebox.showwarning("تنبيه", "الرجاء اختيار فاتورة من الجدول أولاً")
            return

        invoice = self.db.get_supplier_invoice_by_number(self.selected_invoice)
        if not invoice:
            messagebox.showerror("خطأ", "لم يتم العثور على الفاتورة")
            return

        # ─── لون عصري للنافذة ────────────────────────────────────────
        BG       = '#f8f9fa'
        ACCENT   = '#e65100'    # برتقالي داكن للتعديل
        CARD_BG  = '#ffffff'
        BTN_SAVE = '#00897b'
        BTN_DEL  = '#e53935'
        BTN_ADD  = '#1e88e5'

        dialog = tk.Toplevel(self.parent)
        dialog.title("✏️ تعديل فاتورة مشتريات")
        dialog.geometry("780x680")
        dialog.configure(bg=BG)
        dialog.transient(self.parent)
        dialog.grab_set()
        # تمركز النافذة
        dialog.update_idletasks()
        sw, sh = dialog.winfo_screenwidth(), dialog.winfo_screenheight()
        dialog.geometry(f"780x680+{(sw-780)//2}+{(sh-680)//2}")

        # ── رأس النافذة ──
        header = tk.Frame(dialog, bg=ACCENT, height=52)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text="✏️  تعديل فاتورة مشتريات", font=('Arial', 15, 'bold'),
                 bg=ACCENT, fg=TK.WHITE).pack(side='right', padx=15, pady=12)
        tk.Label(header, text=f"رقم الفاتورة: {invoice[1]}", font=('Arial', 11),
                 bg=ACCENT, fg=TK.WARNING).pack(side='left', padx=15)

        main = tk.Frame(dialog, bg=BG)
        main.pack(fill='both', expand=True, padx=16, pady=10)

        # ── بيانات الفاتورة الأساسية ──
        info_card = tk.LabelFrame(main, text="  📄 بيانات الفاتورة  ",
                                  font=('Arial', 11, 'bold'), bg=CARD_BG, fg=TK.TEXT,
                                  relief='flat', bd=1, highlightbackground=TK.BG2,
                                  highlightthickness=1)
        info_card.pack(fill='x', pady=(0, 10))

        grid = tk.Frame(info_card, bg=CARD_BG)
        grid.pack(fill='x', padx=15, pady=10)

        def lbl(parent, text, row, col, **kw):
            tk.Label(parent, text=text, bg=CARD_BG, font=('Arial', 10),
                     fg=TK.TEXT_SUB, **kw).grid(row=row, column=col, padx=8, pady=6, sticky='e')

        def ent(parent, row, col, width=22, val=''):
            e = tk.Entry(parent, font=('Arial', 11), width=width,
                         bg=TK.BG3, relief='flat', bd=4)
            e.insert(0, val)
            e.grid(row=row, column=col, padx=8, pady=6, sticky='w')
            return e

        lbl(grid, "اسم التاجر:", 0, 0)
        supplier_entry = ent(grid, 0, 1, val=invoice[2])

        lbl(grid, "تاريخ الفاتورة:", 0, 2)
        date_entry = ent(grid, 0, 3, width=14, val=invoice[3])

        lbl(grid, "ملاحظات:", 1, 0)
        notes_entry = ent(grid, 1, 1, width=38, val=invoice[8] if invoice[8] else '')

        # ── قسم المنتجات ──
        prod_card = tk.LabelFrame(main, text="  📦 منتجات الفاتورة  ",
                                  font=('Arial', 11, 'bold'), bg=CARD_BG, fg=TK.TEXT,
                                  relief='flat', bd=1, highlightbackground=TK.BG2,
                                  highlightthickness=1)
        prod_card.pack(fill='both', expand=True, pady=(0, 10))

        # شريط إضافة منتج
        add_bar = tk.Frame(prod_card, bg=TK.BG3)
        add_bar.pack(fill='x', padx=10, pady=6)

        tk.Label(add_bar, text="باركود:", bg=TK.BG3, font=('Arial', 10)).pack(side='right', padx=4)
        new_barcode = tk.Entry(add_bar, width=14, font=('Arial', 10), bg=TK.CARD, relief='flat', bd=3)
        new_barcode.pack(side='right', padx=4)

        tk.Label(add_bar, text="الكمية:", bg=TK.BG3, font=('Arial', 10)).pack(side='right', padx=4)
        new_qty = tk.Entry(add_bar, width=8, font=('Arial', 10), bg=TK.CARD, relief='flat', bd=3)
        new_qty.pack(side='right', padx=4)

        tk.Label(add_bar, text="سعر الشراء:", bg=TK.BG3, font=('Arial', 10)).pack(side='right', padx=4)
        new_price = tk.Entry(add_bar, width=10, font=('Arial', 10), bg=TK.CARD, relief='flat', bd=3)
        new_price.pack(side='right', padx=4)

        # جدول المنتجات
        tree_f = tk.Frame(prod_card, bg=CARD_BG)
        tree_f.pack(fill='both', expand=True, padx=10, pady=4)

        style = ttk.Style()
        style.configure("Edit.Treeview", rowheight=28, font=('Arial', 10))
        style.configure("Edit.Treeview.Heading", font=('Arial', 10, 'bold'))

        cols = ('الباركود', 'اسم المنتج', 'الكمية', 'سعر الشراء', 'الإجمالي')
        items_tree = ttk.Treeview(tree_f, columns=cols, show='headings',
                                   height=7, style="Edit.Treeview")
        for col, w in zip(cols, [110, 200, 80, 110, 110]):
            items_tree.heading(col, text=col, anchor='center')
            items_tree.column(col, width=w, anchor='center')

        vsb = ttk.Scrollbar(tree_f, orient='vertical', command=items_tree.yview)
        items_tree.configure(yscrollcommand=vsb.set)
        items_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        # تحميل المنتجات الحالية
        existing_items = self.db.get_invoice_items(invoice[1])
        items_list = []
        for it in existing_items:
            items_list.append({'id': it[0], 'barcode': it[2], 'name': it[3],
                               'quantity': it[4], 'price': it[5], 'total': it[6]})
            items_tree.insert('', 'end', values=(' ' + str(it[2]), it[3], f"{it[4]:.2f}",
                                                  f"{it[5]:.2f}", f"{it[6]:.2f}"))

        total_var = tk.StringVar()
        def refresh_total():
            t = sum(i['total'] for i in items_list)
            total_var.set(f"💰 إجمالي المنتجات: {t:.2f}")

        refresh_total()

        def refresh_tree():
            for row in items_tree.get_children():
                items_tree.delete(row)
            for it in items_list:
                items_tree.insert('', 'end', values=(' ' + str(it['barcode']), it['name'],
                    f"{it['quantity']:.2f}", f"{it['price']:.2f}", f"{it['total']:.2f}"))
            refresh_total()

        def add_item():
            bc = new_barcode.get().strip()
            if not bc:
                messagebox.showerror("خطأ", "أدخل الباركود", parent=dialog)
                return
            mat = self.db.get_material_by_barcode(bc)
            if not mat:
                messagebox.showerror("خطأ", f"الباركود {bc} غير موجود", parent=dialog)
                return
            try:
                q = float(new_qty.get())
                p = float(new_price.get())
                if q <= 0 or p <= 0:
                    raise ValueError
            except Exception:
                messagebox.showerror("خطأ", "الكمية والسعر يجب أن يكونا أكبر من صفر", parent=dialog)
                return
            items_list.append({'id': None, 'barcode': bc, 'name': mat[1],
                                'quantity': q, 'price': p, 'total': q * p})
            refresh_tree()
            new_barcode.delete(0, tk.END)
            new_qty.delete(0, tk.END)
            new_price.delete(0, tk.END)

        def delete_item():
            sel = items_tree.selection()
            if not sel:
                messagebox.showwarning("تنبيه", "اختر منتجاً للحذف", parent=dialog)
                return
            idx = items_tree.index(sel[0])
            if idx < len(items_list):
                if not messagebox.askyesno("تأكيد", "هل تريد حذف هذا المنتج من الفاتورة؟", parent=dialog):
                    return
                del items_list[idx]
                refresh_tree()

        tk.Button(add_bar, text="➕ إضافة", bg=BTN_ADD, fg=TK.WHITE,
                  font=('Arial', 10, 'bold'), relief='flat', padx=10, pady=4,
                  cursor='hand2', command=add_item).pack(side='right', padx=8)

        tk.Button(add_bar, text="🗑️ حذف محدد", bg=BTN_DEL, fg=TK.WHITE,
                  font=('Arial', 10, 'bold'), relief='flat', padx=10, pady=4,
                  cursor='hand2', command=delete_item).pack(side='right', padx=4)

        # شريط الإجمالي
        total_bar = tk.Frame(prod_card, bg=TK.BG3)
        total_bar.pack(fill='x', padx=10, pady=4)
        tk.Label(total_bar, textvariable=total_var, bg=TK.BG3,
                 font=('Arial', 12, 'bold'), fg=TK.WARNING).pack(pady=6)

        # ── أزرار الحفظ / الإلغاء ──
        def save_edit():
            supplier = supplier_entry.get().strip()
            inv_date = date_entry.get().strip()
            notes    = notes_entry.get().strip()
            if not supplier or not inv_date:
                messagebox.showerror("خطأ", "اسم التاجر والتاريخ مطلوبان", parent=dialog)
                return
            if not items_list:
                messagebox.showerror("خطأ", "يجب أن تحتوي الفاتورة على منتج واحد على الأقل", parent=dialog)
                return

            new_total = sum(i['total'] for i in items_list)
            self.db.update_supplier_invoice(invoice[1], supplier, inv_date, new_total, notes)

            # حذف البنود القديمة وإعادة إدراج الجديدة
            cursor = self.db.conn.cursor()
            cursor.execute("DELETE FROM invoice_items WHERE invoice_number=?", (invoice[1],))
            self.db.conn.commit()
            for it in items_list:
                cursor.execute(
                    "INSERT INTO invoice_items (invoice_number,barcode,material_name,quantity,purchase_price,total) VALUES (?,?,?,?,?,?)",
                    (invoice[1], it['barcode'], it['name'], it['quantity'], it['price'], it['total'])
                )
            self.db.conn.commit()

            dialog.destroy()
            self.load_invoices()
            messagebox.showinfo("نجاح ✅", f"✓ تم تعديل الفاتورة رقم {invoice[1]} بنجاح\n"
                                            f"📦 عدد المنتجات: {len(items_list)}\n"
                                            f"💰 الإجمالي الجديد: {new_total:.2f}")

        btn_row = tk.Frame(dialog, bg=BG)
        btn_row.pack(fill='x', padx=16, pady=10)

        tk.Button(btn_row, text="💾  حفظ التعديلات", bg=BTN_SAVE, fg=TK.WHITE,
                  font=('Arial', 12, 'bold'), relief='flat', padx=20, pady=10,
                  cursor='hand2', command=save_edit).pack(side='left', padx=6, expand=True, fill='x')

        tk.Button(btn_row, text="❌  إلغاء", bg=BTN_DEL, fg=TK.WHITE,
                  font=('Arial', 12, 'bold'), relief='flat', padx=20, pady=10,
                  cursor='hand2', command=dialog.destroy).pack(side='right', padx=6, expand=True, fill='x')

    def add_payment(self):
        if not self.selected_invoice:
            messagebox.showwarning("تنبيه", "الرجاء اختيار فاتورة من الجدول")
            return

        invoice = self.db.get_supplier_invoice_by_number(self.selected_invoice)
        if not invoice:
            messagebox.showerror("خطأ", "لم يتم العثور على الفاتورة")
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title("💰 تسجيل دفعة للتاجر")
        dialog.geometry("500x500")
        dialog.configure(bg=TK.CARD)
        dialog.transient(self.parent)
        dialog.grab_set()

        tk.Label(dialog, text="💰 تسجيل دفعة للتاجر", font=('Arial', 16, 'bold'),
                bg=TK.CARD, fg=TK.ACCENT).pack(pady=15)

        frame = tk.Frame(dialog, bg=TK.CARD)
        frame.pack(pady=10, padx=20, fill='both', expand=True)

        info_frame = tk.Frame(frame, bg=TK.BG, relief='ridge', bd=1)
        info_frame.pack(fill='x', pady=5)

        tk.Label(info_frame, text=f"📄 رقم الفاتورة: {invoice[1]}", font=('Arial', 12),
                bg=TK.BG, fg=TK.TEXT).pack(pady=5, anchor='w', padx=10)
        tk.Label(info_frame, text=f"🏢 التاجر: {invoice[2]}", font=('Arial', 12),
                bg=TK.BG, fg=TK.TEXT).pack(pady=5, anchor='w', padx=10)
        tk.Label(info_frame, text=f"💰 الإجمالي: {invoice[4]:.2f}", font=('Arial', 12),
                bg=TK.BG, fg=TK.DANGER).pack(pady=5, anchor='w', padx=10)
        tk.Label(info_frame, text=f"💵 المدفوع: {invoice[5]:.2f}", font=('Arial', 12),
                bg=TK.BG, fg=TK.SUCCESS).pack(pady=5, anchor='w', padx=10)
        tk.Label(info_frame, text=f"📋 المتبقي: {invoice[6]:.2f}", font=('Arial', 12),
                bg=TK.BG, fg=TK.WARNING).pack(pady=5, anchor='w', padx=10)

        payment_frame = tk.LabelFrame(frame, text="💵 بيانات الدفعة",
                                       font=('Arial', 12, 'bold'), bg=TK.CARD, fg=TK.SUCCESS)
        payment_frame.pack(fill='x', pady=10)

        inner_frame = tk.Frame(payment_frame, bg=TK.CARD)
        inner_frame.pack(pady=10, padx=10)

        tk.Label(inner_frame, text="المبلغ:", bg=TK.CARD, font=('Arial', 11)).grid(row=0, column=0, padx=5, pady=8, sticky='e')
        amount_entry = tk.Entry(inner_frame, width=15, font=('Arial', 11))
        amount_entry.grid(row=0, column=1, padx=5, pady=8)

        tk.Label(inner_frame, text="طريقة الدفع:", bg=TK.CARD, font=('Arial', 11)).grid(row=1, column=0, padx=5, pady=8, sticky='e')
        methods = ['نقدي', 'تحويل بنكي', 'شيك', 'بطاقة ائتمان', 'أخرى']
        method_combo = ttk.Combobox(inner_frame, values=methods, width=13)
        method_combo.set('نقدي')
        method_combo.grid(row=1, column=1, padx=5, pady=8)

        tk.Label(inner_frame, text="ملاحظات:", bg=TK.CARD, font=('Arial', 11)).grid(row=2, column=0, padx=5, pady=8, sticky='e')
        notes_entry = tk.Entry(inner_frame, width=30, font=('Arial', 11))
        notes_entry.grid(row=2, column=1, padx=5, pady=8)

        def save_payment():
            try:
                amount = float(amount_entry.get())
                if amount <= 0:
                    messagebox.showerror("خطأ", "المبلغ يجب أن يكون أكبر من صفر")
                    return
                if amount > invoice[6]:
                    result = messagebox.askyesno("⚠️ تنبيه",
                        f"المبلغ المدخل ({amount:.2f}) أكبر من المتبقي ({invoice[6]:.2f})\n"
                        f"هل تريد تسجيل {invoice[6]:.2f} كدفعة كاملة؟")
                    if result:
                        amount = invoice[6]
                    else:
                        return
            except Exception:
                messagebox.showerror("خطأ", "المبلغ يجب أن يكون رقماً")
                return

            method = method_combo.get()
            notes = notes_entry.get().strip()

            self.db.add_supplier_payment(invoice[1], amount, method, notes)

            messagebox.showinfo("نجاح", f"✓ تم تسجيل دفعة بقيمة {amount:.2f}\n"
                                f"✓ طريقة الدفع: {method}\n"
                                f"✓ التاجر: {invoice[2]}")

            dialog.destroy()
            self.load_invoices()

        btn_frame = tk.Frame(frame, bg=TK.CARD)
        btn_frame.pack(fill='x', pady=10)

        tk.Button(btn_frame, text="💾 تسجيل الدفعة", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 11),
                 command=save_payment, padx=25, pady=8).pack(side='left', padx=10, expand=True, fill='x')

        tk.Button(btn_frame, text="❌ إلغاء", bg=TK.DANGER,  fg=TK.WHITE, font=('Arial', 11),
                 command=dialog.destroy, padx=25, pady=8).pack(side='right', padx=10, expand=True, fill='x')

    def delete_invoice(self):
        if not self.selected_invoice:
            messagebox.showwarning("تنبيه", "الرجاء اختيار فاتورة من الجدول أولاً")
            return

        invoice = self.db.get_supplier_invoice_by_number(self.selected_invoice)
        if not invoice:
            messagebox.showerror("خطأ", "لم يتم العثور على الفاتورة")
            return

        confirm = messagebox.askyesno(
            "⚠️ تأكيد حذف الفاتورة",
            f"هل أنت متأكد من حذف الفاتورة رقم: {invoice[1]}؟\n"
            f"🏢 التاجر: {invoice[2]}\n"
            f"💰 الإجمالي: {invoice[4]:.2f}\n\n"
            f"⚠️ تحذير: سيتم حذف جميع بنود الفاتورة والدفعات المرتبطة بها!\n"
            f"لن يتم التراجع عن هذا الإجراء."
        )
        if not confirm:
            return

        self.db.delete_supplier_invoice(self.selected_invoice)
        self.selected_invoice = None
        self.load_invoices()
        messagebox.showinfo("تم", "✅ تم حذف الفاتورة بنجاح")

