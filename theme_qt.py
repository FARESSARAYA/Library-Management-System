"""theme_qt.py — ثيم PyQt6 لمكتبة الفراشات"""

# ألوان التطبيق
class QT:
    BG      = "#1a1a2e"
    BG2     = "#16213e"
    BG3     = "#0f3460"
    CARD    = "#1e2a45"
    ACCENT  = "#e94560"
    ACCENT2 = "#9b59b6"
    SUCCESS = "#27ae60"
    WARNING = "#f39c12"
    DANGER  = "#e74c3c"
    WHITE   = "#ffffff"
    TEXT    = "#ecf0f1"
    TEXT_SUB = "#bdc3c7"
    TEXT_DIM = "#7f8c8d"

MAIN_STYLE = f"""
QMainWindow, QDialog, QWidget {{
    background-color: {QT.BG};
    color: {QT.TEXT};
    font-family: Arial;
}}

QTabWidget::pane {{
    border: 1px solid #2c3e50;
    background: {QT.BG};
}}

QTabBar::tab {{
    background: {QT.BG3};
    color: {QT.TEXT_SUB};
    padding: 8px 18px;
    margin: 2px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
}}

QTabBar::tab:selected {{
    background: {QT.ACCENT2};
    color: {QT.WHITE};
}}

QTabBar::tab:hover {{
    background: #1a4a8a;
    color: {QT.WHITE};
}}

QTreeWidget, QTableWidget {{
    background-color: {QT.CARD};
    color: {QT.TEXT};
    border: 1px solid #2c3e50;
    gridline-color: #2c3e50;
    alternate-background-color: #1a2a3a;
    selection-background-color: {QT.ACCENT2};
    selection-color: {QT.WHITE};
    font-size: 11px;
}}

QTreeWidget::item, QTableWidget::item {{
    padding: 6px;
}}

QTreeWidget::item:hover, QTableWidget::item:hover {{
    background-color: #2a3a5a;
}}

QHeaderView::section {{
    background-color: {QT.BG3};
    color: {QT.TEXT};
    padding: 8px;
    border: 1px solid #2c3e50;
    font-weight: bold;
    font-size: 11px;
}}

QPushButton {{
    padding: 8px 16px;
    border-radius: 5px;
    font-weight: bold;
    font-size: 10px;
    border: none;
    cursor: pointer;
    color: {QT.WHITE};
    background-color: {QT.BG3};
}}

QPushButton:hover {{
    opacity: 0.85;
    filter: brightness(1.1);
}}

QPushButton:pressed {{
    filter: brightness(0.9);
}}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: #2a3a5a;
    color: {QT.TEXT};
    border: 1px solid #4a5a7a;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}}

QLineEdit:focus, QComboBox:focus {{
    border: 2px solid {QT.ACCENT2};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {QT.CARD};
    color: {QT.TEXT};
    selection-background-color: {QT.ACCENT2};
}}

QScrollBar:vertical {{
    background: {QT.BG2};
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background: {QT.BG3};
    border-radius: 5px;
    min-height: 20px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QLabel {{
    color: {QT.TEXT};
}}

QGroupBox {{
    border: 1px solid #4a5a7a;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
    color: {QT.TEXT};
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: {QT.ACCENT2};
}}

QMessageBox {{
    background-color: {QT.CARD};
    color: {QT.TEXT};
}}

QSplitter::handle {{
    background: #2c3e50;
}}

QMenuBar {{
    background-color: {QT.BG3};
    color: {QT.WHITE};
}}

QMenuBar::item:selected {{
    background-color: {QT.ACCENT2};
}}

QMenu {{
    background-color: {QT.CARD};
    color: {QT.TEXT};
    border: 1px solid #4a5a7a;
}}

QMenu::item:selected {{
    background-color: {QT.ACCENT2};
}}

QStatusBar {{
    background-color: {QT.BG3};
    color: {QT.TEXT_SUB};
}}

QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: #2c3e50;
}}
"""

def btn_style(color):
    """إنشاء ستايل زر بلون معيّن"""
    return f"""
    QPushButton {{
        background-color: {color};
        color: white;
        border-radius: 5px;
        padding: 7px 14px;
        font-weight: bold;
        font-size: 10px;
        border: none;
    }}
    QPushButton:hover {{
        background-color: {color}cc;
    }}
    QPushButton:pressed {{
        background-color: {color}99;
    }}
    """

def card_style():
    return f"background-color: {QT.CARD}; border-radius: 8px; padding: 10px;"
