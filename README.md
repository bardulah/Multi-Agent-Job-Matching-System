# Multi-Agent Job Matching System

An intelligent multi-agent system that automatically finds job opportunities from profesia.sk, matches them with your CV and preferences, validates matches through critique, generates tailored CVs, and sends notifications.

## 🎯 Features

- **Automated Job Scraping**: Fetches daily job postings from profesia.sk based on your preferences
- **Intelligent Matching**: Uses AI to match job requirements with your CV and skills
- **Critique Validation**: Second-opinion agent validates matches and identifies red flags
- **CV Tailoring**: Automatically generates customized CVs for each matched job
- **Smart Notifications**: Sends email alerts with job details and tailored CV attached
- **Configurable**: Fully customizable preferences, thresholds, and agent behavior

## 🏗️ Architecture

The system consists of 5 specialized agents orchestrated by a central coordinator:

```
┌─────────────────────────────────────────────────────────┐
│                    Orchestrator                         │
└─────────────────────────────────────────────────────────┘
         │
         ├──> 1. Scraper Agent      (fetches jobs from profesia.sk)
         │
         ├──> 2. Matcher Agent      (compares with CV & preferences)
         │
         ├──> 3. Critique Agent     (validates & identifies issues)
         │
         ├──> 4. CV Tailor Agent    (generates customized CVs)
         │
         └──> 5. Notification Agent (sends email alerts)
```

### Agent Details

1. **Scraper Agent** (`agents/scraper_agent.py`)
   - Scrapes job listings from profesia.sk
   - Handles multiple search queries (job titles × locations)
   - Extracts job details and requirements
   - Deduplicates results

2. **Matcher Agent** (`agents/matcher_agent.py`)
   - Analyzes job requirements vs. CV content
   - Uses AI (Claude or GPT-4) for intelligent matching
   - Calculates match scores based on multiple factors
   - Identifies missing skills

3. **Critique Agent** (`agents/critique_agent.py`)
   - Provides second opinion on matches
   - Identifies red flags and potential issues
   - Validates job quality and fit
   - Can reject unsuitable matches

4. **CV Tailor Agent** (`agents/cv_tailor_agent.py`)
   - Generates job-specific CV versions
   - Highlights relevant experience
   - Optimizes for ATS systems
   - Maintains factual accuracy

5. **Notification Agent** (`agents/notification_agent.py`)
   - Sends email notifications with job details
   - Attaches tailored CV
   - Provides match analysis and insights
   - Supports batch notifications

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key OR Anthropic API key (for AI-powered matching)
- Email account for notifications (Gmail recommended)
- Internet connection for web scraping

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd jobs
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# For Playwright (if using advanced scraping):
playwright install
```

### 3. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

Required environment variables:
```bash
# AI API Keys (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=your_app_password  # Use App Password for Gmail
NOTIFICATION_EMAIL=your.email@gmail.com
```

**Note for Gmail users:** You need to create an [App Password](https://support.google.com/accounts/answer/185833) instead of using your regular password.

### 4. Configure Your Preferences

Edit `config.yaml` to customize:

```yaml
user_preferences:
  job_titles:
    - "Python Developer"
    - "Backend Engineer"
    # Add your desired job titles

  locations:
    - "Bratislava"
    - "Remote"

  required_skills:
    - "Python"
    - "Docker"
    # Add your must-have skills

  preferred_skills:
    - "AWS"
    - "React"
    # Add nice-to-have skills

  min_salary: 3000
  experience_level: "mid"  # junior, mid, senior
```

### 5. Add Your CV

Place your CV in `data/cv/master_cv.md` or update the path in `config.yaml`:

```yaml
cv_config:
  cv_template_path: "data/cv/master_cv.md"
```

A sample CV template is provided at `data/cv/master_cv.md`.

### 6. Run the System

#### Test Mode (Recommended First)

```bash
python main.py --test
```

This runs with sample data to verify configuration.

#### Production Mode

```bash
python main.py
```

#### Scheduled Daily Runs

```bash
python schedule_daily.py
```

This will run the job agent daily at 9:00 AM.

## 📊 Usage Examples

### Basic Usage

```bash
# Run once with default config
python main.py

# Run with custom config file
python main.py --config my_config.yaml

# Run in test mode
python main.py --test

# Enable debug logging
python main.py --log-level DEBUG
```

### Scheduled Execution

The `schedule_daily.py` script runs the agent system on a schedule:

```python
# Edit schedule_daily.py to customize timing
schedule.every().day.at("09:00").do(run_job_agent)  # Daily at 9 AM
schedule.every(6).hours.do(run_job_agent)           # Every 6 hours
```

### As a Service (Linux)

Create a systemd service for continuous operation:

```bash
# Create service file
sudo nano /etc/systemd/system/job-agent.service
```

```ini
[Unit]
Description=Job Agent System
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/jobs
ExecStart=/path/to/jobs/venv/bin/python schedule_daily.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable job-agent
sudo systemctl start job-agent
sudo systemctl status job-agent
```

## 📁 Project Structure

```
jobs/
├── agents/                  # Agent implementations
│   ├── base_agent.py       # Base agent class
│   ├── scraper_agent.py    # Job scraper
│   ├── matcher_agent.py    # Job matcher
│   ├── critique_agent.py   # Match validator
│   ├── cv_tailor_agent.py  # CV generator
│   └── notification_agent.py # Email sender
├── utils/                   # Utility modules
│   ├── config_loader.py    # Configuration loader
│   └── logger.py           # Logging setup
├── data/                    # Data storage
│   ├── cv/                 # CV files
│   │   ├── master_cv.md    # Your master CV
│   │   └── tailored/       # Generated CVs
│   ├── jobs/               # Scraped jobs (JSON)
│   └── logs/               # Log files
├── orchestrator.py          # Main orchestrator
├── main.py                  # Entry point
├── schedule_daily.py        # Scheduler script
├── config.yaml              # Configuration file
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## ⚙️ Configuration

