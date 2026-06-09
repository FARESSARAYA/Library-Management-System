"""materials_tab.py — تبويب إدارة المواد"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
from theme_tk import TK, apply_theme, setup_treeview, fill_treeview, style_button, style_entry, make_card
from tkinter import simpledialog, filedialog
import pandas as pd
from datetime import datetime
from database import Database, round_to_500

class MaterialsTab:
    def __init__(self, parent, db, on_material_change=None):
        self.parent = parent
        self.db = db
        self.on_material_change = on_material_change
        self.create_widgets()
        self.load_materials()

    def create_widgets(self):
        frame = tk.Frame(self.parent, bg=TK.CARD)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(frame, bg=TK.CARD)
        btn_frame.pack(fill='x', pady=5)
        tk.Button(btn_frame, text="➕ إضافة مادة", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 10),
                 command=self.add_material, padx=15, pady=5).pack(side='left', padx=5)
        tk.Button(btn_frame, text="✏️ تعديل مادة", bg=TK.WARNING, fg=TK.WHITE, font=('Arial', 10),
                 command=self.edit_material, padx=15, pady=5).pack(side='left', padx=5)
        tk.Button(btn_frame, text="🗑️ حذف مادة", bg=TK.DANGER,  fg=TK.WHITE, font=('Arial', 10),
                 command=self.delete_material, padx=15, pady=5).pack(side='left', padx=5)
        tk.Button(btn_frame, text="📥 استيراد Excel", bg=TK.ACCENT,  fg=TK.WHITE, font=('Arial', 10),
                 command=self.import_from_excel, padx=15, pady=5).pack(side='left', padx=5)
        tk.Button(btn_frame, text="💰 تحديث السعر من Excel", bg=TK.ACCENT2, fg=TK.WHITE, font=('Arial', 10),
                 command=self.import_price_from_excel, padx=15, pady=5).pack(side='left', padx=5)

        search_frame = tk.Frame(frame, bg=TK.CARD)
        search_frame.pack(fill='x', pady=5)
        tk.Label(search_frame, text="🔍 بحث:", bg=TK.CARD, font=('Arial', 11)).pack(side='left', padx=5)
        self.search_entry = tk.Entry(search_frame, font=('Arial', 11), width=40)
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.load_materials())

        tree_frame = tk.Frame(frame, bg=TK.CARD)
        tree_frame.pack(fill='both', expand=True, pady=5)

        columns = ('الباركود', 'اسم المادة', 'التاجر', 'الوحدة', 'السعر', 'الكمية', 'الحد الأدنى')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)

        col_widths = [100, 180, 120, 80, 100, 80, 100]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def notify_change(self):
        if self.on_material_change:
            self.on_material_change()

    def load_materials(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = self.search_entry.get() if hasattr(self, 'search_entry') else ""
        materials = self.db.get_all_materials()

        for mat in materials:
            if search.lower() in mat[1].lower() or search.lower() in str(mat[0]).lower():
                barcode_str = str(mat[0])
                # نضيف مسافة في البداية لمنع tkinter من تحويل الباركود لرقم
                display_barcode = ' ' + barcode_str
                self.tree.insert('', 'end', iid='bc_' + barcode_str, values=(display_barcode, mat[1], mat[2] if mat[2] else '-', mat[3], mat[4], mat[5], mat[6]))

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
            except Exception as e:
                messagebox.showerror("خطأ", f"السعر يجب أن يكون رقماً\n\nتفاصيل الخطأ:\n{type(e).__name__}: {e}\n\nالقيمة المدخلة: [{entries['💰 السعر'].get()}]")
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
                self.notify_change()

        tk.Button(dialog, text="💾 حفظ", bg=TK.SUCCESS, fg=TK.WHITE, font=('Arial', 11),
                 command=save, padx=25, pady=8).pack(pady=20)

    def edit_material(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ تنبيه", "الرجاء اختيار مادة للتعديل")
            return

        # iid يحتوي على "bc_" + الباركود الأصلي للحفاظ على الأصفار
        original_barcode = selected[0].replace('bc_', '', 1)
        values = [original_barcode] + list(self.tree.item(selected[0])['values'])[1:]

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
                # values[0] هو الباركود الأصلي من قاعدة البيانات مع الأصفار
                entry.insert(0, str(values[i]))
            entry.grid(row=i, column=1, padx=10, pady=8)
            entries[label] = entry
        # تأكيد عرض الباركود الصحيح مع الأصفار
        entries['📦 الباركود'].delete(0, tk.END)
        entries['📦 الباركود'].insert(0, original_barcode)

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

            success, msg = self.db.update_material(original_barcode, barcode, name, trader, unit, price, quantity, min_qty)
            messagebox.showinfo("نتيجة", msg)
            if success:
                dialog.destroy()
                self.load_materials()
                self.notify_change()

        tk.Button(dialog, text="💾 حفظ التعديلات", bg=TK.WARNING, fg=TK.WHITE, font=('Arial', 11),
                 command=save, padx=25, pady=8).pack(pady=20)

    def delete_material(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ تنبيه", "الرجاء اختيار مادة للحذف")
            return

        original_barcode = selected[0].replace('bc_', '', 1)
        values = self.tree.item(selected[0])['values']

        if messagebox.askyesno("🗑️ تأكيد الحذف", f"هل أنت متأكد من حذف المادة:\n\n📝 {values[1]}"):
            self.db.delete_material(original_barcode)
            self.load_materials()
            self.notify_change()

    def import_from_excel(self):
        file_path = filedialog.askopenfilename(
            title="اختر ملف Excel",
            filetypes=[("All files", "*.*"), ("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
        )

        if not file_path:
            return

        if not os.path.exists(file_path):
            messagebox.showerror("خطأ", "الملف غير موجود")
            return

        try:
            df = pd.read_excel(file_path)
            df.columns = [str(c).strip() for c in df.columns]

            # ── اكتشاف الأعمدة تلقائياً ──
            barcode_col = name_col = price_col = qty_col = None
            for col in df.columns:
                cl = col.lower()
                if any(p in cl for p in ['باركود', 'barcode', 'رمز', 'كود', 'code', 'رقم']):
                    if barcode_col is None: barcode_col = col
                if any(p in cl for p in ['اسم', 'name', 'المنتج', 'product', 'مادة', 'وصف']):
                    if name_col is None: name_col = col
                if any(p in cl for p in ['سعر', 'price', 'ثمن', 'sell']):
                    if price_col is None: price_col = col
                if any(p in cl for p in ['كمية', 'quantity', 'qty', 'stock', 'مخزون']):
                    if qty_col is None: qty_col = col

            if not (barcode_col and name_col and price_col):
                messagebox.showwarning("تنبيه",
                    f"لم يتم التعرف على الأعمدة المطلوبة.\n\n"
                    f"الأعمدة الموجودة في الملف:\n{chr(10).join(df.columns.tolist())}\n\n"
                    f"يجب أن يحتوي الملف على أعمدة لـ:\n"
                    f"• الباركود (رمز، كود، barcode...)\n"
                    f"• الاسم (اسم، مادة، name...)\n"
                    f"• السعر (سعر، price, ثمن...)")
                return

            default_qty = 0
            if not qty_col:
                qty_str = simpledialog.askstring(
                    "الكمية الافتراضية",
                    f"الملف لا يحتوي على عمود كمية.\n"
                    f"ما الكمية الافتراضية لكل منتج؟\n(اتركها 0 إذا أردت إضافتها لاحقاً)",
                    initialvalue="0"
                )
                try:
                    default_qty = float(qty_str) if qty_str else 0
                except Exception:
                    default_qty = 0

            col_info = (f"• الباركود  : {barcode_col}\n"
                        f"• الاسم     : {name_col}\n"
                        f"• السعر     : {price_col}\n"
                        f"• الكمية    : {qty_col if qty_col else f'افتراضي ({int(default_qty)})'}")
            result = messagebox.askyesno("تأكيد الاستيراد",
                f"تم قراءة {len(df)} صف من الملف.\n\n"
                f"الأعمدة المُعرَّفة:\n{col_info}\n\n"
                f"ملاحظة: المنتجات الموجودة مسبقاً سيتم تحديث سعرها وكميتها.\n\n"
                f"هل تريد المتابعة؟")
            if not result:
                return

            count_new = count_updated = skipped = 0
            cursor = self.db.conn.cursor()

            for idx, row in df.iterrows():
                barcode = str(row[barcode_col]).strip()
                name    = str(row[name_col]).strip()

                if not barcode or not name or barcode in ('nan', 'None', '') or name in ('nan', 'None', ''):
                    skipped += 1
                    continue

                try:
                    raw_price = row[price_col]
                    price = float(str(raw_price).replace(',', '').strip())
                except Exception:
                    skipped += 1
                    continue

                qty = default_qty
                if qty_col:
                    try:
                        qty = float(str(row[qty_col]).replace(',', '').strip())
                    except Exception:
                        qty = default_qty

                try:
                    cursor.execute("SELECT barcode FROM materials WHERE barcode=?", (barcode,))
                    exists = cursor.fetchone()
                    if exists:
                        cursor.execute(
                            "UPDATE materials SET name=?, sell_price=?, quantity=? WHERE barcode=?",
                            (name, int(price), qty, barcode)
                        )
                        count_updated += 1
                    else:
                        cursor.execute(
                            "INSERT INTO materials (barcode, name, trader_name, main_unit, sell_price, quantity, min_quantity) VALUES (?,?,?,?,?,?,?)",
                            (barcode, name, "", "piece", int(price), qty, 5)
                        )
                        count_new += 1
                except Exception:
                    skipped += 1

            self.db.conn.commit()
            self.load_materials()
            self.notify_change()

            messagebox.showinfo("اكتمل الاستيراد ✅",
                f"✅ منتجات جديدة أُضيفت  : {count_new}\n"
                f"🔄 منتجات تم تحديثها   : {count_updated}\n"
                f"⚠️ صفوف تم تجاهلها    : {skipped}")

        except Exception as e:
            messagebox.showerror("خطأ", f"فشل الاستيراد: {str(e)}")


    def import_price_from_excel(self):
        """استيراد سعر المادة فقط للمواد المطابقة الموجودة في الملف والقائمة معاً"""
        file_path = filedialog.askopenfilename(
            title="اختر ملف Excel لتحديث الأسعار",
            filetypes=[("All files", "*.*"), ("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
        )
        if not file_path or not os.path.exists(file_path):
            return

        try:
            df = pd.read_excel(file_path)
            df.columns = [str(c).strip() for c in df.columns]
            cols = df.columns.tolist()

            # ── اكتشاف الأعمدة تلقائياً ──
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
            price_col   = detect_col(['سعر', 'price', 'ثمن', 'sell'],
                                     exclude=[barcode_col] if barcode_col else [])

            # ── نافذة تعيين الأعمدة ──
            mapping_ok  = [False]
            result_cols = [barcode_col, price_col]

            map_win = tk.Toplevel()
            map_win.title("تحديث السعر من Excel")
            map_win.geometry("480x310")
            map_win.configure(bg="white")
            map_win.resizable(False, False)
            map_win.grab_set()
            sw, sh = map_win.winfo_screenwidth(), map_win.winfo_screenheight()
            map_win.geometry(f"480x310+{(sw-480)//2}+{(sh-310)//2}")

            tk.Label(map_win, text="💰 تحديث السعر من Excel", font=("Arial", 13, "bold"),
                     bg="white", fg="#2c3e50").pack(pady=(15, 4))
            tk.Label(map_win, text=f"الأعمدة في الملف: {chr(32).join(cols)}",
                     font=("Arial", 9), bg="white", fg="#7f8c8d", wraplength=440).pack(pady=(0, 4))
            tk.Label(map_win,
                     text="⚠️ سيتم تحديث السعر فقط للمواد المطابقة بالباركود في القائمة والملف.",
                     font=("Arial", 10), bg="white", fg="#e67e22", wraplength=440).pack(pady=(0, 8))

            CHOICES = ["-- لا يوجد --"] + cols
            fields = [
                ("🔢 عمود الباركود *", barcode_col),
                ("💰 عمود السعر *",    price_col),
            ]
            vars_ = []
            frm = tk.Frame(map_win, bg="white")
            frm.pack(padx=30, fill="x")
            for label, detected in fields:
                tk.Label(frm, text=label, font=("Arial", 11), bg="white", anchor="w").pack(fill="x", pady=(6, 0))
                v = tk.StringVar(value=detected if detected else "-- لا يوجد --")
                cb = ttk.Combobox(frm, textvariable=v, values=CHOICES, state="readonly", font=("Arial", 11))
                cb.pack(fill="x", pady=(2, 0))
                vars_.append(v)

            def on_confirm():
                bc = vars_[0].get()
                pr = vars_[1].get()
                if bc == "-- لا يوجد --" or pr == "-- لا يوجد --":
                    messagebox.showwarning("تنبيه", "الباركود والسعر مطلوبان!", parent=map_win)
                    return
                if bc == pr:
                    messagebox.showwarning("تنبيه", "لا يمكن تعيين نفس العمود لحقلين!", parent=map_win)
                    return
                result_cols[0] = bc
                result_cols[1] = pr
                mapping_ok[0]  = True
                map_win.destroy()

            tk.Button(map_win, text="✅ تأكيد والمتابعة", bg="#8e44ad", fg="white",
                      font=("Arial", 12, "bold"), command=on_confirm,
                      cursor="hand2", pady=6).pack(pady=12)
            map_win.wait_window()

            if not mapping_ok[0]:
                return

            barcode_col, price_col = result_cols

            # ── جلب باركودات القائمة الحالية من DB ──
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT barcode FROM materials")
            db_barcodes = {str(row[0]).strip() for row in cursor.fetchall()}

            # ── حساب المطابقات قبل التنفيذ ──
            EMPTY = {"nan", "none", "null", ""}
            matched_rows = []
            for idx, row in df.iterrows():
                raw_bc = str(row[barcode_col]).strip()
                if raw_bc.endswith(".0"):
                    raw_bc = raw_bc[:-2]
                if raw_bc.lower() in EMPTY:
                    continue
                if raw_bc in db_barcodes:
                    try:
                        price = float(str(row[price_col]).replace(",", "").strip())
                        if price >= 0:
                            matched_rows.append((raw_bc, price, idx))
                    except Exception:
                        pass

            if not matched_rows:
                messagebox.showwarning("لا توجد تطابقات",
                    "لم يتم العثور على أي باركود مشترك بين الملف والقائمة الحالية.\n"
                    "تأكد من صحة عمود الباركود المحدد.")
                return

            if not messagebox.askyesno("تأكيد تحديث الأسعار",
                f"تم العثور على {len(matched_rows)} مادة مطابقة بين الملف والقائمة.\n\n"
                f"• عمود الباركود : {barcode_col}\n"
                f"• عمود السعر    : {price_col}\n\n"
                f"سيتم تحديث السعر فقط بدون تغيير أي بيانات أخرى.\n"
                f"هل تريد المتابعة؟"):
                return

            count_updated = skipped = 0
            skip_details  = []

            for barcode, price, idx in matched_rows:
                try:
                    cursor.execute(
                        "UPDATE materials SET sell_price=? WHERE barcode=?",
                        (round(price), barcode)
                    )
                    count_updated += 1
                except Exception as e:
                    skipped += 1
                    skip_details.append(f"صف {idx+2} [باركود: {barcode}]: {str(e)}")

            self.db.conn.commit()
            self.load_materials()
            self.notify_change()

            detail_msg = ""
            if skip_details:
                detail_msg = "\n\nتفاصيل الأخطاء:\n" + "\n".join(skip_details[:10])
                if len(skip_details) > 10:
                    detail_msg += f"\n... و{len(skip_details)-10} أخرى"

            messagebox.showinfo("اكتمل تحديث الأسعار ✅",
                f"💰 مواد تم تحديث سعرها  : {count_updated}\n"
                f"⚠️ صفوف فشل تحديثها   : {skipped}"
                + detail_msg)

        except Exception as e:
            messagebox.showerror("خطأ", f"فشل العملية: {str(e)}")


