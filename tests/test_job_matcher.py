"""
Tests for JobMatcher
"""

import pytest
from utils.job_matcher import JobMatcher


def test_job_matcher_basic():
    """Test basic job matching."""
    skills = {
        'programming_languages': ['Python', 'JavaScript'],
        'frameworks': ['Django', 'React']
    }

    preferences = {
        'keywords': ['Python', 'Backend'],
        'excluded_keywords': ['Manager'],
        'locations': ['Bratislava', 'Remote'],
        'employment_types': ['full-time']
    }

    matcher = JobMatcher(skills, preferences)

    job = {
        'title': 'Python Backend Developer',
        'description': 'We are looking for a Python developer with Django experience.',
        'location': 'Bratislava',
        'employment_type': 'full-time'
    }

    score = matcher.calculate_match_score(job)

    # Should have a good match score
    assert score >= 0.7
    assert score <= 1.0


def test_job_matcher_excluded_keywords():
    """Test that excluded keywords result in zero score."""
    skills = {'programming_languages': ['Python']}
    preferences = {
        'keywords': ['Developer'],
        'excluded_keywords': ['Senior Manager']
    }

    matcher = JobMatcher(skills, preferences)

    job = {
        'title': 'Senior Manager of Engineering',
        'description': 'Managing a team of developers.',
        'location': 'Bratislava',
        'employment_type': 'full-time'
    }

    score = matcher.calculate_match_score(job)

    # Should be excluded
    assert score == 0.0


def test_get_matching_skills():
    """Test extracting matching skills."""
    skills = {
        'programming_languages': ['Python', 'JavaScript', 'Java'],
        'frameworks': ['Django', 'React']
    }

    preferences = {'keywords': []}

    matcher = JobMatcher(skills, preferences)

    job_description = """
    We are looking for a developer with Python and Django experience.
    Knowledge of React is a plus.
    """

    matching = matcher.get_matching_skills(job_description)

    assert 'python' in matching
    assert 'django' in matching
    assert 'react' in matching
    assert 'java' not in matching


if __name__ == '__main__':
    pytest.main([__file__])
