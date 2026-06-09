"""
check_db.py — سكريبت تشخيص سريع
شغّله بـ: python check_db.py
يخبرك أين يبحث البرنامج عن قاعدة البيانات وكم فيها من بيانات
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import BASE_DIR, DB_PATH

print("=" * 55)
print(f"  مجلد البرنامج : {BASE_DIR}")
print(f"  مسار الداتابيز: {DB_PATH}")
print(f"  الداتابيز موجودة: {'✅ نعم' if os.path.exists(DB_PATH) else '❌ لا — سيتم إنشاء واحدة فارغة!'}")
print("=" * 55)

if os.path.exists(DB_PATH):
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    tables = ["materials", "sales", "supplier_invoices", "returns", "expenses"]
    for t in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  {t:25s}: {count} سجل")
        except Exception as e:
            print(f"  {t:25s}: خطأ — {e}")
    conn.close()
else:
    print()
    print("  ⚠️  الداتابيز غير موجودة في هذا المجلد!")
    print()
    print("  الحل: انسخ ملف accounting.db إلى هذا المجلد:")
    print(f"  {BASE_DIR}")
    print()
    # ابحث عن accounting.db في أماكن شائعة
    search_paths = [
        os.path.join(os.path.expanduser("~"), "Desktop"),
        r"C:\Users\Fares\Desktop",
        r"D:\database",
        r"C:\database",
    ]
    print("  أو ابحث عنها هنا:")
    for sp in search_paths:
        candidate = os.path.join(sp, "accounting.db")
        if os.path.exists(candidate):
            print(f"  ✅ وجدتها هنا: {candidate}")

input("\nاضغط Enter للإغلاق...")
