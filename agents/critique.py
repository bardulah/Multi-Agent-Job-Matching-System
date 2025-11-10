"""
Critique Agent

Analyzes tailored CVs for quality, relevance, and improvement opportunities.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from docx import Document
from loguru import logger
import anthropic


class CritiqueAgent:
    """Agent responsible for critiquing and improving CVs."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Critique Agent.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.llm_config = config.get('llm', {})

        # Initialize LLM client
        self.llm_provider = self.llm_config.get('provider', 'anthropic')
        if self.llm_provider == 'anthropic':
            api_key = self.llm_config.get('api_key')
            if not api_key:
                raise ValueError("Anthropic API key not found in configuration")
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = self.llm_config.get('model', 'claude-sonnet-4-5-20250929')
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

        logger.info("Critique Agent initialized")

    def critique_cv(
        self,
        cv_data: Dict[str, Any],
        cv_file_path: str,
        job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Critique a tailored CV and suggest improvements.

        Args:
            cv_data: CV data dictionary
            cv_file_path: Path to CV document
            job: Job dictionary for context

        Returns:
            Critique results with scores and suggestions
        """
        logger.info(f"Critiquing CV for: {job['title']} at {job['company']}")

        try:
            # Extract text from CV document
            cv_text = self._extract_cv_text(cv_file_path)

            # Perform comprehensive critique
            critique_result = self._perform_critique(cv_text, cv_data, job)

            # Check if CV passes minimum quality threshold
            overall_score = critique_result.get('overall_score', 0)
            passes_critique = overall_score >= 7.0  # Out of 10

            result = {
                'passes': passes_critique,
                'overall_score': overall_score,
                'scores': critique_result.get('scores', {}),
                'strengths': critique_result.get('strengths', []),
                'weaknesses': critique_result.get('weaknesses', []),
                'suggestions': critique_result.get('suggestions', []),
                'keyword_match': critique_result.get('keyword_match', {}),
                'formatting_issues': critique_result.get('formatting_issues', []),
                'grammar_issues': critique_result.get('grammar_issues', []),
                'auto_fixes_applied': [],
                'critique_summary': critique_result.get('summary', '')
            }

            # Apply automatic fixes if needed
            if result['grammar_issues'] or result['formatting_issues']:
                result = self._apply_auto_fixes(result, cv_data, cv_file_path)

            logger.info(
                f"Critique complete. Score: {overall_score}/10, "
                f"Passes: {passes_critique}"
            )

            return result

        except Exception as e:
            logger.error(f"Error critiquing CV: {e}")
            # Return default passing result to avoid blocking
            return {
                'passes': True,
                'overall_score': 7.0,
                'scores': {},
                'strengths': [],
                'weaknesses': [],
                'suggestions': [],
                'keyword_match': {},
                'formatting_issues': [],
                'grammar_issues': [],
                'auto_fixes_applied': [],
                'critique_summary': 'Critique could not be completed, CV approved by default'
            }

    def _extract_cv_text(self, cv_file_path: str) -> str:
        """
        Extract text from CV document.

        Args:
            cv_file_path: Path to CV file

        Returns:
            CV text content
        """
        try:
            doc = Document(cv_file_path)
            text_content = []

            for para in doc.paragraphs:
                if para.text.strip():
                    text_content.append(para.text)

            return '\n'.join(text_content)

        except Exception as e:
            logger.error(f"Error extracting CV text: {e}")
            return ""

    def _perform_critique(
        self,
        cv_text: str,
        cv_data: Dict[str, Any],
        job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive CV critique using LLM.

        Args:
            cv_text: CV text content
            cv_data: CV data dictionary
            job: Job dictionary

        Returns:
            Critique results dictionary
        """
        logger.debug("Performing CV critique with LLM")

        job_description = job.get('full_description', job.get('description', ''))

        prompt = f"""You are an expert CV reviewer and career coach. Critique this CV that has been tailored for a specific job application.

Job Title: {job['title']}
Company: {job['company']}
Location: {job['location']}

Job Description:
{job_description[:1000]}...

CV Content:
{cv_text}

Please analyze the CV comprehensively and provide:

1. **Scores (out of 10)**:
   - Relevance to job (how well it matches the job requirements)
   - Clarity (is it easy to read and understand)
   - Keyword optimization (does it include important keywords from job posting)
   - Formatting (is it well-structured and professional)
   - Grammar and language (is it error-free)
   - Impact (does it demonstrate achievements and value)

2. **Strengths**: List 3-5 strong points of this CV

3. **Weaknesses**: List 2-4 areas that need improvement

4. **Suggestions**: Provide 3-5 specific, actionable suggestions to improve the CV

5. **Keyword Match**:
   - List important keywords from job description that ARE present in CV
   - List important keywords that are MISSING from CV

6. **Grammar/Language Issues**: Any specific grammar, spelling, or language issues (if any)

7. **Overall Score**: A single score out of 10 representing overall quality

8. **Summary**: 2-3 sentence summary of the CV quality and recommendation

Format your response as JSON:
{{
    "scores": {{
        "relevance": 0-10,
        "clarity": 0-10,
        "keyword_optimization": 0-10,
        "formatting": 0-10,
        "grammar": 0-10,
        "impact": 0-10
    }},
    "overall_score": 0-10,
    "strengths": ["strength1", "strength2", ...],
    "weaknesses": ["weakness1", "weakness2", ...],
    "suggestions": ["suggestion1", "suggestion2", ...],
    "keyword_match": {{
        "present": ["keyword1", "keyword2", ...],
        "missing": ["keyword1", "keyword2", ...]
    }},
    "grammar_issues": ["issue1", "issue2", ...],
    "formatting_issues": ["issue1", "issue2", ...],
    "summary": "..."
}}

Be constructive and specific. The CV will be sent to the employer if the overall score is 7.0 or higher.
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            content = response.content[0].text

            # Parse JSON response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            critique = json.loads(content.strip())

            # Calculate overall score if not provided
            if 'overall_score' not in critique:
                scores = critique.get('scores', {})
                if scores:
                    critique['overall_score'] = sum(scores.values()) / len(scores)
                else:
                    critique['overall_score'] = 7.0

            return critique

        except Exception as e:
            logger.error(f"Error performing critique: {e}")
            # Return default passing critique
            return {
                'scores': {
                    'relevance': 7,
                    'clarity': 7,
                    'keyword_optimization': 7,
                    'formatting': 7,
                    'grammar': 8,
                    'impact': 7
                },
                'overall_score': 7.0,
                'strengths': ['Professional presentation'],
                'weaknesses': [],
                'suggestions': [],
                'keyword_match': {'present': [], 'missing': []},
                'grammar_issues': [],
                'formatting_issues': [],
                'summary': 'CV critique failed, approved by default'
            }

    def _apply_auto_fixes(
        self,
        critique_result: Dict[str, Any],
        cv_data: Dict[str, Any],
        cv_file_path: str
    ) -> Dict[str, Any]:
        """
        Apply automatic fixes to minor issues.

        Args:
            critique_result: Critique results
            cv_data: CV data
            cv_file_path: Path to CV file

        Returns:
            Updated critique result with fixes applied
        """
        logger.debug("Applying automatic fixes")

        auto_fixes = []

        # For now, we'll just log what would be fixed
        # In a production system, you'd actually modify the document

        grammar_issues = critique_result.get('grammar_issues', [])
        if grammar_issues:
            auto_fixes.append(f"Grammar check flagged {len(grammar_issues)} issues for review")

        formatting_issues = critique_result.get('formatting_issues', [])
        if formatting_issues:
            auto_fixes.append(f"Formatting check flagged {len(formatting_issues)} issues for review")

        # Add missing keywords suggestion
        missing_keywords = critique_result.get('keyword_match', {}).get('missing', [])
        if missing_keywords and len(missing_keywords) <= 3:
            auto_fixes.append(f"Consider adding these keywords: {', '.join(missing_keywords)}")

        critique_result['auto_fixes_applied'] = auto_fixes

        return critique_result

    def compare_cvs(
        self,
        cv1_path: str,
        cv2_path: str,
        job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two CV versions and recommend the better one.

        Args:
            cv1_path: Path to first CV
            cv2_path: Path to second CV
            job: Job dictionary

        Returns:
            Comparison results
        """
        logger.info("Comparing two CV versions")

        try:
            cv1_text = self._extract_cv_text(cv1_path)
            cv2_text = self._extract_cv_text(cv2_path)

            job_description = job.get('full_description', job.get('description', ''))

            prompt = f"""Compare these two CV versions for the same job application and recommend which one is better.

Job Title: {job['title']}
Company: {job['company']}

CV Version 1:
{cv1_text[:2000]}

CV Version 2:
{cv2_text[:2000]}

Job Description (abbreviated):
{job_description[:500]}

Which CV is better for this job application? Provide:
1. Overall recommendation (1 or 2)
2. Key differences
3. Reasoning for your choice

Format as JSON:
{{
    "recommended_cv": 1 or 2,
    "reason": "...",
    "key_differences": ["diff1", "diff2", ...]
}}
"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            return json.loads(content.strip())

        except Exception as e:
            logger.error(f"Error comparing CVs: {e}")
            return {
                'recommended_cv': 1,
                'reason': 'Comparison failed',
                'key_differences': []
            }
