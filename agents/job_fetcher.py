"""
Job Fetcher Agent

Scrapes job postings from profesia.sk and filters them based on user preferences.
"""

import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin, quote_plus
from loguru import logger


class JobFetcherAgent:
    """Agent responsible for fetching and filtering job postings from profesia.sk."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Job Fetcher Agent.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.scraping_config = config.get('scraping', {}).get('profesia_sk', {})
        self.base_url = self.scraping_config.get('base_url', 'https://www.profesia.sk')
        self.search_url = self.scraping_config.get('search_url', 'https://www.profesia.sk/praca/')
        self.max_pages = self.scraping_config.get('max_pages', 5)
        self.delay = self.scraping_config.get('delay_between_requests', 2)
        self.user_agent = config.get('scraping', {}).get('user_agent', 'Mozilla/5.0')

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'sk,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })

        logger.info("Job Fetcher Agent initialized")

    def fetch_jobs(self, keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch job postings from profesia.sk.

        Args:
            keywords: List of keywords to search for (uses config if None)

        Returns:
            List of job dictionaries
        """
        if keywords is None:
            keywords = self.config.get('job_preferences', {}).get('keywords', [])

        all_jobs = []
        search_query = ' '.join(keywords[:3])  # Use top 3 keywords

        logger.info(f"Starting job search for: {search_query}")

        try:
            for page in range(1, self.max_pages + 1):
                logger.debug(f"Fetching page {page}/{self.max_pages}")

                jobs = self._fetch_page(search_query, page)
                if not jobs:
                    logger.info(f"No more jobs found at page {page}, stopping")
                    break

                all_jobs.extend(jobs)

                # Rate limiting
                if page < self.max_pages:
                    time.sleep(self.delay)

            logger.info(f"Fetched {len(all_jobs)} jobs total")

            # Deduplicate by URL
            unique_jobs = {job['url']: job for job in all_jobs}.values()
            return list(unique_jobs)

        except Exception as e:
            logger.error(f"Error fetching jobs: {e}")
            return []

    def _fetch_page(self, search_query: str, page: int) -> List[Dict[str, Any]]:
        """
        Fetch a single page of job listings.

        Args:
            search_query: Search query string
            page: Page number

        Returns:
            List of job dictionaries
        """
        try:
            # Construct search URL
            # Format: https://www.profesia.sk/praca/?search_query=python&page=1
            params = {
                'search_query': search_query,
                'page': page
            }

            # Build URL
            url = f"{self.search_url}?search_query={quote_plus(search_query)}&page={page}"

            logger.debug(f"Fetching URL: {url}")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')
            jobs = self._parse_job_listings(soup)

            return jobs

        except requests.RequestException as e:
            logger.error(f"Request error on page {page}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing page {page}: {e}")
            return []

    def _parse_job_listings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Parse job listings from the HTML page.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List of job dictionaries
        """
        jobs = []

        # Note: These selectors are examples and may need adjustment based on actual site structure
        # Profesia.sk structure may vary, so this is a flexible implementation

        # Try multiple possible selectors for job listings
        job_listings = (
            soup.find_all('article', class_='list-row') or
            soup.find_all('div', class_='job-item') or
            soup.find_all('li', class_='offer') or
            soup.find_all('div', attrs={'data-jobad': True})
        )

        logger.debug(f"Found {len(job_listings)} job listings on page")

        for listing in job_listings:
            try:
                job = self._parse_single_job(listing)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.warning(f"Error parsing job listing: {e}")
                continue

        return jobs

    def _parse_single_job(self, listing) -> Optional[Dict[str, Any]]:
        """
        Parse a single job listing element.

        Args:
            listing: BeautifulSoup element containing job listing

        Returns:
            Job dictionary or None if parsing fails
        """
        try:
            # Extract job title and URL
            title_element = (
                listing.find('a', class_='title') or
                listing.find('h2', class_='title') or
                listing.find('a', href=True)
            )

            if not title_element:
                return None

            title = title_element.get_text(strip=True)
            url = title_element.get('href', '')

            if url and not url.startswith('http'):
                url = urljoin(self.base_url, url)

            # Extract company
            company_element = (
                listing.find('span', class_='employer') or
                listing.find('div', class_='company') or
                listing.find('span', class_='company-name')
            )
            company = company_element.get_text(strip=True) if company_element else 'Unknown'

            # Extract location
            location_element = (
                listing.find('span', class_='locality') or
                listing.find('div', class_='location') or
                listing.find('span', class_='location')
            )
            location = location_element.get_text(strip=True) if location_element else 'Not specified'

            # Extract salary if available
            salary_element = (
                listing.find('span', class_='salary') or
                listing.find('div', class_='salary')
            )
            salary = salary_element.get_text(strip=True) if salary_element else None

            # Extract short description
            description_element = (
                listing.find('div', class_='description') or
                listing.find('p', class_='description')
            )
            description = description_element.get_text(strip=True) if description_element else ''

            # Extract employment type
            employment_type = 'full-time'  # Default
            if description:
                if 'part-time' in description.lower() or 'čiastočný úväzok' in description.lower():
                    employment_type = 'part-time'
                elif 'contract' in description.lower() or 'zmluva' in description.lower():
                    employment_type = 'contract'

            job = {
                'title': title,
                'company': company,
                'location': location,
                'url': url,
                'salary': salary,
                'description': description,
                'employment_type': employment_type,
                'fetched_at': datetime.now().isoformat(),
                'source': 'profesia.sk'
            }

            logger.debug(f"Parsed job: {title} at {company}")

            return job

        except Exception as e:
            logger.warning(f"Error parsing job element: {e}")
            return None

    def fetch_job_details(self, job_url: str) -> Optional[str]:
        """
        Fetch full job description from job detail page.

        Args:
            job_url: URL of the job posting

        Returns:
            Full job description or None
        """
        try:
            logger.debug(f"Fetching job details from: {job_url}")

            response = self.session.get(job_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Find job description (adjust selectors as needed)
            description_element = (
                soup.find('div', class_='job-description') or
                soup.find('div', class_='content') or
                soup.find('article', class_='offer-description') or
                soup.find('div', id='job-description')
            )

            if description_element:
                # Extract text, preserving some structure
                description = description_element.get_text(separator='\n', strip=True)
                return description

            logger.warning(f"Could not find job description on page: {job_url}")
            return None

        except Exception as e:
            logger.error(f"Error fetching job details from {job_url}: {e}")
            return None

    def enrich_jobs_with_details(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fetch full descriptions for all jobs.

        Args:
            jobs: List of job dictionaries

        Returns:
            Jobs with enriched descriptions
        """
        enriched_jobs = []

        for i, job in enumerate(jobs, 1):
            logger.info(f"Enriching job {i}/{len(jobs)}: {job['title']}")

            full_description = self.fetch_job_details(job['url'])
            if full_description:
                job['full_description'] = full_description
            else:
                job['full_description'] = job.get('description', '')

            enriched_jobs.append(job)

            # Rate limiting
            if i < len(jobs):
                time.sleep(self.delay)

        return enriched_jobs
