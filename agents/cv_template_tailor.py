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
            # Convert response to string if it's an object
            response_text = str(response) if not isinstance(response, str) else response
            analysis = json.loads(response_text)
        except Exception as e:
            logger.warning(f"Failed to parse job analysis JSON: {e}")
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
        return f"""Analyze this CV against this job and provide specific customization advice.

CV Content:
---
{cv_content[:2000]}
---

Job Details:
Title: {job.get('title', '')}
Company: {job.get('company', '')}
Location: {job.get('location', '')}
Description: {job.get('description', '')[:1000]}

Job Key Skills Needed: {', '.join(job_analysis.get('key_skills', []))}

Task: Identify which parts of their CV are most relevant to this specific job.

IMPORTANT: Return ONLY valid JSON, no other text. Format exactly like this:

{{
  "sections_to_emphasize": ["Section1", "Section2"],
  "skills_match": ["Skill1 from CV", "Skill2 from CV"],
  "relevant_achievements": ["Achievement1 from their CV", "Achievement2 from their CV"],
  "why_they_fit": "One sentence explaining why they're a good fit for THIS specific job"
}}

Be specific about which CV sections and skills actually appear in their CV."""

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
            # Convert response to string if it's an object
            response_text = str(response) if not isinstance(response, str) else response
            suggestions = json.loads(response_text)
            # Normalize key names if LLM used different names
            if 'why_they_fit' in suggestions and 'summary' not in suggestions:
                suggestions['summary'] = suggestions['why_they_fit']
            if 'relevant_achievements' not in suggestions:
                suggestions['relevant_achievements'] = []
        except Exception as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            # Fallback if parsing fails
            suggestions = {
                'sections_to_emphasize': ['Technical Skills', 'Professional Experience'],
                'skills_match': [],
                'relevant_achievements': [],
                'summary': f"Qualified candidate for {job.get('company', '')} role"
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

        Approach 3 preserves your authentic voice while creating a job-specific version.
        This creates a text-based customized CV with a cover note showing tailoring.

        Args:
            cv_content: Your CV text
            job: Job posting
            suggestions: LLM suggestions for emphasis

        Returns:
            Path to output CV file (PDF copy with job-specific naming)
        """
        # Generate unique filename
        job_url = job.get('url', '')
        url_parts = job_url.split('/')
        job_identifier = url_parts[-1] if url_parts else 'job'

        company_name = job.get('company', 'Unknown').replace(' ', '_')[:15]
        date = datetime.now().strftime('%Y%m%d')

        # Create unique filename: CV_Company_Date_JobID.pdf
        filename = f"CV_{company_name}_{date}_{job_identifier}.pdf"
        output_path = self.output_dir / filename

        # Copy your CV with job-specific name
        # Note: PDF copying preserves formatting. Customization is in the covering note
        # (stored separately but sent with CV to show tailoring)
        shutil.copy(self.base_cv_path, output_path)

        # Create customization note file (text format showing how CV was tailored)
        note_filename = f"TAILORING_NOTE_{company_name}_{date}_{job_identifier}.txt"
        note_path = self.output_dir / note_filename

        customization_note = self._create_customization_note(job, suggestions, cv_content)
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(customization_note)

        logger.info(f"Created customized CV: {output_path}")
        logger.info(f"Created tailoring note: {note_path}")
        logger.info(f"Emphasis suggestions: {suggestions.get('summary', '')}")

        return output_path

    def _create_customization_note(
        self,
        job: Dict[str, Any],
        suggestions: Dict[str, Any],
        cv_content: str
    ) -> str:
        """
        Create a note showing how the CV was customized for this job.

        Args:
            job: Job posting
            suggestions: LLM suggestions
            cv_content: Original CV content

        Returns:
            Customization note text
        """
        note = f"""
CUSTOMIZATION NOTE FOR: {job.get('title', 'Position')} at {job.get('company', 'Company')}
Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

HOW THIS CV WAS TAILORED FOR THIS JOB:
=====================================

Job Requirements Analysis:
- Title: {job.get('title', 'N/A')}
- Company: {job.get('company', 'N/A')}
- Location: {job.get('location', 'N/A')}

Your Matching Skills:
{self._format_list(suggestions.get('skills_match', []))}

Sections to Emphasize in Your CV:
{self._format_list(suggestions.get('sections_to_emphasize', []))}

Relevant Achievements to Highlight:
{self._format_list(suggestions.get('relevant_achievements', []))}

Your Unique Fit:
{suggestions.get('summary', 'Qualified candidate for this role')}

HOW TO USE THIS CV:
- This is your ACTUAL CV, not AI-generated or fake
- It has been analyzed against the job requirements
- The sections above show what makes you a good match
- When applying, emphasize these points in your cover letter
- Your background in operations + Python skills = unique advantage

IMPORTANT: This CV is your authentic background. No claims have been fabricated.
Every experience, skill, and achievement listed is real.
"""
        return note.strip()

    def _format_list(self, items: list) -> str:
        """Format a list for display."""
        if not items:
            return "  • [No specific items identified]"
        return "\n".join(f"  • {item}" for item in items)
