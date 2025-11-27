"""
Notification Agent

Handles approval workflow and sends notifications with tailored CVs.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger


class NotificationAgent:
    """Agent responsible for approval workflow and sending notifications."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Notification Agent.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.email_config = config.get('email', {})
        self.system_config = config.get('system', {})
        self.user_info = config.get('user', {})

        self.smtp_server = self.email_config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = self.email_config.get('smtp_port', 587)
        self.use_tls = self.email_config.get('use_tls', True)
        self.sender_email = self.email_config.get('sender_email')
        self.sender_password = self.email_config.get('sender_password')
        self.smtp_user = self.email_config.get('smtp_user', self.sender_email)
        self.recipient_email = self.email_config.get('recipient_email', self.sender_email)

        self.enable_auto_send = self.system_config.get('enable_auto_send', False)

        logger.info(f"Notification Agent initialized (auto-send: {self.enable_auto_send})")

    def process_approved_jobs(
        self,
        job_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process approved jobs and send notification.

        Args:
            job_results: List of job application results (job, CV, critique)

        Returns:
            Processing results with status
        """
        logger.info(f"Processing {len(job_results)} job applications")

        # Filter for approved jobs (passed critique)
        approved_jobs = [
            result for result in job_results
            if result.get('critique', {}).get('passes', False)
        ]

        logger.info(f"{len(approved_jobs)} jobs passed critique and are approved")

        if not approved_jobs:
            logger.warning("No jobs passed critique. No notification will be sent.")
            return {
                'status': 'no_approved_jobs',
                'total_processed': len(job_results),
                'approved': 0,
                'rejected': len(job_results),
                'notification_sent': False
            }

        # Compile daily summary
        summary = self._compile_daily_summary(approved_jobs, job_results)

        # Send notification
        if self.enable_auto_send:
            notification_result = self._send_notification(approved_jobs, summary)
        else:
            logger.info("Auto-send disabled. Saving results for manual review.")
            notification_result = self._save_for_review(approved_jobs, summary)

        return {
            'status': 'success',
            'total_processed': len(job_results),
            'approved': len(approved_jobs),
            'rejected': len(job_results) - len(approved_jobs),
            'notification_sent': notification_result['sent'],
            'notification_method': notification_result['method'],
            'summary': summary
        }

    def _compile_daily_summary(
        self,
        approved_jobs: List[Dict[str, Any]],
        all_jobs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compile a daily summary of job applications.

        Args:
            approved_jobs: List of approved job results
            all_jobs: List of all processed job results

        Returns:
            Summary dictionary
        """
        summary = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_jobs_found': len(all_jobs),
            'approved_count': len(approved_jobs),
            'rejected_count': len(all_jobs) - len(approved_jobs),
            'approved_jobs': []
        }

        for result in approved_jobs:
            job = result['job']
            cv = result['cv']
            critique = result['critique']

            job_summary = {
                'title': job['title'],
                'company': job['company'],
                'location': job['location'],
                'url': job['url'],
                'salary': job.get('salary'),
                'match_score': result.get('match_score', 0),
                'cv_path': cv['file_path'],
                'critique_score': critique['overall_score'],
                'key_strengths': critique.get('strengths', [])[:3],
                'suggestions': critique.get('suggestions', [])[:3]
            }

            summary['approved_jobs'].append(job_summary)

        return summary

    def _send_notification(
        self,
        approved_jobs: List[Dict[str, Any]],
        summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send email notification with approved job applications.

        Args:
            approved_jobs: List of approved job results
            summary: Daily summary

        Returns:
            Send result
        """
        logger.info(f"Sending email notification to {self.recipient_email}")

        try:
            # Create email message
            msg = MIMEMultipart()
            msg['Subject'] = f"Daily Job Applications - {summary['approved_count']} Opportunities ({summary['date']})"
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email

            # Create email body
            body = self._create_email_body(summary)
            msg.attach(MIMEText(body, 'html'))

            # Attach CVs
            for result in approved_jobs:
                cv_path = result['cv']['file_path']
                self._attach_file(msg, cv_path)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                if self.sender_password:
                    server.login(self.smtp_user, self.sender_password)

                server.send_message(msg)

            logger.info("Email notification sent successfully")

            return {
                'sent': True,
                'method': 'email',
                'recipient': self.recipient_email,
                'attachments_count': len(approved_jobs)
            }

        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return {
                'sent': False,
                'method': 'email',
                'error': str(e)
            }

    def _save_for_review(
        self,
        approved_jobs: List[Dict[str, Any]],
        summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save results for manual review instead of auto-sending.

        Args:
            approved_jobs: List of approved job results
            summary: Daily summary

        Returns:
            Save result
        """
        logger.info("Saving results for manual review")

        try:
            # Create review directory
            review_dir = Path("data/review") / summary['date']
            review_dir.mkdir(parents=True, exist_ok=True)

            # Save summary as HTML
            html_body = self._create_email_body(summary)
            summary_file = review_dir / "summary.html"
            summary_file.write_text(html_body, encoding='utf-8')

            # Create text file with job details
            jobs_file = review_dir / "jobs.txt"
            with open(jobs_file, 'w', encoding='utf-8') as f:
                f.write(f"Daily Job Applications Review - {summary['date']}\n")
                f.write("=" * 80 + "\n\n")

                for i, result in enumerate(approved_jobs, 1):
                    job = result['job']
                    cv = result['cv']
                    critique = result['critique']

                    f.write(f"{i}. {job['title']} at {job['company']}\n")
                    f.write(f"   Location: {job['location']}\n")
                    f.write(f"   URL: {job['url']}\n")
                    f.write(f"   Match Score: {result.get('match_score', 0):.2f}\n")
                    f.write(f"   Critique Score: {critique['overall_score']:.1f}/10\n")
                    f.write(f"   CV: {cv['file_path']}\n")
                    f.write("\n")

            logger.info(f"Results saved to: {review_dir}")

            return {
                'sent': False,
                'method': 'saved_for_review',
                'review_path': str(review_dir),
                'jobs_count': len(approved_jobs)
            }

        except Exception as e:
            logger.error(f"Error saving results for review: {e}")
            return {
                'sent': False,
                'method': 'saved_for_review',
                'error': str(e)
            }

    def _create_email_body(self, summary: Dict[str, Any]) -> str:
        """
        Create HTML email body.

        Args:
            summary: Daily summary dictionary

        Returns:
            HTML email body
        """
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                .summary {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .job {{ background-color: #fff; border: 1px solid #bdc3c7; border-radius: 5px; padding: 15px; margin: 15px 0; }}
                .job-title {{ color: #2980b9; font-size: 18px; font-weight: bold; }}
                .company {{ color: #7f8c8d; font-size: 14px; }}
                .score {{ display: inline-block; background-color: #27ae60; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold; }}
                .score.good {{ background-color: #27ae60; }}
                .score.average {{ background-color: #f39c12; }}
                .suggestions {{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin-top: 10px; }}
                ul {{ margin: 10px 0; }}
                li {{ margin: 5px 0; }}
                .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #bdc3c7; color: #7f8c8d; font-size: 12px; }}
            </style>
        </head>
        <body>
            <h1>🎯 Daily Job Application Report</h1>

            <div class="summary">
                <h2>Summary for {summary['date']}</h2>
                <p><strong>Total Jobs Analyzed:</strong> {summary['total_jobs_found']}</p>
                <p><strong>Approved Applications:</strong> {summary['approved_count']}</p>
                <p><strong>Filtered Out:</strong> {summary['rejected_count']}</p>
            </div>

            <h2>✅ Approved Job Applications</h2>
            <p>The following jobs have been matched, tailored CVs created, and passed quality review:</p>
        """

        for i, job_info in enumerate(summary['approved_jobs'], 1):
            score_class = 'good' if job_info['critique_score'] >= 8 else 'average'

            html += f"""
            <div class="job">
                <div class="job-title">{i}. {job_info['title']}</div>
                <div class="company">{job_info['company']} - {job_info['location']}</div>

                <p>
                    <strong>Match Score:</strong> <span class="score {score_class}">{job_info['match_score']:.0%}</span>
                    <strong>CV Quality Score:</strong> <span class="score {score_class}">{job_info['critique_score']:.1f}/10</span>
                </p>

                <p><strong>🔗 Job URL:</strong> <a href="{job_info['url']}">{job_info['url']}</a></p>

                {f"<p><strong>💰 Salary:</strong> {job_info['salary']}</p>" if job_info.get('salary') else ""}

                <p><strong>✨ CV Strengths:</strong></p>
                <ul>
            """

            for strength in job_info.get('key_strengths', []):
                html += f"<li>{strength}</li>"

            html += "</ul>"

            if job_info.get('suggestions'):
                html += '<div class="suggestions"><strong>💡 Suggestions for improvement:</strong><ul>'
                for suggestion in job_info['suggestions']:
                    html += f"<li>{suggestion}</li>"
                html += "</ul></div>"

            html += f"""
                <p><strong>📄 Tailored CV:</strong> {Path(job_info['cv_path']).name} (attached)</p>
            </div>
            """

        html += f"""
            <div class="footer">
                <p>This report was generated automatically by the Multi-Agent Job Application System.</p>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """

        return html

    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """
        Attach a file to email message.

        Args:
            msg: Email message object
            file_path: Path to file to attach
        """
        try:
            with open(file_path, 'rb') as f:
                attachment = MIMEApplication(f.read())
                filename = Path(file_path).name
                attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                msg.attach(attachment)
        except Exception as e:
            logger.error(f"Error attaching file {file_path}: {e}")

    def send_test_email(self) -> bool:
        """
        Send a test email to verify configuration.

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Sending test email to {self.recipient_email}")

        try:
            msg = MIMEText("This is a test email from the Multi-Agent Job Application System.")
            msg['Subject'] = "Test Email - Job Application System"
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                if self.sender_password:
                    server.login(self.smtp_user, self.sender_password)

                server.send_message(msg)

            logger.info("Test email sent successfully")
            return True

        except Exception as e:
            logger.error(f"Error sending test email: {e}")
            return False
