-- Migration: add `phone` column to employee staging and main tables
-- Run this once against the `etl_db` database. If your DB already has these
-- columns, skip or modify accordingly.

ALTER TABLE staging_employee
  ADD COLUMN phone VARCHAR(50);

ALTER TABLE main_employee
  ADD COLUMN phone VARCHAR(50);

-- End migration
