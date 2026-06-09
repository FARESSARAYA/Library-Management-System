"""
main.py — نقطة الدخول الرئيسية
مكتبة الفراشات — نظام البيع وإدارة المخزون

الهيكل الجديد:
  config.py                       ← الإعدادات والمسارات
  license.py                      ← نظام الترخيص
  database.py                     ← قاعدة البيانات (SQLite)
  printer.py                      ← الطباعة وحفظ الفواتير
  reports.py                      ← نوافذ التقارير
  ui/
    login_window.py               ← نافذة تسجيل الدخول
    main_window.py                ← النافذة الرئيسية (AccountingSystem)
    sales_tab.py                  ← تبويب المبيعات
    supplier_invoices_tab.py      ← تبويب فواتير الموردين
    returns_tab.py                ← تبويب المرتجعات والتبديلات
    expenses_tab.py               ← تبويب المصروفات
    inventory_tab.py              ← تبويب المخزون
    materials_tab.py              ← تبويب إدارة المواد
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


import tkinter as tk
from tkinter import messagebox

from config  import DB_PATH, BASE_DIR, TRIAL_DAYS
from license import LicenseManager, ActivationWindow
from ui.login_window import LoginWindow
from ui.main_window  import AccountingSystem

import os
try:
    from backup_system import DatabaseBackup
    _backup = DatabaseBackup(
        db_path=DB_PATH,
        backup_folder=os.path.join(BASE_DIR, "backups"),
        interval_hours=6,
        keep_last=28,
        compress=True,
    )
    _backup.start_auto_backup(backup_now=True)
except ImportError:
    pass   


def _launch_main():
    root = tk.Tk()
    AccountingSystem(root)
    root.mainloop()


def _launch_login():
    root = tk.Tk()
    LoginWindow(root, _launch_main)
    root.mainloop()


def main():
    LicenseManager.init_if_new()

    if LicenseManager.is_activated():
        _launch_login()

    elif LicenseManager.is_trial_expired():
        root = tk.Tk()
        ActivationWindow(root, _launch_login)
        root.mainloop()

    else:
        days_left = TRIAL_DAYS - LicenseManager.days_used()
        if days_left <= 2:
            tmp = tk.Tk()
            tmp.withdraw()
            messagebox.showwarning(
                "تنبيه",
                f"⚠️ تنبيه: باقي {days_left} يوم فقط من فترة التجربة المجانية.\n"
                "بعدها ستحتاج إلى مفتاح تفعيل."
            )
            tmp.destroy()
        _launch_login()


if __name__ == "__main__":
    main()
