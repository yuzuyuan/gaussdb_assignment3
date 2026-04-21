"""
社区物业与报修缴费综合管理系统
业务逻辑控制层 (Controller Layer)
"""

import logging
from db_manager import (
    DatabaseManager, DBError,
    PropertyDAO, OwnerDAO, ParkingDAO,
    BillDAO, RepairOrderDAO, StaffDAO
)

logger = logging.getLogger(__name__)


class MainController:
    """核心业务控制器"""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.property_dao = PropertyDAO(db)
        self.owner_dao = OwnerDAO(db)
        self.parking_dao = ParkingDAO(db)
        self.bill_dao = BillDAO(db)
        self.repair_dao = RepairOrderDAO(db)
        self.staff_dao = StaffDAO(db)

    # ========== 房产管理 ==========

    def get_properties(self):
        try:
            data = self.property_dao.get_all()
            return {"success": True, "data": data, "message": "查询成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def get_property(self, property_id):
        try:
            data = self.property_dao.get_by_id(property_id)
            if not data:
                return {"success": False, "data": None, "message": "房产不存在"}
            return {"success": True, "data": data, "message": "查询成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def add_property(self, building_no, room_no, area, layout_type):
        if not all([building_no, room_no, area, layout_type]):
            return {"success": False, "data": None, "message": "请填写完整信息"}
        try:
            self.property_dao.insert(building_no, room_no, float(area), layout_type)
            return {"success": True, "data": None, "message": "房产添加成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def update_property(self, property_id, building_no, room_no, area, layout_type):
        try:
            affected = self.property_dao.update(
                property_id, building_no, room_no, float(area), layout_type)
            if affected == 0:
                return {"success": False, "data": None, "message": "房产不存在"}
            return {"success": True, "data": None, "message": "房产更新成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def delete_property(self, property_id):
        """删除房产（级联校验：检查是否有业主和未缴账单）"""
        try:
            owners = self.owner_dao.get_by_property(property_id)
            if owners:
                names = ', '.join([o['name'] for o in owners])
                return {"success": False, "data": None,
                        "message": f"无法删除：该房产下有业主（{names}），请先处理"}

            has_unpaid = self.bill_dao.has_unpaid_bills(property_id)
            if has_unpaid:
                return {"success": False, "data": None,
                        "message": "无法删除：该房产存在未缴清的账单"}

            affected = self.property_dao.delete(property_id)
            if affected == 0:
                return {"success": False, "data": None, "message": "房产不存在"}
            return {"success": True, "data": None, "message": "房产已删除"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def get_comprehensive_property_info(self):
        try:
            data = self.property_dao.get_comprehensive_info()
            return {"success": True, "data": data, "message": "查询成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    # ========== 业主管理 ==========

    def get_owners(self):
        try:
            data = self.owner_dao.get_all()
            return {"success": True, "data": data, "message": "查询成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def add_owner(self, name, phone, id_card, property_id, move_in_date, owner_type):
        if not all([name, phone, property_id, move_in_date]):
            return {"success": False, "data": None, "message": "请填写完整信息"}
        try:
            self.owner_dao.insert(name, phone, id_card, property_id, move_in_date, owner_type)
            return {"success": True, "data": None, "message": "业主添加成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def update_owner(self, owner_id, name, phone, id_card, property_id, move_in_date, owner_type):
        try:
            self.owner_dao.update(
                owner_id, name, phone, id_card, property_id, move_in_date, owner_type)
            return {"success": True, "data": None, "message": "业主信息更新成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def delete_owner(self, owner_id):
        try:
            affected = self.owner_dao.delete(owner_id)
            if affected == 0:
                return {"success": False, "data": None, "message": "业主不存在"}
            return {"success": True, "data": None, "message": "业主已删除"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    # ========== 车位管理 ==========

    def get_parkings(self):
        try:
            data = self.parking_dao.get_all()
            return {"success": True, "data": data, "message": "查询成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def add_parking(self, parking_no, property_id, status):
        if not parking_no:
            return {"success": False, "data": None, "message": "请填写车位编号"}
        try:
            self.parking_dao.insert(parking_no, property_id or None, status or '空闲')
            return {"success": True, "data": None, "message": "车位添加成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def update_parking(self, parking_id, parking_no, property_id, status):
        try:
            self.parking_dao.update(parking_id, parking_no, property_id, status)
            return {"success": True, "data": None, "message": "车位信息更新成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def delete_parking(self, parking_id):
        try:
            affected = self.parking_dao.delete(parking_id)
            if affected == 0:
                return {"success": False, "data": None, "message": "车位不存在"}
            return {"success": True, "data": None, "message": "车位已删除"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def get_available_parkings(self):
        try:
            data = self.parking_dao.get_available()
            return {"success": True, "data": data, "message": "查询成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    # ========== 账单管理 ==========

    def get_bills(self):
        try:
            data = self.bill_dao.get_all()
            return {"success": True, "data": data, "message": "查询成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def get_bills_by_property(self, property_id):
        try:
            data = self.bill_dao.get_by_property(property_id)
            return {"success": True, "data": data, "message": "查询成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def add_bill(self, property_id, bill_month, fee_type, amount, payment_status, due_date):
        if not all([property_id, bill_month, fee_type, amount]):
            return {"success": False, "data": None, "message": "请填写完整信息"}
        try:
            self.bill_dao.insert(
                property_id, bill_month, fee_type, float(amount),
                payment_status or '未缴费', due_date)
            return {"success": True, "data": None, "message": "账单添加成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def update_bill(self, bill_id, property_id, bill_month, fee_type, amount, payment_status, due_date):
        try:
            self.bill_dao.update(
                bill_id, property_id, bill_month, fee_type,
                float(amount), payment_status, due_date)
            return {"success": True, "data": None, "message": "账单更新成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def delete_bill(self, bill_id):
        try:
            affected = self.bill_dao.delete(bill_id)
            if affected == 0:
                return {"success": False, "data": None, "message": "账单不存在"}
            return {"success": True, "data": None, "message": "账单已删除"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def pay_bill(self, bill_id):
        try:
            affected = self.bill_dao.pay_bill(bill_id)
            if affected == 0:
                return {"success": False, "data": None, "message": "缴费失败：账单不存在或已缴费"}
            return {"success": True, "data": None, "message": "缴费成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def generate_monthly_bills(self, month):
        """调用存储过程批量生成月度物业费"""
        try:
            self.db.call_procedure('sp_generate_monthly_bills', (month,))
            return {"success": True, "data": None, "message": f"{month} 月物业费账单已批量生成"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def dynamic_search_bills(self, condition):
        try:
            data = self.bill_dao.dynamic_search(condition)
            return {"success": True, "data": data, "message": "查询成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    # ========== 报修工单管理 ==========

    def get_repairs(self):
        try:
            data = self.repair_dao.get_all()
            return {"success": True, "data": data, "message": "查询成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def get_repairs_by_property(self, property_id):
        try:
            data = self.repair_dao.get_by_property(property_id)
            return {"success": True, "data": data, "message": "查询成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def submit_repair(self, property_id, content, priority='普通'):
        if not all([property_id, content]):
            return {"success": False, "data": None, "message": "请填写报修内容"}
        try:
            self.repair_dao.insert(property_id, content, priority)
            return {"success": True, "data": None, "message": "报修工单已提交"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def update_repair_status(self, repair_id, status):
        valid = ['待处理', '处理中', '已完成']
        if status not in valid:
            return {"success": False, "data": None, "message": f"无效状态，有效值：{valid}"}
        try:
            self.repair_dao.update_status(repair_id, status)
            return {"success": True, "data": None, "message": f"工单状态已更新为：{status}"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def assign_repair_staff(self, repair_id, staff_id):
        if not staff_id:
            return {"success": False, "data": None, "message": "请选择维修员工"}
        try:
            self.repair_dao.assign_staff(repair_id, staff_id)
            return {"success": True, "data": None, "message": "员工已指派（接单量由触发器自动更新）"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def delete_repair(self, repair_id):
        try:
            affected = self.repair_dao.delete(repair_id)
            if affected == 0:
                return {"success": False, "data": None, "message": "工单不存在"}
            return {"success": True, "data": None, "message": "工单已删除"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def dynamic_search_repairs(self, condition):
        try:
            data = self.repair_dao.dynamic_search(condition)
            return {"success": True, "data": data, "message": "查询成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    # ========== 维修员工管理 ==========

    def get_staff(self):
        try:
            data = self.staff_dao.get_all()
            return {"success": True, "data": data, "message": "查询成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def add_staff(self, name, specialty, phone):
        if not all([name, specialty]):
            return {"success": False, "data": None, "message": "请填写完整信息"}
        try:
            self.staff_dao.insert(name, specialty, phone)
            return {"success": True, "data": None, "message": "员工添加成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def update_staff(self, staff_id, name, specialty, phone):
        try:
            self.staff_dao.update(staff_id, name, specialty, phone)
            return {"success": True, "data": None, "message": "员工信息更新成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def delete_staff(self, staff_id):
        try:
            affected = self.staff_dao.delete(staff_id)
            if affected == 0:
                return {"success": False, "data": None, "message": "员工不存在"}
            return {"success": True, "data": None, "message": "员工已删除"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    def get_staff_workload_stats(self):
        try:
            data = self.staff_dao.get_workload_stats()
            return {"success": True, "data": data, "message": "查询成功"}
        except DBError as e:
            return {"success": False, "data": None, "message": str(e)}

    # ========== 获取所有选项数据（下拉框等） ==========

    def get_property_options(self):
        """获取房产列表供下拉框选择"""
        try:
            data = self.db.execute_query(
                "SELECT property_id, building_no || ' ' || room_no AS label "
                "FROM properties ORDER BY building_no, room_no")
            return data
        except DBError:
            return []

    def get_staff_options(self):
        """获取员工列表供下拉框选择"""
        try:
            data = self.db.execute_query(
                "SELECT staff_id, name || ' (' || specialty || ')' AS label "
                "FROM staff ORDER BY staff_id")
            return data
        except DBError:
            return []
