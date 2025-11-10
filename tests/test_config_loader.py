"""
Tests for ConfigLoader
"""

import pytest
import yaml
import tempfile
from pathlib import Path
from utils.config_loader import ConfigLoader


def test_config_loader_yaml():
    """Test loading YAML configuration."""
    config_data = {
        'user': {'name': 'Test User', 'email': 'test@example.com'},
        'job_preferences': {'keywords': ['Python', 'Django']},
        'skills': {'programming_languages': ['Python']},
        'llm': {'provider': 'anthropic', 'api_key_env': 'TEST_API_KEY'},
        'email': {'sender_email_env': 'TEST_EMAIL', 'sender_password_env': 'TEST_PASS'}
    }

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        # Set test environment variables
        import os
        os.environ['TEST_API_KEY'] = 'test_key_123'
        os.environ['TEST_EMAIL'] = 'test@example.com'
        os.environ['TEST_PASS'] = 'test_password'

        # Load config
        config = ConfigLoader(config_path)

        # Verify data
        assert config.get('user.name') == 'Test User'
        assert config.get('user.email') == 'test@example.com'
        assert 'Python' in config.get('job_preferences.keywords')
        assert config.get('llm.api_key') == 'test_key_123'

    finally:
        Path(config_path).unlink()


def test_config_get_with_default():
    """Test getting config values with defaults."""
    config_data = {
        'user': {'name': 'Test User', 'email': 'test@example.com'},
        'job_preferences': {'keywords': ['Python']},
        'skills': {},
        'llm': {'provider': 'anthropic', 'api_key': 'test_key'},
        'email': {}
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = ConfigLoader(config_path)

        # Existing key
        assert config.get('user.name') == 'Test User'

        # Non-existing key with default
        assert config.get('nonexistent.key', 'default_value') == 'default_value'

    finally:
        Path(config_path).unlink()


if __name__ == '__main__':
    pytest.main([__file__])
