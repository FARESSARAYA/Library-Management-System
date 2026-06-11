"""config.py — الإعدادات والمسارات المشتركة"""
import os

def _get_base_dir():
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        if os.path.isdir(here):
            return here
    except Exception:
        pass
    return os.path.abspath(os.getcwd())

BASE_DIR  = _get_base_dir()
DB_PATH   = os.path.join(BASE_DIR, "accounting.db")
APP_NAME  = "مكتبة الفراشات"
APP_SUB   = "نظام البيع وإدارة المخزون"
