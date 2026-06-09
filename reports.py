"""reports.py — نوافذ التقارير (يومي، شهري، مخزون)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class Reports:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db

    def show_daily_report(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("التقرير اليومي")
        dialog.geometry("1200x700")
        dialog.configure(bg='white')

        today = datetime.now().strftime("%Y-%m-%d")

        tk.Label(dialog, text=f"📊 التقرير اليومي - {today}", font=('Arial', 16, 'bold'),
                bg='white', fg='#9b59b6').pack(pady=15)

        sales = self.db.get_sales_by_date(today)
        expenses = self.db.get_expenses_by_date(today)
        returns = self.db.get_returns_by_date(today)
        total_returns = self.db.get_total_returns_by_date(today)

        sales_frame = tk.LabelFrame(dialog, text="💰 المبيعات", font=('Arial', 12, 'bold'), bg='white', fg='#27ae60')
        sales_frame.pack(fill='x', padx=15, pady=5)

        frame1 = tk.Frame(sales_frame, bg='white')
        frame1.pack(fill='x', padx=5, pady=5)

        columns = ('رقم الفاتورة', 'العميل', 'المنتج', 'الكمية', 'الإجمالي')
        tree = ttk.Treeview(frame1, columns=columns, show='headings', height=5)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)

        scrollbar = ttk.Scrollbar(frame1, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='left', fill='x', expand=True)
        scrollbar.pack(side='right', fill='y')

        total_sales = 0
        for sale in sales:
            tree.insert('', 'end', values=(sale[1], sale[4], sale[3], sale[6], f"{sale[8]:.2f}"))
            total_sales += sale[8]

        returns_frame = tk.LabelFrame(dialog, text="🔄 المرتجعات", font=('Arial', 12, 'bold'), bg='white', fg='#e67e22')
        returns_frame.pack(fill='x', padx=15, pady=5)

        frame_returns = tk.Frame(returns_frame, bg='white')
        frame_returns.pack(fill='x', padx=5, pady=5)

        returns_columns = ('رقم الإرجاع', 'الفاتورة الأصلية', 'المنتج', 'الكمية', 'المبلغ', 'السبب')
        returns_tree = ttk.Treeview(frame_returns, columns=returns_columns, show='headings', height=3)
        for col in returns_columns:
            returns_tree.heading(col, text=col)
            returns_tree.column(col, width=120)

        returns_scroll = ttk.Scrollbar(frame_returns, orient='vertical', command=returns_tree.yview)
        returns_tree.configure(yscrollcommand=returns_scroll.set)
        returns_tree.pack(side='left', fill='x', expand=True)
        returns_scroll.pack(side='right', fill='y')

        for ret in returns:
            returns_tree.insert('', 'end', values=(ret[1], ret[2], ret[4], ret[6], f"{ret[8]:.2f}", ret[9]))

        expenses_frame = tk.LabelFrame(dialog, text="💸 المصروفات", font=('Arial', 12, 'bold'), bg='white', fg='#e74c3c')
        expenses_frame.pack(fill='x', padx=15, pady=5)

        frame2 = tk.Frame(expenses_frame, bg='white')
        frame2.pack(fill='x', padx=5, pady=5)

        exp_columns = ('الفئة', 'المبلغ', 'الوصف')
        exp_tree = ttk.Treeview(frame2, columns=exp_columns, show='headings', height=3)
        for col in exp_columns:
            exp_tree.heading(col, text=col)
            exp_tree.column(col, width=150)

        exp_scroll = ttk.Scrollbar(frame2, orient='vertical', command=exp_tree.yview)
        exp_tree.configure(yscrollcommand=exp_scroll.set)
        exp_tree.pack(side='left', fill='x', expand=True)
        exp_scroll.pack(side='right', fill='y')

        total_expenses = 0
        for exp in expenses:
            exp_tree.insert('', 'end', values=(exp[2], f"{exp[3]:.2f}", exp[4]))
            total_expenses += exp[3]

        total_purchase_cost = self.db.get_purchase_cost_by_date(today)
        net_profit_with_cogs = total_sales - total_returns - total_purchase_cost

        summary_frame = tk.Frame(dialog, bg='#2c3e50', relief='ridge', bd=1)
        summary_frame.pack(fill='x', padx=15, pady=10)

        tk.Label(summary_frame, text="📊 ملخص اليوم", font=('Arial', 12, 'bold'),
                bg='#2c3e50', fg='white').pack(pady=(8,4))

        row1 = tk.Frame(summary_frame, bg='#2c3e50')
        row1.pack(fill='x', padx=10, pady=2)

        def stat_box(parent, label, value, color):
            f = tk.Frame(parent, bg=color, padx=12, pady=6)
            f.pack(side='left', expand=True, fill='x', padx=4)
            tk.Label(f, text=label, font=('Arial', 9), bg=color, fg='white').pack()
            tk.Label(f, text=f"{value:,.0f} ل.س", font=('Arial', 11, 'bold'), bg=color, fg='white').pack()

        stat_box(row1, "💰 المبيعات",         total_sales,             '#27ae60')
        stat_box(row1, "🔄 المرتجعات",        total_returns,           '#e67e22')
        stat_box(row1, "🛒 تكلفة المشتريات",  total_purchase_cost,     '#8e44ad')
        stat_box(row1, "💸 المصاريف",          total_expenses,          '#e74c3c')

        profit_color = '#27ae60' if net_profit_with_cogs >= 0 else '#e74c3c'
        profit_frame = tk.Frame(summary_frame, bg=profit_color, padx=12, pady=8)
        profit_frame.pack(fill='x', padx=14, pady=(4,10))
        sign = "▲" if net_profit_with_cogs >= 0 else "▼"
        tk.Label(profit_frame,
                 text=f"📈 صافي الربح = مبيعات - مرتجعات - تكلفة المشتريات",
                 font=('Arial', 9), bg=profit_color, fg='white').pack()
        tk.Label(profit_frame,
                 text=f"{sign} {net_profit_with_cogs:,.0f} ل.س",
                 font=('Arial', 14, 'bold'), bg=profit_color, fg='white').pack()

        tk.Button(dialog, text="إغلاق", bg='#e74c3c', fg='white', command=dialog.destroy, padx=20, pady=5).pack(pady=10)

    def show_monthly_report(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("التقرير الشهري")
        dialog.geometry("1300x750")
        dialog.configure(bg='white')

        tk.Label(dialog, text="📅 التقرير الشهري", font=('Arial', 16, 'bold'),
                bg='white', fg='#9b59b6').pack(pady=15)

        control_frame = tk.Frame(dialog, bg='white')
        control_frame.pack(pady=10)

        tk.Label(control_frame, text="السنة:", bg='white', font=('Arial', 11)).pack(side='left', padx=5)
        year_entry = tk.Entry(control_frame, width=8, font=('Arial', 11))
        year_entry.insert(0, datetime.now().strftime("%Y"))
        year_entry.pack(side='left', padx=5)

        tk.Label(control_frame, text="الشهر:", bg='white', font=('Arial', 11)).pack(side='left', padx=5)
        month_combo = ttk.Combobox(control_frame, values=list(range(1, 13)), width=6)
        month_combo.set(datetime.now().month)
        month_combo.pack(side='left', padx=5)

        frame = tk.Frame(dialog, bg='white')
        frame.pack(fill='both', expand=True, padx=15, pady=5)

        columns = ('التاريخ', 'المبيعات', 'المرتجعات', 'تكلفة المشتريات', 'المصاريف', 'صافي الربح')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=22)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=180, anchor='center')

        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        summary_label = tk.Label(dialog, text="", font=('Arial', 11, 'bold'), bg='#2c3e50', fg='white')
        summary_label.pack(fill='x', padx=15, pady=5)

        def load_report():
            for item in tree.get_children():
                tree.delete(item)

            year = int(year_entry.get())
            month = int(month_combo.get())

            days_data = {}

            sales = self.db.get_sales_by_month(year, month)
            for sale in sales:
                date = sale[14].split()[0]
                if date not in days_data:
                    days_data[date] = {'sales': 0, 'returns': 0, 'expenses': 0, 'purchases': 0}
                days_data[date]['sales'] += sale[8]

            returns = self.db.get_returns_by_month(year, month)
            for ret in returns:
                date = ret[10].split()[0]
                if date not in days_data:
                    days_data[date] = {'sales': 0, 'returns': 0, 'expenses': 0, 'purchases': 0}
                days_data[date]['returns'] += ret[8]

            expenses = self.db.get_expenses_by_month(year, month)
            for exp in expenses:
                date = exp[1]
                if date not in days_data:
                    days_data[date] = {'sales': 0, 'returns': 0, 'expenses': 0, 'purchases': 0}
                days_data[date]['expenses'] += exp[3]

            # تكلفة المشتريات حسب invoice_date
            cursor = self.db.conn.cursor()
            cursor.execute(
                "SELECT invoice_date, COALESCE(SUM(total_amount),0) FROM supplier_invoices "
                "WHERE invoice_date LIKE ? GROUP BY invoice_date",
                (f'{year}-{month:02d}%',)
            )
            for inv_date, inv_total in cursor.fetchall():
                date = inv_date.split()[0]
                if date not in days_data:
                    days_data[date] = {'sales': 0, 'returns': 0, 'expenses': 0, 'purchases': 0}
                days_data[date]['purchases'] += inv_total

            total_sales = 0
            total_returns = 0
            total_expenses = 0
            total_purchases = 0

            for date, data in sorted(days_data.items()):
                profit = data['sales'] - data['returns'] - data['purchases']
                profit_str = f"{profit:,.0f}"
                tag = 'profit' if profit >= 0 else 'loss'
                tree.insert('', 'end', tags=(tag,), values=(
                    date,
                    f"{data['sales']:,.0f}",
                    f"{data['returns']:,.0f}",
                    f"{data['purchases']:,.0f}",
                    f"{data['expenses']:,.0f}",
                    profit_str
                ))
                total_sales += data['sales']
                total_returns += data['returns']
                total_expenses += data['expenses']
                total_purchases += data['purchases']

            tree.tag_configure('profit', foreground='#27ae60')
            tree.tag_configure('loss',   foreground='#e74c3c')
            tree.tag_configure('manual', foreground='#8e44ad')
            tree.tag_configure('total',  background='#2c3e50', foreground='white')

            # صف الإجمالي داخل الجدول
            total_profit = total_sales - total_returns - total_purchases
            total_sign = "▲" if total_profit >= 0 else "▼"
            tree.insert('', 'end', tags=('total',), values=(
                "📊 الإجمالي",
                f"{total_sales:,.0f}",
                f"{total_returns:,.0f}",
                f"{total_purchases:,.0f}",
                f"{total_expenses:,.0f}",
                f"{total_sign} {total_profit:,.0f}"
            ))

            # تحقق إذا في ربح يدوي محفوظ لهاد الشهر
            manual = self.db.get_manual_profit(year, month)
            if manual:
                sales_profit   = manual[0]
                notes_str      = f"  ({manual[1]})" if manual[1] else ""
                printing_profit = manual[2] if len(manual) > 2 and manual[2] else 0
                net_profit     = sales_profit + printing_profit
                sign           = "▲" if net_profit >= 0 else "▼"
                printing_str   = f"  🖨️ طباعة: {printing_profit:,.0f}" if printing_profit else ""
                summary_label.config(
                    bg='#8e44ad',
                    text=(f"   📝 يدوي{notes_str}   💰 مبيعات: {sales_profit:,.0f}{printing_str}"
                          f"   |   📊 الإجمالي: {sign} {net_profit:,.0f} ل.س   ")
                )
            else:
                net_profit = total_sales - total_returns - total_purchases
                sign = "▲" if net_profit >= 0 else "▼"
                bg = '#27ae60' if net_profit >= 0 else '#e74c3c'
                summary_label.config(
                    bg=bg,
                    text=(f"   💰 {total_sales:,.0f}  −  🔄 {total_returns:,.0f}  −  "
                          f"🛒 {total_purchases:,.0f}  "
                          f"=  📈 صافي الربح: {sign} {net_profit:,.0f} ل.س   ")
                )

        def save_manual_profit():
            try:
                year  = int(year_entry.get())
                month = int(month_combo.get())
            except ValueError:
                messagebox.showerror("خطأ", "اختر السنة والشهر أولاً", parent=dialog)
                return

            month_names = {1:'يناير',2:'فبراير',3:'مارس',4:'أبريل',5:'مايو',6:'يونيو',
                           7:'يوليو',8:'أغسطس',9:'سبتمبر',10:'أكتوبر',11:'نوفمبر',12:'ديسمبر'}

            win = tk.Toplevel(dialog)
            win.title(f"إدخال أرباح {month_names.get(month,month)} {year}")
            win.geometry("420x340")
            win.configure(bg='white')
            win.resizable(False, False)
            win.grab_set()

            tk.Label(win, text=f"📝 أرباح {month_names.get(month,month)} {year}",
                     font=('Arial', 13, 'bold'), bg='white', fg='#8e44ad').pack(pady=(15,5))

            existing = self.db.get_manual_profit(year, month)
            # existing: (net_profit, notes, printing_profit)

            frm = tk.Frame(win, bg='white')
            frm.pack(pady=8)

            tk.Label(frm, text="💰 صافي ربح المبيعات (ل.س):", bg='white',
                     font=('Arial', 11, 'bold')).grid(row=0, column=0, sticky='e', padx=10, pady=6)
            profit_var = tk.StringVar(value=str(int(existing[0])) if existing else "")
            tk.Entry(frm, textvariable=profit_var, font=('Arial', 12), width=18,
                     justify='center').grid(row=0, column=1, padx=10, pady=6)

            tk.Label(frm, text="🖨️ صافي ربح الطباعة (ل.س):", bg='white',
                     font=('Arial', 11, 'bold'), fg='#2980b9').grid(row=1, column=0, sticky='e', padx=10, pady=6)
            printing_var = tk.StringVar(value=str(int(existing[2])) if existing and existing[2] else "0")
            tk.Entry(frm, textvariable=printing_var, font=('Arial', 12), width=18,
                     justify='center', fg='#2980b9').grid(row=1, column=1, padx=10, pady=6)

            tk.Label(frm, text="📝 ملاحظة (اختياري):", bg='white',
                     font=('Arial', 11)).grid(row=2, column=0, sticky='e', padx=10, pady=6)
            notes_var = tk.StringVar(value=existing[1] if existing else "")
            tk.Entry(frm, textvariable=notes_var, font=('Arial', 11), width=18,
                     justify='center').grid(row=2, column=1, padx=10, pady=6)

            # إجمالي مباشر
            total_lbl = tk.Label(win, text="", bg='#eaf4ff', font=('Arial', 12, 'bold'),
                                  fg='#1a3a5c', relief='ridge', padx=10, pady=6)
            total_lbl.pack(fill='x', padx=30, pady=4)

            def update_total(*args):
                try:
                    v = float(profit_var.get().replace(',','') or 0)
                except: v = 0
                try:
                    p = float(printing_var.get().replace(',','') or 0)
                except: p = 0
                total_lbl.config(text=f"📊 الإجمالي الكلي: {v+p:,.0f} ل.س  (مبيعات {v:,.0f} + طباعة {p:,.0f})")

            profit_var.trace_add('write', update_total)
            printing_var.trace_add('write', update_total)
            update_total()

            def do_save():
                try:
                    val = float(profit_var.get().replace(',', ''))
                except ValueError:
                    messagebox.showerror("خطأ", "أدخل رقماً صحيحاً لصافي ربح المبيعات", parent=win)
                    return
                try:
                    printing_val = float(printing_var.get().replace(',', ''))
                except ValueError:
                    messagebox.showerror("خطأ", "أدخل رقماً صحيحاً لصافي ربح الطباعة", parent=win)
                    return
                self.db.set_manual_profit(year, month, val, notes_var.get().strip(), printing_val)
                total = val + printing_val
                messagebox.showinfo("تم ✅",
                    f"تم الحفظ ✅\n"
                    f"💰 ربح المبيعات: {val:,.0f} ل.س\n"
                    f"🖨️ ربح الطباعة: {printing_val:,.0f} ل.س\n"
                    f"📊 الإجمالي: {total:,.0f} ل.س", parent=win)
                win.destroy()
                load_report()

            tk.Button(win, text="💾 حفظ", bg='#8e44ad', fg='white',
                      font=('Arial', 12, 'bold'), padx=20, pady=5,
                      command=do_save).pack(pady=12)

        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="📊 عرض التقرير", bg='#3498db', fg='white', font=('Arial', 11),
                 command=load_report, padx=20, pady=5).pack(side='left', padx=10)
        tk.Button(btn_frame, text="📝 إدخال ربح يدوي", bg='#8e44ad', fg='white', font=('Arial', 11),
                 command=save_manual_profit, padx=20, pady=5).pack(side='left', padx=10)
        tk.Button(btn_frame, text="إغلاق", bg='#e74c3c', fg='white', font=('Arial', 11),
                 command=dialog.destroy, padx=20, pady=5).pack(side='left', padx=10)

        load_report()

    def show_inventory_report(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("تقرير المخزون")
        dialog.geometry("1000x600")
        dialog.configure(bg='white')

        tk.Label(dialog, text="📦 تقرير المخزون الحالي", font=('Arial', 16, 'bold'),
                bg='white', fg='#9b59b6').pack(pady=15)

        frame = tk.Frame(dialog, bg='white')
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

            tree.insert('', 'end', values=(
                mat[0], mat[1], mat[3], f"{mat[4]:.2f}", f"{mat[5]:.2f}", f"{mat[6]:.2f}", status
            ))

        summary_frame = tk.Frame(dialog, bg='#f0f2f5', relief='ridge', bd=1)
        summary_frame.pack(fill='x', padx=15, pady=10)

        tk.Label(summary_frame, text=f"💰 القيمة الإجمالية للمخزون: {total_value:.2f}", font=('Arial', 12, 'bold'),
                bg='#f0f2f5', fg='#27ae60').pack(side='left', padx=20, pady=8)

        low_stock = self.db.get_low_stock_materials()
        tk.Label(summary_frame, text=f"⚠️ مواد أقل من الحد الأدنى: {len(low_stock)}", font=('Arial', 12, 'bold'),
                bg='#f0f2f5', fg='#f39c12').pack(side='left', padx=20, pady=8)

        out_stock = self.db.get_out_of_stock_materials()
        tk.Label(summary_frame, text=f"❌ مواد نفدت (ممنوع البيع): {len(out_stock)}", font=('Arial', 12, 'bold'),
                bg='#f0f2f5', fg='#e74c3c').pack(side='left', padx=20, pady=8)

        tk.Button(dialog, text="إغلاق", bg='#e74c3c', fg='white', command=dialog.destroy, padx=20, pady=5).pack(pady=10)

