# scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from housing_scraper import HousingDataCollector
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("housing_scheduler")

# Configure job stores and executors
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}
executors = {
    'default': ThreadPoolExecutor(20),
    'processpool': ProcessPoolExecutor(5)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)

def scrape_all_sources():
    """Job to run all scrapers"""
    logger.info("Starting scheduled scraping job")
    try:
        collector = HousingDataCollector()
        properties_added = collector.run_all_scrapers()
        logger.info(f"Scheduled job completed. Added {properties_added} properties.")
    except Exception as e:
        logger.error(f"Error in scheduled scraping job: {str(e)}")
    finally:
        logger.info("Scheduled job finished")

def setup_scheduler():
    """Set up and start the scheduler"""
    try:
        # Run scraping job daily at 2 AM
        scheduler.add_job(
            scrape_all_sources,
            'cron',
            hour=2,
            minute=0,
            id='daily_scraping'
        )
        
        # Run a quick update every 6 hours
        scheduler.add_job(
            scrape_all_sources,
            'interval',
            hours=6,
            id='update_scraping'
        )
        
        scheduler.start()
        logger.info("Scheduler started")
    except Exception as e:
        logger.error(f"Error setting up scheduler: {str(e)}")

if __name__ == "__main__":
    setup_scheduler()
    
    # Keep the script running
    try:
        import time
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler shut down")