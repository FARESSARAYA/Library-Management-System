"""materials_tab.py — تبويب إدارة المواد (PyQt6)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QFileDialog, QApplication, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont
from theme import C
import pandas as pd

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


class MaterialDialog(QDialog):
    def __init__(self, parent=None, values=None, title="إضافة مادة"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Title
        lbl = QLabel(title)
        lbl.setStyleSheet(f"font-size:16px;font-weight:bold;color:{C.ACCENT2};padding:8px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        form = QFormLayout()
        form.setSpacing(10)

        fields = [
            ("الباركود",        "barcode"),
            ("اسم المادة",      "name"),
            ("اسم التاجر",      "trader"),
            ("الوحدة",           "unit"),
            ("السعر",            "price"),
            ("الكمية",           "quantity"),
            ("الحد الأدنى",      "min_qty"),
        ]
        self.fields = {}
        for label, key in fields:
            entry = QLineEdit()
            entry.setMinimumHeight(34)
            self.fields[key] = entry
            form.addRow(label + ":", entry)

        # Defaults
        if values:
            keys = ["barcode","name","trader","unit","price","quantity","min_qty"]
            for i, k in enumerate(keys):
                if i < len(values):
                    self.fields[k].setText(str(values[i]))
        else:
            self.fields["quantity"].setText("0")
            self.fields["min_qty"].setText("5")
            self.fields["unit"].setText("piece")

        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Save).setText("💾 حفظ")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        btns.accepted.connect(self.validate_and_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def validate_and_accept(self):
        if not self.fields["barcode"].text().strip():
            QMessageBox.warning(self, "خطأ", "الباركود مطلوب")
            return
        if not self.fields["name"].text().strip():
            QMessageBox.warning(self, "خطأ", "اسم المادة مطلوب")
            return
        try:
            int(self.fields["price"].text().replace(",", ""))
        except ValueError:
            QMessageBox.warning(self, "خطأ", "السعر يجب أن يكون رقماً")
            return
        self.accept()

    def get_values(self):
        return {
            "barcode":  self.fields["barcode"].text().strip(),
            "name":     self.fields["name"].text().strip(),
            "trader":   self.fields["trader"].text().strip(),
            "unit":     self.fields["unit"].text().strip() or "piece",
            "price":    round_to_500(int(self.fields["price"].text().replace(",","") or "0")),
            "quantity": float(self.fields["quantity"].text() or "0"),
            "min_qty":  float(self.fields["min_qty"].text() or "5"),
        }


class MaterialsTab(QWidget):
    material_changed = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.load_materials()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ── Buttons ──
        btn_row = QHBoxLayout()
        self.btn_add    = QPushButton("➕ إضافة مادة")
        self.btn_edit   = QPushButton("✏️ تعديل")
        self.btn_delete = QPushButton("🗑️ حذف")
        self.btn_import = QPushButton("📥 استيراد Excel")
        self.btn_price  = QPushButton("💰 تحديث السعر من Excel")

        self.btn_add.setProperty("class", "success")
        self.btn_edit.setProperty("class", "warning")
        self.btn_delete.setProperty("class", "danger")
        self.btn_import.setProperty("class", "accent2")
        self.btn_price.setProperty("class", "accent2")

        for b in [self.btn_add, self.btn_edit, self.btn_delete, self.btn_import, self.btn_price]:
            b.setMinimumHeight(36)
            btn_row.addWidget(b)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # ── Search ──
        search_row = QHBoxLayout()
        search_lbl = QLabel("🔍 بحث:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث بالباركود أو الاسم...")
        self.search_input.setMinimumHeight(36)
        self.search_input.textChanged.connect(self.load_materials)
        search_row.addWidget(search_lbl)
        search_row.addWidget(self.search_input)
        layout.addLayout(search_row)

        # ── Table ──
        self.table = QTableWidget()
        headers = ["الباركود", "اسم المادة", "التاجر", "الوحدة", "السعر", "الكمية", "الحد الأدنى"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 110)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 100)
        layout.addWidget(self.table)

        # ── Connections ──
        self.btn_add.clicked.connect(self.add_material)
        self.btn_edit.clicked.connect(self.edit_material)
        self.btn_delete.clicked.connect(self.delete_material)
        self.btn_import.clicked.connect(self.import_from_excel)
        self.btn_price.clicked.connect(self.import_price_from_excel)

    def _set_row_color(self, row, qty, min_qty):
        """تلوين الصف بناءً على حالة المخزون"""
        if qty <= 0:
            color = QColor(C.DANGER)
            color.setAlpha(60)
        elif qty <= min_qty:
            color = QColor(C.WARNING)
            color.setAlpha(60)
        else:
            color = QColor(C.SUCCESS)
            color.setAlpha(30)
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(QBrush(color))

    def load_materials(self):
        self.table.setRowCount(0)
        search = self.search_input.text().lower() if hasattr(self, "search_input") else ""
        materials = self.db.get_all_materials()

        for mat in materials:
            barcode, name = str(mat[0]), str(mat[1])
            if search and search not in name.lower() and search not in barcode.lower():
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            vals = [barcode, name,
                    mat[2] if mat[2] else "-",
                    mat[3],
                    f"{int(mat[4]):,}",
                    mat[5],
                    mat[6]]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)
            try:
                self._set_row_color(row, float(mat[5]), float(mat[6]))
            except Exception:
                pass

    def _selected_values(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return [self.table.item(row, c).text() for c in range(self.table.columnCount())]

    def add_material(self):
        dlg = MaterialDialog(self, title="➕ إضافة مادة جديدة")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            v = dlg.get_values()
            ok, msg = self.db.add_material(
                v["barcode"], v["name"], v["trader"], v["unit"],
                v["price"], v["quantity"], v["min_qty"]
            )
            QMessageBox.information(self, "نتيجة", msg)
            if ok:
                self.load_materials()
                self.material_changed.emit()

    def edit_material(self):
        vals = self._selected_values()
        if not vals:
            QMessageBox.warning(self, "تنبيه", "اختر مادة أولاً")
            return
        # Convert price back (remove commas)
        vals[4] = vals[4].replace(",", "")
        dlg = MaterialDialog(self, values=vals, title="✏️ تعديل مادة")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            v = dlg.get_values()
            ok, msg = self.db.update_material(
                vals[0], v["barcode"], v["name"], v["trader"], v["unit"],
                v["price"], v["quantity"], v["min_qty"]
            )
            QMessageBox.information(self, "نتيجة", msg)
            if ok:
                self.load_materials()
                self.material_changed.emit()

    def delete_material(self):
        vals = self._selected_values()
        if not vals:
            QMessageBox.warning(self, "تنبيه", "اختر مادة أولاً")
            return
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل أنت متأكد من حذف المادة:\n\n📝 {vals[1]}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_material(vals[0])
            self.load_materials()
            self.material_changed.emit()

    def import_from_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف Excel", "",
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            df = pd.read_excel(path) if not path.endswith(".csv") else pd.read_csv(path)
            df.columns = [str(c).strip() for c in df.columns]

            barcode_col = name_col = price_col = qty_col = None
            for col in df.columns:
                cl = col.lower()
                if any(p in cl for p in ['باركود','barcode','رمز','كود','code','رقم']):
                    barcode_col = barcode_col or col
                if any(p in cl for p in ['اسم','name','المنتج','product','مادة','وصف']):
                    name_col = name_col or col
                if any(p in cl for p in ['سعر','price','ثمن','sell']):
                    price_col = price_col or col
                if any(p in cl for p in ['كمية','quantity','qty','stock','مخزون']):
                    qty_col = qty_col or col

            if not (barcode_col and name_col and price_col):
                QMessageBox.warning(self, "تنبيه",
                    f"لم يتم التعرف على الأعمدة المطلوبة.\n\n"
                    f"الأعمدة الموجودة:\n{', '.join(df.columns.tolist())}")
                return

            count_new = count_updated = skipped = 0
            cursor = self.db.conn.cursor()
            for _, row in df.iterrows():
                barcode = str(row[barcode_col]).strip()
                name    = str(row[name_col]).strip()
                if not barcode or not name or barcode in ('nan','None','') or name in ('nan','None',''):
                    skipped += 1
                    continue
                try:
                    price = float(str(row[price_col]).replace(',','').strip())
                except Exception:
                    skipped += 1
                    continue
                qty = 0
                if qty_col:
                    try:
                        qty = float(str(row[qty_col]).replace(',','').strip())
                    except Exception:
                        pass
                try:
                    cursor.execute("SELECT barcode FROM materials WHERE barcode=?", (barcode,))
                    if cursor.fetchone():
                        cursor.execute("UPDATE materials SET name=?, sell_price=?, quantity=? WHERE barcode=?",
                                       (name, int(price), qty, barcode))
                        count_updated += 1
                    else:
                        cursor.execute("INSERT INTO materials (barcode,name,trader_name,main_unit,sell_price,quantity,min_quantity) VALUES (?,?,?,?,?,?,?)",
                                       (barcode, name, "", "piece", int(price), qty, 5))
                        count_new += 1
                except Exception:
                    skipped += 1
            self.db.conn.commit()
            self.load_materials()
            self.material_changed.emit()
            QMessageBox.information(self, "اكتمل ✅",
                f"✅ جديدة: {count_new}\n🔄 محدَّثة: {count_updated}\n⚠️ متجاهلة: {skipped}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل الاستيراد: {e}")

    def import_price_from_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "ملف تحديث الأسعار", "",
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            df = pd.read_excel(path) if not path.endswith(".csv") else pd.read_csv(path)
            df.columns = [str(c).strip() for c in df.columns]

            barcode_col = price_col = None
            for col in df.columns:
                cl = col.lower()
                if any(p in cl for p in ['باركود','barcode','رمز','كود']):
                    barcode_col = barcode_col or col
                if any(p in cl for p in ['سعر','price','ثمن']):
                    price_col = price_col or col

            if not (barcode_col and price_col):
                QMessageBox.warning(self, "تنبيه", "تعذّر اكتشاف أعمدة الباركود والسعر")
                return

            cursor = self.db.conn.cursor()
            cursor.execute("SELECT barcode FROM materials")
            db_barcodes = {str(r[0]).strip() for r in cursor.fetchall()}
            EMPTY = {"nan","none","null",""}
            count = 0
            for _, row in df.iterrows():
                bc = str(row[barcode_col]).strip().rstrip(".0")
                if bc.lower() in EMPTY or bc not in db_barcodes:
                    continue
                try:
                    price = float(str(row[price_col]).replace(",","").strip())
                    cursor.execute("UPDATE materials SET sell_price=? WHERE barcode=?", (round(price), bc))
                    count += 1
                except Exception:
                    pass
            self.db.conn.commit()
            self.load_materials()
            self.material_changed.emit()
            QMessageBox.information(self, "تم ✅", f"تم تحديث {count} مادة")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل العملية: {e}")
