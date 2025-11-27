"""
Motivation Letter Generator Agent

Creates personalized motivation/cover letters for each job application
based on the job requirements and your CV/skills.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

from llm import create_llm_client, BaseLLMClient


class MotivationLetterAgent:
    """Generates personalized motivation letters for job applications."""

    def __init__(self, config: Dict[str, Any], llm_client: Optional[BaseLLMClient] = None):
        """
        Initialize the Motivation Letter Agent.

        Args:
            config: Configuration dictionary
            llm_client: Optional pre-configured LLM client
        """
        self.config = config
        self.llm_config = config.get('llm', {})
        self.user_name = config.get('user', {}).get('name', 'Applicant')
        self.user_email = config.get('user', {}).get('email', '')

        if llm_client:
            self.llm_client = llm_client
        else:
            self.llm_client = create_llm_client(self.llm_config)

        # Ensure output directory exists
        self.output_dir = Path("data/cvs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Motivation Letter Agent initialized with {self.llm_client.provider_name} "
            f"({self.llm_client.model})"
        )

    def generate_letter(
        self,
        job: Dict[str, Any],
        cv_content: str = "",
        suggestions: Dict[str, Any] = None
    ) -> str:
        """
        Generate a personalized motivation letter for a job.

        Args:
            job: Job posting dictionary
            cv_content: Your CV text content (optional)
            suggestions: LLM suggestions about job fit (optional)

        Returns:
            Generated motivation letter text
        """
        logger.info(f"Generating motivation letter for: {job['title']} at {job['company']}")

        try:
            # If cv_content not provided, extract from file
            if not cv_content:
                cv_content = self._extract_cv_content()

            # Default suggestions if not provided
            if not suggestions:
                suggestions = {'summary': 'Qualified candidate', 'skills_match': []}

            # Create prompt for motivation letter
            prompt = self._create_motivation_prompt(job, cv_content, suggestions)

            # Generate letter
            letter = self._generate_with_llm(prompt)

            logger.info(f"Motivation letter generated successfully")
            return letter

        except Exception as e:
            logger.error(f"Error generating motivation letter: {e}", exc_info=True)
            raise

    def _extract_cv_content(self) -> str:
        """
        Extract text content from CV PDF if available.

        Returns:
            CV text content
        """
        try:
            from PyPDF2 import PdfReader
            cv_path = self.config.get('cv', {}).get('template_path', 'cv.pdf')

            reader = PdfReader(cv_path)
            content = ""
            for page in reader.pages:
                content += page.extract_text() + "\n"

            return content
        except Exception as e:
            logger.warning(f"Could not extract CV content: {e}")
            return "Professional with relevant experience"

    def _create_motivation_prompt(
        self,
        job: Dict[str, Any],
        cv_content: str,
        suggestions: Dict[str, Any]
    ) -> str:
        """
        Create a prompt to generate a personalized motivation letter.

        Args:
            job: Job posting
            cv_content: Your CV text
            suggestions: Job fit suggestions

        Returns:
            Prompt for LLM
        """
        return f"""Write a professional, personalized motivation letter for this job application.

APPLICANT INFORMATION:
Name: {self.user_name}
Email: {self.user_email}

APPLICANT'S CV (relevant sections):
---
{cv_content[:1500]}
---

JOB DETAILS:
Title: {job.get('title', '')}
Company: {job.get('company', '')}
Location: {job.get('location', '')}
Description: {job.get('description', '')[:1000]}

APPLICANT'S MATCHING SKILLS:
{', '.join(suggestions.get('skills_match', []))}

WHY THEY FIT:
{suggestions.get('summary', 'Qualified candidate')}

REQUIREMENTS:
1. Write a professional motivation/cover letter (300-400 words)
2. Address it to the hiring manager (use "Dear Hiring Manager" if specific name unknown)
3. Include:
   - Brief introduction with position applied for
   - Why you're interested in THIS specific company/position
   - How your skills/experience match their requirements
   - Specific mention of relevant achievements from their CV
   - Your enthusiasm and why you'd be valuable to their team
   - Professional closing with call to action

4. Tone: Professional, confident but humble, genuine interest
5. Format: Ready to paste into email or document
6. Language: English, business formal

Generate ONLY the letter text, no additional commentary."""

    def _generate_with_llm(self, prompt: str) -> str:
        """
        Generate letter using LLM.

        Args:
            prompt: Prompt for the LLM

        Returns:
            Generated letter
        """
        response = self.llm_client.generate(prompt)

        # Convert response to string if it's an object
        response_text = str(response) if not isinstance(response, str) else response

        return response_text.strip()

    def save_letter(
        self,
        letter: str,
        job: Dict[str, Any],
        output_filename: str = None
    ) -> Path:
        """
        Save motivation letter to file.

        Args:
            letter: Letter text
            job: Job details (for filename)
            output_filename: Optional custom filename

        Returns:
            Path to saved file
        """
        if not output_filename:
            # Generate filename
            company_name = job.get('company', 'Unknown').replace(' ', '_')[:15]
            job_id = job.get('url', '').split('/')[-1] if job.get('url') else 'job'
            date = datetime.now().strftime('%Y%m%d')
            output_filename = f"MOTIVATION_LETTER_{company_name}_{date}_{job_id}.txt"

        output_path = self.output_dir / output_filename

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(letter)

        logger.info(f"Motivation letter saved to: {output_path}")
        return output_path
