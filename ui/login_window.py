"""login_window.py — نافذة تسجيل الدخول (PyQt6)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QFrame, QApplication)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from theme_qt import QT, btn_style


class LoginWindow(QDialog):
    def __init__(self, on_success=None):
        super().__init__()
        self.on_success = on_success
        self.setWindowTitle("تسجيل الدخول - مكتبة الفراشات")
        self.setFixedSize(450, 500)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(f"background-color: {QT.BG}; color: {QT.TEXT};")
        self._build_ui()
        self._center()

    def _center(self):
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2,
                  (screen.height() - self.height()) // 2)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        # بطاقة رئيسية
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {QT.CARD};
                border-radius: 12px;
                border: 1px solid #2c3e50;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(30, 25, 30, 25)

        # أيقونة وعنوان
        emoji_lbl = QLabel("🦋")
        emoji_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_lbl.setFont(QFont("Arial", 48))
        card_layout.addWidget(emoji_lbl)

        welcome = QLabel("مرحباً بك في")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        welcome.setStyleSheet(f"color: {QT.TEXT};")
        card_layout.addWidget(welcome)

        title = QLabel("مكتبة الفراشات")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {QT.ACCENT2};")
        card_layout.addWidget(title)

        subtitle = QLabel("نظام البيع وإدارة المخزون")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setStyleSheet(f"color: {QT.TEXT_SUB};")
        card_layout.addWidget(subtitle)

        # فاصل
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: #2c3e50;")
        card_layout.addWidget(line)

        # اسم المستخدم
        user_lbl = QLabel("👤 اسم المستخدم:")
        user_lbl.setFont(QFont("Arial", 12))
        card_layout.addWidget(user_lbl)

        self.username_entry = QLineEdit()
        self.username_entry.setPlaceholderText("أدخل اسم المستخدم")
        self.username_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.username_entry.setFixedHeight(40)
        self.username_entry.setFont(QFont("Arial", 13))
        self.username_entry.setText("admin")
        card_layout.addWidget(self.username_entry)

        # كلمة المرور
        pass_lbl = QLabel("🔒 كلمة المرور:")
        pass_lbl.setFont(QFont("Arial", 12))
        card_layout.addWidget(pass_lbl)

        self.password_entry = QLineEdit()
        self.password_entry.setPlaceholderText("أدخل كلمة المرور")
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.password_entry.setFixedHeight(40)
        self.password_entry.setFont(QFont("Arial", 13))
        card_layout.addWidget(self.password_entry)

        # رسالة الخطأ
        self.error_lbl = QLabel("")
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_lbl.setStyleSheet(f"color: {QT.DANGER};")
        self.error_lbl.setFont(QFont("Arial", 10))
        card_layout.addWidget(self.error_lbl)

        # زر الدخول
        login_btn = QPushButton("🚪 دخول")
        login_btn.setFixedHeight(44)
        login_btn.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        login_btn.setStyleSheet(btn_style(QT.ACCENT2))
        login_btn.clicked.connect(self.check_login)
        card_layout.addWidget(login_btn)

        # تلميح
        hint = QLabel("🔑 admin / 1234")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setFont(QFont("Arial", 10))
        hint.setStyleSheet(f"color: {QT.TEXT_DIM};")
        card_layout.addWidget(hint)

        layout.addWidget(card)

        # ربط Enter
        self.username_entry.returnPressed.connect(self.password_entry.setFocus)
        self.password_entry.returnPressed.connect(self.check_login)
        self.username_entry.setFocus()

    def check_login(self):
        username = self.username_entry.text().strip()
        password = self.password_entry.text().strip()

        USERS = {
            "admin": "1234",
            "مدير": "1234",
            "user": "0000",
        }

        if USERS.get(username) == password:
            self.accept()
            if self.on_success:
                self.on_success()
        else:
            self.error_lbl.setText("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
            self.password_entry.clear()
            self.password_entry.setFocus()
