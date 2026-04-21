"""
社区物业与报修缴费综合管理系统
应用入口 - 组装 MVC 各层
"""

import sys
import logging

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont

from db_manager import DatabaseManager, DBError
from auth_controller import AuthController
from main_controller import MainController
from views.login_window import LoginWindow
from views.main_window import MainWindow


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler('app.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei", 10))

    # 初始化数据库连接
    db = DatabaseManager(
        host='localhost',
        port=5432,
        dbname='property_db',
        user='gaussdb',
        password='gaussdb@123'
    )

    try:
        db.connect()
        logger.info("数据库连接成功")
    except DBError as e:
        QMessageBox.critical(
            None, "数据库连接失败",
            f"无法连接到数据库，请检查配置。\n\n错误信息：{e}\n\n"
            f"请在 main.py 中修改数据库连接参数。")
        sys.exit(1)

    # 初始化控制器
    auth_ctrl = AuthController(db)
    main_ctrl = MainController(db)

    # 显示登录窗口
    login_window = LoginWindow(auth_ctrl)
    main_win = None

    def on_login_success(user_data):
        nonlocal main_win
        login_window.close()
        main_win = MainWindow(auth_ctrl, main_ctrl)
        main_win.show()

    login_window.login_success.connect(on_login_success)
    login_window.show()

    exit_code = app.exec()

    # 清理资源
    db.close_all()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
