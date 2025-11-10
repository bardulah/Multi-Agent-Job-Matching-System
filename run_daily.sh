#!/bin/bash
#
# Daily Job Application System Runner
#
# This script is designed to be run via cron for daily execution
# Example cron entry (runs at 8 AM daily):
# 0 8 * * * /path/to/jobs/run_daily.sh >> /path/to/jobs/logs/cron.log 2>&1

# Set working directory to script location
cd "$(dirname "$0")" || exit 1

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Set environment variables from .env file if it exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Log start time
echo "====================================="
echo "Job Application System - Daily Run"
echo "Started at: $(date)"
echo "====================================="

# Run the orchestrator
python3 orchestrator.py --config config.yaml

# Capture exit code
EXIT_CODE=$?

# Log end time and status
echo "====================================="
echo "Completed at: $(date)"
echo "Exit code: $EXIT_CODE"
echo "====================================="

exit $EXIT_CODE
