"""Agents package for the multi-agent job matching system."""
from .base_agent import BaseAgent
from .scraper_agent import ScraperAgent
from .matcher_agent import MatcherAgent
from .critique_agent import CritiqueAgent
from .cv_tailor_agent import CVTailorAgent
from .notification_agent import NotificationAgent

__all__ = [
    'BaseAgent',
    'ScraperAgent',
    'MatcherAgent',
    'CritiqueAgent',
    'CVTailorAgent',
    'NotificationAgent'
]
