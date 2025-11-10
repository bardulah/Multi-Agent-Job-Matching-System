# Quick Start Guide

Get the Multi-Agent Job Application System up and running in 5 minutes!

## Prerequisites

- Python 3.8+
- Anthropic API key ([get one here](https://console.anthropic.com/))
- Gmail account (or other email service)

## Installation

### 1. Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Create necessary directories
- Copy example configuration files

### 2. Configure API Keys

Edit the `.env` file:

```bash
nano .env
```

Add your credentials:
```env
ANTHROPIC_API_KEY=sk-ant-api03-...
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your_app_password
```

**Gmail users**: Generate an App Password at https://myaccount.google.com/apppasswords

### 3. Set Your Preferences

Edit `config.yaml`:

```bash
nano config.yaml
```

Minimum required changes:
- Update `user` section with your name and email
- Add your skills to `skills` section
- Set job `keywords` you're interested in

### 4. Test Configuration

```bash
python orchestrator.py --test
```

You should see:
```
✓ Configuration loaded successfully
✓ LLM API key found
✓ Email credentials found
✓ Test email sent successfully
```

### 5. Run Your First Job Search

```bash
python orchestrator.py
```

The system will:
1. Search profesia.sk for matching jobs
2. Generate tailored CVs
3. Critique each CV
4. Send you a summary email (if enabled)

## Expected Output

```
================================================================================
Job Application System Starting
================================================================================
[INFO] Orchestrator initialized successfully
[INFO] Starting daily job application cycle
[INFO] Step 1: Fetching jobs from profesia.sk
[INFO] Fetched 25 jobs
[INFO] 8 jobs matched preferences
[INFO] Processing job 1/8: Python Developer at TechCorp
  → Tailoring CV...
  → Critiquing CV...
  ✓ Job processed. Match: 85%, Critique: 8.2/10, Status: approved
...
[INFO] 6 jobs approved
[INFO] Email notification sent
================================================================================
Daily cycle complete
================================================================================
```

## First Run Tips

### Enable Manual Review Mode

For your first run, disable auto-send to review results:

In `config.yaml`:
```yaml
system:
  enable_auto_send: false  # Review before sending
```

Results will be saved to `data/review/YYYY-MM-DD/`

### Lower Match Threshold

If you're getting too few matches, try lowering the threshold:

```yaml
system:
  min_match_score: 0.5  # Default is 0.6
```

### Limit Jobs Processed

Start with a small number to test:

```yaml
system:
  max_jobs_per_day: 3  # Process only 3 jobs
```

## Scheduling (Optional)

### Using Cron

Add to your crontab (runs daily at 8 AM):

```bash
crontab -e
```

Add this line:
```cron
0 8 * * * /full/path/to/jobs/run_daily.sh >> /full/path/to/jobs/logs/cron.log 2>&1
```

### Using Python Scheduler

```bash
python schedule.py
```

Leave it running in the background.

## Checking Results

### View Generated CVs

```bash
ls -lh data/cvs/
```

### View Logs

```bash
tail -f logs/job_system_$(date +%Y-%m-%d).log
```

### Check History

```bash
cat data/history/job_history.json | jq .stats
```

## Common Issues

### "No jobs found"

- Check profesia.sk is accessible
- Try broader keywords
- Lower `min_match_score`

### "Email not sending"

- Verify email credentials in `.env`
- For Gmail, use App Password, not regular password
- Check SMTP settings in `config.yaml`

### "API error"

- Verify Anthropic API key is correct
- Check you have API credits
- Ensure API key has proper permissions

## Next Steps

1. **Customize your CV template** - Add `templates/cv_template.docx`
2. **Fine-tune matching** - Adjust keywords and skills in `config.yaml`
3. **Set up automation** - Enable cron or scheduler
4. **Monitor results** - Check daily emails and logs

## Getting Help

- See full documentation in `README.md`
- Check logs in `logs/` directory
- View generated CVs in `data/cvs/`
- Check job history in `data/history/`

## What's Next?

The system will now:
- Run daily (if scheduled)
- Find relevant jobs
- Tailor your CV for each job
- Send you daily summaries
- Track application history

Just review the daily emails and apply to the jobs you like!

---

**Pro Tip**: Start with `enable_auto_send: false` and review the first few days of results to ensure everything is working as expected before enabling automatic emails.
