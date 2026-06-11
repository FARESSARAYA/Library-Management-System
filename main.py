"""main.py — نقطة الدخول الرئيسية (PyQt6)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from theme import apply_app_style
from main_window import MainWindow
from backup_system import DatabaseBackup
from config import DB_PATH, BASE_DIR

def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    apply_app_style(app)

    # ── نظام النسخ الاحتياطي التلقائي ──────────────────────────────────────
    backup = DatabaseBackup(
        db_path       = DB_PATH,
        backup_folder = os.path.join(BASE_DIR, "backups"),
        interval_hours= 6,
        keep_last     = 28,   # 7 أيام × 4 نسخ يومياً
        compress      = True,
    )
    backup.start_auto_backup(backup_now=True)   # نسخة فورية عند البدء
    app._backup = backup                        # نمنع garbage collection

    win = MainWindow(backup=backup)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
