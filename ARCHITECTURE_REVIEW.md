# Architecture Review & Improvements

## Retrospective: What I Would Do Differently

### 1. **Data Layer - Use Proper Database**

**Current:** JSON files for history tracking
**Better:** SQLite (or PostgreSQL for production)

```python
# Instead of JSON:
# data/history/job_history.json

# Use SQLAlchemy models:
class JobApplication(Base):
    id = Column(Integer, primary_key=True)
    job_url = Column(String, unique=True, index=True)
    title = Column(String)
    company = Column(String)
    match_score = Column(Float)
    cv_path = Column(String)
    critique_score = Column(Float)
    status = Column(Enum('pending', 'approved', 'rejected', 'sent'))
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Benefits:**
- Better querying and indexing
- ACID compliance
- Easier analytics
- Better concurrency

### 2. **Configuration Validation - Use Pydantic**

**Current:** Manual validation in ConfigLoader
**Better:** Pydantic models for type safety

```python
from pydantic import BaseModel, EmailStr, HttpUrl

class UserConfig(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str]
    linkedin: Optional[HttpUrl]

class SystemConfig(BaseModel):
    user: UserConfig
    job_preferences: JobPreferences
    # Auto-validation, type checking, serialization
```

**Benefits:**
- Automatic validation
- Type hints everywhere
- Better error messages
- JSON schema generation

### 3. **Async/Await for Performance**

**Current:** Synchronous I/O operations
**Better:** Async for web requests and LLM calls

```python
import asyncio
import aiohttp

async def fetch_jobs_async(self, urls):
    async with aiohttp.ClientSession() as session:
        tasks = [self._fetch_page_async(session, url) for url in urls]
        return await asyncio.gather(*tasks)
```

**Benefits:**
- 5-10x faster job processing
- Better resource utilization
- Handle more jobs concurrently

### 4. **Abstract Base Classes for Agents**

**Current:** Independent agent classes
**Better:** Common interface via ABC

```python
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger(self.__class__.__name__)

    @abstractmethod
    def process(self, input_data):
        """Each agent implements its processing logic"""
        pass

    def log_metrics(self):
        """Common metrics logging"""
        pass
```

**Benefits:**
- Consistent interface
- Easier testing with mocks
- Plugin architecture possible

### 5. **Dependency Injection Container**

**Current:** Manual dependency passing
**Better:** DI container pattern

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Singleton(ConfigLoader)

    job_fetcher = providers.Factory(
        JobFetcherAgent,
        config=config
    )

    cv_tailor = providers.Factory(
        CVTailorAgent,
        config=config,
        llm_client=llm_client
    )
```

**Benefits:**
- Loose coupling
- Easier testing
- Better lifecycle management

### 6. **LLM Response Caching**

**Current:** Every job makes new LLM calls
**Better:** Cache responses for similar jobs

```python
import hashlib
from functools import lru_cache

def cache_key(job_description: str) -> str:
    return hashlib.md5(job_description.encode()).hexdigest()

# Cache job analysis for 24 hours
@cached(ttl=86400)
def analyze_job(self, job_desc: str):
    ...
```

**Benefits:**
- Significant cost savings
- Faster processing
- Reduced API rate limiting issues

### 7. **Better Error Handling with Custom Exceptions**

**Current:** Generic try/except blocks
**Better:** Custom exception hierarchy

```python
class JobSystemError(Exception):
    """Base exception"""
    pass

class ScrapingError(JobSystemError):
    """Web scraping failed"""
    pass

class LLMError(JobSystemError):
    """LLM API call failed"""
    pass

class ConfigurationError(JobSystemError):
    """Invalid configuration"""
    pass

# Specific handling:
try:
    jobs = fetcher.fetch()
except ScrapingError as e:
    logger.error(f"Scraping failed: {e}")
    # Fall back to cached jobs
except LLMError as e:
    logger.error(f"LLM failed: {e}")
    # Use simpler matching algorithm
```

### 8. **Retry Strategy with Exponential Backoff**

**Current:** Simple delays
**Better:** Sophisticated retry logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.RequestException)
)
def fetch_with_retry(self, url):
    response = requests.get(url)
    response.raise_for_status()
    return response
```

### 9. **Structured Logging**

**Current:** String-based logs
**Better:** Structured JSON logs

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "job_processed",
    job_id=job_id,
    match_score=0.85,
    critique_score=8.2,
    duration_seconds=12.5,
    status="approved"
)

# Easy to query and analyze
```

### 10. **Message Queue for Agent Communication**

**Current:** Direct method calls
**Better:** Message queue pattern

```python
from queue import Queue

class MessageBus:
    def __init__(self):
        self.queues = {
            'jobs_fetched': Queue(),
            'cvs_tailored': Queue(),
            'cvs_critiqued': Queue(),
        }

    def publish(self, topic, message):
        self.queues[topic].put(message)

    def subscribe(self, topic):
        return self.queues[topic].get()
```

**Benefits:**
- Decoupled agents
- Can scale to distributed systems
- Easier to add new agents

### 11. **Web Scraping Improvements**

**Current:** BeautifulSoup with requests
**Better:** Playwright/Selenium for dynamic content

```python
from playwright.async_api import async_playwright

async def scrape_with_playwright(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_selector('.job-listing')
        content = await page.content()
        await browser.close()
        return content
```

**Benefits:**
- Handle JavaScript-rendered pages
- More reliable scraping
- Can take screenshots for debugging

