"""
社区物业与报修缴费综合管理系统
登录窗口 (View Layer)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QMessageBox, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIntValidator


class LoginWindow(QWidget):
    """登录界面"""

    login_success = pyqtSignal(dict)

    def __init__(self, auth_controller, parent=None):
        super().__init__(parent)
        self.auth_controller = auth_controller
        self.setFixedSize(420, 320)
        self.setWindowTitle("社区物业管理系统 - 登录")
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QWidget { background-color: #f0f2f5; }
            QLabel { color: #333; }
            QLineEdit, QComboBox {
                padding: 8px 12px;
                border: 1px solid #d0d5dd;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #4096ff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(12)

        # 标题
        title = QLabel("社区物业管理系统")
        title.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #1d2129; margin-bottom: 10px;")
        layout.addWidget(title)

        # 用户名
        layout.addWidget(QLabel("用户名"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        layout.addWidget(self.username_input)

        # 密码
        layout.addWidget(QLabel("密码"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # 登录按钮
        login_btn = QPushButton("登 录")
        login_btn.setFixedHeight(42)
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4096ff;
                color: white;
                font-size: 15px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #1677ff; }
            QPushButton:pressed { background-color: #0958d9; }
        """)
        login_btn.clicked.connect(self._on_login)
        layout.addWidget(login_btn)

        # 提示
        hint = QLabel("管理员: admin / admin123 | 业主: zhangsan / 123456")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #86909c; font-size: 11px; margin-top: 6px;")
        layout.addWidget(hint)

        self.password_input.returnPressed.connect(login_btn.click)

    def _on_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "提示", "请输入用户名和密码")
            return
        result = self.auth_controller.login(username, password)
        if result['success']:
            self.login_success.emit(result['data'])
        else:
            QMessageBox.warning(self, "登录失败", result['message'])
