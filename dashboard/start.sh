#!/bin/bash

# Start cron service
service cron start

# Setup cron job if environment variable is set
if [ ! -z "$ENABLE_SCHEDULER" ] && [ "$ENABLE_SCHEDULER" = "true" ]; then
    echo "Setting up scheduled ETL jobs..."
    
    # Create crontab entry
    # Run transform every 30 minutes during business hours (8 AM - 6 PM, Mon-Fri)
    echo "*/30 8-18 * * 1-5 cd /app && /usr/local/bin/python /app/scheduler.py >> /app/logs/cron.log 2>&1" | crontab -
    
    # Run transform hourly outside business hours
    echo "0 19-23,0-7 * * * cd /app && /usr/local/bin/python /app/scheduler.py >> /app/logs/cron.log 2>&1" | crontab -a
    
    # Clean up old logs (keep last 30 days)
    echo "0 1 * * * find /app/logs -name 'etl_*.log' -mtime +30 -delete" | crontab -a
    echo "0 1 * * * find /app/logs -name 'scheduler_*.log' -mtime +30 -delete" | crontab -a
    
    echo "Cron jobs configured:"
    crontab -l
else
    echo "Scheduler disabled (set ENABLE_SCHEDULER=true to enable)"
fi

# Start Flask application
echo "Starting Flask dashboard on port $PORT..."
python app.py
