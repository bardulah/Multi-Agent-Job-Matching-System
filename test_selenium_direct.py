#!/usr/bin/env python3
"""Direct test of Selenium scraping"""

import sys
sys.path.insert(0, '/home/user/jobs')

from agents.job_fetcher import JobFetcherAgent
from utils.config_loader import ConfigLoader

print("🚀 YOLO MODE: Testing Selenium Scraping")
print("=" * 80)

config = ConfigLoader('config.yaml')
fetcher = JobFetcherAgent(config.config)

# Override to 1 page for fast testing
fetcher.max_pages = 1

print("\nFetching Python Developer jobs...")
jobs = fetcher.fetch_jobs(keywords=['Python'])

print(f"\n✅ SUCCESS! Found {len(jobs)} jobs!\n")

if jobs:
    print("Sample Jobs:")
    print("-" * 80)
    for i, job in enumerate(jobs[:5], 1):
        print(f"{i}. {job['title']}")
        print(f"   Company: {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   URL: {job['url'][:70]}...")
        print()
else:
    print("No jobs found - check network/site access")
