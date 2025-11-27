#!/usr/bin/env python3
"""
Main entry point for the Multi-Agent Job Application System.
Redirects to orchestrator.py.
"""

import sys
import os
from orchestrator import main

if __name__ == "__main__":
    # Ensure we are running from the script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main())
