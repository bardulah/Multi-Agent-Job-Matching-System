"""
History Manager Module

Tracks job applications and maintains history of processed jobs.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class HistoryManager:
    """Manages job application history and prevents duplicate processing."""

    def __init__(self, history_file: str = "data/history/job_history.json"):
        """
        Initialize the History Manager.

        Args:
            history_file: Path to history JSON file
        """
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        self.history = self._load_history()

        logger.info(f"History Manager initialized with {len(self.history)} entries")

    def _load_history(self) -> Dict[str, Any]:
        """Load history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading history: {e}")
                return {'jobs': {}, 'stats': {}}
        else:
            return {'jobs': {}, 'stats': {}}

    def _save_history(self):
        """Save history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving history: {e}")

    def is_job_processed(self, job_url: str) -> bool:
        """
        Check if a job has already been processed.

        Args:
            job_url: Job URL

        Returns:
            True if already processed, False otherwise
        """
        return job_url in self.history.get('jobs', {})

    def add_job(
        self,
        job: Dict[str, Any],
        match_score: float,
        cv_path: str,
        critique_result: Dict[str, Any],
        status: str = 'processed'
    ):
        """
        Add a job to history.

        Args:
            job: Job dictionary
            match_score: Match score
            cv_path: Path to tailored CV
            critique_result: Critique results
            status: Status (processed, approved, rejected, sent)
        """
        job_url = job['url']

        job_entry = {
            'title': job['title'],
            'company': job['company'],
            'location': job['location'],
            'url': job_url,
            'match_score': match_score,
            'cv_path': cv_path,
            'critique_score': critique_result.get('overall_score', 0),
            'critique_passed': critique_result.get('passes', False),
            'status': status,
            'processed_at': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d')
        }

        if 'jobs' not in self.history:
            self.history['jobs'] = {}

        self.history['jobs'][job_url] = job_entry

        # Update stats
        self._update_stats(status, critique_result.get('passes', False))

        self._save_history()

        logger.debug(f"Added job to history: {job['title']} at {job['company']}")

    def _update_stats(self, status: str, critique_passed: bool):
        """Update statistics."""
        if 'stats' not in self.history:
            self.history['stats'] = {
                'total_processed': 0,
                'total_approved': 0,
                'total_rejected': 0,
                'total_sent': 0
            }

        stats = self.history['stats']
        stats['total_processed'] = stats.get('total_processed', 0) + 1

        if critique_passed:
            stats['total_approved'] = stats.get('total_approved', 0) + 1
        else:
            stats['total_rejected'] = stats.get('total_rejected', 0) + 1

        if status == 'sent':
            stats['total_sent'] = stats.get('total_sent', 0) + 1

    def get_job_history(self, job_url: str) -> Optional[Dict[str, Any]]:
        """
        Get history for a specific job.

        Args:
            job_url: Job URL

        Returns:
            Job history or None
        """
        return self.history.get('jobs', {}).get(job_url)

    def get_recent_jobs(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get jobs processed in the last N days.

        Args:
            days: Number of days

        Returns:
            List of job entries
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_jobs = []

        for job_url, job_entry in self.history.get('jobs', {}).items():
            try:
                processed_at = datetime.fromisoformat(job_entry['processed_at'])
                if processed_at >= cutoff_date:
                    recent_jobs.append(job_entry)
            except Exception:
                continue

        return sorted(recent_jobs, key=lambda x: x['processed_at'], reverse=True)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics.

        Returns:
            Statistics dictionary
        """
        stats = self.history.get('stats', {})

        # Calculate additional stats
        total = stats.get('total_processed', 0)
        approved = stats.get('total_approved', 0)
        rejected = stats.get('total_rejected', 0)

        approval_rate = (approved / total * 100) if total > 0 else 0

        return {
            'total_processed': total,
            'total_approved': approved,
            'total_rejected': rejected,
            'total_sent': stats.get('total_sent', 0),
            'approval_rate': round(approval_rate, 1),
            'total_unique_jobs': len(self.history.get('jobs', {}))
        }

    def cleanup_old_entries(self, retention_days: int = 90):
        """
        Remove entries older than retention period.

        Args:
            retention_days: Number of days to keep
        """
        logger.info(f"Cleaning up entries older than {retention_days} days")

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        jobs_to_remove = []

        for job_url, job_entry in self.history.get('jobs', {}).items():
            try:
                processed_at = datetime.fromisoformat(job_entry['processed_at'])
                if processed_at < cutoff_date:
                    jobs_to_remove.append(job_url)
            except Exception:
                continue

        for job_url in jobs_to_remove:
            del self.history['jobs'][job_url]

        if jobs_to_remove:
            logger.info(f"Removed {len(jobs_to_remove)} old entries")
            self._save_history()

    def export_to_csv(self, output_file: str):
        """
        Export history to CSV file.

        Args:
            output_file: Output CSV file path
        """
        import csv

        logger.info(f"Exporting history to {output_file}")

        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow([
                    'Date', 'Title', 'Company', 'Location', 'URL',
                    'Match Score', 'Critique Score', 'Status', 'CV Path'
                ])

                # Write data
                for job_entry in self.history.get('jobs', {}).values():
                    writer.writerow([
                        job_entry.get('date', ''),
                        job_entry.get('title', ''),
                        job_entry.get('company', ''),
                        job_entry.get('location', ''),
                        job_entry.get('url', ''),
                        job_entry.get('match_score', 0),
                        job_entry.get('critique_score', 0),
                        job_entry.get('status', ''),
                        job_entry.get('cv_path', '')
                    ])

            logger.info(f"History exported successfully to {output_file}")

        except Exception as e:
            logger.error(f"Error exporting history: {e}")
