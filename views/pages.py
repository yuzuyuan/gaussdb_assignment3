"""
社区物业与报修缴费综合管理系统
各业务模块的表格页面实现
"""

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QDateEdit, QMessageBox, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt, QDate

from views.table_page import TablePage
from auth_controller import Session


class PropertyPage(TablePage):
    """房产管理页面"""

    def __init__(self, controller, parent=None):
        super().__init__("楼栋与房产管理", [
            ('property_id', 'ID'), ('building_no', '楼栋号'), ('room_no', '房间号'),
            ('area', '面积(㎡)'), ('layout_type', '户型'),
            ('create_time', '创建时间')
        ], controller, parent)
        self.add_btn.clicked.connect(lambda: self._show_edit_dialog(None))

    def _show_edit_dialog(self, row_data):
        dlg = QDialog(self)
        dlg.setWindowTitle("编辑房产" if row_data else "新增房产")
        dlg.setFixedSize(350, 280)
        form = QFormLayout(dlg)

        building_input = QLineEdit(row_data['building_no'] if row_data else '')
        room_input = QLineEdit(row_data['room_no'] if row_data else '')
        area_input = QLineEdit(str(row_data['area']) if row_data else '')
        layout_combo = QComboBox()
        layout_combo.addItems(['两室一厅', '三室一厅', '三室两厅', '四室两厅', '一室一厅', '复式四室'])
        if row_data:
            idx = layout_combo.findText(row_data['layout_type'])
            if idx >= 0:
                layout_combo.setCurrentIndex(idx)

        form.addRow("楼栋号:", building_input)
        form.addRow("房间号:", room_input)
        form.addRow("面积(㎡):", area_input)
        form.addRow("户型:", layout_combo)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        form.addRow(btn_layout)

        def on_ok():
            b, r, a, lt = building_input.text(), room_input.text(), area_input.text(), layout_combo.currentText()
            if not all([b, r, a]):
                QMessageBox.warning(dlg, "提示", "请填写完整信息")
                return
            if row_data:
                result = self.controller.update_property(row_data['property_id'], b, r, a, lt)
            else:
                result = self.controller.add_property(b, r, a, lt)
            if result['success']:
                dlg.accept()
                self.refresh_requested.emit()
            else:
                QMessageBox.warning(dlg, "失败", result['message'])

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dlg.reject)
        dlg.exec()


class OwnerPage(TablePage):
    """业主管理页面"""

    def __init__(self, controller, parent=None):
        super().__init__("业主/住户管理", [
            ('owner_id', 'ID'), ('name', '姓名'), ('phone', '联系方式'),
            ('id_card', '身份证号'), ('property_address', '房产地址'),
            ('move_in_date', '入住日期'), ('owner_type', '类型')
        ], controller, parent)
        self.add_btn.clicked.connect(lambda: self._show_edit_dialog(None))

    def _show_edit_dialog(self, row_data):
        dlg = QDialog(self)
        dlg.setWindowTitle("编辑业主" if row_data else "新增业主")
        dlg.setFixedSize(400, 350)
        form = QFormLayout(dlg)

        name_input = QLineEdit(row_data['name'] if row_data else '')
        phone_input = QLineEdit(row_data['phone'] if row_data else '')
        id_card_input = QLineEdit(row_data.get('id_card', '') or '')
        property_combo = QComboBox()
        for p in self.controller.get_property_options():
            property_combo.addItem(p['label'], p['property_id'])
        if row_data and row_data.get('property_id'):
            idx = property_combo.findData(row_data['property_id'])
            if idx >= 0:
                property_combo.setCurrentIndex(idx)
        move_in_edit = QDateEdit(QDate.currentDate())
        move_in_edit.setCalendarPopup(True)
        move_in_edit.setDisplayFormat("yyyy-MM-dd")
        if row_data:
            d = QDate.fromString(row_data['move_in_date'], Qt.DateFormat.ISODate)
            if d.isValid():
                move_in_edit.setDate(d)
        type_combo = QComboBox()
        type_combo.addItems(['业主', '租户'])
        if row_data:
            idx = type_combo.findText(row_data.get('owner_type', '业主'))
            if idx >= 0:
                type_combo.setCurrentIndex(idx)

        form.addRow("姓名:", name_input)
        form.addRow("联系方式:", phone_input)
        form.addRow("身份证号:", id_card_input)
        form.addRow("关联房产:", property_combo)
        form.addRow("入住日期:", move_in_edit)
        form.addRow("类型:", type_combo)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        form.addRow(btn_layout)

        def on_ok():
            n, ph, ic = name_input.text(), phone_input.text(), id_card_input.text()
            pid = property_combo.currentData()
            mid = move_in_edit.date().toString(Qt.DateFormat.ISODate)
            ot = type_combo.currentText()
            if not all([n, ph, pid]):
                QMessageBox.warning(dlg, "提示", "请填写完整信息")
                return
            if row_data:
                result = self.controller.update_owner(row_data['owner_id'], n, ph, ic, pid, mid, ot)
            else:
                result = self.controller.add_owner(n, ph, ic, pid, mid, ot)
            if result['success']:
                dlg.accept()
                self.refresh_requested.emit()
            else:
                QMessageBox.warning(dlg, "失败", result['message'])

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dlg.reject)
        dlg.exec()


