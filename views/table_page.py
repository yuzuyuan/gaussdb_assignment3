"""
社区物业与报修缴费综合管理系统
主窗口 (View Layer)
左侧导航 + 右侧标签页布局
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QDateEdit, QAbstractItemView, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from auth_controller import Session


class TablePage(QWidget):
    """通用表格页面，提供统一的增删改查界面"""

    refresh_requested = pyqtSignal()
    search_requested = pyqtSignal(str)

    def __init__(self, title, columns, controller, parent=None):
        super().__init__(parent)
        self.title = title
        self.columns = columns          # [(key, display_name), ...]
        self.controller = controller    # MainController
        self.data = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # 顶部：标题 + 操作按钮
        top_bar = QHBoxLayout()
        label = QLabel(self.title)
        label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        label.setStyleSheet("color: #1d2129;")
        top_bar.addWidget(label)
        top_bar.addStretch()

        self.add_btn = QPushButton("+ 新增")
        self.add_btn.setFixedHeight(34)
        self.add_btn.setStyleSheet("""
            QPushButton { background:#4096ff; color:white; border:none;
                          border-radius:4px; padding:0 16px; font-size:13px; }
            QPushButton:hover { background:#1677ff; }
        """)
        top_bar.addWidget(self.add_btn)

        self.search_input = QLineEdit()
        self.search_input.setFixedWidth(220)
        self.search_input.setFixedHeight(34)
        self.search_input.setPlaceholderText("输入搜索条件...")
        self.search_input.setStyleSheet("""
            QLineEdit { border:1px solid #e5e6eb; border-radius:4px;
                        padding:0 10px; font-size:13px; color:#1d2129; }
            QLineEdit:focus { border-color:#4096ff; }
        """)
        self.search_input.returnPressed.connect(self._on_search)
        top_bar.addWidget(self.search_input)

        self.search_btn = QPushButton("搜索")
        self.search_btn.setFixedHeight(34)
        self.search_btn.setStyleSheet("""
            QPushButton { background:#f2f3f5; color:#4e5969; border:1px solid #e5e6eb;
                          border-radius:4px; padding:0 16px; font-size:13px; }
            QPushButton:hover { background:#e5e6eb; }
        """)
        self.search_btn.clicked.connect(self._on_search)
        top_bar.addWidget(self.search_btn)

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedHeight(34)
        self.refresh_btn.setStyleSheet("""
            QPushButton { background:#f2f3f5; color:#4e5969; border:1px solid #e5e6eb;
                          border-radius:4px; padding:0 16px; font-size:13px; }
            QPushButton:hover { background:#e5e6eb; }
        """)
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        top_bar.addWidget(self.refresh_btn)
        layout.addLayout(top_bar)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels([c[1] for c in self.columns])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { gridline-color: #e5e6eb; font-size: 13px; }
            QTableWidget::item { padding: 6px; }
            QHeaderView::section {
                background: #f7f8fa; color: #4e5969; font-weight: bold;
                padding: 8px; border: none; border-bottom: 1px solid #e5e6eb;
            }
            QTableWidget::item:alternate { background: #fafafa; }
        """)

        header = self.table.horizontalHeader()
        for i in range(len(self.columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)

        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

    def _on_search(self):
        text = self.search_input.text().strip()
        self.search_requested.emit(text)

    def load_data(self, data):
        """加载数据到表格"""
        self.data = data
        self.table.setRowCount(len(data))
        for row_idx, row in enumerate(data):
            for col_idx, (key, _) in enumerate(self.columns):
                val = row.get(key, '')
                if val is None:
                    val = ''
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)

    def _on_double_click(self, index):
        """双击行弹出编辑对话框"""
        row = index.row()
        if row < 0 or row >= len(self.data):
            return
        self._show_edit_dialog(self.data[row])

    def _show_edit_dialog(self, row_data):
        """子类重写此方法实现自定义编辑对话框"""
        pass

    def _confirm_delete(self, delete_fn):
        """删除确认对话框"""
        reply = QMessageBox.warning(
            self, "确认删除", "确定要删除该记录吗？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            result = delete_fn()
            if result['success']:
                QMessageBox.information(self, "成功", result['message'])
                self.refresh_requested.emit()
            else:
                QMessageBox.warning(self, "失败", result['message'])
