# 🦋 مكتبة الفراشات — PyQt6

نظام البيع وإدارة المخزون مُعاد كتابته بمكتبة PyQt6

## المتطلبات
```
pip install PyQt6 pandas openpyxl
```

## التشغيل
```
python main.py
```

## هيكل الملفات
```
butterflies_pyqt6/
├── main.py                    ← نقطة الدخول
├── main_window.py             ← النافذة الرئيسية
├── config.py                  ← الإعدادات والمسارات
├── database.py                ← قاعدة البيانات (SQLite)
├── theme.py                   ← الثيم الداكن
├── accounting.db              ← قاعدة البيانات
└── ui/
    ├── sales_tab.py           ← تبويب المبيعات
    ├── materials_tab.py       ← تبويب إدارة المواد
    ├── inventory_tab.py       ← تبويب المخزون
    ├── expenses_tab.py        ← تبويب المصروفات
    ├── supplier_invoices_tab.py ← فواتير الموردين
    └── returns_tab.py         ← المرتجعات

## الاختصارات
- F3          : إتمام البيع
- F5          : تحديث جميع البيانات
- Ctrl+D      : التقرير اليومي
- Ctrl+M      : التقرير الشهري
- Ctrl+I      : تقرير المخزون
- Ctrl+←/→   : التنقل بين التبويبات
```
