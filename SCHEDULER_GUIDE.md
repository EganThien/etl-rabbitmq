# ETL Scheduler Setup Guide

## Overview
The ETL system includes an automated scheduler that can run transforms on a scheduled basis using cron jobs.

## Features
- ✅ Automatic transform execution during business hours
- ✅ Configurable schedule via environment variables
- ✅ Comprehensive logging to `/app/logs/scheduler_YYYYMMDD.log`
- ✅ Smart execution (only runs if staging data exists)
- ✅ Support for both v1 and v2 transform
- ✅ Automatic log cleanup (30-day retention)

## Quick Start

### 1. Enable Scheduler
Set environment variable in docker-compose.yml or .env:
```bash
ENABLE_SCHEDULER=true
```

### 2. Configure Transform Version
```bash
USE_V2_TRANSFORM=true  # Use new rules-based transform
# OR
USE_V2_TRANSFORM=false  # Use legacy transform
```

### 3. Rebuild and Start Container
```bash
docker-compose down
docker-compose build etl-dashboard
docker-compose up -d etl-dashboard
```

### 4. Verify Cron Jobs
```bash
docker exec -it etl-rabbitmq-etl-dashboard-1 crontab -l
```

## Default Schedule

### Business Hours (Mon-Fri, 8 AM - 6 PM)
```
*/30 8-18 * * 1-5    # Every 30 minutes
```

### Off Hours (Nights and Weekends)
```
0 19-23,0-7 * * *    # Every hour
```

### Log Cleanup (Daily at 1 AM)
```
0 1 * * *            # Delete logs older than 30 days
```

## Custom Schedule

### Option 1: Environment Variables (Future Enhancement)
```bash
SCHEDULER_BUSINESS_HOURS="*/15 8-18 * * 1-5"  # Every 15 minutes
SCHEDULER_OFF_HOURS="0 */2 19-23,0-7 * * *"   # Every 2 hours
```

### Option 2: Modify start.sh
Edit `dashboard/start.sh` and change the crontab entries:
```bash
# More frequent during business hours
echo "*/15 8-18 * * 1-5 cd /app && /usr/local/bin/python /app/scheduler.py >> /app/logs/cron.log 2>&1" | crontab -

# Less frequent at night
echo "0 */3 19-23,0-7 * * * cd /app && /usr/local/bin/python /app/scheduler.py >> /app/logs/cron.log 2>&1" | crontab -a
```

### Option 3: Manual Cron Configuration
Exec into container and edit crontab directly:
```bash
docker exec -it etl-rabbitmq-etl-dashboard-1 bash
crontab -e
```

## Scheduler Logs

### View Real-Time Logs
```bash
# Cron execution log
docker exec etl-rabbitmq-etl-dashboard-1 tail -f /app/logs/cron.log

# Scheduler detailed log
docker exec etl-rabbitmq-etl-dashboard-1 tail -f /app/logs/scheduler_$(date +%Y%m%d).log
```

### Download Logs from Dashboard
1. Navigate to http://localhost:8080
2. Click "📊 History"
3. Scroll to "📁 ETL Log Files"
4. Click download button for desired date

## Monitoring

### Check Last Run
```bash
docker exec etl-rabbitmq-etl-dashboard-1 cat /app/logs/scheduler_$(date +%Y%m%d).log | tail -20
```

### Check Cron Status
```bash
docker exec etl-rabbitmq-etl-dashboard-1 service cron status
```

### Verify Scheduled Jobs
```bash
docker exec etl-rabbitmq-etl-dashboard-1 crontab -l
```

## Manual Execution

### Test Scheduler Script
```bash
docker exec etl-rabbitmq-etl-dashboard-1 python /app/scheduler.py
```

Expected output:
```
2025-01-15 14:30:00 - INFO - Starting scheduled ETL transform check...
2025-01-15 14:30:00 - INFO - Found X records in staging_employee
2025-01-15 14:30:00 - INFO - Found Y records in staging_order_detail
2025-01-15 14:30:01 - INFO - Transform request sent successfully
2025-01-15 14:30:05 - INFO - Transform completed: {"employees_transferred": X, "orders_transferred": Y}
```

### Force Transform via API
```bash
curl -X POST http://localhost:8080/api/run-transform-v2
# OR
curl -X POST http://localhost:8080/api/run-transform
```

## Troubleshooting

### Scheduler Not Running

**Check if cron service is running:**
```bash
docker exec etl-rabbitmq-etl-dashboard-1 service cron status
```

**Restart cron service:**
```bash
docker exec etl-rabbitmq-etl-dashboard-1 service cron restart
```

**Verify ENABLE_SCHEDULER:**
```bash
docker exec etl-rabbitmq-etl-dashboard-1 env | grep ENABLE_SCHEDULER
```

