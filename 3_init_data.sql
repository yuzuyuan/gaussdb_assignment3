-- ============================================
-- 社区物业与报修缴费综合管理系统
-- 视图、动态SQL函数、测试数据
-- 兼容 GaussDB / PostgreSQL
-- ============================================


-- ============================================
-- 一、视图：综合房产信息视图
-- ============================================

-- 视图：v_comprehensive_property_info
-- 将房产信息、业主信息、未缴账单总额汇总在一起
-- 方便前端直接查询展示

CREATE OR REPLACE VIEW v_comprehensive_property_info AS
SELECT
    p.property_id,
    p.building_no,
    p.room_no,
    p.area,
    p.layout_type,
    o.owner_id,
    o.name       AS owner_name,
    o.phone      AS owner_phone,
    o.owner_type,
    o.move_in_date,
    ps.parking_no,
    ps.status    AS parking_status,
    COALESCE(unpaid.unpaid_count, 0)    AS unpaid_bill_count,
    COALESCE(unpaid.unpaid_total, 0.00) AS unpaid_bill_total,
    COALESCE(repair.pending_count, 0)   AS pending_repair_count
FROM properties p
LEFT JOIN owners o ON p.property_id = o.property_id
LEFT JOIN parking_spaces ps ON p.property_id = ps.property_id AND ps.status != '空闲'
LEFT JOIN (
    SELECT
        property_id,
        COUNT(*)                                  AS unpaid_count,
        SUM(amount)                               AS unpaid_total
    FROM bills
    WHERE payment_status = '未缴费'
    GROUP BY property_id
) unpaid ON p.property_id = unpaid.property_id
LEFT JOIN (
    SELECT
        property_id,
        COUNT(*)                                  AS pending_count
    FROM repair_orders
    WHERE status != '已完成'
    GROUP BY property_id
) repair ON p.property_id = repair.property_id;

COMMENT ON VIEW v_comprehensive_property_info IS '综合房产信息视图：关联房产、业主、车位、未缴账单和待处理工单';


-- ============================================
-- 二、视图：维修员工工单统计视图
-- ============================================

CREATE OR REPLACE VIEW v_staff_workload_stats AS
SELECT
    s.staff_id,
    s.name          AS staff_name,
    s.specialty,
    s.phone,
    s.current_workload,
    COALESCE(completed.completed_count, 0)  AS completed_count,
    COALESCE(pending.pending_count, 0)      AS pending_count
FROM staff s
LEFT JOIN (
    SELECT staff_id, COUNT(*) AS completed_count
    FROM repair_orders
    WHERE status = '已完成'
    GROUP BY staff_id
) completed ON s.staff_id = completed.staff_id
LEFT JOIN (
    SELECT staff_id, COUNT(*) AS pending_count
    FROM repair_orders
    WHERE status IN ('待处理', '处理中')
    GROUP BY staff_id
) pending ON s.staff_id = pending.staff_id
ORDER BY s.current_workload DESC;

COMMENT ON VIEW v_staff_workload_stats IS '维修员工工单统计视图：展示每位员工的已完成和待处理工单数';


-- ============================================
-- 三、动态SQL函数：灵活查询账单
-- ============================================

-- 函数：func_dynamic_search_bills(search_condition)
-- 使用 EXECUTE 动态拼装并执行 SQL
-- search_condition 为 WHERE 子句条件（不含 WHERE 关键字）
-- 返回匹配的账单记录

