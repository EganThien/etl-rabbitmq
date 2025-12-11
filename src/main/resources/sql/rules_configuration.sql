-- Rules Configuration Tables
-- Bảng quản lý validation rules có thể enable/disable

CREATE TABLE IF NOT EXISTS validation_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rule_code VARCHAR(20) NOT NULL UNIQUE COMMENT 'Mã rule (R1, R2, R3...)',
    rule_name VARCHAR(100) NOT NULL COMMENT 'Tên rule',
    rule_type VARCHAR(50) NOT NULL COMMENT 'Loại rule: validation, transformation, quality_check',
    entity_type VARCHAR(20) NOT NULL COMMENT 'employee, order, hoặc both',
    field_name VARCHAR(50) COMMENT 'Tên field áp dụng',
    rule_description TEXT COMMENT 'Mô tả chi tiết rule',
    validation_logic TEXT COMMENT 'Logic validation (regex, conditions...)',
    error_message VARCHAR(255) COMMENT 'Thông báo lỗi mặc định',
    is_enabled BOOLEAN DEFAULT TRUE COMMENT 'Bật/tắt rule',
    severity VARCHAR(20) DEFAULT 'ERROR' COMMENT 'ERROR, WARNING, INFO',
    execution_order INT DEFAULT 0 COMMENT 'Thứ tự thực thi',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_entity_type (entity_type),
    INDEX idx_enabled (is_enabled),
    INDEX idx_execution_order (execution_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Quản lý validation rules';

-- Transform Stages Configuration
CREATE TABLE IF NOT EXISTS transform_stages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stage_number INT NOT NULL COMMENT '1 = Cleansing, 2 = Enrichment',
    stage_name VARCHAR(50) NOT NULL COMMENT 'Tên stage',
    stage_description TEXT COMMENT 'Mô tả stage',
    is_enabled BOOLEAN DEFAULT TRUE,
    execution_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_stage (stage_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Cấu hình transform stages';

-- Rules to Stages Mapping
CREATE TABLE IF NOT EXISTS rule_stage_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rule_id INT NOT NULL,
    stage_id INT NOT NULL,
    execution_order INT DEFAULT 0,
    FOREIGN KEY (rule_id) REFERENCES validation_rules(id) ON DELETE CASCADE,
    FOREIGN KEY (stage_id) REFERENCES transform_stages(id) ON DELETE CASCADE,
    UNIQUE KEY unique_rule_stage (rule_id, stage_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Map rules vào stages';

-- Insert default transform stages
INSERT INTO transform_stages (stage_number, stage_name, stage_description, is_enabled, execution_order) VALUES
(1, 'Stage 1: Data Cleansing', 'Làm sạch dữ liệu - normalize, trim, format chuẩn', TRUE, 1),
(2, 'Stage 2: Data Enrichment', 'Làm giàu dữ liệu - derived fields, lookups, calculations', TRUE, 2)
ON DUPLICATE KEY UPDATE stage_name = VALUES(stage_name);

-- Insert default validation rules for EMPLOYEE
INSERT INTO validation_rules (rule_code, rule_name, rule_type, entity_type, field_name, rule_description, validation_logic, error_message, is_enabled, severity, execution_order) VALUES
('R1', 'Employee ID Not Empty', 'validation', 'employee', 'employee_id', 'Kiểm tra mã nhân viên không được rỗng', 'not_empty', 'Mã nhân viên không được để trống', TRUE, 'ERROR', 1),
('R2', 'Full Name Not Empty', 'validation', 'employee', 'full_name', 'Kiểm tra họ tên không được rỗng', 'not_empty', 'Họ tên không được để trống', TRUE, 'ERROR', 2),
('R3', 'Email Valid Format', 'validation', 'employee', 'email', 'Kiểm tra định dạng email hợp lệ', '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$', 'Email không đúng định dạng', TRUE, 'ERROR', 3),
('R4', 'Phone Valid Format', 'validation', 'employee', 'phone', 'Kiểm tra định dạng số điện thoại', '^(\\+84|84|0)[0-9]{9,10}$', 'Số điện thoại không hợp lệ', TRUE, 'ERROR', 4),
('R5', 'Normalize Full Name', 'transformation', 'employee', 'full_name', 'Chuẩn hóa họ tên - Title Case', 'title_case', NULL, TRUE, 'INFO', 10),
('R6', 'Normalize Email', 'transformation', 'employee', 'email', 'Chuẩn hóa email - lowercase, trim', 'lowercase_trim', NULL, TRUE, 'INFO', 11),
('R7', 'Normalize Phone E.164', 'transformation', 'employee', 'phone', 'Chuẩn hóa SĐT về định dạng E.164 (+84xxx)', 'e164_format', NULL, TRUE, 'INFO', 12)
ON DUPLICATE KEY UPDATE rule_name = VALUES(rule_name);

-- Insert default validation rules for ORDER
INSERT INTO validation_rules (rule_code, rule_name, rule_type, entity_type, field_name, rule_description, validation_logic, error_message, is_enabled, severity, execution_order) VALUES
('R10', 'Order ID Not Empty', 'validation', 'order', 'order_id', 'Kiểm tra mã đơn hàng không được rỗng', 'not_empty', 'Mã đơn hàng không được để trống', TRUE, 'ERROR', 1),
('R11', 'Product ID Not Empty', 'validation', 'order', 'product_id', 'Kiểm tra mã sản phẩm không được rỗng', 'not_empty', 'Mã sản phẩm không được để trống', TRUE, 'ERROR', 2),
('R12', 'Quantity Positive', 'validation', 'order', 'quantity', 'Kiểm tra số lượng phải > 0', 'positive_integer', 'Số lượng phải là số nguyên dương', TRUE, 'ERROR', 3),
('R13', 'Price Positive', 'validation', 'order', 'price', 'Kiểm tra giá phải > 0', 'positive_number', 'Giá phải là số dương', TRUE, 'ERROR', 4),
('R14', 'Normalize Product ID', 'transformation', 'order', 'product_id', 'Chuẩn hóa mã sản phẩm - uppercase, trim', 'uppercase_trim', NULL, TRUE, 'INFO', 10),
('R15', 'Round Price', 'transformation', 'order', 'price', 'Làm tròn giá 2 chữ số thập phân', 'round_2_decimals', NULL, TRUE, 'INFO', 11)
ON DUPLICATE KEY UPDATE rule_name = VALUES(rule_name);

-- Map rules to stages
-- Stage 1 (Cleansing): Validation rules
INSERT INTO rule_stage_mapping (rule_id, stage_id, execution_order) 
SELECT r.id, 1, r.execution_order 
FROM validation_rules r 
WHERE r.rule_type = 'validation' AND r.is_enabled = TRUE
ON DUPLICATE KEY UPDATE execution_order = VALUES(execution_order);

-- Stage 2 (Enrichment): Transformation rules  
INSERT INTO rule_stage_mapping (rule_id, stage_id, execution_order)
SELECT r.id, 2, r.execution_order
FROM validation_rules r
WHERE r.rule_type = 'transformation' AND r.is_enabled = TRUE
ON DUPLICATE KEY UPDATE execution_order = VALUES(execution_order);

-- View: Active rules by stage and entity
CREATE OR REPLACE VIEW v_active_rules AS
SELECT 
    r.rule_code,
    r.rule_name,
    r.rule_type,
    r.entity_type,
    r.field_name,
    r.validation_logic,
    r.error_message,
    r.severity,
    s.stage_number,
    s.stage_name,
    rsm.execution_order
FROM validation_rules r
INNER JOIN rule_stage_mapping rsm ON r.id = rsm.rule_id
INNER JOIN transform_stages s ON rsm.stage_id = s.id
WHERE r.is_enabled = TRUE AND s.is_enabled = TRUE
ORDER BY s.stage_number, rsm.execution_order;