class ParkingPage(TablePage):
    """车位管理页面"""

    def __init__(self, controller, parent=None):
        super().__init__("车位管理", [
            ('parking_id', 'ID'), ('parking_no', '车位号'),
            ('property_address', '关联房产'), ('status', '状态')
        ], controller, parent)
        self.add_btn.clicked.connect(lambda: self._show_edit_dialog(None))

    def _show_edit_dialog(self, row_data):
        dlg = QDialog(self)
        dlg.setWindowTitle("编辑车位" if row_data else "新增车位")
        dlg.setFixedSize(350, 240)
        form = QFormLayout(dlg)

        no_input = QLineEdit(row_data['parking_no'] if row_data else '')
        property_combo = QComboBox()
        property_combo.addItem("-- 不绑定 --", None)
        for p in self.controller.get_property_options():
            property_combo.addItem(p['label'], p['property_id'])
        if row_data and row_data.get('property_id'):
            idx = property_combo.findData(row_data['property_id'])
            if idx >= 0:
                property_combo.setCurrentIndex(idx)
        status_combo = QComboBox()
        status_combo.addItems(['空闲', '已租', '已售'])
        if row_data:
            idx = status_combo.findText(row_data.get('status', '空闲'))
            if idx >= 0:
                status_combo.setCurrentIndex(idx)

        form.addRow("车位编号:", no_input)
        form.addRow("关联房产:", property_combo)
        form.addRow("状态:", status_combo)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        form.addRow(btn_layout)

        def on_ok():
            pn = no_input.text()
            pid = property_combo.currentData()
            st = status_combo.currentText()
            if not pn:
                QMessageBox.warning(dlg, "提示", "请填写车位编号")
                return
            if row_data:
                result = self.controller.update_parking(row_data['parking_id'], pn, pid, st)
            else:
                result = self.controller.add_parking(pn, pid, st)
            if result['success']:
                dlg.accept()
                self.refresh_requested.emit()
            else:
                QMessageBox.warning(dlg, "失败", result['message'])

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dlg.reject)
        dlg.exec()


