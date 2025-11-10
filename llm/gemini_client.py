"""
Google Gemini LLM Client

Implementation for Google's Gemini models.
"""

from typing import Dict, Any, Optional
from loguru import logger
import json

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")

from .base import BaseLLMClient, LLMResponse, LLMAPIError, LLMConfigError


class GeminiLLMClient(BaseLLMClient):
    """LLM client for Google Gemini models."""

    # Pricing per million tokens (as of 2025)
    # https://ai.google.dev/pricing
    PRICING = {
        'gemini-1.5-pro': {'input': 1.25, 'output': 5.00},
        'gemini-1.5-pro-002': {'input': 1.25, 'output': 5.00},
        'gemini-1.5-flash': {'input': 0.075, 'output': 0.30},
        'gemini-1.5-flash-002': {'input': 0.075, 'output': 0.30},
        'gemini-1.5-flash-8b': {'input': 0.0375, 'output': 0.15},
        'gemini-2.0-flash-exp': {'input': 0.00, 'output': 0.00},  # Free during preview
        'gemini-exp-1206': {'input': 0.00, 'output': 0.00},  # Experimental - free
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Gemini client.

        Args:
            config: Configuration with 'api_key' and optional 'model'
        """
        if not GEMINI_AVAILABLE:
            raise LLMConfigError(
                "google-generativeai library not installed. "
                "Install with: pip install google-generativeai"
            )

        super().__init__(config)

        api_key = config.get('api_key')
        if not api_key:
            raise LLMConfigError("Gemini API key is required")

        # Configure the Gemini client
        genai.configure(api_key=api_key)

        # Default to Flash if no model specified (fast and cheap)
        if not self.model:
            self.model = 'gemini-1.5-flash-002'

        # Initialize the model
        generation_config = {
            'temperature': self.temperature,
            'max_output_tokens': self.max_tokens,
        }

        self.model_instance = genai.GenerativeModel(
            model_name=self.model,
            generation_config=generation_config
        )

        logger.info(f"✨ Gemini client initialized with model: {self.model}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Gemini."""
        try:
            # Build the full prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Update generation config if overrides provided
            generation_config = {}
            if temperature is not None:
                generation_config['temperature'] = temperature
            if max_tokens is not None:
                generation_config['max_output_tokens'] = max_tokens

            # Generate response
            if generation_config:
                response = self.model_instance.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
            else:
                response = self.model_instance.generate_content(full_prompt)

            # Extract content
            content = response.text

            # Get token usage (if available)
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, 'usage_metadata'):
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count

            # Estimate cost
            cost = self.estimate_cost(input_tokens, output_tokens)

            return LLMResponse(
                content=content,
                model=self.model,
                provider='gemini',
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                metadata={
                    'finish_reason': response.candidates[0].finish_reason if response.candidates else None,
                }
            )

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise LLMAPIError(f"Gemini API call failed: {e}") from e

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate JSON response using Gemini.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            schema: Optional JSON schema (not enforced by Gemini)
            **kwargs: Additional parameters

        Returns:
            Parsed JSON dictionary
        """
        # Add JSON instruction to prompt
        json_prompt = f"{prompt}\n\nRespond with valid JSON only."
        if schema:
            json_prompt += f"\n\nFollow this schema:\n{json.dumps(schema, indent=2)}"

        response = self.generate(
            prompt=json_prompt,
            system_prompt=system_prompt,
            **kwargs
        )

        # Parse JSON from response
        try:
            return self._parse_json_response(response.content)
        except ValueError as e:
            logger.error(f"Failed to parse JSON from Gemini: {e}")
            # Try one more time with stricter prompt
            retry_prompt = f"{prompt}\n\nIMPORTANT: Return ONLY valid JSON, no explanation."
            retry_response = self.generate(
                prompt=retry_prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for more structured output
                **kwargs
            )
            return self._parse_json_response(retry_response.content)

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using Gemini's tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            Token count
        """
        try:
            result = self.model_instance.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            logger.warning(f"Token counting failed, using approximation: {e}")
            # Fallback: approximate as ~4 chars per token
            return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for Gemini token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        pricing = self.PRICING.get(self.model, {'input': 1.25, 'output': 5.00})

        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']

        return input_cost + output_cost

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return 'gemini'
