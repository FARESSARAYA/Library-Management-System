"""sales_tab.py — تبويب المبيعات (PyQt6) — السلة بعرض كامل"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QGroupBox, QFrame, QSpinBox, QDoubleSpinBox,
    QComboBox, QSizePolicy, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont
from theme import C
from datetime import datetime


class SalesTab(QWidget):
    material_changed = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.cart = []
        self.current_invoice = self.db.get_next_invoice_number()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._build_ui()
        self.load_materials()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # ── Stats row ──────────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.stat_total = self._stat_card("إجمالي المبيعات", "0 ل.س", C.SUCCESS)
        self.stat_count = self._stat_card("عدد الفواتير", "0", C.ACCENT)
        self.stat_low   = self._stat_card("مواد ناقصة", "0", C.DANGER)
        for s in [self.stat_total, self.stat_count, self.stat_low]:
            s.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            stats_row.addWidget(s)
        main_layout.addLayout(stats_row)
        self._refresh_stats()

        # ── Splitter عمودي: قائمة المواد فوق، السلة تحت ─────────────────
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        # ═══════════════════════════════════════════════════════════════════
        # القسم العلوي — قائمة المواد + بحث + باركود
        # ═══════════════════════════════════════════════════════════════════
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(6)

        # بحث وباركود في سطر واحد
        search_bar = QHBoxLayout()
        search_bar.setSpacing(10)

        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("📷 ادخل الباركود أو امسح...")
        self.barcode_input.setMinimumHeight(36)
        self.barcode_input.setFixedWidth(260)
        self.barcode_input.returnPressed.connect(self._on_barcode_scan)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 ابحث بالاسم أو الباركود...")
        self.search_input.setMinimumHeight(36)
        self.search_input.textChanged.connect(self.load_materials)

        btn_add_mat = QPushButton("➕ إضافة للسلة")
        btn_add_mat.setProperty("class", "success")
        btn_add_mat.setMinimumHeight(36)
        btn_add_mat.clicked.connect(self._add_selected_to_cart)

        search_bar.addWidget(QLabel("الباركود:"))
        search_bar.addWidget(self.barcode_input)
        search_bar.addSpacing(10)
        search_bar.addWidget(QLabel("🔍"))
        search_bar.addWidget(self.search_input)
        search_bar.addStretch()
        search_bar.addWidget(btn_add_mat)
        top_layout.addLayout(search_bar)

        # جدول المواد — ارتفاع مضغوط
        self.mat_table = QTableWidget()
        self.mat_table.setMaximumHeight(180)   # ✅ يأخذ مساحة صغيرة فوق
        cols = ["الباركود", "اسم المادة", "التاجر", "الوحدة", "السعر", "الكمية"]
        self.mat_table.setColumnCount(len(cols))
        self.mat_table.setHorizontalHeaderLabels(cols)
        self.mat_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.mat_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.mat_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.mat_table.setAlternatingRowColors(True)
        self.mat_table.verticalHeader().setVisible(False)
        self.mat_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.mat_table.doubleClicked.connect(self._add_selected_to_cart)
        top_layout.addWidget(self.mat_table)

        splitter.addWidget(top_widget)

        # ═══════════════════════════════════════════════════════════════════
        # القسم السفلي — السلة بعرض كامل
        # ═══════════════════════════════════════════════════════════════════
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 4, 0, 0)
        bottom_layout.setSpacing(6)

        # رأس الفاتورة: رقم + تاريخ + اسم العميل في سطر واحد
        invoice_bar = QHBoxLayout()
        self.invoice_lbl = QLabel(f"🧾 رقم الفاتورة: {self.current_invoice}")
        self.invoice_lbl.setStyleSheet(f"color:{C.SUCCESS};font-weight:bold;font-size:14px;")
        self.date_lbl = QLabel(datetime.now().strftime("📅 %Y-%m-%d"))
        self.date_lbl.setStyleSheet(f"color:{C.TEXT_SUB};")

        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("👤 اسم العميل (اختياري)")
        self.customer_input.setFixedWidth(220)
        self.customer_input.setMinimumHeight(34)

        invoice_bar.addWidget(self.invoice_lbl)
        invoice_bar.addWidget(self.date_lbl)
        invoice_bar.addStretch()
        invoice_bar.addWidget(QLabel("👤 العميل:"))
        invoice_bar.addWidget(self.customer_input)
        bottom_layout.addLayout(invoice_bar)

        # ✅ جدول السلة — يمتد بعرض كامل
        self.cart_table = QTableWidget()
        self.cart_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cart_cols = ["#", "اسم المادة", "الباركود", "السعر", "الكمية", "المجموع", "حذف"]
        self.cart_table.setColumnCount(len(cart_cols))
        self.cart_table.setHorizontalHeaderLabels(cart_cols)
        # اسم المادة يمتد
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.cart_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.cart_table.setColumnWidth(0, 35)    # #
        self.cart_table.setColumnWidth(2, 110)   # الباركود
        self.cart_table.setColumnWidth(3, 100)   # السعر
        self.cart_table.setColumnWidth(4, 80)    # الكمية
        self.cart_table.setColumnWidth(5, 100)   # المجموع
        self.cart_table.setColumnWidth(6, 50)    # حذف
        self.cart_table.cellClicked.connect(self._cart_cell_clicked)
        bottom_layout.addWidget(self.cart_table, stretch=1)

        # ── شريط الإجماليات + الأزرار في سطر واحد ──────────────────────
        footer = QHBoxLayout()
        footer.setSpacing(16)

        # الإجماليات
        totals_frame = QFrame()
        totals_frame.setProperty("class", "stat-card")
        totals_inner = QHBoxLayout(totals_frame)
        totals_inner.setContentsMargins(16, 8, 16, 8)
        totals_inner.setSpacing(24)

        self.lbl_subtotal = QLabel("0 ل.س")
        self.lbl_discount = QLabel("0 ل.س")
        self.lbl_total    = QLabel("0 ل.س")
        self.discount_input = QDoubleSpinBox()
        self.discount_input.setRange(0, 100)
        self.discount_input.setSuffix(" %")
        self.discount_input.setFixedWidth(90)
        self.discount_input.valueChanged.connect(self._calc_totals)
        self.lbl_total.setStyleSheet(f"color:{C.SUCCESS};font-size:18px;font-weight:bold;")

        for label, widget in [
            ("المجموع:", self.lbl_subtotal),
            ("خصم:", self.discount_input),
            ("قيمة الخصم:", self.lbl_discount),
            ("الإجمالي:", self.lbl_total),
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color:{C.TEXT_SUB};font-size:12px;")
            totals_inner.addWidget(lbl)
            totals_inner.addWidget(widget)

        footer.addWidget(totals_frame, stretch=1)

        # الأزرار
        btn_complete = QPushButton("✅ إتمام البيع  F3")
        btn_complete.setProperty("class", "success")
        btn_complete.setMinimumHeight(48)
        btn_complete.setMinimumWidth(180)
        btn_complete.clicked.connect(self.complete_sale)

        btn_clear = QPushButton("🗑️ مسح السلة")
        btn_clear.setProperty("class", "danger")
        btn_clear.setMinimumHeight(48)
        btn_clear.setMinimumWidth(140)
        btn_clear.clicked.connect(self._clear_cart)

        footer.addWidget(btn_complete)
        footer.addWidget(btn_clear)
        bottom_layout.addLayout(footer)

        splitter.addWidget(bottom_widget)

        # نسب الـ splitter: 35% للمواد، 65% للسلة
        splitter.setStretchFactor(0, 35)
        splitter.setStretchFactor(1, 65)

        main_layout.addWidget(splitter, stretch=1)

        # شريط الحالة
        self.status_lbl = QLabel("✅ جاهز — امسح الباركود أو اختر من القائمة")
        self.status_lbl.setStyleSheet(f"color:{C.TEXT_SUB};font-size:12px;padding:2px;")
        main_layout.addWidget(self.status_lbl)

        self.barcode_input.setFocus()

    # ── helpers ──────────────────────────────────────────────────────────────
    def _stat_card(self, title, value, color):
        frame = QFrame()
        frame.setProperty("class", "stat-card")
        frame.setMinimumHeight(76)
        frame.setMinimumWidth(130)
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(4)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color:{C.TEXT_SUB};font-size:12px;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setWordWrap(True)
        lbl_value = QLabel(value)
        lbl_value.setStyleSheet(f"color:{color};font-size:20px;font-weight:bold;")
        lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        frame._value_lbl = lbl_value
        return frame

    def _refresh_stats(self):
        cursor = self.db.conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COALESCE(SUM(total),0) FROM sales WHERE date LIKE ?", (f"{today}%",))
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT invoice_number) FROM sales WHERE date LIKE ?", (f"{today}%",))
        count = cursor.fetchone()[0]
        low = len(self.db.get_low_stock_materials())
        self.stat_total._value_lbl.setText(f"{int(total):,} ل.س")
        self.stat_count._value_lbl.setText(str(count))
        self.stat_low._value_lbl.setText(str(low))

    def load_materials(self):
        self.mat_table.setRowCount(0)
        search = self.search_input.text().lower() if hasattr(self, "search_input") else ""
        for mat in self.db.get_all_materials():
            barcode, name = str(mat[0]), str(mat[1])
            if search and search not in name.lower() and search not in barcode.lower():
                continue
            row = self.mat_table.rowCount()
            self.mat_table.insertRow(row)
            vals = [barcode, name, mat[2] or "-", mat[3], f"{int(mat[4]):,}", mat[5]]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.mat_table.setItem(row, col, item)
            qty = float(mat[5])
            if qty <= 0:
                c = QColor(C.DANGER); c.setAlpha(50)
            elif qty <= float(mat[6]):
                c = QColor(C.WARNING); c.setAlpha(50)
            else:
                c = QColor(C.SUCCESS); c.setAlpha(20)
            for col in range(self.mat_table.columnCount()):
                item = self.mat_table.item(row, col)
                if item: item.setBackground(QBrush(c))

    def _on_barcode_scan(self):
        barcode = self.barcode_input.text().strip()
        if not barcode:
            return
        mat = self.db.get_material_by_barcode(barcode)
        if mat:
            self._add_to_cart(mat)
            self.barcode_input.clear()
            self.status_lbl.setText(f"✅ تمت إضافة: {mat[1]}")
        else:
            self.status_lbl.setText(f"❌ الباركود غير موجود: {barcode}")
            self.barcode_input.selectAll()

    def _add_selected_to_cart(self):
        row = self.mat_table.currentRow()
        if row < 0:
            self.status_lbl.setText("⚠️ اختر مادة من القائمة أولاً")
            return
        barcode = self.mat_table.item(row, 0).text()
        mat = self.db.get_material_by_barcode(barcode)
        if mat:
            self._add_to_cart(mat)

    def _add_to_cart(self, mat):
        barcode = str(mat[0])
        qty = float(mat[5])
        if qty <= 0:
            QMessageBox.warning(self, "نفدت الكمية", f"❌ لا يمكن البيع — الكمية: {qty}")
            return
        for item in self.cart:
            if item["barcode"] == barcode:
                if item["qty"] + 1 > qty:
                    QMessageBox.warning(self, "تنبيه", "الكمية المطلوبة أكبر من المتاح")
                    return
                item["qty"] += 1
                item["total"] = item["qty"] * item["price"]
                self._render_cart()
                return
        self.cart.append({
            "barcode": barcode,
            "name":    mat[1],
            "price":   int(mat[4]),
            "qty":     1,
            "total":   int(mat[4]),
        })
        self._render_cart()

    def _render_cart(self):
        self.cart_table.setRowCount(0)
        for i, item in enumerate(self.cart):
            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)
            # ترتيب الأعمدة: # | اسم المادة | الباركود | السعر | الكمية | المجموع | حذف
            vals = [i+1, item["name"], item["barcode"],
                    f"{item['price']:,} ل.س", item["qty"],
                    f"{item['total']:,} ل.س", "🗑️"]
            for col, val in enumerate(vals):
                cell = QTableWidgetItem(str(val))
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 6:
                    cell.setForeground(QBrush(QColor(C.DANGER)))
                self.cart_table.setItem(row, col, cell)
        self._calc_totals()

    def _cart_cell_clicked(self, row, col):
        if col == 6:
            if 0 <= row < len(self.cart):
                self.cart.pop(row)
                self._render_cart()

    def _calc_totals(self):
        subtotal = sum(item["total"] for item in self.cart)
        disc_pct = self.discount_input.value()
        disc_amt = int(subtotal * disc_pct / 100)
        total = subtotal - disc_amt
        self.lbl_subtotal.setText(f"{subtotal:,} ل.س")
        self.lbl_discount.setText(f"{disc_amt:,} ل.س")
        self.lbl_total.setText(f"{total:,} ل.س")

    def _clear_cart(self):
        self.cart.clear()
        self._render_cart()
        self.discount_input.setValue(0)
        self.customer_input.clear()

    def complete_sale(self):
        if not self.cart:
            QMessageBox.warning(self, "تنبيه", "السلة فارغة!")
            return
        subtotal = sum(item["total"] for item in self.cart)
        disc_pct = self.discount_input.value()
        disc_amt = int(subtotal * disc_pct / 100)
        total = subtotal - disc_amt
        customer = self.customer_input.text().strip() or "زبون"
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        reply = QMessageBox.question(
            self, "تأكيد البيع",
            f"🧾 فاتورة رقم: {self.current_invoice}\n"
            f"👤 العميل: {customer}\n"
            f"📦 عدد الأصناف: {len(self.cart)}\n"
            f"💰 الإجمالي: {total:,} ل.س\n\n"
            "هل تريد إتمام البيع؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        failed = []
        for item in self.cart:
            try:
                self.db.add_sale(
                    self.current_invoice, item["barcode"], item["name"],
                    customer, "piece", item["qty"], item["price"], item["total"],
                    disc_pct, disc_amt, date
                )
            except Exception as exc:
                failed.append(f"• {item['name']}: {exc}")

        if failed:
            QMessageBox.critical(
                self, "❌ خطأ في البيع",
                "فشل حفظ بعض الأصناف:\n" + "\n".join(failed) +
                "\n\nالأصناف الأخرى تم حفظها."
            )
            self.load_materials(); self._refresh_stats(); self.material_changed.emit()
            return

        QMessageBox.information(self, "✅ تم البيع",
            f"تمت عملية البيع بنجاح!\nرقم الفاتورة: {self.current_invoice}")

        self.current_invoice = self.db.get_next_invoice_number()
        self.invoice_lbl.setText(f"🧾 رقم الفاتورة: {self.current_invoice}")
        self._clear_cart()
        self.load_materials()
        self._refresh_stats()
        self.material_changed.emit()
        self.barcode_input.setFocus()
        self.status_lbl.setText("✅ تم البيع — جاهز لفاتورة جديدة")
