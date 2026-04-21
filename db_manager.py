"""
社区物业与报修缴费综合管理系统
数据库访问层 (Model Layer)
使用 psycopg2 连接 GaussDB / PostgreSQL
"""

import logging
import psycopg2
from psycopg2 import pool

logger = logging.getLogger(__name__)


class DBError(Exception):
    """数据库操作自定义异常"""
    pass


class DatabaseManager:
    """数据库连接管理器（单例模式）"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, host='localhost', port=5432, dbname='property_db',
                 user='gaussdb', password='gaussdb@123'):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._host = host
        self._port = port
        self._dbname = dbname
        self._user = user
        self._password = password
        self._pool = None
        self._initialized = True

    def connect(self):
        """初始化连接池"""
        try:
            self._pool = pool.SimpleConnectionPool(
                minconn=1, maxconn=10,
                host=self._host, port=self._port,
                dbname=self._dbname,
                user=self._user, password=self._password
            )
            logger.info("数据库连接池初始化成功")
        except psycopg2.DatabaseError as e:
            logger.error("数据库连接失败: %s", e)
            raise DBError(f"数据库连接失败: {e}")

    def get_connection(self):
        """从连接池获取连接"""
        if self._pool is None:
            self.connect()
        return self._pool.getconn()

    def return_connection(self, conn):
        """归还连接到连接池"""
        if self._pool and conn:
            self._pool.putconn(conn)

    def close_all(self):
        """关闭所有连接"""
        if self._pool:
            self._pool.closeall()
            logger.info("数据库连接池已关闭")

    def execute_query(self, sql, params=None):
        """执行查询，返回字典列表"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(sql, params)
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = cur.fetchall()
                result = [dict(zip(columns, row)) for row in rows]
                return result
        except psycopg2.DatabaseError as e:
            logger.error("查询执行失败: %s | SQL: %s", e, sql)
            raise DBError(f"查询失败: {e}")
        finally:
            if conn:
                self.return_connection(conn)

    def execute_commit(self, sql, params=None):
        """执行增删改，返回受影响行数"""
        conn = None
        try:
            conn = self.get_connection()
            conn.autocommit = False
            with conn.cursor() as cur:
                cur.execute(sql, params)
                affected = cur.rowcount
                conn.commit()
                return affected
        except psycopg2.DatabaseError as e:
            if conn:
                conn.rollback()
            logger.error("事务执行失败: %s | SQL: %s", e, sql)
            raise DBError(f"操作失败: {e}")
        finally:
            if conn:
                self.return_connection(conn)

    def execute_many(self, sql, params_list):
        """批量执行，返回受影响总行数"""
        conn = None
        try:
            conn = self.get_connection()
            conn.autocommit = False
            with conn.cursor() as cur:
                cur.executemany(sql, params_list)
                affected = cur.rowcount
                conn.commit()
                return affected
        except psycopg2.DatabaseError as e:
            if conn:
                conn.rollback()
            logger.error("批量执行失败: %s", e)
            raise DBError(f"批量操作失败: {e}")
        finally:
            if conn:
                self.return_connection(conn)

    def call_procedure(self, proc_name, params=None):
        """调用存储过程"""
        if params:
            sql = f"CALL {proc_name}(%s)"
        else:
            sql = f"CALL {proc_name}()"
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(sql, params)
                conn.commit()
                logger.info("存储过程 %s 调用成功", proc_name)
        except psycopg2.DatabaseError as e:
            logger.error("存储过程调用失败: %s", e)
            raise DBError(f"存储过程调用失败: {e}")
        finally:
            if conn:
                self.return_connection(conn)


