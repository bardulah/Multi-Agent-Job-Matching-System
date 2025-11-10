"""
Anthropic Claude LLM Client

Implementation for Anthropic's Claude models.
"""

from typing import Dict, Any, Optional
from loguru import logger
import anthropic

from .base import BaseLLMClient, LLMResponse, LLMAPIError, LLMConfigError


class AnthropicLLMClient(BaseLLMClient):
    """LLM client for Anthropic Claude models."""

    # Pricing per million tokens (as of 2025)
    PRICING = {
        'claude-3-opus-20240229': {'input': 15.00, 'output': 75.00},
        'claude-3-sonnet-20240229': {'input': 3.00, 'output': 15.00},
        'claude-3-haiku-20240307': {'input': 0.25, 'output': 1.25},
        'claude-sonnet-4-5-20250929': {'input': 3.00, 'output': 15.00},
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Anthropic client.

        Args:
            config: Configuration with 'api_key' and optional 'model'
        """
        super().__init__(config)

        api_key = config.get('api_key')
        if not api_key:
            raise LLMConfigError("Anthropic API key is required")

        self.client = anthropic.Anthropic(api_key=api_key)

        # Default to Sonnet if no model specified
        if not self.model:
            self.model = 'claude-sonnet-4-5-20250929'

        logger.info(f"Anthropic client initialized with model: {self.model}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Claude."""
        try:
            messages = [{"role": "user", "content": prompt}]

            kwargs_dict = {
                "model": self.model,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature,
                "messages": messages,
            }

            if system_prompt:
                kwargs_dict["system"] = system_prompt

            # Add any additional kwargs
            kwargs_dict.update(kwargs)

            response = self.client.messages.create(**kwargs_dict)

            # Extract content
            content = response.content[0].text

            # Get token usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            # Estimate cost
            cost = self.estimate_cost(input_tokens, output_tokens)

            return LLMResponse(
                content=content,
                model=self.model,
                provider='anthropic',
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                metadata={
                    'id': response.id,
                    'stop_reason': response.stop_reason,
                }
            )

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise LLMAPIError(f"Anthropic API call failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error calling Anthropic: {e}")
            raise LLMAPIError(f"Failed to generate response: {e}") from e

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate JSON response using Claude."""
        # Add JSON instruction to prompt
        json_prompt = f"{prompt}\n\nRespond with valid JSON only."

        response = self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            **kwargs
        )

        # Parse JSON from response
        return self._parse_json_response(response.content)

    def count_tokens(self, text: str) -> int:
        """
        Approximate token count for Claude.

        Claude uses ~4 characters per token on average.
        """
        return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on Claude pricing."""
        pricing = self.PRICING.get(
            self.model,
            {'input': 3.00, 'output': 15.00}  # Default to Sonnet pricing
        )

        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']

        return input_cost + output_cost

    @property
    def provider_name(self) -> str:
        return 'anthropic'
