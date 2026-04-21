-- ============================================
-- 社区物业与报修缴费综合管理系统
-- 数据库表结构设计 (DDL)
-- 兼容 GaussDB / PostgreSQL
-- ============================================

-- 先删除已有表（被引用的表先删）
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS repair_orders CASCADE;
DROP TABLE IF EXISTS bills CASCADE;
DROP TABLE IF EXISTS parking_spaces CASCADE;
DROP TABLE IF EXISTS owners CASCADE;
DROP TABLE IF EXISTS staff CASCADE;
DROP TABLE IF EXISTS properties CASCADE;


-- ============================================
-- 表1: 楼栋与房产表 (properties)
-- ============================================

-- 【范式证明】
-- 主键: property_id（代理键）
-- 所有非主属性 (building_no, room_no, area, layout_type, create_time)
-- 均直接函数依赖于主键 property_id，不存在传递函数依赖。
--
-- 1NF：每个属性都是原子的，不可再分。
-- 2NF：主键是单列代理键，不存在部分函数依赖。
-- 3NF：不存在非主属性通过其他非主属性间接依赖于主键的情况。
--    即不存在 A→B→C 的传递依赖链。
--    building_no（楼栋号）描述的是该房产所在楼栋，
--    并非独立实体被多个属性依赖，因此无需拆分。
-- BCNF：每个决定因素都包含候选键，满足 BCNF。

CREATE TABLE properties (
    property_id  SERIAL       PRIMARY KEY,
    building_no  VARCHAR(10)  NOT NULL,              -- 楼栋号，如 A栋、B栋
    room_no      VARCHAR(10)  NOT NULL,              -- 房间号，如 101、201
    area         DECIMAL(8,2) NOT NULL,              -- 房产面积（平方米）
    layout_type  VARCHAR(20)  NOT NULL,              -- 户型，如 两室一厅、三室两厅
    create_time  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uk_property_room UNIQUE (building_no, room_no)   -- 同一栋楼内房间号唯一
);

COMMENT ON TABLE  properties IS '楼栋与房产表';
COMMENT ON COLUMN properties.property_id IS '房产ID（主键）';
COMMENT ON COLUMN properties.building_no IS '楼栋号';
COMMENT ON COLUMN properties.room_no IS '房间号';
COMMENT ON COLUMN properties.area IS '房产面积（平方米）';
COMMENT ON COLUMN properties.layout_type IS '户型描述';


-- ============================================
-- 表2: 维修员工表 (staff)
-- ============================================

-- 【范式证明】
-- 主键: staff_id（代理键）
-- 所有非主属性 (name, specialty, phone, current_workload, create_time)
-- 均直接函数依赖于 staff_id。
--
-- 1NF：每个属性都是原子的。
-- 2NF：单列主键，无部分函数依赖。
-- 3NF/BCNF：name、specialty、phone 均描述 staff_id 对应的员工本身，
--    不存在"姓名→工种→接单量"之类的传递依赖。
--    每个决定因素（staff_id）都包含候选键。

