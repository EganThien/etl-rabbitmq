### Summary

- Adds stricter email validation (Apache Commons EmailValidator).
- Adds PhoneNumberRule and unit tests.
- Adds phone field to Employee model, updates StagingDao, CSVProducer and SQL schema.
- Transform step validates records and records alidation_errors JSON for invalid rows.
- Adds DB migration migrations/001-add-phone.sql, CI workflow and E2E smoke script.

### Related Issue

- Issue: #<issue-number> (replace if applicable)

### Labels (suggested)
- enhancement
- database
- ci

### Reviewers (suggested)
- @<reviewer-github-username>

### Migration
Run the migration before deploying to environments with existing data:

`powershell
mysql -u <user> -p -h <host> <database> < migrations/001-add-phone.sql
`

### Testing
- Unit tests: mvn test  all unit tests pass locally.
- E2E: run .emplates\scripts\run-e2e.ps1 or .
un-e2e.ps1 (see README for details).

### Checklist
- [ ] mvn test passed locally
- [ ] Migration applied on target DB
- [ ] README/CHANGELOG updated
- [ ] CI green
- [ ] Reviewers assigned and approved

Please replace placeholders above (issue number, reviewers) as needed.
