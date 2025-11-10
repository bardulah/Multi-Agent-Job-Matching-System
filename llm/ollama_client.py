"""
Ollama LLM Client

Implementation for local Ollama models (open-source).
"""

from typing import Dict, Any, Optional
from loguru import logger
import requests
import json

from .base import BaseLLMClient, LLMResponse, LLMAPIError, LLMConfigError


class OllamaLLMClient(BaseLLMClient):
    """LLM client for Ollama (local open-source models)."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Ollama client.

        Args:
            config: Configuration with 'base_url' and 'model'
        """
        super().__init__(config)

        self.base_url = config.get('base_url', 'http://localhost:11434')

        # Default to llama2 if no model specified
        if not self.model:
            self.model = 'llama2'

        logger.info(f"Ollama client initialized with model: {self.model} at {self.base_url}")

        # Test connection
        try:
            self._test_connection()
        except Exception as e:
            logger.warning(f"Could not connect to Ollama at {self.base_url}: {e}")
            logger.warning("Make sure Ollama is running: ollama serve")

    def _test_connection(self):
        """Test connection to Ollama server."""
        response = requests.get(f"{self.base_url}/api/tags", timeout=5)
        response.raise_for_status()

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Ollama."""
        try:
            # Build full prompt with system message if provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{prompt}\n<|assistant|>\n"

            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature if temperature is not None else self.temperature,
                    "num_predict": max_tokens or self.max_tokens,
                }
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120  # Ollama can be slow on CPU
            )
            response.raise_for_status()

            result = response.json()

            # Extract content
            content = result.get('response', '')

            # Approximate token counts (Ollama doesn't return exact counts)
            input_tokens = self.count_tokens(full_prompt)
            output_tokens = self.count_tokens(content)

            return LLMResponse(
                content=content,
                model=self.model,
                provider='ollama',
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=0.0,  # Ollama is free (local)
                metadata={
                    'total_duration': result.get('total_duration'),
                    'eval_count': result.get('eval_count'),
                }
            )

        except requests.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise LLMAPIError(f"Ollama API call failed: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
            raise LLMAPIError(f"Failed to generate response: {e}") from e

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate JSON response using Ollama."""
        # Add JSON instruction to prompt
        json_system = "You are a helpful assistant that always responds with valid JSON."
        if system_prompt:
            json_system = f"{system_prompt}\nAlways respond with valid JSON."

        json_prompt = f"{prompt}\n\nRespond with valid JSON only. Do not include any text outside the JSON object."

        response = self.generate(
            prompt=json_prompt,
            system_prompt=json_system,
            temperature=0.3,  # Lower temperature for structured output
            **kwargs
        )

        # Parse JSON from response
        return self._parse_json_response(response.content)

    def count_tokens(self, text: str) -> int:
        """
        Approximate token count.

        Most models use ~4 characters per token on average.
        """
        return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Ollama is free (runs locally)."""
        return 0.0

    @property
    def provider_name(self) -> str:
        return 'ollama'

    def list_models(self) -> list:
        """List available Ollama models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