CREATE TABLE staff (
    staff_id         SERIAL       PRIMARY KEY,
    name             VARCHAR(50)  NOT NULL,       -- 员工姓名
    specialty        VARCHAR(50)  NOT NULL,       -- 工种，如 水电工、管道工、木工
    phone            VARCHAR(20),                -- 联系电话
    current_workload INT          DEFAULT 0,      -- 当前接单量
    create_time      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  staff IS '维修员工表';
COMMENT ON COLUMN staff.staff_id IS '员工ID（主键）';
COMMENT ON COLUMN staff.name IS '员工姓名';
COMMENT ON COLUMN staff.specialty IS '工种';
COMMENT ON COLUMN staff.phone IS '联系电话';
COMMENT ON COLUMN staff.current_workload IS '当前接单量（由触发器自动维护）';


-- ============================================
-- 表3: 业主/住户表 (owners)
-- ============================================

-- 【范式证明】
-- 主键: owner_id（代理键）
-- 所有非主属性 (name, phone, id_card, property_id, move_in_date, owner_type, create_time)
-- 均直接函数依赖于 owner_id。
--
-- 1NF：每个属性都是原子的。
-- 2NF：单列主键，无部分函数依赖。
-- 3NF/BCNF：
--    name、phone、id_card 描述的是业主个人身份信息，直接依赖于 owner_id。
--    property_id 是外键，表示业主与房产的关联关系。
--    不存在"业主→房产→面积"这样的传递依赖，因为面积信息存储在房产表中，
--    不在本表中重复出现。
--    owner_type（业主/租户）直接描述 owner_id 对应的住户类型，
--    不依赖于 property_id（同一套房产可以先后有业主和租户）。

CREATE TABLE owners (
    owner_id    SERIAL       PRIMARY KEY,
    name        VARCHAR(50)  NOT NULL,           -- 业主/住户姓名
    phone       VARCHAR(20)  NOT NULL,           -- 联系方式
    id_card     VARCHAR(18),                     -- 身份证号
    property_id INTEGER      NOT NULL,           -- 关联房产ID
    move_in_date DATE        NOT NULL,           -- 入住时间
    owner_type  VARCHAR(10)  DEFAULT '业主',      -- 类型：业主 / 租户
    create_time TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_owner_property FOREIGN KEY (property_id)
        REFERENCES properties(property_id) ON DELETE RESTRICT  -- 有业主关联时禁止删除房产
);

COMMENT ON TABLE  owners IS '业主/住户表';
COMMENT ON COLUMN owners.owner_id IS '业主ID（主键）';
COMMENT ON COLUMN owners.name IS '业主/住户姓名';
COMMENT ON COLUMN owners.phone IS '联系方式';
COMMENT ON COLUMN owners.id_card IS '身份证号';
COMMENT ON COLUMN owners.property_id IS '关联的房产ID（外键）';
COMMENT ON COLUMN owners.move_in_date IS '入住时间';
COMMENT ON COLUMN owners.owner_type IS '住户类型（业主/租户）';


-- ============================================
-- 表4: 车位管理表 (parking_spaces)
-- ============================================

-- 【范式证明】
-- 主键: parking_id（代理键）
-- 所有非主属性 (parking_no, property_id, status, create_time)
-- 均直接函数依赖于 parking_id。
--
-- 1NF：每个属性都是原子的。
-- 2NF：单列主键，无部分函数依赖。
-- 3NF/BCNF：
--    parking_no 是车位的编号，直接依赖于 parking_id。
--    status（空闲/已租/已售）描述车位本身的状态，
--    不依赖于 property_id（车位可以不绑定任何房产，property_id 允许为空）。
--    不存在传递依赖。

CREATE TABLE parking_spaces (
    parking_id  SERIAL      PRIMARY KEY,
    parking_no  VARCHAR(20) NOT NULL UNIQUE,     -- 车位编号，如 A-001
    property_id INTEGER,                         -- 关联房产ID（可为空，表示未绑定）
    status      VARCHAR(10) DEFAULT '空闲',      -- 状态：空闲 / 已租 / 已售
    create_time TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_parking_property FOREIGN KEY (property_id)
        REFERENCES properties(property_id) ON DELETE SET NULL  -- 删除房产时车位保留但解除绑定
);

COMMENT ON TABLE  parking_spaces IS '车位管理表';
COMMENT ON COLUMN parking_spaces.parking_id IS '车位ID（主键）';
COMMENT ON COLUMN parking_spaces.parking_no IS '车位编号';
COMMENT ON COLUMN parking_spaces.property_id IS '关联房产ID（外键，可为空）';
COMMENT ON COLUMN parking_spaces.status IS '车位状态（空闲/已租/已售）';


-- ============================================
-- 表5: 物业账单表 (bills)
-- ============================================

-- 【范式证明】
-- 主键: bill_id（代理键）
-- 候选键: (property_id, bill_month, fee_type) 联合唯一
-- 所有非主属性 (property_id, bill_month, fee_type, amount, payment_status, due_date, create_time)
-- 均直接函数依赖于 bill_id。
--
-- 1NF：每个属性都是原子的。
-- 2NF：使用代理键 bill_id 作为主键，不存在部分函数依赖。
-- 3NF/BCNF：
--    关键设计决策：账单依赖于房产 (property_id) 而非业主 (owner_id)。
--    这保证了即使租户变更，账单记录仍然与房产绑定，不会因住户变更导致账单归属混乱。
--    amount（金额）由 fee_type 和房产面积共同决定，但计算逻辑在存储过程中完成，
--    amount 作为账单记录的一个快照值，直接依赖于 bill_id。
--    payment_status 描述的是账单本身的缴费状态，不依赖于其他非主属性。
--    不存在传递依赖。

CREATE TABLE bills (
    bill_id        SERIAL        PRIMARY KEY,
    property_id    INTEGER       NOT NULL,       -- 关联房产ID
    bill_month     VARCHAR(7)    NOT NULL,       -- 账单月份，格式 YYYY-MM
    fee_type       VARCHAR(20)   NOT NULL,       -- 费用类型：水费/电费/物业费/燃气费
    amount         DECIMAL(10,2) NOT NULL,       -- 金额（元）
    payment_status VARCHAR(10)   DEFAULT '未缴费', -- 缴费状态：未缴费 / 已缴费
    due_date       DATE,                         -- 截止缴费日期
    create_time    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_bill_property FOREIGN KEY (property_id)
        REFERENCES properties(property_id) ON DELETE RESTRICT,  -- 有未处理账单时禁止删除房产
    CONSTRAINT uk_bill UNIQUE (property_id, bill_month, fee_type)  -- 同一房产同月同类费用唯一
);

COMMENT ON TABLE  bills IS '物业账单表';
COMMENT ON COLUMN bills.bill_id IS '账单ID（主键）';
COMMENT ON COLUMN bills.property_id IS '关联房产ID（外键）';
COMMENT ON COLUMN bills.bill_month IS '账单月份';
COMMENT ON COLUMN bills.fee_type IS '费用类型';
COMMENT ON COLUMN bills.amount IS '金额（元）';
COMMENT ON COLUMN bills.payment_status IS '缴费状态';
COMMENT ON COLUMN bills.due_date IS '截止缴费日期';


-- ============================================
-- 表6: 报修工单表 (repair_orders)
-- ============================================

-- 【范式证明】
-- 主键: repair_id（代理键）
-- 所有非主属性 (property_id, content, status, staff_id, priority, created_at, completed_at)
-- 均直接函数依赖于 repair_id。
--
-- 1NF：每个属性都是原子的（content 使用 TEXT 类型存储报修描述）。
-- 2NF：单列主键，无部分函数依赖。
-- 3NF/BCNF：
--    status 描述的是工单本身的状态，直接依赖于 repair_id，
--    不依赖于 staff_id 或 property_id。
--    staff_id 是外键，表示该工单指派的维修员工，
--    并非 repair_id 的子属性，而是独立的关联关系，不构成传递依赖。
--    priority 描述工单紧急程度，直接依赖于 repair_id。
--    不存在传递依赖。

CREATE TABLE repair_orders (
    repair_id    SERIAL        PRIMARY KEY,
    property_id  INTEGER       NOT NULL,       -- 报修房产ID
    content      TEXT          NOT NULL,       -- 报修内容描述
    status       VARCHAR(20)   DEFAULT '待处理', -- 状态：待处理 / 处理中 / 已完成
    staff_id     INTEGER,                      -- 指派维修员工ID（可为空）
    priority     VARCHAR(10)   DEFAULT '普通',  -- 优先级：紧急 / 普通 / 低
    created_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,                    -- 完成时间

    CONSTRAINT fk_repair_property FOREIGN KEY (property_id)
        REFERENCES properties(property_id) ON DELETE CASCADE,  -- 删除房产时级联删除相关工单
    CONSTRAINT fk_repair_staff FOREIGN KEY (staff_id)
        REFERENCES staff(staff_id) ON DELETE SET NULL  -- 删除员工时保留工单但解除指派
);

COMMENT ON TABLE  repair_orders IS '报修工单表';
COMMENT ON COLUMN repair_orders.repair_id IS '工单ID（主键）';
COMMENT ON COLUMN repair_orders.property_id IS '报修房产ID（外键）';
COMMENT ON COLUMN repair_orders.content IS '报修内容';
COMMENT ON COLUMN repair_orders.status IS '工单状态（待处理/处理中/已完成）';
COMMENT ON COLUMN repair_orders.staff_id IS '指派维修员工ID（外键）';
COMMENT ON COLUMN repair_orders.priority IS '优先级';
COMMENT ON COLUMN repair_orders.created_at IS '创建时间';
COMMENT ON COLUMN repair_orders.completed_at IS '完成时间';


-- ============================================
-- 表7: 系统用户表 (users) — 登录权限管理
-- ============================================

-- 【范式证明】
-- 主键: user_id（代理键）
-- 所有非主属性 (username, password, role, owner_id, is_active, create_time)
-- 均直接函数依赖于 user_id。
--
-- 1NF：每个属性都是原子的。
-- 2NF：单列主键，无部分函数依赖。
-- 3NF/BCNF：
--    role（ADMIN/OWNER）描述用户权限级别，直接依赖于 user_id，
--    不依赖于 owner_id（管理员用户可能不绑定任何业主记录）。
--    username 具有唯一约束，作为候选键。
--    owner_id 是外键，用于关联业主身份（仅 OWNER 角色需要），
--    不构成传递依赖。

CREATE TABLE users (
    user_id      SERIAL       PRIMARY KEY,
    username     VARCHAR(50)  NOT NULL UNIQUE,   -- 登录用户名
    password     VARCHAR(100) NOT NULL,          -- 密码
    role         VARCHAR(20)  NOT NULL DEFAULT 'OWNER', -- 角色：ADMIN / OWNER
    owner_id     INTEGER,                        -- 关联业主ID（管理员可为空）
    is_active    BOOLEAN     DEFAULT TRUE,       -- 账户是否启用
    create_time  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_owner FOREIGN KEY (owner_id)
        REFERENCES owners(owner_id) ON DELETE SET NULL,
    CONSTRAINT chk_user_role CHECK (role IN ('ADMIN', 'OWNER'))
);

COMMENT ON TABLE  users IS '系统用户表（登录权限管理）';
COMMENT ON COLUMN users.user_id IS '用户ID（主键）';
COMMENT ON COLUMN users.username IS '登录用户名';
COMMENT ON COLUMN users.password IS '密码';
COMMENT ON COLUMN users.role IS '用户角色（ADMIN/OWNER）';
COMMENT ON COLUMN users.owner_id IS '关联业主ID';
COMMENT ON COLUMN users.is_active IS '账户是否启用';


-- ============================================
-- 索引优化（针对常用查询场景）
-- ============================================

CREATE INDEX idx_owners_property ON owners(property_id);
CREATE INDEX idx_parking_property ON parking_spaces(property_id);
CREATE INDEX idx_bills_property ON bills(property_id);
CREATE INDEX idx_bills_status ON bills(payment_status);
CREATE INDEX idx_bills_month ON bills(bill_month);
CREATE INDEX idx_repair_property ON repair_orders(property_id);
CREATE INDEX idx_repair_staff ON repair_orders(staff_id);
CREATE INDEX idx_repair_status ON repair_orders(status);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_owner ON users(owner_id);
