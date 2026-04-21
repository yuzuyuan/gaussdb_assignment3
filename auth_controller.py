"""
社区物业与报修缴费综合管理系统
认证与权限控制层 (Controller Layer)
"""

import logging
from enum import Enum
from db_manager import DatabaseManager, DBError

logger = logging.getLogger(__name__)


class Role(Enum):
    ADMIN = "ADMIN"
    OWNER = "OWNER"


class Session:
    """当前登录会话（单例）"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._user = None
        return cls._instance

    def login(self, user):
        self._user = user

    def logout(self):
        self._user = None

    @property
    def is_logged_in(self):
        return self._user is not None

    @property
    def current_user(self):
        return self._user

    @property
    def role(self):
        return self._user['role'] if self._user else None

    @property
    def username(self):
        return self._user['username'] if self._user else None

    @property
    def owner_id(self):
        return self._user.get('owner_id') if self._user else None

    @property
    def is_admin(self):
        return self.role == Role.ADMIN.value

    @property
    def is_owner(self):
        return self.role == Role.OWNER.value


class AuthController:
    """认证控制器"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def login(self, username, password):
        """验证登录凭据"""
        try:
            rows = self.db.execute_query(
                "SELECT user_id, username, role, owner_id, is_active "
                "FROM users WHERE username = %s AND password = %s",
                (username, password))
            if not rows:
                return {"success": False, "data": None, "message": "用户名或密码错误"}
            user = rows[0]
            if not user['is_active']:
                return {"success": False, "data": None, "message": "账户已被禁用"}
            Session().login(user)
            role_text = "管理员" if user['role'] == 'ADMIN' else "业主"
            return {"success": True, "data": user, "message": f"欢迎，{role_text} {user['username']}"}
        except DBError as e:
            return {"success": False, "data": None, "message": f"登录失败: {e}"}

    def logout(self):
        Session().logout()
        return {"success": True, "data": None, "message": "已退出登录"}

    def get_current_session(self):
        session = Session()
        if not session.is_logged_in:
            return None
        return session.current_user

    def check_permission(self, required_role=None):
        """检查当前用户是否有权限"""
        session = Session()
        if not session.is_logged_in:
            return {"success": False, "message": "请先登录"}
        if required_role and session.role != required_role:
            return {"success": False, "message": "权限不足"}
        return {"success": True, "message": "权限验证通过"}

    def change_password(self, username, old_password, new_password):
        """修改密码"""
        try:
            rows = self.db.execute_query(
                "SELECT user_id FROM users WHERE username = %s AND password = %s",
                (username, old_password))
            if not rows:
                return {"success": False, "data": None, "message": "原密码错误"}
            self.db.execute_commit(
                "UPDATE users SET password = %s WHERE username = %s",
                (new_password, username))
            return {"success": True, "data": None, "message": "密码修改成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": f"修改失败: {e}"}
