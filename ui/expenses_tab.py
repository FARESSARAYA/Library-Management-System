"""expenses_tab.py — تبويب المصروفات"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
from theme_tk import TK, apply_theme, setup_treeview, fill_treeview, style_button, style_entry, make_card
from tkinter import filedialog
import pandas as pd
from datetime import datetime
from database import Database

class ExpensesTab:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db
        self.selected_id = None
        self.create_widgets()
        # عرض جميع المصروفات عند فتح البرنامج (وليس فقط اليوم)
        self.load_all_expenses()

    def create_widgets(self):
        control_frame = tk.Frame(self.parent, bg=TK.CARD)
        control_frame.pack(fill='x', padx=10, pady=10)

        filter_frame = tk.LabelFrame(control_frame, text="تصفية حسب التاريخ", font=('Arial', 10, 'bold'),
                                      bg=TK.CARD, fg=TK.TEXT)
        filter_frame.pack(side='left', padx=10, pady=5)

        tk.Label(filter_frame, text="التاريخ:", bg=TK.CARD, font=('Arial', 10)).pack(side='left', padx=5)
        self.filter_date = tk.Entry(filter_frame, width=12, font=('Arial', 10))
        self.filter_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.filter_date.pack(side='left', padx=5)

        tk.Button(filter_frame, text="عرض", bg=TK.ACCENT,  fg=TK.WHITE, font=('Arial', 9),
                 command=self.load_expenses, padx=10, pady=2).pack(side='left', padx=5)
        tk.Button(filter_frame, text="عرض الكل", bg=TK.ACCENT2, fg=TK.WHITE, font=('Arial', 9),
                 command=self.load_all_expenses, padx=10, pady=2).pack(side='left', padx=5)

        btn_frame = tk.Frame(control_frame, bg=TK.CARD)
        btn_frame.pack(side='right', padx=10)

        tk.Button(btn_frame, text="➕ إضافة مصروف", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 9),
                 command=self.add_expense, padx=12, pady=3).pack(side='left', padx=3)
        tk.Button(btn_frame, text="📥 استيراد من Excel", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 9),
                 command=self.import_from_excel, padx=12, pady=3).pack(side='left', padx=3)
        tk.Button(btn_frame, text="✏️ تعديل", bg=TK.WARNING, fg=TK.WHITE, font=('Arial', 9),
                 command=self.edit_expense, padx=12, pady=3).pack(side='left', padx=3)
        tk.Button(btn_frame, text="🗑️ حذف", bg=TK.DANGER,  fg=TK.WHITE, font=('Arial', 9),
                 command=self.delete_expense, padx=12, pady=3).pack(side='left', padx=3)

        summary_frame = tk.Frame(self.parent, bg=TK.BG, relief='ridge', bd=1)
        summary_frame.pack(fill='x', padx=10, pady=5)
        self.summary_label = tk.Label(summary_frame, text="📊 إجمالي مصروفات اليوم: 0",
                                       font=('Arial', 11, 'bold'), bg=TK.BG, fg=TK.DANGER)
        self.summary_label.pack(pady=5)

        tree_frame = tk.Frame(self.parent, bg=TK.CARD)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        columns = ('ID', 'التاريخ', 'الفئة', 'المبلغ', 'الوصف')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=16)

        col_widths = [40, 100, 120, 100, 350]
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
            self.selected_id = self.tree.item(selected[0])['values'][0]

    def load_expenses(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        date = self.filter_date.get().strip()
        expenses = self.db.get_expenses_by_date(date)
        total = 0
        for exp in expenses:
            self.tree.insert('', 'end', values=(exp[0], exp[1], exp[2], f"{exp[3]:.2f}", exp[4]))
            total += exp[3]
        self.summary_label.config(text=f"📊 إجمالي مصروفات {date}: {total:.2f}")

    def load_all_expenses(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        expenses = self.db.get_all_expenses()
        total = 0
        for exp in expenses:
            self.tree.insert('', 'end', values=(exp[0], exp[1], exp[2], f"{exp[3]:.2f}", exp[4]))
            total += exp[3]
        self.summary_label.config(text=f"📊 إجمالي جميع المصروفات: {total:.2f}")

    def add_expense(self):
        dialog = tk.Toplevel(self.parent)
        dialog.title("➕ إضافة مصروف جديد")
        dialog.geometry("480x420")
        dialog.configure(bg=TK.CARD)
        dialog.transient(self.parent)
        dialog.grab_set()

        tk.Label(dialog, text="➕ إضافة مصروف جديد", font=('Arial', 16, 'bold'),
                bg=TK.CARD, fg=TK.ACCENT2).pack(pady=15)

        frame = tk.Frame(dialog, bg=TK.CARD)
        frame.pack(pady=10)

        tk.Label(frame, text="📅 التاريخ:", bg=TK.CARD, font=('Arial', 11)).grid(row=0, column=0, padx=10, pady=10, sticky='e')
        date_entry = tk.Entry(frame, font=('Arial', 11), width=25)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(frame, text="📂 الفئة:", bg=TK.CARD, font=('Arial', 11)).grid(row=1, column=0, padx=10, pady=10, sticky='e')
        categories = ['ايجار', 'رواتب', 'كهرباء', 'ماء', 'انترنت', 'مشتريات', 'صيانة', 'ديكور', 'أخرى']
        category_combo = ttk.Combobox(frame, values=categories, width=23)
        category_combo.set('أخرى')
        category_combo.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(frame, text="💰 المبلغ:", bg=TK.CARD, font=('Arial', 11)).grid(row=2, column=0, padx=10, pady=10, sticky='e')
        amount_entry = tk.Entry(frame, font=('Arial', 11), width=25)
        amount_entry.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(frame, text="📝 الوصف:", bg=TK.CARD, font=('Arial', 11)).grid(row=3, column=0, padx=10, pady=10, sticky='e')
        desc_entry = tk.Entry(frame, font=('Arial', 11), width=25)
        desc_entry.grid(row=3, column=1, padx=10, pady=10)

        def save():
            date = date_entry.get().strip()
            category = category_combo.get().strip()
            try:
                amount = int(amount_entry.get())
            except Exception:
                messagebox.showerror("خطأ", "المبلغ يجب أن يكون رقماً")
                return
            desc = desc_entry.get().strip()
            if not date or not category:
                messagebox.showerror("خطأ", "التاريخ والفئة مطلوبان")
                return
            self.db.add_expense(date, category, amount, desc)
            dialog.destroy()
            self.load_expenses()
            messagebox.showinfo("نجاح", "✓ تمت إضافة المصروف بنجاح")

        tk.Button(dialog, text="💾 حفظ", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 11),
                 command=save, padx=25, pady=8).pack(pady=20)

    def edit_expense(self):
        if not self.selected_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار مصروف للتعديل")
            return
        expenses = self.db.get_all_expenses()
        expense = None
        for exp in expenses:
            if exp[0] == self.selected_id:
                expense = exp
                break
        if not expense:
            return

        dialog = tk.Toplevel(self.parent)
        dialog.title("✏️ تعديل مصروف")
        dialog.geometry("480x420")
        dialog.configure(bg=TK.CARD)
        dialog.transient(self.parent)
        dialog.grab_set()

        tk.Label(dialog, text="✏️ تعديل مصروف", font=('Arial', 16, 'bold'),
                bg=TK.CARD, fg=TK.WARNING).pack(pady=15)

        frame = tk.Frame(dialog, bg=TK.CARD)
        frame.pack(pady=10)

        tk.Label(frame, text="📅 التاريخ:", bg=TK.CARD, font=('Arial', 11)).grid(row=0, column=0, padx=10, pady=10, sticky='e')
        date_entry = tk.Entry(frame, font=('Arial', 11), width=25)
        date_entry.insert(0, expense[1])
        date_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(frame, text="📂 الفئة:", bg=TK.CARD, font=('Arial', 11)).grid(row=1, column=0, padx=10, pady=10, sticky='e')
        categories = ['ايجار', 'رواتب', 'كهرباء', 'ماء', 'انترنت', 'مشتريات', 'صيانة', 'ديكور', 'أخرى']
        category_combo = ttk.Combobox(frame, values=categories, width=23)
        category_combo.set(expense[2])
        category_combo.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(frame, text="💰 المبلغ:", bg=TK.CARD, font=('Arial', 11)).grid(row=2, column=0, padx=10, pady=10, sticky='e')
        amount_entry = tk.Entry(frame, font=('Arial', 11), width=25)
        amount_entry.insert(0, str(expense[3]))
        amount_entry.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(frame, text="📝 الوصف:", bg=TK.CARD, font=('Arial', 11)).grid(row=3, column=0, padx=10, pady=10, sticky='e')
        desc_entry = tk.Entry(frame, font=('Arial', 11), width=25)
        desc_entry.insert(0, expense[4])
        desc_entry.grid(row=3, column=1, padx=10, pady=10)

        def save():
            date = date_entry.get().strip()
            category = category_combo.get().strip()
            try:
                amount = int(amount_entry.get())
            except Exception:
                messagebox.showerror("خطأ", "المبلغ يجب أن يكون رقماً")
                return
            desc = desc_entry.get().strip()
            self.db.update_expense(self.selected_id, date, category, amount, desc)
            dialog.destroy()
            self.load_expenses()
            messagebox.showinfo("نجاح", "✓ تم تعديل المصروف بنجاح")

        tk.Button(dialog, text="💾 حفظ التعديلات", bg=TK.WARNING, fg=TK.WHITE, font=('Arial', 11),
                 command=save, padx=25, pady=8).pack(pady=20)

    def import_from_excel(self):
        from tkinter import filedialog
        try:
            import openpyxl
        except ImportError:
            messagebox.showerror("خطأ", "مكتبة openpyxl غير مثبتة.\nقم بتشغيل: pip install openpyxl")
            return

        file_path = filedialog.askopenfilename(
            title="اختر ملف Excel للاستيراد",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            ws = wb.active

            # Show preview dialog
            preview_dialog = tk.Toplevel(self.parent)
            preview_dialog.title("📥 استيراد مصروفات من Excel")
            preview_dialog.geometry("700x550")
            preview_dialog.configure(bg=TK.CARD)
            preview_dialog.transient(self.parent)
            preview_dialog.grab_set()

            tk.Label(preview_dialog, text="📥 استيراد مصروفات من Excel",
                    font=('Arial', 14, 'bold'), bg=TK.CARD, fg=TK.SUCCESS).pack(pady=10)

            info_label = tk.Label(preview_dialog,
                text="الأعمدة المطلوبة في الملف: التاريخ | الفئة | المبلغ | الوصف\n"
                     "(يتم تجاهل الصف الأول إذا كان رأس الجدول)",
                font=('Arial', 9), bg=TK.CARD, fg=TK.TEXT_SUB)
            info_label.pack(pady=5)

            # Preview tree
            tree_frame = tk.Frame(preview_dialog, bg=TK.CARD)
            tree_frame.pack(fill='both', expand=True, padx=15, pady=5)

            cols = ('التاريخ', 'الفئة', 'المبلغ', 'الوصف', 'الحالة')
            preview_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=12)
            for col in cols:
                preview_tree.heading(col, text=col)
                preview_tree.column(col, width=120 if col != 'الوصف' else 200)
            scroll = ttk.Scrollbar(tree_frame, orient='vertical', command=preview_tree.yview)
            preview_tree.configure(yscrollcommand=scroll.set)
            preview_tree.pack(side='left', fill='both', expand=True)
            scroll.pack(side='right', fill='y')

            rows_data = []
            for i, row in enumerate(ws.iter_rows(values_only=True)):
                if i == 0:
                    # Check if first row is header
                    if row[0] and str(row[0]).strip() in ['التاريخ', 'Date', 'date', 'تاريخ']:
                        continue
                if not any(row):
                    continue
                try:
                    date_val = str(row[0]).strip() if row[0] else ''
                    category_val = str(row[1]).strip() if row[1] else 'أخرى'
                    raw_amount = str(row[2]).replace(',', '').strip() if row[2] is not None else '0'
                    amount_val = float(raw_amount) if raw_amount else 0
                    desc_val = str(row[3]).strip() if len(row) > 3 and row[3] else ''

                    if not date_val or amount_val <= 0:
                        status = '⚠️ بيانات ناقصة'
                        preview_tree.insert('', 'end', values=(date_val, category_val, amount_val, desc_val, status), tags=('warn',))
                    else:
                        status = '✅ جاهز'
                        rows_data.append((date_val, category_val, amount_val, desc_val))
                        preview_tree.insert('', 'end', values=(date_val, category_val, f"{amount_val:.2f}", desc_val, status), tags=('ok',))
                except Exception as e:
                    preview_tree.insert('', 'end', values=(str(row[0]), '', '', '', f'❌ خطأ'), tags=('err',))

            preview_tree.tag_configure('ok', foreground=TK.SUCCESS)
            preview_tree.tag_configure('warn', foreground=TK.WARNING)
            preview_tree.tag_configure('err', foreground=TK.DANGER)

            count_label = tk.Label(preview_dialog,
                text=f"✅ صفوف جاهزة للاستيراد: {len(rows_data)}",
                font=('Arial', 10, 'bold'), bg=TK.CARD, fg=TK.TEXT)
            count_label.pack(pady=5)

            def confirm_import():
                if not rows_data:
                    messagebox.showwarning("تنبيه", "لا توجد بيانات صالحة للاستيراد")
                    return

                msg = "هل تريد استبدال المصروفات الموجودة؟"
                msg += chr(10) + chr(10) + "نعم = احذف القديم واضف الجديد فقط"
                msg += chr(10) + "لا = اضف الجديد فوق الموجود"
                replace = messagebox.askyesno(
                    "طريقة الاستيراد",
                    msg,
                    parent=preview_dialog
                )

                if replace:
                    try:
                        cursor = self.db.conn.cursor()
                        cursor.execute("DELETE FROM expenses")
                        self.db.conn.commit()
                    except Exception as e:
                        messagebox.showerror("خطأ", f"فشل حذف البيانات القديمة: {e}")
                        return

                imported = 0
                for date_val, category_val, amount_val, desc_val in rows_data:
                    try:
                        safe_amount = int(round(float(amount_val), 0))
                        self.db.add_expense(date_val, category_val, safe_amount, desc_val)
                        imported += 1
                    except Exception:
                        pass

                preview_dialog.destroy()
                self.load_all_expenses()
                messagebox.showinfo("نجاح", f"✓ تم استيراد {imported} مصروف بنجاح من ملف Excel")

            btn_frame2 = tk.Frame(preview_dialog, bg=TK.CARD)
            btn_frame2.pack(fill='x', padx=15, pady=10)

            tk.Button(btn_frame2, text=f"📥 استيراد ({len(rows_data)} سجل)", bg=TK.SUCCESS, fg=TK.WHITE,
                     font=('Arial', 11), command=confirm_import, padx=20, pady=8).pack(side='left', padx=10, expand=True, fill='x')
            tk.Button(btn_frame2, text="❌ إلغاء", bg=TK.DANGER,  fg=TK.WHITE,
                     font=('Arial', 11), command=preview_dialog.destroy, padx=20, pady=8).pack(side='right', padx=10, expand=True, fill='x')

        except Exception as e:
            messagebox.showerror("خطأ في القراءة", f"تعذر قراءة الملف:\n{str(e)}")

    def delete_expense(self):
        if not self.selected_id:
            messagebox.showwarning("تنبيه", "الرجاء اختيار مصروف للحذف")
            return
        if messagebox.askyesno("⚠️ تأكيد الحذف", "هل أنت متأكد من حذف هذا المصروف؟"):
            self.db.delete_expense(self.selected_id)
            self.load_expenses()
            self.selected_id = None
            messagebox.showinfo("نجاح", "✓ تم حذف المصروف بنجاح")

