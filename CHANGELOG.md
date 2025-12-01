# Changelog

All notable changes to this project are documented here.

## [Unreleased]
- Add stricter email validation: `EmailRule` now uses Apache Commons `EmailValidator`.
- Add `phone` field to `Employee` model and DB schema (`staging_employee`, `main_employee`).
- Add `PhoneNumberRule` and unit tests for phone validation.
- Update `CSVProducer` to optionally read `phone` column from `employee.csv` (4th column if present).
- Integrate validation into `TransformLoad`:
  - `transferEmployees()` and `transferOrders()` now validate staging records before upsert.
  - Invalid records are annotated in `validation_errors` JSON column and are not moved to main tables.
- Update `StagingDao` to persist `phone` for employee staging inserts.
- Fix: remove duplicate class declaration in `CSVProducer.java`.
- Tests: added `PhoneNumberRuleTest`; all unit tests pass locally (14 tests, 0 failures).

## Notes
- If upgrading an existing database, run migration SQL to add the `phone` column to `staging_employee` and `main_employee`.
- Phone validation currently allows international formats with `+`, spaces, dashes and parentheses. If you need strict E.164 support, we can change the rule.