class BillPage(TablePage):
    """账单管理页面"""

    def __init__(self, controller, parent=None):
        super().__init__("物业账单管理", [
            ('bill_id', 'ID'), ('property_address', '房产地址'),
            ('bill_month', '月份'), ('fee_type', '费用类型'),
            ('amount', '金额(元)'), ('payment_status', '缴费状态'),
            ('due_date', '截止日期')
        ], controller, parent)
        self.add_btn.clicked.connect(lambda: self._show_edit_dialog(None))

    def load_data(self, data):
        super().load_data(data)
        self._color_unpaid()

    def _color_unpaid(self):
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 5)
            if status_item and status_item.text() == '未缴费':
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setForeground(QColor('#f53f3f'))

    def _show_edit_dialog(self, row_data):
        dlg = QDialog(self)
        dlg.setWindowTitle("编辑账单" if row_data else "新增账单")
        dlg.setFixedSize(400, 380)
        form = QFormLayout(dlg)

        property_combo = QComboBox()
        for p in self.controller.get_property_options():
            property_combo.addItem(p['label'], p['property_id'])
        if row_data and row_data.get('property_id'):
            idx = property_combo.findData(row_data['property_id'])
            if idx >= 0:
                property_combo.setCurrentIndex(idx)
        month_input = QLineEdit(row_data['bill_month'] if row_data else '')
        month_input.setPlaceholderText("YYYY-MM")
        fee_combo = QComboBox()
        fee_combo.addItems(['物业费', '水费', '电费', '燃气费'])
        if row_data:
            idx = fee_combo.findText(row_data.get('fee_type', '物业费'))
            if idx >= 0:
                fee_combo.setCurrentIndex(idx)
        amount_input = QLineEdit(str(row_data['amount']) if row_data else '')
        status_combo = QComboBox()
        status_combo.addItems(['未缴费', '已缴费'])
        if row_data:
            idx = status_combo.findText(row_data.get('payment_status', '未缴费'))
            if idx >= 0:
                status_combo.setCurrentIndex(idx)
        due_edit = QDateEdit()
        due_edit.setCalendarPopup(True)
        due_edit.setDisplayFormat("yyyy-MM-dd")
        if row_data and row_data.get('due_date'):
            d = QDate.fromString(str(row_data['due_date']), Qt.DateFormat.ISODate)
            if d.isValid():
                due_edit.setDate(d)

        form.addRow("房产:", property_combo)
        form.addRow("月份:", month_input)
        form.addRow("费用类型:", fee_combo)
        form.addRow("金额(元):", amount_input)
        form.addRow("缴费状态:", status_combo)
        form.addRow("截止日期:", due_edit)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        form.addRow(btn_layout)

        def on_ok():
            pid = property_combo.currentData()
            bm = month_input.text()
            ft = fee_combo.currentText()
            am = amount_input.text()
            ps = status_combo.currentText()
            dd = due_edit.date().toString(Qt.DateFormat.ISODate)
            if not all([pid, bm, am]):
                QMessageBox.warning(dlg, "提示", "请填写完整信息")
                return
            if row_data:
                result = self.controller.update_bill(row_data['bill_id'], pid, bm, ft, am, ps, dd)
            else:
                result = self.controller.add_bill(pid, bm, ft, am, ps, dd)
            if result['success']:
                dlg.accept()
                self.refresh_requested.emit()
            else:
                QMessageBox.warning(dlg, "失败", result['message'])

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dlg.reject)
        dlg.exec()


