"""main_window.py — النافذة الرئيسية (PyQt6)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QMenuBar, QMenu, QMessageBox,
    QStatusBar, QFrame, QInputDialog, QListWidget, QDialog,
    QDialogButtonBox, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QFont, QIcon, QKeySequence, QShortcut, QAction
from theme import C
from database import Database
from config import APP_NAME, APP_SUB

from ui.sales_tab            import SalesTab
from ui.supplier_invoices_tab import SupplierInvoicesTab
from ui.returns_tab          import ReturnsTab
from ui.expenses_tab         import ExpensesTab
from ui.inventory_tab        import InventoryTab
from ui.materials_tab        import MaterialsTab


class MainWindow(QMainWindow):
    def __init__(self, backup=None):
        super().__init__()
        self.db = Database()
        self.backup = backup          # نظام النسخ الاحتياطي
        self.setWindowTitle(f"{APP_NAME} — {APP_SUB}")
        self.setMinimumSize(1200, 720)
        self.resize(1400, 800)
        self._center()
        self._build_ui()
        self._build_menu()
        self._setup_shortcuts()
        self._start_clock()
        QTimer.singleShot(500, self._check_low_stock)

    def _center(self):
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        w, h = self.width(), self.height()
        self.move((screen.width() - w) // 2, (screen.height() - h) // 2)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet(f"background:{C.HEADER};border-bottom:2px solid {C.BORDER};")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)

        # Logo + title
        title_lbl = QLabel(f"🦋  {APP_NAME}")
        title_lbl.setStyleSheet(f"color:{C.WHITE};font-size:20px;font-weight:bold;")
        sub_lbl = QLabel(APP_SUB)
        sub_lbl.setStyleSheet(f"color:{C.ACCENT2};font-size:12px;")

        title_col = QVBoxLayout()
        title_col.addWidget(title_lbl)
        title_col.addWidget(sub_lbl)
        title_col.setSpacing(0)
        h_layout.addLayout(title_col)
        h_layout.addStretch()

        # Clock
        self.clock_lbl = QLabel("")
        self.clock_lbl.setStyleSheet(
            f"background:{C.ACCENT};color:{C.WHITE};"
            f"padding:6px 14px;border-radius:6px;font-size:13px;font-weight:bold;"
        )
        h_layout.addWidget(self.clock_lbl)

        # Backup badge
        self.backup_lbl = QLabel("💾 ...")
        self.backup_lbl.setStyleSheet(
            f"background:{C.CARD};color:{C.TEXT_SUB};"
            f"padding:4px 10px;border-radius:6px;font-size:11px;"
            f"border:1px solid {C.BORDER};"
        )
        self.backup_lbl.setToolTip("آخر نسخة احتياطية")
        h_layout.addWidget(self.backup_lbl)
        self._update_backup_badge()

        root_layout.addWidget(header)

        # ── Tabs ─────────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.tabs.setDocumentMode(True)
        root_layout.addWidget(self.tabs)

        # Instantiate tabs
        self.sales_tab  = SalesTab(self.db)
        self.sup_tab    = SupplierInvoicesTab(self.db, on_change=self._refresh_all)
        self.ret_tab    = ReturnsTab(self.db, on_change=self._refresh_all)
        self.inv_tab    = InventoryTab(self.db)
        self.exp_tab    = ExpensesTab(self.db)
        self.mat_tab    = MaterialsTab(self.db)

        self.tabs.addTab(self.sales_tab,  "🛒 البيع")
        self.tabs.addTab(self.sup_tab,    "📄 فواتير المشتريات")
        self.tabs.addTab(self.ret_tab,    "🔄 المرتجعات")
        self.tabs.addTab(self.inv_tab,    "📦 المخزون")
        self.tabs.addTab(self.exp_tab,    "💸 المصروفات")
        self.tabs.addTab(self.mat_tab,    "📦 المواد")

        # Cross-tab refresh
        self.sales_tab.material_changed.connect(self._on_material_changed)
        self.mat_tab.material_changed.connect(self._on_material_changed)
        self.inv_tab.material_changed.connect(self._on_material_changed)

        # ── Status bar ───────────────────────────────────────────────────────
        self.status = QStatusBar()
        self.status.setStyleSheet(f"background:{C.HEADER};color:{C.TEXT_SUB};font-size:12px;")
        self.setStatusBar(self.status)
        self.status.showMessage("✅ مكتبة الفراشات — جاهز")

    def _build_menu(self):
        menubar = self.menuBar()
        menubar.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        menubar.setStyleSheet(f"""
            QMenuBar {{ background:{C.HEADER};color:{C.TEXT}; }}
            QMenuBar::item:selected {{ background:{C.ACCENT}; }}
            QMenu {{ background:{C.CARD};color:{C.TEXT};border:1px solid {C.BORDER}; }}
            QMenu::item:selected {{ background:{C.ACCENT}; }}
        """)

        reports_menu = menubar.addMenu("📋 تقارير")
        act_daily  = reports_menu.addAction("📊 التقرير اليومي  (Ctrl+D)")
        act_month  = reports_menu.addAction("📅 التقرير الشهري (Ctrl+M)")
        act_inv    = reports_menu.addAction("📦 تقرير المخزون  (Ctrl+I)")

        act_daily.triggered.connect(self._report_daily)
        act_month.triggered.connect(self._report_monthly)
        act_inv.triggered.connect(self._report_inventory)

        # ── قائمة النسخ الاحتياطي ──────────────────────────────────────────
        backup_menu = menubar.addMenu("💾 النسخ الاحتياطي")
        act_backup_now  = backup_menu.addAction("📦 نسخ احتياطي الآن")
        act_backup_list = backup_menu.addAction("📋 عرض النسخ المتاحة")
        act_backup_restore = backup_menu.addAction("♻️ استعادة نسخة...")
        act_backup_status  = backup_menu.addAction("ℹ️ حالة النظام")

        act_backup_now.triggered.connect(self._backup_now)
        act_backup_list.triggered.connect(self._backup_list)
        act_backup_restore.triggered.connect(self._backup_restore)
        act_backup_status.triggered.connect(self._backup_status)

        help_menu = menubar.addMenu("❓ مساعدة")
        act_shortcuts = help_menu.addAction("⌨️ اختصارات البرنامج")
        act_shortcuts.triggered.connect(self._show_shortcuts)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("F3"), self).activated.connect(
            lambda: self.sales_tab.complete_sale() if self.tabs.currentIndex() == 0 else None
        )
        QShortcut(QKeySequence("F5"), self).activated.connect(self._refresh_all)
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self._report_daily)
        QShortcut(QKeySequence("Ctrl+M"), self).activated.connect(self._report_monthly)
        QShortcut(QKeySequence("Ctrl+I"), self).activated.connect(self._report_inventory)
        QShortcut(QKeySequence("Ctrl+Right"), self).activated.connect(
            lambda: self.tabs.setCurrentIndex(min(self.tabs.count()-1, self.tabs.currentIndex()+1))
        )
        QShortcut(QKeySequence("Ctrl+Left"), self).activated.connect(
            lambda: self.tabs.setCurrentIndex(max(0, self.tabs.currentIndex()-1))
        )

    def _start_clock(self):
        self._tick()
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)

        # تحديث badge النسخ الاحتياطي كل 5 دقائق
        self._badge_timer = QTimer(self)
        self._badge_timer.timeout.connect(self._update_backup_badge)
        self._badge_timer.start(5 * 60 * 1000)

    def _update_backup_badge(self):
        if not self.backup:
            self.backup_lbl.setText("💾 غير مفعّل")
            return
        backups = self.backup.list_backups()
        if backups:
            # استخلاص التاريخ من اسم الملف: backup_20260525_143000.zip
            name = backups[0]
            try:
                ts = name.replace("backup_", "").split(".")[0]  # 20260525_143000
                date_part, time_part = ts.split("_")
                label = f"{date_part[6:8]}/{date_part[4:6]}/{date_part[:4]}  {time_part[:2]}:{time_part[2:4]}"
                self.backup_lbl.setText(f"💾 {label}")
                self.backup_lbl.setStyleSheet(
                    f"background:{C.CARD};color:{C.SUCCESS};"
                    f"padding:4px 10px;border-radius:6px;font-size:11px;"
                    f"border:1px solid {C.SUCCESS};"
                )
            except Exception:
                self.backup_lbl.setText(f"💾 {len(backups)} نسخة")
        else:
            self.backup_lbl.setText("💾 لا توجد نسخ")
            self.backup_lbl.setStyleSheet(
                f"background:{C.CARD};color:{C.WARNING};"
                f"padding:4px 10px;border-radius:6px;font-size:11px;"
                f"border:1px solid {C.WARNING};"
            )

    # ── دوال النسخ الاحتياطي ────────────────────────────────────────────────
    def _backup_now(self):
        if not self.backup:
            QMessageBox.warning(self, "تنبيه", "نظام النسخ الاحتياطي غير مفعّل")
            return
        self.status.showMessage("⏳ جارٍ أخذ نسخة احتياطية...")
        ok = self.backup.create_backup()
        if ok:
            self._update_backup_badge()
            self.status.showMessage("✅ تم أخذ نسخة احتياطية بنجاح", 4000)
            QMessageBox.information(self, "✅ نسخ احتياطي", "تمت عملية النسخ الاحتياطي بنجاح!")
        else:
            self.status.showMessage("❌ فشل النسخ الاحتياطي", 4000)
            QMessageBox.critical(self, "❌ خطأ", "فشلت عملية النسخ الاحتياطي.\nراجع ملف backup.log للتفاصيل.")

    def _backup_list(self):
        if not self.backup:
            QMessageBox.warning(self, "تنبيه", "نظام النسخ الاحتياطي غير مفعّل")
            return
        backups = self.backup.list_backups()
        if not backups:
            QMessageBox.information(self, "النسخ الاحتياطية", "لا توجد نسخ احتياطية حتى الآن.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("📋 النسخ الاحتياطية المتاحة")
        dlg.setMinimumWidth(420)
        dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel(f"إجمالي النسخ: {len(backups)}"))
        lst = QListWidget()
        for b in backups:
            lst.addItem(b)
        layout.addWidget(lst)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        dlg.exec()

    def _backup_restore(self):
        if not self.backup:
            QMessageBox.warning(self, "تنبيه", "نظام النسخ الاحتياطي غير مفعّل")
            return
        backups = self.backup.list_backups()
        if not backups:
            QMessageBox.information(self, "استعادة", "لا توجد نسخ احتياطية للاستعادة.")
            return

        chosen, ok = QInputDialog.getItem(
            self, "♻️ استعادة نسخة احتياطية",
            "اختر النسخة المراد استعادتها:",
            backups, 0, False
        )
        if not ok or not chosen:
            return

        confirm = QMessageBox.warning(
            self, "⚠️ تأكيد الاستعادة",
            f"سيتم استبدال قاعدة البيانات الحالية بالنسخة:\n{chosen}\n\n"
            "هذا الإجراء لا يمكن التراجع عنه. هل أنت متأكد؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        # إغلاق الاتصال قبل الاستعادة
        try:
            self.db.conn.close()
        except Exception:
            pass

        ok = self.backup.restore_backup(chosen)
        if ok:
            QMessageBox.information(
                self, "✅ تمت الاستعادة",
                "تمت استعادة قاعدة البيانات.\nسيُعاد تشغيل الاتصال تلقائياً."
            )
            # إعادة فتح الاتصال
            from database import Database
            self.db = Database()
            self._refresh_all()
        else:
            QMessageBox.critical(self, "❌ خطأ", "فشلت عملية الاستعادة.\nراجع ملف backup.log للتفاصيل.")
            # إعادة فتح الاتصال على أي حال
            from database import Database
            self.db = Database()

    def _backup_status(self):
        if not self.backup:
            QMessageBox.information(self, "حالة النسخ الاحتياطي", "النظام غير مفعّل.")
            return
        st = self.backup.get_status()
        backups = self.backup.list_backups()
        msg = (
            f"📁 قاعدة البيانات موجودة: {'نعم' if st['db_exists'] else 'لا'}\n"
            f"📏 حجمها: {st['db_size_kb']:.1f} KB\n\n"
            f"🗂️  عدد النسخ: {st['backup_count']}\n"
            f"📦 أحدث نسخة: {st['latest_backup'] or 'لا توجد'}\n"
            f"💿 الحجم الكلي للنسخ: {st['total_size_kb']:.1f} KB\n\n"
            f"⏰ تكرار النسخ: كل {st['interval_hours']} ساعة\n"
            f"🗄️  الاحتفاظ بـ: {st['keep_last']} نسخة\n"
            f"🗜️  ضغط: {'نعم' if st['compress'] else 'لا'}"
        )
        QMessageBox.information(self, "ℹ️ حالة نظام النسخ الاحتياطي", msg)

    def _tick(self):
        from datetime import datetime
        now = datetime.now().strftime("🕐 %Y-%m-%d  %H:%M:%S")
        self.clock_lbl.setText(now)

    def _on_material_changed(self):
        self.sales_tab.load_materials()
        self.inv_tab.load_inventory()
        self.mat_tab.load_materials()

    def _refresh_all(self):
        self._on_material_changed()
        self.exp_tab.load_all_expenses()
        self.ret_tab.load_returns()
        self.sup_tab.load_invoices()
        self.sales_tab._refresh_stats()
        self.status.showMessage("🔄 تم تحديث جميع البيانات", 3000)

    def _check_low_stock(self):
        low = self.db.get_low_stock_materials()
        out = self.db.get_out_of_stock_materials()
        msg = ""
        if out:
            msg += "❌ مواد نفدت من المخزون:\n"
            for m in out:
                msg += f"  • {m[1]} (الكمية: {m[2]})\n"
        if low:
            msg += "\n⚠️ مواد وصلت للحد الأدنى:\n"
            for m in low:
                msg += f"  • {m[1]} (المتبقي: {m[2]} / الحد: {m[3]})\n"
        if msg:
            QMessageBox.warning(self, "⚠️ تنبيه المخزون", msg)

    def _report_daily(self):
        from datetime import datetime
        cursor = self.db.conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT COALESCE(SUM(total),0) FROM sales WHERE date LIKE ?", (f"{today}%",))
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT invoice_number) FROM sales WHERE date LIKE ?", (f"{today}%",))
        count = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE date=?", (today,))
        expenses = cursor.fetchone()[0]
        QMessageBox.information(self, f"📊 التقرير اليومي — {today}",
            f"📅 التاريخ: {today}\n\n"
            f"🧾 عدد الفواتير: {count}\n"
            f"💰 إجمالي المبيعات: {int(total):,} ل.س\n"
            f"💸 إجمالي المصروفات: {int(expenses):,} ل.س\n"
            f"📈 صافي اليوم: {int(total - expenses):,} ل.س"
        )

    def _report_monthly(self):
        from datetime import datetime
        now = datetime.now()
        cursor = self.db.conn.cursor()
        prefix = f"{now.year}-{now.month:02d}"
        cursor.execute("SELECT COALESCE(SUM(total),0) FROM sales WHERE date LIKE ?", (f"{prefix}%",))
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE date LIKE ?", (f"{prefix}%",))
        expenses = cursor.fetchone()[0]
        QMessageBox.information(self, f"📅 التقرير الشهري — {prefix}",
            f"📅 الشهر: {prefix}\n\n"
            f"💰 إجمالي المبيعات: {int(total):,} ل.س\n"
            f"💸 إجمالي المصروفات: {int(expenses):,} ل.س\n"
            f"📈 صافي الشهر: {int(total - expenses):,} ل.س"
        )

    def _report_inventory(self):
        mats = self.db.get_all_materials()
        total_val = sum(int(m[4]) * float(m[5]) for m in mats)
        low  = self.db.get_low_stock_materials()
        out  = self.db.get_out_of_stock_materials()
        QMessageBox.information(self, "📦 تقرير المخزون",
            f"📦 إجمالي الأصناف: {len(mats)}\n"
            f"💰 القيمة الإجمالية: {total_val:,.0f} ل.س\n"
            f"⚠️ مواد منخفضة: {len(low)}\n"
            f"❌ مواد نفدت: {len(out)}"
        )

    def _show_shortcuts(self):
        QMessageBox.information(self, "⌨️ اختصارات البرنامج",
            "F3          : إتمام البيع\n"
            "F5          : تحديث جميع البيانات\n"
            "Ctrl + D    : التقرير اليومي\n"
            "Ctrl + M    : التقرير الشهري\n"
            "Ctrl + I    : تقرير المخزون\n"
            "Ctrl + →    : التبويب التالي\n"
            "Ctrl + ←    : التبويب السابق"
        )

    def closeEvent(self, event):
        try:
            if self.backup:
                self.backup.stop_auto_backup()
            self.db.conn.commit()
            self.db.conn.close()
        except Exception:
            pass
        event.accept()
