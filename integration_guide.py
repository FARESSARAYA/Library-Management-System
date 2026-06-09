# ═══════════════════════════════════════════════════════════════════════════════
# كيفية دمج backup_system.py المحدَّث في main.py
# ═══════════════════════════════════════════════════════════════════════════════

# ── 1. استيراد الكلاس (في أعلى main.py، موجود بالفعل) ──────────────────────
from backup_system import DatabaseBackup

# ── 2. تهيئة النظام مرة واحدة (في __init__ الكلاس الرئيسي أو بداية التطبيق) ─

self.backup = DatabaseBackup(
    db_path       = DB_PATH,        # مسار قاعدة البيانات الموجود بالفعل في main.py
    backup_folder = os.path.join(_BASE_DIR, "backups"),
    interval_hours= 6,              # ✅ كل 6 ساعات
    keep_last     = 28,             # احتفظ بآخر 28 نسخة (7 أيام)
    compress      = True,           # ضغط ZIP لتوفير المساحة
)

# ابدأ النسخ التلقائي عند تشغيل البرنامج
self.backup.start_auto_backup(backup_now=True)  # backup_now=True → نسخة فورية عند البدء


# ── 3. زر "نسخ احتياطي الآن" في الواجهة ─────────────────────────────────────
def manual_backup(self):
    success = self.backup.create_backup()
    if success:
        messagebox.showinfo("✅ تم", "تم حفظ نسخة احتياطية بنجاح!")
    else:
        messagebox.showerror("❌ خطأ", "فشل حفظ النسخة الاحتياطية.\nتحقق من ملف backups/backup.log")


# ── 4. زر "استعادة آخر نسخة" في الواجهة ─────────────────────────────────────
def restore_latest(self):
    confirm = messagebox.askyesno(
        "تأكيد الاستعادة",
        "⚠️ سيتم استبدال قاعدة البيانات الحالية بآخر نسخة احتياطية.\nهل أنت متأكد؟"
    )
    if confirm:
        success = self.backup.restore_latest_backup()
        if success:
            messagebox.showinfo("✅ تمت الاستعادة", "تمت الاستعادة بنجاح!\nأعد تشغيل البرنامج.")
        else:
            messagebox.showerror("❌ فشل", "لم يتم العثور على نسخ احتياطية.")


# ── 5. عرض حالة النظام في الواجهة (اختياري) ─────────────────────────────────
def show_backup_status(self):
    status = self.backup.get_status()
    info = (
        f"📁 عدد النسخ:       {status['backup_count']}\n"
        f"📅 أحدث نسخة:      {status['latest_backup'] or 'لا يوجد'}\n"
        f"💾 حجم قاعدة البيانات: {status['db_size_kb']:.1f} KB\n"
        f"🗜️  إجمالي حجم النسخ: {status['total_size_kb']:.1f} KB\n"
        f"⏰ الفترة:          كل {status['interval_hours']} ساعة\n"
        f"🔢 الحد الأقصى:     {status['keep_last']} نسخة\n"
        f"📦 ضغط ZIP:        {'نعم' if status['compress'] else 'لا'}"
    )
    messagebox.showinfo("حالة النسخ الاحتياطي", info)


# ── 6. مثال إضافة أزرار للواجهة في قسم القائمة أو شريط الأدوات ──────────────

# في Tkinter مثلاً:
# backup_menu = tk.Menu(menubar, tearoff=0)
# backup_menu.add_command(label="نسخ احتياطي الآن",    command=self.manual_backup)
# backup_menu.add_command(label="استعادة آخر نسخة",   command=self.restore_latest)
# backup_menu.add_separator()
# backup_menu.add_command(label="حالة النظام",         command=self.show_backup_status)
# menubar.add_cascade(label="النسخ الاحتياطي", menu=backup_menu)