### No Logs Generated

**Check cron execution log:**
```bash
docker exec etl-rabbitmq-etl-dashboard-1 cat /app/logs/cron.log
```

**Verify log directory exists:**
```bash
docker exec etl-rabbitmq-etl-dashboard-1 ls -la /app/logs/
```

**Check file permissions:**
```bash
docker exec etl-rabbitmq-etl-dashboard-1 ls -la /app/scheduler.py
# Should show -rwxr-xr-x (executable)
```

### Transform Not Executing

**Check if data exists in staging:**
```bash
docker exec etl-rabbitmq-mysql-1 mysql -uetl_user -petl_password etl_db \
  -e "SELECT COUNT(*) FROM staging_employee; SELECT COUNT(*) FROM staging_order_detail;"
```

**Check dashboard connectivity:**
```bash
docker exec etl-rabbitmq-etl-dashboard-1 curl -s http://localhost:8080 | head -5
```

**Review scheduler log for errors:**
```bash
docker exec etl-rabbitmq-etl-dashboard-1 grep ERROR /app/logs/scheduler_$(date +%Y%m%d).log
```

## Email Notifications

When scheduler runs transform and errors exceed threshold, email notifications are sent automatically if configured:

```bash
# Required environment variables
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TO_EMAIL=admin@yourcompany.com
ERROR_NOTIFICATION_THRESHOLD=10
```

## Best Practices

### 1. Monitor First Runs
After enabling scheduler, monitor logs closely for first 24 hours:
```bash
docker exec etl-rabbitmq-etl-dashboard-1 tail -f /app/logs/scheduler_$(date +%Y%m%d).log
```

### 2. Adjust Schedule Based on Data Volume
- **High volume (1000+ records/hour)**: Run every 15-30 minutes
- **Medium volume (100-1000 records/hour)**: Run every 30-60 minutes
- **Low volume (<100 records/hour)**: Run every 1-2 hours

### 3. Set Up Log Rotation
Default cleanup keeps 30 days. Adjust in `start.sh`:
```bash
# Keep 90 days instead
echo "0 1 * * * find /app/logs -name '*.log' -mtime +90 -delete" | crontab -a
```

### 4. Use Email Notifications
Configure SMTP to get alerts when transforms fail or have high error rates.

### 5. Backup Before Scheduled Runs
Schedule MySQL backups before heavy transform windows:
```bash
# Add to crontab
0 7 * * 1-5 mysqldump -h mysql -u etl_user -petl_password etl_db > /app/logs/backup_$(date +%Y%m%d).sql
```

## Disabling Scheduler

### Temporary Disable (Keep Container Running)
```bash
docker exec etl-rabbitmq-etl-dashboard-1 crontab -r
```

### Permanent Disable
Set in .env or docker-compose.yml:
```bash
ENABLE_SCHEDULER=false
```

Then rebuild:
```bash
docker-compose down
docker-compose up -d etl-dashboard
```

## Performance Tuning

### Reduce CPU Usage
- Increase interval between runs
- Use v2 transform (more efficient rule-based processing)
- Add database indexes on batch_id columns

### Reduce Memory Usage
- Process in smaller batches
- Clear old transform_log entries regularly
- Optimize validation rules (disable unused rules)

## Maintenance

### Weekly Tasks
- Review scheduler logs for patterns
- Check email notification accuracy
- Verify transform success rate

### Monthly Tasks
- Analyze peak usage times
- Adjust schedule based on data patterns
- Archive old logs to external storage
- Review and update validation rules

### Quarterly Tasks
- Performance testing with production-like data volumes
- Review and optimize slow queries
- Update Python dependencies
- Security audit of SMTP credentials

## Support

For issues or questions:
1. Check logs: `/app/logs/scheduler_YYYYMMDD.log`
2. Review cron log: `/app/logs/cron.log`
3. Test manual execution: `python /app/scheduler.py`
4. Check dashboard API: `curl http://localhost:8080/api/history`

## Example .env Configuration

```bash
# MySQL
MYSQL_ROOT_PASSWORD=root_password
MYSQL_DATABASE=etl_db
MYSQL_USER=etl_user
MYSQL_PASSWORD=etl_password

# RabbitMQ
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest

# Email Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=etl-system@company.com
SMTP_PASSWORD=your-app-specific-password
SMTP_TO_EMAIL=data-team@company.com
ERROR_NOTIFICATION_THRESHOLD=15

# Scheduler
ENABLE_SCHEDULER=true
USE_V2_TRANSFORM=true
DASHBOARD_URL=http://localhost:8080
```

**Note:** For Gmail SMTP, generate an "App Password" instead of using your regular password:
1. Go to Google Account Settings
2. Security → 2-Step Verification
3. App passwords → Generate new
4. Use generated password in SMTP_PASSWORD
