"""theme.py — ثيم PyQt6 الداكن لمكتبة الفراشات"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtCore import Qt

# ── ألوان التطبيق ──────────────────────────────────────────────────────────
class C:
    BG       = "#0f1117"   # خلفية رئيسية
    BG2      = "#1a1d27"   # خلفية ثانوية
    CARD     = "#1e2130"   # بطاقات
    BORDER   = "#2d3150"   # حدود
    ACCENT   = "#5B8CFF"   # أزرق رئيسي
    ACCENT2  = "#8B5CF6"   # بنفسجي
    SUCCESS  = "#22D3A8"   # أخضر
    DANGER   = "#FF4D6D"   # أحمر
    WARNING  = "#FBBF24"   # أصفر
    TEXT     = "#E2E8F0"   # نص رئيسي
    TEXT_SUB = "#94a3b8"   # نص ثانوي
    WHITE    = "#FFFFFF"
    HEADER   = "#141824"   # خلفية الهيدر

STYLESHEET = f"""
/* ──────────────────────────────────────────────────────── */
/*  Global                                                  */
/* ──────────────────────────────────────────────────────── */
* {{
    font-family: 'Segoe UI', 'Arial', sans-serif;
    color: {C.TEXT};
}}
QMainWindow, QDialog {{
    background-color: {C.BG};
}}
QWidget {{
    background-color: {C.BG};
}}

/* ──────────────────────────────────────────────────────── */
/*  QTabWidget                                              */
/* ──────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {C.BORDER};
    background: {C.BG2};
    border-radius: 6px;
}}
QTabBar::tab {{
    background: {C.BG2};
    color: {C.TEXT_SUB};
    padding: 10px 20px;
    border: 1px solid {C.BORDER};
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    min-width: 110px;
    font-size: 13px;
    font-weight: bold;
}}
QTabBar::tab:selected {{
    background: {C.ACCENT};
    color: {C.WHITE};
    border-color: {C.ACCENT};
}}
QTabBar::tab:hover:!selected {{
    background: {C.BORDER};
    color: {C.TEXT};
}}

/* ──────────────────────────────────────────────────────── */
/*  Buttons                                                 */
/* ──────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {C.ACCENT};
    color: {C.WHITE};
    border: none;
    padding: 8px 18px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: #7aa3ff;
}}
QPushButton:pressed {{
    background-color: #3d6ee0;
}}
QPushButton[class="success"] {{
    background-color: {C.SUCCESS};
    color: #0a1f1a;
}}
QPushButton[class="success"]:hover  {{ background-color: #34e8bc; }}
QPushButton[class="danger"]  {{ background-color: {C.DANGER}; }}
QPushButton[class="danger"]:hover   {{ background-color: #ff7090; }}
QPushButton[class="warning"] {{ background-color: {C.WARNING}; color: #1a1400; }}
QPushButton[class="warning"]:hover  {{ background-color: #fcd34d; }}
QPushButton[class="accent2"] {{ background-color: {C.ACCENT2}; }}
QPushButton[class="accent2"]:hover  {{ background-color: #a78bfa; }}

/* ──────────────────────────────────────────────────────── */
/*  LineEdit / ComboBox / SpinBox                           */
/* ──────────────────────────────────────────────────────── */
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {C.CARD};
    border: 1px solid {C.BORDER};
    border-radius: 5px;
    padding: 6px 10px;
    font-size: 13px;
    color: {C.TEXT};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {C.ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {C.CARD};
    border: 1px solid {C.BORDER};
    selection-background-color: {C.ACCENT};
    color: {C.TEXT};
}}

/* ──────────────────────────────────────────────────────── */
/*  QTableWidget / QTreeWidget                              */
/* ──────────────────────────────────────────────────────── */
QTableWidget, QTreeWidget {{
    background-color: {C.CARD};
    border: 1px solid {C.BORDER};
    border-radius: 6px;
    gridline-color: {C.BORDER};
    color: {C.TEXT};
    alternate-background-color: {C.BG2};
}}
QTableWidget::item:selected, QTreeWidget::item:selected {{
    background-color: {C.ACCENT};
    color: {C.WHITE};
}}
QHeaderView::section {{
    background-color: {C.BG};
    color: {C.ACCENT};
    padding: 8px;
    border: none;
    border-bottom: 2px solid {C.ACCENT};
    font-weight: bold;
    font-size: 13px;
}}

/* ──────────────────────────────────────────────────────── */
/*  ScrollBars                                              */
/* ──────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {C.BG2};
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {C.BORDER};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {C.ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QScrollBar:horizontal {{
    background: {C.BG2};
    height: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {C.BORDER};
    border-radius: 5px;
    min-width: 30px;
}}

/* ──────────────────────────────────────────────────────── */
/*  Labels / GroupBox / Frame                               */
/* ──────────────────────────────────────────────────────── */
QLabel {{ background: transparent; }}
QGroupBox {{
    border: 1px solid {C.BORDER};
    border-radius: 8px;
    margin-top: 14px;
    padding: 10px;
    background: {C.BG2};
    font-weight: bold;
    font-size: 13px;
    color: {C.ACCENT2};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {C.BORDER};
}}

/* ──────────────────────────────────────────────────────── */
/*  MessageBox / Dialog                                     */
/* ──────────────────────────────────────────────────────── */
QMessageBox {{ background: {C.BG2}; }}

/* ──────────────────────────────────────────────────────── */
/*  Card widget helper                                      */
/* ──────────────────────────────────────────────────────── */
QFrame[class="card"] {{
    background-color: {C.CARD};
    border: 1px solid {C.BORDER};
    border-radius: 10px;
}}

/* Stats card */
QFrame[class="stat-card"] {{
    background-color: {C.BG2};
    border: 1px solid {C.BORDER};
    border-radius: 10px;
    padding: 10px;
}}
"""

def apply_app_style(app: QApplication):
    app.setStyleSheet(STYLESHEET)
    font = QFont("Segoe UI", 11)
    app.setFont(font)
