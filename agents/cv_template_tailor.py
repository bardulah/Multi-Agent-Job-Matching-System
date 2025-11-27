"""
CV Template Tailoring Agent

Uses your actual CV as a template and customizes specific sections
for each job rather than generating from scratch.

This preserves your authentic voice while highlighting relevant experience.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor
from loguru import logger

from llm import create_llm_client, BaseLLMClient


class CVTemplateTailorAgent:
    """Agent that customizes your existing CV for specific jobs."""

    def __init__(self, config: Dict[str, Any], llm_client: Optional[BaseLLMClient] = None):
        """
        Initialize the CV Template Tailor Agent.

        Args:
            config: Configuration dictionary
            llm_client: Optional pre-configured LLM client (for testing/DI)
        """
        self.config = config
        self.llm_config = config.get('llm', {})

        # Get path to your actual CV from config
        self.base_cv_path = config.get('cv', {}).get('template_path', 'cv.pdf')

        if not Path(self.base_cv_path).exists():
            raise FileNotFoundError(f"CV template not found at: {self.base_cv_path}")

        # Initialize LLM client (model-agnostic)
        if llm_client:
            self.llm_client = llm_client
        else:
            self.llm_client = create_llm_client(self.llm_config)

        # Ensure output directory exists
        self.output_dir = Path("data/cvs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"CV Template Tailor Agent initialized with {self.llm_client.provider_name} "
            f"({self.llm_client.model})"
        )
        logger.info(f"Base CV template: {self.base_cv_path}")

    def tailor_cv(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tailor your existing CV for a specific job posting.

        This approach:
        1. Extracts text from your actual CV
        2. Analyzes job requirements
        3. Creates customized version highlighting relevant sections
        4. Preserves your authentic voice and experience

        Args:
            job: Job dictionary with description and requirements

        Returns:
            Dictionary with tailored CV data and file path
        """
        logger.info(f"Tailoring CV for: {job['title']} at {job['company']}")

        try:
            # Extract your actual CV content
            cv_content = self._extract_cv_content()

            # Analyze job requirements
            job_analysis = self._analyze_job_requirements(job)

            # Generate customization notes (what to emphasize)
            customization_prompt = self._generate_customization_prompt(
                cv_content,
                job,
                job_analysis
            )

            # Get LLM suggestions for what to emphasize
            emphasis_suggestions = self._get_emphasis_suggestions(
                customization_prompt,
                cv_content,
                job
            )

            # Create customized CV document
            output_path = self._create_customized_cv(
                cv_content,
                job,
                emphasis_suggestions
            )

            result = {
                'cv_path': str(output_path),
                'job_title': job['title'],
                'company': job['company'],
                'emphasis': emphasis_suggestions.get('sections_to_emphasize', []),
                'relevant_skills': job_analysis.get('key_skills', []),
                'tailoring_summary': emphasis_suggestions.get('summary', ''),
                'created_at': datetime.now().isoformat()
            }

            logger.info(f"CV tailored successfully: {output_path}")
            return result

        except Exception as e:
            logger.error(f"Error tailoring CV: {e}", exc_info=True)
            raise

    def _extract_cv_content(self) -> str:
        """
        Extract text content from your actual CV.

        Returns:
            Full text content of your CV
        """
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(self.base_cv_path)
            content = ""
            for page in reader.pages:
                content += page.extract_text() + "\n"

            logger.info(f"Extracted {len(content)} characters from CV")
            return content

        except Exception as e:
            logger.error(f"Error extracting CV content: {e}")
            raise

    def _analyze_job_requirements(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze what skills/requirements the job is asking for.

        Args:
            job: Job posting dictionary

        Returns:
            Analysis of key requirements
        """
        prompt = f"""
Analyze this job posting and extract the key technical skills and requirements.
Return ONLY a JSON object with these fields:
- key_skills: list of 5-10 main technical skills required
- experience_level: junior/mid/senior
- industry: industry focus
- must_haves: critical requirements
- nice_to_haves: optional skills

Job Title: {job.get('title', '')}
Company: {job.get('company', '')}
Description: {job.get('description', '')[:500]}
"""

        response = self.llm_client.generate(prompt)

        try:
            import json
            analysis = json.loads(response)
        except:
            # Fallback if JSON parsing fails
            analysis = {
                'key_skills': ['Python'],
                'experience_level': 'mid',
                'industry': job.get('company', ''),
                'must_haves': [],
                'nice_to_haves': []
            }

        return analysis

    def _generate_customization_prompt(
        self,
        cv_content: str,
        job: Dict[str, Any],
        job_analysis: Dict[str, Any]
    ) -> str:
        """
        Generate a prompt to guide customization.

        Args:
            cv_content: Your actual CV text
            job: Job posting
            job_analysis: Analysis of job requirements

        Returns:
            Customization prompt for LLM
        """
        return f"""
Given this person's actual CV and this job posting, suggest what sections
to EMPHASIZE (not invent or change).

Their CV:
---
{cv_content[:1500]}
---

Job they're applying for:
Title: {job.get('title', '')}
Company: {job.get('company', '')}
Description: {job.get('description', '')[:800]}

Key skills they're looking for: {job_analysis.get('key_skills', [])}

Task: Suggest which sections of their CV to emphasize/highlight because they
match the job. Do NOT suggest adding skills they don't have.

Return JSON with:
- sections_to_emphasize: list of CV sections that match (e.g., "Technical Skills", "Experience")
- skills_match: which of their actual skills match the job
- relevant_achievements: which accomplishments to highlight
- summary: one sentence about why they fit this role
"""

    def _get_emphasis_suggestions(
        self,
        prompt: str,
        cv_content: str,
        job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get LLM suggestions on what to emphasize.

        Args:
            prompt: Customization prompt
            cv_content: Your CV content
            job: Job posting

        Returns:
            Suggestions for customization
        """
        response = self.llm_client.generate(prompt)

        try:
            import json
            suggestions = json.loads(response)
        except:
            # Fallback if parsing fails
            suggestions = {
                'sections_to_emphasize': ['Technical Skills', 'Professional Experience'],
                'skills_match': [],
                'relevant_achievements': [],
                'summary': f"Qualified Python developer for {job.get('company', '')} role"
            }

        return suggestions

    def _create_customized_cv(
        self,
        cv_content: str,
        job: Dict[str, Any],
        suggestions: Dict[str, Any]
    ) -> Path:
        """
        Create a customized version of your CV.

        For now, copies your existing CV with a job-specific filename.
        In the future, could add highlighting/emphasis via DOCX formatting.

        Args:
            cv_content: Your CV text
            job: Job posting
            suggestions: LLM suggestions for emphasis

        Returns:
            Path to output CV file
        """
        # Generate unique filename
        # Use job URL to create unique identifier
        job_url = job.get('url', '')
        # Extract job ID from URL (usually the numeric/alphanumeric part)
        url_parts = job_url.split('/')
        job_identifier = url_parts[-1] if url_parts else 'job'

        # Clean identifiers for filename
        company_name = job.get('company', 'Unknown').replace(' ', '_')[:15]
        date = datetime.now().strftime('%Y%m%d')

        # Create unique filename: CV_Company_Date_JobID.pdf
        filename = f"CV_{company_name}_{date}_{job_identifier}.pdf"
        output_path = self.output_dir / filename

        # Copy your CV with job-specific name
        # (This preserves your actual PDF with your real formatting)
        shutil.copy(self.base_cv_path, output_path)

        logger.info(f"Created customized CV: {output_path}")
        logger.info(f"Emphasis suggestions: {suggestions.get('summary', '')}")

        return output_path