### 12. **Prompt Management System**

**Current:** Prompts hardcoded in methods
**Better:** External prompt templates

```python
# prompts/cv_tailor.jinja2
You are a professional CV writer. Tailor this CV for:

Job Title: {{ job.title }}
Company: {{ job.company }}

Requirements:
{% for req in requirements %}
- {{ req }}
{% endfor %}

User Skills:
{% for skill in user_skills %}
- {{ skill }}
{% endfor %}
```

**Benefits:**
- Easy to iterate on prompts
- Version control for prompts
- A/B testing different prompts

### 13. **Cost Tracking**

**Current:** No cost visibility
**Better:** Track API costs

```python
class CostTracker:
    def __init__(self):
        self.costs = []

    def track_llm_call(self, model, input_tokens, output_tokens):
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        self.costs.append({
            'timestamp': datetime.now(),
            'model': model,
            'cost': cost
        })

    def get_daily_cost(self):
        today = datetime.now().date()
        return sum(c['cost'] for c in self.costs
                   if c['timestamp'].date() == today)
```

### 14. **Circuit Breaker Pattern**

**Current:** Keep retrying failed services
**Better:** Circuit breaker to prevent cascading failures

```python
from pybreaker import CircuitBreaker

llm_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=60
)

@llm_breaker
def call_llm_api(prompt):
    return client.messages.create(...)

# After 5 failures, circuit opens for 60 seconds
# Prevents wasting time/money on broken service
```

### 15. **Progressive Enhancement Strategy**

**Current:** All-or-nothing approach
**Better:** Graceful degradation

```python
def tailor_cv(self, job):
    try:
        # Try AI-powered tailoring
        return self._tailor_with_llm(job)
    except LLMError:
        logger.warning("LLM failed, using template-based tailoring")
        # Fall back to template-based approach
        return self._tailor_with_template(job)
    except Exception:
        logger.error("All tailoring failed, using base CV")
        # Last resort: use base CV
        return self._load_base_cv()
```

### 16. **Health Check Endpoint**

**Current:** No system health visibility
**Better:** Health check API

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'components': {
            'llm_api': check_llm_health(),
            'email_smtp': check_email_health(),
            'profesia_sk': check_scraping_health()
        },
        'last_run': get_last_run_time(),
        'jobs_processed_today': get_daily_job_count()
    })
```

### 17. **Testing Infrastructure**

**Current:** Basic unit tests
**Better:** Comprehensive test suite

```python
# tests/conftest.py
@pytest.fixture
def mock_llm_client():
    with patch('anthropic.Anthropic') as mock:
        mock.return_value.messages.create.return_value = {
            'content': [{'text': '{"score": 8.5}'}]
        }
        yield mock

# tests/integration/test_full_workflow.py
def test_end_to_end_workflow(mock_llm_client, mock_scraper):
    orchestrator = JobApplicationOrchestrator()
    result = orchestrator.run_daily_cycle()
    assert result['status'] == 'success'
    assert result['jobs_processed'] > 0
```

### 18. **Configuration Profiles**

**Current:** Single config file
**Better:** Environment-specific configs

```python
# config/base.yaml - Common settings
# config/dev.yaml - Development overrides
# config/prod.yaml - Production overrides

class ConfigLoader:
    def __init__(self, env='dev'):
        base = self._load('config/base.yaml')
        env_config = self._load(f'config/{env}.yaml')
        self.config = {**base, **env_config}
```

### 19. **Observability Dashboard**

**Current:** Log files only
**Better:** Metrics dashboard

```python
from prometheus_client import Counter, Histogram, start_http_server

jobs_processed = Counter('jobs_processed_total', 'Total jobs processed')
cv_generation_time = Histogram('cv_generation_seconds', 'Time to generate CV')
match_score = Histogram('job_match_score', 'Job match scores')

# Expose metrics on :9090/metrics
start_http_server(9090)
```

### 20. **Rate Limiting Client-Side**

**Current:** Simple delays
**Better:** Token bucket algorithm

```python
from ratelimit import limits, sleep_and_retry

class RateLimitedClient:
    @sleep_and_retry
    @limits(calls=10, period=60)  # 10 calls per minute
    def fetch_page(self, url):
        return requests.get(url)
```

## Summary: Priority Improvements

### High Priority (Do First)
1. ✅ **LLM Model Agnosticism** - Support multiple providers
2. **Pydantic for validation** - Type safety
3. **SQLite database** - Better data management
4. **Async/await** - Performance boost
5. **Better error handling** - Custom exceptions

### Medium Priority (Nice to Have)
6. **Response caching** - Cost savings
7. **Structured logging** - Better debugging
8. **Prompt templates** - Easier iteration
9. **Health checks** - System monitoring
10. **Cost tracking** - Budget management

### Low Priority (Future)
11. **Message queue** - Scalability
12. **Circuit breaker** - Resilience
13. **Metrics dashboard** - Observability
14. **Integration tests** - Quality assurance
15. **Web UI** - User experience

## Conclusion

The current implementation is **solid and production-ready**, but these improvements would make it more:
- **Robust**: Better error handling and resilience
- **Performant**: Async operations and caching
- **Maintainable**: Better architecture and testing
- **Observable**: Metrics and monitoring
- **Scalable**: Can handle more jobs and users

Many of these are "nice to haves" that you'd add as the system grows and you understand real usage patterns better. Starting simple (as we did) is often the right choice!
