"""
LLM Client Factory

Creates appropriate LLM client based on configuration.
"""

from typing import Dict, Any
from loguru import logger

from .base import BaseLLMClient, LLMConfigError
from .anthropic_client import AnthropicLLMClient
from .openai_client import OpenAILLMClient
from .ollama_client import OllamaLLMClient


def create_llm_client(config: Dict[str, Any]) -> BaseLLMClient:
    """
    Create an LLM client based on configuration.

    Args:
        config: LLM configuration dictionary with 'provider' key

    Returns:
        Instantiated LLM client

    Raises:
        LLMConfigError: If provider is unsupported or config is invalid

    Example:
        ```python
        config = {
            'provider': 'anthropic',
            'api_key': 'sk-ant-...',
            'model': 'claude-sonnet-4-5-20250929',
            'temperature': 0.7,
            'max_tokens': 4000
        }
        client = create_llm_client(config)
        response = client.generate("What is Python?")
        ```
    """
    provider = config.get('provider', '').lower()

    if not provider:
        raise LLMConfigError("LLM provider not specified in configuration")

    logger.info(f"Creating LLM client for provider: {provider}")

    if provider == 'anthropic':
        return AnthropicLLMClient(config)
    elif provider == 'openai':
        return OpenAILLMClient(config)
    elif provider == 'ollama':
        return OllamaLLMClient(config)
    else:
        raise LLMConfigError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: anthropic, openai, ollama"
        )


def get_available_providers() -> Dict[str, Dict[str, Any]]:
    """
    Get information about available LLM providers.

    Returns:
        Dictionary with provider info
    """
    return {
        'anthropic': {
            'name': 'Anthropic Claude',
            'models': [
                'claude-sonnet-4-5-20250929',
                'claude-3-opus-20240229',
                'claude-3-sonnet-20240229',
                'claude-3-haiku-20240307',
            ],
            'requires_api_key': True,
            'pricing': 'Paid (per token)',
            'speed': 'Fast',
            'quality': 'Excellent',
        },
        'openai': {
            'name': 'OpenAI GPT',
            'models': [
                'gpt-4o',
                'gpt-4o-mini',
                'gpt-4-turbo',
                'gpt-4',
                'gpt-3.5-turbo',
            ],
            'requires_api_key': True,
            'pricing': 'Paid (per token)',
            'speed': 'Fast',
            'quality': 'Excellent',
        },
        'ollama': {
            'name': 'Ollama (Local)',
            'models': [
                'llama2',
                'llama3',
                'mistral',
                'mixtral',
                'codellama',
                'phi',
            ],
            'requires_api_key': False,
            'pricing': 'Free (local)',
            'speed': 'Depends on hardware',
            'quality': 'Good',
            'notes': 'Requires Ollama installed locally'
        },
    }


def print_provider_info():
    """Print information about available providers."""
    providers = get_available_providers()

    print("\n" + "=" * 80)
    print("AVAILABLE LLM PROVIDERS")
    print("=" * 80)

    for provider_id, info in providers.items():
        print(f"\n{info['name']} ({provider_id})")
        print("-" * 40)
        print(f"  Requires API Key: {info['requires_api_key']}")
        print(f"  Pricing: {info['pricing']}")
        print(f"  Speed: {info['speed']}")
        print(f"  Quality: {info['quality']}")
        if 'notes' in info:
            print(f"  Notes: {info['notes']}")
        print(f"  Example Models:")
        for model in info['models'][:3]:
            print(f"    - {model}")

    print("\n" + "=" * 80)
