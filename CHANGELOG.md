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
  - Commit `validation_errors` updates immediately to ensure they persist.
- Harden `StagingDao` with null-safe field handling and better error logging.
- Add integration tests: `TransformLoadTest` with H2 in-memory DB (5 test cases, 19 total tests pass).
- Add GitHub Actions CI workflow to run `mvn test` on push/PR.
- Add E2E smoke script `scripts/run-e2e.ps1` for local end-to-end testing.
- Add DB migration `migrations/001-add-phone.sql` for existing databases.
- Fix: remove duplicate class declaration in `CSVProducer.java`.
- Fix: PowerShell escaping in `run-e2e.ps1`.

## Notes
- If upgrading an existing database, run migration SQL to add the `phone` column to `staging_employee` and `main_employee`.
- Phone validation currently allows international formats with `+`, spaces, dashes and parentheses. If you need strict E.164 support, we can change the rule.

