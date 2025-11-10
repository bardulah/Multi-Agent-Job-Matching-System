# LLM Providers Guide

The Multi-Agent Job Application System now supports multiple LLM providers, allowing you to choose the AI service that best fits your needs, budget, and preferences.

## Supported Providers

### 1. Anthropic Claude (Recommended)
**Best for: High-quality, reliable results**

#### Pros:
- ✅ Excellent understanding of nuanced requirements
- ✅ Very good at structured output (JSON)
- ✅ Strong reasoning capabilities
- ✅ Good at following complex instructions
- ✅ Default and well-tested

#### Cons:
- ❌ Requires API key and credit card
- ❌ Costs money (but reasonable)

#### Setup:
```yaml
# config.yaml
llm:
  provider: "anthropic"
  api_key_env: "ANTHROPIC_API_KEY"
  model: "claude-sonnet-4-5-20250929"  # Balanced option
  # Options:
  # - claude-3-opus-20240229 (best quality, $15/$75 per M tokens)
  # - claude-sonnet-4-5-20250929 (balanced, $3/$15 per M tokens) ← Recommended
  # - claude-3-haiku-20240307 (fastest/cheapest, $0.25/$1.25 per M tokens)
```

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

#### Cost Estimate:
- **Daily (10 jobs)**: $0.10 - $0.30
- **Monthly**: $3 - $9
- Get API key: https://console.anthropic.com/

---

### 2. OpenAI GPT (Alternative)
**Best for: Familiarity, wide adoption**

#### Pros:
- ✅ Well-known and widely used
- ✅ Good performance
- ✅ JSON mode support
- ✅ Multiple model options

#### Cons:
- ❌ Requires API key and credit card
- ❌ Can be more expensive
- ❌ Sometimes less consistent with complex instructions

#### Setup:
```yaml
# config.yaml
llm:
  provider: "openai"
  api_key_env: "OPENAI_API_KEY"
  model: "gpt-4o-mini"  # Cost-effective
  # Options:
  # - gpt-4o ($5/$15 per M tokens) - Balanced
  # - gpt-4o-mini ($0.15/$0.60 per M tokens) - Cheapest ← Recommended for budget
  # - gpt-4-turbo ($10/$30 per M tokens) - High quality
  # - gpt-4 ($30/$60 per M tokens) - Best quality
```

```bash
# .env
OPENAI_API_KEY=sk-xxxxx
```

#### Additional Setup:
```bash
# Uncomment in requirements.txt and install:
pip install openai>=1.0.0 tiktoken>=0.5.0
```

#### Cost Estimate:
- **Daily (10 jobs)**: $0.05 - $0.50
- **Monthly**: $1.50 - $15
- Get API key: https://platform.openai.com/api-keys

---

### 3. Ollama (Local/Open-Source)
**Best for: Privacy, zero cost, offline usage**

#### Pros:
- ✅ Completely free
- ✅ No API key needed
- ✅ Runs locally (privacy)
- ✅ Works offline
- ✅ No per-request costs

#### Cons:
- ❌ Requires local installation
- ❌ Slower on CPU (needs good GPU for speed)
- ❌ Lower quality than Claude/GPT
- ❌ Requires more manual setup

#### Setup:

**Step 1: Install Ollama**
```bash
# Mac/Linux
curl https://ollama.ai/install.sh | sh

# Or download from: https://ollama.ai/download
```

**Step 2: Pull a Model**
```bash
# Recommended models:
ollama pull llama2        # Good balance
ollama pull llama3        # Better quality, larger
ollama pull mistral       # Fast and capable
ollama pull mixtral       # Best quality, slow
ollama pull phi           # Very fast, smaller
```

**Step 3: Start Ollama Server**
```bash
ollama serve  # Keep running in a terminal
```

**Step 4: Configure System**
```yaml
# config.yaml
llm:
  provider: "ollama"
  base_url: "http://localhost:11434"  # Default Ollama port
  model: "llama2"  # Or llama3, mistral, mixtral, phi
  max_tokens: 4000
  temperature: 0.7
```

```bash
# .env
# No API key needed!
```

#### Cost Estimate:
- **Daily**: $0 (free!)
- **Monthly**: $0 (free!)
- **Hardware**: Runs on your computer
  - CPU: Slow but works (minutes per job)
  - GPU: Much faster (seconds per job)

