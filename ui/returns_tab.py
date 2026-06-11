"""returns_tab.py — تبويب المرتجعات (PyQt6)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QDateEdit, QDoubleSpinBox, QSpinBox, QTabWidget, QGroupBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QBrush
from theme import C
from datetime import datetime


class ReturnsTab(QWidget):
    material_changed = pyqtSignal()

    def __init__(self, db, on_change=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.on_change = on_change
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.load_returns()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        sub_tabs = QTabWidget()

        # ── Returns ──
        ret_widget = QWidget()
        ret_layout = QVBoxLayout(ret_widget)
        ret_layout.setContentsMargins(8, 8, 8, 8)

        btn_row = QHBoxLayout()
        btn_add_ret = QPushButton("➕ تسجيل مرتجع")
        btn_add_ret.setProperty("class", "success")
        btn_add_ret.setMinimumHeight(36)
        btn_row.addWidget(btn_add_ret)
        btn_row.addStretch()
        ret_layout.addLayout(btn_row)

        self.ret_table = QTableWidget()
        ret_headers = ["رقم المرتجع", "فاتورة أصلية", "الباركود", "المادة",
                       "العميل", "الكمية", "سعر الإرجاع", "الإجمالي", "السبب", "التاريخ", "الحالة"]
        self.ret_table.setColumnCount(len(ret_headers))
        self.ret_table.setHorizontalHeaderLabels(ret_headers)
        self.ret_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.ret_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ret_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.ret_table.setAlternatingRowColors(True)
        self.ret_table.verticalHeader().setVisible(False)
        ret_layout.addWidget(self.ret_table)

        self.ret_summary = QLabel("📊 إجمالي المرتجعات: 0 ل.س")
        self.ret_summary.setStyleSheet(f"color:{C.WARNING};font-size:13px;font-weight:bold;padding:5px;")
        ret_layout.addWidget(self.ret_summary)
        sub_tabs.addTab(ret_widget, "🔄 المرتجعات")

        layout.addWidget(sub_tabs)

        btn_add_ret.clicked.connect(self.add_return)

    def load_returns(self):
        self.ret_table.setRowCount(0)
        returns = self.db.get_all_returns()
        total = 0
        for r in returns:
            row = self.ret_table.rowCount()
            self.ret_table.insertRow(row)
            vals = list(r[1:])  # skip id
            for col, val in enumerate(vals):
                item = QTableWidgetItem(str(val) if val is not None else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.ret_table.setItem(row, col, item)
            try: total += float(r[8])
            except Exception: pass
        self.ret_summary.setText(f"📊 إجمالي المرتجعات: {int(total):,} ل.س")

    def add_return(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("➕ تسجيل مرتجع")
        dlg.setMinimumWidth(420)
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(dlg)
        form = QFormLayout()

        orig_inv = QSpinBox(); orig_inv.setRange(1, 999999); orig_inv.setMinimumHeight(34)
        barcode  = QLineEdit(); barcode.setMinimumHeight(34)
        mat_name = QLineEdit(); mat_name.setMinimumHeight(34)
        customer = QLineEdit(); customer.setMinimumHeight(34)
        qty      = QDoubleSpinBox(); qty.setRange(0.01, 9999); qty.setValue(1); qty.setMinimumHeight(34)
        price    = QSpinBox(); price.setRange(0, 99_999_999); price.setMinimumHeight(34)
        reason   = QLineEdit(); reason.setMinimumHeight(34)
        date_e   = QDateEdit(); date_e.setCalendarPopup(True); date_e.setDate(QDate.currentDate()); date_e.setMinimumHeight(34)

        # Auto-fill from barcode
        def on_barcode_changed():
            bc = barcode.text().strip()
            mat = self.db.get_material_by_barcode(bc)
            if mat:
                mat_name.setText(mat[1])
                price.setValue(int(mat[4]))

        barcode.editingFinished.connect(on_barcode_changed)

        form.addRow("رقم الفاتورة الأصلية:", orig_inv)
        form.addRow("الباركود:", barcode)
        form.addRow("اسم المادة:", mat_name)
        form.addRow("اسم العميل:", customer)
        form.addRow("الكمية:", qty)
        form.addRow("سعر الإرجاع:", price)
        form.addRow("السبب:", reason)
        form.addRow("التاريخ:", date_e)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("💾 حفظ")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            if not barcode.text().strip():
                QMessageBox.warning(self, "خطأ", "الباركود مطلوب")
                return
            ret_num = self.db.get_next_return_number()
            total_ret = int(qty.value() * price.value())
            self.db.add_return(
                ret_num, orig_inv.value(), barcode.text().strip(),
                mat_name.text().strip(), customer.text().strip(),
                qty.value(), price.value(), total_ret,
                reason.text().strip(),
                date_e.date().toString("yyyy-MM-dd HH:mm:ss"),
                "تم الإرجاع"
            )
            self.load_returns()
            if self.on_change: self.on_change()
            QMessageBox.information(self, "✅ تم", f"تم تسجيل المرتجع رقم {ret_num}")
