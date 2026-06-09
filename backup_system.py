# backup_system.py
import sqlite3
import shutil
import threading
import time
import zipfile
import logging
import os
from datetime import datetime

# ─── إعداد السجل (Log) ────────────────────────────────────────────────────────
def _setup_logger(log_dir: str) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "backup.log")
    logger = logging.getLogger("DatabaseBackup")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                                datefmt="%Y-%m-%d %H:%M:%S")
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(fmt)
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger


class DatabaseBackup:
    """
    نظام نسخ احتياطي تلقائي لقاعدة بيانات SQLite.

    المميزات:
    • نسخ آمن عبر SQLite Online Backup API (لا يتأثر بقاعدة بيانات مفتوحة)
    • ضغط النسخة بصيغة ZIP لتوفير المساحة
    • نسخ كل 6 ساعات (قابل للتخصيص)
    • الاحتفاظ بآخر N نسخة وحذف القديمة تلقائيًا
    • تسجيل كامل في ملف backup.log
    • دعم الاستعادة من أحدث نسخة أو من نسخة بعينها
    """

    # 6 ساعات = 6 × 60 × 60 ثانية
    DEFAULT_INTERVAL_HOURS = 6
    DEFAULT_KEEP_LAST      = 28   # 7 أيام × 4 نسخة يوميًا (كل 6 ساعات)

    def __init__(self,
                 db_path:        str  = "accounting.db",
                 backup_folder:  str  = "backups",
                 interval_hours: int  = DEFAULT_INTERVAL_HOURS,
                 keep_last:      int  = DEFAULT_KEEP_LAST,
                 compress:       bool = True):

        self.db_path        = db_path
        self.backup_folder  = backup_folder
        self.interval_sec   = interval_hours * 3600
        self.keep_last      = keep_last
        self.compress       = compress

        os.makedirs(backup_folder, exist_ok=True)
        self.logger = _setup_logger(backup_folder)
        self._stop_event = threading.Event()

        self.logger.info(
            f"تهيئة نظام النسخ الاحتياطي | "
            f"قاعدة البيانات: {db_path} | "
            f"المجلد: {backup_folder} | "
            f"كل {interval_hours} ساعة | "
            f"الاحتفاظ بـ {keep_last} نسخة"
        )

    
    def _safe_sqlite_backup(self, dest_path: str) -> bool:
       
    
        try:
            src  = sqlite3.connect(self.db_path)
            dst  = sqlite3.connect(dest_path)
            with dst:
                src.backup(dst, pages=256)  
            src.close()
            dst.close()
            return True
        except Exception as exc:
            self.logger.error(f"فشل النسخ الآمن: {exc}")
            return False


    def create_backup(self) -> bool:
        if not os.path.exists(self.db_path):
            self.logger.warning(f"ملف قاعدة البيانات غير موجود: {self.db_path}")
            return False

        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            if self.compress:
                backup_name = f"backup_{timestamp}.zip"
                backup_path = os.path.join(self.backup_folder, backup_name)
                tmp_db      = backup_path + ".tmp.db"

                if not self._safe_sqlite_backup(tmp_db):
                    return False

                with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                    zf.write(tmp_db, arcname=f"backup_{timestamp}.db")
                os.remove(tmp_db)

                size_kb = os.path.getsize(backup_path) / 1024
                self.logger.info(f"✅ تم حفظ نسخة مضغوطة: {backup_name}  ({size_kb:.1f} KB)")

            else:
                backup_name = f"backup_{timestamp}.db"
                backup_path = os.path.join(self.backup_folder, backup_name)

                if not self._safe_sqlite_backup(backup_path):
                    return False

                size_kb = os.path.getsize(backup_path) / 1024
                self.logger.info(f"✅ تم حفظ نسخة: {backup_name}  ({size_kb:.1f} KB)")

            self._clean_old_backups()
            return True

        except Exception as exc:
            self.logger.error(f"❌ فشل النسخ الاحتياطي: {exc}")
            return False


    def _clean_old_backups(self):
        try:
            ext      = ".zip" if self.compress else ".db"
            backups  = sorted(
                [f for f in os.listdir(self.backup_folder)
                 if f.startswith("backup_") and f.endswith(ext)],
                reverse=True
            )
            removed = 0
            for old in backups[self.keep_last:]:
                os.remove(os.path.join(self.backup_folder, old))
                removed += 1
            if removed:
                self.logger.info(f"🗑️  حُذفت {removed} نسخة قديمة (الحد الأقصى: {self.keep_last})")
        except Exception as exc:
            self.logger.warning(f"تحذير أثناء تنظيف النسخ القديمة: {exc}")


    def start_auto_backup(self, backup_now: bool = True):

        hours = self.interval_sec // 3600

        def backup_loop():
            if backup_now:
                self.logger.info("📦 نسخة احتياطية أولية عند بدء التشغيل...")
                self.create_backup()

            while not self._stop_event.wait(timeout=self.interval_sec):
                self.logger.info("⏰ حان وقت النسخ الاحتياطي التلقائي...")
                self.create_backup()

        t = threading.Thread(target=backup_loop, name="BackupThread", daemon=True)
        t.start()
        self.logger.info(
            f"🔄 بدأ النسخ الاحتياطي التلقائي كل {hours} ساعة"
            f"{'  (نسخة فورية عند البدء)' if backup_now else ''}"
        )

    def stop_auto_backup(self):
        self._stop_event.set()
        self.logger.info("🛑 تم إيقاف النسخ الاحتياطي التلقائي")


    def list_backups(self) -> list[str]:
        ext     = ".zip" if self.compress else ".db"
        backups = sorted(
            [f for f in os.listdir(self.backup_folder)
             if f.startswith("backup_") and f.endswith(ext)],
            reverse=True
        )
        return backups

    def restore_backup(self, backup_name: str | None = None) -> bool:

        backups = self.list_backups()
        if not backups:
            self.logger.error("لا توجد نسخ احتياطية للاستعادة.")
            return False

        target = backup_name or backups[0]
        if target not in backups:
            self.logger.error(f"النسخة غير موجودة: {target}")
            return False

        src_path = os.path.join(self.backup_folder, target)

        try:
            if target.endswith(".zip"):
                with zipfile.ZipFile(src_path, "r") as zf:
                    db_files = [n for n in zf.namelist() if n.endswith(".db")]
                    if not db_files:
                        self.logger.error("لم يُعثر على ملف .db داخل الأرشيف.")
                        return False
                    tmp_path = self.db_path + ".restore_tmp"
                    with zf.open(db_files[0]) as src_f, open(tmp_path, "wb") as dst_f:
                        dst_f.write(src_f.read())
                os.replace(tmp_path, self.db_path)
            else:
                shutil.copy2(src_path, self.db_path)

            self.logger.info(f"✅ تمت الاستعادة من: {target}")
            return True

        except Exception as exc:
            self.logger.error(f"❌ فشل الاستعادة: {exc}")
            return False

    def restore_latest_backup(self) -> bool:
        return self.restore_backup()


    def get_status(self) -> dict:
        backups = self.list_backups()
        total_size = sum(
            os.path.getsize(os.path.join(self.backup_folder, f))
            for f in backups
        )
        return {
            "db_exists":        os.path.exists(self.db_path),
            "db_size_kb":       os.path.getsize(self.db_path) / 1024 if os.path.exists(self.db_path) else 0,
            "backup_count":     len(backups),
            "latest_backup":    backups[0] if backups else None,
            "total_size_kb":    total_size / 1024,
            "interval_hours":   self.interval_sec // 3600,
            "keep_last":        self.keep_last,
            "compress":         self.compress,
        }
