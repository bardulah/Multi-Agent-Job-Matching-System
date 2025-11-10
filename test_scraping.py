#!/usr/bin/env python3
"""
Test script to verify web scraping from profesia.sk
"""

import sys
from agents.job_fetcher import JobFetcherAgent
from utils.config_loader import ConfigLoader

def test_scraping():
    """Test if job scraping works."""
    print("=" * 80)
    print("Testing Job Scraping from profesia.sk")
    print("=" * 80)
    print()

    try:
        # Load config
        config = ConfigLoader('config.yaml')
        print("✓ Configuration loaded")

        # Initialize job fetcher
        fetcher = JobFetcherAgent(config.config)
        print("✓ Job Fetcher Agent initialized")
        print()

        # Test with a simple search
        print("Fetching jobs with keywords: ['Python', 'Developer']")
        print("(Limited to 1 page for testing)")
        print()

        # Temporarily limit to 1 page for testing
        original_max_pages = fetcher.max_pages
        fetcher.max_pages = 1

        jobs = fetcher.fetch_jobs(keywords=['Python', 'Developer'])

        fetcher.max_pages = original_max_pages

        print(f"✓ Fetched {len(jobs)} jobs from profesia.sk")
        print()

        if jobs:
            print("Sample job listings:")
            print("-" * 80)
            for i, job in enumerate(jobs[:3], 1):
                print(f"\n{i}. {job['title']}")
                print(f"   Company: {job['company']}")
                print(f"   Location: {job['location']}")
                print(f"   URL: {job['url'][:60]}...")
                if job.get('salary'):
                    print(f"   Salary: {job['salary']}")
                print(f"   Description: {job['description'][:100]}...")

            print()
            print("-" * 80)
            print(f"\n✅ SCRAPING WORKS! Found {len(jobs)} jobs successfully")

            # Test fetching full description for first job
            if jobs:
                print("\nTesting full job description fetch...")
                first_job = jobs[0]
                full_desc = fetcher.fetch_job_details(first_job['url'])

                if full_desc:
                    print(f"✓ Full description fetched ({len(full_desc)} characters)")
                    print(f"  Preview: {full_desc[:200]}...")
                else:
                    print("⚠ Could not fetch full description (may need selector adjustment)")

            return True
        else:
            print("⚠ No jobs found - this could mean:")
            print("  1. Network/connection issue")
            print("  2. Profesia.sk changed their HTML structure")
            print("  3. No jobs matching the search query")
            print()
            print("Recommendation: Check network connection and site accessibility")
            return False

    except Exception as e:
        print(f"\n❌ ERROR during scraping test:")
        print(f"   {type(e).__name__}: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_scraping()
    sys.exit(0 if success else 1)
