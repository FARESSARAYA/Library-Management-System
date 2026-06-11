"""supplier_invoices_tab.py — فواتير الموردين (PyQt6)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QDateEdit, QSpinBox, QDoubleSpinBox, QGroupBox, QTextEdit,
    QSplitter, QComboBox, QFrame
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QBrush
from theme import C
from datetime import datetime

class SupplierInvoicesTab(QWidget):
    material_changed = pyqtSignal()

    def __init__(self, db, on_change=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.on_change = on_change
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.load_invoices()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Summary cards
        summary_row = QHBoxLayout()
        self.card_count   = self._card("عدد الفواتير", "0", C.ACCENT)
        self.card_total   = self._card("الإجمالي", "0", C.TEXT)
        self.card_paid    = self._card("المدفوع", "0", C.SUCCESS)
        self.card_remain  = self._card("المتبقي", "0", C.DANGER)
        for c in [self.card_count, self.card_total, self.card_paid, self.card_remain]:
            summary_row.addWidget(c)
        layout.addLayout(summary_row)

        # Buttons
        btn_row = QHBoxLayout()
        btn_add    = QPushButton("➕ فاتورة جديدة")
        btn_pay    = QPushButton("💵 تسجيل دفعة")
        btn_view   = QPushButton("👁️ تفاصيل")
        btn_delete = QPushButton("🗑️ حذف")
        btn_add.setProperty("class", "success")
        btn_pay.setProperty("class", "accent2")
        btn_delete.setProperty("class", "danger")
        for b in [btn_add, btn_pay, btn_view, btn_delete]:
            b.setMinimumHeight(36)
            btn_row.addWidget(b)
        btn_row.addStretch()

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 بحث باسم المورد...")
        self.search_input.setMinimumHeight(34)
        self.search_input.textChanged.connect(self.load_invoices)
        btn_row.addWidget(self.search_input)
        layout.addLayout(btn_row)

        # Table
        self.table = QTableWidget()
        headers = ["رقم الفاتورة", "المورد", "التاريخ", "الإجمالي", "المدفوع", "المتبقي", "الحالة", "ملاحظات"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        btn_add.clicked.connect(self.add_invoice)
        btn_pay.clicked.connect(self.add_payment)
        btn_view.clicked.connect(self.view_details)
        btn_delete.clicked.connect(self.delete_invoice)

    def _card(self, title, value, color):
        frame = QFrame()
        frame.setProperty("class", "stat-card")
        frame.setMinimumHeight(70)
        lay = QVBoxLayout(frame)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t = QLabel(title); t.setStyleSheet(f"color:{C.TEXT_SUB};font-size:11px;")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v = QLabel(value); v.setStyleSheet(f"color:{color};font-size:16px;font-weight:bold;")
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t); lay.addWidget(v)
        frame._val = v
        return frame

    def load_invoices(self):
        self.table.setRowCount(0)
        search = self.search_input.text().lower() if hasattr(self, "search_input") else ""
        invoices = self.db.get_all_supplier_invoices()
        for inv in invoices:
            if search and search not in str(inv[2]).lower():
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            status = str(inv[7])
            vals = [inv[1], inv[2], inv[3],
                    f"{int(inv[4]):,}", f"{int(inv[5]):,}", f"{int(inv[6]):,}",
                    status, inv[8] or ""]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)
            if "غير" in status:
                c = QColor(C.DANGER); c.setAlpha(50)
            elif "جزئ" in status:
                c = QColor(C.WARNING); c.setAlpha(50)
            else:
                c = QColor(C.SUCCESS); c.setAlpha(30)
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item: item.setBackground(QBrush(c))
        # Update summary cards
        s = self.db.get_supplier_invoices_summary()
        self.card_count._val.setText(str(s["total_count"]))
        self.card_total._val.setText(f"{int(s['total_amount']):,}")
        self.card_paid._val.setText(f"{int(s['total_paid']):,}")
        self.card_remain._val.setText(f"{int(s['total_remaining']):,}")

    def _selected_invoice_number(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "اختر فاتورة أولاً")
            return None
        return self.table.item(row, 0).text()

    def add_invoice(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("➕ فاتورة مورد جديدة")
        dlg.setMinimumWidth(420)
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(dlg)

        form = QFormLayout()
        inv_num = QLineEdit(); inv_num.setMinimumHeight(34)
        inv_num.setText(f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        supplier = QLineEdit(); supplier.setMinimumHeight(34)
        date_edit = QDateEdit(); date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate()); date_edit.setMinimumHeight(34)
        amount = QDoubleSpinBox(); amount.setRange(0, 999_999_999)
        amount.setSuffix(" ل.س"); amount.setMinimumHeight(34)
        notes = QLineEdit(); notes.setMinimumHeight(34)

        form.addRow("رقم الفاتورة:", inv_num)
        form.addRow("اسم المورد:", supplier)
        form.addRow("التاريخ:", date_edit)
        form.addRow("المبلغ الإجمالي:", amount)
        form.addRow("ملاحظات:", notes)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Save).setText("💾 حفظ")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            if not supplier.text().strip():
                QMessageBox.warning(self, "خطأ", "اسم المورد مطلوب")
                return
            result = self.db.add_supplier_invoice(
                inv_num.text().strip(), supplier.text().strip(),
                date_edit.date().toString("yyyy-MM-dd"),
                amount.value(), notes.text().strip()
            )
            if result:
                self.load_invoices()
                if self.on_change: self.on_change()
            else:
                QMessageBox.warning(self, "خطأ", "رقم الفاتورة موجود مسبقاً")

    def add_payment(self):
        inv_num = self._selected_invoice_number()
        if not inv_num: return
        dlg = QDialog(self)
        dlg.setWindowTitle("💵 تسجيل دفعة")
        dlg.setMinimumWidth(360)
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        amount = QDoubleSpinBox(); amount.setRange(0.01, 999_999_999)
        amount.setSuffix(" ل.س"); amount.setMinimumHeight(34)
        method = QComboBox(); method.addItems(["نقد", "حوالة", "شيك"])
        method.setMinimumHeight(34)
        notes = QLineEdit(); notes.setMinimumHeight(34)
        form.addRow("المبلغ المدفوع:", amount)
        form.addRow("طريقة الدفع:", method)
        form.addRow("ملاحظات:", notes)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("✅ تسجيل")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        btns.accepted.connect(dlg.accept); btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.db.add_supplier_payment(inv_num, amount.value(), method.currentText(), notes.text())
            self.load_invoices()

    def view_details(self):
        inv_num = self._selected_invoice_number()
        if not inv_num: return
        inv = self.db.get_supplier_invoice_by_number(inv_num)
        payments = self.db.get_supplier_payments_by_invoice(inv_num)
        msg = f"فاتورة رقم: {inv[1]}\nالمورد: {inv[2]}\nالتاريخ: {inv[3]}\n"
        msg += f"الإجمالي: {int(inv[4]):,} ل.س\nالمدفوع: {int(inv[5]):,} ل.س\n"
        msg += f"المتبقي: {int(inv[6]):,} ل.س\nالحالة: {inv[7]}\n\n"
        if payments:
            msg += "── الدفعات ──\n"
            for p in payments:
                msg += f"• {p[4]}: {int(p[2]):,} ل.س ({p[5]})\n"
        QMessageBox.information(self, "تفاصيل الفاتورة", msg)

    def delete_invoice(self):
        inv_num = self._selected_invoice_number()
        if not inv_num: return
        reply = QMessageBox.question(self, "تأكيد", f"حذف الفاتورة رقم {inv_num}؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_supplier_invoice(inv_num)
            self.load_invoices()
