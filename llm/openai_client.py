"""
OpenAI LLM Client

Implementation for OpenAI's GPT models.
"""

from typing import Dict, Any, Optional
from loguru import logger

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed. Install with: pip install openai")

from .base import BaseLLMClient, LLMResponse, LLMAPIError, LLMConfigError


class OpenAILLMClient(BaseLLMClient):
    """LLM client for OpenAI GPT models."""

    # Pricing per million tokens (as of 2025)
    PRICING = {
        'gpt-4': {'input': 30.00, 'output': 60.00},
        'gpt-4-turbo': {'input': 10.00, 'output': 30.00},
        'gpt-4o': {'input': 5.00, 'output': 15.00},
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50},
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI client.

        Args:
            config: Configuration with 'api_key' and optional 'model'
        """
        super().__init__(config)

        if not OPENAI_AVAILABLE:
            raise LLMConfigError(
                "OpenAI library not installed. Install with: pip install openai"
            )

        api_key = config.get('api_key')
        if not api_key:
            raise LLMConfigError("OpenAI API key is required")

        self.client = openai.OpenAI(api_key=api_key)

        # Default to GPT-4o-mini if no model specified
        if not self.model:
            self.model = 'gpt-4o-mini'

        logger.info(f"OpenAI client initialized with model: {self.model}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using GPT."""
        try:
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs
            )

            # Extract content
            content = response.choices[0].message.content

            # Get token usage
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            # Estimate cost
            cost = self.estimate_cost(input_tokens, output_tokens)

            return LLMResponse(
                content=content,
                model=self.model,
                provider='openai',
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                metadata={
                    'id': response.id,
                    'finish_reason': response.choices[0].finish_reason,
                }
            )

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMAPIError(f"OpenAI API call failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {e}")
            raise LLMAPIError(f"Failed to generate response: {e}") from e

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate JSON response using GPT."""
        # Use response_format for JSON mode (available in newer models)
        if 'response_format' not in kwargs:
            kwargs['response_format'] = {"type": "json_object"}

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
        Approximate token count for GPT models.

        GPT models use ~4 characters per token on average.
        For precise counting, use tiktoken library.
        """
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except ImportError:
            # Fallback to approximation
            return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on OpenAI pricing."""
        pricing = self.PRICING.get(
            self.model,
            {'input': 0.15, 'output': 0.60}  # Default to GPT-4o-mini pricing
        )

        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']

        return input_cost + output_cost

    @property
    def provider_name(self) -> str:
        return 'openai'