CREATE OR REPLACE FUNCTION func_dynamic_search_bills(
    search_condition TEXT
)
RETURNS TABLE (
    bill_id INTEGER,
    building_no VARCHAR(10),
    room_no VARCHAR(10),
    owner_name VARCHAR(50),
    bill_month VARCHAR(7),
    fee_type VARCHAR(20),
    amount DECIMAL(10,2),
    payment_status VARCHAR(10),
    due_date DATE
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_sql TEXT;
BEGIN
    -- 动态拼装 SQL：关联 bills、properties、owners 三表
    v_sql := 'SELECT
                 b.bill_id,
                 p.building_no,
                 p.room_no,
                 o.name,
                 b.bill_month,
                 b.fee_type,
                 b.amount,
                 b.payment_status,
                 b.due_date
              FROM bills b
              JOIN properties p ON b.property_id = p.property_id
              LEFT JOIN owners o ON p.property_id = o.property_id';

    -- 如果用户提供了搜索条件，追加 WHERE 子句
    IF search_condition IS NOT NULL AND TRIM(search_condition) != '' THEN
        v_sql := v_sql || ' WHERE ' || search_condition;
    END IF;

    v_sql := v_sql || ' ORDER BY b.bill_month DESC, p.building_no, p.room_no';

    -- 使用 EXECUTE 执行动态 SQL
    RETURN QUERY EXECUTE v_sql;
END;
$$;

COMMENT ON FUNCTION func_dynamic_search_bills(TEXT) IS '动态SQL函数：灵活查询账单，search_condition为WHERE条件字符串';

-- 使用示例：
-- SELECT * FROM func_dynamic_search_bills('payment_status = ''未缴费''');
-- SELECT * FROM func_dynamic_search_bills('fee_type = ''水费'' AND b.amount > 100');
-- SELECT * FROM func_dynamic_search_bills('p.building_no = ''A栋''');


-- ============================================
-- 四、动态SQL函数：灵活查询报修工单
-- ============================================

CREATE OR REPLACE FUNCTION func_dynamic_search_repairs(
    search_condition TEXT
)
RETURNS TABLE (
    repair_id INTEGER,
    building_no VARCHAR(10),
    room_no VARCHAR(10),
    owner_name VARCHAR(50),
    content TEXT,
    status VARCHAR(20),
    staff_name VARCHAR(50),
    priority VARCHAR(10),
    created_at TIMESTAMP,
    completed_at TIMESTAMP
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_sql TEXT;
BEGIN
    v_sql := 'SELECT
                 ro.repair_id,
                 p.building_no,
                 p.room_no,
                 o.name,
                 ro.content,
                 ro.status,
                 s.name,
                 ro.priority,
                 ro.created_at,
                 ro.completed_at
              FROM repair_orders ro
              JOIN properties p ON ro.property_id = p.property_id
              LEFT JOIN owners o ON p.property_id = o.property_id
              LEFT JOIN staff s ON ro.staff_id = s.staff_id';

    IF search_condition IS NOT NULL AND TRIM(search_condition) != '' THEN
        v_sql := v_sql || ' WHERE ' || search_condition;
    END IF;

    v_sql := v_sql || ' ORDER BY ro.created_at DESC';

    RETURN QUERY EXECUTE v_sql;
END;
$$;

COMMENT ON FUNCTION func_dynamic_search_repairs(TEXT) IS '动态SQL函数：灵活查询报修工单，search_condition为WHERE条件字符串';


-- ============================================
-- 五、测试数据（Mock Data）
-- ============================================

-- 插入顺序：独立表 → 关联表
-- 楼栋与房产表 → 维修员工表 → 业主表 → 车位表 → 账单表 → 报修工单表 → 用户表

-- ---------- 5.1 楼栋与房产表（10条） ----------
INSERT INTO properties (building_no, room_no, area, layout_type) VALUES
('A栋', '101', 89.50,  '两室一厅'),
('A栋', '201', 120.00, '三室两厅'),
('A栋', '302', 75.80,  '两室一厅'),
('B栋', '101', 150.00, '四室两厅'),
('B栋', '203', 89.50,  '两室一厅'),
('B栋', '305', 110.00, '三室一厅'),
('C栋', '102', 65.00,  '一室一厅'),
('C栋', '201', 95.00,  '两室两厅'),
('C栋', '401', 130.00, '三室两厅'),
('D栋', '101', 180.00, '复式四室');

-- ---------- 5.2 维修员工表（8条） ----------
INSERT INTO staff (name, specialty, phone, current_workload) VALUES
('李师傅', '水电工',   '13800138001', 3),
('王师傅', '管道工',   '13800138002', 2),
('张师傅', '木工',     '13800138003', 1),
('刘师傅', '水电工',   '13800138004', 4),
('陈师傅', '油漆工',   '13800138005', 0),
('赵师傅', '管道工',   '13800138006', 2),
('周师傅', '综合维修', '13800138007', 1),
('吴师傅', '水电工',   '13800138008', 3);

-- ---------- 5.3 业主/住户表（10条） ----------
INSERT INTO owners (name, phone, id_card, property_id, move_in_date, owner_type) VALUES
('张三',   '13900001111', '110101199001011234', 1, '2020-03-15', '业主'),
('李四',   '13900002222', '110101198505052345', 2, '2019-08-01', '业主'),
('王五',   '13900003333', '110101199203033456', 3, '2021-01-10', '业主'),
('赵六',   '13900004444', '110101198808084567', 4, '2018-06-20', '业主'),
('孙七',   '13900005555', '110101199505055678', 5, '2022-11-01', '租户'),
('周八',   '13900006666', '110101199106066789', 6, '2020-09-15', '业主'),
('吴九',   '13900007777', '110101198707077890', 7, '2023-02-01', '租户'),
('郑十',   '13900008888', '110101199404048901', 8, '2021-07-20', '业主'),
('钱十一', '13900009999', '110101198912129012', 9, '2019-04-10', '业主'),
('陈十二', '13900010000', '110101199208083012', 10, '2020-12-01', '业主');

-- ---------- 5.4 车位管理表（10条） ----------
INSERT INTO parking_spaces (parking_no, property_id, status) VALUES
('A-001', 1,  '已售'),
('A-002', 2,  '已租'),
('A-003', NULL, '空闲'),
('B-001', 4,  '已售'),
('B-002', 5,  '已租'),
('B-003', NULL, '空闲'),
('C-001', 8,  '已租'),
('C-002', NULL, '空闲'),
('D-001', 10, '已售'),
('D-002', NULL, '空闲');

-- ---------- 5.5 物业账单表（30条：每月×多费用类型） ----------
-- 2025年12月
INSERT INTO bills (property_id, bill_month, fee_type, amount, payment_status, due_date) VALUES
(1,  '2025-12', '物业费', 223.75,  '已缴费', '2025-12-25'),
(1,  '2025-12', '水费',   45.00,   '已缴费', '2025-12-25'),
(1,  '2025-12', '电费',   180.00,  '已缴费', '2025-12-25'),
(2,  '2025-12', '物业费', 300.00,  '已缴费', '2025-12-25'),
(2,  '2025-12', '水费',   60.00,   '已缴费', '2025-12-25'),
(3,  '2025-12', '物业费', 189.50,  '未缴费', '2025-12-25'),
(3,  '2025-12', '电费',   120.00,  '已缴费', '2025-12-25'),
(4,  '2025-12', '物业费', 375.00,  '已缴费', '2025-12-25'),
(4,  '2025-12', '燃气费', 95.00,   '未缴费', '2025-12-25'),
(5,  '2025-12', '物业费', 223.75,  '未缴费', '2025-12-25'),
-- 2026年1月
(1,  '2026-01', '物业费', 223.75,  '已缴费', '2026-01-25'),
(1,  '2026-01', '水费',   38.00,   '未缴费', '2026-01-25'),
(1,  '2026-01', '电费',   210.00,  '已缴费', '2026-01-25'),
(2,  '2026-01', '物业费', 300.00,  '已缴费', '2026-01-25'),
(2,  '2026-01', '燃气费', 110.00,  '已缴费', '2026-01-25'),
(3,  '2026-01', '物业费', 189.50,  '未缴费', '2026-01-25'),
(6,  '2026-01', '物业费', 275.00,  '已缴费', '2026-01-25'),
(6,  '2026-01', '水费',   55.00,   '已缴费', '2026-01-25'),
(7,  '2026-01', '物业费', 162.50,  '未缴费', '2026-01-25'),
(8,  '2026-01', '物业费', 237.50,  '已缴费', '2026-01-25'),
-- 2026年2月
(1,  '2026-02', '物业费', 223.75,  '已缴费', '2026-02-25'),
(1,  '2026-02', '水费',   42.00,   '已缴费', '2026-02-25'),
(1,  '2026-02', '电费',   195.00,  '未缴费', '2026-02-25'),
(2,  '2026-02', '物业费', 300.00,  '已缴费', '2026-02-25'),
(2,  '2026-02', '水费',   52.00,   '未缴费', '2026-02-25'),
(4,  '2026-02', '物业费', 375.00,  '未缴费', '2026-02-25'),
(5,  '2026-02', '物业费', 223.75,  '已缴费', '2026-02-25'),
(9,  '2026-02', '物业费', 325.00,  '已缴费', '2026-02-25'),
(9,  '2026-02', '燃气费', 88.00,   '未缴费', '2026-02-25'),
(10, '2026-02', '物业费', 450.00,  '已缴费', '2026-02-25');

-- ---------- 5.6 报修工单表（10条） ----------
INSERT INTO repair_orders (property_id, content, status, staff_id, priority, created_at, completed_at) VALUES
(1, '厨房水龙头漏水',       '已完成', 1, '普通', '2026-01-05 09:30:00', '2026-01-05 14:20:00'),
(1, '卧室灯泡不亮',         '已完成', 4, '低',   '2026-01-08 10:00:00', '2026-01-09 11:00:00'),
(2, '卫生间马桶堵塞',       '已完成', 2, '紧急', '2026-01-10 08:00:00', '2026-01-10 16:30:00'),
(3, '阳台窗户关不严',       '处理中', 3, '普通', '2026-02-01 14:00:00', NULL),
(4, '客厅墙壁开裂',         '处理中', 5, '普通', '2026-02-10 09:00:00', NULL),
(5, '厨房下水道返味',       '待处理', NULL, '紧急', '2026-02-15 11:30:00', NULL),
(6, '卧室门锁损坏',         '处理中', 7, '普通', '2026-02-18 15:00:00', NULL),
(8, '主卧空调不制冷',       '待处理', NULL, '紧急', '2026-02-20 10:00:00', NULL),
(9, '卫生间瓷砖脱落',       '待处理', NULL, '普通', '2026-02-22 09:00:00', NULL),
(10, '全屋电路故障',        '处理中', 4, '紧急', '2026-02-25 08:30:00', NULL);

-- ---------- 5.7 系统用户表（3条） ----------
-- 密码使用简单的明文（作业演示用，生产环境应使用 bcrypt 等哈希）
INSERT INTO users (username, password, role, owner_id, is_active) VALUES
('admin',  'admin123', 'ADMIN', NULL, TRUE),   -- 管理员
('zhangsan', '123456', 'OWNER', 1, TRUE),       -- 张三（业主）
('lisi',   '123456', 'OWNER', 2, TRUE);         -- 李四（业主）
