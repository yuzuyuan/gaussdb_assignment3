-- ============================================
-- 社区物业与报修缴费综合管理系统
-- 高级特性：存储过程、函数、触发器
-- 兼容 GaussDB / PostgreSQL
-- ============================================


-- ============================================
-- 一、触发器：工单完成时自动减少员工接单量
-- ============================================

-- 触发器函数：监听 repair_orders 表的 UPDATE 操作
-- 当工单状态变更为"已完成"时，将对应维修员工的 current_workload 减 1
-- 同时自动记录 completed_at 完成时间

CREATE OR REPLACE FUNCTION fn_on_repair_completed()
RETURNS TRIGGER AS $$
BEGIN
    -- 仅当工单状态从非"已完成"变更为"已完成"时触发
    IF NEW.status = '已完成' AND (OLD.status IS NULL OR OLD.status != '已完成') THEN

        -- 记录完成时间
        NEW.completed_at := CURRENT_TIMESTAMP;

        -- 如果工单已指派员工，则减少该员工的接单量
        IF NEW.staff_id IS NOT NULL THEN
            UPDATE staff
            SET current_workload = GREATEST(current_workload - 1, 0)
            WHERE staff_id = NEW.staff_id;
        END IF;

        RAISE NOTICE '工单 % 已完成，员工 % 接单量已更新', NEW.repair_id, NEW.staff_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_on_repair_completed() IS '工单完成触发器函数：自动减少员工接单量并记录完成时间';

-- 创建触发器：绑定到 repair_orders 表的 UPDATE 事件
-- 使用 AFTER UPDATE，确保在数据更新完成后执行
CREATE TRIGGER trg_update_staff_workload
AFTER UPDATE ON repair_orders
FOR EACH ROW
EXECUTE FUNCTION fn_on_repair_completed();

COMMENT ON TRIGGER trg_update_staff_workload ON repair_orders IS '工单状态变更为已完成时，自动减少维修员工接单量';


-- ============================================
-- 二、触发器：指派工单时自动增加员工接单量
-- ============================================

-- 触发器函数：当工单被指派给员工（staff_id 从 NULL 变为具体值）时，
-- 自动将该员工的 current_workload 加 1

CREATE OR REPLACE FUNCTION fn_on_repair_assigned()
RETURNS TRIGGER AS $$
BEGIN
    -- 当工单新指派了员工（且之前没有指派或更换了员工）时
    IF NEW.staff_id IS NOT NULL AND (OLD.staff_id IS NULL OR OLD.staff_id != NEW.staff_id) THEN

        -- 如果之前有指派其他员工，先减去旧员工的接单量
        IF OLD.staff_id IS NOT NULL AND OLD.staff_id != NEW.staff_id THEN
            UPDATE staff
            SET current_workload = GREATEST(current_workload - 1, 0)
            WHERE staff_id = OLD.staff_id;
        END IF;

        -- 增加新指派员工的接单量
        UPDATE staff
        SET current_workload = current_workload + 1
        WHERE staff_id = NEW.staff_id;

        -- 同步更新工单状态为"处理中"
        IF NEW.status = '待处理' THEN
            UPDATE repair_orders
            SET status = '处理中'
            WHERE repair_id = NEW.repair_id;
        END IF;

        RAISE NOTICE '工单 % 已指派给员工 %', NEW.repair_id, NEW.staff_id;
    END IF;

    -- 当员工被撤销指派（staff_id 变为 NULL）时，减少原员工接单量
    IF NEW.staff_id IS NULL AND OLD.staff_id IS NOT NULL THEN
        UPDATE staff
        SET current_workload = GREATEST(current_workload - 1, 0)
        WHERE staff_id = OLD.staff_id;

        RAISE NOTICE '工单 % 已撤销员工 % 的指派', NEW.repair_id, OLD.staff_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_on_repair_assigned() IS '工单指派触发器函数：自动增减员工接单量';

CREATE TRIGGER trg_on_repair_assigned
AFTER UPDATE ON repair_orders
FOR EACH ROW
EXECUTE FUNCTION fn_on_repair_assigned();

COMMENT ON TRIGGER trg_on_repair_assigned ON repair_orders IS '工单指派/撤销员工时自动维护接单量';


-- ============================================
-- 三、存储过程：批量生成月度物业账单
-- ============================================

