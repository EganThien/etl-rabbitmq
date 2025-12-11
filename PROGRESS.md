ETL-RabbitMQ — Progress Snapshot

**Last Updated:** 2025-12-07  
**Author:** Team ETL Demo

## ✅ Completion Status: 83% (8.3/10 Features)

### Core Features (100% Complete)
- ✅ Producer/Consumer for `employee.csv` and `order_detail.csv`
- ✅ Validation rules engine with database persistence
- ✅ Two-stage transform architecture (Validation + Enrichment)
- ✅ Transform logging with batch tracking
- ✅ Field-level audit trail (original vs transformed data)
- ✅ Web dashboard with file upload, history, and rules management
- ✅ Docker Compose orchestration (MySQL, RabbitMQ, Dashboard)

### Advanced Features (Completed This Session)
1. ✅ **Transform Log Table** - Comprehensive tracking in `transform_log` table with UI
2. ✅ **Data Transformation Audit** - Field-level changes logged in `data_transformation_audit`
3. ✅ **Batch ID System** - All 4 tables updated with `batch_id` columns + indexes
4. ✅ **Write Log File** - Python logging framework with daily rotation to `/app/logs/`
5. ✅ **Rules Configuration System** - 15+ validation/transformation rules in database
   - UI at `/rules` route with enable/disable toggles
   - 3 new tables: `validation_rules`, `transform_stages`, `rule_stage_mapping`
6. ✅ **Quality Metrics Dashboard** - Chart.js visualizations for Valid/Error rates
7. ✅ **Two-Stage Transform Architecture** - Rules-driven Stage 1 (Validation) + Stage 2 (Enrichment)
   - Employees: 100% complete
   - Orders: 100% complete (just implemented)
8. ✅ **Email Notifications** - SMTP integration with threshold-based error alerts (95% - needs SMTP config)
9. ✅ **Scheduled Jobs** - Cron-based automation via `scheduler.py` (85% - needs deployment)
10. ⏳ **Data Lineage Visualization** - Batch tracking in place, UI pending (40%)

## 🚀 Latest Changes (Dec 7, 2025)

### Major Enhancements
1. **Rules-Based Transform V2** - `/api/run-transform-v2` endpoint
   - Database-driven validation and transformation rules
   - Two-stage processing: Cleansing (Stage 1) → Enrichment (Stage 2)
   - Dynamic rule loading from `validation_rules` table
   - Support for both employees and orders

2. **Comprehensive Logging System**
   - File-based logging to `/app/logs/etl_YYYYMMDD.log`
   - API endpoints: `/api/list-logs` and `/api/download-logs`
   - UI integration in History page with download links

3. **Quality Metrics Visualization**
   - Chart.js line charts for Valid Rate and Error Rate trends
   - 7-day history with interactive tooltips
   - Real-time metrics calculation

4. **Rules Management UI** - New `/rules` page
   - View all validation and transformation rules
   - Enable/disable rules with toggle switches
   - Organized by Stage 1 (Validation) and Stage 2 (Transformation)
   - Separate sections for Employee and Order rules

5. **Email Notification System**
   - SMTP integration with configurable threshold
   - HTML email templates with dashboard links
   - Automatic alerts when error count exceeds threshold
   - Environment-based configuration

6. **Scheduled Jobs Infrastructure**
   - `scheduler.py` script for cron execution
   - Comprehensive logging to `/app/logs/scheduler_YYYYMMDD.log`
   - Smart execution (checks staging data before running)
   - Support for v1 and v2 transform
   - `start.sh` script to launch dashboard + cron
   - Example cron configurations in `SCHEDULER_GUIDE.md`

### Database Updates
- Added `batch_id` columns to all 4 tables (staging + main)
- Added `original_data` JSON columns to main tables
- Created `validation_rules` table with 15+ pre-configured rules
- Created `transform_stages` table (2 stages)
- Created `rule_stage_mapping` table for rule execution order
- Added view `v_active_rules` for easy querying

### Previous Changes (Nov 20, 2025)
- Added migration script `scripts/migrate-validation-errors.ps1`
- Updated `scripts/integration-run.ps1` to call migration after schema load
- Dashboard shows `validation_errors` for staging rows

How to run a quick demo locally (minimal steps)
1) Build and start the stack (Docker Desktop required):

```powershell
cd d:\1.ProjectTuHoc\DA_TichHopHeThong\etl-rabbitmq
docker compose up -d --build
```

2) Run schema and migration (script waits for MySQL):

```powershell
.\scripts\integration-run.ps1 -RunProducer -RunTransform
```

This will:
- Load schema (creates tables)
- Run migration to add `validation_errors` columns if needed
- Run the producer (publish CSV rows into RabbitMQ)
- Wait a short time and run the transform step (if `-RunTransform` given)
- Print docker status, DB counts and app logs

Notes / Known issues
- Do NOT include `.env` with credentials when sharing. Use `.env.example` if needed.
- If your MySQL service has a different name in `docker-compose.yml`, edit `scripts/load-schema.ps1` and `scripts/migrate-validation-errors.ps1` (they exec into service named `mysql`).

Remaining work
- Finish `file_2` consumer (if different dataset) — currently `OrderConsumer` consumes `order_detail.csv` sample
- Add dashboard panel for `validation_errors` counts (optional)
- Add integration tests for end-to-end verification

Contact
- Reply to this branch/PR or email the team for clarifications.
