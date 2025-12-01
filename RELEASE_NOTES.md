# Release Notes: v0.2.0

**Release Date:** 2025-12-01  
**Branch:** `feature/add-phone-and-validation`  
**Tag:** `v0.2.0`

## 🎯 Overview

This release significantly enhances the ETL pipeline with robust data validation, comprehensive testing infrastructure, and production-grade error handling. Major improvements include phone number validation, integration test coverage, null-safe DAO operations, and automated CI/CD workflows.

---

## ✨ New Features

### 📞 Phone Number Validation
- **PhoneNumberRule**: Validates international phone format (E.164 standard)
- **Regex Pattern**: `^\+?[1-9]\d{1,14}$` supports international prefixes
- **Model Updates**: `Employee` class extended with `phone` field
- **Database Schema**: Migration script adds `phone` column to staging and main tables
- **Test Coverage**: `PhoneNumberRuleTest` with 5 test cases

### ✅ Enhanced Email Validation
- **Apache Commons Validator**: Replaced custom email regex with industry-standard `EmailValidator`
- **Improved Accuracy**: Better handling of complex email formats
- **Dependency**: `commons-validator:1.7` added to pom.xml

### 🧪 Integration Testing
- **TransformLoadTest**: End-to-end testing with H2 in-memory database
- **Test Scenarios**:
  - Valid employee records transfer to main table
  - Invalid records marked with `validation_errors` JSON
  - Mixed valid/invalid batch processing
  - Order detail validation (quantity rules)
- **H2 Database**: MySQL-compatible mode for fast test execution
- **Coverage**: 19 total tests (14 unit + 5 integration) - all passing

### 🔒 Hardened Data Access Layer
- **Null-Safe Operations**: All `StagingDao` methods validate non-null parameters
- **Helper Method**: `nullSafe(String value)` converts null to empty string
- **Error Logging**: SQLException messages include entity IDs for debugging
- **JavaDoc**: Comprehensive method documentation with parameter validation rules

### 🔄 Improved Transform Logic
- **Immediate Error Commit**: `TransformLoad` commits `validation_errors` JSON immediately after marking invalid records
- **Data Integrity**: Prevents validation error loss in batch processing
- **Batch Processing**: Optimized with configurable `BATCH_SIZE` (500 records)

### 🚀 CI/CD Pipeline
- **GitHub Actions**: `.github/workflows/maven.yml` workflow
- **Automated Testing**: Runs on push/PR to main/develop branches
- **Build Verification**: Java 11 compilation and test suite execution

### 🐳 E2E Smoke Testing
- **PowerShell Script**: `scripts/run-e2e.ps1` automates Docker Compose testing
- **Services**: RabbitMQ, MySQL, consumers, dashboard
- **Fixed**: PowerShell escaping issues with nested quotes
- **Simplified**: Single-quoted strings and variable extraction

### 📊 Database Migration
- **Migration File**: `migrations/001-add-phone.sql`
- **Schema Changes**: Adds `phone VARCHAR(20)` to `staging_employee` and `main_employee`
- **Safe Execution**: Idempotent ALTER TABLE statements

---

## 🐛 Bug Fixes

- **PowerShell Escaping**: Fixed nested quote parsing errors in `run-e2e.ps1`
- **Validation Commit Timing**: TransformLoad now commits errors immediately (prevents data loss)
- **Null Handling**: StagingDao rejects null entities with `IllegalArgumentException`

---

## 📦 Dependencies

### New Dependencies
```xml
<!-- Email validation -->
<dependency>
  <groupId>commons-validator</groupId>
  <artifactId>commons-validator</artifactId>
  <version>1.7</version>
</dependency>

<!-- Integration testing -->
<dependency>
  <groupId>com.h2database</groupId>
  <artifactId>h2</artifactId>
  <version>2.2.224</version>
  <scope>test</scope>
</dependency>
```

### Existing Dependencies
- **Jackson**: 2.15.2 (JSON processing)
- **OpenCSV**: 5.7.1 (CSV parsing)
- **RabbitMQ Client**: 5.16.0 (message queue)
- **MySQL Connector**: 8.0.33 (database)
- **JUnit**: 5.9.3 (testing)
- **SLF4J**: 1.7.36 (logging)

---

## 🔧 Migration Instructions

### Database Schema Update

1. **Apply Migration Script**:
   ```bash
   mysql -u etl_user -p etl_db < migrations/001-add-phone.sql
   ```

2. **Verify Column Addition**:
   ```sql
   DESCRIBE staging_employee;
   DESCRIBE main_employee;
   ```
   Confirm `phone VARCHAR(20)` column exists.

### Code Deployment

1. **Build Project**:
   ```bash
   mvn clean package
   ```

2. **Run Tests**:
   ```bash
   mvn test
   ```
   Expected: 19 tests passing, 0 failures.

3. **Deploy JAR**:
   ```bash
   java -cp target/etl-rabbitmq-0.2.0.jar com.example.etl.main.MainApp
   ```

### Docker Environment Update

1. **Rebuild Containers**:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

2. **Run Migration**:
   ```bash
   docker exec -i etl_mysql mysql -u etl_user -petl_password etl_db < migrations/001-add-phone.sql
   ```

3. **Verify Consumers**:
   ```bash
   docker logs etl_consumer
   ```

---

## 🧪 Testing

### Run Unit Tests
```bash
mvn test -Dtest=*RuleTest
```

### Run Integration Tests
```bash
mvn test -Dtest=TransformLoadTest
```

### E2E Smoke Test
```powershell
.\scripts\run-e2e.ps1
```

### Expected Results
- **Total Tests**: 19 (14 unit + 5 integration)
- **Failures**: 0
- **Errors**: 0
- **Skipped**: 0
- **Build**: SUCCESS

---

## 📝 Breaking Changes

⚠️ **None** - This release is backward compatible with v0.1.0.

### Upgrade Path from v0.1.0
1. Apply database migration (adds `phone` column)
2. Update dependencies (`mvn clean install`)
3. Rebuild application JAR
4. No configuration changes required

---

## 🔮 Future Enhancements (Roadmap)

- [ ] Docker-based E2E tests in CI workflow
- [ ] Additional validation rules (date format, postal code)
- [ ] Performance benchmarking for large datasets
- [ ] Monitoring dashboard improvements
- [ ] Support for additional CSV schemas

---

## 🤝 Contributing

To contribute to this project:

1. Create feature branch from `develop`
2. Follow validation rule pattern (implement `Rule` interface)
3. Add unit tests for new rules
4. Update integration tests if changing transform logic
5. Run full test suite before PR: `mvn clean test`
6. Fill in PR template with issue number, labels, and reviewers

---

## 📚 Documentation

- **README.md**: Project overview and setup instructions
- **CHANGELOG.md**: Detailed change history
- **SCRIPTS.md**: PowerShell script documentation
- **PROGRESS.md**: Development progress tracking
- **PR_BODY.md**: Pull request template content

---

## 🏷️ Release Tag

```bash
git tag -a v0.2.0 -m "Release v0.2.0: Phone validation, integration tests, hardened DAO, CI/CD pipeline"
git push origin v0.2.0
```

---

## 📞 Support

For issues or questions:
- **GitHub Issues**: https://github.com/EganThien/etl-rabbitmq/issues
- **Pull Requests**: https://github.com/EganThien/etl-rabbitmq/pulls

---

**Full Changelog**: https://github.com/EganThien/etl-rabbitmq/compare/v0.1.0...v0.2.0
