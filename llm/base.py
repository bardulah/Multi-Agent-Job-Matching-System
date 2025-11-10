"""
Base LLM Client Interface

Abstract base class that all LLM clients must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""

    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return self.content


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM client.

        Args:
            config: Configuration dictionary with provider-specific settings
        """
        self.config = config
        self.model = config.get('model')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 4000)

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            prompt: The user prompt/query
            system_prompt: Optional system prompt to set behavior
            temperature: Override default temperature
            max_tokens: Override default max tokens
            **kwargs: Provider-specific additional parameters

        Returns:
            LLMResponse object with content and metadata
        """
        pass

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from the LLM.

        Args:
            prompt: The user prompt/query
            system_prompt: Optional system prompt
            schema: Optional JSON schema for validation
            **kwargs: Provider-specific parameters

        Returns:
            Parsed JSON dictionary
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text (approximate).

        Args:
            text: Text to count tokens for

        Returns:
            Approximate token count
        """
        pass

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'anthropic', 'openai')."""
        pass

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling markdown code blocks.

        Args:
            content: Raw response content

        Returns:
            Parsed JSON dictionary
        """
        import json

        # Try to extract JSON from markdown code blocks
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]

        # Clean up content
        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\nContent: {content}")


class LLMClientError(Exception):
    """Base exception for LLM client errors."""
    pass


class LLMAPIError(LLMClientError):
    """API call to LLM provider failed."""
    pass


class LLMResponseError(LLMClientError):
    """LLM response was invalid or couldn't be parsed."""
    pass


class LLMConfigError(LLMClientError):
    """LLM client configuration is invalid."""
    pass