class PropertyDAO:
    """房产数据访问对象"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self):
        return self.db.execute_query(
            "SELECT * FROM properties ORDER BY building_no, room_no")

    def get_by_id(self, property_id):
        rows = self.db.execute_query(
            "SELECT * FROM properties WHERE property_id = %s", (property_id,))
        return rows[0] if rows else None

    def insert(self, building_no, room_no, area, layout_type):
        affected = self.db.execute_commit(
            "INSERT INTO properties (building_no, room_no, area, layout_type) VALUES (%s, %s, %s, %s)",
            (building_no, room_no, area, layout_type))
        return affected

    def update(self, property_id, building_no, room_no, area, layout_type):
        return self.db.execute_commit(
            "UPDATE properties SET building_no=%s, room_no=%s, area=%s, layout_type=%s WHERE property_id=%s",
            (building_no, room_no, area, layout_type, property_id))

    def delete(self, property_id):
        return self.db.execute_commit(
            "DELETE FROM properties WHERE property_id = %s", (property_id,))

    def get_comprehensive_info(self):
        return self.db.execute_query("SELECT * FROM v_comprehensive_property_info")


class OwnerDAO:
    """业主数据访问对象"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self):
        return self.db.execute_query(
            "SELECT o.*, p.building_no || p.room_no AS property_address "
            "FROM owners o JOIN properties p ON o.property_id = p.property_id "
            "ORDER BY o.owner_id")

    def get_by_id(self, owner_id):
        rows = self.db.execute_query(
            "SELECT o.*, p.building_no || p.room_no AS property_address "
            "FROM owners o JOIN properties p ON o.property_id = p.property_id "
            "WHERE o.owner_id = %s", (owner_id,))
        return rows[0] if rows else None

    def get_by_property(self, property_id):
        return self.db.execute_query(
            "SELECT * FROM owners WHERE property_id = %s", (property_id,))

    def insert(self, name, phone, id_card, property_id, move_in_date, owner_type):
        return self.db.execute_commit(
            "INSERT INTO owners (name, phone, id_card, property_id, move_in_date, owner_type) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (name, phone, id_card, property_id, move_in_date, owner_type))

    def update(self, owner_id, name, phone, id_card, property_id, move_in_date, owner_type):
        return self.db.execute_commit(
            "UPDATE owners SET name=%s, phone=%s, id_card=%s, property_id=%s, "
            "move_in_date=%s, owner_type=%s WHERE owner_id=%s",
            (name, phone, id_card, property_id, move_in_date, owner_type, owner_id))

    def delete(self, owner_id):
        return self.db.execute_commit(
            "DELETE FROM owners WHERE owner_id = %s", (owner_id,))


class ParkingDAO:
    """车位数据访问对象"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self):
        return self.db.execute_query(
            "SELECT ps.*, p.building_no || p.room_no AS property_address "
            "FROM parking_spaces ps LEFT JOIN properties p ON ps.property_id = p.property_id "
            "ORDER BY ps.parking_no")

    def get_by_id(self, parking_id):
        rows = self.db.execute_query(
            "SELECT * FROM parking_spaces WHERE parking_id = %s", (parking_id,))
        return rows[0] if rows else None

    def insert(self, parking_no, property_id, status):
        return self.db.execute_commit(
            "INSERT INTO parking_spaces (parking_no, property_id, status) VALUES (%s, %s, %s)",
            (parking_no, property_id, status))

    def update(self, parking_id, parking_no, property_id, status):
        return self.db.execute_commit(
            "UPDATE parking_spaces SET parking_no=%s, property_id=%s, status=%s WHERE parking_id=%s",
            (parking_no, property_id, status, parking_id))

    def delete(self, parking_id):
        return self.db.execute_commit(
            "DELETE FROM parking_spaces WHERE parking_id = %s", (parking_id,))

    def get_available(self):
        return self.db.execute_query(
            "SELECT * FROM parking_spaces WHERE status = '空闲' ORDER BY parking_no")


class BillDAO:
    """账单数据访问对象"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self):
        return self.db.execute_query(
            "SELECT b.*, p.building_no || p.room_no AS property_address "
            "FROM bills b JOIN properties p ON b.property_id = p.property_id "
            "ORDER BY b.bill_month DESC, p.building_no, p.room_no")

    def get_by_id(self, bill_id):
        rows = self.db.execute_query(
            "SELECT b.*, p.building_no || p.room_no AS property_address "
            "FROM bills b JOIN properties p ON b.property_id = p.property_id "
            "WHERE b.bill_id = %s", (bill_id,))
        return rows[0] if rows else None

    def get_by_property(self, property_id):
        return self.db.execute_query(
            "SELECT b.*, p.building_no || p.room_no AS property_address "
            "FROM bills b JOIN properties p ON b.property_id = p.property_id "
            "WHERE b.property_id = %s ORDER BY b.bill_month DESC", (property_id,))

    def insert(self, property_id, bill_month, fee_type, amount, payment_status, due_date):
        return self.db.execute_commit(
            "INSERT INTO bills (property_id, bill_month, fee_type, amount, payment_status, due_date) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (property_id, bill_month, fee_type, amount, payment_status, due_date))

    def update(self, bill_id, property_id, bill_month, fee_type, amount, payment_status, due_date):
        return self.db.execute_commit(
            "UPDATE bills SET property_id=%s, bill_month=%s, fee_type=%s, amount=%s, "
            "payment_status=%s, due_date=%s WHERE bill_id=%s",
            (property_id, bill_month, fee_type, amount, payment_status, due_date, bill_id))

    def delete(self, bill_id):
        return self.db.execute_commit(
            "DELETE FROM bills WHERE bill_id = %s", (bill_id,))

    def pay_bill(self, bill_id):
        """缴费"""
        return self.db.execute_commit(
            "UPDATE bills SET payment_status='已缴费' WHERE bill_id=%s AND payment_status='未缴费'",
            (bill_id,))

    def get_unpaid_by_property(self, property_id):
        """获取指定房产的未缴账单"""
        return self.db.execute_query(
            "SELECT * FROM bills WHERE property_id=%s AND payment_status='未缴费'",
            (property_id,))

    def has_unpaid_bills(self, property_id):
        """检查房产是否有未缴账单"""
        rows = self.db.execute_query(
            "SELECT COUNT(*) AS cnt FROM bills WHERE property_id=%s AND payment_status='未缴费'",
            (property_id,))
        return rows[0]['cnt'] > 0 if rows else False

    def dynamic_search(self, condition):
        """动态SQL查询账单"""
        return self.db.execute_query(
            "SELECT * FROM func_dynamic_search_bills(%s)", (condition,))


class RepairOrderDAO:
    """报修工单数据访问对象"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self):
        return self.db.execute_query(
            "SELECT ro.*, p.building_no || p.room_no AS property_address, "
            "s.name AS staff_name "
            "FROM repair_orders ro "
            "JOIN properties p ON ro.property_id = p.property_id "
            "LEFT JOIN staff s ON ro.staff_id = s.staff_id "
            "ORDER BY ro.created_at DESC")

    def get_by_id(self, repair_id):
        rows = self.db.execute_query(
            "SELECT ro.*, p.building_no || p.room_no AS property_address, "
            "s.name AS staff_name "
            "FROM repair_orders ro "
            "JOIN properties p ON ro.property_id = p.property_id "
            "LEFT JOIN staff s ON ro.staff_id = s.staff_id "
            "WHERE ro.repair_id = %s", (repair_id,))
        return rows[0] if rows else None

    def get_by_property(self, property_id):
        return self.db.execute_query(
            "SELECT ro.*, s.name AS staff_name "
            "FROM repair_orders ro "
            "LEFT JOIN staff s ON ro.staff_id = s.staff_id "
            "WHERE ro.property_id = %s ORDER BY ro.created_at DESC", (property_id,))

    def insert(self, property_id, content, priority='普通'):
        return self.db.execute_commit(
            "INSERT INTO repair_orders (property_id, content, priority) VALUES (%s, %s, %s)",
            (property_id, content, priority))

    def update_status(self, repair_id, status):
        return self.db.execute_commit(
            "UPDATE repair_orders SET status=%s WHERE repair_id=%s", (status, repair_id))

    def assign_staff(self, repair_id, staff_id):
        return self.db.execute_commit(
            "UPDATE repair_orders SET staff_id=%s WHERE repair_id=%s",
            (staff_id, repair_id))

    def delete(self, repair_id):
        return self.db.execute_commit(
            "DELETE FROM repair_orders WHERE repair_id = %s", (repair_id,))

    def dynamic_search(self, condition):
        return self.db.execute_query(
            "SELECT * FROM func_dynamic_search_repairs(%s)", (condition,))


class StaffDAO:
    """维修员工数据访问对象"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self):
        return self.db.execute_query("SELECT * FROM staff ORDER BY staff_id")

    def get_by_id(self, staff_id):
        rows = self.db.execute_query(
            "SELECT * FROM staff WHERE staff_id = %s", (staff_id,))
        return rows[0] if rows else None

    def insert(self, name, specialty, phone):
        return self.db.execute_commit(
            "INSERT INTO staff (name, specialty, phone) VALUES (%s, %s, %s)",
            (name, specialty, phone))

    def update(self, staff_id, name, specialty, phone):
        return self.db.execute_commit(
            "UPDATE staff SET name=%s, specialty=%s, phone=%s WHERE staff_id=%s",
            (name, specialty, phone, staff_id))

    def delete(self, staff_id):
        return self.db.execute_commit(
            "DELETE FROM staff WHERE staff_id = %s", (staff_id,))

    def get_workload_stats(self):
        return self.db.execute_query("SELECT * FROM v_staff_workload_stats")

    def get_staff_workload_detail(self, staff_id):
        return self.db.execute_query(
            "SELECT * FROM func_staff_workload_detail(%s)", (staff_id,))