class RepairPage(TablePage):
    """报修工单管理页面"""

    def __init__(self, controller, parent=None):
        super().__init__("报修工单管理", [
            ('repair_id', 'ID'), ('property_address', '房产地址'),
            ('content', '报修内容'), ('status', '状态'),
            ('staff_name', '维修员工'), ('priority', '优先级'),
            ('created_at', '创建时间'), ('completed_at', '完成时间')
        ], controller, parent)
        self.add_btn.clicked.connect(lambda: self._show_edit_dialog(None))

    def load_data(self, data):
        super().load_data(data)
        self._color_priority()

    def _color_priority(self):
        colors = {'紧急': '#f53f3f', '普通': '#4e5969', '低': '#86909c'}
        for row in range(self.table.rowCount()):
            prio_item = self.table.item(row, 5)
            status_item = self.table.item(row, 3)
            if prio_item:
                color = QColor(colors.get(prio_item.text(), '#4e5969'))
                prio_item.setForeground(color)
            if status_item and status_item.text() == '已完成':
                color = QColor('#00b42a')
                status_item.setForeground(color)

    def _show_edit_dialog(self, row_data):
        session = Session()
        is_admin = session.is_admin

        dlg = QDialog(self)
        if row_data:
            dlg.setWindowTitle("编辑工单")
        else:
            dlg.setWindowTitle("提交报修")
        dlg.setFixedSize(450, 420 if is_admin else 320)
        form = QFormLayout(dlg)

        property_combo = QComboBox()
        if is_admin:
            for p in self.controller.get_property_options():
                property_combo.addItem(p['label'], p['property_id'])
            if row_data and row_data.get('property_id'):
                idx = property_combo.findData(row_data['property_id'])
                if idx >= 0:
                    property_combo.setCurrentIndex(idx)
            form.addRow("房产:", property_combo)

        content_edit = QTextEdit()
        content_edit.setPlainText(row_data['content'] if row_data else '')
        content_edit.setMaximumHeight(80)
        form.addRow("报修内容:", content_edit)

        priority_combo = QComboBox()
        priority_combo.addItems(['普通', '紧急', '低'])
        if row_data:
            idx = priority_combo.findText(row_data.get('priority', '普通'))
            if idx >= 0:
                priority_combo.setCurrentIndex(idx)
        form.addRow("优先级:", priority_combo)

        if is_admin:
            status_combo = QComboBox()
            status_combo.addItems(['待处理', '处理中', '已完成'])
            if row_data:
                idx = status_combo.findText(row_data.get('status', '待处理'))
                if idx >= 0:
                    status_combo.setCurrentIndex(idx)
            form.addRow("状态:", status_combo)

            staff_combo = QComboBox()
            staff_combo.addItem("-- 未指派 --", None)
            for s in self.controller.get_staff_options():
                staff_combo.addItem(s['label'], s['staff_id'])
            if row_data and row_data.get('staff_id'):
                idx = staff_combo.findData(row_data['staff_id'])
                if idx >= 0:
                    staff_combo.setCurrentIndex(idx)
            form.addRow("指派员工:", staff_combo)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        if row_data and is_admin:
            del_btn = QPushButton("删除")
            del_btn.setStyleSheet("QPushButton{background:#f53f3f;color:white;border:none;"
                                 "border-radius:4px;padding:0 16px;}")
            btn_layout.addWidget(del_btn)

            def on_del():
                self._confirm_delete(
                    lambda: self.controller.delete_repair(row_data['repair_id']))
                dlg.reject()

            del_btn.clicked.connect(on_del)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        form.addRow(btn_layout)

        def on_ok():
            if not is_admin:
                pid = session.owner_id
            else:
                pid = property_combo.currentData()
            ct = content_edit.toPlainText().strip()
            pr = priority_combo.currentText()
            if not ct:
                QMessageBox.warning(dlg, "提示", "请填写报修内容")
                return
            if row_data:
                if is_admin:
                    self.controller.update_repair_status(row_data['repair_id'], status_combo.currentText())
                    sid = staff_combo.currentData()
                    if sid:
                        self.controller.assign_repair_staff(row_data['repair_id'], sid)
                dlg.accept()
                self.refresh_requested.emit()
            else:
                result = self.controller.submit_repair(pid, ct, pr)
                if result['success']:
                    dlg.accept()
                    self.refresh_requested.emit()
                else:
                    QMessageBox.warning(dlg, "失败", result['message'])

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dlg.reject)
        dlg.exec()


class StaffPage(TablePage):
    """维修员工管理页面"""

    def __init__(self, controller, parent=None):
        super().__init__("维修员工管理", [
            ('staff_id', 'ID'), ('name', '姓名'), ('specialty', '工种'),
            ('phone', '联系电话'), ('current_workload', '当前接单量')
        ], controller, parent)
        self.add_btn.clicked.connect(lambda: self._show_edit_dialog(None))

    def _show_edit_dialog(self, row_data):
        dlg = QDialog(self)
        dlg.setWindowTitle("编辑员工" if row_data else "新增员工")
        dlg.setFixedSize(350, 250)
        form = QFormLayout(dlg)

        name_input = QLineEdit(row_data['name'] if row_data else '')
        spec_combo = QComboBox()
        spec_combo.addItems(['水电工', '管道工', '木工', '油漆工', '综合维修', '家电维修'])
        if row_data:
            idx = spec_combo.findText(row_data.get('specialty', ''))
            if idx >= 0:
                spec_combo.setCurrentIndex(idx)
        phone_input = QLineEdit(row_data.get('phone', '') or '')

        form.addRow("姓名:", name_input)
        form.addRow("工种:", spec_combo)
        form.addRow("联系电话:", phone_input)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        form.addRow(btn_layout)

        def on_ok():
            n, sp, ph = name_input.text(), spec_combo.currentText(), phone_input.text()
            if not all([n, sp]):
                QMessageBox.warning(dlg, "提示", "请填写完整信息")
                return
            if row_data:
                result = self.controller.update_staff(row_data['staff_id'], n, sp, ph)
            else:
                result = self.controller.add_staff(n, sp, ph)
            if result['success']:
                dlg.accept()
                self.refresh_requested.emit()
            else:
                QMessageBox.warning(dlg, "失败", result['message'])

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dlg.reject)
        dlg.exec()
