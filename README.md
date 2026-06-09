# 🦋 مكتبة الفراشات — هيكل المشروع

## الملفات الرئيسية
- `main.py`           — نقطة الدخول الرئيسية
- `database.py`       — قاعدة البيانات وكل العمليات
- `config.py`         — الإعدادات العامة
- `license.py`        — نظام الترخيص والتفعيل
- `reports.py`        — التقارير
- `printer.py`        — الطباعة
- `check_db.py`       — فحص قاعدة البيانات

## الملفات المساعدة
- `backup_system.py`  — نظام النسخ الاحتياطي التلقائي (كل 6 ساعات)
- `excel_handler.py`  — استيراد/تصدير Excel
- `theme.py`          — ثيم PyQt5 الموحد (ألوان، ستايل، StatCard، SidebarButton)
- `integration_guide.py` — دليل دمج نظام النسخ الاحتياطي

## مجلد ui/
- `sales_tab.py`          — تبويب البيع
- `inventory_tab.py`      — تبويب المخزون
- `materials_tab.py`      — تبويب المواد
- `expenses_tab.py`       — تبويب المصروفات
- `returns_tab.py`        — تبويب المرتجعات والتبديلات
- `supplier_invoices_tab.py` — تبويب فواتير المشتريات
- `login_window.py`       — نافذة تسجيل الدخول
- `main_window.py`        — النافذة الرئيسية

## تشغيل البرنامج
```
python main.py
```
