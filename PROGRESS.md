ETL-RabbitMQ — Progress snapshot

Date: 2025-11-20
Author: Team ETL Demo

Summary
- Producer/Consumer for `employee.csv` (file_1): done
- Producer for `order_detail.csv` (file_1): done
- Consumers: `EmployeeConsumer` and `OrderConsumer` implemented; validation rules applied and validation errors persisted to staging (new column `validation_errors`)
- Rule engine & unit tests: done (tests green)
- Transform (staging -> main): implemented in `TransformLoad` (transferEmployees, transferOrders)
- Docker compose and dashboard: present (dashboard shows queues and table counts)

What I changed now (Nov 20, 2025)
- Added migration script `scripts/migrate-validation-errors.ps1` to add `validation_errors` column on existing DBs
- Updated `scripts/integration-run.ps1` to call the migration script after loading schema
- Updated `dashboard/app.py` to surface `validation_errors` beside recent staging rows
- Added this `PROGRESS.md`

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
