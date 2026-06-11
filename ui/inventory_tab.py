"""inventory_tab.py — تبويب المخزون (PyQt6)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QDoubleSpinBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush
from theme import C

class InventoryTab(QWidget):
    material_changed = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.load_inventory()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Buttons
        btn_row = QHBoxLayout()
        btn_add = QPushButton("➕ إضافة كمية للمخزون")
        btn_add.setProperty("class", "success")
        btn_refresh = QPushButton("🔄 تحديث")
        btn_refresh.setProperty("class", "accent2")
        btn_alert = QPushButton("⚠️ تنبيهات المخزون")
        btn_alert.setProperty("class", "warning")
        for b in [btn_add, btn_refresh, btn_alert]:
            b.setMinimumHeight(36)
            btn_row.addWidget(b)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Search
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 ابحث بالباركود أو الاسم...")
        self.search_input.setMinimumHeight(34)
        self.search_input.textChanged.connect(self.load_inventory)
        search_row.addWidget(QLabel("🔍 بحث:"))
        search_row.addWidget(self.search_input)
        layout.addLayout(search_row)

        # Table
        self.table = QTableWidget()
        headers = ["الباركود", "اسم المادة", "الوحدة", "السعر", "الكمية", "الحد الأدنى", "الحالة", "قيمة المخزون"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Summary
        self.summary_lbl = QLabel("💰 القيمة الإجمالية للمخزون: 0 ل.س")
        self.summary_lbl.setStyleSheet(f"color:{C.SUCCESS};font-size:14px;font-weight:bold;padding:8px;")
        self.low_lbl = QLabel("")
        self.low_lbl.setStyleSheet(f"color:{C.DANGER};font-size:12px;padding:4px;")
        layout.addWidget(self.summary_lbl)
        layout.addWidget(self.low_lbl)

        # Connect
        btn_add.clicked.connect(self.add_quantity)
        btn_refresh.clicked.connect(self.load_inventory)
        btn_alert.clicked.connect(self.show_low_stock_alert)

    def load_inventory(self):
        self.table.setRowCount(0)
        search = self.search_input.text().lower()
        materials = self.db.get_all_materials()
        total_value = 0

        for mat in materials:
            barcode, name = str(mat[0]), str(mat[1])
            if search and search not in name.lower() and search not in barcode.lower():
                continue
            qty = float(mat[5])
            min_qty = float(mat[6])
            price = int(mat[4])
            stock_val = qty * price
            total_value += stock_val

            if qty <= 0:
                status = "❌ نفدت"
                color = QColor(C.DANGER); color.setAlpha(60)
            elif qty <= min_qty:
                status = "⚠️ منخفض"
                color = QColor(C.WARNING); color.setAlpha(60)
            else:
                status = "✅ متوفر"
                color = QColor(C.SUCCESS); color.setAlpha(30)

            row = self.table.rowCount()
            self.table.insertRow(row)
            vals = [barcode, name, mat[3], f"{price:,}", qty, min_qty, status, f"{stock_val:,.0f}"]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(QBrush(color))
                self.table.setItem(row, col, item)

        self.summary_lbl.setText(f"💰 القيمة الإجمالية للمخزون: {total_value:,.0f} ل.س")
        low = self.db.get_low_stock_materials()
        if low:
            self.low_lbl.setText(f"⚠️ {len(low)} مادة وصلت للحد الأدنى")
        else:
            self.low_lbl.setText("✅ جميع المواد بكميات كافية")

    def add_quantity(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "اختر مادة من الجدول أولاً")
            return
        barcode = self.table.item(row, 0).text()
        name    = self.table.item(row, 1).text()
        current = float(self.table.item(row, 4).text())

        dlg = QDialog(self)
        dlg.setWindowTitle("➕ إضافة كمية")
        dlg.setMinimumWidth(300)
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel(f"المادة: {name}"))
        layout.addWidget(QLabel(f"الكمية الحالية: {current}"))
        spin = QDoubleSpinBox()
        spin.setRange(0.01, 99999)
        spin.setValue(1)
        spin.setMinimumHeight(34)
        layout.addWidget(QLabel("الكمية المضافة:"))
        layout.addWidget(spin)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("✅ إضافة")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            qty_add = spin.value()
            self.db.update_quantity(barcode, qty_add, is_sale=False)
            self.load_inventory()
            self.material_changed.emit()
            QMessageBox.information(self, "✅ تم", f"تمت إضافة {qty_add} للمادة: {name}")

    def show_low_stock_alert(self):
        low = self.db.get_low_stock_materials()
        out = self.db.get_out_of_stock_materials()
        msg = ""
        if out:
            msg += "❌ مواد نفدت:\n"
            for m in out:
                msg += f"  • {m[1]} (الكمية: {m[2]})\n"
        if low:
            msg += "\n⚠️ مواد وصلت للحد الأدنى:\n"
            for m in low:
                msg += f"  • {m[1]} (المتبقي: {m[2]} / الحد: {m[3]})\n"
        if not msg:
            msg = "✅ المخزون بحالة جيدة"
        QMessageBox.information(self, "حالة المخزون", msg)
