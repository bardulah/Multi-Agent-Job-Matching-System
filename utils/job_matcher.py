"""
Job Matcher Module

Calculates match scores between job postings and user preferences/skills.
"""

from typing import Dict, List, Set, Any
import re


class JobMatcher:
    """Matches jobs against user preferences and skills."""

    def __init__(self, user_skills: Dict[str, List[str]], preferences: Dict[str, Any]):
        """
        Initialize the job matcher.

        Args:
            user_skills: User's skills from configuration
            preferences: Job preferences from configuration
        """
        self.user_skills = user_skills
        self.preferences = preferences

        # Flatten all skills into a single set for matching
        self.all_skills = set()
        for skill_category in user_skills.values():
            if isinstance(skill_category, list):
                self.all_skills.update(s.lower() for s in skill_category)

        # Prepare keywords
        self.required_keywords = set(k.lower() for k in preferences.get('keywords', []))
        self.excluded_keywords = set(k.lower() for k in preferences.get('excluded_keywords', []))

    def calculate_match_score(self, job: Dict[str, Any]) -> float:
        """
        Calculate how well a job matches user preferences.

        Args:
            job: Job posting dictionary

        Returns:
            Match score between 0.0 and 1.0
        """
        score = 0.0
        weights = {
            'keywords': 0.3,
            'skills': 0.4,
            'location': 0.15,
            'employment_type': 0.15
        }

        # Combine title and description for analysis
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()

        # Check for excluded keywords (instant disqualification)
        if self._has_excluded_keywords(job_text):
            return 0.0

        # 1. Keyword matching
        keyword_score = self._calculate_keyword_score(job_text)
        score += keyword_score * weights['keywords']

        # 2. Skills matching
        skills_score = self._calculate_skills_score(job_text)
        score += skills_score * weights['skills']

        # 3. Location matching
        location_score = self._calculate_location_score(job.get('location', ''))
        score += location_score * weights['location']

        # 4. Employment type matching
        employment_score = self._calculate_employment_score(job.get('employment_type', ''))
        score += employment_score * weights['employment_type']

        return round(score, 2)

    def _has_excluded_keywords(self, text: str) -> bool:
        """Check if text contains any excluded keywords."""
        for keyword in self.excluded_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                return True
        return False

    def _calculate_keyword_score(self, text: str) -> float:
        """Calculate score based on required keywords."""
        if not self.required_keywords:
            return 1.0

        matches = 0
        for keyword in self.required_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                matches += 1

        return matches / len(self.required_keywords)

    def _calculate_skills_score(self, text: str) -> float:
        """Calculate score based on skills matching."""
        if not self.all_skills:
            return 1.0

        matches = 0
        for skill in self.all_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                matches += 1

        return min(matches / max(len(self.all_skills) * 0.3, 1), 1.0)

    def _calculate_location_score(self, location: str) -> float:
        """Calculate score based on location preferences."""
        preferred_locations = self.preferences.get('locations', [])
        if not preferred_locations:
            return 1.0

        location_lower = location.lower()
        for pref_location in preferred_locations:
            if pref_location.lower() in location_lower:
                return 1.0

        return 0.0

    def _calculate_employment_score(self, employment_type: str) -> float:
        """Calculate score based on employment type preferences."""
        preferred_types = self.preferences.get('employment_types', [])
        if not preferred_types:
            return 1.0

        employment_lower = employment_type.lower()
        for pref_type in preferred_types:
            if pref_type.lower() in employment_lower:
                return 1.0

        return 0.5  # Partial score if not exact match

    def get_matching_skills(self, job_description: str) -> List[str]:
        """
        Extract which user skills are mentioned in the job description.

        Args:
            job_description: Job description text

        Returns:
            List of matching skills
        """
        matching = []
        job_text_lower = job_description.lower()

        for skill in self.all_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', job_text_lower, re.IGNORECASE):
                matching.append(skill)

        return matching
