"""config.py — الإعدادات والمسارات المشتركة"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def _get_base_dir():
    """
    يحدد مجلد البرنامج بدقة سواء شغّلنا main.py مباشرة
    أو من داخل مجلد ui/ أو من أي مكان آخر.
    """
    # 1. مجلد هذا الملف (config.py) نفسه — الأموثوق
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        if os.path.isdir(here):
            return here
    except Exception:
        pass
    # 2. مجلد السكريبت المُشغَّل
    try:
        argv0 = os.path.abspath(sys.argv[0])
        d = os.path.dirname(argv0)
        # إذا كان داخل ui/ ارجع خطوة لأعلى
        if os.path.basename(d).lower() == "ui":
            d = os.path.dirname(d)
        if os.path.isdir(d):
            return d
    except Exception:
        pass
    return os.path.abspath(os.getcwd())

BASE_DIR     = _get_base_dir()
DB_PATH      = os.path.join(BASE_DIR, "accounting.db")
LICENSE_FILE = os.path.join(os.path.expanduser("~"), ".butterflies_license.json")

SECRET     = os.environ.get("APP_SECRET", "ButterfliesApp@2024#Key")
TRIAL_DAYS = 7

# ── تشخيص: اطبع المسار عند التشغيل لأول مرة ──────────────────────────────
if os.environ.get("DEBUG_PATH"):
    print(f"[config] BASE_DIR  = {BASE_DIR}")
    print(f"[config] DB_PATH   = {DB_PATH}")
    print(f"[config] DB exists = {os.path.exists(DB_PATH)}")
