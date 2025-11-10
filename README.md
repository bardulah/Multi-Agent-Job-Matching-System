# Multi-Agent Job Application System

An intelligent, automated system that helps you find relevant jobs, tailor your CV for each position, and manage your job application process efficiently.

## Features

### 🔍 Job Fetching Agent
- Scrapes daily job postings from **profesia.sk**
- Filters jobs based on your preferences and skills
- Avoids duplicate processing with built-in history tracking

### ✍️ CV Tailoring Agent
- Analyzes job requirements using AI (Claude)
- Automatically customizes your CV for each job
- Highlights relevant skills and experience
- Generates professional DOCX documents

### 🔎 Critique Agent
- Reviews each tailored CV for quality
- Checks relevance, clarity, keyword optimization, and formatting
- Provides actionable improvement suggestions
- Auto-approves high-quality CVs (score ≥ 7/10)

### 📧 Approval & Notification Agent
- Compiles daily summaries of approved jobs
- Sends email notifications with:
  - Job links
  - Tailored CVs as attachments
  - Quality scores and suggestions
- Optional manual review mode

### 📊 Additional Features
- **Job history tracking** - Never apply to the same job twice
- **Statistics dashboard** - Track your application success rate
- **Configurable matching** - Set minimum match scores and preferences
- **Cron-compatible** - Easy daily scheduling
- **Comprehensive logging** - Debug and monitor system activity

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Job Application System                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │ Job Fetcher  │   │  CV Tailor   │   │   Critique   │    │
│  │    Agent     │──▶│    Agent     │──▶│    Agent     │    │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│         │                   │                   │            │
│         ▼                   ▼                   ▼            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Orchestrator & History Manager            │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                   │
│                          ▼                                   │
│                 ┌──────────────┐                            │
│                 │ Notification │                            │
│                 │    Agent     │                            │
│                 └──────────────┘                            │
│                          │                                   │
│                          ▼                                   │
│                   📧 Daily Email                             │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd jobs
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your credentials
   ```

   Required variables:
   - `ANTHROPIC_API_KEY` - Your Anthropic API key ([get one here](https://console.anthropic.com/))
   - `EMAIL_ADDRESS` - Your email address
   - `EMAIL_PASSWORD` - Your email password or app password

5. **Configure the system**
   ```bash
   cp config.example.yaml config.yaml
   nano config.yaml  # Customize your preferences
   ```

   Key configuration sections:
   - **user**: Your personal information
   - **job_preferences**: Job search criteria (keywords, locations, etc.)
   - **skills**: Your technical and soft skills
   - **email**: Email notification settings
   - **system**: System behavior settings

6. **Test the configuration**
   ```bash
   python orchestrator.py --test
   ```

## Usage

### Manual Execution

Run the system once:
```bash
python orchestrator.py
```

Run with custom config:
```bash
python orchestrator.py --config my_config.yaml
```

### Scheduled Execution

#### Option 1: Using Cron (Linux/Mac)

1. Make the script executable:
   ```bash
   chmod +x run_daily.sh
   ```

2. Edit your crontab:
   ```bash
   crontab -e
   ```

3. Add this line to run daily at 8 AM:
   ```cron
   0 8 * * * /full/path/to/jobs/run_daily.sh >> /full/path/to/jobs/logs/cron.log 2>&1
   ```

#### Option 2: Using Python Scheduler

Run the built-in scheduler:
```bash
python schedule.py
```

This will run the system daily at 8:00 AM. Press Ctrl+C to stop.

#### Option 3: Using systemd (Linux)

Create a systemd service and timer for more robust scheduling. See `docs/systemd-setup.md` for details.

## Configuration Guide

### Job Preferences

Configure what jobs you're looking for:

```yaml
job_preferences:
  keywords:
    - "Python"
    - "Machine Learning"
    - "Backend Developer"

  excluded_keywords:
    - "Senior Manager"
    - "Director"

  locations:
    - "Bratislava"
    - "Remote"

  employment_types:
    - "full-time"
    - "contract"

  min_salary: 2000  # Optional, in EUR
```

### Skills

List all your skills for better matching:

```yaml
skills:
  programming_languages:
    - "Python"
    - "JavaScript"
    - "SQL"

  frameworks:
    - "Django"
    - "FastAPI"
    - "React"

  tools:
    - "Docker"
    - "Git"
    - "AWS"
