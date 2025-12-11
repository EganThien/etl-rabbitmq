-- Clear old data first
TRUNCATE staging_employee;
TRUNCATE staging_order_detail;
TRUNCATE main_employee;
TRUNCATE main_order_detail;

-- Insert 10 employees (5 valid, 5 invalid)
INSERT INTO staging_employee (employee_id, full_name, email, phone) VALUES
-- VALID EMPLOYEES (5)
('E001', 'Alice Smith', 'alice@example.com', '+84901234567'),
('E002', 'John Doe', 'john.doe@company.com', '+84912345678'),
('E003', 'Maria Garcia', 'maria.garcia@test.com', '+84923456789'),
('E004', 'Chen Wei', 'chen.wei@email.com', '+84934567890'),
('E005', 'Sarah Johnson', 'sarah.j@work.com', '+84945678901'),

-- INVALID EMPLOYEES (5)
('E006', 'Bob Invalid', 'bob_at_company', '123'),
('E007', 'Li Chen', 'li@test', '+8499'),
('E008', 'Bad Email', 'notanemail', '456'),
('E009', 'Short Phone', 'good@email.com', '12'),
('E010', 'No Domain', 'missing@', '+84908639483');

-- Insert 10 orders (6 valid, 4 invalid)
INSERT INTO staging_order_detail (order_id, product_id, quantity, price) VALUES
-- VALID ORDERS (6)
('O1001', 'P001', 5, 1500.00),
('O1002', 'P002', 10, 250.50),
('O1003', 'P003', 3, 99.99),
('O1004', 'P004', 1, 2500.00),
('O1005', 'P005', 20, 15.75),
('O1006', 'P006', 7, 450.00),

-- INVALID ORDERS (4)
('O1007', '', 5, 100.00),
('O1008', 'P008', -5, 50.00),
('O1009', '', 3, 75.00),
('O1010', 'P010', -10, 200.00);
