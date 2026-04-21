"""
社区物业与报修缴费综合管理系统
主窗口 - 左侧导航 + 右侧标签页
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QTabWidget, QLabel, QMessageBox,
    QStatusBar, QInputDialog
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QAction, QIcon

from auth_controller import Session, AuthController
from main_controller import MainController
from views.pages import (
    PropertyPage, OwnerPage, ParkingPage,
    BillPage, RepairPage, StaffPage
)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self, auth_controller: AuthController,
                 main_controller: MainController, parent=None):
        super().__init__(parent)
        self.auth_controller = auth_controller
        self.main_controller = main_controller
        self.session = Session()
        self.pages = {}
        self._init_ui()
        self._apply_role_permissions()
        self._refresh_all()

    def _init_ui(self):
        self.setWindowTitle("社区物业与报修缴费综合管理系统")
        self.setMinimumSize(1200, 750)
        self.resize(1300, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧导航栏
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("""
            QWidget#sidebar {
                background-color: #1d2129;
            }
        """)
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(2)

        # 导航标题
        nav_title = QLabel("  功能菜单")
        nav_title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        nav_title.setStyleSheet("color:#ffffff; padding:16px 12px 8px; background:transparent;")
        sidebar_layout.addWidget(nav_title)

        self.nav_buttons = []

        menu_items = [
            ("property", "楼栋与房产"),
            ("owners", "业主管理"),
            ("parking", "车位管理"),
            ("bills", "物业账单"),
            ("repairs", "报修工单"),
            ("staff", "维修员工"),
            ("monthly", "批量生成账单"),
            ("logout", "退出登录"),
        ]

        for key, text in menu_items:
            btn = QPushButton(f"  {text}")
            btn.setFixedHeight(44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("nav_key", key)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #c9cdd4; text-align: left;
                    border: none; font-size: 14px; padding-left: 20px;
                }
                QPushButton:hover { background: #2c3240; color: #ffffff; }
                QPushButton:checked { background: #4096ff; color: #ffffff; border-left: 3px solid #4096ff; }
            """)
            btn.clicked.connect(lambda checked, k=key: self._on_nav(k))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append((key, btn))

        sidebar_layout.addStretch()

        # 当前用户信息
        self.user_label = QLabel(f"  当前用户: {self.session.username}")
        self.user_label.setStyleSheet("color:#86909c; padding:12px; font-size:12px; background:transparent;")
        sidebar_layout.addWidget(self.user_label)

        main_layout.addWidget(self.sidebar)

        # 右侧内容区
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._on_tab_close)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e5e6eb; }
            QTabBar::tab {
                padding: 8px 20px; font-size: 13px;
                border: 1px solid #e5e6eb; border-bottom: none;
                background: #f7f8fa; color: #4e5969;
            }
            QTabBar::tab:selected { background: white; color: #4096ff; font-weight: bold; }
            QTabBar::tab:hover { background: #e8f3ff; }
        """)
        main_layout.addWidget(self.tabs)

        # 状态栏
        self.statusBar().showMessage("就绪")
        self.statusBar().setStyleSheet("color:#86909c; font-size:12px;")

        # 默认打开房产管理页
        self._open_tab("property")

    def _apply_role_permissions(self):
        """根据用户角色显示/隐藏菜单"""
        admin_only = {"property", "owners", "parking", "staff", "monthly"}
        if self.session.is_owner:
            for key, btn in self.nav_buttons:
                if key in admin_only:
                    btn.setVisible(False)

    def _on_nav(self, key):
        if key == "logout":
            self._on_logout()
            return
        if key == "monthly":
            self._generate_monthly_bills()
            return
        self._open_tab(key)

    def _open_tab(self, page_key):
        if page_key in self.pages:
            self.tabs.setCurrentWidget(self.pages[page_key])
            self._highlight_nav(page_key)
            return

        page_map = {
            "property": ("楼栋与房产", PropertyPage),
            "owners": ("业主管理", OwnerPage),
            "parking": ("车位管理", ParkingPage),
            "bills": ("物业账单", BillPage),
            "repairs": ("报修工单", RepairPage),
            "staff": ("维修员工", StaffPage),
        }

        if page_key not in page_map:
            return

        title, page_cls = page_map[page_key]
        page = page_cls(self.main_controller)
        page.refresh_requested.connect(lambda k=page_key: self._refresh_page(k))
        page.search_requested.connect(lambda text, k=page_key: self._search_page(k, text))
        self.pages[page_key] = page
        idx = self.tabs.addTab(page, title)
        self.tabs.setCurrentIndex(idx)
        self._highlight_nav(page_key)
        self._refresh_page(page_key)

    def _highlight_nav(self, key):
        for k, btn in self.nav_buttons:
            btn.setChecked(k == key)

    def _refresh_page(self, page_key):
        refresh_map = {
            "property": self.main_controller.get_properties,
            "owners": self.main_controller.get_owners,
            "parking": self.main_controller.get_parkings,
            "bills": self.main_controller.get_bills,
            "repairs": self.main_controller.get_repairs,
            "staff": self.main_controller.get_staff,
        }
        if page_key in refresh_map:
            result = refresh_map[page_key]()
            if result['success']:
                self.pages[page_key].load_data(result['data'])
                self.statusBar().showMessage(f"{result['message']} | 共 {len(result['data'])} 条记录")
            else:
                self.statusBar().showMessage(f"加载失败: {result['message']}")

    def _search_page(self, page_key, text):
        if not text:
            self._refresh_page(page_key)
            return
        search_map = {
            "bills": self.main_controller.dynamic_search_bills,
            "repairs": self.main_controller.dynamic_search_repairs,
        }
        if page_key in search_map:
            result = search_map[page_key](text)
            if result['success']:
                self.pages[page_key].load_data(result['data'])
                self.statusBar().showMessage(f"动态搜索完成 | 共 {len(result['data'])} 条记录")
            else:
                self.statusBar().showMessage(f"搜索失败: {result['message']}")
        else:
            self.statusBar().showMessage("当前页面不支持搜索功能")

    def _refresh_all(self):
        for key in list(self.pages.keys()):
            self._refresh_page(key)

    def _on_tab_close(self, index):
        widget = self.tabs.widget(index)
        if widget:
            for key, page in self.pages.items():
                if page is widget:
                    del self.pages[key]
                    break
        self.tabs.removeTab(index)

    def _generate_monthly_bills(self):
        month, ok = QInputDialog.getText(
            self, "批量生成物业费", "请输入目标月份 (YYYY-MM):",
            text="2026-04")
        if ok and month:
            result = self.main_controller.generate_monthly_bills(month)
            QMessageBox.information(self, "提示", result['message'])
            if "bills" in self.pages:
                self._refresh_page("bills")

    def _on_logout(self):
        reply = QMessageBox.question(
            self, "退出", "确定要退出登录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.auth_controller.logout()
            self.close()
