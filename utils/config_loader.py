"""
Configuration Loader Module

Handles loading and validating configuration from YAML/JSON files and environment variables.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigLoader:
    """Loads and manages system configuration."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration loader.

        Args:
            config_path: Path to configuration file (YAML or JSON)
        """
        load_dotenv()  # Load environment variables from .env file

        if config_path is None:
            # Try to find config file in standard locations
            for path in ['config.yaml', 'config.yml', 'config.json']:
                if os.path.exists(path):
                    config_path = path
                    break

        if config_path is None:
            raise FileNotFoundError(
                "No configuration file found. Please provide config.yaml or config.json"
            )

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._resolve_env_variables()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            if self.config_path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif self.config_path.suffix == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported config format: {self.config_path.suffix}")

    def _resolve_env_variables(self):
        """Resolve environment variable references in config."""
        # Resolve API keys and credentials from environment
        if 'llm' in self.config and 'api_key_env' in self.config['llm']:
            env_var = self.config['llm']['api_key_env']
            self.config['llm']['api_key'] = os.getenv(env_var)

        if 'email' in self.config:
            if 'sender_email_env' in self.config['email']:
                env_var = self.config['email']['sender_email_env']
                self.config['email']['sender_email'] = os.getenv(env_var)

            if 'sender_password_env' in self.config['email']:
                env_var = self.config['email']['sender_password_env']
                self.config['email']['sender_password'] = os.getenv(env_var)

    def _validate_config(self):
        """Validate required configuration fields."""
        required_sections = ['user', 'job_preferences', 'skills', 'llm', 'email']

        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")

        # Validate user info
        if 'email' not in self.config['user']:
            raise ValueError("User email is required in configuration")

        # Validate LLM config
        if not self.config['llm'].get('api_key'):
            raise ValueError(
                f"LLM API key not found. Set {self.config['llm'].get('api_key_env', 'API_KEY')} "
                "environment variable"
            )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Configuration key (e.g., 'user.email')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section."""
        return self.config.get(section, {})

    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self.config[key]

    def __contains__(self, key: str) -> bool:
        """Check if key exists in config."""
        return key in self.config
