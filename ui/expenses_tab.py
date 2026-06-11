"""expenses_tab.py — تبويب المصروفات (PyQt6)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QDateEdit, QSpinBox, QComboBox, QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QBrush
from theme import C
from datetime import datetime

CATEGORIES = ["إيجار", "رواتب", "كهرباء", "ماء", "اتصالات", "صيانة", "نقل", "أخرى"]


class ExpenseDialog(QDialog):
    def __init__(self, parent=None, values=None):
        super().__init__(parent)
        is_edit = values is not None
        self.setWindowTitle("✏️ تعديل مصروف" if is_edit else "➕ إضافة مصروف")
        self.setMinimumWidth(380)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumHeight(34)

        self.cat_combo = QComboBox()
        self.cat_combo.addItems(CATEGORIES)
        self.cat_combo.setMinimumHeight(34)

        self.amount_spin = QSpinBox()
        self.amount_spin.setRange(0, 99_999_999)
        self.amount_spin.setSuffix(" ل.س")
        self.amount_spin.setMinimumHeight(34)

        self.desc_edit = QLineEdit()
        self.desc_edit.setMinimumHeight(34)

        form.addRow("التاريخ:", self.date_edit)
        form.addRow("الفئة:", self.cat_combo)
        form.addRow("المبلغ:", self.amount_spin)
        form.addRow("الوصف:", self.desc_edit)
        layout.addLayout(form)

        if values:
            try:
                self.date_edit.setDate(QDate.fromString(str(values[1]), "yyyy-MM-dd"))
            except Exception:
                pass
            idx = self.cat_combo.findText(str(values[2]))
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)
            try:
                self.amount_spin.setValue(int(float(str(values[3]))))
            except Exception:
                pass
            self.desc_edit.setText(str(values[4]) if len(values) > 4 else "")

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("💾 حفظ")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_values(self):
        return {
            "date":     self.date_edit.date().toString("yyyy-MM-dd"),
            "category": self.cat_combo.currentText(),
            "amount":   self.amount_spin.value(),
            "desc":     self.desc_edit.text().strip(),
        }


class ExpensesTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.selected_id = None
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.load_all_expenses()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Filter + buttons
        top_row = QHBoxLayout()
        filter_box = QGroupBox("تصفية حسب التاريخ")
        filter_lay = QHBoxLayout(filter_box)
        self.filter_date = QDateEdit()
        self.filter_date.setCalendarPopup(True)
        self.filter_date.setDate(QDate.currentDate())
        self.filter_date.setMinimumHeight(34)
        btn_filter = QPushButton("عرض")
        btn_filter.setMinimumHeight(34)
        btn_all = QPushButton("عرض الكل")
        btn_all.setProperty("class", "accent2")
        btn_all.setMinimumHeight(34)
        filter_lay.addWidget(QLabel("التاريخ:"))
        filter_lay.addWidget(self.filter_date)
        filter_lay.addWidget(btn_filter)
        filter_lay.addWidget(btn_all)
        top_row.addWidget(filter_box)

        btn_frame = QHBoxLayout()
        btn_add    = QPushButton("➕ إضافة مصروف")
        btn_edit   = QPushButton("✏️ تعديل")
        btn_delete = QPushButton("🗑️ حذف")
        btn_add.setProperty("class", "success")
        btn_edit.setProperty("class", "warning")
        btn_delete.setProperty("class", "danger")
        for b in [btn_add, btn_edit, btn_delete]:
            b.setMinimumHeight(36)
            btn_frame.addWidget(b)
        top_row.addLayout(btn_frame)
        layout.addLayout(top_row)

        # Summary
        self.summary_lbl = QLabel("📊 إجمالي المصروفات: 0 ل.س")
        self.summary_lbl.setStyleSheet(f"color:{C.DANGER};font-size:14px;font-weight:bold;padding:6px;")
        layout.addWidget(self.summary_lbl)

        # Table
        self.table = QTableWidget()
        headers = ["#", "التاريخ", "الفئة", "المبلغ", "الوصف"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 120)
        self.table.clicked.connect(self._on_select)
        layout.addWidget(self.table)

        btn_filter.clicked.connect(self.load_expenses)
        btn_all.clicked.connect(self.load_all_expenses)
        btn_add.clicked.connect(self.add_expense)
        btn_edit.clicked.connect(self.edit_expense)
        btn_delete.clicked.connect(self.delete_expense)

    def _on_select(self):
        row = self.table.currentRow()
        if row >= 0:
            self.selected_id = int(self.table.item(row, 0).text())

    def _fill_table(self, expenses):
        self.table.setRowCount(0)
        total = 0
        for exp in expenses:
            row = self.table.rowCount()
            self.table.insertRow(row)
            vals = [exp[0], exp[1], exp[2], f"{int(exp[3]):,}", exp[4] if len(exp) > 4 else ""]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)
            total += exp[3]
        self.summary_lbl.setText(f"📊 إجمالي المصروفات: {int(total):,} ل.س")

    def load_expenses(self):
        date = self.filter_date.date().toString("yyyy-MM-dd")
        self._fill_table(self.db.get_expenses_by_date(date))

    def load_all_expenses(self):
        self._fill_table(self.db.get_all_expenses())

    def add_expense(self):
        dlg = ExpenseDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            v = dlg.get_values()
            self.db.add_expense(v["date"], v["category"], v["amount"], v["desc"])
            self.load_all_expenses()

    def edit_expense(self):
        if self.selected_id is None:
            QMessageBox.warning(self, "تنبيه", "اختر مصروفاً أولاً")
            return
        row = self.table.currentRow()
        vals = [self.table.item(row, c).text() for c in range(self.table.columnCount())]
        dlg = ExpenseDialog(self, values=vals)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            v = dlg.get_values()
            self.db.update_expense(self.selected_id, v["date"], v["category"], v["amount"], v["desc"])
            self.load_all_expenses()

    def delete_expense(self):
        if self.selected_id is None:
            QMessageBox.warning(self, "تنبيه", "اختر مصروفاً أولاً")
            return
        reply = QMessageBox.question(self, "تأكيد", "هل تريد حذف هذا المصروف؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_expense(self.selected_id)
            self.selected_id = None
            self.load_all_expenses()
