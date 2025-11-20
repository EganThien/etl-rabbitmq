-- Staging tables
CREATE DATABASE IF NOT EXISTS etl_db;
USE etl_db;

CREATE TABLE IF NOT EXISTS staging_employee (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id VARCHAR(50),
  full_name VARCHAR(255),
  email VARCHAR(255),
  raw_payload TEXT,
  validation_errors TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS main_employee (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id VARCHAR(50) UNIQUE,
  full_name VARCHAR(255),
  email VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging_order_detail (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id VARCHAR(50),
  product_id VARCHAR(50),
  quantity INT,
  price DECIMAL(12,2),
  raw_payload TEXT,
  validation_errors TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS main_order_detail (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id VARCHAR(50),
  product_id VARCHAR(50),
  quantity INT,
  price DECIMAL(12,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Note: unique constraint on order_id can be added if desired; keep schema simple for compatibility
