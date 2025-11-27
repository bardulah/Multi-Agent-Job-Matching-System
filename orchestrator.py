"""
Main Orchestrator

Coordinates all agents to process jobs daily.
"""

import sys
from typing import Dict, Any, List
from pathlib import Path
from loguru import logger

from utils.config_loader import ConfigLoader
from utils.logger import setup_logger
from utils.job_matcher import JobMatcher
from utils.history_manager import HistoryManager
from agents.job_fetcher import JobFetcherAgent
from agents.cv_tailor import CVTailorAgent
from agents.cv_template_tailor import CVTemplateTailorAgent
from agents.critique import CritiqueAgent
from agents.notification import NotificationAgent


class JobApplicationOrchestrator:
    """Main orchestrator that coordinates all agents."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the orchestrator.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = ConfigLoader(config_path)

        # Setup logging
        log_level = self.config.get('system.log_level', 'INFO')
        setup_logger(log_level=log_level)

        logger.info("=" * 80)
        logger.info("Job Application System Starting")
        logger.info("=" * 80)

        # Initialize components
        self.job_matcher = JobMatcher(
            self.config.get_section('skills'),
            self.config.get_section('job_preferences')
        )
        self.history_manager = HistoryManager()

        # Initialize agents
        self.job_fetcher = JobFetcherAgent(self.config.config)

        # Choose CV tailoring approach
        use_template = self.config.get('cv.use_template', False)
        if use_template:
            logger.info("📋 Using Approach 3: Template-based CV (your actual CV + customization)")
            self.cv_tailor = CVTemplateTailorAgent(self.config.config)
        else:
            logger.info("✏️  Using Approach 1: Generated CV from config data")
            self.cv_tailor = CVTailorAgent(self.config.config)

        self.critique_agent = CritiqueAgent(self.config.config)
        self.notification_agent = NotificationAgent(self.config.config)

        # System settings
        self.max_jobs = self.config.get('system.max_jobs_per_day', 10)
        self.min_match_score = self.config.get('system.min_match_score', 0.6)

        logger.info("Orchestrator initialized successfully")

    def run_daily_cycle(self) -> Dict[str, Any]:
        """
        Run the complete daily job application cycle.

        Returns:
            Results dictionary
        """
        logger.info("Starting daily job application cycle")

        try:
            # Step 1: Fetch jobs
            logger.info("Step 1: Fetching jobs from profesia.sk")
            jobs = self.job_fetcher.fetch_jobs()

            if not jobs:
                logger.warning("No jobs found. Cycle complete.")
                return {
                    'status': 'no_jobs_found',
                    'jobs_fetched': 0,
                    'jobs_processed': 0,
                    'jobs_approved': 0
                }

            logger.info(f"Fetched {len(jobs)} jobs")

            # Step 2: Filter and match jobs
            logger.info("Step 2: Filtering and matching jobs")
            matched_jobs = self._filter_and_match_jobs(jobs)

            if not matched_jobs:
                logger.warning("No jobs matched preferences. Cycle complete.")
                return {
                    'status': 'no_matches',
                    'jobs_fetched': len(jobs),
                    'jobs_processed': 0,
                    'jobs_approved': 0
                }

            logger.info(f"{len(matched_jobs)} jobs matched preferences")

            # Limit to max jobs per day
            if len(matched_jobs) > self.max_jobs:
                logger.info(f"Limiting to {self.max_jobs} top matches")
                matched_jobs = matched_jobs[:self.max_jobs]

            # Step 3: Enrich jobs with full descriptions
            logger.info("Step 3: Fetching full job descriptions")
            matched_jobs = self.job_fetcher.enrich_jobs_with_details(matched_jobs)

            # Step 4: Process each job (tailor CV, critique, track)
            logger.info("Step 4: Processing jobs (tailoring CVs and critiquing)")
            job_results = self._process_jobs(matched_jobs)

            # Step 5: Send notifications
            logger.info("Step 5: Processing notifications")
            notification_result = self.notification_agent.process_approved_jobs(job_results)

            # Step 6: Cleanup old history
            retention_days = self.config.get('system.data_retention_days', 90)
            self.history_manager.cleanup_old_entries(retention_days)

            # Compile final results
            stats = self.history_manager.get_statistics()

            final_result = {
                'status': 'success',
                'jobs_fetched': len(jobs),
                'jobs_matched': len(matched_jobs),
                'jobs_processed': len(job_results),
                'jobs_approved': notification_result['approved'],
                'jobs_rejected': notification_result['rejected'],
                'notification_sent': notification_result['notification_sent'],
                'statistics': stats
            }

            logger.info("=" * 80)
            logger.info("Daily cycle complete")
            logger.info(f"Jobs fetched: {final_result['jobs_fetched']}")
            logger.info(f"Jobs matched: {final_result['jobs_matched']}")
            logger.info(f"Jobs processed: {final_result['jobs_processed']}")
            logger.info(f"Jobs approved: {final_result['jobs_approved']}")
            logger.info(f"Notification sent: {final_result['notification_sent']}")
            logger.info("=" * 80)

            return final_result

        except Exception as e:
            logger.error(f"Error in daily cycle: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'jobs_processed': 0
            }

    def _filter_and_match_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter jobs and calculate match scores.

        Args:
            jobs: List of job dictionaries

        Returns:
            List of matched jobs with scores, sorted by match score
        """
        matched_jobs = []

        for job in jobs:
            # Skip if already processed
            if self.history_manager.is_job_processed(job['url']):
                logger.debug(f"Skipping already processed job: {job['title']}")
                continue

            # Calculate match score
            match_score = self.job_matcher.calculate_match_score(job)

            if match_score >= self.min_match_score:
                job['match_score'] = match_score
                matched_jobs.append(job)
                logger.debug(
                    f"Job matched: {job['title']} at {job['company']} "
                    f"(score: {match_score:.2f})"
                )
            else:
                logger.debug(
                    f"Job filtered out: {job['title']} "
                    f"(score: {match_score:.2f} < {self.min_match_score})"
                )

        # Sort by match score (highest first)
        matched_jobs.sort(key=lambda x: x['match_score'], reverse=True)

        return matched_jobs

    def _process_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process each job: tailor CV, critique, and track.

        Args:
            jobs: List of matched job dictionaries

        Returns:
            List of job results
        """
        results = []

        for i, job in enumerate(jobs, 1):
            logger.info(f"Processing job {i}/{len(jobs)}: {job['title']} at {job['company']}")

            try:
                # Tailor CV
                logger.info("  → Tailoring CV...")
                cv_result = self.cv_tailor.tailor_cv(job)

                # Critique CV
                logger.info("  → Critiquing CV...")
                # Handle both template-based and generated CVs
                cv_data = cv_result.get('cv_data', {})  # Generated CVs
                file_path = cv_result.get('cv_path') or cv_result.get('file_path')  # Both types

                critique_result = self.critique_agent.critique_cv(
                    cv_data,
                    file_path,
                    job
                )

                # Determine status
                status = 'approved' if critique_result['passes'] else 'rejected'

                # Add to history
                # Handle both template-based and generated CVs (different key names)
                cv_path = cv_result.get('cv_path') or cv_result.get('file_path')
                self.history_manager.add_job(
                    job,
                    job['match_score'],
                    cv_path,
                    critique_result,
                    status=status
                )

                result = {
                    'job': job,
                    'cv': cv_result,
                    'critique': critique_result,
                    'match_score': job['match_score'],
                    'status': status
                }

                results.append(result)

                logger.info(
                    f"  ✓ Job processed. "
                    f"Match: {job['match_score']:.0%}, "
                    f"Critique: {critique_result['overall_score']:.1f}/10, "
                    f"Status: {status}"
                )

            except Exception as e:
                logger.error(f"  ✗ Error processing job: {e}")
                continue

        return results

    def test_configuration(self) -> bool:
        """
        Test system configuration.

        Returns:
            True if all tests pass, False otherwise
        """
        logger.info("Testing system configuration...")

        all_passed = True

        # Test 1: Configuration loaded
        logger.info("✓ Configuration loaded successfully")

        # Test 2: Check LLM API key
        try:
            llm_key = self.config.get('llm.api_key')
            if llm_key:
                logger.info("✓ LLM API key found")
            else:
                logger.error("✗ LLM API key not found")
                all_passed = False
        except Exception as e:
            logger.error(f"✗ Error checking LLM API key: {e}")
            all_passed = False

        # Test 3: Check email configuration
        try:
            email_addr = self.config.get('email.sender_email')
            email_pass = self.config.get('email.sender_password')

            if email_addr and email_pass:
                logger.info("✓ Email credentials found")

                # Test email send
                logger.info("Testing email send...")
                if self.notification_agent.send_test_email():
                    logger.info("✓ Test email sent successfully")
                else:
                    logger.warning("⚠ Test email failed (check credentials)")
            else:
                logger.warning("⚠ Email credentials not fully configured")
        except Exception as e:
            logger.warning(f"⚠ Email test skipped: {e}")

        # Test 4: Check directories
        required_dirs = ['data/jobs', 'data/cvs', 'data/history', 'logs']
        for dir_path in required_dirs:
            if Path(dir_path).exists():
                logger.info(f"✓ Directory exists: {dir_path}")
            else:
                logger.warning(f"⚠ Directory missing: {dir_path} (will be created)")

        if all_passed:
            logger.info("=" * 80)
            logger.info("✓ All configuration tests passed!")
            logger.info("=" * 80)
        else:
            logger.error("=" * 80)
            logger.error("✗ Some configuration tests failed")
            logger.error("=" * 80)

        return all_passed


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Agent Job Application System")
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test configuration and exit'
    )

    args = parser.parse_args()

    try:
        orchestrator = JobApplicationOrchestrator(config_path=args.config)

        if args.test:
            # Run configuration tests
            success = orchestrator.test_configuration()
            sys.exit(0 if success else 1)
        else:
            # Run daily cycle
            result = orchestrator.run_daily_cycle()
            sys.exit(0 if result['status'] in ['success', 'no_jobs_found', 'no_matches'] else 1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
