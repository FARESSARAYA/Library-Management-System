"""returns_tab.py — تبويب المرتجعات والتبديلات"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
from theme_tk import TK, apply_theme, setup_treeview, fill_treeview, style_button, style_entry, make_card
from datetime import datetime
from database import Database
from printer import Printer

class ReturnsTab:
    def __init__(self, parent, db, on_material_change=None):
        self.parent = parent
        self.db = db
        self.on_material_change = on_material_change
        self.selected_return = None
        self.create_widgets()
        self.load_returns()
        self.load_exchanges()

    def create_widgets(self):
        control_frame = tk.Frame(self.parent, bg=TK.CARD)
        control_frame.pack(fill='x', padx=10, pady=10)

        btn_frame = tk.Frame(control_frame, bg=TK.CARD)
        btn_frame.pack(side='left', padx=10)

        tk.Button(btn_frame, text="🔄 إرجاع منتج", bg=TK.WARNING, fg=TK.WHITE, font=('Arial', 10),
                 command=self.add_return, padx=15, pady=5).pack(side='left', padx=5)

        tk.Button(btn_frame, text="🔄🔄 تبديل منتج", bg=TK.ACCENT2, fg=TK.WHITE, font=('Arial', 10),
                 command=self.add_exchange, padx=15, pady=5).pack(side='left', padx=5)

        filter_frame = tk.Frame(control_frame, bg=TK.CARD)
        filter_frame.pack(side='right', padx=10)

        tk.Label(filter_frame, text="تصفية حسب التاريخ:", bg=TK.CARD, font=('Arial', 10)).pack(side='left', padx=5)
        self.filter_date = tk.Entry(filter_frame, width=12, font=('Arial', 10))
        self.filter_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.filter_date.pack(side='left', padx=5)
        tk.Button(filter_frame, text="عرض", bg=TK.ACCENT2, fg=TK.WHITE, font=('Arial', 9),
                 command=self.load_returns, padx=10, pady=2).pack(side='left', padx=5)
        tk.Button(filter_frame, text="عرض الكل", bg=TK.ACCENT,  fg=TK.WHITE, font=('Arial', 9),
                 command=self.load_all_returns, padx=10, pady=2).pack(side='left', padx=5)

        self.inner_notebook = ttk.Notebook(self.parent)
        self.inner_notebook.pack(fill='both', expand=True, padx=10, pady=5)

        self.returns_frame = tk.Frame(self.inner_notebook, bg=TK.CARD)
        self.inner_notebook.add(self.returns_frame, text="📋 المرتجعات")
        self.create_returns_tab()

        self.exchanges_frame = tk.Frame(self.inner_notebook, bg=TK.CARD)
        self.inner_notebook.add(self.exchanges_frame, text="🔄🔄 التبديلات")
        self.create_exchanges_tab()

    def create_returns_tab(self):
        summary_frame = tk.Frame(self.returns_frame, bg=TK.BG, relief='ridge', bd=1)
        summary_frame.pack(fill='x', padx=10, pady=5)
        self.returns_summary_label = tk.Label(summary_frame, text="📊 إجمالي المرتجعات: 0",
                                               font=('Arial', 11, 'bold'), bg=TK.BG, fg=TK.WARNING)
        self.returns_summary_label.pack(pady=5)

        tree_frame = tk.Frame(self.returns_frame, bg=TK.CARD)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        columns = ('رقم الإرجاع', 'الفاتورة الأصلية', 'المنتج', 'العميل', 'الكمية', 'سعر الإرجاع', 'الإجمالي', 'السبب', 'التاريخ', 'الحالة')
        self.returns_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=16)

        col_config = {
            'رقم الإرجاع':     (80,  False),
            'الفاتورة الأصلية': (90,  False),
            'المنتج':           (150, True),
            'العميل':           (120, True),
            'الكمية':           (60,  False),
            'سعر الإرجاع':     (85,  False),
            'الإجمالي':         (85,  False),
            'السبب':            (130, True),
            'التاريخ':          (105, False),
            'الحالة':           (75,  False),
        }
        for col in columns:
            w, stretch = col_config[col]
            self.returns_tree.heading(col, text=col, anchor='center')
            self.returns_tree.column(col, width=w, minwidth=50, stretch=stretch, anchor='center')

        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.returns_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.returns_tree.xview)
        self.returns_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.returns_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

    def create_exchanges_tab(self):
        summary_frame = tk.Frame(self.exchanges_frame, bg=TK.BG, relief='ridge', bd=1)
        summary_frame.pack(fill='x', padx=10, pady=5)
        self.exchanges_summary_label = tk.Label(summary_frame, text="📊 عدد التبديلات اليوم: 0",
                                                font=('Arial', 11, 'bold'), bg=TK.BG, fg=TK.ACCENT2)
        self.exchanges_summary_label.pack(pady=5)

        btn_frame = tk.Frame(self.exchanges_frame, bg=TK.CARD)
        btn_frame.pack(fill='x', padx=10, pady=5)

        tk.Button(btn_frame, text="🖨️ طباعة الفاتورة", bg=TK.ACCENT,  fg=TK.WHITE, font=('Arial', 9),
                 command=self.print_selected_exchange, padx=15, pady=3).pack(side='left', padx=5)

        tree_frame = tk.Frame(self.exchanges_frame, bg=TK.CARD)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        columns = ('رقم التبديل', 'الفاتورة', 'منتج مرتجع', 'كمية', 'منتج جديد', 'كمية جديدة', 'الفارق', 'العميل', 'التاريخ')
        self.exchanges_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=16)

        col_config = {
            'رقم التبديل': (85,  False),
            'الفاتورة':    (80,  False),
            'منتج مرتجع': (150, True),
            'كمية':        (60,  False),
            'منتج جديد':  (150, True),
            'كمية جديدة': (75,  False),
            'الفارق':      (90,  False),
            'العميل':      (120, True),
            'التاريخ':     (105, False),
        }
        for col in columns:
            w, stretch = col_config[col]
            self.exchanges_tree.heading(col, text=col, anchor='center')
            self.exchanges_tree.column(col, width=w, minwidth=50, stretch=stretch, anchor='center')

        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.exchanges_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.exchanges_tree.xview)
        self.exchanges_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.exchanges_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

    def print_selected_exchange(self):
        selected = self.exchanges_tree.selection()
        if not selected:
            messagebox.showwarning("تنبيه", "الرجاء اختيار عملية تبديل للطباعة")
            return

        values = self.exchanges_tree.item(selected[0])['values']
        exchange_number = values[0]

        exchanges = self.db.get_all_exchanges()
        exchange = None
        for exc in exchanges:
            if exc[1] == exchange_number:
                exchange = exc
                break

        if exchange:
            sales = self.db.get_sales_by_invoice(exchange[2])
            original_total = sum(sale[8] for sale in sales)

            invoice_data = {
                'exchange_number': exchange[1],
                'date': exchange[14],
                'customer_name': exchange[13],
                'original_invoice': exchange[2],
                'returned_items': [{
                    'name': exchange[4],
                    'quantity': exchange[6],
                    'price': exchange[7],
                    'total': exchange[6] * exchange[7]
                }],
                'new_items': [{
                    'name': exchange[9],
                    'quantity': exchange[10],
                    'price': exchange[11],
                    'total': exchange[10] * exchange[11]
                }],
                'original_total': original_total,
                'returned_total': exchange[6] * exchange[7],
                'new_total': exchange[10] * exchange[11],
                'price_difference': exchange[12],
                'reason': exchange[13]
            }

            printer = Printer(self.parent)
            file_path, pdf_path = printer.print_exchange_invoice(invoice_data)

            message = f"✓ تم حفظ وطباعة فاتورة التبديل رقم {exchange_number}\n\n"
            message += f"📁 تم حفظ الفاتورة في:\n{file_path}"
            if pdf_path:
                message += f"\n📄 نسخة PDF: {pdf_path}"

            messagebox.showinfo("طباعة", message)

    def load_returns(self):
        for item in self.returns_tree.get_children():
            self.returns_tree.delete(item)

        date = self.filter_date.get().strip()
        returns = self.db.get_returns_by_date(date)
        total = 0

        for ret in returns:
            self.returns_tree.insert('', 'end', values=(
                ret[1], ret[2], ret[4], ret[5], f"{ret[6]:.2f}",
                f"{ret[7]:.2f}", f"{ret[8]:.2f}", ret[9], ret[10], ret[11]
            ))
            total += ret[8]

        self.returns_summary_label.config(text=f"📊 إجمالي المرتجعات في {date}: {total:.2f}")

    def load_all_returns(self):
        for item in self.returns_tree.get_children():
            self.returns_tree.delete(item)

        returns = self.db.get_all_returns()
        total = 0

        for ret in returns:
            self.returns_tree.insert('', 'end', values=(
                ret[1], ret[2], ret[4], ret[5], f"{ret[6]:.2f}",
                f"{ret[7]:.2f}", f"{ret[8]:.2f}", ret[9], ret[10], ret[11]
            ))
            total += ret[8]

        self.returns_summary_label.config(text=f"📊 إجمالي جميع المرتجعات: {total:.2f}")
        self.filter_date.delete(0, tk.END)

    def load_exchanges(self):
        for item in self.exchanges_tree.get_children():
            self.exchanges_tree.delete(item)

        date = self.filter_date.get().strip() if self.filter_date.get() else datetime.now().strftime("%Y-%m-%d")
        exchanges = self.db.get_exchanges_by_date(date)

        for exc in exchanges:
            self.exchanges_tree.insert('', 'end', values=(
                exc[1], exc[2], exc[4], f"{exc[6]:.2f}", exc[8], f"{exc[10]:.2f}",
                f"{exc[12]:.2f}", exc[13], exc[14]
            ))

        self.exchanges_summary_label.config(text=f"📊 عدد التبديلات اليوم: {len(exchanges)}")

    def refresh_all(self):
        self.load_returns()
        self.load_exchanges()
        if self.on_material_change:
            self.on_material_change()

    def add_return(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("🔄 إرجاع منتج")
        dialog.geometry("700x700")
        dialog.configure(bg=TK.CARD)
        dialog.transient(self.parent)
        dialog.grab_set()

        tk.Label(dialog, text="🔄 إرجاع منتج", font=('Arial', 16, 'bold'),
                bg=TK.CARD, fg=TK.WARNING).pack(pady=15)

        main_frame = tk.Frame(dialog, bg=TK.CARD)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        invoice_frame = tk.LabelFrame(main_frame, text="🔍 البحث عن الفاتورة",
                                       font=('Arial', 12, 'bold'), bg=TK.CARD, fg=TK.ACCENT2)
        invoice_frame.pack(fill='x', pady=5)

        row1 = tk.Frame(invoice_frame, bg=TK.CARD)
        row1.pack(fill='x', padx=10, pady=10)

        tk.Label(row1, text="رقم الفاتورة:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)
        self.return_invoice_entry = tk.Entry(row1, font=('Arial', 11), width=15)
        self.return_invoice_entry.pack(side='right', padx=5)

        search_btn = tk.Button(row1, text="🔍 بحث", bg=TK.ACCENT,  fg=TK.WHITE, font=('Arial', 10),
                               command=lambda: self.search_invoice_for_return(), padx=15, pady=3)
        search_btn.pack(side='right', padx=5)

        self.return_customer_frame = tk.Frame(invoice_frame, bg=TK.BG, relief='ridge', bd=1)
        self.return_customer_frame.pack(fill='x', padx=10, pady=5)
        self.return_customer_label = tk.Label(self.return_customer_frame, text="👤 العميل: ---",
                                               font=('Arial', 11), bg=TK.BG, fg=TK.TEXT)
        self.return_customer_label.pack(pady=5, padx=10, anchor='w')

        self.return_date_label = tk.Label(self.return_customer_frame, text="📅 التاريخ: ---",
                                           font=('Arial', 11), bg=TK.BG, fg=TK.TEXT)
        self.return_date_label.pack(pady=5, padx=10, anchor='w')

        products_frame = tk.LabelFrame(main_frame, text="📦 منتجات الفاتورة",
                                        font=('Arial', 12, 'bold'), bg=TK.CARD, fg=TK.ACCENT2)
        products_frame.pack(fill='both', expand=True, pady=5)

        tree_frame = tk.Frame(products_frame, bg=TK.CARD)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        columns = ('الباركود', 'اسم المنتج', 'الكمية المباعة', 'سعر البيع', 'الإجمالي')
        self.return_products_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=6)

        col_widths = [100, 180, 80, 80, 100]
        for col, width in zip(columns, col_widths):
            self.return_products_tree.heading(col, text=col)
            self.return_products_tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.return_products_tree.yview)
        self.return_products_tree.configure(yscrollcommand=scrollbar.set)
        self.return_products_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.return_products_tree.bind('<<TreeviewSelect>>', self.on_return_product_select)

        return_frame = tk.LabelFrame(main_frame, text="📝 بيانات الإرجاع",
                                      font=('Arial', 12, 'bold'), bg=TK.CARD, fg=TK.WARNING)
        return_frame.pack(fill='x', pady=5)

        row2 = tk.Frame(return_frame, bg=TK.CARD)
        row2.pack(fill='x', padx=10, pady=10)

        tk.Label(row2, text="الكمية المرتجعة:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)
        self.return_qty_entry = tk.Entry(row2, font=('Arial', 11), width=15)
        self.return_qty_entry.pack(side='right', padx=5)

        tk.Label(row2, text=f"الحد الأقصى:", bg=TK.CARD, font=('Arial', 11), fg=TK.SUCCESS).pack(side='right', padx=5)
        self.return_max_qty_label = tk.Label(row2, text="0", bg=TK.CARD, font=('Arial', 11, 'bold'), fg=TK.SUCCESS)
        self.return_max_qty_label.pack(side='right', padx=5)

        row3 = tk.Frame(return_frame, bg=TK.CARD)
        row3.pack(fill='x', padx=10, pady=10)

        tk.Label(row3, text="سعر الإرجاع:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)
        self.return_price_entry = tk.Entry(row3, font=('Arial', 11), width=15)
        self.return_price_entry.pack(side='right', padx=5)

        row4 = tk.Frame(return_frame, bg=TK.CARD)
        row4.pack(fill='x', padx=10, pady=10)

        tk.Label(row4, text="سبب الإرجاع:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)
        reasons = ['عيوب في المنتج', 'منتج غير مطابق', 'خطأ في الفاتورة', 'تغيير رأي', 'منتج تالف', 'أخرى']
        self.return_reason_combo = ttk.Combobox(row4, values=reasons, width=20)
        self.return_reason_combo.set('أخرى')
        self.return_reason_combo.pack(side='right', padx=5)

        self.return_info_label = tk.Label(main_frame, text="", font=('Arial', 9), bg=TK.CARD, fg=TK.SUCCESS)
        self.return_info_label.pack(pady=5)

        btn_frame = tk.Frame(main_frame, bg=TK.CARD)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="💾 تسجيل الإرجاع", bg=TK.WARNING, fg=TK.WHITE, font=('Arial', 11),
                 command=self.save_return, padx=25, pady=8).pack(side='left', padx=10)
        tk.Button(btn_frame, text="❌ إلغاء", bg=TK.DANGER,  fg=TK.WHITE, font=('Arial', 11),
                 command=dialog.destroy, padx=25, pady=8).pack(side='left', padx=10)

        self.return_invoice_data = None
        self.return_selected_product = None

    def search_invoice_for_return(self):
        invoice_num_str = self.return_invoice_entry.get().strip()
        if not invoice_num_str:
            messagebox.showerror("خطأ", "الرجاء إدخال رقم فاتورة صحيح")
            return
        # نحاول البحث بالرقم كما هو (نص) ثم كـ integer لدعم الأرقام التي تبدأ بالصفر
        sales = self.db.get_sales_by_invoice(invoice_num_str)
        if not sales:
            try:
                invoice_num = int(invoice_num_str)
                sales = self.db.get_sales_by_invoice(invoice_num)
            except ValueError:
                pass

        if not sales:
            messagebox.showerror("خطأ", f"❌ لم يتم العثور على فاتورة رقم {invoice_num_str}")
            return

        self.return_invoice_data = {
            'invoice_number': sales[0][1],
            'customer': sales[0][4],
            'date': sales[0][14]
        }

        self.return_customer_label.config(text=f"👤 العميل: {sales[0][4]}")
        self.return_date_label.config(text=f"📅 التاريخ: {sales[0][14]}")

        for item in self.return_products_tree.get_children():
            self.return_products_tree.delete(item)

        products_summary = {}
        for sale in sales:
            barcode = sale[2]
            if barcode not in products_summary:
                products_summary[barcode] = {
                    'name': sale[3],
                    'quantity': 0,
                    'price': sale[7],
                    'total': 0
                }
            products_summary[barcode]['quantity'] += sale[6]
            products_summary[barcode]['total'] += sale[8]

        for barcode, data in products_summary.items():
            self.return_products_tree.insert('', 'end', iid='bc_' + str(barcode), values=(
                ' ' + str(barcode), data['name'], f"{data['quantity']:.2f}",
                f"{data['price']:.2f}", f"{data['total']:.2f}"
            ))

        self.return_info_label.config(text=f"✅ تم العثور على {len(products_summary)} منتج", fg=TK.SUCCESS)

    def on_return_product_select(self, event):
        selected = self.return_products_tree.selection()
        if not selected:
            return

        values = self.return_products_tree.item(selected[0])['values']

        self.return_selected_product = {
            'barcode': selected[0].replace('bc_', '', 1),  # من iid للحفاظ على الأصفار
            'name': values[1],
            'max_quantity': float(values[2]),
            'price': float(values[3])
        }

        self.return_max_qty_label.config(text=f"{self.return_selected_product['max_quantity']:.2f}")
        self.return_price_entry.delete(0, tk.END)
        self.return_price_entry.insert(0, str(self.return_selected_product['price']))
        self.return_qty_entry.delete(0, tk.END)
        self.return_qty_entry.focus()

    def save_return(self):
        if not self.return_invoice_data:
            messagebox.showerror("خطأ", "الرجاء البحث عن فاتورة أولاً")
            return

        if not self.return_selected_product:
            messagebox.showerror("خطأ", "الرجاء اختيار منتج للإرجاع")
            return

        try:
            quantity = float(self.return_qty_entry.get())
            if quantity <= 0:
                messagebox.showerror("خطأ", "الكمية يجب أن تكون أكبر من صفر")
                return
            if quantity > self.return_selected_product['max_quantity']:
                messagebox.showerror("خطأ", f"الكمية المرتجعة تتجاوز الكمية المباعة")
                return
        except Exception:
            messagebox.showerror("خطأ", "الكمية يجب أن تكون رقماً")
            return

        try:
            return_price = int(self.return_price_entry.get())
            if return_price <= 0:
                messagebox.showerror("خطأ", "سعر الإرجاع يجب أن يكون أكبر من صفر")
                return
        except Exception:
            messagebox.showerror("خطأ", "سعر الإرجاع يجب أن يكون رقماً")
            return

        reason = self.return_reason_combo.get()
        total_return = quantity * return_price
        return_number = self.db.get_next_return_number()
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.db.add_return(
            return_number,
            self.return_invoice_data['invoice_number'],
            self.return_selected_product['barcode'],
            self.return_selected_product['name'],
            self.return_invoice_data['customer'],
            quantity,
            return_price,
            total_return,
            reason,
            date
        )

        messagebox.showinfo("نجاح", f"✓ تم تسجيل الإرجاع رقم {return_number}")

        for widget in self.parent.winfo_children():
            if isinstance(widget, tk.Toplevel) and widget != self.parent:
                widget.destroy()

        self.load_returns()
        if self.on_material_change:
            self.on_material_change()

    def add_exchange(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("🔄🔄 تبديل منتج بآخر")
        dialog.geometry("900x700")
        dialog.configure(bg=TK.CARD)
        dialog.transient(self.parent)
        dialog.grab_set()

        main_canvas = tk.Canvas(dialog, bg=TK.CARD)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg=TK.CARD)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        main_frame = scrollable_frame

        tk.Label(main_frame, text="🔄🔄 تبديل منتج بآخر", font=('Arial', 18, 'bold'),
                bg=TK.CARD, fg=TK.ACCENT2).pack(pady=15)

        invoice_frame = tk.LabelFrame(main_frame, text="🔍 البحث عن الفاتورة",
                                       font=('Arial', 12, 'bold'), bg=TK.CARD, fg=TK.ACCENT)
        invoice_frame.pack(fill='x', pady=5, padx=10)

        row1 = tk.Frame(invoice_frame, bg=TK.CARD)
        row1.pack(fill='x', padx=10, pady=10)

        tk.Label(row1, text="رقم الفاتورة:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)
        self.ex_invoice_entry = tk.Entry(row1, font=('Arial', 11), width=15)
        self.ex_invoice_entry.pack(side='right', padx=5)

        search_btn = tk.Button(row1, text="🔍 بحث", bg=TK.ACCENT,  fg=TK.WHITE, font=('Arial', 10),
                               command=lambda: self.search_invoice_for_exchange(), padx=15, pady=3)
        search_btn.pack(side='right', padx=5)

        self.ex_customer_frame = tk.Frame(invoice_frame, bg=TK.BG, relief='ridge', bd=1)
        self.ex_customer_frame.pack(fill='x', padx=10, pady=5)
        self.ex_customer_label = tk.Label(self.ex_customer_frame, text="👤 العميل: ---",
                                           font=('Arial', 11), bg=TK.BG, fg=TK.TEXT)
        self.ex_customer_label.pack(pady=5, padx=10, anchor='w')

        self.ex_date_label = tk.Label(self.ex_customer_frame, text="📅 التاريخ: ---",
                                       font=('Arial', 11), bg=TK.BG, fg=TK.TEXT)
        self.ex_date_label.pack(pady=5, padx=10, anchor='w')

        return_frame = tk.LabelFrame(main_frame, text="📦 المنتج المراد إرجاعه",
                                      font=('Arial', 12, 'bold'), bg=TK.CARD, fg=TK.WARNING)
        return_frame.pack(fill='both', expand=True, pady=5, padx=10)

        tree_frame1 = tk.Frame(return_frame, bg=TK.CARD)
        tree_frame1.pack(fill='both', expand=True, padx=10, pady=5)

        columns1 = ('الباركود', 'اسم المنتج', 'الكمية المباعة', 'سعر البيع', 'الإجمالي')
        self.return_products_ex_tree = ttk.Treeview(tree_frame1, columns=columns1, show='headings', height=4)

        for col, width in zip(columns1, [100, 180, 80, 80, 100]):
            self.return_products_ex_tree.heading(col, text=col)
            self.return_products_ex_tree.column(col, width=width)

        scrollbar1 = ttk.Scrollbar(tree_frame1, orient='vertical', command=self.return_products_ex_tree.yview)
        self.return_products_ex_tree.configure(yscrollcommand=scrollbar1.set)
        self.return_products_ex_tree.pack(side='left', fill='both', expand=True)
        scrollbar1.pack(side='right', fill='y')

        self.return_products_ex_tree.bind('<<TreeviewSelect>>', self.on_ex_return_select)

        return_qty_frame = tk.Frame(return_frame, bg=TK.CARD)
        return_qty_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(return_qty_frame, text="الكمية المرتجعة:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)
        self.ex_return_qty = tk.Entry(return_qty_frame, font=('Arial', 11), width=15)
        self.ex_return_qty.pack(side='right', padx=5)
        self.ex_return_qty.bind('<KeyRelease>', self.calculate_exchange_difference)

        tk.Label(return_qty_frame, text="الحد الأقصى:", bg=TK.CARD, font=('Arial', 11), fg=TK.SUCCESS).pack(side='right', padx=5)
        self.ex_max_qty_label = tk.Label(return_qty_frame, text="0", bg=TK.CARD, font=('Arial', 11, 'bold'), fg=TK.SUCCESS)
        self.ex_max_qty_label.pack(side='right', padx=5)

        new_frame = tk.LabelFrame(main_frame, text="🆕 المنتج البديل",
                                   font=('Arial', 12, 'bold'), bg=TK.CARD, fg=TK.SUCCESS)
        new_frame.pack(fill='both', expand=True, pady=5, padx=10)

        note_label = tk.Label(new_frame, text="⚠️ ملاحظة: لا يمكن اختيار نفس المنتج كبديل",
                              font=('Arial', 9), bg=TK.CARD, fg=TK.DANGER)
        note_label.pack(pady=5)

        tree_frame2 = tk.Frame(new_frame, bg=TK.CARD)
        tree_frame2.pack(fill='both', expand=True, padx=10, pady=5)

        columns2 = ('الباركود', 'اسم المنتج', 'الوحدة', 'السعر', 'الكمية المتوفرة')
        self.new_products_tree = ttk.Treeview(tree_frame2, columns=columns2, show='headings', height=4)

        for col, width in zip(columns2, [100, 180, 70, 80, 100]):
            self.new_products_tree.heading(col, text=col)
            self.new_products_tree.column(col, width=width)

        scrollbar2 = ttk.Scrollbar(tree_frame2, orient='vertical', command=self.new_products_tree.yview)
        self.new_products_tree.configure(yscrollcommand=scrollbar2.set)
        self.new_products_tree.pack(side='left', fill='both', expand=True)
        scrollbar2.pack(side='right', fill='y')

        self.new_products_tree.bind('<<TreeviewSelect>>', self.on_ex_new_select)

        self.load_initial_exchange_products()

        new_qty_frame = tk.Frame(new_frame, bg=TK.CARD)
        new_qty_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(new_qty_frame, text="الكمية المطلوبة:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)
        self.ex_new_qty = tk.Entry(new_qty_frame, font=('Arial', 11), width=15)
        self.ex_new_qty.pack(side='right', padx=5)
        self.ex_new_qty.bind('<KeyRelease>', self.calculate_exchange_difference)

        tk.Label(new_qty_frame, text="الكمية المتوفرة:", bg=TK.CARD, font=('Arial', 11), fg=TK.SUCCESS).pack(side='right', padx=5)
        self.ex_available_qty_label = tk.Label(new_qty_frame, text="0", bg=TK.CARD, font=('Arial', 11, 'bold'), fg=TK.SUCCESS)
        self.ex_available_qty_label.pack(side='right', padx=5)

        diff_frame = tk.LabelFrame(main_frame, text="💰 حساب الفارق",
                                    font=('Arial', 12, 'bold'), bg=TK.CARD, fg=TK.WARNING)
        diff_frame.pack(fill='x', pady=5, padx=10)

        diff_inner = tk.Frame(diff_frame, bg=TK.CARD)
        diff_inner.pack(fill='x', padx=10, pady=10)

        tk.Label(diff_inner, text="قيمة المنتج المرتجع:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)
        self.ex_return_value_label = tk.Label(diff_inner, text="0", bg=TK.CARD, font=('Arial', 11, 'bold'), fg=TK.WARNING)
        self.ex_return_value_label.pack(side='right', padx=5)

        tk.Label(diff_inner, text="قيمة المنتج الجديد:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)
        self.ex_new_value_label = tk.Label(diff_inner, text="0", bg=TK.CARD, font=('Arial', 11, 'bold'), fg=TK.SUCCESS)
        self.ex_new_value_label.pack(side='right', padx=5)

        tk.Label(diff_inner, text="الفارق:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)
        self.ex_difference_label = tk.Label(diff_inner, text="0", bg=TK.CARD, font=('Arial', 12, 'bold'), fg=TK.WARNING)
        self.ex_difference_label.pack(side='right', padx=5)

        reason_frame = tk.LabelFrame(main_frame, text="📝 سبب التبديل",
                                      font=('Arial', 12, 'bold'), bg=TK.CARD, fg=TK.TEXT)
        reason_frame.pack(fill='x', pady=5, padx=10)

        reason_inner = tk.Frame(reason_frame, bg=TK.CARD)
        reason_inner.pack(fill='x', padx=10, pady=10)

        reasons = ['عيوب في المنتج', 'منتج غير مطابق', 'تغيير رأي', 'منتج أفضل', 'أخرى']
        self.ex_reason_combo = ttk.Combobox(reason_inner, values=reasons, width=30, font=('Arial', 11))
        self.ex_reason_combo.set('أخرى')
        self.ex_reason_combo.pack(side='right', padx=5)
        tk.Label(reason_inner, text="سبب التبديل:", bg=TK.CARD, font=('Arial', 11)).pack(side='right', padx=5)

        self.ex_info_label = tk.Label(main_frame, text="", font=('Arial', 9), bg=TK.CARD, fg=TK.SUCCESS)
        self.ex_info_label.pack(pady=5)

        btn_frame = tk.Frame(main_frame, bg=TK.CARD)
        btn_frame.pack(side='bottom', fill='x', pady=15, padx=10)

        btn_save = tk.Button(btn_frame, text="💾 تسجيل التبديل وطباعة الفاتورة",
                            bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 12, 'bold'),
                            command=lambda: self.save_exchange_with_print(dialog),
                            padx=20, pady=10)
        btn_save.pack(side='left', padx=5, expand=True, fill='x')

        btn_cancel = tk.Button(btn_frame, text="❌ إلغاء",
                              bg=TK.DANGER,  fg=TK.WHITE, font=('Arial', 12, 'bold'),
                              command=dialog.destroy, padx=20, pady=10)
        btn_cancel.pack(side='right', padx=5, expand=True, fill='x')

        status_frame = tk.Frame(main_frame, bg=TK.BG, relief='sunken', bd=1)
        status_frame.pack(fill='x', pady=10, padx=10)
        self.ex_status_label = tk.Label(status_frame, text="✅ جاهز - اختر المنتج المراد إرجاعه ثم المنتج البديل",
                                         font=('Arial', 9), bg=TK.BG, fg=TK.TEXT)
        self.ex_status_label.pack(pady=5)

        self.ex_invoice_data = None
        self.ex_return_product = None
        self.ex_new_product = None

    def load_initial_exchange_products(self):
        for item in self.new_products_tree.get_children():
            self.new_products_tree.delete(item)

        materials = self.db.get_all_materials()

        for mat in materials:
            if mat[5] > 0:
                barcode_str = str(mat[0])
                self.new_products_tree.insert('', 'end', iid='bc_' + barcode_str, values=(
                    ' ' + barcode_str, mat[1], mat[3], f"{mat[4]:.2f}", f"{mat[5]:.2f}"
                ))

    def load_exchange_products(self):
        for item in self.new_products_tree.get_children():
            self.new_products_tree.delete(item)

        materials = self.db.get_all_materials()

        for mat in materials:
            if mat[5] > 0:
                barcode_str = str(mat[0])
                if self.ex_return_product and barcode_str == str(self.ex_return_product['barcode']):
                    continue
                self.new_products_tree.insert('', 'end', iid='bc_' + barcode_str, values=(
                    ' ' + barcode_str, mat[1], mat[3], f"{mat[4]:.2f}", f"{mat[5]:.2f}"
                ))

    def search_invoice_for_exchange(self):
        invoice_num_str = self.ex_invoice_entry.get().strip()
        if not invoice_num_str:
            messagebox.showerror("خطأ", "الرجاء إدخال رقم فاتورة صحيح")
            return
        # نحاول البحث بالرقم كما هو ثم كـ integer لدعم الأرقام التي تبدأ بالصفر
        sales = self.db.get_sales_by_invoice(invoice_num_str)
        if not sales:
            try:
                invoice_num = int(invoice_num_str)
                sales = self.db.get_sales_by_invoice(invoice_num)
            except ValueError:
                pass

        if not sales:
            messagebox.showerror("خطأ", f"❌ لم يتم العثور على فاتورة رقم {invoice_num_str}")
            return

        self.ex_return_product = None
        self.ex_new_product = None

        if hasattr(self, 'ex_return_qty'):
            self.ex_return_qty.delete(0, tk.END)
        if hasattr(self, 'ex_new_qty'):
            self.ex_new_qty.delete(0, tk.END)

        self.ex_max_qty_label.config(text="0")
        self.ex_available_qty_label.config(text="0")
        self.ex_return_value_label.config(text="0")
        self.ex_new_value_label.config(text="0")
        self.ex_difference_label.config(text="0")

        self.load_initial_exchange_products()

        self.ex_invoice_data = {
            'invoice_number': sales[0][1],
            'customer': sales[0][4],
            'date': sales[0][14]
        }

        self.ex_customer_label.config(text=f"👤 العميل: {sales[0][4]}")
        self.ex_date_label.config(text=f"📅 التاريخ: {sales[0][14]}")

        for item in self.return_products_ex_tree.get_children():
            self.return_products_ex_tree.delete(item)

        products_summary = {}
        self.original_invoice_total = 0

        for sale in sales:
            barcode = sale[2]
            if barcode not in products_summary:
                products_summary[barcode] = {
                    'name': sale[3],
                    'quantity': 0,
                    'price': sale[7],
                    'total': 0
                }
            products_summary[barcode]['quantity'] += sale[6]
            products_summary[barcode]['total'] += sale[8]
            self.original_invoice_total += sale[8]

        for barcode, data in products_summary.items():
            barcode_str = str(barcode)
            self.return_products_ex_tree.insert('', 'end', iid='bc_' + barcode_str, values=(
                ' ' + barcode_str, data['name'], f"{data['quantity']:.2f}",
                f"{data['price']:.2f}", f"{data['total']:.2f}"
            ))

        self.ex_info_label.config(text=f"✅ تم العثور على {len(products_summary)} منتج - إجمالي الفاتورة: {self.original_invoice_total:.2f}", fg=TK.SUCCESS)
        self.ex_status_label.config(text=f"✅ تم العثور على فاتورة رقم {invoice_num_str} - اختر المنتج المراد إرجاعه")

    def on_ex_return_select(self, event):
        selected = self.return_products_ex_tree.selection()
        if not selected:
            return

        values = self.return_products_ex_tree.item(selected[0])['values']
        real_barcode = selected[0].replace('bc_', '', 1)  # من iid

        if self.ex_new_product and real_barcode == str(self.ex_new_product['barcode']):
            messagebox.showwarning("⚠️ تنبيه", "هذا المنتج تم اختياره بالفعل كمنتج بديل!\nالرجاء اختيار منتج مختلف للإرجاع.")
            self.return_products_ex_tree.selection_remove(selected)
            return

        self.ex_return_product = {
            'barcode': real_barcode,
            'name': values[1],
            'max_quantity': float(values[2]),
            'price': float(values[3])
        }

        self.ex_max_qty_label.config(text=f"{self.ex_return_product['max_quantity']:.2f}")
        self.ex_return_qty.delete(0, tk.END)
        self.ex_return_qty.focus()
        self.calculate_exchange_difference()

        self.load_exchange_products()

        self.ex_info_label.config(text=f"✅ تم اختيار للإرجاع: {self.ex_return_product['name']}", fg=TK.SUCCESS)
        self.ex_status_label.config(text=f"✅ تم اختيار {self.ex_return_product['name']} للإرجاع - اختر المنتج البديل الآن")

    def on_ex_new_select(self, event):
        selected = self.new_products_tree.selection()
        if not selected:
            return

        values = self.new_products_tree.item(selected[0])['values']
        real_barcode = selected[0].replace('bc_', '', 1)  # من iid

        if self.ex_return_product and real_barcode == str(self.ex_return_product['barcode']):
            messagebox.showwarning("⚠️ تنبيه", "لا يمكنك اختيار نفس المنتج كبديل!\nالرجاء اختيار منتج مختلف.")
            self.new_products_tree.selection_remove(selected)
            return

        self.ex_new_product = {
            'barcode': real_barcode,
            'name': values[1],
            'available_quantity': float(values[4]),
            'price': float(values[3])
        }

        self.ex_available_qty_label.config(text=f"{self.ex_new_product['available_quantity']:.2f}")
        self.ex_new_qty.delete(0, tk.END)
        self.ex_new_qty.focus()

        self.ex_info_label.config(text=f"✅ تم اختيار: {self.ex_new_product['name']}", fg=TK.SUCCESS)
        self.ex_status_label.config(text=f"✅ تم اختيار {self.ex_new_product['name']} كمنتج بديل - أدخل الكميات ثم اضغط تسجيل")
        self.calculate_exchange_difference()

    def calculate_exchange_difference(self, event=None):
        try:
            return_qty = float(self.ex_return_qty.get()) if self.ex_return_qty.get() else 0
            new_qty = float(self.ex_new_qty.get()) if self.ex_new_qty.get() else 0

            if self.ex_return_product:
                return_value = return_qty * self.ex_return_product['price']
                self.ex_return_value_label.config(text=f"{return_value:.2f}")
            else:
                return_value = 0

            if self.ex_new_product:
                new_value = new_qty * self.ex_new_product['price']
                self.ex_new_value_label.config(text=f"{new_value:.2f}")
            else:
                new_value = 0

            difference = new_value - return_value
            self.ex_difference_label.config(text=f"{difference:.2f}")

            if difference > 0:
                self.ex_difference_label.config(fg=TK.DANGER)
            elif difference < 0:
                self.ex_difference_label.config(fg=TK.SUCCESS)
            else:
                self.ex_difference_label.config(fg=TK.WARNING)
        except Exception:
            pass

    def save_exchange_with_print(self, dialog):
        if not self.ex_invoice_data:
            messagebox.showerror("خطأ", "الرجاء البحث عن فاتورة أولاً")
            return

        if not self.ex_return_product:
            messagebox.showerror("خطأ", "الرجاء اختيار منتج للإرجاع")
            return

        if not self.ex_new_product:
            messagebox.showerror("خطأ", "الرجاء اختيار منتج بديل")
            return

        try:
            return_qty = float(self.ex_return_qty.get())
            if return_qty <= 0:
                messagebox.showerror("خطأ", "كمية الإرجاع يجب أن تكون أكبر من صفر")
                return
            if return_qty > self.ex_return_product['max_quantity']:
                messagebox.showerror("خطأ", f"كمية الإرجاع ({return_qty}) تتجاوز الكمية المباعة ({self.ex_return_product['max_quantity']})")
                return
        except Exception:
            messagebox.showerror("خطأ", "كمية الإرجاع يجب أن تكون رقماً")
            return

        try:
            new_qty = float(self.ex_new_qty.get())
            if new_qty <= 0:
                messagebox.showerror("خطأ", "كمية المنتج الجديد يجب أن تكون أكبر من صفر")
                return
            if new_qty > self.ex_new_product['available_quantity']:
                messagebox.showerror("خطأ", f"الكمية المطلوبة ({new_qty}) غير متوفرة في المخزون (المتوفرة: {self.ex_new_product['available_quantity']})")
                return
        except Exception:
            messagebox.showerror("خطأ", "كمية المنتج الجديد يجب أن تكون رقماً")
            return

        reason = self.ex_reason_combo.get()
        return_value = return_qty * self.ex_return_product['price']
        new_value = new_qty * self.ex_new_product['price']
        price_difference = new_value - return_value

        exchange_number = self.db.get_next_exchange_number()
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        calculation_details = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    📊 تفاصيل حساب الفاتورة                       ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                 ║
║  📋 الفاتورة الأصلية: {self.ex_invoice_data['invoice_number']}
║  💰 إجمالي الفاتورة الأصلية: {self.original_invoice_total:.2f}
║                                                                 ║
║  🔄 عملية التبديل:                                               ║
║  ❌ تم إرجاع: {self.ex_return_product['name']}                 ║
║     الكمية: {return_qty} × {self.ex_return_product['price']} = {return_value:.2f} ║
║                                                                 ║
║  ✅ تم أخذ: {self.ex_new_product['name']}                      ║
║     الكمية: {new_qty} × {self.ex_new_product['price']} = {new_value:.2f} ║
║                                                                 ║
║  📊 حساب الإجمالي الجديد:                                       ║
║     الإجمالي الأصلي:     {self.original_invoice_total:>10.2f}              ║
║     - قيمة المرتجع:      {return_value:>10.2f}              ║
║     + قيمة الجديد:       {new_value:>10.2f}              ║
║     {'='*50}                                                  ║
║     الإجمالي الجديد:     {(self.original_invoice_total - return_value + new_value):>10.2f} ║
║                                                                 ║
║  💰 الفارق المالي: {price_difference:.2f}                       ║
╚══════════════════════════════════════════════════════════════════╝
"""

        result = messagebox.askyesno("تأكيد عملية التبديل",
            f"{calculation_details}\n\nهل تريد تأكيد عملية التبديل؟\n(بعد التأكيد سيتم حفظ وطباعة الفاتورة)")

        if not result:
            return

        self.db.add_exchange(
            exchange_number,
            self.ex_invoice_data['invoice_number'],
            self.ex_return_product['barcode'],
            self.ex_return_product['name'],
            return_qty,
            self.ex_return_product['price'],
            self.ex_new_product['barcode'],
            self.ex_new_product['name'],
            new_qty,
            self.ex_new_product['price'],
            price_difference,
            self.ex_invoice_data['customer'],
            reason,
            date
        )

        exchange_data = {
            'exchange_number': exchange_number,
            'date': date,
            'customer_name': self.ex_invoice_data['customer'],
            'original_invoice': self.ex_invoice_data['invoice_number'],
            'returned_items': [{
                'name': self.ex_return_product['name'],
                'quantity': return_qty,
                'price': self.ex_return_product['price'],
                'total': return_value
            }],
            'new_items': [{
                'name': self.ex_new_product['name'],
                'quantity': new_qty,
                'price': self.ex_new_product['price'],
                'total': new_value
            }],
            'original_total': self.original_invoice_total,
            'returned_total': return_value,
            'new_total': new_value,
            'price_difference': price_difference,
            'reason': reason
        }

        printer = Printer(self.parent)
        file_path, pdf_path = printer.print_exchange_invoice(exchange_data)

        message = f"✓ تم تسجيل التبديل رقم {exchange_number}\n\n"
        message += f"📦 تم إرجاع: {self.ex_return_product['name']} (كمية: {return_qty})\n"
        message += f"🆕 تم أخذ: {self.ex_new_product['name']} (كمية: {new_qty})\n"
        message += f"\n📊 حساب الفاتورة:\n"
        message += f"   الإجمالي الأصلي: {self.original_invoice_total:.2f}\n"
        message += f"   - قيمة المرتجع: {return_value:.2f}\n"
        message += f"   + قيمة الجديد: {new_value:.2f}\n"
        message += f"   = الإجمالي الجديد: {(self.original_invoice_total - return_value + new_value):.2f}\n"

        if price_difference > 0:
            message += f"\n💰 يدفع العميل فرق: {price_difference:.2f}"
        elif price_difference < 0:
            message += f"\n💰 يسترد العميل فرق: {abs(price_difference):.2f}"
        else:
            message += f"\n💰 لا يوجد فروق مالية"

        message += f"\n\n📁 تم حفظ الفاتورة في:\n{file_path}"
        if pdf_path:
            message += f"\n📄 نسخة PDF: {pdf_path}"

        messagebox.showinfo("نجاح", message)

        dialog.destroy()

        self.load_exchanges()
        if self.on_material_change:
            self.on_material_change()

