# ETL System - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Docker Desktop installed and running
- PowerShell (Windows) or Bash (Linux/Mac)
- Port 8080, 3306, 5672, 15672 available

---

## Step 1: Start the System

```powershell
cd d:\1.ProjectTuHoc\DA_TichHopHeThong\etl-rabbitmq
docker-compose up -d
```

**Wait ~30 seconds for services to be ready**

---

## Step 2: Load Database Schema

```powershell
# Load main schema
docker exec etl-rabbitmq-mysql-1 mysql -uetl_user -petl_password etl_db < src/main/resources/sql/create_tables.sql

# Load rules configuration
docker exec etl-rabbitmq-mysql-1 mysql -uetl_user -petl_password etl_db < src/main/resources/sql/rules_configuration.sql
```

**✅ System is now ready!**

---

## Step 3: Access the Dashboard

Open browser: **http://localhost:8080**

You should see the main dashboard with:
- 📊 Current table counts
- 📁 Upload CSV button
- 📈 History button
- ⚙️ Rules Config button

---

## Step 4: Upload Sample Data

### Option A: Via Dashboard (Recommended)
1. Click **"📁 Upload CSV"** button
2. Select file: `src/main/resources/data/employee.csv`
3. Click **"Upload CSV"**
4. Wait for success message

### Option B: Via PowerShell Script
```powershell
.\scripts\run-producer.ps1
```

---

## Step 5: Run Transform

### Option A: Via Dashboard
1. After upload, click **"🔄 Run Transform"** button
2. Watch progress in real-time
3. See results in popup

### Option B: Via API (Transform V2)
```powershell
curl -X POST http://localhost:8080/api/run-transform-v2
```

### Option C: Via PowerShell Script
```powershell
.\scripts\run-transform.ps1
```

---

## Step 6: View Results

### Check History
1. Click **"📊 History"** button
2. See all transform executions with:
   - Batch ID
   - Records processed
   - Error counts
   - Processing time

### View Quality Charts
Scroll down on History page to see:
- Valid Rate trend (7 days)
- Error Rate trend (7 days)

### Check Audit Trail
View field-level transformations:
- Original values
- Transformed values
- Rules applied

---

## 🎯 Quick Tasks

### View/Edit Validation Rules
```
Navigate to: http://localhost:8080/rules
```
- See all 15+ validation and transformation rules
- Enable/disable rules with toggle switches
- View rule details in modal

### Download Logs
```
1. Go to History page
2. Scroll to "📁 ETL Log Files" section
3. Click download button for desired date
```

### Check Database Records
```powershell
# Check staging tables
docker exec etl-rabbitmq-mysql-1 mysql -uetl_user -petl_password etl_db -e "SELECT COUNT(*) as staging_employees FROM staging_employee; SELECT COUNT(*) as staging_orders FROM staging_order_detail;"

# Check main tables
docker exec etl-rabbitmq-mysql-1 mysql -uetl_user -petl_password etl_db -e "SELECT COUNT(*) as main_employees FROM main_employee; SELECT COUNT(*) as main_orders FROM main_order_detail;"

# Check transform log
docker exec etl-rabbitmq-mysql-1 mysql -uetl_user -petl_password etl_db -e "SELECT * FROM transform_log ORDER BY started_at DESC LIMIT 5;"
```

---

## ⚙️ Configuration Options

### Enable Email Notifications
Edit `docker-compose.yml` and add:
```yaml
environment:
  SMTP_HOST: smtp.gmail.com
  SMTP_PORT: 587
  SMTP_USER: your-email@gmail.com
  SMTP_PASSWORD: your-app-password
  SMTP_TO_EMAIL: admin@company.com
  ERROR_NOTIFICATION_THRESHOLD: 10
```

Then restart:
```powershell
docker-compose down
docker-compose up -d
```

### Enable Scheduled Jobs
Edit `docker-compose.yml` and set:
```yaml
environment:
  ENABLE_SCHEDULER: "true"
  USE_V2_TRANSFORM: "true"
```

Then rebuild:
```powershell
docker-compose down
docker-compose build etl-dashboard
docker-compose up -d
```

Scheduler will run:
- Every 30 minutes during business hours (Mon-Fri, 8 AM - 6 PM)
- Every hour outside business hours

---

## 🔧 Troubleshooting

### Dashboard Not Loading
```powershell
# Check container status
docker ps

# Check dashboard logs
docker logs etl-rabbitmq-etl-dashboard-1

# Restart dashboard
docker-compose restart etl-dashboard
```

### Upload Shows 0 Rows
```powershell
# Check if batch_id columns exist
docker exec etl-rabbitmq-mysql-1 mysql -uetl_user -petl_password etl_db -e "DESC staging_employee;"

# If missing, run migration
.\scripts\migrate-validation-errors.ps1
```

### Transform Fails
```powershell
# Check validation rules loaded
docker exec etl-rabbitmq-mysql-1 mysql -uetl_user -petl_password etl_db -e "SELECT COUNT(*) FROM validation_rules;"

# Should return 15+ rules
# If 0, reload rules:
docker exec etl-rabbitmq-mysql-1 mysql -uetl_user -petl_password etl_db < src/main/resources/sql/rules_configuration.sql
```

### Scheduler Not Running
```powershell
# Check if enabled
docker exec etl-rabbitmq-etl-dashboard-1 env | grep ENABLE_SCHEDULER

# Check cron status
docker exec etl-rabbitmq-etl-dashboard-1 service cron status

# View scheduler logs
docker exec etl-rabbitmq-etl-dashboard-1 cat /app/logs/scheduler_$(date +%Y%m%d).log
```

---

## 📚 Learn More

- **Full Setup Guide:** See README.md
- **Scheduler Guide:** See SCHEDULER_GUIDE.md
- **Progress Report:** See PROGRESS.md
- **Completion Report:** See COMPLETION_REPORT.md
- **Scripts Documentation:** See SCRIPTS.md

---

## 🎉 You're All Set!

The ETL system is now running with:
- ✅ CSV upload functionality
- ✅ Two-stage transform (Validation + Enrichment)
- ✅ 15+ configurable validation rules
- ✅ Comprehensive logging and audit trail
- ✅ Quality metrics with charts
- ✅ Email notifications (if configured)
- ✅ Scheduled automation (if enabled)

**Next Steps:**
1. Upload your own CSV files
2. Customize validation rules via `/rules` page
3. Monitor quality metrics over time
4. Set up email notifications for production
5. Enable scheduler for automated transforms

**Need Help?**
- Check logs: http://localhost:8080 → History → Log Files
- View errors: Check staging tables for validation_errors
- Test API: `curl http://localhost:8080/api/status`

---

**Happy ETL-ing!** 🚀