### Agent Configuration

```yaml
agent_config:
  # Matching
  min_match_score: 0.7           # Minimum score to consider a match

  # Critique
  critique_enabled: true          # Enable/disable critique agent
  critique_strict_mode: false     # Stricter validation

  # CV Tailoring
  cv_tailor_model: "gpt-4"       # AI model for CV generation
  cv_max_pages: 2                # Maximum CV length

  # Notifications
  send_notifications: true        # Enable/disable notifications
  notification_method: "email"    # Notification method

  # Rate Limiting
  max_jobs_per_day: 10           # Maximum jobs to process
  scrape_interval_hours: 24      # Hours between scrapes
```

### CV Configuration

```yaml
cv_config:
  cv_template_path: "data/cv/master_cv.md"
  output_directory: "data/cv/tailored/"

  personal_info:
    name: "Your Name"
    email: "your.email@example.com"
    phone: "+421 XXX XXX XXX"
    location: "Bratislava, Slovakia"
    linkedin: "https://linkedin.com/in/yourprofile"
    github: "https://github.com/yourusername"
```

## 🔍 How It Works

### Workflow

1. **Scraping Phase**
   - Searches profesia.sk for jobs matching your titles and locations
   - Extracts job details, requirements, and descriptions
   - Saves raw data to `data/jobs/`

2. **Matching Phase**
   - Analyzes each job against your CV
   - Calculates match scores (0.0-1.0)
   - Identifies matching and missing skills
   - Filters jobs below minimum threshold

3. **Critique Phase**
   - Reviews each match with critical eye
   - Identifies red flags (unrealistic requirements, unclear descriptions)
   - Validates job quality and career fit
   - Rejects unsuitable matches

4. **CV Tailoring Phase**
   - Generates customized CV for each approved job
   - Highlights relevant experience and skills
   - Uses keywords from job description
   - Saves to `data/cv/tailored/`

5. **Notification Phase**
   - Sends email with job details
   - Attaches tailored CV
   - Includes match analysis and insights
   - Provides direct link to apply

### Match Scoring

Match scores are calculated based on:
- **Job Title Alignment** (25%): How well the title matches your preferences
- **Skills Match** (40%): Percentage of required skills you have
- **Experience Level** (20%): Alignment with your experience level
- **Location Preference** (10%): Match with preferred locations
- **Overall Fit** (5%): Culture and company alignment

## 📧 Email Notifications

Email notifications include:
- ✅ Job title, company, and location
- 📊 Match scores and critique results
- 💡 Why the job matches your profile
- ⚠️ Any red flags identified
- 🔗 Direct link to job posting
- 📄 Tailored CV as attachment

### Sample Email

```
Subject: 🎯 Job Match: Senior Python Developer at Tech Company

Match Score: 85%
Critique Score: 82%

WHY THIS JOB MATCHES:
• Job title matches preferences
• Matches 9/10 required skills
• Location matches preferences
• Strong match for your experience level

STRENGTHS:
✓ Clear job description
✓ Realistic requirements
✓ Good company reputation

[Tailored CV attached]

View Job: https://profesia.sk/...
```

## 🛠️ Troubleshooting

### No jobs found
- Check that job titles in `config.yaml` match profesia.sk listings
- Verify your search criteria aren't too restrictive
- Try broader location preferences (include "Remote")

### AI matching not working
- Verify API keys in `.env`
- Check API key has sufficient credits
- System will fall back to rule-based matching if AI unavailable

### Email notifications failing
- For Gmail, use App Password (not regular password)
- Enable "Less secure app access" if needed
- Check SMTP settings are correct
- Verify notification email address is valid

### Scraping errors
- Profesia.sk may have changed their HTML structure
- Update CSS selectors in `scraper_agent.py`
- Check internet connection
- Consider rate limiting (add delays between requests)

### Missing dependencies
```bash
pip install -r requirements.txt --upgrade
```

## 🔐 Security & Privacy

- **API Keys**: Never commit `.env` file to version control
- **CV Data**: Stored locally, never sent to third parties (except AI APIs for processing)
- **Credentials**: Use environment variables, not hardcoded values
- **Rate Limiting**: Respects profesia.sk servers with delays between requests

## 🚧 Known Limitations

- **Profesia.sk HTML Changes**: Web scraping may break if site structure changes
- **AI API Costs**: Using OpenAI/Anthropic incurs costs per job processed
- **Email Rate Limits**: Gmail has daily sending limits
- **Language Support**: Primarily designed for English/Slovak jobs
- **CV Formats**: Currently supports Markdown/DOCX output

## 🛣️ Roadmap

- [ ] Support for additional job boards (LinkedIn, Indeed)
- [ ] Web dashboard for monitoring and configuration
- [ ] Slack/Discord notification support
- [ ] Cover letter generation
- [ ] Application auto-submit capability
- [ ] Interview preparation agent
- [ ] Salary negotiation insights
- [ ] Job market analytics

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Enhanced web scraping (handle dynamic content)
- Additional job board integrations
- Improved CV formatting
- Better email templates
- Unit tests and CI/CD
- Documentation improvements

## 📄 License

This project is for personal use. Please respect profesia.sk's terms of service and robots.txt when scraping.

## 🙏 Acknowledgments

- Built with Claude (Anthropic) and GPT-4 (OpenAI)
- Uses BeautifulSoup for web scraping
- Email templates inspired by modern design practices

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review configuration examples

---

**Happy Job Hunting! 🎯**
