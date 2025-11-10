"""
Scheduler Module

Alternative to cron - runs the system on a schedule using Python's schedule library.
"""

import schedule
import time
from datetime import datetime
from loguru import logger
from orchestrator import JobApplicationOrchestrator


def run_job():
    """Run the daily job application cycle."""
    logger.info(f"Scheduled run started at {datetime.now()}")

    try:
        orchestrator = JobApplicationOrchestrator()
        result = orchestrator.run_daily_cycle()

        logger.info(f"Scheduled run completed with status: {result['status']}")

    except Exception as e:
        logger.error(f"Error in scheduled run: {e}", exc_info=True)


def main():
    """Main scheduler loop."""
    # Configure logger
    from utils.logger import setup_logger
    setup_logger(log_level="INFO")

    logger.info("Job Application System Scheduler Starting")

    # Schedule daily run at 8:00 AM
    schedule.every().day.at("08:00").do(run_job)

    logger.info("Scheduled to run daily at 08:00")
    logger.info("Press Ctrl+C to stop")

    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")


if __name__ == '__main__':
    main()
