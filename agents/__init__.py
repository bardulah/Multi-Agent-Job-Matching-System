"""
Multi-Agent Job Application System

This package contains all the agents for the automated job application system.
"""

from .job_fetcher import JobFetcherAgent
from .cv_tailor import CVTailorAgent
from .critique import CritiqueAgent
from .notification import NotificationAgent

__all__ = [
    'JobFetcherAgent',
    'CVTailorAgent',
    'CritiqueAgent',
    'NotificationAgent',
]