```

### System Settings

```yaml
system:
  max_jobs_per_day: 10          # Maximum jobs to process
  min_match_score: 0.6          # Minimum match score (0-1)
  enable_auto_send: false       # Auto-send emails vs manual review
  log_level: "INFO"             # DEBUG, INFO, WARNING, ERROR
  data_retention_days: 90       # Keep history for 90 days
```

## Project Structure

```
jobs/
├── agents/                  # Agent modules
│   ├── __init__.py
│   ├── job_fetcher.py      # Job scraping agent
│   ├── cv_tailor.py        # CV customization agent
│   ├── critique.py         # CV review agent
│   └── notification.py     # Email notification agent
├── utils/                   # Utility modules
│   ├── __init__.py
│   ├── config_loader.py    # Configuration management
│   ├── logger.py           # Logging setup
│   ├── job_matcher.py      # Job matching logic
│   └── history_manager.py  # Job history tracking
├── data/                    # Data directories
│   ├── cvs/                # Generated CVs
│   ├── jobs/               # Scraped job data
│   ├── history/            # Job application history
│   └── review/             # Manual review queue
├── logs/                    # Log files
├── templates/               # CV templates
├── tests/                   # Unit tests
├── config.example.yaml      # Example configuration
├── .env.example            # Example environment variables
├── orchestrator.py         # Main orchestrator
├── schedule.py             # Python scheduler
├── run_daily.sh            # Bash script for cron
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Email Configuration

### Gmail Setup

To use Gmail for sending notifications:

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to https://myaccount.google.com/security
   - Select "2-Step Verification"
   - Scroll to "App passwords"
   - Generate a new app password for "Mail"
3. Use this app password in your `.env` file

### Other Email Providers

Update the SMTP settings in `config.yaml`:

```yaml
email:
  smtp_server: "smtp.yourprovider.com"
  smtp_port: 587
  use_tls: true
```

## Monitoring & Logs

### View Logs

All activities are logged to `logs/` directory:

```bash
# View today's log
tail -f logs/job_system_$(date +%Y-%m-%d).log

# View all logs
ls -lh logs/
```

### Check Job History

```bash
# View history file
cat data/history/job_history.json | jq .

# Export to CSV
python -c "from utils.history_manager import HistoryManager; h = HistoryManager(); h.export_to_csv('history.csv')"
```

### View Statistics

Statistics are included in the daily email and logged at the end of each run.

## Manual Review Mode

If you prefer to review applications before sending:

1. Set in `config.yaml`:
   ```yaml
   system:
     enable_auto_send: false
   ```

2. After each run, review the output in `data/review/YYYY-MM-DD/`
   - `summary.html` - Visual summary
   - `jobs.txt` - Text summary
   - CVs are in `data/cvs/`

3. Manually send applications you approve

## Troubleshooting

### No jobs found
- Check your keywords aren't too restrictive
- Verify profesia.sk is accessible
- Check logs for scraping errors

### Email not sending
- Verify email credentials in `.env`
- Check SMTP settings in `config.yaml`
- Test with: `python orchestrator.py --test`
- For Gmail, ensure you're using an App Password

### Low match scores
- Adjust `min_match_score` in config (try 0.4 or 0.5)
- Add more relevant keywords
- Expand location preferences

### API errors
- Verify your Anthropic API key is valid
- Check API quotas and limits
- Ensure you have API credits

## Advanced Features

### Custom CV Templates

Place your CV template (DOCX format) in `templates/cv_template.docx`. The system will use it as a base for tailoring.

### Cloud Storage Integration

(Optional) Store CVs in Google Drive or Dropbox:

```yaml
cloud_storage:
  enabled: true
  provider: "google_drive"
  credentials_path: "config/cloud_credentials.json"
  folder_id: "your-folder-id"
```

### Web Dashboard

(Coming soon) View and manage applications via web interface:

```yaml
dashboard:
  enabled: true
  host: "0.0.0.0"
  port: 8000
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black .
flake8 .
```

### Adding New Features

1. Create a new agent in `agents/` directory
2. Add it to the orchestrator workflow
3. Update configuration schema
4. Add tests
5. Update documentation

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Your License Here]

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/) for intelligent CV tailoring and critique
- Job data from [profesia.sk](https://www.profesia.sk/)
- Uses Python libraries: requests, BeautifulSoup, python-docx, loguru, and more

## Disclaimer

This tool is for personal use to help manage your job search. Always review generated CVs before sending. Respect websites' terms of service and rate limits when scraping.
