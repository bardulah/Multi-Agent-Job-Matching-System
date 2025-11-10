"""
Tests for LLM Clients
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from llm import create_llm_client, BaseLLMClient, LLMResponse
from llm.anthropic_client import AnthropicLLMClient
from llm.openai_client import OpenAILLMClient
from llm.ollama_client import OllamaLLMClient
from llm.base import LLMConfigError


def test_create_anthropic_client():
    """Test creating Anthropic client."""
    config = {
        'provider': 'anthropic',
        'api_key': 'test_key',
        'model': 'claude-sonnet-4-5-20250929'
    }

    with patch('llm.anthropic_client.anthropic.Anthropic'):
        client = create_llm_client(config)
        assert isinstance(client, AnthropicLLMClient)
        assert client.provider_name == 'anthropic'


def test_create_openai_client():
    """Test creating OpenAI client."""
    config = {
        'provider': 'openai',
        'api_key': 'test_key',
        'model': 'gpt-4o-mini'
    }

    with patch('llm.openai_client.OPENAI_AVAILABLE', True):
        with patch('llm.openai_client.openai.OpenAI'):
            client = create_llm_client(config)
            assert isinstance(client, OpenAILLMClient)
            assert client.provider_name == 'openai'


def test_create_ollama_client():
    """Test creating Ollama client."""
    config = {
        'provider': 'ollama',
        'model': 'llama2',
        'base_url': 'http://localhost:11434'
    }

    with patch('llm.ollama_client.requests.get'):
        client = create_llm_client(config)
        assert isinstance(client, OllamaLLMClient)
        assert client.provider_name == 'ollama'


def test_invalid_provider():
    """Test that invalid provider raises error."""
    config = {
        'provider': 'invalid_provider',
        'api_key': 'test_key'
    }

    with pytest.raises(LLMConfigError):
        create_llm_client(config)


def test_missing_api_key_anthropic():
    """Test that missing API key raises error for Anthropic."""
    config = {
        'provider': 'anthropic',
        # Missing api_key
    }

    with pytest.raises(LLMConfigError):
        create_llm_client(config)


def test_anthropic_cost_estimation():
    """Test Anthropic cost estimation."""
    config = {
        'provider': 'anthropic',
        'api_key': 'test_key',
        'model': 'claude-sonnet-4-5-20250929'
    }

    with patch('llm.anthropic_client.anthropic.Anthropic'):
        client = create_llm_client(config)

        # Test cost estimation
        input_tokens = 1000
        output_tokens = 500
        cost = client.estimate_cost(input_tokens, output_tokens)

        # Sonnet pricing: $3/M input, $15/M output
        expected_cost = (1000 / 1_000_000 * 3) + (500 / 1_000_000 * 15)
        assert abs(cost - expected_cost) < 0.0001


def test_anthropic_token_counting():
    """Test token counting approximation."""
    config = {
        'provider': 'anthropic',
        'api_key': 'test_key',
        'model': 'claude-sonnet-4-5-20250929'
    }

    with patch('llm.anthropic_client.anthropic.Anthropic'):
        client = create_llm_client(config)

        text = "This is a test" * 100  # ~400 characters
        tokens = client.count_tokens(text)

        # Should be approximately text_length / 4
        assert tokens > 0
        assert tokens < len(text)


@patch('llm.anthropic_client.anthropic.Anthropic')
def test_anthropic_generate(mock_anthropic):
    """Test Anthropic generate method."""
    config = {
        'provider': 'anthropic',
        'api_key': 'test_key',
        'model': 'claude-sonnet-4-5-20250929'
    }

    # Mock the response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Test response")]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    mock_response.id = "test_id"
    mock_response.stop_reason = "end_turn"

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    client = create_llm_client(config)
    response = client.generate("Test prompt")

    assert isinstance(response, LLMResponse)
    assert response.content == "Test response"
    assert response.input_tokens == 100
    assert response.output_tokens == 50
    assert response.provider == 'anthropic'
    assert response.cost_usd > 0


@patch('llm.anthropic_client.anthropic.Anthropic')
def test_anthropic_generate_json(mock_anthropic):
    """Test Anthropic JSON generation."""
    config = {
        'provider': 'anthropic',
        'api_key': 'test_key',
        'model': 'claude-sonnet-4-5-20250929'
    }

    # Mock the response with JSON
    json_content = '{"key": "value", "number": 42}'
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json_content)]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    mock_response.id = "test_id"
    mock_response.stop_reason = "end_turn"

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    client = create_llm_client(config)
    result = client.generate_json("Generate JSON")

    assert isinstance(result, dict)
    assert result['key'] == 'value'
    assert result['number'] == 42


@patch('llm.anthropic_client.anthropic.Anthropic')
def test_anthropic_json_with_code_blocks(mock_anthropic):
    """Test parsing JSON from markdown code blocks."""
    config = {
        'provider': 'anthropic',
        'api_key': 'test_key',
        'model': 'claude-sonnet-4-5-20250929'
    }

    # Mock response with JSON in code block
    json_content = '```json\n{"key": "value"}\n```'
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json_content)]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    mock_response.id = "test_id"
    mock_response.stop_reason = "end_turn"

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    client = create_llm_client(config)
    result = client.generate_json("Generate JSON")

    assert isinstance(result, dict)
    assert result['key'] == 'value'


def test_ollama_free_cost():
    """Test that Ollama reports zero cost."""
    config = {
        'provider': 'ollama',
        'model': 'llama2',
        'base_url': 'http://localhost:11434'
    }

    with patch('llm.ollama_client.requests.get'):
        client = create_llm_client(config)

        cost = client.estimate_cost(1000, 500)
        assert cost == 0.0


@patch('llm.ollama_client.requests.post')
@patch('llm.ollama_client.requests.get')
def test_ollama_generate(mock_get, mock_post):
    """Test Ollama generate method."""
    config = {
        'provider': 'ollama',
        'model': 'llama2',
        'base_url': 'http://localhost:11434'
    }

    # Mock connection test
    mock_get.return_value.status_code = 200

    # Mock generate response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'response': 'Test response from Ollama',
        'total_duration': 1000000,
        'eval_count': 50
    }
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    client = create_llm_client(config)
    response = client.generate("Test prompt")

    assert isinstance(response, LLMResponse)
    assert response.content == 'Test response from Ollama'
    assert response.provider == 'ollama'
    assert response.cost_usd == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