#### Performance Tips:
- Use smaller models (llama2, phi) for faster results
- Use GPU if available (NVIDIA, Apple Silicon)
- Consider mixtral for best quality (but slower)

---

## Comparison Table

| Feature | Anthropic Claude | OpenAI GPT | Ollama |
|---------|-----------------|------------|---------|
| **Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Speed** | ⚡⚡⚡⚡ | ⚡⚡⚡⚡ | ⚡⚡ (CPU) / ⚡⚡⚡⚡ (GPU) |
| **Cost/Day** | $0.10-0.30 | $0.05-0.50 | $0 |
| **Setup** | Easy | Easy | Medium |
| **Privacy** | Cloud | Cloud | Local ✓ |
| **Offline** | ❌ | ❌ | ✓ |
| **Reliability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## Switching Providers

You can easily switch between providers by editing `config.yaml`:

```yaml
# Try different providers:
llm:
  # provider: "anthropic"  # Option 1
  # provider: "openai"     # Option 2
  provider: "ollama"       # Option 3 (active)
```

Then set the appropriate API key in `.env` (if needed).

## Recommendations

### For Most Users
**Use Anthropic Claude Sonnet 4.5**
- Best balance of quality and cost
- Reliable and well-tested
- ~$5/month for typical usage

### For Budget-Conscious Users
**Use OpenAI GPT-4o-mini**
- Very affordable ($1-2/month)
- Still good quality
- Fast and reliable

### For Privacy/Offline Users
**Use Ollama with Llama2 or Mistral**
- Completely free
- No data leaves your machine
- Good enough for most use cases

### For Maximum Quality
**Use Anthropic Claude Opus**
- Best possible results
- Worth it for important applications
- ~$15/month

## Testing Different Providers

You can test each provider:

```bash
# Test your current configuration
python orchestrator.py --test

# Or use the provider info tool
python -c "from llm.factory import print_provider_info; print_provider_info()"
```

## Troubleshooting

### Anthropic Issues
- **"API key not found"**: Set `ANTHROPIC_API_KEY` in `.env`
- **"Insufficient credits"**: Add payment method at console.anthropic.com
- **Rate limits**: Use haiku model or slow down requests

### OpenAI Issues
- **"Invalid API key"**: Check `OPENAI_API_KEY` in `.env`
- **"Model not found"**: Use correct model name (e.g., `gpt-4o-mini`)
- **Install error**: `pip install openai tiktoken`

### Ollama Issues
- **"Connection refused"**: Start Ollama server with `ollama serve`
- **"Model not found"**: Pull model with `ollama pull <model-name>`
- **Slow performance**: Use smaller model or GPU
- **Installation**: Visit https://ollama.ai/download

## Advanced: Custom Models

You can use any model supported by your provider:

```yaml
llm:
  provider: "anthropic"
  model: "claude-3-opus-20240229"  # Use specific model

  # Or for OpenAI:
  # provider: "openai"
  # model: "gpt-4-turbo-preview"

  # Or for Ollama:
  # provider: "ollama"
  # model: "codellama:13b"  # Specific size variant
```

## Cost Tracking

The system tracks LLM costs automatically:

```python
# Each LLM response includes cost information
response = llm_client.generate("Your prompt")
print(f"Cost: ${response.cost_usd:.4f}")
print(f"Input tokens: {response.input_tokens}")
print(f"Output tokens: {response.output_tokens}")
```

## Best Practices

1. **Start with the default** (Anthropic Sonnet) - it's well-tested
2. **Monitor costs** in your first few runs
3. **Try Ollama** if you have a good GPU or want privacy
4. **Use cheaper models** for testing/development
5. **Switch providers** anytime without code changes

---

**Need help choosing?** Use this flowchart:

```
Do you need maximum quality?
  ├─ Yes → Anthropic Claude Opus
  └─ No ↓

Do you want it free/offline?
  ├─ Yes → Ollama (llama2 or mistral)
  └─ No ↓

Budget < $3/month?
  ├─ Yes → OpenAI GPT-4o-mini
  └─ No → Anthropic Claude Sonnet (Recommended) ✓
```
