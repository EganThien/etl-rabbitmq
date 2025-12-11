-- Staging tables
CREATE DATABASE IF NOT EXISTS etl_db;
USE etl_db;

CREATE TABLE IF NOT EXISTS staging_employee (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id VARCHAR(50),
  full_name VARCHAR(255),
  email VARCHAR(255),
  phone VARCHAR(50),
  raw_payload TEXT,
  validation_errors TEXT,
  batch_id VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_batch (batch_id)
);

CREATE TABLE IF NOT EXISTS main_employee (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id VARCHAR(50) UNIQUE,
  full_name VARCHAR(255),
  email VARCHAR(255),
  phone VARCHAR(50),
  batch_id VARCHAR(50),
  original_data JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_batch (batch_id)
);

CREATE TABLE IF NOT EXISTS staging_order_detail (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id VARCHAR(50),
  product_id VARCHAR(50),
  quantity INT,
  price DECIMAL(12,2),
  raw_payload TEXT,
  validation_errors TEXT,
  batch_id VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_batch (batch_id)
);

CREATE TABLE IF NOT EXISTS main_order_detail (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id VARCHAR(50),
  product_id VARCHAR(50),
  quantity INT,
  price DECIMAL(12,2),
  batch_id VARCHAR(50),
  original_data JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_batch (batch_id)
);

-- Transform Log Table - Track ETL processing history
CREATE TABLE IF NOT EXISTS transform_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  batch_id VARCHAR(50) NOT NULL,
  entity_type VARCHAR(20) NOT NULL,
  total_records INT DEFAULT 0,
  valid_records INT DEFAULT 0,
  error_records INT DEFAULT 0,
  processing_time_ms INT DEFAULT 0,
  status VARCHAR(20) DEFAULT 'processing',
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP NULL,
  INDEX idx_batch (batch_id),
  INDEX idx_entity (entity_type),
  INDEX idx_status (status)
);

-- Data Transformation Audit Table - Track field-level changes
CREATE TABLE IF NOT EXISTS data_transformation_audit (
  id INT AUTO_INCREMENT PRIMARY KEY,
  batch_id VARCHAR(50),
  entity_type VARCHAR(20) NOT NULL,
  entity_id VARCHAR(50) NOT NULL,
  field_name VARCHAR(50) NOT NULL,
  original_value TEXT,
  transformed_value TEXT,
  transform_rule VARCHAR(100),
  transformed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_batch (batch_id),
  INDEX idx_entity (entity_type, entity_id)
);

-- Data Quality Metrics Table - Track quality trends over time
CREATE TABLE IF NOT EXISTS data_quality_metrics (
  id INT AUTO_INCREMENT PRIMARY KEY,
  metric_date DATE NOT NULL,
  entity_type VARCHAR(20) NOT NULL,
  total_records INT DEFAULT 0,
  valid_records INT DEFAULT 0,
  error_records INT DEFAULT 0,
  valid_rate DECIMAL(5,2) DEFAULT 0,
  error_rate DECIMAL(5,2) DEFAULT 0,
  duplicate_count INT DEFAULT 0,
  duplicate_rate DECIMAL(5,2) DEFAULT 0,
  completeness_score DECIMAL(5,2) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY unique_metric (metric_date, entity_type),
  INDEX idx_date (metric_date)
);

-- Note: unique constraint on order_id can be added if desired; keep schema simple for compatibility