-- 存储过程：sp_generate_monthly_bills(target_month)
-- 遍历所有房产，为每户生成指定月份的物业费账单
-- 金额根据房产面积计算：物业费单价 × 面积
-- 如果该房产该月已有物业费账单则跳过

CREATE OR REPLACE PROCEDURE sp_generate_monthly_bills(
    target_month VARCHAR  -- 目标月份，格式 'YYYY-MM'
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_property_id  INTEGER;
    v_building_no  VARCHAR(10);
    v_room_no      VARCHAR(10);
    v_area         DECIMAL(8,2);
    v_amount       DECIMAL(10,2);
    v_unit_price   DECIMAL(6,2) := 2.50;  -- 物业费单价：2.50 元/平方米/月
    v_count        INTEGER := 0;
BEGIN
    RAISE NOTICE '开始生成 % 月物业费账单...', target_month;

    -- 遍历所有房产
    FOR v_property_id, v_building_no, v_room_no, v_area IN
        SELECT property_id, building_no, room_no, area
        FROM properties
        ORDER BY building_no, room_no
    LOOP
        -- 检查该房产该月是否已有物业费账单
        IF EXISTS (
            SELECT 1 FROM bills
            WHERE property_id = v_property_id
              AND bill_month = target_month
              AND fee_type = '物业费'
        ) THEN
            RAISE NOTICE '跳过 % %（已有 % 月物业费账单）', v_building_no, v_room_no, target_month;
            CONTINUE;
        END IF;

        -- 计算物业费金额 = 单价 × 面积
        v_amount := v_unit_price * v_area;

        -- 插入物业费账单
        INSERT INTO bills (property_id, bill_month, fee_type, amount, payment_status, due_date)
        VALUES (v_property_id, target_month, '物业费', v_amount, '未缴费',
                (target_month || '-25')::DATE);

        v_count := v_count + 1;
        RAISE NOTICE '已生成 % % %月物业费：%.2f 元', v_building_no, v_room_no, target_month, v_amount;
    END LOOP;

    RAISE NOTICE '物业费账单生成完毕，共新增 % 条', v_count;
END;
$$;

COMMENT ON PROCEDURE sp_generate_monthly_bills(VARCHAR) IS '批量生成指定月份的物业费账单，金额按面积计算';


-- ============================================
-- 四、函数：统计指定月份的缴费率
-- ============================================

-- 函数：func_payment_rate(month)
-- 返回指定月份的物业费缴费率（百分比）

CREATE OR REPLACE FUNCTION func_payment_rate(
    target_month VARCHAR
)
RETURNS DECIMAL(5,2)
LANGUAGE plpgsql
AS $$
DECLARE
    v_total   INTEGER;
    v_paid    INTEGER;
    v_rate    DECIMAL(5,2);
BEGIN
    SELECT COUNT(*), SUM(CASE WHEN payment_status = '已缴费' THEN 1 ELSE 0 END)
    INTO v_total, v_paid
    FROM bills
    WHERE bill_month = target_month AND fee_type = '物业费';

    IF v_total IS NULL OR v_total = 0 THEN
        RETURN 0.00;
    END IF;

    v_rate := ROUND(v_paid::DECIMAL / v_total * 100, 2);
    RETURN v_rate;
END;
$$;

COMMENT ON FUNCTION func_payment_rate(VARCHAR) IS '统计指定月份物业费的缴费率（百分比）';


-- ============================================
-- 五、函数：获取员工当前工单明细
-- ============================================

-- 函数：func_staff_workload_detail(staff_id_param)
-- 返回指定员工当前所有未完成工单的明细

CREATE OR REPLACE FUNCTION func_staff_workload_detail(
    p_staff_id INTEGER
)
RETURNS TABLE (
    repair_id INTEGER,
    building_no VARCHAR(10),
    room_no VARCHAR(10),
    content TEXT,
    priority VARCHAR(10),
    created_at TIMESTAMP
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT ro.repair_id, p.building_no, p.room_no,
           ro.content, ro.priority, ro.created_at
    FROM repair_orders ro
    JOIN properties p ON ro.property_id = p.property_id
    WHERE ro.staff_id = p_staff_id
      AND ro.status != '已完成'
    ORDER BY
        CASE ro.priority WHEN '紧急' THEN 1 WHEN '普通' THEN 2 ELSE 3 END,
        ro.created_at;
END;
$$;

COMMENT ON FUNCTION func_staff_workload_detail(INTEGER) IS '查询指定员工当前未完成工单明细，按优先级排序';
