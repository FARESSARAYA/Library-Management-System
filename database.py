"""database.py — طبقة قاعدة البيانات (SQLite)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from datetime import datetime
from config import DB_PATH

def round_to_500(price):
    price = int(price)
    if price < 1000:
        return price
    remainder = price % 1000
    base = price - remainder
    if remainder < 500:
        return base
    elif remainder == 500:
        return price
    else:
        return base + 1000

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        # WAL mode: يضمن حفظ البيانات فوراً على القرص حتى لو أُغلق البرنامج بشكل مفاجئ
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.commit()
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE,
                name TEXT NOT NULL,
                trader_name TEXT,
                main_unit TEXT DEFAULT 'piece',
                sell_price INTEGER DEFAULT 0,
                quantity REAL DEFAULT 0,
                min_quantity REAL DEFAULT 5
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number INTEGER,
                barcode TEXT,
                material_name TEXT,
                customer_name TEXT,
                unit_type TEXT,
                quantity REAL,
                sell_price INTEGER,
                total INTEGER,
                discount_percent REAL,
                discount_amount INTEGER,
                amount_paid INTEGER,
                remaining INTEGER,
                payment_status TEXT,
                date TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS supplier_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE,
                supplier_name TEXT NOT NULL,
                invoice_date TEXT,
                total_amount REAL,
                paid_amount REAL DEFAULT 0,
                remaining_amount REAL,
                payment_status TEXT DEFAULT 'غير مدفوع',
                notes TEXT,
                created_date TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS supplier_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT,
                amount_paid REAL,
                payment_date TEXT,
                payment_method TEXT,
                notes TEXT,
                FOREIGN KEY (invoice_number) REFERENCES supplier_invoices(invoice_number)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT,
                barcode TEXT,
                material_name TEXT,
                quantity REAL,
                purchase_price REAL,
                total REAL,
                FOREIGN KEY (invoice_number) REFERENCES supplier_invoices(invoice_number),
                FOREIGN KEY (barcode) REFERENCES materials(barcode)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                category TEXT,
                amount INTEGER,
                description TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                barcode TEXT,
                material_name TEXT,
                quantity REAL,
                purchase_price INTEGER,
                trader_name TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_sequence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_invoice INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_number INTEGER,
                original_invoice INTEGER,
                barcode TEXT,
                material_name TEXT,
                customer_name TEXT,
                quantity REAL,
                return_price INTEGER,
                total_return INTEGER,
                reason TEXT,
                date TEXT,
                status TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS return_sequence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_return INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchanges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exchange_number INTEGER,
                original_invoice INTEGER,
                original_barcode TEXT,
                original_material_name TEXT,
                original_quantity REAL,
                original_price INTEGER,
                new_barcode TEXT,
                new_material_name TEXT,
                new_quantity REAL,
                new_price INTEGER,
                price_difference INTEGER,
                customer_name TEXT,
                reason TEXT,
                date TEXT,
                status TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_sequence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_exchange INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dollar_linked_products (
                barcode TEXT PRIMARY KEY,
                FOREIGN KEY (barcode) REFERENCES materials(barcode)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manual_profits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                net_profit REAL NOT NULL,
                notes TEXT,
                UNIQUE(year, month)
            )
        ''')

        cursor.execute("SELECT COUNT(*) FROM invoice_sequence")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO invoice_sequence (last_invoice) VALUES (0)")

        cursor.execute("SELECT COUNT(*) FROM return_sequence")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO return_sequence (last_return) VALUES (0)")

        cursor.execute("SELECT COUNT(*) FROM exchange_sequence")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO exchange_sequence (last_exchange) VALUES (0)")

        # ── Migration: إضافة الأعمدة الجديدة إذا لم تكن موجودة في قاعدة بيانات قديمة ──
        migrations = [
            ("materials",      "quantity",         "ALTER TABLE materials ADD COLUMN quantity REAL DEFAULT 0"),
            ("materials",      "min_quantity",     "ALTER TABLE materials ADD COLUMN min_quantity REAL DEFAULT 5"),
            ("materials",      "purchase_price",   "ALTER TABLE materials ADD COLUMN purchase_price REAL DEFAULT 0"),
            ("sales",          "amount_paid",      "ALTER TABLE sales ADD COLUMN amount_paid INTEGER DEFAULT 0"),
            ("sales",          "remaining",        "ALTER TABLE sales ADD COLUMN remaining INTEGER DEFAULT 0"),
            ("sales",          "payment_status",   "ALTER TABLE sales ADD COLUMN payment_status TEXT DEFAULT 'مدفوع بالكامل'"),
            ("manual_profits", "printing_profit",  "ALTER TABLE manual_profits ADD COLUMN printing_profit REAL DEFAULT 0"),
        ]
        for table, col, sql in migrations:
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                existing_cols = [row[1] for row in cursor.fetchall()]
                if col not in existing_cols:
                    cursor.execute(sql)
            except Exception:
                pass

        self.conn.commit()

    def round_all_prices(self):
        """تقريب جميع الأسعار الموجودة في قاعدة البيانات لأقرب 500 لأعلى"""
        import math
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT barcode, sell_price FROM materials")
            rows = cursor.fetchall()
            fixed = 0
            for barcode, price in rows:
                try:
                    price_int = int(str(price).replace(',', '').strip())
                    rounded = round_to_500(price_int)
                    if rounded != price_int:
                        cursor.execute("UPDATE materials SET sell_price=? WHERE barcode=?", (rounded, barcode))
                        fixed += 1
                except Exception:
                    pass
            if fixed > 0:
                self.conn.commit()
        except Exception:
            pass

    def get_all_materials(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT barcode, name, trader_name, main_unit, sell_price, quantity, min_quantity FROM materials ORDER BY name")
        return cursor.fetchall()

    def get_material_by_barcode(self, barcode):
        cursor = self.conn.cursor()
        cursor.execute("SELECT barcode, name, trader_name, main_unit, sell_price, quantity, min_quantity FROM materials WHERE barcode=?", (barcode,))
        return cursor.fetchone()

    def add_material(self, barcode, name, trader_name, main_unit, sell_price, quantity=0, min_quantity=5):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO materials (barcode, name, trader_name, main_unit, sell_price, quantity, min_quantity) VALUES (?,?,?,?,?,?,?)",
                          (barcode, name, trader_name, main_unit, sell_price, quantity, min_quantity))
            self.conn.commit()
            return True, "تمت الإضافة"
        except Exception:
            return False, "الباركود موجود"

    def update_material(self, old_barcode, barcode, name, trader_name, main_unit, sell_price, quantity, min_quantity):
        cursor = self.conn.cursor()
        # تأكد أن old_barcode نص وليس رقم
        old_barcode = str(old_barcode).strip()
        cursor.execute("UPDATE materials SET barcode=?, name=?, trader_name=?, main_unit=?, sell_price=?, quantity=?, min_quantity=? WHERE barcode=?",
                      (barcode, name, trader_name, main_unit, sell_price, quantity, min_quantity, old_barcode))
        self.conn.commit()
        if cursor.rowcount == 0:
            # جرب البحث بدون أصفار في البداية كحل احتياطي
            cursor.execute("SELECT barcode FROM materials WHERE CAST(barcode AS INTEGER) = CAST(? AS INTEGER)", (old_barcode,))
            row = cursor.fetchone()
            if row:
                real_barcode = row[0]
                cursor.execute("UPDATE materials SET barcode=?, name=?, trader_name=?, main_unit=?, sell_price=?, quantity=?, min_quantity=? WHERE barcode=?",
                              (barcode, name, trader_name, main_unit, sell_price, quantity, min_quantity, real_barcode))
                self.conn.commit()
                if cursor.rowcount > 0:
                    return True, "تم التعديل"
            return False, f"لم يتم العثور على الباركود: {old_barcode}"
        return True, "تم التعديل"

    def delete_material(self, barcode):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM materials WHERE barcode=?", (barcode,))
        self.conn.commit()
        return True, "تم الحذف"

    def update_quantity(self, barcode, quantity_change, is_sale=True):
        cursor = self.conn.cursor()
        if is_sale:
            cursor.execute("UPDATE materials SET quantity = quantity - ? WHERE barcode=?", (quantity_change, barcode))
        else:
            cursor.execute("UPDATE materials SET quantity = quantity + ? WHERE barcode=?", (quantity_change, barcode))
        self.conn.commit()
        cursor.execute("SELECT quantity, name FROM materials WHERE barcode=?", (barcode,))
        result = cursor.fetchone()
        if result:
            return result[0], result[1]
        return None, None

    def get_low_stock_materials(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT barcode, name, quantity, min_quantity FROM materials WHERE quantity <= min_quantity AND quantity > 0")
        return cursor.fetchall()

    def get_out_of_stock_materials(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT barcode, name, quantity FROM materials WHERE quantity <= 0")
        return cursor.fetchall()

    def get_next_invoice_number(self):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE invoice_sequence SET last_invoice = last_invoice + 1 WHERE id=1")
        self.conn.commit()
        cursor.execute("SELECT last_invoice FROM invoice_sequence WHERE id=1")
        return cursor.fetchone()[0]

    def get_next_return_number(self):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE return_sequence SET last_return = last_return + 1 WHERE id=1")
        self.conn.commit()
        cursor.execute("SELECT last_return FROM return_sequence WHERE id=1")
        return cursor.fetchone()[0]

    def get_next_exchange_number(self):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE exchange_sequence SET last_exchange = last_exchange + 1 WHERE id=1")
        self.conn.commit()
        cursor.execute("SELECT last_exchange FROM exchange_sequence WHERE id=1")
        return cursor.fetchone()[0]

    def add_sale(self, invoice_number, barcode, material_name, customer_name, unit_type, quantity, sell_price, total, discount_percent, discount_amount, date):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO sales (
            invoice_number, barcode, material_name, customer_name, unit_type,
            quantity, sell_price, total, discount_percent, discount_amount,
            amount_paid, remaining, payment_status, date
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (invoice_number, barcode, material_name, customer_name, unit_type,
         quantity, sell_price, total, discount_percent, discount_amount,
         total, 0, 'مدفوع بالكامل', date))
        self.conn.commit()
        new_qty, name = self.update_quantity(barcode, quantity, is_sale=True)
        return cursor.lastrowid, new_qty, name

    def get_sales_by_date(self, date):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sales WHERE date LIKE ?", (f'{date}%',))
        return cursor.fetchall()

    def get_sales_by_month(self, year, month):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sales WHERE date LIKE ?", (f'{year}-{month:02d}%',))
        return cursor.fetchall()

    def get_sales_by_invoice(self, invoice_number):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sales WHERE invoice_number = ?", (invoice_number,))
        return cursor.fetchall()

    def add_supplier_invoice(self, invoice_number, supplier_name, invoice_date, total_amount, notes=""):
        cursor = self.conn.cursor()
        created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor.execute('''
                INSERT INTO supplier_invoices
                (invoice_number, supplier_name, invoice_date, total_amount, paid_amount, remaining_amount, payment_status, notes, created_date)
                VALUES (?,?,?,?,?,?,?,?,?)
            ''', (invoice_number, supplier_name, invoice_date, total_amount, 0, total_amount, 'غير مدفوع', notes, created_date))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def update_supplier_invoice(self, invoice_number, supplier_name, invoice_date, total_amount, notes=""):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE supplier_invoices
            SET supplier_name=?, invoice_date=?, total_amount=?, notes=?
            WHERE invoice_number=?
        ''', (supplier_name, invoice_date, total_amount, notes, invoice_number))
        self.conn.commit()

    def add_supplier_payment(self, invoice_number, amount_paid, payment_method, notes=""):
        cursor = self.conn.cursor()
        payment_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO supplier_payments (invoice_number, amount_paid, payment_date, payment_method, notes)
            VALUES (?,?,?,?,?)
        ''', (invoice_number, amount_paid, payment_date, payment_method, notes))
        self.conn.commit()

        cursor.execute("SELECT paid_amount, total_amount FROM supplier_invoices WHERE invoice_number = ?", (invoice_number,))
        result = cursor.fetchone()
        if result:
            new_paid = result[0] + amount_paid
            total = result[1]
            new_remaining = total - new_paid
            if new_remaining <= 0:
                status = "مدفوع بالكامل"
                new_remaining = 0
            else:
                status = "مدفوع جزئياً"
            cursor.execute('''
                UPDATE supplier_invoices
                SET paid_amount = ?, remaining_amount = ?, payment_status = ?
                WHERE invoice_number = ?
            ''', (new_paid, new_remaining, status, invoice_number))
            self.conn.commit()
        return cursor.lastrowid

    def get_all_supplier_invoices(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM supplier_invoices ORDER BY created_date DESC")
        return cursor.fetchall()

    def get_supplier_invoice_by_number(self, invoice_number):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM supplier_invoices WHERE invoice_number = ?", (invoice_number,))
        return cursor.fetchone()

    def get_supplier_payments_by_invoice(self, invoice_number):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM supplier_payments WHERE invoice_number = ? ORDER BY payment_date", (invoice_number,))
        return cursor.fetchall()

    def add_invoice_item(self, invoice_number, barcode, material_name, quantity, purchase_price):
        cursor = self.conn.cursor()
        total = quantity * purchase_price
        cursor.execute('''
            INSERT INTO invoice_items (invoice_number, barcode, material_name, quantity, purchase_price, total)
            VALUES (?,?,?,?,?,?)
        ''', (invoice_number, barcode, material_name, quantity, purchase_price, total))
        # تحديث سعر الشراء الأخير في جدول المواد
        cursor.execute(
            "UPDATE materials SET purchase_price=? WHERE barcode=?",
            (purchase_price, barcode)
        )
        self.conn.commit()
        self.update_quantity(barcode, quantity, is_sale=False)
        return cursor.lastrowid

    def get_invoice_items(self, invoice_number):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM invoice_items WHERE invoice_number = ?", (invoice_number,))
        return cursor.fetchall()

    def get_supplier_invoices_summary(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM supplier_invoices")
        total_count = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM supplier_invoices")
        total_amount = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(paid_amount), 0) FROM supplier_invoices")
        total_paid = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(remaining_amount), 0) FROM supplier_invoices")
        total_remaining = cursor.fetchone()[0]

        return {
            'total_count': total_count,
            'total_amount': total_amount,
            'total_paid': total_paid,
            'total_remaining': total_remaining
        }

    def add_return(self, return_number, original_invoice, barcode, material_name, customer_name, quantity, return_price, total_return, reason, date, status="تم الإرجاع"):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO returns (
            return_number, original_invoice, barcode, material_name, customer_name,
            quantity, return_price, total_return, reason, date, status
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
        (return_number, original_invoice, barcode, material_name, customer_name,
         quantity, return_price, total_return, reason, date, status))
        self.conn.commit()
        self.update_quantity(barcode, quantity, is_sale=False)
        return cursor.lastrowid

    def add_exchange(self, exchange_number, original_invoice, original_barcode, original_material_name,
                     original_quantity, original_price, new_barcode, new_material_name,
                     new_quantity, new_price, price_difference, customer_name, reason, date, status="تم التبديل"):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO exchanges (
            exchange_number, original_invoice, original_barcode, original_material_name,
            original_quantity, original_price, new_barcode, new_material_name,
            new_quantity, new_price, price_difference, customer_name, reason, date, status
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (exchange_number, original_invoice, original_barcode, original_material_name,
         original_quantity, original_price, new_barcode, new_material_name,
         new_quantity, new_price, price_difference, customer_name, reason, date, status))
        self.conn.commit()
        self.update_quantity(original_barcode, original_quantity, is_sale=False)
        self.update_quantity(new_barcode, new_quantity, is_sale=True)
        return cursor.lastrowid

    def get_returns_by_date(self, date):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM returns WHERE date LIKE ?", (f'{date}%',))
        return cursor.fetchall()

    def get_returns_by_month(self, year, month):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM returns WHERE date LIKE ?", (f'{year}-{month:02d}%',))
        return cursor.fetchall()

    def get_all_returns(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM returns ORDER BY date DESC")
        return cursor.fetchall()

    def get_total_returns_by_date(self, date):
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(total_return) FROM returns WHERE date LIKE ?", (f'{date}%',))
        result = cursor.fetchone()[0]
        return result if result else 0

    def get_exchanges_by_date(self, date):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM exchanges WHERE date LIKE ?", (f'{date}%',))
        return cursor.fetchall()

    def get_all_exchanges(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM exchanges ORDER BY date DESC")
        return cursor.fetchall()

    def add_purchase(self, date, barcode, material_name, quantity, purchase_price, trader_name):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO purchases (date, barcode, material_name, quantity, purchase_price, trader_name) VALUES (?,?,?,?,?,?)",
                      (date, barcode, material_name, quantity, purchase_price, trader_name))
        self.conn.commit()
        self.update_quantity(barcode, quantity, is_sale=False)
        return True

    def add_expense(self, date, category, amount, description):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO expenses (date, category, amount, description) VALUES (?,?,?,?)",
                      (date, category, amount, description))
        self.conn.commit()
        return True

    def get_purchase_cost_by_date(self, date):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM supplier_invoices WHERE invoice_date = ?", (date,))
        return cursor.fetchone()[0]

    def get_purchase_cost_by_month(self, year, month):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM supplier_invoices WHERE invoice_date LIKE ?", (f'{year}-{month:02d}%',))
        return cursor.fetchone()[0]

    def set_manual_profit(self, year, month, net_profit, notes="", printing_profit=0):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO manual_profits (year, month, net_profit, notes, printing_profit)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(year, month) DO UPDATE SET
                net_profit=excluded.net_profit,
                notes=excluded.notes,
                printing_profit=excluded.printing_profit
        ''', (year, month, net_profit, notes, printing_profit))
        self.conn.commit()

    def set_printing_profit(self, year, month, printing_profit):
        """تحديث ربح الطباعة فقط لشهر معين"""
        cursor = self.conn.cursor()
        # إنشاء السجل إذا لم يكن موجوداً
        cursor.execute('''
            INSERT INTO manual_profits (year, month, net_profit, notes, printing_profit)
            VALUES (?, ?, 0, '', ?)
            ON CONFLICT(year, month) DO UPDATE SET printing_profit=excluded.printing_profit
        ''', (year, month, printing_profit))
        self.conn.commit()

    def get_manual_profit(self, year, month):
        cursor = self.conn.cursor()
        cursor.execute("SELECT net_profit, notes, COALESCE(printing_profit,0) FROM manual_profits WHERE year=? AND month=?", (year, month))
        return cursor.fetchone()

    def get_all_manual_profits(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT year, month, net_profit, notes, COALESCE(printing_profit,0) FROM manual_profits ORDER BY year, month")
        return cursor.fetchall()

    def get_expenses_by_date(self, date):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE date = ? ORDER BY id", (date,))
        return cursor.fetchall()

    def get_expenses_by_month(self, year, month):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE date LIKE ? ORDER BY date", (f'{year}-{month:02d}%',))
        return cursor.fetchall()

    def get_all_expenses(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
        return cursor.fetchall()

    def update_expense(self, expense_id, date, category, amount, description):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE expenses SET date=?, category=?, amount=?, description=? WHERE id=?",
                      (date, category, amount, description, expense_id))
        self.conn.commit()
        return True

    def delete_expense(self, expense_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
        self.conn.commit()
        return True

    def get_dollar_linked_barcodes(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT barcode FROM dollar_linked_products")
        return set(row[0] for row in cursor.fetchall())

    def set_dollar_linked_products(self, barcodes):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM dollar_linked_products")
        for bc in barcodes:
            cursor.execute("INSERT OR IGNORE INTO dollar_linked_products (barcode) VALUES (?)", (bc,))
        self.conn.commit()

    def delete_supplier_invoice(self, invoice_number):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM invoice_items WHERE invoice_number=?", (invoice_number,))
        cursor.execute("DELETE FROM supplier_payments WHERE invoice_number=?", (invoice_number,))
        cursor.execute("DELETE FROM supplier_invoices WHERE invoice_number=?", (invoice_number,))
        self.conn.commit()
        return True

