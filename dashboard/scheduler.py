#!/usr/bin/env python3
"""
ETL Scheduled Jobs - Auto Transform Runner
Run this script with cron to automatically execute transforms
"""

import requests
import json
import logging
from datetime import datetime
import os
import sys

# Configure logging
log_dir = '/app/logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"scheduler_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Configuration
DASHBOARD_URL = os.environ.get('DASHBOARD_URL', 'http://localhost:8080')
USE_V2_TRANSFORM = os.environ.get('USE_V2_TRANSFORM', 'true').lower() == 'true'

def check_staging_records():
    """Check if there are records in staging tables"""
    try:
        logger.info("Checking for records in staging tables...")
        
        # This would ideally query the database, but for simplicity we'll use the API
        response = requests.get(f"{DASHBOARD_URL}/api/staging/employee/errors?limit=1", timeout=10)
        
        if response.status_code == 200:
            logger.info("Staging tables accessible")
            return True
        else:
            logger.warning(f"Could not access staging tables: {response.status_code}")
            return False
    
    except Exception as e:
        logger.error(f"Error checking staging records: {str(e)}")
        return False

def run_transform():
    """Execute transform operation"""
    try:
        endpoint = '/api/run-transform-v2' if USE_V2_TRANSFORM else '/api/run-transform'
        url = f"{DASHBOARD_URL}{endpoint}"
        
        logger.info(f"Starting scheduled transform via {endpoint}...")
        
        response = requests.post(url, json={}, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                logger.info(f"Transform completed successfully:")
                logger.info(f"  - Employees transferred: {result.get('employees', 0)}")
                logger.info(f"  - Orders transferred: {result.get('orders', 0)}")
                logger.info(f"  - Errors: {result.get('errors', 0)}")
                logger.info(f"  - Batch ID: {result.get('batch_id', 'N/A')}")
                logger.info(f"  - Processing time: {result.get('processing_time_ms', 0)}ms")
                
                # Check if errors exceeded threshold
                if result.get('errors', 0) > 10:
                    logger.warning(f"⚠️  High error count: {result.get('errors')} errors detected!")
                
                return True
            else:
                logger.error(f"Transform failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            logger.error(f"Transform request failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        logger.error("Transform request timed out (300s)")
        return False
    
    except Exception as e:
        logger.error(f"Error running transform: {str(e)}")
        return False

def main():
    """Main scheduler function"""
    logger.info("=" * 60)
    logger.info("ETL Scheduled Job Started")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Dashboard URL: {DASHBOARD_URL}")
    logger.info(f"Using Transform V2: {USE_V2_TRANSFORM}")
    logger.info("=" * 60)
    
    try:
        # Check if staging has records
        has_records = check_staging_records()
        
        if has_records:
            # Run transform
            success = run_transform()
            
            if success:
                logger.info("✅ Scheduled job completed successfully")
                sys.exit(0)
            else:
                logger.error("❌ Scheduled job failed")
                sys.exit(1)
        else:
            logger.info("ℹ️  No records to process, skipping transform")
            sys.exit(0)
    
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
