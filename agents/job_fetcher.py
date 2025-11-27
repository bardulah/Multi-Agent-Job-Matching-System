"""
Job Fetcher Agent with Selenium Support

Scrapes job postings from profesia.sk using Selenium to bypass anti-bot protection.
"""

import time
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin
from loguru import logger

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not installed. Install with: pip install selenium webdriver-manager")


class JobFetcherAgent:
    """Agent responsible for fetching and filtering job postings from profesia.sk."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Job Fetcher Agent."""
        self.config = config
        self.scraping_config = config.get('scraping', {}).get('profesia_sk', {})
        self.base_url = self.scraping_config.get('base_url', 'https://www.profesia.sk')
        self.search_url = self.scraping_config.get('search_url', 'https://www.profesia.sk/praca/')
        self.max_pages = self.scraping_config.get('max_pages', 5)
        self.delay = self.scraping_config.get('delay_between_requests', 2)

        self.use_selenium = SELENIUM_AVAILABLE

        if self.use_selenium:
            logger.info("🚀 Job Fetcher with Selenium - ANTI-BOT BYPASS ENABLED!")
        else:
            logger.warning("⚠️  Selenium not available - install it!")

    def _get_driver(self):
        """Create and configure Selenium WebDriver."""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        # Remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

    def fetch_jobs(self, keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch job postings from profesia.sk."""
        if keywords is None:
            keywords = self.config.get('job_preferences', {}).get('keywords', [])

        all_jobs = []
        search_query = ' '.join(keywords[:3])

        logger.info(f"🔍 Searching for: {search_query}")

        if not self.use_selenium:
            logger.error("❌ Selenium not available - cannot bypass bot protection")
            return []

        driver = None
        try:
            driver = self._get_driver()
            logger.info("✓ Browser launched")

            for page in range(1, self.max_pages + 1):
                logger.info(f"📄 Fetching page {page}/{self.max_pages}...")

                jobs = self._fetch_page_selenium(driver, search_query, page)
                if not jobs:
                    logger.info(f"No more jobs at page {page}")
                    break

                all_jobs.extend(jobs)
                logger.info(f"  Found {len(jobs)} jobs on this page")

                if page < self.max_pages:
                    time.sleep(self.delay)

            logger.info(f"✅ Total: {len(all_jobs)} jobs fetched!")

            unique_jobs = {job['url']: job for job in all_jobs}.values()
            return list(unique_jobs)

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if driver:
                driver.quit()
                logger.debug("Browser closed")

    def _fetch_page_selenium(self, driver, search_query: str, page: int) -> List[Dict[str, Any]]:
        """Fetch a single page using Selenium."""
        try:
            url = f"{self.search_url}?search_anywhere={search_query}&page={page}"
            logger.debug(f"Loading: {url}")

            driver.get(url)
            time.sleep(4)  # Wait for page load and JS

            # Parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            jobs = self._parse_job_listings(soup)

            return jobs

        except Exception as e:
            logger.error(f"Error on page {page}: {e}")
            return []

    def _parse_job_listings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse job listings from HTML."""
        jobs = []

        # Try multiple selectors
        job_listings = (
            soup.find_all('li', class_='list-row') or
            soup.find_all('article') or
            soup.find_all('div', class_='offer') or
            soup.find_all('li', class_='offer') or
            soup.find_all('a', href=lambda x: x and '/praca/' in x and len(x) > 10)[:30]
        )

        logger.debug(f"Found {len(job_listings)} potential listings")

        for listing in job_listings:
            try:
                job = self._parse_single_job(listing)
                if job and job['title'] and len(job['title']) > 3:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"Skip listing: {e}")
                continue

        return jobs

    def _parse_single_job(self, listing) -> Optional[Dict[str, Any]]:
        """Parse a single job listing."""
        try:
            # Get all text and links
            text = listing.get_text(strip=True)
            links = listing.find_all('a', href=True)

            if not links:
                return None

            # Find best link (longest href with /praca/)
            # Exclude login/redirect links which might be longer
            valid_links = [
                l for l in links 
                if '/praca/' in l.get('href', '') 
                and 'login' not in l.get('href', '')
                and 'redirect' not in l.get('href', '')
            ]

            best_link = max(
                valid_links,
                key=lambda x: len(x.get('href', '')),
                default=None
            )

            if not best_link:
                return None

            url = best_link.get('href', '')
            if not url.startswith('http'):
                url = urljoin(self.base_url, url)

            logger.debug(f"Parsed job URL: {url}")

            # Extract title
            title = best_link.get_text(strip=True) or text[:100]

            # Try to extract company and location from surrounding text
            all_text_elements = listing.find_all(text=True)
            text_parts = [t.strip() for t in all_text_elements if t.strip()]

            company = 'Unknown'
            location = 'Not specified'

            # Simple heuristic: company often after title, location has city names
            if len(text_parts) > 1:
                company = text_parts[1] if len(text_parts[1]) < 50 else 'Unknown'
            if len(text_parts) > 2:
                location = text_parts[2] if len(text_parts[2]) < 30 else 'Not specified'

            job = {
                'title': title,
                'company': company,
                'location': location,
                'url': url,
                'salary': None,
                'description': text[:200],
                'employment_type': 'full-time',
                'fetched_at': datetime.now().isoformat(),
                'source': 'profesia.sk'
            }

            return job

        except Exception as e:
            return None

    def fetch_job_details(self, job_url: str) -> Optional[str]:
        """Fetch full job description."""
        if not self.use_selenium:
            return None

        driver = None
        try:
            driver = self._get_driver()
            driver.get(job_url)
            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Get all text from page
            description = soup.get_text(separator='\n', strip=True)

            return description[:5000]  # Limit size

        except Exception as e:
            logger.error(f"Error fetching details: {e}")
            return None
        finally:
            if driver:
                driver.quit()

    def enrich_jobs_with_details(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fetch full descriptions for all jobs."""
        enriched_jobs = []

        for i, job in enumerate(jobs, 1):
            logger.info(f"Enriching {i}/{len(jobs)}: {job['title']}")

            full_description = self.fetch_job_details(job['url'])
            if full_description:
                job['full_description'] = full_description
            else:
                job['full_description'] = job.get('description', '')

            enriched_jobs.append(job)

            if i < len(jobs):
                time.sleep(self.delay)

        return enriched_jobs
